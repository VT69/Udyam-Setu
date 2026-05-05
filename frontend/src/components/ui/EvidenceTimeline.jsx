import React from 'react';
import { Clock, Factory, ShieldAlert, FileText, Zap, AlertTriangle } from 'lucide-react';

export default function EvidenceTimeline({ events, showGaps = false }) {
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
      case 'FACTORIES': return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
      case 'KSPCB': return 'bg-orange-500/20 text-orange-400 border-orange-500/50';
      case 'SHOP_ESTABLISHMENT': return 'bg-purple-500/20 text-purple-400 border-purple-500/50';
      case 'BESCOM': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
      default: return 'bg-steel/20 text-steel-light border-steel/50';
    }
  };

  // Sort events chronologically descending (newest first)
  const sortedEvents = [...events].sort((a, b) => new Date(b.date) - new Date(a.date));

  return (
    <div className="relative border-l-2 border-steel-dark ml-3 py-2 space-y-8">
      {sortedEvents.map((evt, idx) => {
        
        let gapIndicator = null;
        if (showGaps && idx < sortedEvents.length - 1) {
          const currentDate = new Date(evt.date);
          const nextDate = new Date(sortedEvents[idx + 1].date);
          const diffMonths = (currentDate - nextDate) / (1000 * 60 * 60 * 24 * 30.4);
          
          if (diffMonths > 3) {
            gapIndicator = (
              <div className="absolute -left-4 -bottom-6 flex items-center w-full">
                <div className="h-6 w-8 bg-navy border border-dashed border-red-500/50 rounded flex items-center justify-center relative z-10">
                  <AlertTriangle size={12} className="text-red-400" />
                </div>
                <span className="ml-3 text-[10px] font-mono text-red-400 opacity-70">
                  {Math.round(diffMonths)} month gap in telemetry
                </span>
              </div>
            );
          }
        }

        return (
          <div key={idx} className="relative pl-6">
            <div className={`absolute -left-[15px] top-1 flex h-7 w-7 items-center justify-center rounded-full border bg-navy ${getColorForDept(evt.dept)} shadow-lg`}>
              {getIconForDept(evt.dept)}
            </div>
            
            <div className="flex flex-col">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-sora font-semibold text-white">{evt.event_type.replace('_', ' ')}</span>
                <span className="text-xs font-mono text-steel-light">
                  {new Date(evt.date).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' })}
                </span>
              </div>
              
              <div>
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-[9px] font-mono font-medium border uppercase ${getColorForDept(evt.dept)}`}>
                  {evt.dept.replace('_', ' ')}
                </span>
              </div>
            </div>
            {gapIndicator}
          </div>
        );
      })}
    </div>
  );
}
