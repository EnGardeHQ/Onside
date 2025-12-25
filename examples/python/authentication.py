"""
Capilytics API - Python Authentication Examples
"""

import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.getenv('CAPILYTICS_API_URL', 'http://localhost:8000/api/v1')


class CapilyticsAuthClient:
    """Simple authentication client for Capilytics API"""

    def __init__(self, base_url=None):
        self.base_url = base_url or BASE_URL
        self.token = None
        self.token_expires_at = None

    def register(self, email, password, name):
        """Register a new user account"""
        response = requests.post(
            f'{self.base_url}/auth/register',
            json={
                'email': email,
                'password': password,
                'name': name
            }
        )
        response.raise_for_status()
        return response.json()

    def login(self, email, password):
        """Login and store access token"""
        response = requests.post(
            f'{self.base_url}/auth/login',
            json={
                'email': email,
                'password': password
            }
        )
        response.raise_for_status()

        data = response.json()
        self.token = data['access_token']
        # Set expiration to 23 hours (default is 24 hours)
        self.token_expires_at = datetime.utcnow() + timedelta(hours=23)

        return data

    def is_authenticated(self):
        """Check if client has valid token"""
        if not self.token:
            return False
        if self.token_expires_at and datetime.utcnow() >= self.token_expires_at:
            return False
        return True

    def get_headers(self):
        """Get authorization headers"""
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please login first.")

        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def logout(self):
        """Logout (invalidate token)"""
        if not self.is_authenticated():
            return

        response = requests.post(
            f'{self.base_url}/auth/logout',
            headers=self.get_headers()
        )
        response.raise_for_status()

        self.token = None
        self.token_expires_at = None

        return response.json()

    def get_user_profile(self, user_id):
        """Get user profile"""
        response = requests.get(
            f'{self.base_url}/auth/users/{user_id}',
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == '__main__':
    # Initialize client
    client = CapilyticsAuthClient()

    # Example 1: Register new user
    try:
        user = client.register(
            email='newuser@example.com',
            password='SecurePassword123!',
            name='John Doe'
        )
        print(f"Registered user: {user['email']} (ID: {user['id']})")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print("User already exists")
        else:
            raise

    # Example 2: Login
    login_result = client.login(
        email='user@example.com',
        password='SecurePassword123!'
    )
    print(f"\nLogged in as: {login_result['user']['name']}")
    print(f"Token: {login_result['access_token'][:50]}...")

    # Example 3: Check authentication status
    print(f"\nAuthenticated: {client.is_authenticated()}")

    # Example 4: Get user profile
    user_profile = client.get_user_profile(login_result['user']['id'])
    print(f"\nUser Profile:")
    print(f"  Name: {user_profile['name']}")
    print(f"  Email: {user_profile['email']}")
    print(f"  Role: {user_profile['role']}")
    print(f"  Created: {user_profile['created_at']}")

    # Example 5: Logout
    logout_result = client.logout()
    print(f"\n{logout_result['message']}")
    print(f"Authenticated: {client.is_authenticated()}")
