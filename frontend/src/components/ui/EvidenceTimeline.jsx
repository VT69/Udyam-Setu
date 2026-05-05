import React from 'react';
import { Clock, Factory, ShieldAlert, FileText, Zap } from 'lucide-react';

export default function EvidenceTimeline({ events }) {
  if (!events || events.length === 0) {
    return <div className="text-steel-light text-sm italic py-4">No events recorded.</div>;
  }

  const getIconForDept = (dept) => {
    switch (dept) {
      case 'FACTORIES': return <Factory size={16} />;
      case 'KSPCB': return <ShieldAlert size={16} />;
      case 'SHOP_ESTABLISHMENT': return <FileText size={16} />;
      case 'BESCOM': return <Zap size={16} />;
      default: return <Clock size={16} />;
    }
  };

  const getColorForDept = (dept) => {
    switch (dept) {
      case 'FACTORIES': return 'bg-blue-500/20 text-blue-400';
      case 'KSPCB': return 'bg-green-500/20 text-green-400';
      case 'SHOP_ESTABLISHMENT': return 'bg-purple-500/20 text-purple-400';
      case 'BESCOM': return 'bg-yellow-500/20 text-yellow-400';
      default: return 'bg-steel/20 text-steel-light';
    }
  };

  return (
    <div className="relative border-l border-steel-dark ml-3 py-2 space-y-6">
      {events.map((evt, idx) => (
        <div key={idx} className="relative pl-6">
          <div className={`absolute -left-3 top-1 flex h-6 w-6 items-center justify-center rounded-full border border-steel-dark bg-navy ${getColorForDept(evt.dept)}`}>
            {getIconForDept(evt.dept)}
          </div>
          
          <div className="flex flex-col">
            <div className="flex items-center space-x-2 mb-1">
              <span className="text-sm font-sora font-semibold text-white">{evt.event_type.replace('_', ' ')}</span>
              <span className="text-xs font-mono text-steel-light">
                {new Date(evt.date).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' })}
              </span>
            </div>
            
            <span className={`inline-block px-2 py-0.5 rounded text-xs font-mono font-medium max-w-max ${getColorForDept(evt.dept)}`}>
              {evt.dept.replace('_', ' ')}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
