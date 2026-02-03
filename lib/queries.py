'''

                            Online Python Compiler.
                Code, Compile, Run and Debug python program online.
Write your code in this editor and press "Run" button to execute it.

'''

"""
Database Queries Library - Dynamic Version
Contains all SQL queries with dynamic query building capabilities
"""
from typing import Dict, List, Optional, Any, Union
from .database import DatabaseConnection


class QueryBuilder:
    """Dynamic SQL query builder"""
    
    @staticmethod
    def build_select(
        table: str,
        columns: List[str] = None,
        where: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None
    ) -> tuple:
        """
        Build a dynamic SELECT query
        
        Args:
            table: Table name
            columns: List of columns to select (None = SELECT *)
            where: Dictionary of WHERE conditions {column: value}
            order_by: Column to order by (can include ASC/DESC)
            limit: LIMIT value
            offset: OFFSET value
            
        Returns:
            Tuple of (query_string, values_tuple)
        """
        # SELECT clause
        if columns:
            select_cols = ", ".join(columns)
        else:
            select_cols = "*"
        
        query = f"SELECT {select_cols} FROM {table}"
        values = []
        
        # WHERE clause
        if where:
            conditions = []
            for key, value in where.items():
                if value is None:
                    conditions.append(f"{key} IS NULL")
                elif isinstance(value, (list, tuple)):
                    placeholders = ", ".join(["%s"] * len(value))
                    conditions.append(f"{key} IN ({placeholders})")
                    values.extend(value)
                elif isinstance(value, dict):
                    # Support for operators: {'operator': '>=', 'value': 100}
                    operator = value.get('operator', '=')
                    conditions.append(f"{key} {operator} %s")
                    values.append(value.get('value'))
                else:
                    conditions.append(f"{key} = %s")
                    values.append(value)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        # ORDER BY clause
        if order_by:
            query += f" ORDER BY {order_by}"
        
        # LIMIT clause
        if limit:
            query += f" LIMIT {limit}"
        
        # OFFSET clause
        if offset:
            query += f" OFFSET {offset}"
        
        return query, tuple(values)
    
    @staticmethod
    def build_insert(table: str, data: Dict[str, Any]) -> tuple:
        """
        Build a dynamic INSERT query
        
        Args:
            table: Table name
            data: Dictionary of {column: value}
            
        Returns:
            Tuple of (query_string, values_tuple)
        """
        columns = list(data.keys())
        values = list(data.values())
        
        placeholders = ", ".join(["%s"] * len(values))
        columns_str = ", ".join(columns)
        
        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        
        return query, tuple(values)
    
    @staticmethod
    def build_update(table: str, data: Dict[str, Any], where: Dict[str, Any]) -> tuple:
        """
        Build a dynamic UPDATE query
        
        Args:
            table: Table name
            data: Dictionary of {column: new_value}
            where: Dictionary of WHERE conditions {column: value}
            
        Returns:
            Tuple of (query_string, values_tuple)
        """
        set_clauses = []
        values = []
        
        # SET clause
        for key, value in data.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        
        query = f"UPDATE {table} SET {', '.join(set_clauses)}"
        
        # WHERE clause
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = %s")
                values.append(value)
            
            query += " WHERE " + " AND ".join(conditions)
        
        return query, tuple(values)
    
    @staticmethod
    def build_delete(table: str, where: Dict[str, Any]) -> tuple:
        """
        Build a dynamic DELETE query
        
        Args:
            table: Table name
            where: Dictionary of WHERE conditions {column: value}
            
        Returns:
            Tuple of (query_string, values_tuple)
        """
        query = f"DELETE FROM {table}"
        values = []
        
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = %s")
                values.append(value)
            
            query += " WHERE " + " AND ".join(conditions)
        
        return query, tuple(values)


