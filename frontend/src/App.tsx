/**
 * Main App Component
 * Application root with routing configuration
 */

import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './utils/queryClient';
import { useAuthStore } from './store/authStore';
import { ErrorBoundary } from './components/common';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { DashboardLayout } from './layouts/DashboardLayout';
import { LoginPage } from './pages/Login';
import { RegisterPage } from './pages/Register';
import { DashboardPage } from './pages/Dashboard';
import { CompetitorsPage } from './pages/Competitors';
import { ReportsPage } from './pages/Reports';
import { SEOAnalyticsPage } from './pages/SEOAnalytics';

const App: React.FC = () => {
  const { loadUser } = useAuthStore();

  useEffect(() => {
    // Attempt to load user on app mount
    loadUser();
  }, [loadUser]);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected routes */}
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <DashboardLayout />
                </ProtectedRoute>
              }
            >
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="competitors" element={<CompetitorsPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="seo-analytics" element={<SEOAnalyticsPage />} />
              <Route path="settings" element={<div>Settings Page Coming Soon</div>} />
              <Route index element={<Navigate to="/dashboard" replace />} />
            </Route>

            {/* Redirect root to dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* 404 fallback */}
            <Route
              path="*"
              element={
                <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                  <div className="text-center">
                    <h1 className="text-6xl font-bold text-gray-900 dark:text-gray-100">404</h1>
                    <p className="text-xl text-gray-600 dark:text-gray-400 mt-2">Page not found</p>
                    <a
                      href="/dashboard"
                      className="inline-block mt-4 px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                    >
                      Go to Dashboard
                    </a>
                  </div>
                </div>
              }
            />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
