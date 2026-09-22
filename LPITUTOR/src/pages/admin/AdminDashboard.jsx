import React, { useState, useEffect } from 'react';
import { adminService } from '../../services/api';
import { 
  Users, 
  GraduationCap, 
  BookOpen, 
  Database, 
  Activity, 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  RefreshCw,
  Search,
  Check,
  X,
  FileText,
  Layers,
  Sparkles,
  AlertCircle,
  Trash2,
  Plus
} from 'lucide-react';

export const AdminDashboard = () => {
  const [data, setData] = useState({
    metrics: {
      registered_students: 0,
      registered_teachers: 0,
      active_teachers: 0,
      inactive_teachers: 0,
      access_granted_teachers: 0,
      total_uploaded_pdfs: 0,
      active_knowledge_bases: 0,
      system_health: "100% Operational"
    },
    teachers: [],
    uploaded_pdfs: [],
    knowledge_bases: [],
    recent_activity: []
  });

  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchAdminData = async () => {
    setLoading(true);
    try {
      const res = await adminService.getDashboard();
      if (res) {
        setData({
          metrics: res.metrics || {
            registered_students: 0,
            registered_teachers: 0,
            active_teachers: 0,
            inactive_teachers: 0,
            access_granted_teachers: 0,
            total_uploaded_pdfs: 0,
            active_knowledge_bases: 0,
            system_health: "100% Operational"
          },
          teachers: res.teachers || [],
          uploaded_pdfs: res.uploaded_pdfs || [],
          knowledge_bases: res.knowledge_bases || [],
          recent_activity: res.recent_activity || []
        });
      }
    } catch (e) {
      console.warn('Error loading real admin dashboard data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleToggleAccess = async (teacherId, currentAccess) => {
    try {
      const res = await adminService.updateTeacherAccess(teacherId, !currentAccess);
      if (res && res.teacher) {
        fetchAdminData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleStatus = async (teacherId, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    try {
      const res = await adminService.updateTeacherStatus(teacherId, newStatus);
      if (res && res.teacher) {
        fetchAdminData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const ALL_SUBJECTS = [
    { id: 'operating_systems', name: 'Operating Systems', short: 'OS' },
    { id: 'computer_networks', name: 'Computer Networks', short: 'CN' },
    { id: 'data_structures', name: 'Data Structures', short: 'DS' },
    { id: 'dbms', name: 'DBMS', short: 'DBMS' },
    { id: 'software_engineering', name: 'Software Engineering', short: 'SE' }
  ];

  const handleToggleSubjectPermission = async (teacher, subId) => {
    const currentSubs = teacher.subjects || teacher.assigned_subjects || ['operating_systems'];
    let newSubs;
    if (currentSubs.includes(subId)) {
      if (currentSubs.length === 1) {
        alert("Teacher must remain assigned to at least 1 subject.");
        return;
      }
      newSubs = currentSubs.filter(s => s !== subId);
    } else {
      newSubs = [...currentSubs, subId];
    }

    try {
      await adminService.updateTeacherSubjects(teacher.id, newSubs);
      fetchAdminData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleClearSubjectKB = async (subjectId, subjectName) => {
    if (window.confirm(`Are you sure you want to delete all uploaded PDFs and clear the ChromaDB Knowledge Base for ${subjectName}? This action cannot be undone.`)) {
      try {
        await adminService.clearKnowledgeBase(subjectId);
        fetchAdminData();
      } catch (e) {
        console.error(e);
        alert(e.response?.data?.detail || "Failed to clear knowledge base.");
      }
    }
  };

  const teachersList = data.teachers || [];
  const filteredTeachers = teachersList.filter(t => 
    (t.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (t.email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (t.department || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const metrics = data.metrics || {};
  const pdfsList = data.uploaded_pdfs || [];
  const kbList = data.knowledge_bases || [];
  const activityList = data.recent_activity || [];

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-purple-400">Platform Control Center</span>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2 mt-0.5">
            <ShieldCheck className="w-7 h-7 text-purple-400" />
            Admin Dashboard & Monitoring Console
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time backend database metrics, teacher authorization, course PDF monitoring, and ChromaDB readiness.
          </p>
        </div>
        <button
          onClick={fetchAdminData}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-all text-xs font-semibold shadow-sm"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Live Metrics
        </button>
      </div>

      {/* 1. REAL METRICS ROW */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        
        {/* Total Registered Students */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Registered Students</span>
            <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-xl border border-blue-500/20">
              <GraduationCap className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white">{metrics.registered_students || 0}</div>
          <div className="text-xs text-slate-400">Total registered student accounts</div>
        </div>

        {/* Total Registered Teachers */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Registered Teachers</span>
            <div className="p-2.5 bg-amber-500/10 text-amber-400 rounded-xl border border-amber-500/20">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white">{metrics.registered_teachers || 0}</div>
          <div className="text-xs text-amber-400 font-medium">
            {metrics.active_teachers || 0} Active • {metrics.inactive_teachers || 0} Inactive
          </div>
        </div>

        {/* Uploaded PDF Course Documents */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Uploaded PDFs</span>
            <div className="p-2.5 bg-purple-500/10 text-purple-400 rounded-xl border border-purple-500/20">
              <FileText className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white">{metrics.total_uploaded_pdfs || 0}</div>
          <div className="text-xs text-slate-400">Course PDF syllabus files in <code className="bg-slate-900 px-1 py-0.5 rounded text-purple-300 font-mono">data/</code></div>
        </div>

        {/* Active Knowledge Bases */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Knowledge Bases</span>
            <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
              <Database className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white">{metrics.active_knowledge_bases || 0}</div>
          <div className="text-xs text-emerald-400 font-medium flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> ChromaDB Vector Collections
          </div>
        </div>

      </div>

      {/* 2. TEACHER ACCESS & AUTHORIZATION TABLE */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden space-y-0">
        <div className="p-6 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-amber-400" />
              Registered Teachers Authorization & Access Control
            </h2>
            <p className="text-xs text-slate-400">Grant or revoke teacher access permissions and enable or disable teacher accounts in real-time.</p>
          </div>
          
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search teachers by name, email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-purple-500 w-64"
            />
          </div>
        </div>

        {filteredTeachers.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <Users className="w-10 h-10 text-slate-600 mx-auto" />
            <div className="text-sm font-semibold text-slate-300">No Registered Teachers Found</div>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Initially there are 0 teachers in the system. Teachers can sign up with their email address via the Teacher Sign Up portal.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/90 text-xs font-semibold uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-6">Teacher Profile</th>
                  <th className="py-3.5 px-6">Department</th>
                  <th className="py-3.5 px-6">Assigned Course Subjects</th>
                  <th className="py-3.5 px-6">Account Status</th>
                  <th className="py-3.5 px-6">KB Access Status</th>
                  <th className="py-3.5 px-6 text-right">Admin Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredTeachers.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-4 px-6">
                      <div className="font-semibold text-slate-100">{t.name}</div>
                      <div className="text-xs text-slate-400 font-mono">{t.email}</div>
                    </td>
                    <td className="py-4 px-6 text-xs text-slate-300">{t.department || "Computer Science"}</td>
                    <td className="py-4 px-6">
                      <div className="flex flex-wrap gap-1.5 max-w-xs">
                        {ALL_SUBJECTS.map((sub) => {
                          const teacherSubs = t.subjects || t.assigned_subjects || [];
                          const hasSubject = teacherSubs.includes(sub.id);
                          return (
                            <button
                              key={sub.id}
                              onClick={() => handleToggleSubjectPermission(t, sub.id)}
                              title={hasSubject ? `Click to revoke ${sub.name}` : `Click to grant ${sub.name}`}
                              className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold border transition-all flex items-center gap-1 ${
                                hasSubject
                                  ? 'bg-amber-500/10 border-amber-500/40 text-amber-300 hover:bg-rose-500/20 hover:border-rose-500/40 hover:text-rose-300'
                                  : 'bg-slate-950/60 border-slate-800 text-slate-500 hover:text-slate-200 hover:border-slate-700'
                              }`}
                            >
                              {hasSubject ? <Check className="w-2.5 h-2.5" /> : '+'}
                              {sub.short}
                            </button>
                          );
                        })}
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                        t.status === 'active'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${t.status === 'active' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`}></span>
                        {(t.status || 'active').toUpperCase()}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border ${
                        t.access_granted
                          ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                          : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                      }`}>
                        {t.access_granted ? <Check className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
                        {t.access_granted ? 'GRANTED' : 'RESTRICTED'}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right space-x-2">
                      <button
                        onClick={() => handleToggleAccess(t.id, t.access_granted)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                          t.access_granted
                            ? 'bg-rose-500/10 border-rose-500/30 text-rose-300 hover:bg-rose-500/20'
                            : 'bg-blue-600 border-blue-500 text-white hover:bg-blue-500'
                        }`}
                      >
                        {t.access_granted ? 'Revoke Access' : 'Grant Access'}
                      </button>
                      <button
                        onClick={() => handleToggleStatus(t.id, t.status)}
                        className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-900 border border-slate-700 text-slate-300 hover:bg-slate-800 transition-all"
                      >
                        {t.status === 'active' ? 'Disable Account' : 'Enable Account'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 3. KNOWLEDGE-BASE PREPARATION & CHROMADB MONITOR */}
      <div className="glass-card rounded-2xl border border-slate-800 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-emerald-400" />
            Knowledge-Base Preparation & Build Status Monitor
          </h2>
          <span className="text-xs text-slate-400">ChromaDB Vector Collections</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {kbList.map((kb) => (
            <div key={kb.subject_id} className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-white">{kb.subject_name}</span>
                  <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                    kb.status === 'ready' 
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                      : 'bg-slate-950 text-slate-400 border-slate-800'
                  }`}>
                    {kb.status === 'ready' && <CheckCircle2 className="w-3 h-3" />}
                    {(kb.status || 'not_created').toUpperCase()}
                  </span>
                </div>
                <div className="text-[11px] font-mono text-purple-300 bg-slate-950 p-2 rounded border border-slate-900 truncate">
                  {kb.collection_name}
                </div>
                <div className="flex justify-between text-xs text-slate-300">
                  <span>Course PDFs: <strong className="text-white">{kb.pdf_count} files</strong></span>
                  <span>Vector Chunks: <strong className="text-emerald-400 font-mono">{kb.vector_chunks}</strong></span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex justify-end">
                <button
                  onClick={() => handleClearSubjectKB(kb.subject_id, kb.subject_name)}
                  className="px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all"
                >
                  <Trash2 className="w-3.5 h-3.5 text-rose-400" /> Clear KB & PDFs
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. PDF UPLOADS MONITOR */}
      <div className="glass-card rounded-2xl border border-slate-800 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-purple-400" />
            Course PDF Document Upload Monitor
          </h2>
          <span className="text-xs font-mono text-purple-300">{pdfsList.length} PDF Files Tracked</span>
        </div>

        {pdfsList.length === 0 ? (
          <div className="text-xs text-slate-400 italic p-4 text-center">No PDF files uploaded yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/90 font-semibold uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-4">PDF Filename</th>
                  <th className="py-2.5 px-4">Subject</th>
                  <th className="py-2.5 px-4">File Size</th>
                  <th className="py-2.5 px-4 text-right">Modified Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {pdfsList.map((pdf, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="py-2.5 px-4 font-bold text-slate-200">{pdf.filename}</td>
                    <td className="py-2.5 px-4 text-amber-300 uppercase">{pdf.subject_id.replace('_', ' ')}</td>
                    <td className="py-2.5 px-4 text-slate-400">{pdf.size_mb} MB</td>
                    <td className="py-2.5 px-4 text-right text-slate-400">{pdf.mtime}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 5. SYSTEM ACTIVITY LOG STREAM */}
      <div className="glass-card rounded-2xl border border-slate-800 p-6 space-y-3">
        <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-3">
          <Activity className="w-5 h-5 text-purple-400" />
          Real-Time Activity Stream
        </h2>
        <div className="space-y-2">
          {activityList.map((act) => (
            <div key={act.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] ${
                  act.role === 'ADMIN' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
                  act.role === 'TEACHER' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                  'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                }`}>
                  {act.role}
                </span>
                <span className="text-slate-200 font-medium">{act.user}</span>
                <span className="text-slate-400">— {act.action}</span>
              </div>
              <span className="text-slate-400 font-mono">{act.timestamp}</span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
