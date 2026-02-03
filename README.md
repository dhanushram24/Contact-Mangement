# Contact Management System

A modular contact management system with authentication built using FastAPI, featuring a clean separation of concerns with reusable libraries.

## 📁 Project Structure

```
contact_management/
├── lib/                          # Reusable library modules
│   ├── __init__.py              # Library exports
│   ├── database.py              # Database connection handling
│   ├── queries.py               # All SQL queries organized
│   └── auth.py                  # Authentication & JWT management
├── static/                       # Frontend static files
│   ├── styles.css               # All CSS styling
│   └── app.js                   # Frontend JavaScript logic
├── templates/                    # HTML templates
│   └── index.html               # Login and contact display UI
├── main.py                       # FastAPI application
└── requirements.txt             # Python dependencies
```

## 🚀 Features

### Backend (Library-based Architecture)
- **Modular Database Library** - Reusable connection management with context managers
- **Organized Queries** - All SQL queries in one place, categorized by functionality
- **JWT Authentication** - Secure token-based authentication
- **Clean Separation** - Each concern (DB, Auth, Queries) in its own module

### Frontend
- **Separated Concerns** - CSS, JavaScript, and HTML in separate files
- **Modern UI** - Gradient design with smooth animations
- **Responsive Design** - Mobile-friendly interface
- **Session Management** - Automatic token storage and verification

## 📦 Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Database** (in `lib/database.py` if needed)
```python
config = DatabaseConfig(
    host="localhost",
    user="root",
    password="",  # Update with your password
    charset="utf8mb4"
)
```

3. **Run the Application**
```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

4. **Access the Application**
- UI: http://127.0.0.1:8000/ui
- API Docs: http://127.0.0.1:8000/docs

## 🔧 Library Usage

### Database Connection

```python
from lib import get_db, DatabaseConfig

# Get database instance
db = get_db()

# Use context manager for queries
with db.get_cursor('database_name') as cursor:
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()

# Use transaction context for writes
with db.transaction('database_name') as cursor:
    cursor.execute("INSERT INTO users ...")
```

### Query Library

```python
from lib import MasterQueries, ContactQueries

# Get user data
user = MasterQueries.get_user_by_username(db, "username")

# Get all contacts
contacts = ContactQueries.get_all_contacts(db, "database_name")

# Get active contacts only
active_contacts = ContactQueries.get_active_contacts(db, "database_name")

# Search contacts
results = ContactQueries.search_contacts_by_name(db, "database_name", "John")
```

### Authentication

```python
from lib import get_auth_service

auth = get_auth_service()

# Create token
token = auth.token_manager.create_token(
    username="user",
    database="db_name"
)

# Verify token
payload = auth.validate_token(token)

# Check expiration
is_expired = auth.token_manager.is_token_expired(token)
```

## 🔌 API Endpoints

### Authentication
- `POST /login` - Login and get access token
- `GET /verify-token` - Verify JWT token

### Contacts
- `GET /contacts/{database}` - Get all contacts
- `GET /contacts/{database}/active` - Get active contacts only
- `GET /contacts/{database}/search?name={name}` - Search contacts

### Debug
- `GET /debug/structure` - View database structure
- `GET /debug/check-user/{username}` - Check user data
- `GET /debug/databases` - List all databases

## 📝 Database Schema

### Master Database (ondem_master_rb)
- `pm1userdata` - User accounts
- `pm1clientdata` - Client information and database mappings

### Child Databases
- `pm1contact_rep` - Contact information

## 🎨 Customization

### Styling
All styles are in `static/styles.css` with CSS variables for easy theming:

```css
:root {
    --primary-gradient-start: #667eea;
    --primary-gradient-end: #764ba2;
    /* ... more variables */
}
```

### Configuration
Update configurations in library modules:

**Database Config** (`lib/database.py`):
```python
DatabaseConfig(
    host="localhost",
    user="root",
    password="your_password"
)
```

**Auth Config** (`lib/auth.py`):
```python
AuthConfig(
    secret_key="your-secret-key",
    token_expire_minutes=30
)
```

## 🧪 Example Usage

### Using the Library in Another Project

```python
# In your own project
from contact_management.lib import (
    get_db,
    MasterQueries,
    ContactQueries,
    get_auth_service
)

# Initialize
db = get_db()
auth = get_auth_service()

# Use the library
user = MasterQueries.get_user_by_username(db, "admin")
contacts = ContactQueries.get_all_contacts(db, "my_database")
token = auth.token_manager.create_token("user", "database")
```

### Adding New Queries

Add to `lib/queries.py`:

```python
class ContactQueries:
    # Add your query constant
    GET_CONTACTS_BY_DATE = "SELECT * FROM pm1contact_rep WHERE creation_date > %s"
    
    # Add your method
    @staticmethod
    def get_recent_contacts(db: DatabaseConnection, database: str, days: int):
        with db.get_cursor(database) as cursor:
            cursor.execute(
                "SELECT * FROM pm1contact_rep WHERE creation_date > DATE_SUB(NOW(), INTERVAL %s DAY)",
                (days,)
            )
            return cursor.fetchall()
```

## 🔒 Security Notes

- Change the `SECRET_KEY` in production
- Use environment variables for sensitive data
- Implement password hashing (currently not implemented)
- Add rate limiting for production use
- Enable HTTPS in production

## 📊 Features by Module

### Database Module (`lib/database.py`)
- ✅ Connection pooling capability
- ✅ Context managers for automatic cleanup
- ✅ Transaction support with automatic rollback
- ✅ Singleton pattern for connection reuse
- ✅ Configurable connection parameters

### Queries Module (`lib/queries.py`)
- ✅ Master database queries
- ✅ Contact CRUD operations
- ✅ Search and filter functions
- ✅ Debug and inspection queries
- ✅ Type-safe query methods

### Auth Module (`lib/auth.py`)
- ✅ JWT token generation
- ✅ Token validation and verification
- ✅ Expiration checking
- ✅ User session management
- ✅ Configurable token lifetime

## 🛠️ Development

### Running Tests
```bash
# Add your test framework
pytest tests/
```

### Code Style
```bash
# Format code
black .

# Check style
flake8 .
```

## 📄 License

This project is licensed under the MIT License.

## 👥 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues and questions, please create an issue in the repository.