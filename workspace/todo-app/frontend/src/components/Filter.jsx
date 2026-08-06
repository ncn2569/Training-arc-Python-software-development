import React from 'react';

const Filter = ({ activeFilter, onFilterChange }) => {
  const filters = [
    { value: 'all', label: 'All' },
    { value: 'completed', label: 'Completed' },
    { value: 'pending', label: 'Pending' },
  ];

  return (
    <div className="filter-container">
      {filters.map((filter) => (
        <button
          key={filter.value}
          className={`filter-btn ${activeFilter === filter.value ? 'active' : ''}`}
          onClick={() => onFilterChange(filter.value)}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
};

export default Filter;
