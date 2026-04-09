"""
Database management utilities for PostgreSQL Migrator.
Handles creating, dropping, and preparing databases for migration.
"""

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import Tuple, Optional, Dict, Any

from .utils import parse_dsn, build_dsn
from .logger import get_logger


class DatabaseManager:
    """
    Manages PostgreSQL database creation and deletion.
    Connects to the postgres system database to perform operations.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        user: str = "postgres",
        password: str = "",
    ):
        """
        Initialize database manager.
        
        Args:
            host: Database server host
            port: Database server port
            user: PostgreSQL superuser username
            password: Password for the user
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.logger = get_logger()
        self._connection = None
    
    def _get_system_dsn(self) -> str:
        """Get DSN for postgres system database."""
        return build_dsn(
            host=self.host,
            port=self.port,
            dbname="postgres",
            user=self.user,
            password=self.password,
        )
    
    def _connect_system(self) -> bool:
        """Connect to postgres system database."""
        try:
            self._connection = psycopg2.connect(self._get_system_dsn())
            self._connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            return True
        except Exception as e:
            self.logger.error(f"Cannot connect to system database: {e}")
            return False
    
    def _disconnect(self):
        """Disconnect from database."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def database_exists(self, dbname: str) -> bool:
        """
        Check if a database exists.
        
        Args:
            dbname: Name of the database to check
            
        Returns:
            True if database exists, False otherwise
        """
        try:
            if not self._connection:
                if not self._connect_system():
                    return False
            
            with self._connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (dbname,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Error checking database existence: {e}")
            return False
    
    def create_database(
        self,
        dbname: str,
        owner: Optional[str] = None,
        encoding: str = "UTF8",
        template: str = "template0",
    ) -> Tuple[bool, str]:
        """
        Create a new database.
        
        Args:
            dbname: Name of the database to create
            owner: Owner of the database (defaults to current user)
            encoding: Database encoding
            template: Template database to use
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self._connection:
                if not self._connect_system():
                    return False, "Cannot connect to system database"
            
            owner = owner or self.user
            
            with self._connection.cursor() as cursor:
                # Build CREATE DATABASE query
                query = sql.SQL(
                    "CREATE DATABASE {dbname} OWNER {owner} ENCODING {encoding} TEMPLATE {template}"
                ).format(
                    dbname=sql.Identifier(dbname),
                    owner=sql.Identifier(owner),
                    encoding=sql.Literal(encoding),
                    template=sql.Identifier(template),
                )
                
                cursor.execute(query)
            
            self.logger.success(f"Database '{dbname}' created successfully")
            return True, f"Database '{dbname}' created"
            
        except psycopg2.errors.DuplicateDatabase:
            return False, f"Database '{dbname}' already exists"
        except Exception as e:
            self.logger.error(f"Error creating database: {e}")
            return False, str(e)
    
    def drop_database(self, dbname: str, force: bool = True) -> Tuple[bool, str]:
        """
        Drop an existing database.
        
        Args:
            dbname: Name of the database to drop
            force: Force drop by terminating connections
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self._connection:
                if not self._connect_system():
                    return False, "Cannot connect to system database"
            
            # Safety check - don't drop system databases
            if dbname.lower() in ("postgres", "template0", "template1"):
                return False, f"Cannot drop system database '{dbname}'"
            
            with self._connection.cursor() as cursor:
                # Terminate existing connections if force is True
                if force:
                    cursor.execute(
                        """
                        SELECT pg_terminate_backend(pid) 
                        FROM pg_stat_activity 
                        WHERE datname = %s AND pid <> pg_backend_pid()
                        """,
                        (dbname,)
                    )
                    self.logger.info(f"Terminated active connections to '{dbname}'")
                
                # Drop the database
                query = sql.SQL("DROP DATABASE IF EXISTS {dbname}").format(
                    dbname=sql.Identifier(dbname)
                )
                cursor.execute(query)
            
            self.logger.success(f"Database '{dbname}' dropped successfully")
            return True, f"Database '{dbname}' dropped"
            
        except psycopg2.errors.ObjectInUse:
            return False, f"Database '{dbname}' is in use. Close all connections first."
        except Exception as e:
            self.logger.error(f"Error dropping database: {e}")
            return False, str(e)
    
    def clear_database_content(self, dbname: str) -> Tuple[bool, str]:
        """
        Clear all content from a database without dropping the database itself.
        Drops all user schemas (excluding system schemas) and recreates public schema.
        
        Args:
            dbname: Name of the database to clear
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Connect directly to the target database
            target_dsn = build_dsn(
                host=self.host,
                port=self.port,
                dbname=dbname,
                user=self.user,
                password=self.password,
            )
            
            target_conn = psycopg2.connect(target_dsn)
            target_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            with target_conn.cursor() as cursor:
                # Get all user schemas (excluding system schemas)
                cursor.execute("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                    AND schema_name NOT LIKE 'pg_temp_%'
                    AND schema_name NOT LIKE 'pg_toast_temp_%'
                """)
                schemas = [row[0] for row in cursor.fetchall()]
                
                # Drop each schema with CASCADE
                for schema in schemas:
                    self.logger.info(f"Dropping schema '{schema}'...")
                    cursor.execute(
                        sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                            sql.Identifier(schema)
                        )
                    )
                
                # Recreate public schema
                cursor.execute("CREATE SCHEMA IF NOT EXISTS public")
                cursor.execute("GRANT ALL ON SCHEMA public TO PUBLIC")
                
            target_conn.close()
            
            self.logger.success(f"Database '{dbname}' content cleared successfully")
            return True, f"Database '{dbname}' content cleared"
            
        except Exception as e:
            self.logger.error(f"Error clearing database content: {e}")
            return False, str(e)
    
    def prepare_target_database(
        self,
        dbname: str,
        drop_if_exists: bool = True,
        owner: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Prepare target database for migration.
        If exists and drop_if_exists is True, clears all content (schemas/tables).
        If not exists, creates the database.
        
        Args:
            dbname: Name of the target database
            drop_if_exists: If True, clear existing database content
            owner: Owner of the database
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self._connection:
                if not self._connect_system():
                    return False, "Cannot connect to system database"
            
            exists = self.database_exists(dbname)
            
            if exists:
                if drop_if_exists:
                    self.logger.info(f"Database '{dbname}' exists, clearing content...")
                    success, msg = self.clear_database_content(dbname)
                    if not success:
                        return False, f"Failed to clear database content: {msg}"
                    return True, f"Target database '{dbname}' is ready (content cleared)"
                else:
                    return False, f"Database '{dbname}' already exists"
            else:
                self.logger.info(f"Database '{dbname}' does not exist, creating...")
            
            # Create the database
            success, msg = self.create_database(dbname, owner=owner)
            if success:
                return True, f"Target database '{dbname}' is ready"
            else:
                return False, f"Failed to create database: {msg}"
                
        except Exception as e:
            self.logger.error(f"Error preparing target database: {e}")
            return False, str(e)
        finally:
            self._disconnect()
    
    def __enter__(self):
        self._connect_system()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._disconnect()
        return False


def prepare_target_db(
    host: str,
    port: int,
    dbname: str,
    user: str,
    password: str,
    drop_if_exists: bool = True,
) -> Tuple[bool, str]:
    """
    Convenience function to prepare target database.
    
    Args:
        host: Database server host
        port: Database server port
        dbname: Name of the target database
        user: PostgreSQL user
        password: Password
        drop_if_exists: If True, drop existing database first
        
    Returns:
        Tuple of (success, message)
    """
    manager = DatabaseManager(
        host=host,
        port=port,
        user=user,
        password=password,
    )
    
    return manager.prepare_target_database(
        dbname=dbname,
        drop_if_exists=drop_if_exists,
        owner=user,
    )


def prepare_target_db_from_dsn(dsn: str, drop_if_exists: bool = True) -> Tuple[bool, str]:
    """
    Prepare target database from DSN string.
    
    Args:
        dsn: Database connection string
        drop_if_exists: If True, drop existing database first
        
    Returns:
        Tuple of (success, message)
    """
    params = parse_dsn(dsn)
    
    return prepare_target_db(
        host=params.get("host", "localhost"),
        port=int(params.get("port", 5432)),
        dbname=params.get("dbname", "postgres"),
        user=params.get("user", "postgres"),
        password=params.get("password", ""),
        drop_if_exists=drop_if_exists,
    )
