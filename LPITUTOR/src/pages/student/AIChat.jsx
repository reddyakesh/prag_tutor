import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { studentService } from '../../services/api';
import { 
  Bot, 
  Send, 
  Sparkles, 
  BookOpen, 
  CheckCircle2, 
  AlertTriangle, 
  FileText, 
  Loader2, 
  Compass, 
  Image as ImageIcon,
  Check,
  ChevronDown,
  ChevronUp,
  Award,
  Layers,
  HelpCircle,
  BrainCircuit
} from 'lucide-react';

export const AIChat = () => {
  const [searchParams] = useSearchParams();
  const initialSubject = searchParams.get('subject') || 'operating_systems';
  const initialQuery = searchParams.get('query') || '';

  const [subject, setSubject] = useState(initialSubject);
  const [query, setQuery] = useState(initialQuery);
  const [level, setLevel] = useState('beginner');
  const [attachedImages, setAttachedImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [showSourcesMap, setShowSourcesMap] = useState({});
  const [learnedTopics, setLearnedTopics] = useState(new Set());
  const [markingTopic, setMarkingTopic] = useState(null);
  const [previewImageModal, setPreviewImageModal] = useState(null);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const samplePrompts = [
    "What is a process?",
    "Show diagram of process states",
    "Explain CPU scheduling algorithms",
    "Show image of PCB structure",
    "What is virtual memory?"
  ];

  const subjectsList = [
    { id: 'operating_systems', name: 'Operating Systems' },
    { id: 'computer_networks', name: 'Computer Networks' },
    { id: 'data_structures', name: 'Data Structures' },
    { id: 'dbms', name: 'DBMS' },
    { id: 'software_engineering', name: 'Software Engineering' }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleImageSelect = (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = (event) => {
        setAttachedImages(prev => [...prev, {
          id: Date.now() + Math.random(),
          name: file.name,
          dataUri: event.target.result
        }]);
      };
      reader.readAsDataURL(file);
    });

    e.target.value = '';
  };

  const removeAttachedImage = (idToRemove) => {
    setAttachedImages(prev => prev.filter(img => img.id !== idToRemove));
  };

  const handleMarkLearned = async (msgId, topicKey, topicName) => {
    try {
      setMarkingTopic(topicKey || topicName);
      const studentUser = JSON.parse(localStorage.getItem('pragtutor_user') || '{}');
      const studentId = studentUser.id || 'STU001';
      const topicToMark = topicKey || topicName;
      await studentService.markLearned(studentId, subject, topicToMark);
      setLearnedTopics(prev => new Set([...prev, topicToMark, topicName, topicToMark.toLowerCase(), topicToMark.replace('_', ' ')]));
    } catch (err) {
      console.error('Failed to mark topic as learned:', err);
    } finally {
      setMarkingTopic(null);
    }
  };

  const handleSend = async (customQuery = null) => {
    const textToSend = customQuery || query;
    if (!textToSend.trim() && attachedImages.length === 0) return;

    const studentUser = JSON.parse(localStorage.getItem('pragtutor_user') || '{}');
    const studentId = studentUser.id || 'STU001';

    const currentImages = [...attachedImages];

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: textToSend || "Analyzing attached image(s)...",
      attachedImages: currentImages.map(img => img.dataUri),
      level,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    if (!customQuery) setQuery('');
    setAttachedImages([]);
    setLoading(true);

    try {
      const imgPayload = currentImages.length > 0 ? currentImages.map(img => img.dataUri) : null;
      const res = await studentService.queryTutor(textToSend || "Explain the attached image", subject, imgPayload, studentId, level);
      const isKbUnavailable = res.status === 'kb_unavailable';
      
      const botMessage = {
        id: Date.now() + 1,
        sender: 'tutor',
        isKbUnavailable,
        rawTopic: res.topic_id || res.topic || "general",
        topic: res.topic_name || res.topic || "General Concept",
        topicConfidence: Math.round((res.topic_confidence || 0.85) * 100),
        level: res.level || level,
        completedPrereqs: res.student_completed || [],
        missingPrereqs: res.missing_prerequisites || [],
        learningPath: res.learning_path || res.prerequisites_used || [],
        sources: res.sources || res.retrieved_content || [],
        images: res.images || res.retrieved_images || [],
        answer: isKbUnavailable 
          ? (res.message || "PDFs have not been uploaded by your teachers for this subject yet.") 
          : (res.answer || res.llm_response || "Explanation generated."),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error(error);
      const errorMsg = {
        id: Date.now() + 1,
        sender: 'tutor',
        isKbUnavailable: false,
        answer: "I apologize, but I encountered an error processing your query. Please check your network or try again.",
        topic: "System Notice",
        topicConfidence: 100,
        level,
        completedPrereqs: [],
        missingPrereqs: [],
        learningPath: [],
        sources: [],
        images: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSources = (msgId) => {
    setShowSourcesMap(prev => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  return (
    <div className="flex flex-col h-[calc(100vh-65px)] max-w-6xl mx-auto p-4 md:p-6 space-y-4">
      {/* Header Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              PragTutor Interactive AI Session
            </h1>
            <p className="text-xs text-slate-400">RAG Knowledge Retrieval & Adaptive Prerequisite Engine</p>
          </div>
        </div>

        {/* Subject Selector */}
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl text-xs">
          <BookOpen className="w-4 h-4 text-amber-400" />
          <span className="text-slate-400 font-medium">Subject:</span>
          <select
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="bg-transparent text-slate-200 font-semibold focus:outline-none cursor-pointer"
          >
            {subjectsList.map(s => (
              <option key={s.id} value={s.id} className="bg-slate-900 text-slate-100">
                {s.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-6 pr-2">
        {messages.length === 0 && (
          <div className="glass-panel p-8 rounded-3xl border border-slate-800/80 text-center space-y-6 my-auto max-w-2xl mx-auto mt-12">
            <div className="w-16 h-16 rounded-2xl bg-blue-600/20 border border-blue-500/30 text-blue-400 mx-auto flex items-center justify-center">
              <Bot className="w-8 h-8" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold text-white">Ask PragTutor Anything</h2>
              <p className="text-xs text-slate-400">
                PragTutor uses RAG to pull context from your course PDFs, analyzes your prerequisite knowledge state, and designs a custom step-by-step explanation.
              </p>
            </div>

            {/* Quick Sample Prompts */}
            <div className="space-y-2 text-left">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                Recommended Questions:
              </span>
              <div className="flex flex-wrap gap-2">
                {samplePrompts.map((promptText, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(promptText)}
                    className="px-3.5 py-2 rounded-xl bg-slate-900/90 hover:bg-blue-600/20 border border-slate-800 hover:border-blue-500/40 text-xs text-slate-300 hover:text-white transition-all text-left flex items-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    {promptText}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} space-y-2`}>
            
            {/* USER BUBBLE */}
            {msg.sender === 'user' && (
              <div className="max-w-2xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl rounded-tr-none px-5 py-3.5 text-sm shadow-lg shadow-blue-600/20 space-y-2">
                <p>{msg.text}</p>
                {msg.attachedImages && msg.attachedImages.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1 border-t border-blue-400/30">
                    {msg.attachedImages.map((imgUri, idx) => (
                      <img
                        key={idx}
                        src={imgUri}
                        alt="Attached upload"
                        onClick={() => setPreviewImageModal(imgUri)}
                        className="w-24 h-24 object-cover rounded-lg border border-white/30 cursor-pointer hover:opacity-90 transition-opacity"
                      />
                    ))}
                  </div>
                )}
                <div className="text-[10px] text-blue-200 text-right mt-1 font-mono">{msg.timestamp}</div>
              </div>
            )}

            {/* TUTOR RESPONSE BUBBLE */}
            {msg.sender === 'tutor' && (
              msg.isKbUnavailable ? (
                <div className="w-full glass-panel rounded-3xl border border-amber-500/30 bg-amber-500/5 p-6 space-y-4 shadow-xl">
                  <div className="flex items-center gap-3 text-amber-400">
                    <AlertTriangle className="w-6 h-6 shrink-0" />
                    <div>
                      <h3 className="text-base font-bold text-amber-200">Knowledge Base Not Available</h3>
                      <p className="text-xs text-amber-300/80">Subject: {subject.replace('_', ' ').toUpperCase()}</p>
                    </div>
                  </div>
                  <div className="text-sm text-slate-200 font-medium leading-relaxed bg-slate-900/80 p-4 rounded-2xl border border-amber-500/20">
                    {msg.answer}
                  </div>
                </div>
              ) : (
                <div className="w-full glass-panel rounded-3xl border border-slate-800 p-6 space-y-6 shadow-xl">
                  
                  {/* 1. TOPIC & CONFIDENCE BADGE */}
                  <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800">
                    <div className="flex items-center gap-3">
                      <span className="p-2 bg-blue-500/10 text-blue-400 rounded-xl">
                        <BrainCircuit className="w-5 h-5" />
                      </span>
                      <div>
                        <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Identified Course Topic</div>
                        <div className="text-sm font-bold text-white flex items-center gap-2">
                          {msg.topic}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800">
                      <span className="text-xs text-slate-400 font-medium">Confidence:</span>
                      <span className="text-xs font-mono font-bold text-emerald-400">{msg.topicConfidence}%</span>
                      <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${msg.topicConfidence}%` }}></div>
                      </div>
                      <span className="ml-2 text-[11px] font-semibold uppercase px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-300 border border-blue-500/20">
                        {msg.level || 'beginner'}
                      </span>
                    </div>
                  </div>

                  {/* 2. PREREQUISITE ANALYSIS BOX */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Completed Prerequisites */}
                    <div className="p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 space-y-2">
                      <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4" />
                        Completed Prerequisites (Mastered)
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.completedPrereqs.length > 0 ? (
                          msg.completedPrereqs.map((p, i) => (
                            <span key={i} className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 text-xs font-medium border border-emerald-500/20">
                              ✓ {p.replace('_', ' ')}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-slate-400">All basic requirements verified.</span>
                        )}
                      </div>
                    </div>

                    {/* Missing Prerequisites */}
                    <div className="p-4 rounded-2xl bg-amber-500/5 border border-amber-500/20 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
                          <AlertTriangle className="w-4 h-4" />
                          Missing Prerequisites (Click to mark learned)
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.missingPrereqs.length > 0 ? (
                          msg.missingPrereqs.map((p, i) => {
                            const isLearned = learnedTopics.has(p) || learnedTopics.has(p.toLowerCase()) || learnedTopics.has(p.replace('_', ' '));
                            return (
                              <button
                                key={i}
                                onClick={() => !isLearned && handleMarkLearned(msg.id, p, p)}
                                title={isLearned ? "Already learned and saved to database" : "Click to mark as learned in your database"}
                                className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all flex items-center gap-1 cursor-pointer ${
                                  isLearned
                                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                                    : 'bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border-amber-500/20 hover:border-amber-400'
                                }`}
                              >
                                {isLearned ? '✓' : '⚠'} {p.replace('_', ' ')} {isLearned ? '(Learned)' : '(Click to complete)'}
                              </button>
                            );
                          })
                        ) : (
                          <span className="text-xs text-slate-400">No missing prerequisites detected!</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* 3. PERSONALIZED LEARNING PATH CARD */}
                  {msg.learningPath.length > 0 && (
                    <div className="p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/20 space-y-3">
                      <span className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                        <Compass className="w-4 h-4 text-indigo-400" />
                        Personalized Learning Sequence
                      </span>
                      <div className="flex flex-wrap items-center gap-2 text-xs">
                        {msg.learningPath.map((step, idx) => (
                          <React.Fragment key={idx}>
                            <span className="px-3 py-1 rounded-xl bg-indigo-900/60 text-indigo-200 border border-indigo-700/50 font-medium">
                              {idx + 1}. {step.replace('_', ' ').toUpperCase()}
                            </span>
                            {idx < msg.learningPath.length - 1 && (
                              <span className="text-indigo-400 font-bold">→</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 3.5 RETRIEVED DIAGRAMS & IMAGES CARD */}
                  {msg.images && msg.images.length > 0 && (
                    <div className="p-4 rounded-2xl bg-purple-500/5 border border-purple-500/20 space-y-3">
                      <span className="text-xs font-bold text-purple-300 flex items-center gap-1.5">
                        <ImageIcon className="w-4 h-4 text-purple-400" />
                        Retrieved Course Diagrams & Visual Material ({msg.images.length} Image{msg.images.length > 1 ? 's' : ''})
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {msg.images.map((imgObj, idx) => (
                          <div 
                            key={idx} 
                            onClick={() => setPreviewImageModal(imgObj.url || imgObj)}
                            className="p-2 bg-slate-900/90 rounded-xl border border-slate-800 hover:border-purple-500/40 cursor-pointer space-y-2 group transition-all"
                          >
                            <img 
                              src={imgObj.url || imgObj} 
                              alt={imgObj.caption || "Course Diagram"} 
                              className="w-full h-40 object-contain bg-slate-950 rounded-lg group-hover:scale-[1.02] transition-transform" 
                            />
                            <div className="text-[11px] font-semibold text-purple-200 text-center px-1 truncate">
                              {imgObj.caption || `Diagram ${idx + 1}`}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 4. MAIN LLM TUTOR EXPLANATION */}
                  <div className="prose prose-invert max-w-none text-sm leading-relaxed text-slate-200 space-y-3 pt-2">
                    <div className="font-bold text-base text-blue-300 flex items-center gap-2 border-b border-slate-800 pb-2">
                      <Bot className="w-5 h-5 text-blue-400" />
                      Personalized AI Explanation ({msg.level ? msg.level.toUpperCase() : 'BEGINNER'})
                    </div>
                    <div className="whitespace-pre-line text-slate-300 font-sans">
                      {msg.answer}
                    </div>
                  </div>

                  {/* 5. CITED SOURCES ACCORDION */}
                  {msg.sources.length > 0 && (
                    <div className="pt-3 border-t border-slate-800/80 space-y-3">
                      <button
                        onClick={() => toggleSources(msg.id)}
                        className="w-full flex items-center justify-between text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
                      >
                        <span className="flex items-center gap-1.5">
                          <FileText className="w-4 h-4 text-amber-400" />
                          Retrieved Course References ({msg.sources.length} Sources from ChromaDB)
                        </span>
                        {showSourcesMap[msg.id] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>

                      {showSourcesMap[msg.id] && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                          {msg.sources.map((src, idx) => (
                            <div key={idx} className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5 text-xs">
                              <div className="flex items-center justify-between font-mono text-[11px] text-amber-300">
                                <span>📄 {src.source_file || src.metadata?.source || 'Course Document'}</span>
                                <span>Unit {src.unit || '1'} • Page {src.page || '1'}</span>
                              </div>
                              <p className="text-[11px] text-slate-400 italic line-clamp-3 bg-slate-950 p-2 rounded border border-slate-900">
                                "{src.content || src.text}"
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* 6. MARK AS LEARNED BUTTON */}
                  <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
                    <div className="text-xs text-slate-400">
                      Learned topic <span className="font-semibold text-slate-200">{msg.topic}</span>?
                    </div>
                    <button
                      onClick={() => handleMarkLearned(msg.id, msg.rawTopic, msg.topic)}
                      disabled={learnedTopics.has(msg.rawTopic) || learnedTopics.has(msg.topic) || markingTopic === (msg.rawTopic || msg.topic)}
                      className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                        learnedTopics.has(msg.rawTopic) || learnedTopics.has(msg.topic)
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 cursor-default'
                          : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/20'
                      }`}
                    >
                      {learnedTopics.has(msg.rawTopic) || learnedTopics.has(msg.topic) ? (
                        <>
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          Learned ✓ (Saved to DB)
                        </>
                      ) : markingTopic === (msg.rawTopic || msg.topic) ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Saving to Database...
                        </>
                      ) : (
                        <>
                          <Award className="w-4 h-4" />
                          Mark as Learned
                        </>
                      )}
                    </button>
                  </div>

                </div>
              )
            )}
          </div>
        ))}

        {loading && (
          <div className="glass-panel p-6 rounded-3xl border border-slate-800 flex items-center gap-4 text-slate-300 text-sm">
            <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
            <div>
              <div className="font-bold text-white">Analyzing query & searching ChromaDB ({level.toUpperCase()} level)...</div>
              <div className="text-xs text-slate-400">Running topic classifier, checking prerequisites, and generating AI tutor response.</div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box with Level Selector */}
      <div className="glass-panel p-3.5 rounded-2xl border border-slate-800 shrink-0 space-y-2.5">
        {/* 3-Option Level Selector: Beginner, Intermediate, Advance */}
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-bold text-slate-300">Explanation Level:</span>
          </div>
          <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800">
            <button
              type="button"
              onClick={() => setLevel('beginner')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                level === 'beginner'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Beginner
            </button>
            <button
              type="button"
              onClick={() => setLevel('intermediate')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                level === 'intermediate'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Intermediate
            </button>
            <button
              type="button"
              onClick={() => setLevel('advance')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                level === 'advance' || level === 'advanced'
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Advance
            </button>
          </div>
        </div>

        {/* Attached Images Preview Chips */}
        {attachedImages.length > 0 && (
          <div className="flex flex-wrap gap-2 p-2 bg-slate-900/90 rounded-xl border border-slate-800">
            {attachedImages.map(img => (
              <div key={img.id} className="relative group shrink-0">
                <img src={img.dataUri} alt="Attached preview" className="w-16 h-16 object-cover rounded-lg border border-slate-700" />
                <button
                  type="button"
                  onClick={() => removeAttachedImage(img.id)}
                  className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-600 hover:bg-red-500 text-white rounded-full text-xs font-bold flex items-center justify-center shadow"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="flex items-center gap-2"
        >
          <input
            type="file"
            ref={fileInputRef}
            accept="image/*"
            multiple
            onChange={handleImageSelect}
            className="hidden"
          />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            title="Attach image(s) to your question"
            className="p-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-blue-500/40 text-slate-300 hover:text-blue-400 transition-all flex items-center gap-1 text-xs shrink-0"
          >
            <ImageIcon className="w-4 h-4 text-blue-400" />
            <span className="hidden sm:inline">Image</span>
          </button>

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Ask a question or upload image in ${subject.replace('_', ' ')} (${level.toUpperCase()} mode)...`}
            className="flex-1 bg-transparent px-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />

          <button
            type="submit"
            disabled={loading || (!query.trim() && attachedImages.length === 0)}
            className="p-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold shadow-lg shadow-blue-500/20 disabled:opacity-50 transition-all flex items-center gap-1.5 text-xs shrink-0"
          >
            <span>Send</span>
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Fullscreen Image Lightbox Modal */}
      {previewImageModal && (
        <div 
          onClick={() => setPreviewImageModal(null)}
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4"
        >
          <div className="relative max-w-4xl max-h-[90vh] bg-slate-900 p-2 rounded-2xl border border-slate-800 overflow-hidden flex flex-col items-center">
            <button
              onClick={() => setPreviewImageModal(null)}
              className="absolute top-3 right-3 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-bold z-10 border border-slate-700"
            >
              ✕ Close
            </button>
            <img src={previewImageModal} alt="Enlarged Diagram Preview" className="max-w-full max-h-[82vh] object-contain rounded-xl" />
          </div>
        </div>
      )}

    </div>
  );
};
