import React, { useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { api } from '../../api/endpoints';
import ConfidenceBadge from '../ui/ConfidenceBadge';
import ShapWaterfall from '../ui/ShapWaterfall';
import { ArrowLeft, Check, X, AlertTriangle } from 'lucide-react';

export default function ReviewTask() {
  const { state } = useLocation();
  const { pairId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [reason, setReason] = useState('');

  const pair = state?.pair;

  if (!pair) {
    return (
      <div className="text-center p-12">
        <h2 className="text-xl text-white">No pair selected for review.</h2>
        <button onClick={() => navigate('/entity-resolution')} className="mt-4 text-saffron">Go Back</button>
      </div>
    );
  }

  const handleDecision = async (decision) => {
    if (!reason.trim()) {
      alert("Please provide a reason for your decision.");
      return;
    }
    setLoading(true);
    try {
      await api.er.submitReview(pair.pair_id, decision, reason, 'admin-123');
      navigate('/entity-resolution');
    } catch (err) {
      console.error(err);
      alert("Failed to submit decision");
      setLoading(false);
    }
  };

  const renderRecordField = (label, valA, valB, isAnchor = false) => {
    const isMatch = valA && valB && valA.toString().toLowerCase() === valB.toString().toLowerCase();
    return (
      <div className="grid grid-cols-12 gap-4 py-3 border-b border-steel-dark last:border-0">
        <div className={`col-span-2 font-mono text-xs uppercase tracking-wider ${isAnchor ? 'text-saffron font-bold' : 'text-steel-light'}`}>
          {label}
        </div>
        <div className={`col-span-5 font-sora text-sm ${isMatch ? 'text-green-400 font-semibold bg-green-900/20 p-1 -m-1 rounded' : 'text-white'}`}>
          {valA || '-'}
        </div>
        <div className={`col-span-5 font-sora text-sm ${isMatch ? 'text-green-400 font-semibold bg-green-900/20 p-1 -m-1 rounded' : 'text-white'}`}>
          {valB || '-'}
        </div>
      </div>
    );
  };

  // Convert shap object to array for chart
  const shapData = Object.entries(pair.shap_values || {}).map(([key, val]) => ({
    feature: key,
    contribution: val,
    value: pair.feature_vector[key]
  })).sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)); // Sort by absolute impact

  return (
    <div className="space-y-6 animate-fade-in max-w-6xl mx-auto pb-20">
      <div className="flex items-center space-x-4 mb-8">
        <button onClick={() => navigate('/entity-resolution')} className="p-2 bg-navy-light text-steel-light hover:text-white rounded-full transition-colors">
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1 className="text-2xl font-sora font-bold text-white flex items-center space-x-3">
            <span>Identity Resolution Task</span>
            <ConfidenceBadge score={pair.score} />
          </h1>
          <p className="text-steel-light font-mono text-sm">Reviewing ML proposed link for ID: {pair.pair_id}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Explanation */}
        <div className="col-span-1 space-y-6">
          <div className="glass-panel p-6">
            <h3 className="text-white font-sora font-semibold mb-4 flex items-center">
              <AlertTriangle size={18} className="mr-2 text-saffron" />
              Model Explainability (SHAP)
            </h3>
            <p className="text-steel-light text-xs mb-4">Positive values push the model towards MERGE. Negative values push towards KEEP SEPARATE.</p>
            <ShapWaterfall data={shapData} />
          </div>

          <div className="glass-panel p-6">
            <h3 className="text-white font-sora font-semibold mb-4">Decision</h3>
            <textarea 
              className="w-full bg-navy border border-steel-dark rounded-lg p-3 text-sm text-white focus:outline-none focus:border-saffron focus:ring-1 focus:ring-saffron font-sans mb-4"
              rows={4}
              placeholder="Provide reasoning for your decision (required)..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            
            <div className="flex space-x-3">
              <button 
                onClick={() => handleDecision('MERGE')}
                disabled={loading}
                className="flex-1 bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/50 py-2 rounded-lg flex items-center justify-center space-x-2 font-sora font-semibold transition-colors disabled:opacity-50"
              >
                <Check size={18} />
                <span>MERGE</span>
              </button>
              <button 
                onClick={() => handleDecision('KEEP_SEPARATE')}
                disabled={loading}
                className="flex-1 bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/50 py-2 rounded-lg flex items-center justify-center space-x-2 font-sora font-semibold transition-colors disabled:opacity-50"
              >
                <X size={18} />
                <span>SEPARATE</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Col: Comparison */}
        <div className="col-span-2 glass-panel p-0 overflow-hidden">
          <div className="grid grid-cols-12 gap-4 p-4 bg-navy-light border-b border-steel-dark font-sora font-semibold text-white">
            <div className="col-span-2"></div>
            <div className="col-span-5 flex flex-col">
              <span className="text-saffron mb-1">Incoming Record</span>
              <span className="font-mono text-xs text-steel-light font-normal">{pair.record_a.department}</span>
            </div>
            <div className="col-span-5 flex flex-col">
              <span className="text-blue-400 mb-1">Target Record</span>
              <span className="font-mono text-xs text-steel-light font-normal">{pair.record_b.department}</span>
            </div>
          </div>
          
          <div className="p-4">
            {renderRecordField('Business Name', pair.record_a.business_name, pair.record_b.business_name)}
            {renderRecordField('PAN', pair.record_a.pan, pair.record_b.pan, true)}
            {renderRecordField('GSTIN', pair.record_a.gstin, pair.record_b.gstin, true)}
            {renderRecordField('Street', pair.record_a.address_street, pair.record_b.address_street)}
            {renderRecordField('Locality', pair.record_a.address_locality, pair.record_b.address_locality)}
            {renderRecordField('Pincode', pair.record_a.address_pincode, pair.record_b.address_pincode)}
            {renderRecordField('District', pair.record_a.address_district, pair.record_b.address_district)}
            {renderRecordField('Phone', pair.record_a.phone, pair.record_b.phone)}
            {renderRecordField('Signatory', pair.record_a.signatory_name, pair.record_b.signatory_name)}
          </div>
        </div>
      </div>
    </div>
  );
}
