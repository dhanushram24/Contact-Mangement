"""
Database Connection Library
Handles all database connections and connection pooling
"""
import pymysql
from typing import Optional
from contextlib import contextmanager


class DatabaseConfig:
    """Database configuration settings"""
    
    def __init__(
        self,
        host: str = "localhost",
        user: str = "root",
        password: str = "",
        charset: str = "utf8mb4",
        connect_timeout: int = 5
    ):
        self.host = host
        self.user = user
        self.password = password
        self.charset = charset
        self.connect_timeout = connect_timeout


class DatabaseConnection:
    """Manages database connections"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
    
    def get_connection(self, database: str):
        """
        Create a new database connection
        
        Args:
            database: Database name to connect to
            
        Returns:
            pymysql.Connection object
            
        Raises:
            Exception: If connection fails
        """
        try:
            connection = pymysql.connect(
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=database,
                charset=self.config.charset,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=self.config.connect_timeout
            )
            return connection
        except Exception as e:
            raise Exception(f"Database connection failed for '{database}': {str(e)}")
    
    @contextmanager
    def get_cursor(self, database: str):
        """
        Context manager for database cursor
        Automatically handles connection and cursor cleanup
        
        Usage:
            with db.get_cursor('mydb') as cursor:
                cursor.execute("SELECT * FROM users")
                results = cursor.fetchall()
        
        Args:
            database: Database name to connect to
            
        Yields:
            Database cursor
        """
        connection = None
        cursor = None
        try:
            connection = self.get_connection(database)
            cursor = connection.cursor()
            yield cursor
            connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    @contextmanager
    def transaction(self, database: str):
        """
        Context manager for database transactions
        Automatically commits on success, rolls back on error
        
        Usage:
            with db.transaction('mydb') as cursor:
                cursor.execute("INSERT INTO users ...")
                cursor.execute("UPDATE stats ...")
        
        Args:
            database: Database name to connect to
            
        Yields:
            Database cursor
        """
        connection = None
        cursor = None
        try:
            connection = self.get_connection(database)
            cursor = connection.cursor()
            yield cursor
            connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


# Singleton instance
_db_instance = None

def get_db(config: Optional[DatabaseConfig] = None) -> DatabaseConnection:
    """
    Get singleton database connection instance
    
    Args:
        config: Optional database configuration
        
    Returns:
        DatabaseConnection instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection(config)
    return _db_instance