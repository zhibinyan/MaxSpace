def init_file_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS file_entry (
            id INT AUTO_INCREMENT PRIMARY KEY,
            parent_id INT NULL,
            name VARCHAR(255) NOT NULL,
            is_folder TINYINT(1) NOT NULL DEFAULT 0,
            ext VARCHAR(32) NULL,
            mime_type VARCHAR(128) NULL,
            size_bytes BIGINT NOT NULL DEFAULT 0,
            category VARCHAR(32) NOT NULL DEFAULT 'other',
            storage_key VARCHAR(512) NULL,
            created_by VARCHAR(64) NULL,
            updated_by VARCHAR(64) NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_file_parent_name (parent_id, name),
            INDEX idx_file_category (category),
            INDEX idx_file_updated (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )


def seed_file_manager_menu(cursor) -> None:
    """注册「文件管理」菜单（若不存在）。"""
    cursor.execute(
        "SELECT id FROM menu WHERE path = %s OR name = %s LIMIT 1",
        ('files', 'fileManager'),
    )
    if cursor.fetchone():
        return

    cursor.execute(
        """
        INSERT INTO menu (
            parent_id, path, name, title, icon, component,
            redirect, keep_alive, dock, sort_order
        ) VALUES (
            NULL, 'files', 'fileManager', '文件管理', 'folder',
            '@/views/files/FileManagerView.vue',
            NULL, 1, 1, 40
        )
        """
    )
