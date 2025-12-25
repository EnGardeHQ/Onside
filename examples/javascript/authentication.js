/**
 * Capilytics API - JavaScript Authentication Examples
 */

const axios = require('axios');

const BASE_URL = process.env.CAPILYTICS_API_URL || 'http://localhost:8000/api/v1';

class CapilyticsAuthClient {
  constructor(baseUrl = BASE_URL) {
    this.baseUrl = baseUrl;
    this.token = null;
    this.tokenExpiresAt = null;
  }

  /**
   * Register a new user account
   */
  async register(email, password, name) {
    try {
      const response = await axios.post(`${this.baseUrl}/auth/register`, {
        email,
        password,
        name
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Login and store access token
   */
  async login(email, password) {
    try {
      const response = await axios.post(`${this.baseUrl}/auth/login`, {
        email,
        password
      });

      const data = response.data;
      this.token = data.access_token;

      // Set expiration to 23 hours (default is 24 hours)
      this.tokenExpiresAt = new Date(Date.now() + 23 * 60 * 60 * 1000);

      return data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Check if client has valid token
   */
  isAuthenticated() {
    if (!this.token) {
      return false;
    }
    if (this.tokenExpiresAt && new Date() >= this.tokenExpiresAt) {
      return false;
    }
    return true;
  }

  /**
   * Get authorization headers
   */
  getHeaders() {
    if (!this.isAuthenticated()) {
      throw new Error('Not authenticated. Please login first.');
    }

    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Logout (invalidate token)
   */
  async logout() {
    if (!this.isAuthenticated()) {
      return;
    }

    try {
      const response = await axios.post(
        `${this.baseUrl}/auth/logout`,
        {},
        { headers: this.getHeaders() }
      );

      this.token = null;
      this.tokenExpiresAt = null;

      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get user profile
   */
  async getUserProfile(userId) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/auth/users/${userId}`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Handle API errors
   */
  handleError(error) {
    if (error.response) {
      const message = error.response.data.detail || 'Unknown error';
      const status = error.response.status;
      return new Error(`API Error ${status}: ${message}`);
    } else if (error.request) {
      return new Error('No response from API server');
    } else {
      return error;
    }
  }
}

// Example usage
async function main() {
  const client = new CapilyticsAuthClient();

  try {
    // Example 1: Register new user
    console.log('Registering new user...');
    try {
      const user = await client.register(
        'newuser@example.com',
        'SecurePassword123!',
        'John Doe'
      );
      console.log(`Registered user: ${user.email} (ID: ${user.id})`);
    } catch (error) {
      if (error.message.includes('400')) {
        console.log('User already exists');
      } else {
        throw error;
      }
    }

    // Example 2: Login
    console.log('\nLogging in...');
    const loginResult = await client.login(
      'user@example.com',
      'SecurePassword123!'
    );
    console.log(`Logged in as: ${loginResult.user.name}`);
    console.log(`Token: ${loginResult.access_token.substring(0, 50)}...`);

    // Example 3: Check authentication status
    console.log(`\nAuthenticated: ${client.isAuthenticated()}`);

    // Example 4: Get user profile
    console.log('\nFetching user profile...');
    const userProfile = await client.getUserProfile(loginResult.user.id);
    console.log('User Profile:');
    console.log(`  Name: ${userProfile.name}`);
    console.log(`  Email: ${userProfile.email}`);
    console.log(`  Role: ${userProfile.role}`);
    console.log(`  Created: ${userProfile.created_at}`);

    // Example 5: Logout
    console.log('\nLogging out...');
    const logoutResult = await client.logout();
    console.log(logoutResult.message);
    console.log(`Authenticated: ${client.isAuthenticated()}`);

  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = CapilyticsAuthClient;
