import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';

// Pages
import Dashboard from './pages/Dashboard';
import EntityResolution from './pages/EntityResolution';
import ReviewTask from './pages/ReviewTask';
import ActivityIntelligence from './pages/ActivityIntelligence';
import UBIDDetail from './pages/UBIDDetail';
import QueryBuilder from './pages/QueryBuilder';
import EventAttribution from './pages/EventAttribution';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        
        {/* Entity Resolution */}
        <Route path="entity-resolution" element={<EntityResolution />} />
        <Route path="review-task/:pairId" element={<ReviewTask />} />
        
        {/* Activity Intelligence */}
        <Route path="activity-intelligence" element={<ActivityIntelligence />} />
        
        {/* Golden Record View */}
        <Route path="ubid/:ubid" element={<UBIDDetail />} />
        
        {/* Queries */}
        <Route path="query-builder" element={<QueryBuilder />} />
        
        {/* Events */}
        <Route path="event-attribution" element={<EventAttribution />} />
        
        {/* Fallbacks */}
        <Route path="system-health" element={<div className="text-white p-8">System Health Dashboard (Coming Soon)</div>} />
        <Route path="ubid-lookup" element={<Navigate to="/query-builder" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
