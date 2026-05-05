import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/endpoints';
import StatCard from '../ui/StatCard';
import StatusBadge from '../ui/StatusBadge';
import EmptyState from '../ui/EmptyState';
import LoadingSpinner from '../ui/LoadingSpinner';
import { Activity, Clock, AlertCircle, ArrowRight } from 'lucide-react';

export default function ActivityIntelligence() {
  const [stats, setStats] = useState(null);
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, queueRes] = await Promise.all([
        api.activity.getStats(),
        api.activity.getReviewQueue(1, 10)
      ]);
      setStats(statsRes.data);
      setQueue(queueRes.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const reclassifyAll = async () => {
    try {
      await api.activity.classifyAll();
      alert("Classification batch job triggered.");
    } catch (e) {
      alert("Failed to trigger batch job.");
    }
  };

  if (loading) return <LoadingSpinner text="Loading Activity Data..." />;
  if (!stats) return <div className="text-red-400">Failed to load stats.</div>;

  const total = stats.active_count + stats.dormant_count + stats.closed_count + stats.unclassified_count;
  const activePct = total > 0 ? Math.round((stats.active_count / total) * 100) : 0;

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-sora font-bold text-white mb-2">Activity Intelligence</h1>
          <p className="text-steel-light font-mono text-sm">Operational status classification driven by 18-month telemetry</p>
        </div>
        <button 
          onClick={reclassifyAll}
          className="bg-navy-light hover:bg-steel-dark text-white px-4 py-2 rounded-lg font-sora font-semibold transition-colors shadow-lg border border-steel-dark flex items-center space-x-2"
        >
          <Activity size={18} />
          <span>Recompute All Statuses</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Active Rate" 
          value={`${activePct}%`} 
          icon={Activity} 
          color="text-green-400"
        />
        <StatCard 
          title="Active Businesses" 
          value={stats.active_count} 
          icon={Activity} 
          color="text-green-400"
        />
        <StatCard 
          title="Dormant Businesses" 
          value={stats.dormant_count} 
          icon={Clock} 
          color="text-saffron"
        />
        <StatCard 
          title="Needs Human Review" 
          value={stats.needs_review_count} 
          icon={AlertCircle} 
          color="text-red-400"
        />
      </div>

      <div>
        <h2 className="text-xl font-sora font-bold text-white mb-6">Uncertainty Review Queue</h2>
        {queue.length === 0 ? (
          <EmptyState 
            icon={Activity} 
            title="High Model Confidence" 
            description="The ML classifier is confident across the board. No boundary cases require human status overrides." 
          />
        ) : (
          <div className="glass-panel overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-navy border-b border-steel-dark text-steel-light text-xs uppercase tracking-wider font-sora">
                  <th className="p-4">UBID</th>
                  <th className="p-4">Predicted Status</th>
                  <th className="p-4">ML Explanation</th>
                  <th className="p-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-steel-dark">
                {queue.map((item) => (
                  <tr key={item.ubid} className="hover:bg-navy-light/50 transition-colors">
                    <td className="p-4 align-top font-mono text-sm text-white">
                      {item.ubid}
                    </td>
                    <td className="p-4 align-top">
                      <div className="mb-1"><StatusBadge status={item.status} /></div>
                      <span className="font-mono text-xs text-saffron">Conf: {(item.confidence * 100).toFixed(1)}%</span>
                    </td>
                    <td className="p-4 align-top">
                      <p className="text-sm text-steel-light leading-relaxed max-w-xl">
                        {item.evidence_summary}
                      </p>
                    </td>
                    <td className="p-4 align-top text-right">
                      <button 
                        onClick={() => navigate(`/ubid/${item.ubid}`)}
                        className="inline-flex items-center space-x-1 text-saffron hover:text-white transition-colors text-sm font-sora font-semibold"
                      >
                        <span>Inspect</span>
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
    </div>
  );
}
