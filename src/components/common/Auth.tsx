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
    <div className="min-h-screen flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-2xl shadow-sm border border-slate-100">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 rounded-xl bg-teal-50 flex items-center justify-center border border-teal-100">
            <GraduationCap className="h-6 w-6 text-teal-600" id="auth-logo-icon" />
          </div>
          <h2 className="mt-6 text-3xl font-bold tracking-tight text-slate-900 flex items-center justify-center gap-2">
            SmilAI
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Offline Virtual-Teacher & Assessment Platform
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
                className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 text-sm"
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
              className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 text-sm"
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
              className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 text-sm"
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
                className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 text-sm"
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
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition-colors disabled:opacity-55 mt-6"
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
            className="text-sm font-medium text-teal-600 hover:text-teal-500 cursor-pointer"
            id="toggle-auth-mode-btn"
          >
            {isLogin ? "Don't have an account? Sign Up" : "Already have an account? Log In"}
          </button>
        </div>

        {/* Quick Seeder Login Options */}
        <div className="border-t border-slate-100 pt-6 mt-6">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center mb-3">
            Quick Sandbox Demo Accounts
          </p>
          <div className="grid grid-cols-1 gap-2">
            <button
              onClick={() => handleQuickLogin('rahul@school.org')}
              className="flex items-center justify-between px-3 py-2 border border-slate-100 hover:border-teal-200 bg-slate-50/50 hover:bg-teal-50/20 text-xs rounded-lg text-slate-600 hover:text-teal-800 transition-all text-left cursor-pointer"
              id="quick-login-student"
            >
              <span className="flex items-center gap-2">
                <GraduationCap className="h-3.5 w-3.5 text-teal-500" />
                <span>Student: <strong>Rahul Kumar</strong></span>
              </span>
              <span className="text-[10px] text-slate-400">rahul@school.org</span>
            </button>
            <button
              onClick={() => handleQuickLogin('sharma@school.org')}
              className="flex items-center justify-between px-3 py-2 border border-slate-100 hover:border-indigo-200 bg-slate-50/50 hover:bg-indigo-50/20 text-xs rounded-lg text-slate-600 hover:text-indigo-800 transition-all text-left cursor-pointer"
              id="quick-login-teacher"
            >
              <span className="flex items-center gap-2">
                <School className="h-3.5 w-3.5 text-indigo-500" />
                <span>Teacher: <strong>Mr. Sharma</strong></span>
              </span>
              <span className="text-[10px] text-slate-400">sharma@school.org</span>
            </button>
            <button
              onClick={() => handleQuickLogin('admin@school.org')}
              className="flex items-center justify-between px-3 py-2 border border-slate-100 hover:border-amber-200 bg-slate-50/50 hover:bg-amber-50/20 text-xs rounded-lg text-slate-600 hover:text-amber-800 transition-all text-left cursor-pointer"
              id="quick-login-admin"
            >
              <span className="flex items-center gap-2">
                <LogIn className="h-3.5 w-3.5 text-amber-500" />
                <span>Admin: <strong>School Administrator</strong></span>
              </span>
              <span className="text-[10px] text-slate-400">admin@school.org</span>
            </button>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
