import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { api } from '../../api/endpoints';
import ShapWaterfall from '../ui/ShapWaterfall';
import { ArrowLeft, Check, CheckCircle2, X, AlertTriangle, ArrowUpRight } from 'lucide-react';
import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis } from 'recharts';

export default function ReviewTask() {
  const { state } = useLocation();
  const { pairId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [reason, setReason] = useState('');
  
  // In a real app we might fetch the pair if not in state
  const pair = state?.pair;

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignore if typing in textarea
      if (e.target.tagName.toLowerCase() === 'textarea') return;
      
      const isReady = reason.trim().length >= 10 && !loading;
      if (!isReady) return;

      if (e.key.toLowerCase() === 'm') handleDecision('MERGE');
      if (e.key.toLowerCase() === 's') handleDecision('KEEP_SEPARATE');
      if (e.key.toLowerCase() === 'e') handleDecision('ESCALATE');
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [reason, loading]);

  if (!pair) {
    return (
      <div className="text-center p-12">
        <h2 className="text-xl text-white">No pair selected for review.</h2>
        <button onClick={() => navigate('/entity-resolution')} className="mt-4 text-saffron">Go Back</button>
      </div>
    );
  }

  const handleDecision = async (decision) => {
    if (reason.trim().length < 10) return;
    setLoading(true);
    try {
      await api.er.submitReview(pair.pair_id, decision, reason, 'admin-123');
      alert(`Successfully submitted: ${decision}`);
      navigate('/entity-resolution');
    } catch (err) {
      console.error(err);
      alert("Failed to submit decision");
      setLoading(false);
    }
  };

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

  const getScoreColorHex = (score) => {
    if (score > 0.80) return '#4ADE80'; // Green
    if (score >= 0.65) return '#F4A500'; // Amber/Saffron
    return '#F87171'; // Red
  };

  const renderField = (label, valA, valB, isRightCol) => {
    const isMatch = valA && valB && valA.toString().toLowerCase() === valB.toString().toLowerCase();
    const isDifferent = valA && valB && !isMatch;
    
    // For right col, highlight differences in amber, show checkmark for matches
    let valueClass = "text-white";
    let icon = null;

    if (isRightCol) {
      if (isMatch) {
        valueClass = "text-white";
        icon = <CheckCircle2 size={14} className="text-green-400 ml-2 shrink-0" />;
      } else if (isDifferent) {
        valueClass = "text-saffron font-bold bg-saffron/10 px-1 -ml-1 rounded";
      }
    }

    const displayVal = isRightCol ? valB : valA;

    return (
      <div className="mb-4">
        <div className="text-[10px] uppercase font-mono tracking-widest text-steel-light mb-1">{label}</div>
        <div className="flex items-center">
          {displayVal ? (
            <span className={`font-sora text-sm ${valueClass}`}>{displayVal}</span>
          ) : (
            <span className="font-mono text-xs text-steel-dark italic">Not Available</span>
          )}
          {icon}
        </div>
      </div>
    );
  };

  const shapData = Object.entries(pair.shap_values || {}).map(([key, val]) => ({
    feature: key,
    contribution: val,
    value: pair.feature_vector[key]
  })).sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));

  const radialData = [{ name: 'Score', value: pair.score * 100, fill: getScoreColorHex(pair.score) }];
  const scorePercent = (pair.score * 100).toFixed(1);

  return (
    <div className="space-y-6 animate-fade-in max-w-[1600px] mx-auto pb-12">
      <div className="flex items-center space-x-4 mb-6 border-b border-steel-dark pb-4">
        <button onClick={() => navigate('/entity-resolution')} className="p-2 bg-navy-light text-steel-light hover:text-white rounded-full transition-colors">
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1 className="text-2xl font-sora font-bold text-white flex items-center space-x-3">
            <span>Identity Resolution Task</span>
          </h1>
          <p className="text-steel-light font-mono text-sm">Evaluating Pair: {pair.pair_id}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN - Record A */}
        <div className="glass-panel p-6 flex flex-col h-full border-t-4 border-t-blue-500/50">
          <div className="flex justify-between items-start mb-6 border-b border-steel-dark pb-4">
            <div>
              <span className="text-steel-light text-xs font-mono uppercase block mb-1">Incoming Record (A)</span>
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold border uppercase ${getDeptColor(pair.record_a.department)}`}>
                {pair.record_a.department}
              </span>
            </div>
            <div className="text-right">
              <span className="text-steel-dark text-xs font-mono block">ID: {pair.record_a.original_record_id}</span>
            </div>
          </div>
          
          <div className="flex-1">
            <div className="mb-6">
              <h2 className="text-xl font-sora font-bold text-white mb-1">{pair.record_a.business_name || 'N/A'}</h2>
              <p className="font-mono text-xs text-steel-light italic">{pair.record_a.business_name_normalized || 'N/A'}</p>
            </div>
            
            <div className="space-y-1">
              {renderField('Address', pair.record_a.address_raw, pair.record_b.address_raw, false)}
              <div className="grid grid-cols-2 gap-4">
                {renderField('PIN Code', pair.record_a.address_pincode, pair.record_b.address_pincode, false)}
                {renderField('Registration Date', pair.record_a.registration_date, pair.record_b.registration_date, false)}
              </div>
              <div className="grid grid-cols-2 gap-4">
                {renderField('PAN', pair.record_a.pan, pair.record_b.pan, false)}
                {renderField('GSTIN', pair.record_a.gstin, pair.record_b.gstin, false)}
              </div>
            </div>
          </div>
        </div>

        {/* CENTER COLUMN - Evidence & Decision */}
        <div className="flex flex-col space-y-6">
          
          {/* Evidence Card */}
          <div className="glass-panel p-6 flex-1 flex flex-col items-center">
            <h3 className="text-white font-sora font-semibold w-full text-center mb-2">Model Confidence</h3>
            <p className="text-steel-light text-xs font-mono w-full text-center mb-4">Probability these are the same business</p>
            
            <div className="relative h-40 w-40 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart 
                  cx="50%" cy="50%" 
                  innerRadius="70%" outerRadius="100%" 
                  barSize={10} 
                  data={radialData}
                  startAngle={90} endAngle={-270}
                >
                  <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
                  <RadialBar background={{ fill: '#1B263B' }} clockWise dataKey="value" cornerRadius={5} />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex items-center justify-center flex-col">
                <span className={`text-2xl font-mono font-bold`} style={{ color: getScoreColorHex(pair.score) }}>{scorePercent}%</span>
              </div>
            </div>

            <div className="w-full mt-6 mb-4">
              <span className="text-steel-light text-xs font-mono uppercase mb-2 block">Top SHAP Contributions</span>
              <div className="bg-navy p-2 rounded border border-steel-dark">
                <ShapWaterfall data={shapData.slice(0, 5)} />
              </div>
            </div>

            <div className="w-full">
              <span className="text-steel-light text-xs font-mono uppercase mb-2 block">Triggered Blocking Passes</span>
              <div className="flex flex-wrap gap-2">
                {pair.blocking_signals.map(sig => (
                  <span key={sig} className="px-2 py-1 text-[10px] font-mono rounded bg-steel-dark text-steel-lightest uppercase">
                    {sig.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Decision Card */}
          <div className="glass-panel p-6 bg-navy/95 border-saffron/30 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-saffron/50"></div>
            
            <textarea 
              className="w-full bg-navy border border-steel-dark rounded p-3 text-sm text-white focus:outline-none focus:border-saffron focus:ring-1 focus:ring-saffron font-sans mb-2 resize-none"
              rows={3}
              placeholder="Explain your decision (minimum 10 characters)..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <div className="flex justify-between items-center mb-4">
              <span className={`text-[10px] font-mono ${reason.length < 10 ? 'text-red-400' : 'text-green-400'}`}>
                {reason.length} / 10 min chars
              </span>
              <span className="text-[10px] font-mono text-steel-light">Keyboard shortcuts enabled</span>
            </div>
            
            <div className="flex space-x-3">
              <button 
                onClick={() => handleDecision('MERGE')}
                disabled={loading || reason.length < 10}
                className="flex-1 bg-green-500 text-navy hover:bg-green-400 py-3 rounded-lg flex flex-col items-center justify-center font-sora font-bold transition-colors disabled:opacity-30 disabled:cursor-not-allowed group relative"
              >
                <div className="flex items-center space-x-2">
                  <Check size={18} />
                  <span>MERGE</span>
                </div>
                <span className="absolute bottom-1 right-2 text-[9px] font-mono opacity-50 group-hover:opacity-100">[M]</span>
              </button>
              
              <button 
                onClick={() => handleDecision('KEEP_SEPARATE')}
                disabled={loading || reason.length < 10}
                className="flex-1 bg-red-500 text-white hover:bg-red-400 py-3 rounded-lg flex flex-col items-center justify-center font-sora font-bold transition-colors disabled:opacity-30 disabled:cursor-not-allowed group relative"
              >
                <div className="flex items-center space-x-2">
                  <X size={18} />
                  <span>SEPARATE</span>
                </div>
                <span className="absolute bottom-1 right-2 text-[9px] font-mono opacity-50 group-hover:opacity-100">[S]</span>
              </button>

              <button 
                onClick={() => handleDecision('ESCALATE')}
                disabled={loading || reason.length < 10}
                className="flex-1 bg-saffron text-navy hover:bg-saffron-hover py-3 rounded-lg flex flex-col items-center justify-center font-sora font-bold transition-colors disabled:opacity-30 disabled:cursor-not-allowed group relative"
              >
                <div className="flex items-center space-x-2">
                  <ArrowUpRight size={18} />
                  <span>ESCALATE</span>
                </div>
                <span className="absolute bottom-1 right-2 text-[9px] font-mono opacity-50 group-hover:opacity-100">[E]</span>
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN - Record B */}
        <div className="glass-panel p-6 flex flex-col h-full border-t-4 border-t-saffron/50 bg-navy-light/20">
          <div className="flex justify-between items-start mb-6 border-b border-steel-dark pb-4">
            <div>
              <span className="text-steel-light text-xs font-mono uppercase block mb-1">Target Golden Record (B)</span>
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold border uppercase ${getDeptColor(pair.record_b.department)}`}>
                {pair.record_b.department}
              </span>
            </div>
            <div className="text-right">
              <span className="text-steel-dark text-xs font-mono block">ID: {pair.record_b.original_record_id}</span>
            </div>
          </div>
          
          <div className="flex-1">
            <div className="mb-6">
              <h2 className="text-xl font-sora font-bold text-white mb-1 flex items-center">
                {pair.record_b.business_name || 'N/A'}
                {pair.record_a.business_name === pair.record_b.business_name && <CheckCircle2 size={18} className="text-green-400 ml-2 shrink-0" />}
              </h2>
              <p className="font-mono text-xs text-steel-light italic">{pair.record_b.business_name_normalized || 'N/A'}</p>
            </div>
            
            <div className="space-y-1">
              {renderField('Address', pair.record_a.address_raw, pair.record_b.address_raw, true)}
              <div className="grid grid-cols-2 gap-4">
                {renderField('PIN Code', pair.record_a.address_pincode, pair.record_b.address_pincode, true)}
                {renderField('Registration Date', pair.record_a.registration_date, pair.record_b.registration_date, true)}
              </div>
              <div className="grid grid-cols-2 gap-4">
                {renderField('PAN', pair.record_a.pan, pair.record_b.pan, true)}
                {renderField('GSTIN', pair.record_a.gstin, pair.record_b.gstin, true)}
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
