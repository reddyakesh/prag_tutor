import React, { useState, useEffect } from 'react';
import { studentService } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { 
  GraduationCap, 
  BookOpen, 
  Bot, 
  ArrowRight, 
  Sparkles, 
  CheckCircle2, 
  History,
  BrainCircuit,
  Compass
} from 'lucide-react';

const FALLBACK_SUBJECTS = [
  { id: "operating_systems", name: "Operating Systems", description: "Processes, CPU Scheduling, Synchronization, Deadlocks, Memory Management, File Systems." },
  { id: "computer_networks", name: "Computer Networks", description: "OSI Reference Model, TCP/IP Suite, Routing Algorithms, IP Addressing, Security." },
  { id: "data_structures", name: "Data Structures", description: "Arrays, Linked Lists, Stacks, Queues, Binary Trees, Graphs, Sorting & Searching." },
  { id: "dbms", name: "DBMS", description: "Relational Database Management Systems, ER Diagrams, SQL Queries, Normalization, ACID Properties." },
  { id: "software_engineering", name: "Software Engineering", description: "SDLC Models, Agile Methodologies, System Design, Testing & Quality Assurance." }
];

export const StudentDashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [subjects, setSubjects] = useState(FALLBACK_SUBJECTS);
  const [completedTopics, setCompletedTopics] = useState([]);
  const [history, setHistory] = useState([
    { query: "What is process synchronization?", topic: "process_synchronization", timestamp: "Today" },
    { query: "Explain CPU scheduling algorithms", topic: "cpu_scheduling", timestamp: "Yesterday" }
  ]);

  useEffect(() => {
    studentService.getSubjects()
      .then(res => {
        if (res && res.subjects) {
          const loaded = Array.isArray(res.subjects) ? res.subjects : (res.subjects.subjects || []);
          if (loaded.length > 0) setSubjects(loaded);
        }
      })
      .catch(err => console.warn('Using fallback subjects', err));

    studentService.getHistory(user?.id || 'STU001')
      .then(res => {
        if (res) {
          if (res.recent_queries && res.recent_queries.length > 0) setHistory(res.recent_queries);
          if (res.completed_topics) setCompletedTopics(res.completed_topics);
        }
      })
      .catch(err => console.warn('Using fallback history', err));
  }, [user]);

  const openTutorForSubject = (subjectId) => {
    navigate(`/student/chat?subject=${subjectId}`);
  };

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto">
      {/* Hero Welcome Banner */}
      <div className="glass-panel p-8 rounded-3xl border border-slate-800 bg-gradient-to-r from-slate-900 via-blue-950/40 to-slate-900 relative overflow-hidden">
        <div className="absolute -right-10 -bottom-10 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="max-w-2xl space-y-3 relative z-10">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/20">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" /> PragTutor AI Engineering Platform
          </span>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            Hi, {user?.name || "Student"}! Ready to master your engineering topics?
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Your personalized AI tutor adapts explanations based on your current knowledge state, checks prerequisites automatically, and constructs personalized learning paths.
          </p>
          
          <div className="pt-2 flex flex-wrap gap-3">
            <button
              onClick={() => openTutorForSubject('operating_systems')}
              className="px-5 py-3 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs shadow-lg shadow-blue-500/25 flex items-center gap-2 group transition-all"
            >
              <Bot className="w-4 h-4" /> Launch PragTutor AI Chat
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </div>

      {/* Student Known Topics Badge / Section */}
      <div className="glass-card rounded-2xl border border-slate-800 p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Student Known Topics</h3>
            <p className="text-xs text-slate-400">Mastered prerequisites & confirmed learned concepts</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {completedTopics.length > 0 ? (
            completedTopics.map((topic, idx) => (
              <span key={idx} className="px-3 py-1 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
                ✓ {topic.replace('_', ' ').toUpperCase()}
              </span>
            ))
          ) : (
            <span className="px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-amber-300/80 text-xs font-mono font-medium">
              Student Known Topics: None
            </span>
          )}
        </div>
      </div>

      {/* 5 Subject Hub Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Compass className="w-6 h-6 text-blue-400" />
            Select Core Engineering Course
          </h2>
          <span className="text-xs text-slate-400">5 Courses Active</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {subjects.map((sub) => (
            <div 
              key={sub.id} 
              className="glass-card rounded-3xl p-6 border border-slate-800 space-y-4 flex flex-col justify-between hover:border-blue-500/40 transition-all group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="p-3 bg-blue-500/10 text-blue-400 rounded-2xl border border-blue-500/20 group-hover:scale-110 transition-transform">
                    <BookOpen className="w-6 h-6" />
                  </span>
                  <span className="text-[10px] font-mono bg-slate-900 text-blue-300 border border-blue-900 px-2 py-1 rounded-full">
                    {sub.topics ? sub.topics.length : 12} Topics
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-white group-hover:text-blue-300 transition-colors">
                    {sub.name}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                    {sub.description || "Core engineering principles, RAG knowledge retrieval, and interactive AI tutoring."}
                  </p>
                </div>
              </div>

              <button
                onClick={() => openTutorForSubject(sub.id)}
                className="w-full py-3 px-4 rounded-xl bg-blue-600/10 hover:bg-blue-600 text-blue-300 hover:text-white font-semibold text-xs border border-blue-500/30 hover:border-blue-500 flex items-center justify-center gap-2 group/btn transition-all"
              >
                <Bot className="w-4 h-4" /> Start AI Tutor Session
                <ArrowRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Query History */}
      <div className="glass-card rounded-2xl border border-slate-800 p-6 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-400" />
          Recent Learning Sessions
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {history.map((item, idx) => (
            <div 
              key={idx} 
              onClick={() => navigate(`/student/chat?query=${encodeURIComponent(item.query)}`)}
              className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-blue-500/30 cursor-pointer transition-all space-y-2"
            >
              <div className="text-xs text-slate-400 font-mono flex items-center justify-between">
                <span>{item.timestamp}</span>
                <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 text-[10px] uppercase font-bold">
                  {item.topic}
                </span>
              </div>
              <div className="text-sm font-semibold text-slate-200">
                "{item.query}"
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
