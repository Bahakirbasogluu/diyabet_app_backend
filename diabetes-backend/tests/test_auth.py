"""
Authentication API Tests
"""

import pytest
from httpx import AsyncClient


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, test_user_data: dict):
        """Test successful user registration"""
        response = await client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user_data: dict):
        """Test registration with duplicate email"""
        # First registration
        await client.post("/auth/register", json=test_user_data)
        
        # Try to register again
        response = await client.post("/auth/register", json=test_user_data)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password"""
        weak_user = {
            "email": "weak@example.com",
            "password": "123",
            "name": "Weak User"
        }
        response = await client.post("/auth/register", json=weak_user)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email"""
        invalid_user = {
            "email": "not-an-email",
            "password": "StrongPassword123!",
            "name": "Invalid User"
        }
        response = await client.post("/auth/register", json=invalid_user)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user_data: dict):
        """Test successful login"""
        # Register first
        await client.post("/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user_data: dict):
        """Test login with wrong password"""
        # Register first
        await client.post("/auth/register", json=test_user_data)
        
        # Login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        }
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_me(self, authenticated_client):
        """Test get current user profile"""
        client, _ = authenticated_client
        
        response = await client.get("/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "name" in data
    
    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """Test get current user without authentication"""
        response = await client.get("/auth/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, test_user_data: dict):
        """Test token refresh"""
        # Register and get tokens
        register_response = await client.post("/auth/register", json=test_user_data)
        tokens = register_response.json()
        
        # Refresh
        refresh_response = await client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]}
        )
        
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]
    
    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token"""
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )
        assert response.status_code == 401
