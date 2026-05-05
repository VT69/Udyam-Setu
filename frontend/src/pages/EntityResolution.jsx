import React, { useState, useEffect } from 'react';
import { api } from '../../api/endpoints';
import ConfidenceBadge from '../ui/ConfidenceBadge';
import StatusBadge from '../ui/StatusBadge';
import EmptyState from '../ui/EmptyState';
import LoadingSpinner from '../ui/LoadingSpinner';
import { CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function EntityResolution() {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    try {
      const res = await api.er.getReviewQueue(1, 20);
      setQueue(res.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner text="Loading ER Review Queue..." />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-sora font-bold text-white mb-2">Entity Resolution Queue</h1>
          <p className="text-steel-light font-mono text-sm">Human-in-the-loop review for borderline identity matches</p>
        </div>
      </div>

      {queue.length === 0 ? (
        <EmptyState 
          icon={CheckCircle} 
          title="Inbox Zero" 
          description="There are no candidate pairs currently awaiting human review. The automated pipeline is handling everything!" 
        />
      ) : (
        <div className="glass-panel overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-navy border-b border-steel-dark text-steel-light text-xs uppercase tracking-wider font-sora">
                <th className="p-4">Confidence</th>
                <th className="p-4">Record A (Incoming)</th>
                <th className="p-4">Record B (Existing)</th>
                <th className="p-4">Blocking Signals</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-steel-dark">
              {queue.map((pair) => (
                <tr key={pair.pair_id} className="hover:bg-navy-light/50 transition-colors">
                  <td className="p-4 align-top">
                    <ConfidenceBadge score={pair.score} />
                  </td>
                  <td className="p-4 align-top">
                    <div className="font-sora text-sm font-semibold text-white mb-1">{pair.record_a.business_name}</div>
                    <div className="font-mono text-xs text-steel-light">{pair.record_a.department} • {pair.record_a.address_pincode}</div>
                    {(pair.record_a.pan || pair.record_a.gstin) && (
                      <div className="mt-2 font-mono text-xs text-saffron">Anchor: {pair.record_a.pan || pair.record_a.gstin}</div>
                    )}
                  </td>
                  <td className="p-4 align-top">
                    <div className="font-sora text-sm font-semibold text-white mb-1">{pair.record_b.business_name}</div>
                    <div className="font-mono text-xs text-steel-light">{pair.record_b.department} • {pair.record_b.address_pincode}</div>
                    {(pair.record_b.pan || pair.record_b.gstin) && (
                      <div className="mt-2 font-mono text-xs text-saffron">Anchor: {pair.record_b.pan || pair.record_b.gstin}</div>
                    )}
                  </td>
                  <td className="p-4 align-top">
                    <div className="flex flex-wrap gap-2">
                      {pair.blocking_signals.map(sig => (
                        <span key={sig} className="px-2 py-1 text-[10px] font-mono rounded bg-steel-dark text-steel-lightest uppercase">
                          {sig.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="p-4 align-top text-right">
                    <button 
                      onClick={() => navigate(`/review-task/${pair.pair_id}`, { state: { pair } })}
                      className="inline-flex items-center space-x-1 text-saffron hover:text-white transition-colors text-sm font-sora font-semibold"
                    >
                      <span>Review</span>
                      <ArrowRight size={16} />
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
