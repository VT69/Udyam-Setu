import React, { useState } from 'react';
import { api } from '../../api/endpoints';
import StatusBadge from '../ui/StatusBadge';
import EmptyState from '../ui/EmptyState';
import { Search, Filter, Database, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function QueryBuilder() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [queryInfo, setQueryInfo] = useState(null);
  
  const [filters, setFilters] = useState({
    status: '',
    department: '',
    pincode: '',
    no_inspection_since_months: '',
    nic_code_prefix: ''
  });

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Clean empty strings
    const params = Object.fromEntries(
      Object.entries(filters).filter(([_, v]) => v !== '')
    );

    try {
      const res = await api.activity.crossDeptQuery({ ...params, limit: 50 });
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

  return (
    <div className="space-y-6 animate-fade-in pb-12 max-w-7xl mx-auto">
      <div>
        <h1 className="text-3xl font-sora font-bold text-white mb-2">Cross-Department Targeting</h1>
        <p className="text-steel-light font-mono text-sm">Query the golden registry combining operational status with specific regulatory criteria.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Col: Query Form */}
        <div className="col-span-1 glass-panel p-6">
          <div className="flex items-center space-x-2 mb-6 border-b border-steel-dark pb-2">
            <Filter size={18} className="text-saffron" />
            <h3 className="text-white font-sora font-semibold">Query Parameters</h3>
          </div>
          
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-steel-light mb-1">Operational Status</label>
              <select 
                className="w-full bg-navy border border-steel-dark rounded p-2 text-sm text-white focus:border-saffron focus:ring-1 focus:ring-saffron"
                value={filters.status}
                onChange={e => setFilters({...filters, status: e.target.value})}
              >
                <option value="">Any</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="DORMANT">DORMANT</option>
                <option value="CLOSED">CLOSED</option>
              </select>
            </div>
            
            <div>
              <label className="block text-xs font-mono text-steel-light mb-1">Registered Department</label>
              <select 
                className="w-full bg-navy border border-steel-dark rounded p-2 text-sm text-white focus:border-saffron focus:ring-1 focus:ring-saffron"
                value={filters.department}
                onChange={e => setFilters({...filters, department: e.target.value})}
              >
                <option value="">Any</option>
                <option value="FACTORIES">Factories</option>
                <option value="SHOP_ESTABLISHMENT">Shop & Establishment</option>
                <option value="KSPCB">KSPCB (Pollution)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono text-steel-light mb-1">Pincode</label>
              <input 
                type="text" 
                placeholder="e.g. 560058"
                className="w-full bg-navy border border-steel-dark rounded p-2 text-sm text-white focus:border-saffron focus:ring-1 focus:ring-saffron"
                value={filters.pincode}
                onChange={e => setFilters({...filters, pincode: e.target.value})}
              />
            </div>
            
            <div>
              <label className="block text-xs font-mono text-steel-light mb-1">No Inspection in Months</label>
              <input 
                type="number" 
                placeholder="e.g. 18"
                className="w-full bg-navy border border-steel-dark rounded p-2 text-sm text-white focus:border-saffron focus:ring-1 focus:ring-saffron"
                value={filters.no_inspection_since_months}
                onChange={e => setFilters({...filters, no_inspection_since_months: e.target.value})}
              />
            </div>

            <button 
              type="submit"
              disabled={loading}
              className="w-full mt-6 bg-saffron hover:bg-saffron-hover text-navy font-sora font-semibold py-2 rounded-lg flex items-center justify-center space-x-2 transition-colors disabled:opacity-50"
            >
              <Search size={18} />
              <span>{loading ? 'Searching...' : 'Run Query'}</span>
            </button>
          </form>
        </div>

        {/* Right Col: Results */}
        <div className="col-span-3 space-y-4">
          {queryInfo && (
            <div className="glass-panel p-4 border-l-4 border-l-saffron flex flex-col space-y-2">
              <span className="text-white font-sora text-sm">Targeting: <span className="text-saffron">{queryInfo.interp}</span></span>
              <span className="text-steel-light font-mono text-xs">Returned {queryInfo.total} matching golden records.</span>
              <details className="mt-2 text-xs">
                <summary className="text-steel-light cursor-pointer hover:text-white font-mono">View Raw SQL</summary>
                <pre className="mt-2 p-2 bg-navy rounded border border-steel-dark text-steel-light overflow-x-auto">
                  {queryInfo.sql}
                </pre>
              </details>
            </div>
          )}

          {!results ? (
            <EmptyState 
              icon={Database} 
              title="Query Builder" 
              description="Configure your filters on the left to discover specific cohorts of businesses across department silos." 
            />
          ) : results.length === 0 ? (
            <EmptyState 
              icon={Search} 
              title="No matches found" 
              description="Try adjusting your query parameters." 
            />
          ) : (
            <div className="glass-panel overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-navy border-b border-steel-dark text-steel-light text-xs uppercase tracking-wider font-sora">
                    <th className="p-4">Business</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Location</th>
                    <th className="p-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-steel-dark">
                  {results.map((row) => (
                    <tr key={row.ubid} className="hover:bg-navy-light/50 transition-colors">
                      <td className="p-4">
                        <div className="font-sora text-sm font-semibold text-white mb-1">{row.business_name}</div>
                        <div className="font-mono text-xs text-saffron">{row.ubid}</div>
                      </td>
                      <td className="p-4">
                        <StatusBadge status={row.status} />
                      </td>
                      <td className="p-4 font-mono text-xs text-steel-light">
                        {row.pincode} • {row.district}
                      </td>
                      <td className="p-4 text-right">
                        <button 
                          onClick={() => navigate(`/ubid/${row.ubid}`)}
                          className="inline-flex items-center space-x-1 text-saffron hover:text-white transition-colors text-sm font-sora font-semibold"
                        >
                          <span>Inspect</span>
                          <ChevronRight size={16} />
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
    </div>
  );
}
