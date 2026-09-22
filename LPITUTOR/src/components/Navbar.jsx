import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Bot, Shield, GraduationCap, BookOpen, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const getRoleBadge = (role) => {
    switch (role) {
      case 'admin':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
            <Shield className="w-3.5 h-3.5 text-purple-400" /> Admin Console
          </span>
        );
      case 'teacher':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
            <BookOpen className="w-3.5 h-3.5 text-amber-400" /> Teacher Portal
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30">
            <GraduationCap className="w-3.5 h-3.5 text-blue-400" /> Student Workspace
          </span>
        );
    }
  };

  const handleBrandClick = () => {
    if (!user) navigate('/login');
    else if (user.role === 'admin') navigate('/admin');
    else if (user.role === 'teacher') navigate('/teacher');
    else navigate('/student');
  };

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-6 py-3.5 flex items-center justify-between">
      {/* Brand & Identity */}
      <div className="flex items-center gap-4">
        <div 
          onClick={handleBrandClick} 
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 p-0.5 shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Bot className="w-6 h-6 text-blue-400 group-hover:text-blue-300 transition-colors" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
                PragTutor
              </span>
              <span className="text-[10px] font-semibold tracking-widest uppercase bg-blue-900/60 text-blue-300 border border-blue-700/50 px-1.5 py-0.5 rounded">
                AI Tutor v2
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Personalized AI Tutoring for Engineering</p>
          </div>
        </div>
      </div>

      {/* User Info & Logout (No Role Switching in Navbar) */}
      <div className="flex items-center gap-3">
        {user && (
          <div className="flex items-center gap-3 pl-3">
            {getRoleBadge(user.role)}
            <div className="hidden md:block text-right">
              <div className="text-sm font-semibold text-slate-200">{user.name}</div>
              <div className="text-[11px] text-slate-400">{user.email}</div>
            </div>
            <button
              onClick={() => { logout(); navigate('/login'); }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/20 hover:bg-rose-500/20 transition-all"
              title="Sign Out"
            >
              <LogOut className="w-3.5 h-3.5 text-rose-400" />
              <span>Logout</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
