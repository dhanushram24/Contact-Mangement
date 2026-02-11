"""
Enhanced Authentication Library
Handles JWT token creation, validation, expiration, and authentication dependencies
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt, JWTError
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


class AuthConfig:
    """Authentication configuration"""
    
    def __init__(
        self,
        secret_key: str = "paramantra-secret",
        algorithm: str = "HS256",
        token_expire_minutes: int = 30
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes


class TokenManager:
    """Manages JWT tokens"""
    
    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or AuthConfig()
    
    def create_token(self, username: str, database: str, **extra_data) -> str:
        """Create JWT token with user information"""
        expire = datetime.utcnow() + timedelta(minutes=self.config.token_expire_minutes)
        
        payload = {
            "sub": username,
            "dbname": database,
            "exp": expire,
            "iat": datetime.utcnow(),
            **extra_data
        }
        
        token = jwt.encode(
            payload,
            self.config.secret_key,
            algorithm=self.config.algorithm
        )
        
        return token
    
    def verify_token(self, token: str) -> Dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm]
            )
            
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                raise JWTError("Token has expired")
            
            return payload
        except JWTError as e:
            raise JWTError(f"Invalid token: {str(e)}")
    
    def get_username_from_token(self, token: str) -> Optional[str]:
        """Extract username from token"""
        try:
            payload = self.verify_token(token)
            return payload.get("sub")
        except JWTError:
            return None
    
    def get_database_from_token(self, token: str) -> Optional[str]:
        """Extract database name from token"""
        try:
            payload = self.verify_token(token)
            return payload.get("dbname")
        except JWTError:
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired"""
        try:
            payload = self.verify_token(token)
            exp = payload.get("exp")
            if exp:
                return datetime.utcnow().timestamp() > exp
            return True
        except JWTError:
            return True
    
    def get_token_expiry_info(self, token: str) -> Dict:
        """Get detailed token expiry information"""
        try:
            payload = self.verify_token(token)
            exp = payload.get("exp")
            iat = payload.get("iat")
            
            if exp:
                exp_datetime = datetime.fromtimestamp(exp)
                time_remaining = exp_datetime - datetime.utcnow()
                
                return {
                    "is_expired": time_remaining.total_seconds() <= 0,
                    "expires_at": exp_datetime.isoformat(),
                    "issued_at": datetime.fromtimestamp(iat).isoformat() if iat else None,
                    "seconds_remaining": max(0, int(time_remaining.total_seconds())),
                    "minutes_remaining": max(0, int(time_remaining.total_seconds() / 60))
                }
            return {"is_expired": True}
        except JWTError:
            return {"is_expired": True, "error": "Invalid token"}


class AuthenticationService:
    """Main authentication service"""
    
    def __init__(self, token_manager: Optional[TokenManager] = None):
        self.token_manager = token_manager or TokenManager()
        self.security = HTTPBearer()
    
    def authenticate_user(
        self,
        username: str,
        password: str,
        user_data: Dict,
        database: str
    ) -> Dict:
        """Authenticate user and create session"""
        access_token = self.token_manager.create_token(
            username=username,
            database=database,
            client_id=user_data.get("clientID")
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": username,
            "database": database,
            "expires_in": self.token_manager.config.token_expire_minutes * 60
        }
    
    def validate_token(self, token: str) -> Dict:
        """Validate token and return user info"""
        return self.token_manager.verify_token(token)
    
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> Dict:
        """FastAPI dependency to get current authenticated user"""
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = credentials.credentials
        
        try:
            payload = self.token_manager.verify_token(token)
            
            if self.token_manager.is_token_expired(token):
                raise HTTPException(
                    status_code=401,
                    detail="Token has expired. Please login again.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            return {
                "username": payload.get("sub"),
                "database": payload.get("dbname"),
                "client_id": payload.get("client_id"),
                "payload": payload
            }
        
        except JWTError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid authentication token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def create_token_dependency(self):
        """Create a dependency function for token validation"""
        async def verify_token_dependency(
            credentials: HTTPAuthorizationCredentials = Security(self.security)
        ):
            return await self.get_current_user(credentials)
        
        return verify_token_dependency


# Singleton instance
_auth_instance = None

def get_auth_service(config: Optional[AuthConfig] = None) -> AuthenticationService:
    """Get singleton authentication service instance"""
    global _auth_instance
    if _auth_instance is None:
        token_manager = TokenManager(config) if config else TokenManager()
        _auth_instance = AuthenticationService(token_manager)
    return _auth_instance