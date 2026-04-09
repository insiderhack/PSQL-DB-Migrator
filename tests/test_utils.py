import pytest
from pg_migrator.utils import build_dsn, mask_password

def test_build_dsn():
    """Test DSN construction string format."""
    dsn = build_dsn("localhost", 5432, "mydb", "postgres", "secret123")
    assert dsn == "host=localhost port=5432 dbname=mydb user=postgres password=secret123"

def test_build_dsn_no_password():
    """Test DSN construction without password."""
    dsn = build_dsn("localhost", 5432, "mydb", "postgres")
    assert dsn == "host=localhost port=5432 dbname=mydb user=postgres"

def test_mask_dsn_password():
    """Test masking passwords in DSN string."""
    dsn = "host=localhost port=5432 dbname=mydb user=postgres password=secret123"
    masked = mask_password(dsn)
    assert masked == "host=localhost port=5432 dbname=mydb user=postgres password=****"
    
def test_mask_dsn_no_password():
    """Test masking a DSN that doesn't have a password."""
    dsn = "host=localhost port=5432 dbname=mydb user=postgres"
    masked = mask_password(dsn)
    assert masked == "host=localhost port=5432 dbname=mydb user=postgres"

