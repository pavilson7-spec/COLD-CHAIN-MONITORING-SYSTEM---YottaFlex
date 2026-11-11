import React, { useState } from 'react';
import { 
  Truck, Package, Box, Cpu, Activity, Navigation, 
  Sliders, AlertOctagon, Bell, History, CheckSquare, 
  FileText, ShieldAlert, Settings, LogOut, User as UserIcon, Menu, X
} from 'lucide-react';

export default function Layout({ user, onLogout, activePage, onNavigate, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigationItems = [
    { name: 'Dashboard', icon: Activity },
    { name: 'Products', icon: Package },
    { name: 'Shipments', icon: Truck },
    { name: 'Containers', icon: Box },
    { name: 'Sensors', icon: Cpu },
    { name: 'Readings', icon: Activity },
    { name: 'Route Tracking', icon: Navigation },
    { name: 'Threshold Policies', icon: Sliders },
    { name: 'Excursions', icon: AlertOctagon },
    { name: 'Alerts', icon: Bell },
    { name: 'Custody History', icon: History },
    { name: 'Corrective Actions', icon: CheckSquare },
    { name: 'Reports', icon: FileText },
    { name: 'Data Validation', icon: ShieldAlert },
    { name: 'System Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar for Desktop */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-slate-900 text-slate-300 border-r border-slate-800">
        <div className="p-5 flex items-center space-x-3 border-b border-slate-800">
          <div className="p-2 rounded-xl bg-blue-600 text-white">
            <Truck className="w-5 h-5" />
          </div>
          <div>
            <div className="font-bold text-white text-sm tracking-wide">Cold Chain Mon</div>
            <div className="text-[10px] text-blue-400 font-mono">v1.0.0 Production</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.name;
            return (
              <button
                key={item.name}
                onClick={() => onNavigate(item.name)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                  isActive 
                    ? 'bg-blue-600 text-white font-semibold shadow-sm' 
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span className="truncate">{item.name}</span>
              </button>
            );
          })}
        </nav>

        {/* User Role Card */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/50">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-xs">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-white truncate">{user?.full_name || user?.username}</div>
              <div className="text-[10px] text-slate-400 truncate">{user?.role}</div>
            </div>
            <button
              onClick={onLogout}
              title="Sign Out"
              className="text-slate-400 hover:text-rose-400 transition-colors p-1"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="bg-white border-b border-slate-200 h-16 flex items-center justify-between px-6 z-10">
          <div className="flex items-center space-x-3">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 text-slate-500 hover:bg-slate-100 rounded-lg"
            >
              <Menu className="w-5 h-5" />
            </button>
            <span className="text-sm font-semibold text-slate-700">{activePage}</span>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex items-center space-x-2 text-xs text-slate-500 bg-slate-100 px-3 py-1.5 rounded-full">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>PostgreSQL Connected</span>
            </div>
            <span className="text-xs font-medium text-slate-600 bg-blue-50 text-blue-700 px-2.5 py-1 rounded-full border border-blue-200">
              Role: {user?.role}
            </span>
          </div>
        </header>

        {/* Dynamic Page Viewport */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
