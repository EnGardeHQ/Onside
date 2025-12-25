#!/bin/bash

# Capilytics API - cURL Authentication Examples

BASE_URL="${CAPILYTICS_API_URL:-http://localhost:8000/api/v1}"

echo "=== Capilytics API Authentication Examples ==="
echo

# Example 1: Register new user
echo "1. Registering new user..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePassword123!",
    "name": "John Doe"
  }')

echo "Response: $REGISTER_RESPONSE"
echo

# Example 2: Login
echo "2. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }')

# Extract token from response
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "Login successful!"
echo "Token: ${TOKEN:0:50}..."
echo

# Example 3: Get user profile
echo "3. Getting user profile..."
USER_ID=$(echo $LOGIN_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

PROFILE_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "Profile: $PROFILE_RESPONSE"
echo

# Example 4: Logout
echo "4. Logging out..."
LOGOUT_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/logout" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "Response: $LOGOUT_RESPONSE"
echo

# Save token to file for other scripts
echo "$TOKEN" > .token
echo "Token saved to .token file"
