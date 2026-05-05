import React from 'react';

export default function StatusBadge({ status }) {
  if (!status) return null;
  
  let color = 'bg-steel/20 text-steel-light border-steel/50';
  
  switch (status.toUpperCase()) {
    case 'ACTIVE':
    case 'ATTRIBUTED':
    case 'MERGED':
    case 'AUTO_LINKED':
      color = 'bg-green-500/20 text-green-400 border-green-500/50';
      break;
    case 'DORMANT':
    case 'PENDING_REVIEW':
      color = 'bg-saffron/20 text-saffron border-saffron/50';
      break;
    case 'CLOSED':
    case 'REJECTED':
    case 'UNATTRIBUTABLE':
      color = 'bg-red-500/20 text-red-400 border-red-500/50';
      break;
    default:
      break;
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-sora font-semibold border uppercase tracking-wider ${color}`}>
      {status.replace('_', ' ')}
    </span>
  );
}
