import React, { useState, useEffect } from 'react';

export default function StatCard({ title, value, icon: Icon, change, changeText, color = 'text-saffron' }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    if (value === undefined || value === null || isNaN(value)) {
      setDisplayValue(value);
      return;
    }

    const duration = 1500; // 1.5s
    const frames = 30;
    const stepTime = duration / frames;
    const target = Number(value);
    const stepValue = target / frames;
    let current = 0;

    const timer = setInterval(() => {
      current += stepValue;
      if (current >= target) {
        setDisplayValue(target);
        clearInterval(timer);
      } else {
        setDisplayValue(Math.floor(current));
      }
    }, stepTime);

    return () => clearInterval(timer);
  }, [value]);

  return (
    <div className="glass-panel p-6 flex flex-col justify-between">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-steel-light text-[10px] font-sora uppercase font-semibold tracking-wider">{title}</h3>
        <div className={`p-2 rounded-lg bg-navy ${color} bg-opacity-50`}>
          <Icon size={16} />
        </div>
      </div>
      
      <div>
        <div className="text-2xl font-mono font-semibold text-white mb-1">
          {displayValue !== undefined && displayValue !== null && !isNaN(displayValue) 
            ? displayValue.toLocaleString() 
            : '---'}
        </div>
        
        {change && (
          <div className="flex items-center text-xs">
            <span className={`font-mono mr-1 ${change > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {change > 0 ? '+' : ''}{change}%
            </span>
            <span className="text-steel-light tracking-wide">{changeText}</span>
          </div>
        )}
      </div>
    </div>
  );
}
