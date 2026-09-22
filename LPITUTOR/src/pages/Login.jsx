import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { Bot, Shield, GraduationCap, BookOpen, ArrowRight, CheckCircle2, KeyRound, Mail, User, Building, Lock, Loader2, Sparkles, UserPlus, Check } from 'lucide-react';

export const Login = () => {
  const { setUser } = useAuth();
  const navigate = useNavigate();

  // Active Tab: 'student', 'teacher', 'admin', or 'signup'
  const [activeTab, setActiveTab] = useState('student');

  // Login Form States
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  // Signup / OTP Verification States
  const [signupStage, setSignupStage] = useState(1); // 1: Info, 2: OTP & Set Password
  const [signupRole, setSignupRole] = useState('student');
  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [department, setDepartment] = useState('');
  const [selectedSubjects, setSelectedSubjects] = useState(['operating_systems']);
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [receivedOtp, setReceivedOtp] = useState('');
  const [signupMsg, setSignupMsg] = useState('');
  const [signupError, setSignupError] = useState('');
  const [signupLoading, setSignupLoading] = useState(false);

  const ALL_AVAILABLE_SUBJECTS = [
    { id: 'operating_systems', name: 'Operating Systems' },
    { id: 'computer_networks', name: 'Computer Networks' },
    { id: 'data_structures', name: 'Data Structures' },
    { id: 'dbms', name: 'DBMS' },
    { id: 'software_engineering', name: 'Software Engineering' }
  ];

  const toggleSubject = (subId) => {
    setSelectedSubjects(prev => {
      if (prev.includes(subId)) {
        if (prev.length === 1) return prev; // Keep at least 1 selected
        return prev.filter(s => s !== subId);
      } else {
        return [...prev, subId];
      }
    });
  };

  const handlePortalSwitch = (portal) => {
    setActiveTab(portal);
    setLoginError('');
    setEmail('');
    setPassword('');
  };

  // Handle Login for Student, Teacher, or Admin
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);

    try {
      const res = await authService.login(email.trim(), password, activeTab);
      if (res && res.user) {
        if (activeTab === 'admin' && res.user.role !== 'admin') {
          throw new Error("This account is not authorized for Admin access.");
        }
        if (activeTab === 'teacher' && res.user.role !== 'teacher') {
          throw new Error("This account is not a registered Teacher account. Please use Student login.");
        }
        if (activeTab === 'student' && res.user.role !== 'student') {
          throw new Error("This account is a Teacher/Admin account. Please use the appropriate portal.");
        }

        const userData = { ...res.user, token: res.token };
        localStorage.setItem('pragtutor_user', JSON.stringify(userData));
        if (setUser) setUser(userData);

        if (res.user.role === 'admin') navigate('/admin');
        else if (res.user.role === 'teacher') navigate('/teacher');
        else navigate('/student');
        return;
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Invalid credentials. Please check your email and password.";
      setLoginError(msg);
    } finally {
      setLoginLoading(false);
    }
  };

  // Step 1: Request Email OTP from pragtutor.ai@gmail.com
  const handleRequestOTP = async (e) => {
    e.preventDefault();
    setSignupError('');
    setSignupMsg('');
    setSignupLoading(true);

    try {
      const res = await authService.requestOTP(
        signupEmail.trim(), 
        signupName.trim(), 
        signupRole, 
        department.trim(),
        signupRole === 'teacher' ? selectedSubjects : []
      );
      setReceivedOtp(res.otp_debug || '');
      setSignupMsg(res.message || `Verification OTP code sent from pragtutor.ai@gmail.com to ${signupEmail}.`);
      setSignupStage(2);
    } catch (err) {
      setSignupError(err.response?.data?.detail || "Failed to send OTP code. Please check your email and try again.");
    } finally {
      setSignupLoading(false);
    }
  };

  // Step 2: Verify OTP & Set Password
  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setSignupError('');
    setSignupLoading(true);

    try {
      const res = await authService.verifyOTPRegister(signupEmail.trim(), otp.trim(), newPassword);
      if (res && res.user) {
        const userData = { ...res.user, token: res.token };
        localStorage.setItem('pragtutor_user', JSON.stringify(userData));
        if (setUser) setUser(userData);

        if (res.user.role === 'teacher') navigate('/teacher');
        else navigate('/student');
        return;
      }
    } catch (err) {
      setSignupError(err.response?.data?.detail || "Invalid OTP verification code. Please check your email and try again.");
    } finally {
      setSignupLoading(false);
    }
  };

  const autoFillOtp = () => {
    if (receivedOtp) setOtp(receivedOtp);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-10 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-600/15 rounded-full blur-3xl pointer-events-none"></div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center z-10">
        <div className="mx-auto w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 p-0.5 shadow-xl shadow-blue-500/20 mb-3 flex items-center justify-center">
          <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
            <Bot className="w-9 h-9 text-blue-400" />
          </div>
        </div>
        <h2 className="text-3xl font-extrabold text-white tracking-tight">
          PragTutor <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">AI Learning</span>
        </h2>
        <p className="mt-1.5 text-xs text-slate-400">
          Personalized AI Tutoring Platform for Engineering
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md z-10">
        <div className="glass-panel py-7 px-6 shadow-2xl rounded-3xl sm:px-8 border border-slate-800 space-y-5">
          
          {/* 4 Navigation Tabs: Student, Teacher, Admin, Sign Up */}
          <div className="grid grid-cols-4 gap-1.5 bg-slate-900/90 p-1.5 rounded-2xl border border-slate-800 text-[11px] font-bold">
            <button
              type="button"
              onClick={() => handlePortalSwitch('student')}
              className={`py-2 px-1 rounded-xl flex items-center justify-center gap-1 transition-all ${
                activeTab === 'student' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <GraduationCap className="w-3.5 h-3.5" /> Student
            </button>

            <button
              type="button"
              onClick={() => handlePortalSwitch('teacher')}
              className={`py-2 px-1 rounded-xl flex items-center justify-center gap-1 transition-all ${
                activeTab === 'teacher' ? 'bg-amber-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" /> Teacher
            </button>

            <button
              type="button"
              onClick={() => handlePortalSwitch('admin')}
              className={`py-2 px-1 rounded-xl flex items-center justify-center gap-1 transition-all ${
                activeTab === 'admin' ? 'bg-purple-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Shield className="w-3.5 h-3.5" /> Admin
            </button>

            <button
              type="button"
              onClick={() => { setActiveTab('signup'); setSignupStage(1); setSignupError(''); }}
              className={`py-2 px-1 rounded-xl flex items-center justify-center gap-1 transition-all ${
                activeTab === 'signup' ? 'bg-emerald-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <UserPlus className="w-3.5 h-3.5" /> Sign Up
            </button>
          </div>

          {/* PORTAL TITLE BADGE */}
          {activeTab !== 'signup' && (
            <div className="text-center pt-1">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
                activeTab === 'admin' ? 'bg-purple-500/10 text-purple-300 border-purple-500/30' :
                activeTab === 'teacher' ? 'bg-amber-500/10 text-amber-300 border-amber-500/30' :
                'bg-blue-500/10 text-blue-300 border-blue-500/30'
              }`}>
                {activeTab === 'admin' && <Shield className="w-3.5 h-3.5 text-purple-400" />}
                {activeTab === 'teacher' && <BookOpen className="w-3.5 h-3.5 text-amber-400" />}
                {activeTab === 'student' && <GraduationCap className="w-3.5 h-3.5 text-blue-400" />}
                {activeTab.toUpperCase()} PORTAL LOGIN
              </span>
            </div>
          )}

          {/* ------------------------------------------------------------- */}
          {/* LOGIN FORMS (STUDENT / TEACHER / ADMIN) */}
          {/* ------------------------------------------------------------- */}
          {activeTab !== 'signup' && (
            <form className="space-y-4" onSubmit={handleLoginSubmit}>
              {loginError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-medium">
                  {loginError}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-blue-500"
                    placeholder={activeTab === 'admin' ? "vundhyalaakeshreddy@gmail.com" : "email@university.edu"}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-blue-500"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loginLoading}
                className={`w-full py-3 px-4 rounded-xl text-white font-semibold text-sm shadow-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 ${
                  activeTab === 'admin' ? 'bg-gradient-to-r from-purple-600 to-indigo-600 shadow-purple-500/25' :
                  activeTab === 'teacher' ? 'bg-gradient-to-r from-amber-600 to-orange-600 shadow-amber-500/25' :
                  'bg-gradient-to-r from-blue-600 to-indigo-600 shadow-blue-500/25'
                }`}
              >
                {loginLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : `Log In to ${activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Portal`}
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

          {/* ------------------------------------------------------------- */}
          {/* EMAIL OTP SIGNUP FORM (pragtutor.ai@gmail.com Sender) */}
          {/* ------------------------------------------------------------- */}
          {activeTab === 'signup' && (
            <div className="space-y-4">
              <div className="text-center">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                  <UserPlus className="w-3.5 h-3.5 text-emerald-400" /> EMAIL OTP ACCOUNT REGISTRATION
                </span>
              </div>

              {/* Role Picker for Signup */}
              <div className="grid grid-cols-2 gap-2 bg-slate-900/60 p-1 rounded-xl border border-slate-800">
                <button
                  type="button"
                  onClick={() => setSignupRole('student')}
                  className={`py-2 px-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                    signupRole === 'student' ? 'bg-blue-600 text-white' : 'text-slate-400'
                  }`}
                >
                  <GraduationCap className="w-3.5 h-3.5" /> Student Account
                </button>
                <button
                  type="button"
                  onClick={() => setSignupRole('teacher')}
                  className={`py-2 px-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                    signupRole === 'teacher' ? 'bg-amber-600 text-white' : 'text-slate-400'
                  }`}
                >
                  <BookOpen className="w-3.5 h-3.5" /> Teacher Account
                </button>
              </div>

              {signupError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-medium">
                  {signupError}
                </div>
              )}

              {/* STAGE 1: Request OTP via Email */}
              {signupStage === 1 && (
                <form className="space-y-3" onSubmit={handleRequestOTP}>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Full Name</label>
                    <div className="relative">
                      <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        required
                        value={signupName}
                        onChange={(e) => setSignupName(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-emerald-500"
                        placeholder="Your Full Name"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Your Email Address</label>
                    <div className="relative">
                      <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="email"
                        required
                        value={signupEmail}
                        onChange={(e) => setSignupEmail(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-emerald-500"
                        placeholder="your.email@university.edu"
                      />
                    </div>
                  </div>

                  {signupRole === 'teacher' && (
                    <>
                      <div>
                        <label className="block text-xs font-semibold text-slate-300 mb-1">Department</label>
                        <div className="relative">
                          <Building className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                          <input
                            type="text"
                            required
                            value={department}
                            onChange={(e) => setDepartment(e.target.value)}
                            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-emerald-500"
                            placeholder="e.g. Computer Science & Engineering"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                          Assigned Subjects <span className="text-amber-400 font-normal">(Select 1 or more)</span>
                        </label>
                        <div className="space-y-1.5 bg-slate-900/90 p-3 rounded-xl border border-slate-800 max-h-44 overflow-y-auto">
                          {ALL_AVAILABLE_SUBJECTS.map((sub) => {
                            const isChecked = selectedSubjects.includes(sub.id);
                            return (
                              <div
                                key={sub.id}
                                onClick={() => toggleSubject(sub.id)}
                                className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${
                                  isChecked
                                    ? 'bg-amber-500/10 border-amber-500/40 text-amber-300'
                                    : 'bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-slate-200'
                                }`}
                              >
                                <span className="text-xs font-medium">{sub.name}</span>
                                <div className={`w-4 h-4 rounded flex items-center justify-center border ${
                                  isChecked ? 'bg-amber-500 border-amber-500 text-slate-950' : 'border-slate-700 bg-slate-900'
                                }`}>
                                  {isChecked && <Check className="w-3 h-3 stroke-[3]" />}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </>
                  )}

                  <button
                    type="submit"
                    disabled={signupLoading}
                    className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm shadow-lg shadow-emerald-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                  >
                    {signupLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Send Verification OTP to Email"}
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </form>
              )}

              {/* STAGE 2: Enter Email OTP & Set Password */}
              {signupStage === 2 && (
                <form className="space-y-4" onSubmit={handleVerifyOTP}>
                  {signupMsg && (
                    <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-medium leading-relaxed space-y-2">
                      <div className="flex items-start gap-2">
                        <Mail className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <div>
                          <span>Verification OTP code sent from </span>
                          <strong className="text-white font-mono">pragtutor.ai@gmail.com</strong>
                          <span> to </span>
                          <strong className="text-white font-mono">{signupEmail}</strong>.
                        </div>
                      </div>
                      
                      {receivedOtp && (
                        <div className="flex items-center justify-between pt-1 border-t border-emerald-500/20">
                          <span className="text-[11px] text-amber-300 font-semibold flex items-center gap-1">
                            <Sparkles className="w-3.5 h-3.5" /> Code Received: <span className="font-mono text-xs text-white">{receivedOtp}</span>
                          </span>
                          <button
                            type="button"
                            onClick={autoFillOtp}
                            className="px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/30 text-[10px] font-bold transition-all flex items-center gap-1"
                          >
                            <Check className="w-3 h-3" /> Auto-Fill Code
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Enter 6-Digit OTP Code</label>
                    <div className="relative">
                      <KeyRound className="w-4 h-4 text-amber-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        required
                        maxLength={6}
                        value={otp}
                        onChange={(e) => setOtp(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-amber-300 font-mono text-base tracking-widest focus:outline-none focus:border-amber-500"
                        placeholder="123456"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">Create Account Password</label>
                    <div className="relative">
                      <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="password"
                        required
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-emerald-500"
                        placeholder="••••••••"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={signupLoading}
                    className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm shadow-lg shadow-emerald-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                  >
                    {signupLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Verify OTP & Complete Registration"}
                    <CheckCircle2 className="w-4 h-4" />
                  </button>
                </form>
              )}

            </div>
          )}

        </div>
      </div>
    </div>
  );
};
