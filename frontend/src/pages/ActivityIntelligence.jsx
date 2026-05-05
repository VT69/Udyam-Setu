import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/endpoints';
import StatCard from '../ui/StatCard';
import StatusBadge from '../ui/StatusBadge';
import ConfidenceBadge from '../ui/ConfidenceBadge';
import EmptyState from '../ui/EmptyState';
import LoadingSpinner from '../ui/LoadingSpinner';
import { Activity, Clock, AlertCircle, Search, Filter, Play, CheckCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function ActivityIntelligence() {
  const [activeTab, setActiveTab] = useState('overview'); // overview, details, review
  const [stats, setStats] = useState(null);
  const [listData, setListData] = useState([]);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [filterStatus, setFilterStatus] = useState('');
  const [filterQuery, setFilterQuery] = useState('');
  
  // Modal state
  const [overrideModal, setOverrideModal] = useState({ isOpen: false, ubid: null, status: 'ACTIVE', reason: '' });

  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, queryRes, queueRes] = await Promise.all([
        api.activity.getStats(),
        api.activity.crossDeptQuery({ limit: 100 }), // Mock fetching list of UBIDs
        api.activity.getReviewQueue(1, 20)
      ]);
      setStats(statsRes.data);
      setListData(queryRes.data.results || []);
      setReviewQueue(queueRes.data.items || []);
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

  const handleOverrideSubmit = async () => {
    if (overrideModal.reason.length < 10) {
      alert("Please provide a reason (min 10 chars).");
      return;
    }
    try {
      await api.activity.submitOverride(overrideModal.ubid, overrideModal.status, overrideModal.reason, 'admin');
      alert(`Status for ${overrideModal.ubid} overridden successfully!`);
      setOverrideModal({ isOpen: false, ubid: null, status: 'ACTIVE', reason: '' });
      fetchData(); // Refresh
    } catch (e) {
      alert("Failed to override status.");
    }
  };

  if (loading) return <LoadingSpinner text="Loading Activity Intelligence..." />;
  if (!stats) return <div className="text-red-400 p-8">Failed to load stats.</div>;

  const total = stats.active_count + stats.dormant_count + stats.closed_count + stats.unclassified_count;
  const activePct = total > 0 ? ((stats.active_count / total) * 100).toFixed(1) : 0;
  const dormantPct = total > 0 ? ((stats.dormant_count / total) * 100).toFixed(1) : 0;
  const closedPct = total > 0 ? ((stats.closed_count / total) * 100).toFixed(1) : 0;

  // Mock data for BarChart: Status Distribution by Department
  const barData = [
    { name: 'FACTORIES', active: 4000, dormant: 1200, closed: 300 },
    { name: 'SHOP_EST', active: 15000, dormant: 6000, closed: 2100 },
    { name: 'KSPCB', active: 2000, dormant: 400, closed: 150 },
    { name: 'BESCOM', active: 18000, dormant: 5000, closed: 1900 },
  ];

  const filteredList = listData.filter(item => {
    const matchStatus = filterStatus ? item.status === filterStatus : true;
    const matchQuery = filterQuery ? (
      item.ubid.toLowerCase().includes(filterQuery.toLowerCase()) || 
      item.business_name.toLowerCase().includes(filterQuery.toLowerCase())
    ) : true;
    return matchStatus && matchQuery;
  });

  const renderOverview = () => (
    <div className="space-y-8 animate-fade-in">
      {/* Top KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title="Active Businesses" 
          value={stats.active_count} 
          icon={Activity} 
          color="text-green-400"
          change={activePct}
          changeText="% of total"
        />
        <StatCard 
          title="Dormant Businesses" 
          value={stats.dormant_count} 
          icon={Clock} 
          color="text-saffron"
          change={dormantPct}
          changeText="% of total"
        />
        <StatCard 
          title="Closed Businesses" 
          value={stats.closed_count} 
          icon={AlertCircle} 
          color="text-red-400"
          change={closedPct}
          changeText="% of total"
        />
      </div>

      {/* Bar Chart */}
      <div className="glass-panel p-6">
        <h3 className="text-white font-sora font-semibold mb-6">Status Distribution by Department</h3>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2A4054" vertical={false} />
              <XAxis dataKey="name" stroke="#778DA9" tick={{ fill: '#778DA9', fontSize: 12, fontFamily: 'IBM Plex Mono' }} />
              <YAxis stroke="#778DA9" tick={{ fill: '#778DA9', fontSize: 12, fontFamily: 'IBM Plex Mono' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0D1B2A', borderColor: '#3D5A73', color: '#fff', borderRadius: '8px' }}
                itemStyle={{ fontFamily: 'IBM Plex Mono', fontSize: '12px' }}
              />
              <Legend wrapperStyle={{ fontFamily: 'Sora', fontSize: '12px', color: '#E0E1DD' }} />
              <Bar dataKey="active" name="Active" fill="#4ADE80" radius={[4, 4, 0, 0]} />
              <Bar dataKey="dormant" name="Dormant" fill="#F4A500" radius={[4, 4, 0, 0]} />
              <Bar dataKey="closed" name="Closed" fill="#F87171" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Filterable List */}
      <div className="glass-panel overflow-hidden flex flex-col">
        <div className="p-4 border-b border-steel-dark bg-navy flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center flex-1 min-w-[300px]">
            <div className="relative w-full max-w-md">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search size={16} className="text-steel-light" />
              </div>
              <input 
                type="text" 
                placeholder="Search UBID or Business Name..."
                className="w-full bg-navy border border-steel-dark rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-saffron"
                value={filterQuery}
                onChange={e => setFilterQuery(e.target.value)}
              />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Filter size={16} className="text-steel-light" />
            <select 
              className="bg-navy border border-steel-dark rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-saffron"
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="DORMANT">Dormant</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-navy border-b border-steel-dark text-steel-light text-xs uppercase tracking-wider font-sora">
                <th className="p-4">UBID</th>
                <th className="p-4">Primary Name</th>
                <th className="p-4">Linked Depts</th>
                <th className="p-4">Status</th>
                <th className="p-4">Confidence</th>
                <th className="p-4 hidden lg:table-cell">Evidence Preview</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-steel-dark">
              {filteredList.map((item) => (
                <tr 
                  key={item.ubid} 
                  className="hover:bg-navy-light/50 transition-colors cursor-pointer group"
                  onClick={() => navigate(`/ubid/${item.ubid}`)}
                >
                  <td className="p-4 align-top font-mono text-sm text-saffron group-hover:underline">
                    {item.ubid}
                  </td>
                  <td className="p-4 align-top">
                    <div className="font-sora text-sm font-semibold text-white">{item.business_name}</div>
                  </td>
                  <td className="p-4 align-top">
                    <div className="flex flex-wrap gap-1">
                      {item.linked_departments.map(d => (
                        <span key={d} className="px-1.5 py-0.5 text-[9px] font-mono rounded bg-steel-dark text-steel-lightest">{d}</span>
                      ))}
                    </div>
                  </td>
                  <td className="p-4 align-top">
                    <StatusBadge status={item.status} />
                  </td>
                  <td className="p-4 align-top">
                    <ConfidenceBadge score={item.confidence} />
                  </td>
                  <td className="p-4 align-top hidden lg:table-cell">
                    <p className="text-xs text-steel-light truncate max-w-sm">{item.evidence_summary}</p>
                  </td>
                </tr>
              ))}
              {filteredList.length === 0 && (
                <tr>
                  <td colSpan="6" className="p-8 text-center text-steel-light">No records found matching filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderReviewQueue = () => (
    <div className="animate-fade-in">
      {reviewQueue.length === 0 ? (
        <EmptyState 
          icon={CheckCircle} 
          title="No Items Pending Review" 
          description="The Activity Classifier is highly confident across the board. No manual overrides are currently flagged as necessary." 
        />
      ) : (
        <div className="glass-panel overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-navy border-b border-steel-dark text-steel-light text-xs uppercase tracking-wider font-sora">
                <th className="p-4">UBID</th>
                <th className="p-4">Predicted Status</th>
                <th className="p-4">Evidence Flag</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-steel-dark">
              {reviewQueue.map((item) => (
                <tr key={item.ubid} className="hover:bg-navy-light/50 transition-colors">
                  <td className="p-4 align-top font-mono text-sm text-white">{item.ubid}</td>
                  <td className="p-4 align-top">
                    <div className="mb-1"><StatusBadge status={item.status} /></div>
                    <ConfidenceBadge score={item.confidence} />
                  </td>
                  <td className="p-4 align-top">
                    <p className="text-sm text-steel-light max-w-xl">{item.evidence_summary}</p>
                  </td>
                  <td className="p-4 align-top text-right">
                    <button 
                      onClick={() => setOverrideModal({ isOpen: true, ubid: item.ubid, status: item.status, reason: '' })}
                      className="bg-navy-light hover:bg-steel-dark border border-steel-dark text-white px-3 py-1.5 rounded transition-colors text-xs font-sora font-semibold"
                    >
                      Override Status
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

  return (
    <div className="space-y-6 animate-fade-in pb-12 max-w-[1600px] mx-auto relative">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-sora font-bold text-white mb-2">Activity Intelligence</h1>
          <p className="text-steel-light font-mono text-sm">Classification of operational status based on 18-month telemetry.</p>
        </div>
        <button 
          onClick={reclassifyAll}
          className="bg-saffron hover:bg-saffron-hover text-navy px-4 py-2 rounded-lg font-sora font-bold transition-colors shadow-lg flex items-center space-x-2"
        >
          <Play size={18} className="fill-current" />
          <span>Reclassify All</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 border-b border-steel-dark mb-6">
        <button 
          onClick={() => setActiveTab('overview')}
          className={`px-6 py-3 font-sora font-semibold text-sm transition-colors ${activeTab === 'overview' ? 'text-saffron border-b-2 border-saffron' : 'text-steel-light hover:text-white'}`}
        >
          Status Overview
        </button>
        <button 
          onClick={() => setActiveTab('review')}
          className={`px-6 py-3 font-sora font-semibold text-sm transition-colors flex items-center space-x-2 ${activeTab === 'review' ? 'text-saffron border-b-2 border-saffron' : 'text-steel-light hover:text-white'}`}
        >
          <span>Needs Review</span>
          {reviewQueue.length > 0 && <span className="bg-red-500 text-white text-[10px] px-1.5 py-0.5 rounded-full font-mono font-bold">{reviewQueue.length}</span>}
        </button>
        <button 
          onClick={() => setActiveTab('details')}
          className={`px-6 py-3 font-sora font-semibold text-sm transition-colors ${activeTab === 'details' ? 'text-saffron border-b-2 border-saffron' : 'text-steel-light hover:text-white'}`}
        >
          Classification Details
        </button>
      </div>

      <div className="mt-6">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'review' && renderReviewQueue()}
        {activeTab === 'details' && (
          <EmptyState 
            icon={Activity} 
            title="Classification Rules & Details" 
            description="Documentation for how the ActivityFeatureEngineer and LightGBM models compute recency, frequency, and BESCOM telemetry to score entities." 
          />
        )}
      </div>

      {/* Override Modal */}
      {overrideModal.isOpen && (
        <div className="fixed inset-0 bg-navy/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-navy border border-steel-dark rounded-xl shadow-2xl p-6 w-full max-w-md animate-fade-in">
            <h3 className="text-white font-sora font-bold text-xl mb-4">Manual Status Override</h3>
            <p className="text-steel-light text-sm mb-6">Overriding status for <span className="font-mono text-saffron">{overrideModal.ubid}</span>.</p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-steel-light mb-1">New Status</label>
                <select 
                  className="w-full bg-navy-light border border-steel-dark rounded p-2 text-white focus:outline-none focus:border-saffron"
                  value={overrideModal.status}
                  onChange={(e) => setOverrideModal({...overrideModal, status: e.target.value})}
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="DORMANT">DORMANT</option>
                  <option value="CLOSED">CLOSED</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-mono text-steel-light mb-1">Override Reason</label>
                <textarea 
                  className="w-full bg-navy-light border border-steel-dark rounded p-2 text-white focus:outline-none focus:border-saffron resize-none"
                  rows={4}
                  placeholder="Explain why the ML model prediction is incorrect..."
                  value={overrideModal.reason}
                  onChange={(e) => setOverrideModal({...overrideModal, reason: e.target.value})}
                />
                <div className={`text-right text-[10px] font-mono mt-1 ${overrideModal.reason.length < 10 ? 'text-red-400' : 'text-green-400'}`}>
                  {overrideModal.reason.length} / 10 chars required
                </div>
              </div>
            </div>

            <div className="mt-8 flex justify-end space-x-3">
              <button 
                onClick={() => setOverrideModal({ isOpen: false, ubid: null, status: 'ACTIVE', reason: '' })}
                className="px-4 py-2 text-steel-light hover:text-white transition-colors text-sm font-sora"
              >
                Cancel
              </button>
              <button 
                onClick={handleOverrideSubmit}
                disabled={overrideModal.reason.length < 10}
                className="bg-saffron hover:bg-saffron-hover text-navy px-4 py-2 rounded font-sora font-semibold transition-colors disabled:opacity-50"
              >
                Submit Override
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
