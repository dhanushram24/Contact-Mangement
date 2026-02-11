"""
Contact Management API - Production Ready
FastAPI application with comprehensive error handling and logging
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
import sys
import logging
from pathlib import Path

# Setup path for lib imports
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Contact Management API",
    version="3.0.0",
    description="Production-ready API for contact management system with JWT authentication",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
db = get_db(DatabaseConfig())
auth_service = get_auth_service(AuthConfig(token_expire_minutes=60))

# Pydantic Models
class LoginRequest(BaseModel):
    username: str
    password: str

    @validator('username')
    def username_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()


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


class ErrorResponse(BaseModel):
    detail: str
    timestamp: str
    path: str


# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


# PUBLIC ENDPOINTS
@app.get("/")
def root():
    """API health check"""
    return {
        "status": "healthy",
        "service": "Contact Management API",
        "version": "3.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "JWT Authentication",
            "Token Expiration",
            "Protected Routes",
            "Comprehensive Error Handling"
        ]
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    try:
        MasterQueries.get_all_valid_clients(db)
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ui")
def get_ui():
    """Serve the web UI"""
    return FileResponse("templates/index.html")


@app.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    """Authenticate user and return access token with contacts"""
    try:
        logger.info(f"Login attempt for user: {data.username}")

        user_data = MasterQueries.get_user_by_username(db, data.username)
        
        if not user_data:
            logger.warning(f"User not found: {data.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        client_id = user_data.get("clientID")
        if not client_id:
            logger.error(f"No client ID found for user: {data.username}")
            raise HTTPException(status_code=404, detail="Client configuration not found")
        
        client_data = MasterQueries.get_client_by_id(db, client_id)
        if not client_data:
            client_data = MasterQueries.get_client_by_username(db, data.username)
        if not client_data:
            all_clients = MasterQueries.get_all_valid_clients(db)
            if all_clients:
                client_data = all_clients[0]
        
        if not client_data:
            logger.error(f"No client data found for clientID: {client_id}")
            raise HTTPException(status_code=404, detail="Client configuration not found")
        
        child_dbname = client_data.get("dbname")
        if not child_dbname:
            logger.error(f"No database name in client data for: {data.username}")
            raise HTTPException(status_code=404, detail="Database configuration not found")
        
        logger.info(f"User {data.username} mapped to database: {child_dbname}")
        
        contact_data = ContactQueries.get_contact_by_username(db, child_dbname, data.username)
        
        if not contact_data:
            logger.warning(f"User {data.username} not found in contact database")
            raise HTTPException(status_code=401, detail="User not found in contact database")
        
        contacts = ContactQueries.get_all_contacts(db, child_dbname)
        logger.info(f"Loaded {len(contacts)} contacts for user: {data.username}")
        
        auth_response = auth_service.authenticate_user(
            username=data.username,
            password=data.password,
            user_data=user_data,
            database=child_dbname
        )
        
        expire_time = datetime.utcnow() + timedelta(
            minutes=auth_service.token_manager.config.token_expire_minutes
        )
        
        logger.info(f"Login successful for user: {data.username}")
        
        return LoginResponse(
            success=True,
            access_token=auth_response["access_token"],
            token_type=auth_response["token_type"],
            username=data.username,
            client_id=client_id,
            database=child_dbname,
            contacts=contacts,
            contact_count=len(contacts),
            expires_in=auth_response["expires_in"],
            expires_at=expire_time.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {data.username}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@app.post("/verify-token", response_model=TokenVerifyResponse)
def verify_token(token: str):
    """Verify JWT token and return detailed expiration information"""
    try:
        expiry_info = auth_service.token_manager.get_token_expiry_info(token)
        
        if expiry_info.get("is_expired"):
            raise HTTPException(status_code=401, detail="Token has expired")
        
        payload = auth_service.validate_token(token)
        
        return TokenVerifyResponse(
            valid=True,
            username=payload.get("sub"),
            database=payload.get("dbname"),
            expires_at=expiry_info.get("expires_at"),
            seconds_remaining=expiry_info.get("seconds_remaining"),
            minutes_remaining=expiry_info.get("minutes_remaining")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


# PROTECTED ENDPOINTS
@app.get("/protected/profile")
async def get_profile(current_user: dict = Depends(auth_service.get_current_user)):
    """Get current user profile"""
    return {
        "message": "Profile data",
        "user": current_user,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/protected/contacts")
async def get_user_contacts(current_user: dict = Depends(auth_service.get_current_user)):
    """Get contacts for authenticated user"""
    try:
        database = current_user.get("database")
        contacts = ContactQueries.get_all_contacts(db, database)
        
        logger.info(f"Fetched {len(contacts)} contacts for user: {current_user.get('username')}")
        
        return {
            "username": current_user.get("username"),
            "database": database,
            "count": len(contacts),
            "contacts": contacts
        }
    except Exception as e:
        logger.error(f"Error fetching contacts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching contacts: {str(e)}")


@app.get("/protected/contacts/active")
async def get_user_active_contacts(current_user: dict = Depends(auth_service.get_current_user)):
    """Get only active contacts"""
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
        logger.error(f"Error fetching active contacts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching active contacts: {str(e)}")


@app.get("/protected/tickets")
async def get_tickets_with_contacts(
    status_id: int = None,
    limit: int = 100,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get tickets with contact information"""
    try:
        database = current_user.get("database")
        results = ContactQueries.get_tickets_with_contacts(
            db, database, status_id=status_id, limit=limit
        )
        
        logger.info(f"Fetched {len(results)} tickets for user: {current_user.get('username')}")
        
        return {
            "username": current_user.get("username"),
            "database": database,
            "count": len(results),
            "tickets": results
        }
    except Exception as e:
        logger.error(f"Error fetching tickets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching tickets: {str(e)}")


