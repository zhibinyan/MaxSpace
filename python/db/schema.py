def column_exists(cursor, table: str, column: str, schema: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (schema, table, column),
    )
    return cursor.fetchone()['count'] > 0
