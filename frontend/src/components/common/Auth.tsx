import React, { useState } from 'react';
import { LogIn, UserPlus, GraduationCap, School, ShieldAlert, Check } from 'lucide-react';
import { User, Role } from '../../types';
import Footer from './Footer';

interface AuthProps {
  onLoginSuccess: (user: User) => void;
}

export default function Auth({ onLoginSuccess }: AuthProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState<Role>('student');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = isLogin ? '/v1/auth/login' : '/v1/auth/register';
      const body = isLogin 
        ? { email, password } 
        : { name, email, password, role };

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Authentication failed');
      }

      onLoginSuccess(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (quickEmail: string) => {
    setEmail(quickEmail);
    setPassword('password');
    setIsLogin(true);
  };

  return (
    <div className="min-h-screen flex bg-slate-50 font-sans">
      
      {/* Left Column: Form */}
      <div className="flex-1 flex flex-col justify-center px-4 sm:px-6 lg:flex-none lg:w-1/2 lg:px-20 xl:px-24 py-12 relative z-10">
        <div className="mx-auto w-full max-w-md lg:w-96 space-y-8 bg-white/80 backdrop-blur-xl p-8 rounded-2xl shadow-xl border border-white">
          <div className="text-center">
            <div className="mx-auto h-12 w-12 rounded-xl bg-teal-50 flex items-center justify-center border border-teal-100 shadow-sm">
              <GraduationCap className="h-6 w-6 text-teal-600" id="auth-logo-icon" />
            </div>
            <h2 className="mt-6 text-3xl font-bold tracking-tight text-slate-900 flex items-center justify-center gap-2">
              SmilAI
            </h2>
            <p className="mt-2 text-sm font-medium text-slate-500">
              Offline Virtual-Teacher Platform
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-sm flex items-center gap-2 animate-pulse">
              <ShieldAlert className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-slate-700">Full Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 text-sm bg-white/50"
                  placeholder="e.g. Rahul Kumar"
                  id="reg-name-input"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-700">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 text-sm bg-white/50"
                placeholder="you@school.org"
                id="auth-email-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 text-sm bg-white/50"
                placeholder="••••••••"
                id="auth-password-input"
              />
            </div>

            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-slate-700">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as Role)}
                  className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 text-sm bg-white/50"
                  id="reg-role-select"
                >
                  <option value="student">Student</option>
                  <option value="teacher">Teacher (Real Educator)</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-lg shadow-md shadow-teal-500/20 text-sm font-bold text-white bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition-all cursor-pointer disabled:opacity-55 mt-6"
              id="auth-submit-btn"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Processing...
                </span>
              ) : isLogin ? (
                <span className="flex items-center gap-2"><LogIn className="h-4 w-4" /> Log In</span>
              ) : (
                <span className="flex items-center gap-2"><UserPlus className="h-4 w-4" /> Sign Up</span>
              )}
            </button>
          </form>

          <div className="text-center mt-4">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm font-semibold text-teal-600 hover:text-teal-500 cursor-pointer"
              id="toggle-auth-mode-btn"
            >
              {isLogin ? "Don't have an account? Sign Up" : "Already have an account? Log In"}
            </button>
          </div>

          {/* Quick Seeder Login Options */}
          <div className="border-t border-slate-100 pt-6 mt-6">
            <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-widest text-center mb-3">
              Quick Sandbox Demo Accounts
            </p>
            <div className="grid grid-cols-1 gap-2">
              <button
                onClick={() => handleQuickLogin('rahul@school.org')}
                className="flex items-center justify-between px-3 py-2 border border-slate-100 hover:border-teal-200 bg-slate-50/50 hover:bg-teal-50/50 text-xs rounded-lg text-slate-600 hover:text-teal-800 transition-all text-left cursor-pointer"
                id="quick-login-student"
              >
                <span className="flex items-center gap-2">
                  <GraduationCap className="h-3.5 w-3.5 text-teal-500" />
                  <span>Student: <strong>Rahul Kumar</strong></span>
                </span>
                <span className="text-[10px] text-slate-400 font-mono">rahul@school.org</span>
              </button>
              <button
                onClick={() => handleQuickLogin('sharma@school.org')}
                className="flex items-center justify-between px-3 py-2 border border-slate-100 hover:border-indigo-200 bg-slate-50/50 hover:bg-indigo-50/50 text-xs rounded-lg text-slate-600 hover:text-indigo-800 transition-all text-left cursor-pointer"
                id="quick-login-teacher"
              >
                <span className="flex items-center gap-2">
                  <School className="h-3.5 w-3.5 text-indigo-500" />
                  <span>Teacher: <strong>Mr. Sharma</strong></span>
                </span>
                <span className="text-[10px] text-slate-400 font-mono">sharma@school.org</span>
              </button>
              <button
                onClick={() => handleQuickLogin('admin@school.org')}
                className="flex items-center justify-between px-3 py-2 border border-slate-100 hover:border-amber-200 bg-slate-50/50 hover:bg-amber-50/50 text-xs rounded-lg text-slate-600 hover:text-amber-800 transition-all text-left cursor-pointer"
                id="quick-login-admin"
              >
                <span className="flex items-center gap-2">
                  <LogIn className="h-3.5 w-3.5 text-amber-500" />
                  <span>Admin: <strong>School Administrator</strong></span>
                </span>
                <span className="text-[10px] text-slate-400 font-mono">admin@school.org</span>
              </button>
            </div>
          </div>
        </div>
        
        {/* Footer hidden on desktop so it doesn't break split layout, visible on mobile */}
        <div className="lg:hidden mt-8">
          <Footer />
        </div>
      </div>

      {/* Right Column: Dynamic Hero Banner (Hidden on Mobile) */}
      <div className="hidden lg:block relative w-0 flex-1">
        <img
          className="absolute inset-0 h-full w-full object-cover rounded-l-[40px] shadow-2xl shadow-teal-900/20"
          src="/login_banner.png"
          alt="SmilAI Education Platform"
        />
        <div className="absolute inset-0 bg-teal-900/40 mix-blend-multiply rounded-l-[40px]"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-teal-900/90 via-teal-900/20 to-transparent rounded-l-[40px] flex items-end">
          <div className="p-16 text-white w-full max-w-3xl">
            <h2 className="text-5xl font-extrabold tracking-tight mb-4 animate-float" style={{animationDuration: '6s'}}>Empower Every Mind.</h2>
            <p className="text-xl text-teal-50 mb-8 leading-relaxed font-light">
              SmilAI is an offline-first, highly personalized mentoring and assessment engine. Step into the classroom of the future.
            </p>
            
            <div className="flex gap-4">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md border border-white/30 text-sm font-semibold shadow-sm">
                <Check className="h-4 w-4" /> 100% Offline AI
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md border border-white/30 text-sm font-semibold shadow-sm">
                <Check className="h-4 w-4" /> Voice Interactive
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md border border-white/30 text-sm font-semibold shadow-sm">
                <Check className="h-4 w-4" /> Personal Tutor
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
