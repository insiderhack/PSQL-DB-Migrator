"""
Pure Python PostgreSQL Migration using psycopg2.
No dependency on pg_dump/pg_restore command-line tools.
"""

from dataclasses import dataclass
from io import StringIO
from typing import Callable, List, Optional, Tuple

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, connection

from .logger import get_logger


@dataclass
class TableInfo:
    """Information about a table."""
    schema: str
    name: str
    columns: List[str]
    row_count: int = 0


class PythonMigrator:
    """
    Pure Python PostgreSQL migrator using psycopg2.
    Migrates schema and data without requiring pg_dump/pg_restore.
    """

    def __init__(
        self,
        source_dsn: str,
        target_dsn: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ):
        """
        Initialize the migrator.
        
        Args:
            source_dsn: Source database connection string
            target_dsn: Target database connection string
            progress_callback: Optional callback for progress updates (message, current, total)
        """
        self.source_dsn = source_dsn
        self.target_dsn = target_dsn
        self.progress_callback = progress_callback
        self.logger = get_logger()

        self._source_conn: Optional[connection] = None
        self._target_conn: Optional[connection] = None

    def _update_progress(self, message: str, current: int = 0, total: int = 0):
        """Update progress via callback."""
        if self.progress_callback:
            self.progress_callback(message, current, total)
        self.logger.info(message)

    def connect(self) -> Tuple[bool, str]:
        """Connect to both databases. Creates target database if it doesn't exist."""
        try:
            # Connect to source
            self._source_conn = psycopg2.connect(self.source_dsn)

            # Try to connect to target
            try:
                self._target_conn = psycopg2.connect(self.target_dsn)
            except psycopg2.OperationalError as e:
                # Database might not exist - try to create it
                if "does not exist" in str(e):
                    self._update_progress("Target database not found, creating...")
                    if self._create_target_database():
                        self._target_conn = psycopg2.connect(self.target_dsn)
                    else:
                        return False, f"Cannot create target database: {e}"
                else:
                    return False, f"Target connection error: {e}"

            self._target_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            return True, "Connected to both databases"
        except Exception as e:
            return False, f"Connection error: {e}"

    def _create_target_database(self) -> bool:
        """Create the target database by connecting to postgres database first."""
        try:
            # Parse target DSN to get database name and create DSN for postgres db
            target_parts = {}
            for part in self.target_dsn.split():
                if '=' in part:
                    key, value = part.split('=', 1)
                    target_parts[key] = value

            dbname = target_parts.get('dbname', target_parts.get('database', 'postgres'))
            owner = target_parts.get('user', 'postgres')

            # Create DSN for postgres database
            postgres_dsn = self.target_dsn.replace(f"dbname={dbname}", "dbname=postgres")
            postgres_dsn = postgres_dsn.replace(f"database={dbname}", "database=postgres")

            # Connect to postgres database
            admin_conn = psycopg2.connect(postgres_dsn)
            admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            with admin_conn.cursor() as cur:
                # Create the database
                cur.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(dbname),
                        sql.Identifier(owner)
                    )
                )

            admin_conn.close()
            self._update_progress(f"Created target database: {dbname}")
            return True

        except Exception as e:
            self.logger.warning(f"Failed to create database: {e}")
            return False

    def disconnect(self):
        """Disconnect from both databases."""
        if self._source_conn:
            self._source_conn.close()
        if self._target_conn:
            self._target_conn.close()

    def get_schemas(self) -> List[str]:
        """Get list of user schemas from source database."""
        if self._source_conn is None:
            return []
            
        with self._source_conn.cursor() as cur:
            cur.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                AND schema_name NOT LIKE 'pg_temp_%'
                AND schema_name NOT LIKE 'pg_toast_temp_%'
                ORDER BY schema_name
            """)
            return [row[0] for row in cur.fetchall()]

    def get_tables(self, schema: str = 'public') -> List[TableInfo]:
        """Get list of tables in a schema."""
        tables: List[TableInfo] = []
        
        if self._source_conn is None:
            return tables

        with self._source_conn.cursor() as cur:
            # Get tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (schema,))

            for (table_name,) in cur.fetchall():
                # Get columns
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table_name))
                columns = [row[0] for row in cur.fetchall()]

                # Get row count
                cur.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                        sql.Identifier(schema),
                        sql.Identifier(table_name)
                    )
                )
                row_count_res = cur.fetchone()
                row_count = row_count_res[0] if row_count_res else 0

                tables.append(TableInfo(
                    schema=schema,
                    name=table_name,
                    columns=columns,
                    row_count=row_count,
                ))

        return tables

    def migrate_schema(self) -> Tuple[bool, str]:
        """
        Migrate the database schema (DDL) from source to target.
        """
        try:
            self._update_progress("Migrating schema...")
            
            if self._source_conn is None or self._target_conn is None:
                return False, "Not connected to databases"

            with self._source_conn.cursor() as src_cur:
                # Get all schema DDL

                # 1. Create schemas
                schemas = self.get_schemas()
                for schema in schemas:
                    if schema != 'public':  # public already exists
                        try:
                            with self._target_conn.cursor() as tgt_cur:
                                tgt_cur.execute(
                                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                                        sql.Identifier(schema)
                                    )
                                )
                            self._update_progress(f"Created schema: {schema}")
                        except Exception as e:
                            self.logger.warning(f"Schema {schema}: {e}")

                # 2. Get and recreate types (enums)
                src_cur.execute("""
                    SELECT n.nspname as schema, t.typname as name,
                           string_agg(e.enumlabel, ',' ORDER BY e.enumsortorder) as labels
                    FROM pg_type t
                    JOIN pg_enum e ON t.oid = e.enumtypid
                    JOIN pg_namespace n ON t.typnamespace = n.oid
                    WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
                    GROUP BY n.nspname, t.typname
                """)

                for schema, name, labels in src_cur.fetchall():
                    try:
                        with self._target_conn.cursor() as tgt_cur:
                            # Drop if exists
                            tgt_cur.execute(
                                sql.SQL("DROP TYPE IF EXISTS {}.{} CASCADE").format(
                                    sql.Identifier(schema),
                                    sql.Identifier(name)
                                )
                            )
                            # Create enum
                            label_list = labels.split(',')
                            tgt_cur.execute(
                                sql.SQL("CREATE TYPE {}.{} AS ENUM ({})").format(
                                    sql.Identifier(schema),
                                    sql.Identifier(name),
                                    sql.SQL(', ').join(sql.Literal(l) for l in label_list)
                                )
                            )
                        self._update_progress(f"Created type: {schema}.{name}")
                    except Exception as e:
                        self.logger.warning(f"Type {schema}.{name}: {e}")

                # 3. Get and recreate sequences
                src_cur.execute("""
                    SELECT schemaname, sequencename, start_value, increment_by, 
                           max_value, min_value, cycle
                    FROM pg_sequences
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                """)

                for row in src_cur.fetchall():
                    schema, name, start, inc, max_val, min_val, cycle = row
                    try:
                        with self._target_conn.cursor() as tgt_cur:
                            cycle_str = "CYCLE" if cycle else "NO CYCLE"
                            tgt_cur.execute(
                                sql.SQL("""
                                    CREATE SEQUENCE IF NOT EXISTS {}.{}
                                    START WITH {} INCREMENT BY {} 
                                    MINVALUE {} MAXVALUE {} {}
                                """).format(
                                    sql.Identifier(schema),
                                    sql.Identifier(name),
                                    sql.Literal(start or 1),
                                    sql.Literal(inc or 1),
                                    sql.Literal(min_val or 1),
                                    sql.Literal(max_val or 9223372036854775807),
                                    sql.SQL(cycle_str)
                                )
                            )
                        self._update_progress(f"Created sequence: {schema}.{name}")
                    except Exception as e:
                        self.logger.warning(f"Sequence {schema}.{name}: {e}")

                # 4. Get and recreate tables
                for schema in schemas:
                    src_cur.execute("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = %s AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """, (schema,))

                    for (table_name,) in src_cur.fetchall():
                        try:
                            # Get table DDL using pg_get_tabledef workaround
                            ddl = self._get_table_ddl(schema, table_name)

                            with self._target_conn.cursor() as tgt_cur:
                                # Drop if exists
                                tgt_cur.execute(
                                    sql.SQL("DROP TABLE IF EXISTS {}.{} CASCADE").format(
                                        sql.Identifier(schema),
                                        sql.Identifier(table_name)
                                    )
                                )
                                # Create table
                                tgt_cur.execute(ddl)

                            self._update_progress(f"Created table: {schema}.{table_name}")
                        except Exception as e:
                            self.logger.warning(f"Table {schema}.{table_name}: {e}")

            return True, "Schema migration completed"

        except Exception as e:
            return False, f"Schema migration error: {e}"

    def _get_table_ddl(self, schema: str, table_name: str) -> str:
        """Generate CREATE TABLE statement for a table."""
        columns = []
        
        if self._source_conn is None:
            return ""

        with self._source_conn.cursor() as cur:
            # Get columns with their definitions
            cur.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    is_nullable,
                    column_default,
                    udt_schema,
                    udt_name
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table_name))

            for row in cur.fetchall():
                col_name, data_type, char_len, num_prec, num_scale, nullable, default, udt_schema, udt_name = row

                # Build column type
                if data_type == 'USER-DEFINED':
                    col_type = f'"{udt_schema}"."{udt_name}"'
                elif data_type in ('character varying', 'varchar'):
                    col_type = f'VARCHAR({char_len})' if char_len else 'VARCHAR'
                elif data_type == 'character':
                    col_type = f'CHAR({char_len})' if char_len else 'CHAR'
                elif data_type == 'numeric':
                    if num_prec and num_scale:
                        col_type = f'NUMERIC({num_prec},{num_scale})'
                    elif num_prec:
                        col_type = f'NUMERIC({num_prec})'
                    else:
                        col_type = 'NUMERIC'
                elif data_type == 'ARRAY':
                    col_type = f'"{udt_name}"'
                else:
                    col_type = data_type.upper()

                # Build column definition
                col_def = f'"{col_name}" {col_type}'

                if nullable == 'NO':
                    col_def += ' NOT NULL'

                if default:
                    col_def += f' DEFAULT {default}'

                columns.append(col_def)

            # Get primary key
            cur.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass
                AND i.indisprimary
                ORDER BY array_position(i.indkey, a.attnum)
            """, (f'{schema}.{table_name}',))

            pk_cols = [row[0] for row in cur.fetchall()]

            if pk_cols:
                pk_def = 'PRIMARY KEY (' + ', '.join(f'"{c}"' for c in pk_cols) + ')'
                columns.append(pk_def)

        ddl = f'CREATE TABLE "{schema}"."{table_name}" (\n  '
        ddl += ',\n  '.join(columns)
        ddl += '\n)'

        return ddl

    def migrate_data(self, batch_size: int = 10000) -> Tuple[bool, str]:
        """
        Migrate data from source to target using COPY for efficiency.
        """
        try:
            schemas = self.get_schemas()
            total_tables = 0
            migrated_tables = 0
            total_rows = 0

            # Count tables
            for schema in schemas:
                tables = self.get_tables(schema)
                total_tables += len(tables)

            self._update_progress(f"Migrating data for {total_tables} tables...")

            for schema in schemas:
                tables = self.get_tables(schema)

                for table in tables:
                    try:
                        rows = self._copy_table_data(schema, table.name, batch_size)
                        total_rows += rows
                        migrated_tables += 1
                        self._update_progress(
                            f"Migrated {table.name}: {rows} rows",
                            migrated_tables,
                            total_tables
                        )
                    except Exception as e:
                        self.logger.warning(f"Data for {schema}.{table.name}: {e}")

            return True, f"Data migration completed: {total_rows} rows in {migrated_tables} tables"

        except Exception as e:
            return False, f"Data migration error: {e}"

    def _copy_table_data(self, schema: str, table_name: str, batch_size: int = 10000) -> int:
        """Copy data for a single table using COPY command."""
        total_rows = 0
        
        if self._source_conn is None or self._target_conn is None:
            return 0

        # Use COPY for efficient data transfer
        with self._source_conn.cursor() as src_cur:
            # Create a buffer
            buffer = StringIO()

            # Copy data to buffer
            copy_sql = sql.SQL("COPY {}.{} TO STDOUT WITH (FORMAT CSV, HEADER FALSE, NULL '\\N')").format(
                sql.Identifier(schema),
                sql.Identifier(table_name)
            )
            src_cur.copy_expert(copy_sql, buffer)

            # Get row count
            buffer.seek(0)
            content = buffer.read()
            if content.strip():
                total_rows = content.count('\n')

                # Copy from buffer to target
                buffer.seek(0)
                with self._target_conn.cursor() as tgt_cur:
                    copy_sql = sql.SQL("COPY {}.{} FROM STDIN WITH (FORMAT CSV, HEADER FALSE, NULL '\\N')").format(
                        sql.Identifier(schema),
                        sql.Identifier(table_name)
                    )
                    tgt_cur.copy_expert(copy_sql, buffer)
                    self._target_conn.commit()

        return total_rows

    def migrate_constraints(self) -> Tuple[bool, str]:
        """Migrate foreign keys and other constraints."""
        try:
            self._update_progress("Migrating constraints...")
            
            if self._source_conn is None or self._target_conn is None:
                return False, "Not connected to databases"

            with self._source_conn.cursor() as src_cur:
                # Get foreign keys
                src_cur.execute("""
                    SELECT
                        tc.table_schema,
                        tc.table_name,
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_schema AS foreign_table_schema,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
                """)

                for row in src_cur.fetchall():
                    schema, table, constraint, column, fk_schema, fk_table, fk_column = row
                    try:
                        with self._target_conn.cursor() as tgt_cur:
                            tgt_cur.execute(
                                sql.SQL("""
                                    ALTER TABLE {}.{} 
                                    ADD CONSTRAINT {} 
                                    FOREIGN KEY ({}) 
                                    REFERENCES {}.{} ({})
                                """).format(
                                    sql.Identifier(schema),
                                    sql.Identifier(table),
                                    sql.Identifier(constraint),
                                    sql.Identifier(column),
                                    sql.Identifier(fk_schema),
                                    sql.Identifier(fk_table),
                                    sql.Identifier(fk_column)
                                )
                            )
                        self._update_progress(f"Created FK: {constraint}")
                    except Exception as e:
                        self.logger.warning(f"FK {constraint}: {e}")

            return True, "Constraints migration completed"

        except Exception as e:
            return False, f"Constraints migration error: {e}"

    def migrate_indexes(self) -> Tuple[bool, str]:
        """Migrate indexes."""
        try:
            self._update_progress("Migrating indexes...")
            
            if self._source_conn is None or self._target_conn is None:
                return False, "Not connected to databases"

            with self._source_conn.cursor() as src_cur:
                # Get index definitions
                src_cur.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                    AND indexname NOT LIKE '%_pkey'
                """)

                for schema, table, index_name, index_def in src_cur.fetchall():
                    try:
                        with self._target_conn.cursor() as tgt_cur:
                            # Replace schema in index definition if needed
                            tgt_cur.execute(index_def)
                        self._update_progress(f"Created index: {index_name}")
                    except Exception as e:
                        self.logger.warning(f"Index {index_name}: {e}")

            return True, "Index migration completed"

        except Exception as e:
            return False, f"Index migration error: {e}"

    def update_sequences(self) -> Tuple[bool, str]:
        """Update sequence values to match source."""
        try:
            self._update_progress("Updating sequences...")
            
            if self._source_conn is None or self._target_conn is None:
                return False, "Not connected to databases"

            with self._source_conn.cursor() as src_cur:
                src_cur.execute("""
                    SELECT schemaname, sequencename, last_value
                    FROM pg_sequences
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                """)

                for schema, name, last_value in src_cur.fetchall():
                    if last_value:
                        try:
                            with self._target_conn.cursor() as tgt_cur:
                                tgt_cur.execute(
                                    sql.SQL("SELECT setval({}, {})").format(
                                        sql.Literal(f'{schema}.{name}'),
                                        sql.Literal(last_value)
                                    )
                                )
                            self._update_progress(f"Updated sequence: {name} = {last_value}")
                        except Exception as e:
                            self.logger.warning(f"Sequence {name}: {e}")

            return True, "Sequence update completed"

        except Exception as e:
            return False, f"Sequence update error: {e}"

    def run_migration(self) -> Tuple[bool, str]:
        """
        Run the complete migration process.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Connect
            success, msg = self.connect()
            if not success:
                return False, msg

            self._update_progress("Starting Python-based migration...")

            # 1. Migrate schema
            success, msg = self.migrate_schema()
            if not success:
                return False, msg

            # 2. Migrate data
            success, msg = self.migrate_data()
            if not success:
                return False, msg

            # 3. Migrate constraints
            success, msg = self.migrate_constraints()
            if not success:
                self.logger.warning(f"Constraint migration had issues: {msg}")

            # 4. Migrate indexes
            success, msg = self.migrate_indexes()
            if not success:
                self.logger.warning(f"Index migration had issues: {msg}")

            # 5. Update sequences
            success, msg = self.update_sequences()
            if not success:
                self.logger.warning(f"Sequence update had issues: {msg}")

            self._update_progress("Migration completed successfully!")
            return True, "Migration completed successfully"

        except Exception as e:
            return False, f"Migration error: {e}"
        finally:
            self.disconnect()
