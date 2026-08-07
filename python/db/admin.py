from config import DB_NAME

from db.schema import column_exists


def init_admin_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS admin (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(64) NOT NULL UNIQUE,
            password CHAR(32) NOT NULL COMMENT 'MD5 hex',
            is_super TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1=超级管理员',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    if not column_exists(cursor, 'admin', 'is_super', DB_NAME):
        cursor.execute(
            'ALTER TABLE admin ADD COLUMN is_super TINYINT(1) NOT NULL DEFAULT 0 COMMENT \'1=超级管理员\''
        )

    cursor.execute(
        'UPDATE admin SET is_super = 1 WHERE username = %s AND is_super = 0',
        ('admin',),
    )
