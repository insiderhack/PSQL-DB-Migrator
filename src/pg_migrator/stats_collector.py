"""
Database statistics collector for pre-migration analysis.
Gathers table counts, row counts, data sizes, and other metrics.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extensions import connection


@dataclass
class TableStats:
    """Statistics for a single table."""
    schema: str
    name: str
    row_count: int
    size_bytes: int
    column_count: int
    has_primary_key: bool = True
    has_foreign_keys: bool = False
    has_indexes: bool = False

    @property
    def full_name(self) -> str:
        return f"{self.schema}.{self.name}"

    @property
    def size_formatted(self) -> str:
        """Return human-readable size."""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        elif self.size_bytes < 1024 * 1024 * 1024:
            return f"{self.size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{self.size_bytes / (1024 * 1024 * 1024):.2f} GB"


@dataclass
class SchemaStats:
    """Statistics for a schema."""
    name: str
    table_count: int
    total_rows: int
    total_size_bytes: int

    @property
    def size_formatted(self) -> str:
        if self.total_size_bytes < 1024 * 1024:
            return f"{self.total_size_bytes / 1024:.1f} KB"
        elif self.total_size_bytes < 1024 * 1024 * 1024:
            return f"{self.total_size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{self.total_size_bytes / (1024 * 1024 * 1024):.2f} GB"


@dataclass
class DatabaseStats:
    """Complete database statistics."""
    database_name: str
    total_schemas: int = 0
    total_tables: int = 0
    total_rows: int = 0
    total_size_bytes: int = 0
    total_indexes: int = 0
    total_views: int = 0
    total_functions: int = 0
    total_sequences: int = 0
    total_triggers: int = 0
    total_extensions: int = 0

    tables: List[TableStats] = field(default_factory=list)
    schemas: List[SchemaStats] = field(default_factory=list)
    extensions: List[str] = field(default_factory=list)

    @property
    def total_size_formatted(self) -> str:
        if self.total_size_bytes < 1024 * 1024:
            return f"{self.total_size_bytes / 1024:.1f} KB"
        elif self.total_size_bytes < 1024 * 1024 * 1024:
            return f"{self.total_size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{self.total_size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def get_migration_steps(self) -> List[Dict[str, Any]]:
        """Get estimated migration steps with weights for progress tracking."""
        steps = [
            {"name": "Connect to databases", "weight": 5},
            {"name": "Detect versions", "weight": 5},
            {"name": "Analyze compatibility", "weight": 10},
            {"name": "Create schemas", "weight": 5, "count": self.total_schemas},
        ]

        # Add weight for each table migration
        for table in self.tables:
            weight = max(1, min(20, table.row_count // 10000 + 1))  # Weight based on rows
            steps.append({
                "name": f"Migrate {table.full_name}",
                "weight": weight,
                "rows": table.row_count,
                "size": table.size_bytes,
            })

        steps.extend([
            {"name": "Create indexes", "weight": 10, "count": self.total_indexes},
            {"name": "Create constraints", "weight": 5},
            {"name": "Create sequences", "weight": 3, "count": self.total_sequences},
            {"name": "Create views", "weight": 5, "count": self.total_views},
            {"name": "Create functions", "weight": 5, "count": self.total_functions},
            {"name": "Validate migration", "weight": 10},
        ])

        return steps

    def get_total_weight(self) -> int:
        """Get total weight for progress calculation."""
        return sum(step["weight"] for step in self.get_migration_steps())


class DatabaseStatsCollector:
    """Collects statistics from a PostgreSQL database for migration planning."""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self._conn: Optional[connection] = None

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self._conn = psycopg2.connect(self.dsn)
            return True
        except Exception:
            return False

    def disconnect(self):
        """Close connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def collect_stats(self) -> Optional[DatabaseStats]:
        """Collect comprehensive database statistics."""
        if not self._conn:
            if not self.connect():
                return None

        try:
            stats = DatabaseStats(database_name=self._get_database_name())

            # Get schema stats
            stats.schemas = self._get_schema_stats()
            stats.total_schemas = len(stats.schemas)

            # Get table stats
            stats.tables = self._get_table_stats()
            stats.total_tables = len(stats.tables)
            stats.total_rows = sum(t.row_count for t in stats.tables)
            stats.total_size_bytes = sum(t.size_bytes for t in stats.tables)

            # Get other object counts
            stats.total_indexes = self._get_index_count()
            stats.total_views = self._get_view_count()
            stats.total_functions = self._get_function_count()
            stats.total_sequences = self._get_sequence_count()
            stats.total_triggers = self._get_trigger_count()
            stats.extensions = self._get_extensions()
            stats.total_extensions = len(stats.extensions)

            return stats

        except Exception as e:
            print(f"Error collecting stats: {e}")
            return None

    def _get_database_name(self) -> str:
        """Get current database name."""
        if self._conn is None:
            return ""
        with self._conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            result = cur.fetchone()
            return result[0] if result else ""

    def _get_schema_stats(self) -> List[SchemaStats]:
        """Get statistics per schema."""
        schemas: List[SchemaStats] = []
        if self._conn is None:
            return schemas
        query = """
        SELECT 
            schemaname,
            COUNT(*) as table_count,
            COALESCE(SUM(n_live_tup), 0) as total_rows,
            COALESCE(SUM(pg_total_relation_size(schemaname || '.' || relname)), 0) as total_size
        FROM pg_stat_user_tables
        GROUP BY schemaname
        ORDER BY schemaname
        """
        with self._conn.cursor() as cur:
            cur.execute(query)
            for row in cur.fetchall():
                schemas.append(SchemaStats(
                    name=row[0],
                    table_count=row[1],
                    total_rows=row[2],
                    total_size_bytes=row[3],
                ))
        return schemas

    def _get_table_stats(self) -> List[TableStats]:
        """Get statistics per table."""
        tables: List[TableStats] = []
        if self._conn is None:
            return tables
        query = """
        SELECT 
            schemaname,
            relname,
            n_live_tup,
            pg_total_relation_size(schemaname || '.' || relname) as size_bytes,
            (SELECT COUNT(*) FROM information_schema.columns c 
             WHERE c.table_schema = t.schemaname AND c.table_name = t.relname) as col_count
        FROM pg_stat_user_tables t
        ORDER BY n_live_tup DESC
        """
        with self._conn.cursor() as cur:
            cur.execute(query)
            for row in cur.fetchall():
                tables.append(TableStats(
                    schema=row[0],
                    name=row[1],
                    row_count=row[2] or 0,
                    size_bytes=row[3] or 0,
                    column_count=row[4] or 0,
                ))
        return tables

    def _get_index_count(self) -> int:
        """Count user indexes."""
        if self._conn is None:
            return 0
        with self._conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM pg_indexes 
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            """)
            result = cur.fetchone()
            return result[0] if result else 0

    def _get_view_count(self) -> int:
        """Count user views."""
        if self._conn is None:
            return 0
        with self._conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.views 
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            """)
            result = cur.fetchone()
            return result[0] if result else 0

    def _get_function_count(self) -> int:
        """Count user functions."""
        if self._conn is None:
            return 0
        with self._conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
            """)
            result = cur.fetchone()
            return result[0] if result else 0

    def _get_sequence_count(self) -> int:
        """Count sequences."""
        if self._conn is None:
            return 0
        with self._conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.sequences 
                WHERE sequence_schema NOT IN ('pg_catalog', 'information_schema')
            """)
            result = cur.fetchone()
            return result[0] if result else 0

    def _get_trigger_count(self) -> int:
        """Count triggers."""
        if self._conn is None:
            return 0
        with self._conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.triggers 
                WHERE trigger_schema NOT IN ('pg_catalog', 'information_schema')
            """)
            result = cur.fetchone()
            return result[0] if result else 0

    def _get_extensions(self) -> List[str]:
        """Get list of installed extensions."""
        if self._conn is None:
            return []
        with self._conn.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension WHERE extname != 'plpgsql'")
            return [row[0] for row in cur.fetchall()]

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
