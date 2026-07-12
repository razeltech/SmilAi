import React from 'react';
import { LogOut, GraduationCap, BookOpen, Layers } from 'lucide-react';
import { User, Subject } from '../../types';

interface HeaderProps {
  user: User;
  subjects: Subject[];
  selectedSubject: Subject | null;
  onSelectSubject: (subject: Subject) => void;
  onLogout: () => void;
  orgSettings?: any;
}

export default function Header({ user, subjects, selectedSubject, onSelectSubject, onLogout, orgSettings }: HeaderProps) {
  return (
    <header className="bg-white border-b border-slate-100 sticky top-0 z-50 font-sans shadow-sm/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-teal-50 border border-teal-100 flex items-center justify-center">
              <GraduationCap className="h-5 w-5 text-teal-600" />
            </div>
            <div>
              <h1 className="text-sm font-extrabold text-slate-900 leading-none truncate max-w-[200px] sm:max-w-[320px]" title={orgSettings?.name || 'SmilAI'}>
                {orgSettings?.name || 'SmilAI'}
              </h1>
              <p className="text-[9px] text-teal-600 font-bold mt-1 uppercase tracking-wider">
                {orgSettings?.boardType === 'ap_govt_ssc' ? 'AP Govt State Syllabus (SSC)' : 
                 orgSettings?.boardType === 'private_ssc' ? 'AP Private State Syllabus (SSC)' : 
                 orgSettings?.boardType === 'private_cbse' ? 'AP Private Central Board (CBSE)' : 'Virtual Teacher Platform'}
              </p>
            </div>
          </div>

          {/* Subject Switcher for Students & Teachers */}
          {user.role !== 'admin' && subjects.length > 0 && (
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-slate-400 shrink-0" />
              <select
                value={selectedSubject?.id || ''}
                onChange={(e) => {
                  const s = subjects.find(subj => subj.id === e.target.value);
                  if (s) onSelectSubject(s);
                }}
                className="text-sm font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
                id="header-subject-select"
              >
                <option value="" disabled>Select Subject</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.gradeBandName || 'Class 10'})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* User Profile Info & Log Out */}
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-semibold text-slate-900">{user.name}</div>
              <div className="text-[10px] text-slate-400 flex items-center justify-end gap-1 font-medium capitalize">
                <span className={`inline-block w-1.5 h-1.5 rounded-full ${
                  user.role === 'admin' ? 'bg-amber-400' : user.role === 'teacher' ? 'bg-indigo-400' : 'bg-teal-400'
                }`}></span>
                {user.role} Account
              </div>
            </div>

            <button
              onClick={onLogout}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg border border-slate-100 transition-colors cursor-pointer"
              title="Log Out"
              id="header-logout-btn"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
