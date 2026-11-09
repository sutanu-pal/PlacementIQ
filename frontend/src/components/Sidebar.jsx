import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  FileText,
  Briefcase,
  Code2,
  Mic,
  Compass,
  ShieldCheck,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

export const Sidebar = ({ isOpen, onClose }) => {
  const { user } = useAuth();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, active: true },
    { name: 'Resume Analyzer', href: '/resume', icon: FileText, badge: 'Active', isLive: true },
    { name: 'Job Matching', href: '/jobs', icon: Briefcase, badge: 'Phase 2' },
    { name: 'DSA Engine', href: '/dsa', icon: Code2, badge: 'Phase 2' },
    { name: 'Mock Interview', href: '/interview', icon: Mic, badge: 'Phase 2' },
    { name: 'Learning Roadmap', href: '/roadmap', icon: Compass, badge: 'Phase 2' },
  ];

  if (user?.is_admin) {
    navigation.push({
      name: 'Admin Dashboard',
      href: '/admin',
      icon: ShieldCheck,
      badge: 'Admin Scope',
    });
  }

  const sidebarContent = (
    <div className="flex flex-col h-full bg-slate-950 border-r border-slate-800/80 w-64 p-4">
      {/* Platform Meta Info */}
      <div className="mb-6 px-3 py-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 mb-1">
          <Sparkles className="w-3.5 h-3.5" />
          <span>7th Sem Major Project</span>
        </div>
        <p className="text-[11px] text-slate-400">
          CSE (AI & ML) Platform · Foundation Active
        </p>
      </div>

      {/* Nav List */}
      <div className="space-y-1 flex-1">
        <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
          Intelligence Modules
        </p>
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            onClick={onClose}
            className={({ isActive }) =>
              `group flex items-center justify-between px-3 py-2.5 text-xs font-medium rounded-xl transition-all ${
                isActive
                  ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`
            }
          >
            <div className="flex items-center gap-3">
              <item.icon className="w-4 h-4 text-slate-400 group-hover:text-indigo-400 transition-colors" />
              <span>{item.name}</span>
            </div>
            {item.badge && (
              <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-md border ${
                item.isLive
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-slate-800 text-slate-400 border-slate-700/60'
              }`}>
                {item.badge}
              </span>
            )}
          </NavLink>
        ))}
      </div>

      {/* Footer / Placement Readiness Pill */}
      <div className="pt-4 border-t border-slate-800/80 px-2">
        <div className="text-[11px] text-slate-500 flex items-center justify-between">
          <span>Target Batch</span>
          <span className="text-slate-300 font-mono font-medium">2026 Grad</span>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Fixed Sidebar */}
      <aside className="hidden lg:block shrink-0 sticky top-16 h-[calc(100vh-4rem)]">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer */}
      {isOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
            onClick={onClose}
          />
          <div className="relative flex-1 flex flex-col max-w-xs w-full">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
