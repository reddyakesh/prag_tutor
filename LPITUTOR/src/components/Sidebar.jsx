import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  MessageSquareText, 
  BookOpen, 
  FileText, 
  Users, 
  Settings, 
  Activity, 
  Database,
  GraduationCap,
  Sparkles
} from 'lucide-react';

export const Sidebar = () => {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) return null;

  const getNavItems = () => {
    switch (user.role) {
      case 'admin':
        return [
          { label: 'Admin Dashboard', path: '/admin', icon: LayoutDashboard },
          { label: 'Teacher Management', path: '/admin/teachers', icon: Users },
          { label: 'Knowledge Base Monitor', path: '/admin/kb', icon: Database },
          { label: 'Activity Logs', path: '/admin/activity', icon: Activity },
        ];
      case 'teacher':
        return [
          { label: 'Subject Workspaces', path: '/teacher', icon: BookOpen },
          { label: 'Upload Course Materials', path: '/teacher/upload', icon: FileText },
          { label: 'KB Build Pipeline', path: '/teacher/pipeline', icon: Database },
        ];
      default:
        return [
          { label: 'Engineering Hub', path: '/student', icon: GraduationCap },
          { label: 'PragTutor AI Chat', path: '/student/chat', icon: MessageSquareText },
        ];
    }
  };

  const navItems = getNavItems();

  return (
    <aside className="w-64 glass-panel border-r border-slate-800/80 p-4 flex flex-col justify-between shrink-0 hidden md:flex min-h-[calc(100vh-65px)]">
      <div className="space-y-6">
        <div>
          <div className="px-3 text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            {user.role} Navigation
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all ${
                    isActive
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* AI Backend Status Card */}
        <div className="glass-card rounded-2xl p-4 border border-slate-800/80 bg-gradient-to-b from-slate-900/90 to-slate-950">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              AI RAG Engine
            </span>
            <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.5 rounded">
              ONLINE
            </span>
          </div>
          <div className="space-y-1.5 text-[11px] text-slate-400">
            <div className="flex justify-between">
              <span>Retrieval:</span>
              <span className="text-slate-200 font-mono">ChromaDB Vector</span>
            </div>
            <div className="flex justify-between">
              <span>Embeddings:</span>
              <span className="text-slate-200 font-mono">all-MiniLM-L6-v2</span>
            </div>
            <div className="flex justify-between">
              <span>LLM Engine:</span>
              <span className="text-slate-200 font-mono">Gemini 2.5 Tutor</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-4 border-t border-slate-800/80 text-xs text-slate-500 flex items-center justify-between">
        <span>PragTutor v2.0</span>
        <span className="flex items-center gap-1 text-slate-400">
          <Sparkles className="w-3 h-3 text-amber-400" /> EdTech RAG
        </span>
      </div>
    </aside>
  );
};
