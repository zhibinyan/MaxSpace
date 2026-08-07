def init_markdown_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS markdown (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(128) NOT NULL,
            content LONGTEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_markdown_updated (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