class MasterQueries:
    """Queries for the master database (ondem_master_rb)"""
    
    MASTER_DB = "ondem_master_rb"
    
    @staticmethod
    def get_user_by_username(db: DatabaseConnection, username: str) -> Optional[Dict]:
        """Get user data by username"""
        query, values = QueryBuilder.build_select(
            table="pm1userdata",
            where={"username": username}
        )
        with db.get_cursor(MasterQueries.MASTER_DB) as cursor:
            cursor.execute(query, values)
            return cursor.fetchone()
    
    @staticmethod
    def get_user_by_field(db: DatabaseConnection, field: str, value: Any) -> Optional[Dict]:
        """Get user by any field dynamically"""
        query, values = QueryBuilder.build_select(
            table="pm1userdata",
            where={field: value}
        )
        with db.get_cursor(MasterQueries.MASTER_DB) as cursor:
            cursor.execute(query, values)
            return cursor.fetchone()
    
    @staticmethod
    def get_users_by_criteria(
        db: DatabaseConnection,
        where: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = None
    ) -> List[Dict]:
        """Get users by dynamic criteria"""
        query, values = QueryBuilder.build_select(
            table="pm1userdata",
            where=where,
            order_by=order_by,
            limit=limit
        )
        with db.get_cursor(MasterQueries.MASTER_DB) as cursor:
            cursor.execute(query, values)
            return cursor.fetchall()
    
    @staticmethod
    def get_all_users(db: DatabaseConnection) -> List[Dict]:
        """Get all users"""
        return MasterQueries.get_users_by_criteria(db)
    
    @staticmethod
    def get_client_by_id(db: DatabaseConnection, client_id: int) -> Optional[Dict]:
        """Get client data by client ID"""
        query, values = QueryBuilder.build_select(
            table="pm1clientdata",
            where={"clientID": client_id}
        )
        with db.get_cursor(MasterQueries.MASTER_DB) as cursor:
            cursor.execute(query, values)
            return cursor.fetchone()
    
    @staticmethod
    def get_client_by_field(db: DatabaseConnection, field: str, value: Any) -> Optional[Dict]:
        """Get client by any field dynamically"""
        query, values = QueryBuilder.build_select(
            table="pm1clientdata",
            where={field: value}
        )
        with db.get_cursor(MasterQueries.MASTER_DB) as cursor:
            cursor.execute(query, values)
            return cursor.fetchone()
    
    @staticmethod
    def get_client_by_username(db: DatabaseConnection, username: str) -> Optional[Dict]:
        """Get client data by username or dbuser"""
        # For OR conditions, we need custom query
        query = "SELECT * FROM pm1clientdata WHERE username = %s OR dbuser = %s"
        with db.get_cursor(MasterQueries.MASTER_DB) as cursor:
            cursor.execute(query, (username, username))
            return cursor.fetchone()
    
    @staticmethod
    def get_clients_by_criteria(
        db: DatabaseConnection,
        where: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = None
    ) -> List[Dict]:
        """Get clients by dynamic criteria"""
        query, values = QueryBuilder.build_select(
            table="pm1clientdata",
            where=where,
            order_by=order_by,
            limit=limit
        )
        with db.get_cursor(MasterQueries.MASTER_DB) as cursor:
            cursor.execute(query, values)
            return cursor.fetchall()
    
    @staticmethod
    def get_all_valid_clients(db: DatabaseConnection) -> List[Dict]:
        """Get all clients with valid database names"""
        # Clients where dbname is not NULL and not empty
        query = "SELECT * FROM pm1clientdata WHERE dbname IS NOT NULL AND dbname != ''"
        with db.get_cursor(MasterQueries.MASTER_DB) as cursor:
            cursor.execute(query)
            return cursor.fetchall()
    
    @staticmethod
    def get_all_clients(db: DatabaseConnection) -> List[Dict]:
        """Get all client records"""
        return MasterQueries.get_clients_by_criteria(db)
    
    @staticmethod
    def create_user(db: DatabaseConnection, user_data: Dict[str, Any]) -> int:
        """Create a new user dynamically"""
        query, values = QueryBuilder.build_insert("pm1userdata", user_data)
        with db.transaction(MasterQueries.MASTER_DB) as cursor:
            cursor.execute(query, values)
            return cursor.lastrowid
    
    @staticmethod
    def update_user(
        db: DatabaseConnection,
        user_id: int,
        user_data: Dict[str, Any]
    ) -> bool:
        """Update user data dynamically"""
        query, values = QueryBuilder.build_update(
            table="pm1userdata",
            data=user_data,
            where={"id": user_id}
        )
        with db.transaction(MasterQueries.MASTER_DB) as cursor:
            cursor.execute(query, values)
            return cursor.rowcount > 0
    
    @staticmethod
    def delete_user(db: DatabaseConnection, user_id: int) -> bool:
        """Delete a user"""
        query, values = QueryBuilder.build_delete(
            table="pm1userdata",
            where={"id": user_id}
        )
        with db.transaction(MasterQueries.MASTER_DB) as cursor:
            cursor.execute(query, values)
            return cursor.rowcount > 0


