"""
Example Usage of Contact Management Library
Demonstrates how to use the library independently
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from lib import (
    get_db,
    get_auth_service,
    MasterQueries,
    ContactQueries,
    DebugQueries,
    DatabaseConfig,
    AuthConfig
)


def example_1_basic_connection():
    """Example 1: Basic database connection and query"""
    print("\n=== Example 1: Basic Connection ===")
    
    # Get database instance
    db = get_db()
    
    # Query using context manager
    with db.get_cursor("ondem_master_rb") as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM pm1userdata")
        result = cursor.fetchone()
        print(f"Total users in master DB: {result['count']}")


def example_2_query_library():
    """Example 2: Using the query library"""
    print("\n=== Example 2: Query Library ===")
    
    db = get_db()
    
    # Get user by username
    user = MasterQueries.get_user_by_username(db, "abadmin")
    if user:
        print(f"Found user: {user['username']}")
        print(f"Client ID: {user.get('clientID')}")
    
    # Get all valid clients
    clients = MasterQueries.get_all_valid_clients(db)
    print(f"Total valid clients: {len(clients)}")
    
    for client in clients[:3]:  # Show first 3
        print(f"  - {client.get('dbname')}")


def example_3_contacts():
    """Example 3: Working with contacts"""
    print("\n=== Example 3: Contacts ===")
    
    db = get_db()
    
    # First, get a valid database name
    clients = MasterQueries.get_all_valid_clients(db)
    if not clients:
        print("No valid databases found")
        return
    
    database = clients[0].get('dbname')
    print(f"Using database: {database}")
    
    # Get all contacts
    contacts = ContactQueries.get_all_contacts(db, database)
    print(f"Total contacts: {len(contacts)}")
    
    # Get active contacts only
    active = ContactQueries.get_active_contacts(db, database)
    print(f"Active contacts: {len(active)}")
    
    # Show first contact
    if contacts:
        contact = contacts[0]
        print(f"\nFirst contact:")
        print(f"  Name: {contact.get('f_name')} {contact.get('l_name')}")
        print(f"  Email: {contact.get('email')}")
        print(f"  Status: {contact.get('status')}")


def example_4_authentication():
    """Example 4: JWT token creation and verification"""
    print("\n=== Example 4: Authentication ===")
    
    auth = get_auth_service()
    
    # Create a token
    token = auth.token_manager.create_token(
        username="testuser",
        database="test_db",
        role="admin"
    )
    print(f"Generated token: {token[:50]}...")
    
    # Verify the token
    try:
        payload = auth.validate_token(token)
        print(f"Token valid!")
        print(f"  Username: {payload['sub']}")
        print(f"  Database: {payload['dbname']}")
        print(f"  Expires: {payload['exp']}")
        
        # Check if expired
        is_expired = auth.token_manager.is_token_expired(token)
        print(f"  Is expired: {is_expired}")
    except Exception as e:
        print(f"Token validation failed: {e}")


def example_5_transaction():
    """Example 5: Using transactions (demo only, no actual write)"""
    print("\n=== Example 5: Transactions ===")
    
    db = get_db()
    
    # Get a database
    clients = MasterQueries.get_all_valid_clients(db)
    if not clients:
        print("No valid databases found")
        return
    
    database = clients[0].get('dbname')
    
    print(f"Transaction example (read-only demo):")
    print(f"Database: {database}")
    
    # This would be how you'd do a transaction
    # Commented out to avoid actual writes
    
    # try:
    #     with db.transaction(database) as cursor:
    #         # Insert a new contact
    #         cursor.execute(
    #             "INSERT INTO pm1contact_rep (f_name, l_name, email, user_name, status) VALUES (%s, %s, %s, %s, %s)",
    #             ("John", "Doe", "john@example.com", "jdoe", 2)
    #         )
    #         contact_id = cursor.lastrowid
    #         
    #         # Update something
    #         cursor.execute(
    #             "UPDATE pm1contact_rep SET status = %s WHERE id = %s",
    #             (1, contact_id)
    #         )
    #         
    #         # If any error occurs, automatic rollback happens
    #         print(f"Contact created with ID: {contact_id}")
    # except Exception as e:
    #     print(f"Transaction failed (rolled back): {e}")
    
    print("(Actual transaction code commented out to prevent writes)")


def example_6_search():
    """Example 6: Searching contacts"""
    print("\n=== Example 6: Search ===")
    
    db = get_db()
    
    # Get a database
    clients = MasterQueries.get_all_valid_clients(db)
    if not clients:
        print("No valid databases found")
        return
    
    database = clients[0].get('dbname')
    
    # Get a contact to search for
    contacts = ContactQueries.get_all_contacts(db, database)
    if not contacts:
        print("No contacts to search")
        return
    
    # Get first name from first contact
    search_name = contacts[0].get('f_name', '')
    if not search_name:
        print("No name to search for")
        return
    
    print(f"Searching for: {search_name}")
    results = ContactQueries.search_contacts_by_name(db, database, search_name)
    print(f"Found {len(results)} results")
    
    for result in results[:3]:  # Show first 3
        print(f"  - {result.get('f_name')} {result.get('l_name')}")


def example_7_debug():
    """Example 7: Using debug queries"""
    print("\n=== Example 7: Debug Queries ===")
    
    db = get_db()
    
    # Get table structure
    columns = DebugQueries.get_table_structure(db, "ondem_master_rb", "pm1userdata")
    print(f"pm1userdata columns: {len(columns)}")
    for col in columns[:5]:  # Show first 5
        print(f"  - {col['Field']}: {col['Type']}")
    
    # Get list of tables
    tables = DebugQueries.get_database_tables(db, "ondem_master_rb")
    print(f"\nTables in ondem_master_rb: {len(tables)}")
    for table in tables[:5]:  # Show first 5
        print(f"  - {table}")


def example_8_custom_config():
    """Example 8: Using custom configuration"""
    print("\n=== Example 8: Custom Configuration ===")
    
    # Custom database config
    db_config = DatabaseConfig(
        host="localhost",
        user="root",
        password="",
        connect_timeout=10
    )
    
    # Custom auth config
    auth_config = AuthConfig(
        secret_key="my-custom-secret",
        algorithm="HS256",
        token_expire_minutes=60  # 1 hour
    )
    
    print(f"Database config:")
    print(f"  Host: {db_config.host}")
    print(f"  Timeout: {db_config.connect_timeout}s")
    
    print(f"\nAuth config:")
    print(f"  Algorithm: {auth_config.algorithm}")
    print(f"  Expiry: {auth_config.token_expire_minutes} minutes")


def main():
    """Run all examples"""
    print("=" * 60)
    print("Contact Management Library - Usage Examples")
    print("=" * 60)
    
    try:
        example_1_basic_connection()
        example_2_query_library()
        example_3_contacts()
        example_4_authentication()
        example_5_transaction()
        example_6_search()
        example_7_debug()
        example_8_custom_config()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()