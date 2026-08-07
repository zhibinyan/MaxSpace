from config import DB_NAME

from db.admin import init_admin_table
from db.connection import get_connection
from db.file import init_file_table, seed_file_manager_menu
from db.linux import init_linux_tables, seed_linux_service_menu
from db.menu import init_menu_table
from db.markdown import init_markdown_table
from db.process import init_process_table

__all__ = ['get_connection', 'migrate']


def migrate():
    conn = get_connection(database=None)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                'DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
            )
    finally:
        conn.close()

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            init_admin_table(cursor)
            init_menu_table(cursor)
            init_process_table(cursor)
            init_markdown_table(cursor)
            init_file_table(cursor)
            seed_file_manager_menu(cursor)
            init_linux_tables(cursor)
            seed_linux_service_menu(cursor)
    finally:
        conn.close()
