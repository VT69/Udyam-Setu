import React from 'react';

export default function ConfidenceBadge({ score }) {
  if (score === undefined || score === null) return null;
  
  let color = 'bg-red-500/20 text-red-400 border-red-500/50';
  if (score >= 0.90) {
    color = 'bg-green-500/20 text-green-400 border-green-500/50';
  } else if (score >= 0.60) {
    color = 'bg-saffron/20 text-saffron border-saffron/50';
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${color}`}>
      {(score * 100).toFixed(1)}% Conf
    </span>
  );
}
