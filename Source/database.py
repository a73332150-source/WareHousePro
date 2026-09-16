"""
WareHousePro - Database Management Subsystem
Engineered for ACID compliance, zero corruption, Foreign Keys enforcement,
and thread-safe transactional integrity.
"""
import os
import sqlite3
import threading
import logging
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

from exceptions import (
    WareHouseProException,
    DatabaseError,
    DatabaseIntegrityError,
    InsufficientStockError,
    RecordNotFoundError
)

logger = logging.getLogger("WareHousePro.Database")

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = "warehousepro.db"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._init_db(db_path)
            return cls._instance

    def _init_db(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        self._thread_local = threading.local()
        logger.info(f"Connecting to database at: {self.db_path}")
        self._bootstrap_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a thread-local SQLite connection with PRAGMA optimizations."""
        if not hasattr(self._thread_local, "conn") or self._thread_local.conn is None:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False
            )
            # Enable Row Factory for dictionary-style access
            conn.row_factory = sqlite3.Row
            # Mandatory Pragmas for Enterprise Reliability
            with conn:
                # 1. Force Foreign Keys enforcement
                conn.execute("PRAGMA foreign_keys = ON;")
                # 2. Write-Ahead Logging for high concurrency & power-loss safety
                conn.execute("PRAGMA journal_mode = WAL;")
                # 3. Normal synchronous mode gives optimal performance while remaining WAL-safe
                conn.execute("PRAGMA synchronous = NORMAL;")
                # 4. UTF-8 Encoding
                conn.execute("PRAGMA encoding = 'UTF-8';")
            self._thread_local.conn = conn
        return self._thread_local.conn

    @contextmanager
    def transaction(self):
        """
        Thread-safe context manager for atomic database transactions.
        Guarantees automatic rollback on failure and release of resources.
        """
        conn = self._get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            yield conn
            conn.commit()
        except WareHouseProException:
            conn.rollback()
            raise
        except sqlite3.IntegrityError as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to IntegrityError: {e}")
            raise DatabaseIntegrityError(f"Database constraint violation: {e}") from e
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to unexpected error: {e}")
            raise DatabaseError(f"Transaction failed: {e}") from e

    def _bootstrap_schema(self):
        """Initializes database tables with strict relational integrity."""
        with self.transaction() as conn:
            # Users & Roles
            conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('ADMIN', 'MANAGER', 'OPERATOR')),
                full_name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1 NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
            """)

            # Categories
            conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            );
            """)

            # Products Table with Foreign Keys
            conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category_id INTEGER,
                quantity INTEGER DEFAULT 0 NOT NULL CHECK(quantity >= 0),
                min_threshold INTEGER DEFAULT 5 NOT NULL CHECK(min_threshold >= 0),
                unit_price REAL DEFAULT 0.0 NOT NULL CHECK(unit_price >= 0.0),
                supplier_name TEXT,
                location_bin TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            );
            """)

            # Stock Movements (Inbound / Outbound / Audit)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL CHECK(movement_type IN ('IN', 'OUT', 'ADJUST')),
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL DEFAULT 0.0,
                reference_no TEXT,
                notes TEXT,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """)

            # System Audit Log
            conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity TEXT NOT NULL,
                entity_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """)

            # Indices for lightning-fast queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_movements_prod ON stock_movements(product_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_movements_date ON stock_movements(created_at);")

            # Seed default categories if empty
            cur = conn.execute("SELECT COUNT(*) as count FROM categories;")
            if cur.fetchone()["count"] == 0:
                categories = [
                    ("قطع غيار وإلكترونيات", "الأجزاء والمكونات الإلكترونية والمتحكمات"),
                    ("مواد خام وتغليف", "صناديق ومواد التغليف والتعبئة"),
                    ("معدات وأدوات صناعية", "الأدوات والمعدات الميكانيكية"),
                    ("بضائع تامة الصنع", "المنتجات الجاهزة للشحن والتوزيع")
                ]
                conn.executemany("INSERT INTO categories (name, description) VALUES (?, ?);", categories)

    # ------------------ Products API ------------------
    def get_all_products(self, search: str = "", category_id: Optional[int] = None, low_stock_only: bool = False) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        """
        params: List[Any] = []

        if search:
            query += " AND (p.name LIKE ? OR p.sku LIKE ? OR p.supplier_name LIKE ?)"
            term = f"%{search.strip()}%"
            params.extend([term, term, term])

        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)

        if low_stock_only:
            query += " AND p.quantity <= p.min_threshold"

        query += " ORDER BY p.name ASC;"
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_product_by_id(self, product_id: int) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM products WHERE id = ?;", (product_id,))
        row = cursor.fetchone()
        if not row:
            raise RecordNotFoundError(f"Product ID {product_id} not found.")
        return dict(row)

    def add_product(self, sku: str, name: str, category_id: Optional[int], quantity: int, min_threshold: int, unit_price: float, supplier_name: str, location_bin: str, user_id: Optional[int] = None) -> int:
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO products (sku, name, category_id, quantity, min_threshold, unit_price, supplier_name, location_bin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (sku.strip().upper(), name.strip(), category_id, quantity, min_threshold, unit_price, supplier_name.strip(), location_bin.strip()))
            prod_id = cursor.lastrowid

            # Initial stock movement if quantity > 0
            if quantity > 0:
                conn.execute("""
                    INSERT INTO stock_movements (product_id, movement_type, quantity, unit_price, reference_no, notes, user_id)
                    VALUES (?, 'IN', ?, ?, 'INITIAL-STOCK', 'رصيد افتتاحي أولي', ?);
                """, (prod_id, quantity, unit_price, user_id))

            conn.execute("""
                INSERT INTO audit_logs (user_id, action, entity, entity_id, details)
                VALUES (?, 'CREATE_PRODUCT', 'products', ?, ?);
            """, (user_id, prod_id, f"Created product {name} ({sku}) with qty {quantity}"))
            return prod_id

    def update_product(self, product_id: int, name: str, category_id: Optional[int], min_threshold: int, unit_price: float, supplier_name: str, location_bin: str, user_id: Optional[int] = None):
        with self.transaction() as conn:
            conn.execute("""
                UPDATE products
                SET name = ?, category_id = ?, min_threshold = ?, unit_price = ?, supplier_name = ?, location_bin = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
            """, (name.strip(), category_id, min_threshold, unit_price, supplier_name.strip(), location_bin.strip(), product_id))
            conn.execute("""
                INSERT INTO audit_logs (user_id, action, entity, entity_id, details)
                VALUES (?, 'UPDATE_PRODUCT', 'products', ?, ?);
            """, (user_id, product_id, f"Updated details for product ID {product_id}"))

    # ------------------ Atomic Stock Movement ------------------
    def record_stock_movement(self, product_id: int, movement_type: str, quantity: int, unit_price: float, reference_no: str, notes: str, user_id: Optional[int] = None) -> Tuple[int, int]:
        """
        Executes an atomic inventory transaction.
        Checks stock availability, updates balance, inserts movement record and audit log.
        """
        if quantity <= 0:
            raise ValueError("Movement quantity must be greater than zero.")

        with self.transaction() as conn:
            # Lock the row with SELECT FOR UPDATE style logic
            cur = conn.execute("SELECT quantity, name FROM products WHERE id = ?;", (product_id,))
            prod = cur.fetchone()
            if not prod:
                raise RecordNotFoundError(f"Product ID {product_id} not found.")

            current_qty = prod["quantity"]
            prod_name = prod["name"]

            if movement_type == 'IN':
                new_qty = current_qty + quantity
            elif movement_type == 'OUT':
                if current_qty < quantity:
                    raise InsufficientStockError(
                        f"الكمية المطلوبة ({quantity}) أكبر من الرصيد المتوفر ({current_qty}) للصنف '{prod_name}'."
                    )
                new_qty = current_qty - quantity
            elif movement_type == 'ADJUST':
                new_qty = quantity  # Absolute adjustment
            else:
                raise ValueError(f"Unknown movement type: {movement_type}")

            # Update product quantity
            conn.execute("UPDATE products SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (new_qty, product_id))

            # Record movement log
            cur_move = conn.execute("""
                INSERT INTO stock_movements (product_id, movement_type, quantity, unit_price, reference_no, notes, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (product_id, movement_type, quantity, unit_price, reference_no.strip(), notes.strip(), user_id))
            movement_id = cur_move.lastrowid

            # Audit record
            conn.execute("""
                INSERT INTO audit_logs (user_id, action, entity, entity_id, details)
                VALUES (?, ?, 'stock_movements', ?, ?);
            """, (user_id, f"STOCK_{movement_type}", movement_id, f"{movement_type} {quantity} units for {prod_name}. Previous: {current_qty}, New: {new_qty}"))

            return movement_id, new_qty

    def get_recent_movements(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT m.*, p.name as product_name, p.sku, u.full_name as user_name
            FROM stock_movements m
            JOIN products p ON m.product_id = p.id
            LEFT JOIN users u ON m.user_id = u.id
            ORDER BY m.created_at DESC
            LIMIT ?;
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_dashboard_kpis(self) -> Dict[str, Any]:
        conn = self._get_connection()
        cur = conn.execute("""
            SELECT
                COUNT(*) as total_products,
                COALESCE(SUM(quantity), 0) as total_units,
                COALESCE(SUM(quantity * unit_price), 0.0) as total_valuation,
                COALESCE(SUM(CASE WHEN quantity <= min_threshold THEN 1 ELSE 0 END), 0) as low_stock_count
            FROM products;
        """)
        stats = dict(cur.fetchone())

        # Today's operations
        cur_today = conn.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN movement_type = 'IN' THEN quantity ELSE 0 END), 0) as in_today,
                COALESCE(SUM(CASE WHEN movement_type = 'OUT' THEN quantity ELSE 0 END), 0) as out_today
            FROM stock_movements
            WHERE date(created_at) = date('now', 'localtime');
        """)
        stats.update(dict(cur_today.fetchone()))
        return stats

    def check_integrity(self) -> bool:
        """Runs SQLite PRAGMA integrity_check to guarantee database health."""
        conn = self._get_connection()
        cur = conn.execute("PRAGMA integrity_check;")
        row = cur.fetchone()
        return row[0] == "ok" if row else False
