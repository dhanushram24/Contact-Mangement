"""
Contact Management API - Enhanced with Token Expiration
FastAPI application with automatic token validation on protected routes
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
import sys
from pathlib import Path
from datetime import datetime, timedelta 
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

app = FastAPI(
    title="Contact Management API",
    version="2.0.0",
    description="API for contact management system with JWT token expiration"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services with custom token expiration (15 minutes)
db = get_db(DatabaseConfig())
auth_service = get_auth_service(AuthConfig(token_expire_minutes=15))

# Pydantic Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    access_token: str
    token_type: str
    username: str
    client_id: int
    database: str
    contacts: list
    contact_count: int
    expires_in: int
    expires_at: str

class TokenVerifyResponse(BaseModel):
    valid: bool
    username: str
    database: str
    expires_at: str
    seconds_remaining: int
    minutes_remaining: int

class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    expires_at: str


# ============== PUBLIC ENDPOINTS (No Authentication) ==============

@app.get("/")
def root():
    """API health check"""
    return {
        "status": "API is running",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": ["JWT Authentication", "Token Expiration", "Protected Routes"]
    }


@app.get("/ui")
def get_ui():
    """Serve the UI"""
    return FileResponse("templates/index.html")


@app.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    """
    Authenticate user and return access token with contacts
    
    Flow:
    1. Validate user exists in master database
    2. Get client data and database name
    3. Verify user in child database
    4. Fetch all contacts
    5. Generate JWT token (expires in 15 minutes)
    """
    try:
        print(f"\n=== Login Attempt ===")
        print(f"Username: {data.username}")

        # Step 1: Get user from master database
        user_data = MasterQueries.get_user_by_username(db, data.username)
        
        if not user_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid username"
            )
        
        print(f"User found: {user_data}")
        
        # Step 2: Get client ID and find client data
        client_id = user_data.get("clientID")
        if not client_id:
            raise HTTPException(
                status_code=404,
                detail="Client ID not found for this user"
            )
        
        print(f"Client ID: {client_id}")
        
        # Try to get client data
        client_data = MasterQueries.get_client_by_id(db, client_id)
        if not client_data:
            client_data = MasterQueries.get_client_by_username(db, data.username)
        if not client_data:
            all_clients = MasterQueries.get_all_valid_clients(db)
            if all_clients:
                client_data = all_clients[0]
        
        if not client_data:
            raise HTTPException(
                status_code=404,
                detail=f"Client data not found for clientID: {client_id}"
            )
        
        # Get child database name
        child_dbname = client_data.get("dbname")
        if not child_dbname:
            raise HTTPException(
                status_code=404,
                detail="Database name not found for this client"
            )
        
        print(f"Child database: {child_dbname}")
        
        # Step 3: Verify user exists in child database
        contact_data = ContactQueries.get_contact_by_username(db, child_dbname, data.username)
        
        if not contact_data:
            raise HTTPException(
                status_code=401,
                detail="User not found in contact database"
            )
        
        # Step 4: Get all contacts
        contacts = ContactQueries.get_all_contacts(db, child_dbname)
        print(f"Found {len(contacts)} contacts")
        
        # Step 5: Generate authentication token
        auth_response = auth_service.authenticate_user(
            username=data.username,
            password=data.password,
            user_data=user_data,
            database=child_dbname
        )
        
        # Calculate expiration time
        expire_time = datetime.utcnow() + timedelta(minutes=auth_service.token_manager.config.token_expire_minutes)
        
        # Return complete response
        return {
            "success": True,
            "access_token": auth_response["access_token"],
            "token_type": auth_response["token_type"],
            "username": data.username,
            "client_id": client_id,
            "database": child_dbname,
            "contacts": contacts,
            "contact_count": len(contacts),
            "expires_in": auth_response["expires_in"],
            "expires_at": expire_time.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n=== Login Error ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )


@app.post("/verify-token", response_model=TokenVerifyResponse)
def verify_token(token: str):
    """
    Verify JWT token and return detailed expiration information
    """
    try:
        expiry_info = auth_service.token_manager.get_token_expiry_info(token)
        
        if expiry_info.get("is_expired"):
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        
        payload = auth_service.validate_token(token)
        
        return {
            "valid": True,
            "username": payload.get("sub"),
            "database": payload.get("dbname"),
            "expires_at": expiry_info.get("expires_at"),
            "seconds_remaining": expiry_info.get("seconds_remaining"),
            "minutes_remaining": expiry_info.get("minutes_remaining")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )


# ============== PROTECTED ENDPOINTS (Require Valid Token) ==============

@app.get("/protected/profile")
async def get_profile(current_user: dict = Depends(auth_service.get_current_user)):
    """
    Protected route example - Get current user profile
    Token is automatically validated, raises 401 if expired
    """
    return {
        "message": "This is a protected route",
        "user": current_user
    }


@app.get("/protected/contacts")
async def get_user_contacts(current_user: dict = Depends(auth_service.get_current_user)):
    """
    Protected route - Get contacts for authenticated user
    """
    try:
        database = current_user.get("database")
        contacts = ContactQueries.get_all_contacts(db, database)
        
        return {
            "username": current_user.get("username"),
            "database": database,
            "count": len(contacts),
            "contacts": contacts
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching contacts: {str(e)}"
        )


@app.get("/protected/contacts/active")
async def get_user_active_contacts(current_user: dict = Depends(auth_service.get_current_user)):
    """Protected route - Get only active contacts"""
    try:
        database = current_user.get("database")
        contacts = ContactQueries.get_active_contacts(db, database)
        
        return {
            "username": current_user.get("username"),
            "database": database,
            "count": len(contacts),
            "contacts": contacts
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching active contacts: {str(e)}"
        )


@app.get("/protected/contacts/search")
async def search_user_contacts(
    name: str,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Protected route - Search contacts by name"""
    try:
        database = current_user.get("database")
        contacts = ContactQueries.search_contacts_by_name(db, database, name)
        
        return {
            "username": current_user.get("username"),
            "database": database,
            "query": name,
            "count": len(contacts),
            "contacts": contacts
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching contacts: {str(e)}"
        )


