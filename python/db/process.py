def init_process_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS process (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(128) NOT NULL,
            description VARCHAR(512) NULL,
            process_data LONGTEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_process_updated (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
