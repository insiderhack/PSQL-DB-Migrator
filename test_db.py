from src.pg_migrator.config import get_config
import psycopg2

c = get_config()
print(c.database.get_source_dsn())
try:
    psycopg2.connect(c.database.get_source_dsn())
    print("Success")
except Exception as e:
    print(f"Error: {e}")
