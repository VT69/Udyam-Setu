import React, { useState, useEffect } from 'react';
import { api } from '../../api/endpoints';
import StatCard from '../ui/StatCard';
import LoadingSpinner from '../ui/LoadingSpinner';
import { Users, Link2, AlertTriangle, Building2, Activity, Play } from 'lucide-react';

export default function Dashboard() {
  const [erStats, setErStats] = useState(null);
  const [activityStats, setActivityStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [erRes, actRes] = await Promise.all([
          api.er.getStats(),
          api.activity.getStats()
        ]);
        setErStats(erRes.data);
        setActivityStats(actRes.data);
      } catch (err) {
        console.error("Failed to load dashboard stats", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const triggerPipeline = async () => {
    try {
      await api.er.runPipeline();
      alert("Pipeline triggered successfully");
    } catch (e) {
      alert("Failed to trigger pipeline");
    }
  };

  if (loading) return <LoadingSpinner text="Loading Dashboard..." />;
  if (!erStats || !activityStats) return <div className="text-red-400">Error loading dashboard</div>;

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-sora font-bold text-white mb-2">Platform Overview</h1>
          <p className="text-steel-light font-mono text-sm">Karnataka Business Intelligence Grid</p>
        </div>
        <button 
          onClick={triggerPipeline}
          className="flex items-center space-x-2 bg-saffron hover:bg-saffron-hover text-navy px-4 py-2 rounded-lg font-sora font-semibold transition-colors shadow-lg"
        >
          <Play size={18} />
          <span>Run Resolution Pipeline</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Raw Records" 
          value={erStats.total_records} 
          icon={Building2} 
          color="text-blue-400"
        />
        <StatCard 
          title="Golden UBIDs" 
          value={erStats.total_ubids} 
          icon={Users} 
          color="text-green-400"
          change={+12.4}
          changeText="vs last week"
        />
        <StatCard 
          title="Auto-Linked Pairs" 
          value={erStats.auto_linked_pairs} 
          icon={Link2} 
          color="text-saffron"
        />
        <StatCard 
          title="Pending ER Review" 
          value={erStats.pending_review} 
          icon={AlertTriangle} 
          color="text-red-400"
        />
      </div>

      <h2 className="text-xl font-sora font-bold text-white mt-12 mb-6">Activity Intelligence</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title="Active Businesses" 
          value={activityStats.active_count} 
          icon={Activity} 
          color="text-green-400"
        />
        <StatCard 
          title="Dormant Businesses" 
          value={activityStats.dormant_count} 
          icon={Activity} 
          color="text-saffron"
        />
        <StatCard 
          title="Closed Businesses" 
          value={activityStats.closed_count} 
          icon={Activity} 
          color="text-red-400"
        />
      </div>
    </div>
  );
}
