import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../api/endpoints';
import StatusBadge from '../ui/StatusBadge';
import ConfidenceBadge from '../ui/ConfidenceBadge';
import EvidenceTimeline from '../ui/EvidenceTimeline';
import LoadingSpinner from '../ui/LoadingSpinner';
import ShapWaterfall from '../ui/ShapWaterfall';
import { ArrowLeft, Clock, History, AlertTriangle, Building2, MapPin, Search } from 'lucide-react';

export default function UBIDDetail() {
  const { ubid } = useParams();
  const navigate = useNavigate();
  const [registryData, setRegistryData] = useState(null);
  const [activityData, setActivityData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Override form
  const [overrideStatus, setOverrideStatus] = useState('ACTIVE');
  const [overrideReason, setOverrideReason] = useState('');
  const [overrideLoading, setOverrideLoading] = useState(false);

  useEffect(() => {
    const fetchFullProfile = async () => {
      try {
        const [regRes, actRes] = await Promise.all([
          api.er.getUbidDetail(ubid),
          api.activity.getStatus(ubid).catch(() => ({ data: null }))
        ]);
        setRegistryData(regRes.data);
        setActivityData(actRes.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchFullProfile();
  }, [ubid]);

  const submitOverride = async () => {
    if (overrideReason.length < 10) return;
    setOverrideLoading(true);
    try {
      await api.activity.submitOverride(ubid, overrideStatus, overrideReason, 'admin');
      alert('Status overridden successfully');
      // Refresh
      const actRes = await api.activity.getStatus(ubid);
      setActivityData(actRes.data);
      setOverrideReason('');
    } catch (err) {
      alert('Failed to override status');
    } finally {
      setOverrideLoading(false);
    }
  };

  if (loading) return <LoadingSpinner text="Retrieving Golden Record..." />;
  if (!registryData) return <div className="text-red-400 p-8 flex flex-col items-center"><Search size={48} className="mb-4 opacity-50"/><h2 className="font-sora text-2xl mb-2">Record Not Found</h2><p>UBID {ubid} does not exist in the Golden Registry.</p></div>;

  const masterName = registryData.linked_records[0]?.business_name || 'Unknown Business';
  const hoursSinceClassification = activityData?.last_classified_at 
    ? Math.round((new Date() - new Date(activityData.last_classified_at)) / (1000 * 60 * 60)) 
    : null;

  const shapData = activityData?.top_signals?.map(s => ({
    feature: s.feature,
    contribution: s.contribution,
    value: s.value
  })) || [];

  const getDeptColor = (dept) => {
    switch (dept) {
      case 'FACTORIES': return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
      case 'SHOP_ESTABLISHMENT': return 'bg-purple-500/20 text-purple-400 border-purple-500/50';
      case 'LABOUR': return 'bg-teal-500/20 text-teal-400 border-teal-500/50';
      case 'KSPCB': return 'bg-orange-500/20 text-orange-400 border-orange-500/50';
      case 'BESCOM': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
      default: return 'bg-steel/20 text-steel-light border-steel/50';
    }
  };

  return (
    <div className="space-y-8 max-w-[1400px] mx-auto pb-20">
      
      {/* HEADER - Animates first */}
      <div className="flex items-center justify-between border-b border-steel-dark pb-6 animate-fade-in">
        <div className="flex items-start space-x-6">
          <button onClick={() => navigate(-1)} className="p-2 bg-navy-light text-steel-light hover:text-white rounded-full transition-colors mt-1 shrink-0">
            <ArrowLeft size={20} />
          </button>
          <div>
            <div className="flex items-center space-x-4 mb-3">
              <h1 className="text-3xl font-mono font-bold text-white tracking-wider">{ubid}</h1>
              {activityData && <div className="scale-110 origin-left"><StatusBadge status={activityData.status} /></div>}
              {registryData.pan_anchor ? (
                <span className="px-3 py-1 bg-green-500/20 text-green-400 border border-green-500/50 rounded-md font-mono text-xs font-bold uppercase">Anchored</span>
              ) : (
                <span className="px-3 py-1 bg-saffron/20 text-saffron border border-saffron/50 rounded-md font-mono text-xs font-bold uppercase">Anchor Pending</span>
              )}
            </div>
            <h2 className="text-xl font-sora text-steel-light">{masterName}</h2>
            {hoursSinceClassification !== null && (
              <div className="flex items-center text-steel-light text-xs mt-2 font-mono">
                <Clock size={12} className="mr-1.5" />
                <span>Last classified: {hoursSinceClassification === 0 ? '< 1' : hoursSinceClassification} hours ago</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* SECTION 1: Linked Department Records - Animates second */}
      <section className="animate-fade-in" style={{ animationDelay: '100ms', animationFillMode: 'both' }}>
        <h3 className="text-lg font-sora font-semibold text-white mb-4 flex items-center">
          <Building2 size={18} className="mr-2 text-steel-light" />
          Linked Department Records
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {registryData.linked_records.map(rec => (
            <div key={rec.id} className="glass-panel p-4 flex flex-col h-full border-t-2" style={{ borderTopColor: getDeptColor(rec.department).split('text-')[1]?.split(' ')[0].replace('400', '500') || '#3D5A73' }}>
              <div className="flex justify-between items-start mb-3">
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold border uppercase ${getDeptColor(rec.department)}`}>
                  {rec.department}
                </span>
                <span className="font-mono text-[10px] text-steel-light">{rec.original_record_id}</span>
              </div>
              
              <div className="flex-1">
                <h4 className="font-sora text-sm text-white font-semibold mb-2">{rec.business_name}</h4>
                <div className="flex items-start space-x-2 text-steel-light text-xs mb-3">
                  <MapPin size={14} className="shrink-0 mt-0.5" />
                  <span className="truncate">{rec.address_street}, {rec.address_pincode}</span>
                </div>
              </div>
              
              <div className="mt-4 pt-3 border-t border-steel-dark flex justify-between items-center text-xs">
                <span className="text-steel-light font-mono">PAN: {rec.pan || '---'}</span>
                {rec.confidence && <ConfidenceBadge score={rec.confidence} />}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Grid for Section 2 and 3 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* SECTION 2: Activity Evidence - Animates third */}
        <section className="lg:col-span-2 animate-fade-in space-y-6" style={{ animationDelay: '200ms', animationFillMode: 'both' }}>
          <h3 className="text-lg font-sora font-semibold text-white mb-4 flex items-center border-b border-steel-dark pb-2">
            <AlertTriangle size={18} className="mr-2 text-saffron" />
            Activity Evidence
          </h3>
          
          {activityData ? (
            <>
              {/* Styled Quote Block */}
              <div className="bg-navy-light/40 border-l-4 border-saffron p-5 rounded-r-lg shadow-lg relative">
                <span className="absolute top-2 left-2 text-4xl text-saffron/20 font-serif opacity-50">"</span>
                <p className="text-white text-sm leading-relaxed relative z-10 font-sora pl-4">
                  {activityData.evidence_summary}
                </p>
              </div>

              {/* Top Signals */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {activityData.top_signals.slice(0, 4).map((sig, idx) => (
                  <div key={idx} className="bg-navy border border-steel-dark p-3 rounded-lg flex items-center space-x-3">
                    <div className={`h-8 w-8 rounded flex items-center justify-center shrink-0 ${sig.contribution > 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                      {sig.contribution > 0 ? '✓' : '✗'}
                    </div>
                    <div>
                      <div className="text-xs font-mono text-steel-light uppercase mb-0.5">{sig.feature}</div>
                      <div className="text-sm font-sora text-white font-semibold">{sig.value}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Shap Waterfall */}
              <div className="glass-panel p-6">
                <h4 className="text-sm text-steel-light font-mono uppercase mb-4">ML Feature Contributions</h4>
                <div className="bg-navy rounded p-2">
                  <ShapWaterfall data={shapData} />
                </div>
              </div>
            </>
          ) : (
            <div className="glass-panel p-8 text-center">
              <p className="text-steel-light">No activity telemetry available. Entity is too new or lacks matched events.</p>
            </div>
          )}
        </section>

        {/* SECTION 3 & 4 Right Column */}
        <div className="space-y-8">
          
          {/* SECTION 3: Event Timeline - Animates fourth */}
          <section className="animate-fade-in" style={{ animationDelay: '300ms', animationFillMode: 'both' }}>
            <h3 className="text-lg font-sora font-semibold text-white mb-4 flex items-center border-b border-steel-dark pb-2">
              <Clock size={18} className="mr-2 text-steel-light" />
              Event Timeline
            </h3>
            <div className="glass-panel p-6 max-h-[600px] overflow-y-auto">
              {activityData?.event_timeline ? (
                <EvidenceTimeline events={activityData.event_timeline} showGaps={true} />
              ) : (
                <p className="text-sm text-steel-light">No events recorded.</p>
              )}
            </div>
          </section>

          {/* SECTION 4: Reviewer Actions - Animates fifth */}
          <section className="animate-fade-in" style={{ animationDelay: '400ms', animationFillMode: 'both' }}>
            <h3 className="text-lg font-sora font-semibold text-white mb-4 flex items-center border-b border-steel-dark pb-2">
              <History size={18} className="mr-2 text-steel-light" />
              Reviewer Actions
            </h3>
            <div className="glass-panel p-6 border-saffron/30">
              <h4 className="text-sm font-sora font-semibold text-white mb-4">Override Operational Status</h4>
              <div className="space-y-4">
                <select 
                  className="w-full bg-navy border border-steel-dark rounded p-2 text-white focus:outline-none focus:border-saffron font-sora text-sm"
                  value={overrideStatus}
                  onChange={(e) => setOverrideStatus(e.target.value)}
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="DORMANT">DORMANT</option>
                  <option value="CLOSED">CLOSED</option>
                </select>
                
                <textarea 
                  className="w-full bg-navy border border-steel-dark rounded p-3 text-sm text-white focus:outline-none focus:border-saffron resize-none font-sans"
                  rows={3}
                  placeholder="Explain your override reason (min 10 chars)..."
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                />
                
                <div className="flex justify-between items-center mt-2">
                  <span className={`text-[10px] font-mono ${overrideReason.length < 10 ? 'text-red-400' : 'text-green-400'}`}>
                    {overrideReason.length} / 10 min chars
                  </span>
                  <button 
                    onClick={submitOverride}
                    disabled={overrideReason.length < 10 || overrideLoading}
                    className="bg-saffron hover:bg-saffron-hover text-navy px-4 py-2 rounded font-sora font-semibold transition-colors disabled:opacity-50 text-sm"
                  >
                    Submit Override
                  </button>
                </div>
              </div>
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}
