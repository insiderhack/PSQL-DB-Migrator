import pytest
from unittest.mock import MagicMock
from pg_migrator.analyzer import CompatibilityAnalyzer, IssueSeverity

def test_analyzer_connection_failure():
    """Test analyzer behavior when connection fails."""
    analyzer = CompatibilityAnalyzer("host=invalid", 14)
    result = analyzer.analyze()
    
    assert result.source_version == 14
    assert result.critical_count == 1
    assert "Cannot connect" in result.issues[0].message

def test_check_authentication_md5(mock_db_connection):
    """Test detection of MD5 authentication."""
    conn, cursor = mock_db_connection
    cursor.fetchone.return_value = (5,)  # 5 MD5 users
    
    analyzer = CompatibilityAnalyzer("dsn", 14)
    analyzer._connection = conn
    
    # We need to mock the other methods called by analyze() to isolate authentication
    analyzer._check_breaking_changes = MagicMock()
    analyzer._check_deprecations = MagicMock()
    analyzer._check_extensions = MagicMock()
    analyzer._check_schemas = MagicMock()
    analyzer._check_data_types = MagicMock()
    analyzer._check_opportunities = MagicMock()
    
    result = analyzer.analyze()
    
    # Check that MD5 issue was added
    auth_issues = [i for i in result.issues if "MD5" in i.message]
    assert len(auth_issues) == 1
    assert auth_issues[0].severity == IssueSeverity.WARNING
