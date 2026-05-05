import React, { useState, useEffect } from 'react';
import { api } from '../../api/endpoints';
import StatusBadge from '../ui/StatusBadge';
import EmptyState from '../ui/EmptyState';
import LoadingSpinner from '../ui/LoadingSpinner';
import { CheckCircle, Clock } from 'lucide-react';

export default function EventAttribution() {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    try {
      const res = await api.events.getAttributionQueue(1, 20);
      setQueue(res.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner text="Loading Attribution Queue..." />;

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-sora font-bold text-white mb-2">Event Attribution Review</h1>
          <p className="text-steel-light font-mono text-sm">Manually route orphaned telemetry events to Golden UBIDs.</p>
        </div>
      </div>

      {queue.length === 0 ? (
        <EmptyState 
          icon={CheckCircle} 
          title="All Events Attributed" 
          description="The event processor has successfully attributed all incoming telemetry streams to existing entities." 
        />
      ) : (
        <div className="glass-panel overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-navy border-b border-steel-dark text-steel-light text-xs uppercase tracking-wider font-sora">
                <th className="p-4">Event Date</th>
                <th className="p-4">Source</th>
                <th className="p-4">Extracted Data</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-steel-dark">
              {queue.map((item) => (
                <tr key={item.event_id} className="hover:bg-navy-light/50 transition-colors">
                  <td className="p-4 align-top font-mono text-sm text-white">
                    <div className="flex items-center space-x-2">
                      <Clock size={14} className="text-steel-light" />
                      <span>{new Date(item.event_time).toLocaleDateString()}</span>
                    </div>
                  </td>
                  <td className="p-4 align-top">
                    <div className="font-sora text-sm font-semibold text-white mb-1">{item.event_type.replace('_', ' ')}</div>
                    <div className="font-mono text-xs text-saffron">{item.department}</div>
                  </td>
                  <td className="p-4 align-top">
                    <pre className="text-xs font-mono text-steel-light bg-navy p-2 rounded max-w-sm overflow-x-auto border border-steel-dark">
                      {JSON.stringify(item.event_data, null, 2)}
                    </pre>
                  </td>
                  <td className="p-4 align-top text-right">
                    <button 
                      className="bg-navy border border-steel-dark hover:border-saffron text-saffron px-3 py-1.5 rounded transition-colors text-xs font-sora font-semibold"
                    >
                      Attribute...
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
