from config import DB_NAME

from db.schema import column_exists


def init_menu_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS menu (
            id INT AUTO_INCREMENT PRIMARY KEY,
            parent_id INT NULL,
            path VARCHAR(128) NOT NULL,
            name VARCHAR(64) NULL,
            title VARCHAR(64) NOT NULL,
            icon VARCHAR(64) NOT NULL DEFAULT 'Menu',
            component VARCHAR(512) NULL,
            redirect VARCHAR(256) NULL,
            keep_alive TINYINT(1) NOT NULL DEFAULT 0,
            dock TINYINT(1) NOT NULL DEFAULT 0,
            sort_order INT NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_menu_parent_sort (parent_id, sort_order)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )

    if not column_exists(cursor, 'menu', 'dock', DB_NAME):
        cursor.execute(
            'ALTER TABLE menu ADD COLUMN dock TINYINT(1) NOT NULL DEFAULT 0'
        )
