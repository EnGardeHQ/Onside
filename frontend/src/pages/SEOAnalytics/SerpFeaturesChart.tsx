/**
 * SERP Features Chart
 * Visualizes SERP feature distribution
 */

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { SerpFeature } from '../../types';

interface SerpFeaturesChartProps {
  features: SerpFeature[];
}

const COLORS = ['#1f77b4', '#28a745', '#ffc107', '#dc3545', '#17a2b8', '#6f42c1'];

export const SerpFeaturesChart: React.FC<SerpFeaturesChartProps> = ({ features }) => {
  if (features.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
        No SERP features data available
      </div>
    );
  }

  const data = features.map((feature) => ({
    name: feature.feature,
    value: feature.count,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percentage }) => `${name}: ${(percentage * 100).toFixed(0)}%`}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};