@app.get("/protected/contacts/search")
async def search_user_contacts(
    name: str,
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Search contacts by name"""
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
        logger.error(f"Error searching contacts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching contacts: {str(e)}")


@app.post("/protected/refresh-token", response_model=TokenRefreshResponse)
async def refresh_token(current_user: dict = Depends(auth_service.get_current_user)):
    """Refresh authentication token"""
    try:
        new_token = auth_service.token_manager.create_token(
            username=current_user.get("username"),
            database=current_user.get("database"),
            client_id=current_user.get("client_id")
        )
        
        expire_time = datetime.utcnow() + timedelta(
            minutes=auth_service.token_manager.config.token_expire_minutes
        )
        
        logger.info(f"Token refreshed for user: {current_user.get('username')}")
        
        return TokenRefreshResponse(
            access_token=new_token,
            token_type="bearer",
            expires_in=auth_service.token_manager.config.token_expire_minutes * 60,
            expires_at=expire_time.isoformat()
        )
    except Exception as e:
        logger.error(f"Error refreshing token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error refreshing token: {str(e)}")


# DEBUG ENDPOINTS
@app.get("/debug/structure")
def debug_structure():
    """Debug: Check database table structures"""
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
        logger.error(f"Debug error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")


@app.get("/debug/check-user/{username}")
def debug_check_user(username: str):
    """Debug: Check user data across tables"""
    try:
        user_data = MasterQueries.get_user_by_username(db, username)
        all_clients = MasterQueries.get_all_clients(db)
        
        return {
            "username": username,
            "pm1userdata": user_data,
            "all_pm1clientdata": all_clients
        }
    except Exception as e:
        logger.error(f"Debug error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("=" * 60)
    logger.info("Contact Management API Starting")
    logger.info("=" * 60)
    logger.info(f"Version: 3.0.0")
    logger.info(f"Token Expiration: {auth_service.token_manager.config.token_expire_minutes} minutes")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Contact Management API Shutting Down")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )