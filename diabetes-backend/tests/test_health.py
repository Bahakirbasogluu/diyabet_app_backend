"""
Health Data API Tests
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health data endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_health_record(self, authenticated_client):
        """Test creating a health record"""
        client, _ = authenticated_client
        
        health_data = {
            "type": "glucose",
            "value": 120.5,
            "note": "Test measurement"
        }
        
        response = await client.post("/health", json=health_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "glucose"
        assert data["value"] == 120.5
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_create_health_record_unauthenticated(self, client: AsyncClient):
        """Test creating health record without auth"""
        health_data = {
            "type": "glucose",
            "value": 120.5
        }
        response = await client.post("/health", json=health_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_health_history(self, authenticated_client):
        """Test getting health history"""
        client, _ = authenticated_client
        
        # Create some records first
        for value in [100, 110, 120]:
            await client.post("/health", json={"type": "glucose", "value": value})
        
        # Get history
        response = await client.get("/health/history")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3
    
    @pytest.mark.asyncio
    async def test_get_health_history_filtered(self, authenticated_client):
        """Test getting filtered health history"""
        client, _ = authenticated_client
        
        # Create records of different types
        await client.post("/health", json={"type": "glucose", "value": 120})
        await client.post("/health", json={"type": "weight", "value": 70})
        
        # Get filtered history
        response = await client.get("/health/history?record_type=glucose")
        
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["type"] == "glucose"
    
    @pytest.mark.asyncio
    async def test_get_health_stats(self, authenticated_client):
        """Test getting health statistics"""
        client, _ = authenticated_client
        
        # Create some records
        for value in [100, 110, 120, 130, 140]:
            await client.post("/health", json={"type": "glucose", "value": value})
        
        # Get stats
        response = await client.get("/health/stats?record_type=glucose")
        
        assert response.status_code == 200
        data = response.json()
        assert "average" in data
        assert "min" in data
        assert "max" in data
        assert "count" in data
    
    @pytest.mark.asyncio
    async def test_delete_health_record(self, authenticated_client):
        """Test deleting a health record"""
        client, _ = authenticated_client
        
        # Create a record
        create_response = await client.post(
            "/health",
            json={"type": "glucose", "value": 120}
        )
        record_id = create_response.json()["id"]
        
        # Delete it
        delete_response = await client.delete(f"/health/{record_id}")
        assert delete_response.status_code == 200
        
        # Verify it's deleted
        history_response = await client.get("/health/history")
        history = history_response.json()
        record_ids = [item["id"] for item in history["items"]]
        assert record_id not in record_ids
    
    @pytest.mark.asyncio
    async def test_invalid_health_value(self, authenticated_client):
        """Test creating health record with invalid value"""
        client, _ = authenticated_client
        
        invalid_data = {
            "type": "glucose",
            "value": -10  # Negative value
        }
        
        response = await client.post("/health", json=invalid_data)
        assert response.status_code in [400, 422]
