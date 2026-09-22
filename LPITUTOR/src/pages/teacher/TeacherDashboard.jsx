import React, { useState, useEffect } from 'react';
import { teacherService } from '../../services/api';
import { UploadPDFModal } from './UploadPDF';
import { 
  BookOpen, 
  FileText, 
  Database, 
  CheckCircle2, 
  Plus, 
  ArrowRight,
  Layers,
  Sparkles,
  RefreshCw
} from 'lucide-react';

const FALLBACK_TEACHER_SUBJECTS = [
  { id: "operating_systems", name: "Operating Systems", doc_count: 0, total_chunks: 0, status: "not_created" },
  { id: "computer_networks", name: "Computer Networks", doc_count: 0, total_chunks: 0, status: "not_created" },
  { id: "data_structures", name: "Data Structures", doc_count: 0, total_chunks: 0, status: "not_created" },
  { id: "dbms", name: "Database Management Systems", doc_count: 0, total_chunks: 0, status: "not_created" },
  { id: "software_engineering", name: "Software Engineering", doc_count: 0, total_chunks: 0, status: "not_created" }
];

export const TeacherDashboard = () => {
  const [subjects, setSubjects] = useState(FALLBACK_TEACHER_SUBJECTS);
  const [loading, setLoading] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState(null);

  const fetchSubjects = async () => {
    setLoading(true);
    try {
      const res = await teacherService.getSubjects();
      if (res && res.subjects) {
        const loaded = Array.isArray(res.subjects) ? res.subjects : (res.subjects.subjects || []);
        if (loaded.length > 0) setSubjects(loaded);
      }
    } catch (e) {
      console.warn('Teacher dashboard fallback used:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubjects();
  }, []);

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-amber-400">Faculty Management</span>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2 mt-0.5">
            <BookOpen className="w-7 h-7 text-amber-400" />
            Teacher Subject Workspaces
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage course materials, upload unit PDFs, and build RAG knowledge bases for student AI tutoring.
          </p>
        </div>

        <button
          onClick={fetchSubjects}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors text-sm font-medium"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Workspaces
        </button>
      </div>

      {/* 5 Subject Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {subjects.map((sub) => (
          <div key={sub.id} className="glass-card rounded-3xl p-6 border border-slate-800 space-y-5 flex flex-col justify-between hover:border-amber-500/40 transition-all">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="p-2.5 bg-amber-500/10 text-amber-400 rounded-2xl border border-amber-500/20">
                  <BookOpen className="w-6 h-6" />
                </span>
                {sub.status === 'ready' ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <CheckCircle2 className="w-3.5 h-3.5" /> KB Ready
                  </span>
                ) : sub.status === 'building' ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/20 animate-pulse">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Building...
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-900 text-slate-400 border border-slate-800">
                    No KB Created
                  </span>
                )}
              </div>

              <div>
                <h3 className="text-lg font-bold text-white group-hover:text-amber-300 transition-colors">
                  {sub.name}
                </h3>
                <p className="text-xs font-mono text-slate-400 mt-0.5">Collection: {sub.id}_knowledge_base</p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2">
                <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800/80">
                  <div className="text-slate-400 text-[11px]">PDF Documents</div>
                  <div className="text-base font-bold text-slate-200 mt-0.5 flex items-center gap-1.5">
                    <FileText className="w-4 h-4 text-blue-400" />
                    {sub.doc_count || 0} Files
                  </div>
                </div>

                <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800/80">
                  <div className="text-slate-400 text-[11px]">Indexed Chunks</div>
                  <div className="text-base font-bold text-slate-200 mt-0.5 flex items-center gap-1.5">
                    <Layers className="w-4 h-4 text-purple-400" />
                    {sub.total_chunks || 0} Chunks
                  </div>
                </div>
              </div>
            </div>

            <button
              onClick={() => setSelectedSubject(sub)}
              className="w-full py-3 px-4 rounded-xl bg-slate-900 hover:bg-amber-600 text-slate-200 hover:text-white font-semibold text-xs border border-slate-800 hover:border-amber-500 shadow-md flex items-center justify-center gap-2 group transition-all"
            >
              <Plus className="w-4 h-4" /> Manage PDF & Build KB
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        ))}
      </div>

      {/* Modal for PDF upload & KB build */}
      {selectedSubject && (
        <UploadPDFModal
          subject={selectedSubject}
          onClose={() => setSelectedSubject(null)}
          onRefresh={fetchSubjects}
        />
      )}
    </div>
  );
};
