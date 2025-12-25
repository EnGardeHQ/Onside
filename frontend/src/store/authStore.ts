/**
 * Auth Store
 * Global authentication state management with Zustand
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, AuthTokens } from '../types';
import { authApi, apiClient } from '../api';

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
  setUser: (user: User) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        try {
          set({ isLoading: true, error: null });

          const tokens = await authApi.login({ username, password });

          // Set token in API client
          apiClient.setToken(tokens.access_token);

          // Load user data
          const user = await authApi.getCurrentUser();

          set({
            user,
            tokens,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          let errorMessage = 'Login failed';

          if (typeof error.detail === 'string') {
            errorMessage = error.detail;
          } else if (Array.isArray(error.detail)) {
            errorMessage = error.detail.map((e: any) => e.msg || e.message).join(', ');
          } else if (error.message) {
            errorMessage = error.message;
          }

          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
          });
          throw error;
        }
      },

      register: async (email: string, username: string, password: string) => {
        try {
          set({ isLoading: true, error: null });

          const user = await authApi.register({ email, username, password });

          // Auto-login after registration
          await get().login(username, password);
        } catch (error: any) {
          let errorMessage = 'Registration failed';

          if (typeof error.detail === 'string') {
            errorMessage = error.detail;
          } else if (Array.isArray(error.detail)) {
            errorMessage = error.detail.map((e: any) => e.msg || e.message).join(', ');
          } else if (error.message) {
            errorMessage = error.message;
          }

          set({
            error: errorMessage,
            isLoading: false,
          });
          throw error;
        }
      },

      logout: () => {
        authApi.logout();
        set({
          user: null,
          tokens: null,
          isAuthenticated: false,
          error: null,
        });
      },

      loadUser: async () => {
        try {
          const tokens = get().tokens;
          if (!tokens?.access_token) {
            return;
          }

          set({ isLoading: true });

          // Ensure token is set
          apiClient.setToken(tokens.access_token);

          const user = await authApi.getCurrentUser();

          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          // Token invalid or expired
          get().logout();
          set({ isLoading: false });
        }
      },

      setUser: (user: User) => {
        set({ user });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
