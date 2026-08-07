import sys

from db import migrate


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] != 'migrate':
        print('Usage: python -m db migrate')
        sys.exit(1)

    migrate()
    print('Database migration completed.')


if __name__ == '__main__':
    main()
