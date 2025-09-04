"""
FastAPI Authentication Router
Provides JWT authentication endpoints for login, logout, refresh, and user management
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie
from pydantic import BaseModel, Field
from passlib.context import CryptContext

from src.auth.jwt_handler import jwt_handler
from src.auth.dependencies import (
    get_current_user,
    get_current_user_optional, 
    verify_refresh_token,
    login_rate_limiter,
    check_auth_enabled
)
from src.services.async_base_service import AsyncBaseService
from src.utils.logger import get_logger

logger = get_logger("mvidarr.api.fastapi.auth")

# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)
    remember_me: bool = False

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str
    user_id: Optional[int] = None

class RefreshRequest(BaseModel):
    refresh_token: str

class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    username: str
    user_id: Optional[int] = None
    is_authenticated: bool = True

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

class AuthStatusResponse(BaseModel):
    authenticated: bool
    auth_enabled: bool
    username: Optional[str] = None
    user_id: Optional[int] = None

# Create router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])

class AsyncAuthService(AsyncBaseService):
    """Async authentication service for FastAPI routes"""
    
    def __init__(self):
        super().__init__("mvidarr.api.fastapi.auth_service")
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate user with username and password using current system"""
        try:
            # Get stored credentials using current settings structure
            query = """
                SELECT setting_key, setting_value FROM settings 
                WHERE setting_key IN ('simple_auth_username', 'simple_auth_password')
            """
            result = await self.execute_query(query)
            
            settings = {row['setting_key']: row['setting_value'] for row in result}
            stored_username = settings.get('simple_auth_username')
            stored_password_hash = settings.get('simple_auth_password')
            
            if not stored_username or not stored_password_hash:
                self.logger.warning("No credentials configured")
                return None
                
            # Check username
            if username != stored_username:
                self.logger.warning(f"Username mismatch: {username} != {stored_username}")
                return None
                
            # Check password - current system uses SHA256
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if password_hash != stored_password_hash:
                self.logger.warning("Password verification failed")
                return None
                
            self.logger.info(f"User authenticated: {username}")
            return {
                "username": username,
                "user_id": 1,  # Single user system
                "is_active": True
            }
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return None

    async def update_user_password(self, username: str, new_password: str) -> bool:
        """Update user password with bcrypt hash"""
        try:
            # Hash password using bcrypt for future security
            password_hash = jwt_handler.hash_password(new_password)
            
            # Update password in settings
            query = """
                UPDATE settings 
                SET setting_value = %s 
                WHERE setting_key = 'simple_auth_password'
            """
            await self.execute_query(query, [password_hash])
            
            # Also mark that we're now using bcrypt
            bcrypt_query = """
                INSERT INTO settings (setting_key, setting_value) 
                VALUES ('password_hash_type', 'bcrypt')
                ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
            """
            await self.execute_query(bcrypt_query)
            
            self.logger.info(f"Password updated for user: {username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating password: {e}")
            return False

# Global service instance
auth_service = AsyncAuthService()

@auth_router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    request: Request,
    _rate_limit: bool = Depends(login_rate_limiter)
):
    """
    Authenticate user and return JWT tokens
    """
    try:
        # Check if auth is enabled
        if not await check_auth_enabled():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authentication is not enabled"
            )
        
        # Authenticate user
        user = await auth_service.authenticate_user(login_data.username, login_data.password)
        if not user:
            # Log failed attempt for rate limiting
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(f"Failed login attempt for {login_data.username} from {client_ip}")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create token pair
        expires_delta = timedelta(days=7) if login_data.remember_me else None
        token_data = await jwt_handler.create_token_pair(
            username=user["username"],
            user_id=user["user_id"]
        )
        
        # Set secure HTTP-only cookies for tokens
        response.set_cookie(
            key="access_token",
            value=token_data["access_token"],
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=token_data["expires_in"]
        )
        
        response.set_cookie(
            key="refresh_token",
            value=token_data["refresh_token"],
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=token_data["refresh_expires_in"]
        )
        
        logger.info(f"User {user['username']} logged in successfully")
        
        return LoginResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            username=user["username"],
            user_id=user["user_id"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@auth_router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    refresh_data: RefreshRequest,
    response: Response,
    refresh_token_cookie: Optional[str] = Cookie(None)
):
    """
    Refresh access token using refresh token
    """
    try:
        # Get refresh token from request body or cookie
        refresh_token = refresh_data.refresh_token or refresh_token_cookie
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token required"
            )
        
        # Verify and refresh token
        new_token_data = await jwt_handler.refresh_access_token(refresh_token)
        
        if not new_token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update access token cookie
        response.set_cookie(
            key="access_token",
            value=new_token_data["access_token"],
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=jwt_handler.access_token_expire_minutes * 60
        )
        
        logger.debug("Access token refreshed successfully")
        
        return RefreshResponse(
            access_token=new_token_data["access_token"],
            token_type=new_token_data["token_type"],
            expires_in=jwt_handler.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@auth_router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    user: Optional[dict] = Depends(get_current_user_optional),
    access_token_cookie: Optional[str] = Cookie(None),
    refresh_token_cookie: Optional[str] = Cookie(None)
):
    """
    Logout user and revoke tokens
    """
    try:
        # Get tokens from request
        tokens_to_revoke = []
        
        # Get token from Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            tokens_to_revoke.append(auth_header.split(" ")[1])
        
        # Get tokens from cookies
        if access_token_cookie:
            tokens_to_revoke.append(access_token_cookie)
        if refresh_token_cookie:
            tokens_to_revoke.append(refresh_token_cookie)
        
        # Revoke all found tokens
        for token in tokens_to_revoke:
            await jwt_handler.revoke_token(token)
        
        # Clear cookies
        response.delete_cookie(key="access_token", samesite="lax")
        response.delete_cookie(key="refresh_token", samesite="lax")
        
        username = user["username"] if user else "unknown"
        logger.info(f"User {username} logged out successfully")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Even if token revocation fails, clear cookies
        response.delete_cookie(key="access_token", samesite="lax")
        response.delete_cookie(key="refresh_token", samesite="lax")
        
        return {"message": "Logged out"}

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """
    Get current user information
    """
    return UserResponse(
        username=user["username"],
        user_id=user.get("user_id"),
        is_authenticated=True
    )

@auth_router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Get authentication status
    """
    auth_enabled = await check_auth_enabled()
    
    return AuthStatusResponse(
        authenticated=user is not None,
        auth_enabled=auth_enabled,
        username=user["username"] if user else None,
        user_id=user.get("user_id") if user else None
    )

@auth_router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    user: dict = Depends(get_current_user)
):
    """
    Change user password
    """
    try:
        # Verify current password
        current_user = await auth_service.authenticate_user(
            user["username"], 
            password_data.current_password
        )
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Verify new password confirmation
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password confirmation does not match"
            )
        
        # Check password strength
        is_strong, message = jwt_handler.is_password_strong(password_data.new_password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Update password
        success = await auth_service.update_user_password(
            user["username"], 
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        logger.info(f"Password changed for user: {user['username']}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@auth_router.post("/check")
async def check_authentication(user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Check if user is authenticated (compatibility endpoint)
    """
    auth_enabled = await check_auth_enabled()
    
    if not auth_enabled:
        return {
            "authenticated": True,  # If auth is disabled, consider everyone authenticated
            "auth_enabled": False,
            "username": "system"
        }
    
    return {
        "authenticated": user is not None,
        "auth_enabled": True,
        "username": user["username"] if user else None,
        "user_id": user.get("user_id") if user else None
    }