@app.post("/protected/refresh-token", response_model=TokenRefreshResponse)
async def refresh_token(current_user: dict = Depends(auth_service.get_current_user)):
    """
    Refresh the authentication token
    Returns a new token with extended expiration
    """
    try:
        # Create new token
        new_token = auth_service.token_manager.create_token(
            username=current_user.get("username"),
            database=current_user.get("database"),
            client_id=current_user.get("client_id")
        )
        
        expire_time = datetime.utcnow() + timedelta(
            minutes=auth_service.token_manager.config.token_expire_minutes
        )
        
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": auth_service.token_manager.config.token_expire_minutes * 60,
            "expires_at": expire_time.isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing token: {str(e)}"
        )


# ============== DEBUG ENDPOINTS ==============

@app.get("/debug/structure")
def debug_structure():
    """Debug endpoint: Check table structures"""
    try:
        master_db = "ondem_master_rb"
        
        clientdata_cols = DebugQueries.get_table_structure(db, master_db, "pm1clientdata")
        userdata_cols = DebugQueries.get_table_structure(db, master_db, "pm1userdata")
        clientdata_sample = DebugQueries.get_table_sample(db, master_db, "pm1clientdata", 3)
        userdata_sample = MasterQueries.get_user_by_username(db, "abadmin")
        
        return {
            "pm1clientdata_columns": clientdata_cols,
            "pm1userdata_columns": userdata_cols,
            "pm1clientdata_sample": clientdata_sample,
            "pm1userdata_sample": userdata_sample
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Debug error: {str(e)}"
        )


@app.get("/debug/check-user/{username}")
def debug_check_user(username: str):
    """Debug endpoint: Check user data across tables"""
    try:
        user_data = MasterQueries.get_user_by_username(db, username)
        all_clients = MasterQueries.get_all_clients(db)
        
        return {
            "username": username,
            "pm1userdata": user_data,
            "all_pm1clientdata": all_clients
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Debug error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    from datetime import timedelta
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True
    )