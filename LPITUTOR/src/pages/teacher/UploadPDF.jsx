import React, { useState, useEffect, useRef } from 'react';
import { teacherService } from '../../services/api';
import { Upload, FileText, CheckCircle2, Loader2, Database, AlertCircle, ArrowRight, X, Trash2 } from 'lucide-react';

export const UploadPDFModal = ({ subject, onClose, onRefresh }) => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadedFilesCount, setUploadedFilesCount] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState('');
  
  const [building, setBuilding] = useState(false);
  const [buildProgressPct, setBuildProgressPct] = useState(0);
  const [buildStageText, setBuildStageText] = useState('');
  const [buildDone, setBuildDone] = useState(false);
  const [buildError, setBuildError] = useState('');

  const pollIntervalRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setSelectedFiles(prev => {
        const existingNames = new Set(prev.map(f => f.name));
        const added = newFiles.filter(f => !existingNames.has(f.name));
        return [...prev, ...added];
      });
      setUploadSuccess(false);
      setUploadError('');
    }
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    setUploading(true);
    setUploadError('');
    try {
      const res = await teacherService.uploadPDF(subject.id, selectedFiles);
      setUploadedFilesCount(selectedFiles.length);
      setUploadSuccess(true);
      if (onRefresh) onRefresh();
    } catch (e) {
      console.error(e);
      setUploadError(e.response?.data?.detail || "Failed to upload files. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const handlePrepareKB = async () => {
    setBuilding(true);
    setBuildError('');
    setBuildDone(false);
    setBuildProgressPct(10);
    setBuildStageText('Initializing Knowledge Base builder...');

    try {
      await teacherService.prepareKB(subject.id);
      
      // Poll build status from backend
      pollIntervalRef.current = setInterval(async () => {
        try {
          const statusRes = await teacherService.getBuildStatus(subject.id);
          if (statusRes) {
            setBuildProgressPct(statusRes.progress_pct || 50);
            setBuildStageText(statusRes.stage || 'Processing PDFs...');

            if (statusRes.status === 'ready') {
              clearInterval(pollIntervalRef.current);
              setBuildDone(true);
              setBuilding(false);
              setBuildProgressPct(100);
              if (onRefresh) onRefresh();
            } else if (statusRes.status === 'error') {
              clearInterval(pollIntervalRef.current);
              setBuilding(false);
              setBuildError(statusRes.stage || "Error building knowledge base.");
            }
          }
        } catch (err) {
          console.warn('Polling status note:', err);
        }
      }, 800);

    } catch (e) {
      console.error(e);
      setBuilding(false);
      setBuildError(e.response?.data?.detail || "Failed to initiate Knowledge Base build.");
    }
  };

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const [prereqFile, setPrereqFile] = useState(null);
  const [uploadingPrereq, setUploadingPrereq] = useState(false);
  const [prereqSuccess, setPrereqSuccess] = useState(false);
  const [prereqError, setPrereqError] = useState('');

  const handlePrereqFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setPrereqFile(e.target.files[0]);
      setPrereqSuccess(false);
      setPrereqError('');
    }
  };

  const handleUploadPrerequisites = async () => {
    if (!prereqFile) return;
    setUploadingPrereq(true);
    setPrereqError('');
    try {
      await teacherService.uploadPrerequisites(subject.id, prereqFile);
      setPrereqSuccess(true);
      if (onRefresh) onRefresh();
    } catch (e) {
      console.error(e);
      setPrereqError(e.response?.data?.detail || "Failed to upload prerequisite JSON. Please check format.");
    } finally {
      setUploadingPrereq(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md overflow-y-auto">
      <div className="glass-panel w-full max-w-2xl rounded-3xl border border-slate-800 p-6 sm:p-8 shadow-2xl relative space-y-6 my-8">
        
        {/* Close button */}
        <button 
          onClick={onClose}
          className="absolute top-6 right-6 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-amber-400">Faculty Workspace</span>
          <h2 className="text-xl font-bold text-white mt-1 flex items-center gap-2">
            Subject Workspace: <span className="text-blue-400">{subject.name}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Upload unit PDFs, configure prerequisite rules, and build RAG knowledge bases for student AI tutoring.
          </p>
        </div>

        {/* Step 1: Upload Multiple PDFs */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Upload className="w-4 h-4 text-blue-400" />
            1. Upload Course Syllabus & Unit PDFs (Multiple Allowed)
          </h3>

          <div className="border-2 border-dashed border-slate-800 hover:border-blue-500/50 rounded-2xl p-6 text-center transition-colors">
            <input
              type="file"
              accept=".pdf"
              multiple
              id="pdf-upload-multi"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="pdf-upload-multi" className="cursor-pointer space-y-2 block">
              <FileText className="w-10 h-10 text-slate-500 mx-auto" />
              <div className="text-sm font-medium text-slate-200">
                Click to select or drag PDF files here
              </div>
              <div className="text-xs text-slate-400">Supports selecting multiple PDF files at once</div>
            </label>
          </div>

          {/* Selected Files List */}
          {selectedFiles.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-bold text-slate-300 flex items-center justify-between">
                <span>Selected Files ({selectedFiles.length}):</span>
                <button
                  type="button"
                  onClick={() => setSelectedFiles([])}
                  className="text-[11px] text-rose-400 hover:underline"
                >
                  Clear All
                </button>
              </div>
              <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1">
                {selectedFiles.map((f, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                    <div className="flex items-center gap-2 truncate">
                      <FileText className="w-4 h-4 text-blue-400 shrink-0" />
                      <span className="text-slate-200 font-medium truncate">{f.name}</span>
                      <span className="text-slate-500 font-mono text-[10px]">({(f.size / (1024 * 1024)).toFixed(2)} MB)</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(idx)}
                      className="text-slate-500 hover:text-rose-400 p-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {uploadError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-medium">
              {uploadError}
            </div>
          )}

          {selectedFiles.length > 0 && !uploadSuccess && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Uploading {selectedFiles.length} PDF(s)...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" /> Confirm & Upload {selectedFiles.length} PDF(s)
                </>
              )}
            </button>
          )}

          {uploadSuccess && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{uploadedFilesCount > 0 ? `${uploadedFilesCount} PDF document(s)` : 'Documents'} uploaded successfully! Ready for Knowledge Base indexing.</span>
            </div>
          )}
        </div>

        {/* Step 2: Prerequisite JSON Configuration Upload */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <FileText className="w-4 h-4 text-amber-400" />
            2. Upload Subject Prerequisite JSON Rules
          </h3>

          <div className="border border-dashed border-slate-800 hover:border-amber-500/50 rounded-2xl p-4 text-center transition-colors bg-slate-950/40">
            <input
              type="file"
              accept=".json"
              id="prereq-json-upload"
              onChange={handlePrereqFileChange}
              className="hidden"
            />
            <label htmlFor="prereq-json-upload" className="cursor-pointer space-y-1 block">
              <FileText className="w-7 h-7 text-amber-400/80 mx-auto" />
              <div className="text-xs font-medium text-slate-200">
                {prereqFile ? prereqFile.name : "Click to select Prerequisite JSON configuration file"}
              </div>
              <div className="text-[11px] text-slate-400">Example: &#123;"deadlock": ["process", "resource_allocation"]&#125;</div>
            </label>
          </div>

          {prereqError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-medium">
              {prereqError}
            </div>
          )}

          {prereqFile && !prereqSuccess && (
            <button
              onClick={handleUploadPrerequisites}
              disabled={uploadingPrereq}
              className="w-full py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              {uploadingPrereq ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Uploading Prerequisite Rules...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" /> Save Subject Prerequisite Rules
                </>
              )}
            </button>
          )}

          {prereqSuccess && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Prerequisite rules successfully updated and linked to {subject.name}!</span>
            </div>
          )}
        </div>

        {/* Step 3: Non-blocking KB Build Progress */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Database className="w-4 h-4 text-purple-400" />
              3. Prepare Knowledge Base (ChromaDB Indexing)
            </h3>
            {!building && (
              <button
                onClick={handlePrepareKB}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-xs shadow-lg shadow-purple-500/20 flex items-center gap-2"
              >
                <Database className="w-4 h-4" /> {buildDone ? "Rebuild Knowledge Base" : "Create Knowledge Base"}
              </button>
            )}
          </div>

          {/* Real Live Progress Indicator */}
          {(building || buildDone || buildProgressPct > 0) && (
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-purple-300 flex items-center gap-2">
                  {building && <Loader2 className="w-4 h-4 animate-spin text-purple-400" />}
                  {buildDone && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                  {buildStageText}
                </span>
                <span className="font-mono text-slate-300">{buildProgressPct}%</span>
              </div>

              {/* Progress bar */}
              <div className="w-full h-2 rounded-full bg-slate-900 border border-slate-800 overflow-hidden">
                <div 
                  className={`h-full transition-all duration-300 ${buildDone ? 'bg-emerald-500' : 'bg-gradient-to-r from-purple-600 to-indigo-500'}`}
                  style={{ width: `${buildProgressPct}%` }}
                ></div>
              </div>
            </div>
          )}

          {buildError && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-medium flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {buildError}
            </div>
          )}

          {buildDone && (
            <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs font-medium space-y-1">
              <div className="font-bold text-sm text-purple-200 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Knowledge Base Ready for Students!
              </div>
              <p>
                Collection <code className="bg-slate-900 px-1.5 py-0.5 rounded text-purple-300 font-mono">{subject.id}_knowledge_base</code> is indexed and active for student AI RAG queries.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium text-xs transition-colors"
          >
            Done
          </button>
        </div>

      </div>
    </div>
  );
};
