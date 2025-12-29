"""Unit tests for core routes."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
from backend.app.routers.core.routes import router
from fastapi import FastAPI

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestCoreRoutes:
    """Test suite for core infrastructure routes."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/core/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data
        assert "environment" in data
    
    @patch('backend.app.routers.core.routes.scheduled_portfolio_job')
    def test_trigger_portfolio_calculation(self, mock_job):
        """Test manual portfolio calculation trigger."""
        response = client.get("/core/debug/trigger/calculate")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Portfolio calculation job triggered manually"
        mock_job.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open, read_data='line1\nline2\nline3\nline4\nline5\n')
    def test_read_scheduler_logs(self, mock_file):
        """Test reading scheduler logs."""
        response = client.get("/core/logs/scheduler?lines=3")
        
        assert response.status_code == 200
        lines = response.json()
        assert isinstance(lines, list)
        assert len(lines) == 3
        assert lines[-1] == 'line5\n'
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_read_scheduler_logs_not_found(self, mock_file):
        """Test scheduler logs when file doesn't exist."""
        response = client.get("/core/logs/scheduler")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch('builtins.open', new_callable=mock_open, read_data='app_line1\napp_line2\napp_line3\n')
    def test_read_app_logs(self, mock_file):
        """Test reading application logs."""
        response = client.get("/core/logs/app?lines=2")
        
        assert response.status_code == 200
        lines = response.json()
        assert isinstance(lines, list)
        assert len(lines) == 2
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_read_app_logs_not_found(self, mock_file):
        """Test app logs when file doesn't exist."""
        response = client.get("/core/logs/app")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_read_logs_default_lines(self):
        """Test logs endpoint with default lines parameter."""
        log_content = '\n'.join([f'line{i}' for i in range(100)])
        
        with patch('builtins.open', mock_open(read_data=log_content)):
            response = client.get("/core/logs/scheduler")
            
            assert response.status_code == 200
            # Default is 50 lines, but our mock has 100 lines total
            lines = response.json()
            assert isinstance(lines, list)
