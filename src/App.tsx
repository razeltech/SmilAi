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

  const fetchOrgSettings = async () => {
    try {
      const res = await fetch('/v1/org-settings');
      if (res.ok) {
        const data = await res.json();
        setOrgSettings(data);
      }
    } catch (err) {
      console.error('Failed to fetch org settings:', err);
    }
  };

  // Check if session exists in localStorage for immediate offline-first load
  useEffect(() => {
    fetchOrgSettings();
    const cachedUser = localStorage.getItem('smilai_user');
    if (cachedUser) {
      const u = JSON.parse(cachedUser);
      setUser(u);
      fetchSubjects(u);
    }
  }, []);

  const fetchSubjects = async (u: User) => {
    try {
      const res = await fetch(`/v1/subjects?userId=${u.id}&role=${u.role}`);
      if (res.ok) {
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
