import grpc
import pytest
from fastapi.testclient import TestClient
from main import app
import user_auth_pb2_grpc

@pytest.fixture
def client(monkeypatch):
    # Nadpisanie get_auth_stub(), aby używać lokalnego serwera gRPC
    def mock_get_auth_stub():
        channel = grpc.insecure_channel("localhost:50051")
        return user_auth_pb2_grpc.AuthUserServiceStub(channel)
    
    monkeypatch.setattr("routers.autorizationAndAuthentication.get_auth_stub", mock_get_auth_stub)
    return TestClient(app)

def test_register_user_success(client):
    response = client.post("/auth/register", json={"username": "new_user", "password": "password"})
    assert response.status_code == 201
    assert response.json()["user_id"] == "test_user_id"
    assert "password_reset_code" in response.json()

def test_register_user_already_exists(client):
    response = client.post("/auth/register", json={"username": "existing_user", "password": "password"})
    assert response.status_code == 403
    assert response.json()["detail"] == "User with username: existing_user already exists"