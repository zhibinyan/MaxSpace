from typing import Optional

import pymysql

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def get_connection(database: Optional[str] = DB_NAME):
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=database,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=5,
    )
