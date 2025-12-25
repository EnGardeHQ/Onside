/**
 * Auth API
 * Authentication and user management endpoints
 */

import { apiClient } from './client';
import { User, LoginCredentials, RegisterData, AuthTokens } from '../types';

export const authApi = {
  /**
   * Login with username and password
   */
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    return apiClient.post<AuthTokens>('/auth/login', {
      email: credentials.username,
      password: credentials.password,
    });
  },

  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<User> {
    return apiClient.post<User>('/auth/register', data);
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/auth/me');
  },

  /**
   * Logout (clear tokens)
   */
  async logout(): Promise<void> {
    apiClient.clearToken();
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    return apiClient.post<AuthTokens>('/auth/refresh', { refresh_token: refreshToken });
  },

  /**
   * Update user profile
   */
  async updateProfile(userId: number, data: Partial<User>): Promise<User> {
    return apiClient.put<User>(`/auth/users/${userId}`, data);
  },

  /**
   * Change password
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    return apiClient.post<void>('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },
};
