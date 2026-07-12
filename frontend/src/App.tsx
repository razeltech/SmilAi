import React, { useState, useEffect } from 'react';
import Auth from './components/common/Auth.tsx';
import Header from './components/common/Header.tsx';
import Footer from './components/common/Footer.tsx';
import AdminDashboard from './components/dashboard/AdminDashboard.tsx';
import TeacherDashboard from './components/dashboard/TeacherDashboard.tsx';
import StudentDashboard from './components/dashboard/StudentDashboard.tsx';
import { User, Subject } from './types';

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [orgSettings, setOrgSettings] = useState<any>(null);

  const [isInitializing, setIsInitializing] = useState(true);

  const fetchWithRetry = async (url: string, retries = 5, delay = 1000): Promise<Response> => {
    for (let i = 0; i < retries; i++) {
      try {
        const res = await fetch(url);
        if (res.ok) return res;
      } catch (err) {
        // Network error (ECONNREFUSED from proxy)
      }
      if (i < retries - 1) await new Promise(resolve => setTimeout(resolve, delay));
    }
    throw new Error('Backend unavailable after retries');
  };

  const fetchOrgSettings = async () => {
    try {
      const res = await fetchWithRetry('/v1/org-settings');
      const data = await res.json();
      setOrgSettings(data);
    } catch (err) {
      console.error('Failed to fetch org settings:', err);
    }
  };

  // Check if session exists in localStorage for immediate offline-first load
  useEffect(() => {
    const init = async () => {
      await fetchOrgSettings();
      const cachedUser = localStorage.getItem('smilai_user');
      if (cachedUser) {
        const u = JSON.parse(cachedUser);
        setUser(u);
        await fetchSubjects(u);
      }
      setIsInitializing(false);
    };
    init();
  }, []);

  const fetchSubjects = async (u: User) => {
    try {
      const res = await fetchWithRetry(`/v1/subjects?userId=${u.id}&role=${u.role}`);
      const data = await res.json();
      setSubjects(data);
      if (data.length > 0) {
        // Find default mathematical subject for Sharma or first
        if (u.role === 'teacher') {
          const teachSub = data.find((s: Subject) => s.teacherId === u.id);
          setSelectedSubject(teachSub || data[0]);
        } else {
          setSelectedSubject(data[0]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch subjects:', err);
    }
  };

  const handleLoginSuccess = (loggedInUser: User) => {
    setUser(loggedInUser);
    localStorage.setItem('smilai_user', JSON.stringify(loggedInUser));
    fetchSubjects(loggedInUser);
    fetchOrgSettings();
  };

  const handleLogout = () => {
    setUser(null);
    setSelectedSubject(null);
    setSubjects([]);
    localStorage.removeItem('smilai_user');
    if (window.speechSynthesis) window.speechSynthesis.cancel();
  };

  if (isInitializing) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center font-sans">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-teal-600 mb-4"></div>
        <h2 className="text-xl text-slate-700 font-semibold">Connecting to SmilAI Brain...</h2>
        <p className="text-slate-500 mt-2 text-sm">Loading AI models and local database (usually takes a few seconds)</p>
      </div>
    );
  }

  if (!user) {
    return <Auth onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header
        user={user}
        subjects={subjects}
        selectedSubject={selectedSubject}
        onSelectSubject={setSelectedSubject}
        onLogout={handleLogout}
        orgSettings={orgSettings}
      />

      <main className="flex-grow">
        {user.role === 'admin' && (
          <AdminDashboard 
            user={user} 
            onRefreshSubjects={() => fetchSubjects(user)} 
            onRefreshOrgSettings={fetchOrgSettings}
          />
        )}

        {user.role === 'teacher' && selectedSubject && (
          <TeacherDashboard user={user} subject={selectedSubject} />
        )}

        {user.role === 'student' && selectedSubject && (
          <StudentDashboard user={user} subject={selectedSubject} />
        )}

        {user.role !== 'admin' && !selectedSubject && (
          <div className="max-w-7xl mx-auto px-4 py-16 text-center text-slate-500">
            No subjects configured or assigned yet. Please contact the administrator to create a subject.
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
