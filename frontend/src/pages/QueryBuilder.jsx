import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/endpoints';
import StatusBadge from '../ui/StatusBadge';
import ConfidenceBadge from '../ui/ConfidenceBadge';
import EmptyState from '../ui/EmptyState';
import { Search, Filter, Database, ArrowRight, Download, Code, CheckCircle2, Circle, Factory, ShieldAlert, FileText, Zap, HelpCircle } from 'lucide-react';

export default function QueryBuilder() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [queryInfo, setQueryInfo] = useState(null);
  
  const [filters, setFilters] = useState({
    status: '', // '' = ALL
    departments: [],
    pincode: '',
    no_inspection_since_months: 0,
    nic_code_prefix: '',
    min_confidence: 0.5
  });

  const toggleDept = (dept) => {
    if (filters.departments.includes(dept)) {
      setFilters({ ...filters, departments: filters.departments.filter(d => d !== dept) });
    } else {
      setFilters({ ...filters, departments: [...filters.departments, dept] });
    }
  };

  const handlePreFill = () => {
    setFilters({
      status: 'ACTIVE',
      departments: ['FACTORIES'],
      pincode: '560058',
      no_inspection_since_months: 18,
      nic_code_prefix: '',
      min_confidence: 0.8
    });
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    // The backend expects a single `department` string currently, we'll pass the first selected
    // or join them if the backend is upgraded. For the demo, pass the first one.
    const dept = filters.departments.length > 0 ? filters.departments[0] : '';

    const params = {
      ...(filters.status && { status: filters.status }),
      ...(dept && { department: dept }),
      ...(filters.pincode && { pincode: filters.pincode }),
      ...(filters.no_inspection_since_months > 0 && { no_inspection_since_months: filters.no_inspection_since_months }),
      ...(filters.nic_code_prefix && { nic_code_prefix: filters.nic_code_prefix }),
      ...(filters.min_confidence > 0.5 && { min_confidence: filters.min_confidence }),
      limit: 50
    };

    try {
      const res = await api.activity.crossDeptQuery(params);
      setResults(res.data.results);
      setQueryInfo({
        interp: res.data.query_interpreted_as,
        sql: res.data.query_sql,
        total: res.data.total_results
      });
    } catch (err) {
      console.error(err);
      alert("Query failed");
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    if (!results || results.length === 0) return;
    
    const headers = ['UBID', 'Business Name', 'Status', 'Confidence', 'Pincode', 'District'];
    const csvContent = "data:text/csv;charset=utf-8," 
      + headers.join(',') + '\n'
      + results.map(r => `${r.ubid},"${r.business_name}",${r.status},${r.confidence},${r.pincode},${r.district}`).join('\n');
      
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "udyam_setu_query_results.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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

  const getIconForDept = (dept) => {
    switch (dept) {
      case 'FACTORIES': return <Factory size={16} />;
      case 'KSPCB': return <ShieldAlert size={16} />;
      case 'SHOP_ESTABLISHMENT': return <FileText size={16} />;
      case 'BESCOM': return <Zap size={16} />;
      default: return null;
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-20 max-w-[1400px] mx-auto">
      
      {/* HERO SECTION */}
      <div className="text-center py-8">
        <h1 className="text-4xl font-sora font-bold text-white mb-3">Cross-Department Intelligence Query</h1>
        <p className="text-steel-light font-mono text-base max-w-2xl mx-auto">
          Ask complex targeting questions that no single siloed department system can answer on its own.
        </p>
      </div>

      <div className="glass-panel p-6 border-saffron/30 relative overflow-hidden bg-gradient-to-r from-navy to-navy-light max-w-3xl mx-auto">
        <div className="absolute top-0 left-0 w-1 h-full bg-saffron"></div>
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div>
            <span className="text-[10px] uppercase font-mono text-saffron tracking-widest block mb-2">Featured Query</span>
            <p className="text-lg text-white font-sora italic leading-relaxed">
              "Active factories in PIN 560058 with no inspection in the last 18 months"
            </p>
          </div>
          <button 
            onClick={handlePreFill}
            className="shrink-0 bg-saffron/20 hover:bg-saffron text-saffron hover:text-navy border border-saffron/50 px-4 py-2 rounded font-sora font-semibold transition-colors flex items-center space-x-2"
          >
            <span>Run This Query</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* QUERY FORM */}
      <div className="glass-panel p-8 max-w-5xl mx-auto">
        <div className="flex items-center space-x-2 mb-8 border-b border-steel-dark pb-4">
          <Filter size={20} className="text-saffron" />
          <h3 className="text-xl text-white font-sora font-semibold">Query Parameters</h3>
        </div>
        
        <form onSubmit={handleSearch} className="space-y-8">
          
          {/* Status Toggles */}
          <div>
            <label className="block text-xs font-mono text-steel-light mb-3 uppercase tracking-wider">Business Status</label>
            <div className="flex flex-wrap gap-3">
              {[
                { val: '', label: 'ALL' },
                { val: 'ACTIVE', label: 'ACTIVE' },
                { val: 'DORMANT', label: 'DORMANT' },
                { val: 'CLOSED', label: 'CLOSED' }
              ].map(opt => (
                <button
                  key={opt.val}
                  type="button"
                  onClick={() => setFilters({...filters, status: opt.val})}
                  className={`px-6 py-2 rounded-lg font-sora font-semibold text-sm transition-colors border ${
                    filters.status === opt.val 
                      ? 'bg-saffron text-navy border-saffron shadow-[0_0_15px_rgba(244,165,0,0.3)]' 
                      : 'bg-navy border-steel-dark text-steel-light hover:text-white hover:border-steel-light'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* PIN Code */}
            <div>
              <label className="block text-xs font-mono text-steel-light mb-2 uppercase tracking-wider">PIN Code</label>
              <input 
                type="text" 
                placeholder="e.g. 560058"
                maxLength={6}
                className="w-full bg-navy border border-steel-dark rounded-lg p-3 text-white focus:outline-none focus:border-saffron focus:ring-1 focus:ring-saffron font-mono text-lg transition-colors"
                value={filters.pincode}
                onChange={e => setFilters({...filters, pincode: e.target.value.replace(/\D/g, '')})}
              />
            </div>
            
            {/* NIC Code */}
            <div>
              <label className="flex items-center text-xs font-mono text-steel-light mb-2 uppercase tracking-wider group relative">
                NIC Code Prefix
                <HelpCircle size={14} className="ml-2 text-steel-dark cursor-help group-hover:text-steel-light transition-colors" />
                <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-64 bg-navy-light text-steel-lightest text-xs p-2 rounded shadow-xl border border-steel-dark z-10 normal-case font-sans">
                  e.g. "13" for Textiles, "10" for Food Processing
                </div>
              </label>
              <input 
                type="text" 
                placeholder="e.g. 13"
                className="w-full bg-navy border border-steel-dark rounded-lg p-3 text-white focus:outline-none focus:border-saffron focus:ring-1 focus:ring-saffron font-mono text-lg transition-colors"
                value={filters.nic_code_prefix}
                onChange={e => setFilters({...filters, nic_code_prefix: e.target.value.replace(/\D/g, '')})}
              />
            </div>
          </div>

          {/* Department Presence */}
          <div>
            <label className="block text-xs font-mono text-steel-light mb-3 uppercase tracking-wider">Department Presence (Must exist in)</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { id: 'FACTORIES', label: 'Factories', icon: <Factory size={18} /> },
                { id: 'SHOP_ESTABLISHMENT', label: 'Shop & Est', icon: <FileText size={18} /> },
                { id: 'KSPCB', label: 'KSPCB (Pollution)', icon: <ShieldAlert size={18} /> },
                { id: 'BESCOM', label: 'BESCOM', icon: <Zap size={18} /> }
              ].map(dept => {
                const isActive = filters.departments.includes(dept.id);
                return (
                  <button
                    key={dept.id}
                    type="button"
                    onClick={() => toggleDept(dept.id)}
                    className={`flex items-center p-3 rounded-lg border transition-colors text-left ${
                      isActive 
                        ? 'bg-navy-light border-saffron text-white' 
                        : 'bg-navy border-steel-dark text-steel-light hover:border-steel-light'
                    }`}
                  >
                    <div className={`mr-3 ${isActive ? 'text-saffron' : 'text-steel-dark'}`}>
                      {isActive ? <CheckCircle2 size={18} /> : <Circle size={18} />}
                    </div>
                    <div className={`mr-3 ${isActive ? 'text-saffron' : 'text-steel-dark'}`}>
                      {dept.icon}
                    </div>
                    <span className="font-sora text-sm font-semibold">{dept.label}</span>
                  </button>
                )
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            {/* No Inspection Since Slider */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <label className="text-xs font-mono text-steel-light uppercase tracking-wider">No Inspection Since</label>
                <span className="text-saffron font-mono font-bold">{filters.no_inspection_since_months === 0 ? 'Any Time' : `${filters.no_inspection_since_months} months`}</span>
              </div>
              <input 
                type="range" 
                min="0" max="36" step="1"
                className="w-full accent-saffron h-2 bg-steel-dark rounded-lg appearance-none cursor-pointer"
                value={filters.no_inspection_since_months}
                onChange={e => setFilters({...filters, no_inspection_since_months: parseInt(e.target.value)})}
              />
              <div className="flex justify-between text-[10px] font-mono text-steel-dark mt-2">
                <span>0m</span>
                <span>12m</span>
                <span>24m</span>
                <span>36m</span>
              </div>
            </div>

            {/* Minimum Confidence Slider */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <label className="text-xs font-mono text-steel-light uppercase tracking-wider">Minimum AI Confidence</label>
                <span className="text-saffron font-mono font-bold">{filters.min_confidence.toFixed(2)}</span>
              </div>
              <input 
                type="range" 
                min="0.5" max="1.0" step="0.05"
                className="w-full accent-saffron h-2 bg-steel-dark rounded-lg appearance-none cursor-pointer"
                value={filters.min_confidence}
                onChange={e => setFilters({...filters, min_confidence: parseFloat(e.target.value)})}
              />
              <div className="flex justify-between text-[10px] font-mono text-steel-dark mt-2">
                <span>0.5</span>
                <span>0.6</span>
                <span>0.7</span>
                <span>0.8</span>
                <span>0.9</span>
                <span>1.0</span>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-steel-dark">
            <button 
              type="submit"
              disabled={loading}
              className="w-full bg-saffron hover:bg-saffron-hover text-navy font-sora font-bold text-lg py-4 rounded-xl flex items-center justify-center space-x-2 transition-all shadow-[0_0_30px_rgba(244,165,0,0.2)] hover:shadow-[0_0_40px_rgba(244,165,0,0.4)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Search size={22} />
              <span>{loading ? 'Querying State Repositories...' : 'Run Query'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* LOADING STATE */}
      {loading && (
        <div className="max-w-5xl mx-auto space-y-4">
          <div className="text-center py-8">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-saffron/20 mb-4 animate-pulse">
              <Database size={24} className="text-saffron" />
            </div>
            <p className="text-saffron font-mono text-sm animate-pulse">Querying across isolated departments...</p>
          </div>
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-navy-light animate-pulse rounded-xl border border-steel-dark"></div>
          ))}
        </div>
      )}

      {/* RESULTS SECTION */}
      {!loading && results && (
        <div className="max-w-5xl mx-auto space-y-6 mt-12 animate-fade-in">
          
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <h2 className="text-2xl font-sora font-bold text-white">Query Results</h2>
            <button 
              onClick={exportToCSV}
              className="bg-navy-light hover:bg-steel-dark text-white border border-steel-dark px-4 py-2 rounded-lg font-sora font-semibold transition-colors flex items-center space-x-2"
            >
              <Download size={18} />
              <span>Export to CSV</span>
            </button>
          </div>

          {queryInfo && (
            <div className="glass-panel p-6 border-l-4 border-l-saffron">
              <div className="flex items-start space-x-4">
                <div className="p-2 bg-saffron/10 rounded text-saffron shrink-0">
                  <Database size={24} />
                </div>
                <div>
                  <h3 className="text-steel-light text-xs font-mono uppercase mb-2">Query Interpretation</h3>
                  <p className="text-white font-sora text-sm leading-relaxed mb-4">
                    "You asked: {queryInfo.interp}"
                  </p>
                  <p className="text-green-400 font-mono text-sm font-semibold">
                    Found {queryInfo.total} businesses matching your exact criteria.
                  </p>
                </div>
              </div>
            </div>
          )}

          {results.length === 0 ? (
            <EmptyState 
              icon={Search} 
              title="No matches found" 
              description="Zero businesses match this strict criteria. Try relaxing your filters or decreasing the 'No Inspection Since' threshold." 
            />
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {results.map((row) => (
                <div 
                  key={row.ubid} 
                  onClick={() => navigate(`/ubid/${row.ubid}`)}
                  className="glass-panel p-6 hover:border-saffron/50 transition-colors cursor-pointer group"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="font-mono text-xs text-saffron group-hover:underline">{row.ubid}</span>
                        <StatusBadge status={row.status} />
                        <ConfidenceBadge score={row.confidence} />
                      </div>
                      <h3 className="text-xl font-sora font-bold text-white mb-3">{row.business_name}</h3>
                      
                      <div className="flex flex-wrap gap-2 mb-4">
                        {row.linked_departments.map(d => (
                          <span key={d} className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium border uppercase ${getDeptColor(d)}`}>
                            {getIconForDept(d)}
                            <span className="ml-1.5">{d}</span>
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="md:text-right border-t md:border-t-0 md:border-l border-steel-dark pt-4 md:pt-0 md:pl-6 shrink-0 min-w-[200px]">
                      <div className="mb-3">
                        <span className="text-[10px] font-mono text-steel-light uppercase block mb-1">Key Insight</span>
                        <span className="text-sm font-sora text-red-400 font-semibold bg-red-400/10 px-2 py-1 rounded">
                          {filters.no_inspection_since_months > 0 
                            ? `Last inspection: >${filters.no_inspection_since_months}m ago` 
                            : 'Matched all criteria'}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] font-mono text-steel-light uppercase block mb-1">Location</span>
                        <span className="text-sm font-mono text-white">{row.pincode} • {row.district}</span>
                      </div>
                    </div>

                  </div>
                  
                  <div className="mt-4 pt-4 border-t border-steel-dark">
                    <p className="text-xs text-steel-light line-clamp-2 leading-relaxed">
                      {row.evidence_summary}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {queryInfo?.sql && (
            <details className="mt-8 bg-navy-light/30 border border-steel-dark rounded-lg overflow-hidden group">
              <summary className="cursor-pointer p-4 flex items-center text-steel-light hover:text-white font-mono text-sm transition-colors select-none">
                <Code size={16} className="mr-2" />
                <span>View Raw SQL Execution Logic</span>
              </summary>
              <div className="p-4 border-t border-steel-dark bg-navy">
                <pre className="text-[10px] font-mono text-steel-lightest overflow-x-auto whitespace-pre-wrap leading-relaxed">
                  {queryInfo.sql}
                </pre>
              </div>
            </details>
          )}

        </div>
      )}

    </div>
  );
}
