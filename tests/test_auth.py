import pytest
from fastapi import status
from src.auth.models import User
from src.auth.security import create_access_token
from datetime import datetime, timezone

def test_register_user_success(client, db_session):
    response = client.post("/api/auth/register", json={
        "email": "newuser@example.com",
        "password": "strongpassword123",
        "name": "New User"
    })

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["email"] == "newuser@example.com"
    assert "password" not in data

def test_register_user_duplicate_email(client, db_session, mock_user):
    response = client.post("/api/auth/register", json={
        "email": mock_user.email,
        "password": "strongpassword123",
        "name": "Another User"
    })

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "Email already registered" in data["detail"]

def test_login_user_success(auth_client, db_session, mock_user):
    response = auth_client.post("/api/auth/login", json={
        "email": mock_user.email,
        "password": "test123"  # Match password in conftest.py
    })

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == mock_user.email

def test_login_user_invalid_credentials(auth_client, db_session, mock_user):
    response = auth_client.post("/api/auth/login", json={
        "email": mock_user.email,
        "password": "wrongpassword"
    })

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "Incorrect email or password" in data["detail"]

def test_login_user_nonexistent(auth_client, db_session):
    response = auth_client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "anypassword"
    })

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "Incorrect email or password" in data["detail"]

def test_logout_user_success(auth_client, mock_token):
    response = auth_client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Successfully logged out"

def test_logout_user_no_token(client):
    response = client.post("/api/auth/logout")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "Not authenticated" in data["detail"]

def test_get_user_profile_success(auth_client, mock_user, mock_token):
    response = auth_client.get(
        f"/api/auth/users/{mock_user.id}",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == mock_user.id
    assert data["email"] == mock_user.email
    assert "password" not in data

def test_get_user_profile_not_found(auth_client, mock_token):
    response = auth_client.get(
        "/api/auth/users/999999",
        headers={"Authorization": f"Bearer {mock_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "User not found" in data["detail"]

def test_get_user_profile_unauthorized(auth_client, mock_user, mock_token_other_user, db_session):
    # Debug: Check user IDs in database
    all_users = db_session.query(User).all()
    print("\nAll users in database:")
    for user in all_users:
        print(f"User ID: {user.id}, Email: {user.email}, Role: {user.role}")

    # Try to access mock_user's profile with other_user's token
    response = auth_client.get(
        f"/api/auth/users/{mock_user.id}",
        headers={"Authorization": f"Bearer {mock_token_other_user}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "Not authorized" in data["detail"]

def test_get_user_profile_admin_access(auth_client, mock_user, mock_token_admin):
    response = auth_client.get(
        f"/api/auth/users/{mock_user.id}",
        headers={"Authorization": f"Bearer {mock_token_admin}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == mock_user.id
    assert data["email"] == mock_user.email
