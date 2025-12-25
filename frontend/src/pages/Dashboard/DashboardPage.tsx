/**
 * Dashboard Home Page
 * Overview dashboard with key metrics and recent activity
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Users, FileText, TrendingUp, Activity } from 'lucide-react';
import { Card, CardTitle, CardContent } from '../../components/common';

export const DashboardPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Welcome to OnSide Competitive Intelligence Platform
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card hover className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Competitors</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                12
              </p>
            </div>
            <div className="p-3 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
              <Users className="text-primary-600 dark:text-primary-400" size={24} />
            </div>
          </div>
        </Card>

        <Card hover className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Reports</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                24
              </p>
            </div>
            <div className="p-3 bg-success-100 dark:bg-success-900/30 rounded-lg">
              <FileText className="text-success-600 dark:text-success-400" size={24} />
            </div>
          </div>
        </Card>

        <Card hover className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Keywords</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                156
              </p>
            </div>
            <div className="p-3 bg-warning-100 dark:bg-warning-900/30 rounded-lg">
              <TrendingUp className="text-warning-600 dark:text-warning-400" size={24} />
            </div>
          </div>
        </Card>

        <Card hover className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Active Tracking</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                8
              </p>
            </div>
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Activity className="text-blue-600 dark:text-blue-400" size={24} />
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Link to="/competitors">
          <Card hover className="p-6 transition-all">
            <CardTitle>Competitor Management</CardTitle>
            <CardContent>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Track and analyze your competitors' performance, content, and strategies
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/reports">
          <Card hover className="p-6 transition-all">
            <CardTitle>Reports</CardTitle>
            <CardContent>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Generate comprehensive intelligence reports with AI-powered insights
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/seo-analytics">
          <Card hover className="p-6 transition-all">
            <CardTitle>SEO Analytics</CardTitle>
            <CardContent>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                Monitor keyword rankings, SERP features, and Core Web Vitals
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Getting Started */}
      <Card className="p-6">
        <CardTitle>Getting Started</CardTitle>
        <CardContent>
          <div className="mt-4 space-y-3">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-full flex items-center justify-center text-sm font-semibold">
                1
              </div>
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  Add your first competitor
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Start tracking competitors by adding their information and domains
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-full flex items-center justify-center text-sm font-semibold">
                2
              </div>
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  Configure SEO tracking
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Add keywords you want to track for ranking and SERP analysis
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-full flex items-center justify-center text-sm font-semibold">
                3
              </div>
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  Generate your first report
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Create intelligence reports to analyze trends and opportunities
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