class ContactQueries:
    """Queries for contact databases (child databases)"""
    
    @staticmethod
    def get_contact_by_username(
        db: DatabaseConnection,
        database: str,
        username: str
    ) -> Optional[Dict]:
        """Get contact by username from specific database"""
        query, values = QueryBuilder.build_select(
            table="pm1contact_rep",
            where={"user_name": username}
        )
        with db.get_cursor(database) as cursor:
            cursor.execute(query, values)
            return cursor.fetchone()
    
    @staticmethod
    def get_contact_by_field(
        db: DatabaseConnection,
        database: str,
        field: str,
        value: Any
    ) -> Optional[Dict]:
        """Get contact by any field dynamically"""
        query, values = QueryBuilder.build_select(
            table="pm1contact_rep",
            where={field: value}
        )
        with db.get_cursor(database) as cursor:
            cursor.execute(query, values)
            return cursor.fetchone()
    
    @staticmethod
    def get_contacts_by_criteria(
        db: DatabaseConnection,
        database: str,
        where: Dict[str, Any] = None,
        columns: List[str] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None
    ) -> List[Dict]:
        """Get contacts by dynamic criteria"""
        query, values = QueryBuilder.build_select(
            table="pm1contact_rep",
            columns=columns,
            where=where,
            order_by=order_by,
            limit=limit,
            offset=offset
        )
        with db.get_cursor(database) as cursor:
            cursor.execute(query, values)
            return cursor.fetchall()
    
    @staticmethod
    def get_all_contacts(db: DatabaseConnection, database: str) -> List[Dict]:
        """Get all contacts from specific database"""
        return ContactQueries.get_contacts_by_criteria(db, database)
    
    @staticmethod
    def get_active_contacts(db: DatabaseConnection, database: str) -> List[Dict]:
        """Get all active contacts (status = 2)"""
        return ContactQueries.get_contacts_by_criteria(
            db, database, where={"status": 2}
        )
    
    @staticmethod
    def get_contacts_by_status(
        db: DatabaseConnection,
        database: str,
        status: int
    ) -> List[Dict]:
        """Get contacts by status"""
        return ContactQueries.get_contacts_by_criteria(
            db, database, where={"status": status}
        )
    
    @staticmethod
    def get_contact_by_id(
        db: DatabaseConnection,
        database: str,
        contact_id: int
    ) -> Optional[Dict]:
        """Get contact by ID"""
        return ContactQueries.get_contact_by_field(
            db, database, "id", contact_id
        )
    
    @staticmethod
    def get_contacts_by_email(
        db: DatabaseConnection,
        database: str,
        email: str
    ) -> List[Dict]:
        """Get contacts by email"""
        return ContactQueries.get_contacts_by_criteria(
            db, database, where={"email": email}
        )
    
    @staticmethod
    def search_contacts_by_name(
        db: DatabaseConnection,
        database: str,
        name: str
    ) -> List[Dict]:
        """Search contacts by name (first or last)"""
        search_term = f"%{name}%"
        query = "SELECT * FROM pm1contact_rep WHERE f_name LIKE %s OR l_name LIKE %s"
        with db.get_cursor(database) as cursor:
            cursor.execute(query, (search_term, search_term))
            return cursor.fetchall()
    
    @staticmethod
    def search_contacts_advanced(
        db: DatabaseConnection,
        database: str,
        search_fields: Dict[str, str],
        match_all: bool = True
    ) -> List[Dict]:
        """
        Advanced search with LIKE operator on multiple fields
        
        Args:
            db: Database connection
            database: Database name
            search_fields: Dict of {field: search_term}
            match_all: If True, uses AND (default), if False uses OR
        """
        conditions = []
        values = []
        
        for field, term in search_fields.items():
            conditions.append(f"{field} LIKE %s")
            values.append(f"%{term}%")
        
        operator = " AND " if match_all else " OR "
        query = f"SELECT * FROM pm1contact_rep WHERE {operator.join(conditions)}"
        
        with db.get_cursor(database) as cursor:
            cursor.execute(query, tuple(values))
            return cursor.fetchall()
    
    @staticmethod
    def create_contact(
        db: DatabaseConnection,
        database: str,
        contact_data: Dict[str, Any]
    ) -> int:
        """Create a new contact dynamically"""
        # Add timestamps if not provided
        if 'creation_date' not in contact_data:
            contact_data['creation_date'] = 'NOW()'
        if 'modification_date' not in contact_data:
            contact_data['modification_date'] = 'NOW()'
        
        # Handle NOW() function calls
        data_copy = {}
        now_fields = []
        for key, value in contact_data.items():
            if value == 'NOW()':
                now_fields.append(key)
            else:
                data_copy[key] = value
        
        # Build query with NOW() handled specially
        columns = list(data_copy.keys()) + now_fields
        values = list(data_copy.values())
        
        placeholders = ["%s"] * len(data_copy) + ["NOW()"] * len(now_fields)
        
        query = f"""
            INSERT INTO pm1contact_rep ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        with db.transaction(database) as cursor:
            cursor.execute(query, tuple(values))
            return cursor.lastrowid
    
    @staticmethod
    def update_contact(
        db: DatabaseConnection,
        database: str,
        contact_id: int,
        contact_data: Dict[str, Any]
    ) -> bool:
        """Update an existing contact dynamically"""
        # Add modification timestamp
        contact_data['modification_date'] = 'NOW()'
        
        # Handle NOW() function calls
        data_copy = {}
        now_fields = []
        for key, value in contact_data.items():
            if value == 'NOW()':
                now_fields.append(key)
            else:
                data_copy[key] = value
        
        # Build SET clause
        set_clauses = [f"{key} = %s" for key in data_copy.keys()]
        set_clauses += [f"{key} = NOW()" for key in now_fields]
        
        query = f"""
            UPDATE pm1contact_rep 
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        
        values = list(data_copy.values()) + [contact_id]
        
        with db.transaction(database) as cursor:
            cursor.execute(query, tuple(values))
            return cursor.rowcount > 0
    
    @staticmethod
    def delete_contact(
        db: DatabaseConnection,
        database: str,
        contact_id: int
    ) -> bool:
        """Delete a contact"""
        query, values = QueryBuilder.build_delete(
            table="pm1contact_rep",
            where={"id": contact_id}
        )
        with db.transaction(database) as cursor:
            cursor.execute(query, values)
            return cursor.rowcount > 0
    
    @staticmethod
    def bulk_update_contacts(
        db: DatabaseConnection,
        database: str,
        where: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> int:
        """Bulk update contacts matching criteria"""
        query, values = QueryBuilder.build_update(
            table="pm1contact_rep",
            data=update_data,
            where=where
        )
        with db.transaction(database) as cursor:
            cursor.execute(query, values)
            return cursor.rowcount


class DebugQueries:
    """Queries for debugging and inspection"""
    
    @staticmethod
    def get_table_structure(
        db: DatabaseConnection,
        database: str,
        table: str
    ) -> List[Dict]:
        """Get table column structure"""
        with db.get_cursor(database) as cursor:
            cursor.execute(f"SHOW COLUMNS FROM {table}")
            return cursor.fetchall()
    
    @staticmethod
    def get_table_sample(
        db: DatabaseConnection,
        database: str,
        table: str,
        limit: int = 5
    ) -> List[Dict]:
        """Get sample data from table"""
        with db.get_cursor(database) as cursor:
            cursor.execute(f"SELECT * FROM {table} LIMIT {limit}")
            return cursor.fetchall()
    
    @staticmethod
    def get_database_tables(db: DatabaseConnection, database: str) -> List[str]:
        """Get all tables in database"""
        with db.get_cursor(database) as cursor:
            cursor.execute("SHOW TABLES")
            return [list(row.values())[0] for row in cursor.fetchall()]
    
    @staticmethod
    def execute_raw_query(
        db: DatabaseConnection,
        database: str,
        query: str,
        params: tuple = None
    ) -> List[Dict]:
        """Execute a raw SQL query (use with caution)"""
        with db.get_cursor(database) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    @staticmethod
    def get_table_row_count(
        db: DatabaseConnection,
        database: str,
        table: str,
        where: Dict[str, Any] = None
    ) -> int:
        """Get row count for a table with optional WHERE clause"""
        query = f"SELECT COUNT(*) as count FROM {table}"
        values = []
        
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = %s")
                values.append(value)
            query += " WHERE " + " AND ".join(conditions)
        
        with db.get_cursor(database) as cursor:
            cursor.execute(query, tuple(values))
            result = cursor.fetchone()
            return result['count'] if result else 0


class GenericQueries:
    """Generic queries that work with any table"""
    
    @staticmethod
    def select(
        db: DatabaseConnection,
        database: str,
        table: str,
        columns: List[str] = None,
        where: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None
    ) -> List[Dict]:
        """Generic SELECT query"""
        query, values = QueryBuilder.build_select(
            table=table,
            columns=columns,
            where=where,
            order_by=order_by,
            limit=limit,
            offset=offset
        )
        with db.get_cursor(database) as cursor:
            cursor.execute(query, values)
            return cursor.fetchall()
    
    @staticmethod
    def insert(
        db: DatabaseConnection,
        database: str,
        table: str,
        data: Dict[str, Any]
    ) -> int:
        """Generic INSERT query"""
        query, values = QueryBuilder.build_insert(table, data)
        with db.transaction(database) as cursor:
            cursor.execute(query, values)
            return cursor.lastrowid
    
    @staticmethod
    def update(
        db: DatabaseConnection,
        database: str,
        table: str,
        data: Dict[str, Any],
        where: Dict[str, Any]
    ) -> int:
        """Generic UPDATE query"""
        query, values = QueryBuilder.build_update(table, data, where)
        with db.transaction(database) as cursor:
            cursor.execute(query, values)
            return cursor.rowcount
    
    @staticmethod
    def delete(
        db: DatabaseConnection,
        database: str,
        table: str,
        where: Dict[str, Any]
    ) -> int:
        """Generic DELETE query"""
        query, values = QueryBuilder.build_delete(table, where)
        with db.transaction(database) as cursor:
            cursor.execute(query, values)
            return cursor.rowcount