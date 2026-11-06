
from radar.database.connection import get_connection


def main() -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT current_database(), version()")
            database_name, version = cursor.fetchone()

            print("Database connection successful!")
            print(f"Database: {database_name}")
            print(f"PostgreSQL: {version.split(',')[0]}")


if __name__ == "__main__":
    main()
