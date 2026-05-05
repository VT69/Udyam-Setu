import React from 'react';

export default function StatCard({ title, value, icon: Icon, change, changeText, color = 'text-saffron' }) {
  return (
    <div className="glass-panel p-6 flex flex-col justify-between">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-steel-light text-sm font-medium uppercase tracking-wider">{title}</h3>
        <div className={`p-2 rounded-lg bg-navy ${color} bg-opacity-50`}>
          <Icon size={20} />
        </div>
      </div>
      
      <div>
        <div className="text-3xl font-mono font-semibold text-white mb-2">
          {value !== undefined ? value.toLocaleString() : '---'}
        </div>
        
        {change && (
          <div className="flex items-center text-sm">
            <span className={`font-mono mr-2 ${change > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {change > 0 ? '+' : ''}{change}%
            </span>
            <span className="text-steel-light">{changeText}</span>
          </div>
        )}
      </div>
    </div>
  );
}
