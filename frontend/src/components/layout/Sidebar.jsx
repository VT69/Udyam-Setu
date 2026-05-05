import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, Activity, Search, Filter, ClipboardList, ActivitySquare } from 'lucide-react';

export default function Sidebar({ collapsed }) {
  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/entity-resolution', label: 'Entity Resolution', icon: Users },
    { path: '/activity-intelligence', label: 'Activity Intelligence', icon: Activity },
    { path: '/ubid-lookup', label: 'UBID Lookup', icon: Search },
    { path: '/query-builder', label: 'Query Builder', icon: Filter },
    { path: '/event-attribution', label: 'Event Attribution', icon: ClipboardList },
    { path: '/system-health', label: 'System Health', icon: ActivitySquare },
  ];

  return (
    <div className={`fixed left-0 top-0 h-screen bg-navy border-r border-steel-dark flex flex-col transition-all duration-300 z-20 ${collapsed ? 'w-16' : 'w-64'}`}>
      
      {/* Logo Area */}
      <div className="h-16 flex items-center justify-center border-b border-steel-dark shrink-0">
        <div className="w-8 h-8 rounded bg-saffron flex items-center justify-center">
          <span className="font-sora font-bold text-navy">US</span>
        </div>
        {!collapsed && (
          <div className="ml-3 flex flex-col">
            <span className="font-sora font-bold text-white text-lg leading-tight">Udyam Setu</span>
            <span className="font-mono text-[10px] text-steel-light tracking-widest uppercase">AI for Bharat</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto py-4 space-y-1 px-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => 
              `flex items-center px-3 py-2.5 rounded-lg transition-colors group ${
                isActive 
                  ? 'bg-navy-light text-saffron' 
                  : 'text-steel-light hover:bg-navy-light/50 hover:text-white'
              }`
            }
          >
            <item.icon size={20} className="shrink-0" />
            {!collapsed && (
              <span className="ml-3 font-sora text-sm font-medium whitespace-nowrap">
                {item.label}
              </span>
            )}
            
            {/* Tooltip for collapsed state */}
            {collapsed && (
              <div className="absolute left-14 bg-navy-light text-white text-xs px-2 py-1 rounded opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all whitespace-nowrap border border-steel-dark z-50">
                {item.label}
              </div>
            )}
          </NavLink>
        ))}
      </div>
    </div>
  );
}
