import React from 'react';

const Stats = ({ stats }) => {
  if (!stats) return null;

  const completionPercentage = stats.total > 0
    ? Math.round((stats.completed / stats.total) * 100)
    : 0;

  return (
    <div className="stats-container">
      <div className="stat-card">
        <div className="stat-number">{stats.total}</div>
        <div className="stat-label">Total</div>
      </div>
      <div className="stat-card completed">
        <div className="stat-number">{stats.completed}</div>
        <div className="stat-label">Completed</div>
      </div>
      <div className="stat-card pending">
        <div className="stat-number">{stats.pending}</div>
        <div className="stat-label">Pending</div>
      </div>
      <div className="stat-card percentage">
        <div className="stat-number">{completionPercentage}%</div>
        <div className="stat-label">Completion Rate</div>
      </div>
    </div>
  );
};

export default Stats;
