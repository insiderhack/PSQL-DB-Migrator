import pytest
from unittest.mock import MagicMock
import psycopg2

@pytest.fixture
def mock_db_connection():
    """Mock a psycopg2 database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Configure cursor context manager
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    return mock_conn, mock_cursor
