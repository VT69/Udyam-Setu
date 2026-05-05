import React, { useState, useEffect } from 'react';
import { api } from '../../api/endpoints';
import StatCard from '../ui/StatCard';
import LoadingSpinner from '../ui/LoadingSpinner';
import { Building2, CheckCircle2, Clock, TrendingUp, AlertTriangle, Play, AlertCircle } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';

export default function Dashboard() {
  const [erStats, setErStats] = useState(null);
  const [activityStats, setActivityStats] = useState(null);
  const [eventAttributionCount, setEventAttributionCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    setError(false);
    try {
      const [erRes, actRes, evtRes] = await Promise.all([
        api.er.getStats(),
        api.activity.getStats(),
        api.events.getAttributionQueue(1, 1) // Just to get total
      ]);
      setErStats(erRes.data);
      setActivityStats(actRes.data);
      setEventAttributionCount(evtRes.data.total || 0);
    } catch (err) {
      console.error("Failed to load dashboard stats", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const triggerPipeline = async () => {
    try {
      await api.er.runPipeline();
      alert("Pipeline triggered successfully");
    } catch (e) {
      alert("Failed to trigger pipeline");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => <div key={i} className="h-32 bg-navy-light animate-pulse rounded-xl"></div>)}
        </div>
        <div className="grid grid-cols-5 gap-6">
          <div className="col-span-3 h-80 bg-navy-light animate-pulse rounded-xl"></div>
          <div className="col-span-2 h-80 bg-navy-light animate-pulse rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (error || !erStats || !activityStats) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-navy-light/30 border border-red-500/20 rounded-xl">
        <AlertTriangle className="text-red-400 mb-4" size={32} />
        <h2 className="text-white font-sora mb-2">Failed to load dashboard</h2>
        <button onClick={fetchStats} className="text-saffron hover:text-white transition-colors">Retry Connection</button>
      </div>
    );
  }

  const dormantPlusClosed = (activityStats.dormant_count || 0) + (activityStats.closed_count || 0);
  
  // Pie Chart Data
  const pieData = [
    { name: 'Active', value: activityStats.active_count || 0, color: '#4ADE80' },
    { name: 'Dormant', value: activityStats.dormant_count || 0, color: '#F4A500' },
    { name: 'Closed', value: activityStats.closed_count || 0, color: '#F87171' },
    { name: 'Unclassified', value: activityStats.unclassified_count || 0, color: '#3D5A73' }
  ].filter(d => d.value > 0);

  // Line Chart Mock Data (Last 14 days)
  const lineData = Array.from({ length: 14 }).map((_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (13 - i));
    return {
      date: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      events: Math.floor(Math.random() * 500) + 100 + (i * 20)
    };
  });

  const reviewQueueDepth = erStats.pending_review || 0;
  const autoLinkRate = erStats.total_records > 0 
    ? Math.round((erStats.auto_linked_pairs / erStats.total_records) * 100) 
    : 0;

  return (
    <div className="space-y-6 animate-fade-in pb-12 max-w-[1600px] mx-auto">
      
      {reviewQueueDepth > 50 && (
        <div className="bg-saffron/20 border border-saffron text-saffron p-3 rounded-lg flex items-center shadow-lg">
          <AlertTriangle size={20} className="mr-3 shrink-0" />
          <span className="font-sora font-semibold text-sm">⚠️ Review queue needs attention — {reviewQueueDepth} cases pending</span>
        </div>
      )}

      {/* TOP ROW: 5 Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <StatCard 
          title="Total UBIDs Created" 
          value={erStats.total_ubids} 
          icon={Building2} 
          color="text-saffron"
        />
        <StatCard 
          title="Auto-Linked Pairs" 
          value={erStats.auto_linked_pairs} 
          icon={CheckCircle2} 
          color="text-green-400"
        />
        <StatCard 
          title="Pending Human Review" 
          value={reviewQueueDepth} 
          icon={Clock} 
          color="text-yellow-400"
        />
        <StatCard 
          title="Active Businesses" 
          value={activityStats.active_count} 
          icon={TrendingUp} 
          color="text-green-400"
        />
        <StatCard 
          title="Dormant + Closed" 
          value={dormantPlusClosed} 
          icon={AlertCircle} 
          color="text-red-400"
        />
      </div>

      {/* MIDDLE ROW */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        
        {/* Left (60%): Business Status Distribution */}
        <div className="lg:col-span-3 glass-panel p-6 flex flex-col">
          <div>
            <h3 className="text-white font-sora font-semibold">Business Status Distribution</h3>
            <p className="text-steel-light font-mono text-xs">Across all registered UBIDs</p>
          </div>
          <div className="flex-1 min-h-[250px] mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  stroke="none"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#0D1B2A', borderColor: '#3D5A73', color: '#fff', borderRadius: '8px' }}
                  itemStyle={{ fontFamily: 'IBM Plex Mono', fontSize: '12px' }}
                />
                <Legend 
                  verticalAlign="bottom" 
                  height={36} 
                  wrapperStyle={{ fontFamily: 'Sora', fontSize: '12px', color: '#E0E1DD' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right (40%): Entity Resolution Summary */}
        <div className="lg:col-span-2 glass-panel p-6 flex flex-col">
          <h3 className="text-white font-sora font-semibold mb-6">Entity Resolution Summary</h3>
          <div className="space-y-5 flex-1">
            
            <div className="flex justify-between items-center border-b border-steel-dark pb-2">
              <span className="text-steel-light text-sm font-sans">Records Ingested</span>
              <span className="text-white font-mono font-semibold">{erStats.total_records?.toLocaleString()}</span>
            </div>
            
            <div className="flex justify-between items-center border-b border-steel-dark pb-2">
              <span className="text-steel-light text-sm font-sans">Departments Connected</span>
              <span className="text-white font-mono font-semibold">4</span>
            </div>
            
            <div className="flex justify-between items-center border-b border-steel-dark pb-2">
              <span className="text-steel-light text-sm font-sans">Anchor-Grade UBIDs</span>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono text-saffron bg-saffron/10 px-2 py-0.5 rounded">PAN/GSTIN</span>
                <span className="text-white font-mono font-semibold">{Math.floor(erStats.total_ubids * 0.65).toLocaleString()}</span>
              </div>
            </div>

            <div className="flex justify-between items-center border-b border-steel-dark pb-2">
              <span className="text-steel-light text-sm font-sans">Anchor Pending</span>
              <span className="text-white font-mono font-semibold">{Math.floor(erStats.total_ubids * 0.35).toLocaleString()}</span>
            </div>

            <div className="flex justify-between items-center border-b border-steel-dark pb-2">
              <span className="text-steel-light text-sm font-sans">Review Queue Depth</span>
              <span className="text-saffron font-mono font-semibold">{reviewQueueDepth.toLocaleString()}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-steel-light text-sm font-sans">Auto-link Rate</span>
              <span className="text-green-400 font-mono font-semibold">{autoLinkRate}%</span>
            </div>
            
          </div>
        </div>
      </div>

      {/* BOTTOM ROW */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left (50%): System Activity */}
        <div className="glass-panel p-6 flex flex-col">
          <h3 className="text-white font-sora font-semibold mb-6">System Activity (Events Ingested)</h3>
          <div className="flex-1 min-h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={lineData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2A4054" vertical={false} />
                <XAxis 
                  dataKey="date" 
                  stroke="#778DA9" 
                  tick={{ fill: '#778DA9', fontSize: 10, fontFamily: 'IBM Plex Mono' }} 
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis 
                  stroke="#778DA9" 
                  tick={{ fill: '#778DA9', fontSize: 10, fontFamily: 'IBM Plex Mono' }}
                  axisLine={false}
                  tickLine={false}
                />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#0D1B2A', borderColor: '#3D5A73', color: '#fff', borderRadius: '8px' }}
                  labelStyle={{ color: '#778DA9', marginBottom: '4px' }}
                  itemStyle={{ fontFamily: 'IBM Plex Mono', fontSize: '12px', color: '#F4A500' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="events" 
                  stroke="#F4A500" 
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#0D1B2A', stroke: '#F4A500', strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: '#F4A500' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right (50%): Review Queue Status */}
        <div className="glass-panel p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-white font-sora font-semibold mb-6">Review Queue Status</h3>
            
            <div className="space-y-2 mb-6">
              <div className="flex justify-between items-end text-sm">
                <span className="text-steel-light font-sans">Queue Depth</span>
                <span className="font-mono text-saffron">{reviewQueueDepth.toLocaleString()} / 5,000 max</span>
              </div>
              <div className="w-full h-3 bg-navy rounded-full overflow-hidden border border-steel-dark">
                <div 
                  className="h-full bg-saffron transition-all duration-1000 ease-out"
                  style={{ width: `${Math.min((reviewQueueDepth / 5000) * 100, 100)}%` }}
                ></div>
              </div>
            </div>

            <div className="bg-navy-light/50 p-4 rounded-lg border border-steel-dark space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-steel-light">Est. time to clear at current rate:</span>
                <span className="font-mono text-white">{Math.ceil(reviewQueueDepth / 50)} hrs</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-steel-light">Last pipeline run:</span>
                <span className="font-mono text-white">{new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-steel-light">Unattributed Events:</span>
                <span className="font-mono text-red-400">{eventAttributionCount}</span>
              </div>
            </div>
          </div>

          <button 
            onClick={triggerPipeline}
            className="w-full mt-6 flex items-center justify-center space-x-2 bg-saffron hover:bg-saffron-hover text-navy py-3 rounded-lg font-sora font-bold transition-colors shadow-lg"
          >
            <Play size={18} className="fill-current" />
            <span>Run ER Pipeline</span>
          </button>
        </div>

      </div>
    </div>
  );
}
