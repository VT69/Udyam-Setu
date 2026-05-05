import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-navy flex font-sans">
      <Sidebar collapsed={collapsed} />
      
      <div className="flex-1 flex flex-col relative min-h-screen">
        <TopBar collapsed={collapsed} setCollapsed={setCollapsed} />
        
        {/* Main Content Area */}
        <main 
          className={`flex-1 overflow-x-hidden overflow-y-auto bg-navy bg-pattern transition-all duration-300 mt-16 ${
            collapsed ? 'ml-16' : 'ml-64'
          }`}
        >
          <div className="container mx-auto p-6 min-h-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
