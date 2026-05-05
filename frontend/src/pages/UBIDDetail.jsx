import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../api/endpoints';
import StatusBadge from '../ui/StatusBadge';
import ConfidenceBadge from '../ui/ConfidenceBadge';
import EvidenceTimeline from '../ui/EvidenceTimeline';
import LoadingSpinner from '../ui/LoadingSpinner';
import ShapWaterfall from '../ui/ShapWaterfall';
import { ArrowLeft, Building2, MapPin, Phone, Mail, Link as LinkIcon } from 'lucide-react';

export default function UBIDDetail() {
  const { ubid } = useParams();
  const navigate = useNavigate();
  const [registryData, setRegistryData] = useState(null);
  const [activityData, setActivityData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFullProfile = async () => {
      try {
        const [regRes, actRes] = await Promise.all([
          api.er.getUbidDetail(ubid),
          api.activity.getStatus(ubid).catch(() => ({ data: null })) // May not have activity yet
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

  if (loading) return <LoadingSpinner text="Assembling Golden Record..." />;
  if (!registryData) return <div className="text-red-400 p-8">UBID not found or system error.</div>;

  // Derive master profile from linked records
  const masterName = registryData.linked_records[0]?.business_name || 'Unknown Business';
  const masterAddress = registryData.linked_records[0] ? `${registryData.linked_records[0].address_street}, ${registryData.linked_records[0].address_locality}, ${registryData.linked_records[0].address_pincode}` : 'Address not available';

  const shapData = activityData?.top_signals?.map(s => ({
    feature: s.feature,
    contribution: s.contribution,
    value: s.value
  })) || [];

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto pb-20">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <button onClick={() => navigate(-1)} className="p-2 bg-navy-light text-steel-light hover:text-white rounded-full transition-colors">
            <ArrowLeft size={20} />
          </button>
          <div>
            <div className="flex items-center space-x-3 mb-1">
              <h1 className="text-2xl font-sora font-bold text-white">{masterName}</h1>
              {activityData && <StatusBadge status={activityData.status} />}
            </div>
            <p className="text-saffron font-mono text-sm tracking-wider">{ubid}</p>
          </div>
        </div>
        
        {registryData.pan_anchor && (
          <div className="glass-panel px-4 py-2 border-saffron/30">
            <span className="text-steel-light text-xs uppercase block mb-1">PAN Anchor</span>
            <span className="font-mono text-white tracking-widest">{registryData.pan_anchor}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Col: Master Identity & Links */}
        <div className="col-span-1 space-y-6">
          <div className="glass-panel p-6">
            <h3 className="text-white font-sora font-semibold mb-4 border-b border-steel-dark pb-2">Master Identity</h3>
            <div className="space-y-4">
              <div className="flex items-start space-x-3 text-steel-light">
                <MapPin size={18} className="shrink-0 mt-0.5" />
                <span className="text-sm">{masterAddress}</span>
              </div>
              <div className="flex items-center space-x-3 text-steel-light">
                <Phone size={18} />
                <span className="text-sm font-mono">{registryData.linked_records[0]?.phone || 'N/A'}</span>
              </div>
              <div className="flex items-center space-x-3 text-steel-light">
                <Mail size={18} />
                <span className="text-sm">{registryData.linked_records[0]?.email || 'N/A'}</span>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6">
            <h3 className="text-white font-sora font-semibold mb-4 border-b border-steel-dark pb-2 flex items-center">
              <LinkIcon size={18} className="mr-2" />
              Linked Registrations ({registryData.linked_records.length})
            </h3>
            <div className="space-y-3">
              {registryData.linked_records.map(rec => (
                <div key={rec.id} className="bg-navy p-3 rounded border border-steel-dark">
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-mono text-xs text-saffron">{rec.department}</span>
                    <span className="font-mono text-[10px] text-steel-light">{rec.original_record_id}</span>
                  </div>
                  <div className="text-white font-sora text-sm truncate">{rec.business_name}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Middle Col: ML Explainability */}
        <div className="col-span-1 space-y-6">
          {activityData ? (
            <>
              <div className="glass-panel p-6">
                <div className="flex justify-between items-center mb-4 border-b border-steel-dark pb-2">
                  <h3 className="text-white font-sora font-semibold">Activity Evidence</h3>
                  <ConfidenceBadge score={activityData.confidence} />
                </div>
                <p className="text-sm text-steel-light leading-relaxed mb-6">
                  {activityData.evidence_summary}
                </p>
                
                <h4 className="text-xs font-mono text-steel-light uppercase mb-3">Model Top Drivers</h4>
                <div className="bg-navy rounded p-2">
                  <ShapWaterfall data={shapData} />
                </div>
              </div>
            </>
          ) : (
            <div className="glass-panel p-6 flex flex-col items-center justify-center text-center h-full">
              <Building2 size={32} className="text-steel-dark mb-4" />
              <p className="text-steel-light">No activity telemetry available for this entity yet.</p>
            </div>
          )}
        </div>

        {/* Right Col: Timeline */}
        <div className="col-span-1 glass-panel p-6">
          <h3 className="text-white font-sora font-semibold mb-6 border-b border-steel-dark pb-2 flex items-center">
            <Clock size={18} className="mr-2" />
            Operational Timeline
          </h3>
          <div className="h-[600px] overflow-y-auto pr-2">
            {activityData?.event_timeline ? (
              <EvidenceTimeline events={activityData.event_timeline} />
            ) : (
              <p className="text-sm text-steel-light">No events recorded.</p>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
