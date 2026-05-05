import React, { useState, useEffect } from 'react';
import { Menu, Bell } from 'lucide-react';
import { api } from '../../api/endpoints';

export default function TopBar({ collapsed, setCollapsed }) {
  const [isHealthy, setIsHealthy] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await api.getHealth();
        setIsHealthy(true);
      } catch (err) {
        setIsHealthy(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className={`fixed top-0 right-0 h-16 bg-navy/90 backdrop-blur-md border-b border-steel-dark flex items-center justify-between px-4 z-10 transition-all duration-300 ${collapsed ? 'left-16' : 'left-64'}`}>
      
      <div className="flex items-center">
        <button 
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 mr-4 text-steel-light hover:text-white rounded-lg hover:bg-navy-light focus:outline-none"
        >
          <Menu size={20} />
        </button>
        <div className="hidden md:flex flex-col">
          <span className="font-sora text-sm font-semibold text-white tracking-wide">Karnataka Commerce & Industry</span>
          <span className="font-mono text-xs text-steel-light">AI Business Intelligence Platform</span>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* System Status */}
        <div className="flex items-center space-x-2 bg-navy-light px-3 py-1.5 rounded-full border border-steel-dark">
          <div className="relative flex h-3 w-3">
            {isHealthy && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>}
            <span className={`relative inline-flex rounded-full h-3 w-3 ${isHealthy ? 'bg-green-500' : 'bg-red-500'}`}></span>
          </div>
          <span className="font-mono text-xs text-steel-light">API {isHealthy ? 'ONLINE' : 'OFFLINE'}</span>
        </div>
        
        {/* Notifications */}
        <button className="relative p-2 text-steel-light hover:text-white rounded-full hover:bg-navy-light">
          <Bell size={20} />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-saffron border border-navy"></span>
        </button>
        
        {/* User Profile */}
        <div className="h-8 w-8 rounded-full bg-steel flex items-center justify-center border border-steel-light cursor-pointer">
          <span className="font-sora text-xs font-bold text-white">AD</span>
        </div>
      </div>
    </div>
  );
}
