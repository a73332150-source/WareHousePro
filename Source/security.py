"""
WareHousePro - Security, Cryptography & RBAC Subsystem
Enforces salted PBKDF2 password hashing, constant-time comparison,
and strict multi-role permission authorization.
"""
import hashlib
import hmac
import os
import logging
from typing import Optional, Dict, Any, List
from enum import Enum

from exceptions import AuthenticationError, PermissionDeniedError

logger = logging.getLogger("WareHousePro.Security")

class UserRole(Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    OPERATOR = "OPERATOR"

PERMISSIONS = {
    "VIEW_INVENTORY": [UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR],
    "RECORD_MOVEMENT": [UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR],
    "MANAGE_PRODUCTS": [UserRole.ADMIN, UserRole.MANAGER],
    "VIEW_REPORTS": [UserRole.ADMIN, UserRole.MANAGER],
    "EXPORT_DATA": [UserRole.ADMIN, UserRole.MANAGER],
    "MANAGE_USERS": [UserRole.ADMIN],
    "DATABASE_BACKUP": [UserRole.ADMIN],
    "VIEW_AUDIT_LOGS": [UserRole.ADMIN],
}

class SecurityManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SecurityManager, cls).__new__(cls)
            cls._instance.current_user: Optional[Dict[str, Any]] = None
        return cls._instance

    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """Generates a cryptographically secure salted PBKDF2 hash (100,000 rounds)."""
        if salt is None:
            salt = os.urandom(32)
        pwd_hash = hashlib.pbkdf2_hmac(
            hash_name='sha256',
            password=password.encode('utf-8'),
            salt=salt,
            iterations=100_000
        )
        return pwd_hash.hex(), salt.hex()

    @staticmethod
    def verify_password(password: str, stored_hash_hex: str, salt_hex: str) -> bool:
        """Constant-time password verification preventing timing attack vectors."""
        salt = bytes.fromhex(salt_hex)
        computed_hash, _ = SecurityManager.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, stored_hash_hex)

    def login(self, username: str, password: str, db_manager) -> Dict[str, Any]:
        conn = db_manager._get_connection()
        cur = conn.execute(
            "SELECT id, username, password_hash, salt, role, full_name, is_active FROM users WHERE username = ?;",
            (username.strip(),)
        )
        user = cur.fetchone()

        if not user:
            logger.warning(f"Failed login attempt for non-existent user '{username}'")
            raise AuthenticationError("اسم المستخدم أو كلمة المرور غير صحيحة.")

        if not user["is_active"]:
            logger.warning(f"Login rejected for deactivated user '{username}'")
            raise AuthenticationError("هذا الحساب معطل حالياً. يرجى مراجعة مسؤول النظام.")

        if not self.verify_password(password, user["password_hash"], user["salt"]):
            logger.warning(f"Invalid password for user '{username}'")
            raise AuthenticationError("اسم المستخدم أو كلمة المرور غير صحيحة.")

        self.current_user = {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": UserRole(user["role"])
        }
        logger.info(f"User '{username}' logged in successfully with role {user['role']}")
        return self.current_user

    def logout(self):
        logger.info(f"User {self.current_user.get('username') if self.current_user else 'unknown'} logged out.")
        self.current_user = None

    def has_permission(self, permission_key: str) -> bool:
        if not self.current_user:
            return False
        user_role = self.current_user["role"]
        allowed_roles = PERMISSIONS.get(permission_key, [])
        return user_role in allowed_roles

    def require_permission(self, permission_key: str):
        if not self.has_permission(permission_key):
            raise PermissionDeniedError(
                f"عفواً، لا تملك الصلاحيات الكافية لتنفيذ هذا الإجراء ({permission_key}). يرجى التواصل مع المسؤول."
            )

    def bootstrap_default_admin(self, db_manager):
        """Creates the initial admin user safely if the system has zero accounts."""
        conn = db_manager._get_connection()
        cur = conn.execute("SELECT COUNT(*) as count FROM users;")
        if cur.fetchone()["count"] == 0:
            logger.info("No users found. Creating default Administrator account...")
            pwd_hash, salt = self.hash_password("Admin@123")
            with db_manager.transaction() as tx:
                tx.execute("""
                    INSERT INTO users (username, password_hash, salt, role, full_name, is_active)
                    VALUES (?, ?, ?, 'ADMIN', 'مدير النظام الرئيسي', 1);
                """, ("admin", pwd_hash, salt))
            logger.info("Initial Admin created with username: admin")
