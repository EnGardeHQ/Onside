/**
 * Competitor Rankings Chart
 * Compares competitor ranking performance
 */

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { CompetitorRanking } from '../../types';

interface CompetitorRankingsChartProps {
  rankings: CompetitorRanking[];
}

export const CompetitorRankingsChart: React.FC<CompetitorRankingsChartProps> = ({ rankings }) => {
  if (rankings.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
        No competitor ranking data available
      </div>
    );
  }

  const data = rankings.map((ranking) => ({
    name: ranking.competitor_name,
    avgPosition: ranking.average_position,
    visibility: ranking.visibility_score,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="avgPosition" fill="#1f77b4" name="Avg Position" />
        <Bar dataKey="visibility" fill="#28a745" name="Visibility Score" />
      </BarChart>
    </ResponsiveContainer>
  );
};
