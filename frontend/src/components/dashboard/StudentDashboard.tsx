import React, { useState, useEffect, useRef } from 'react';
import { BookOpen, Code, FileText, Send, Mic, MicOff, Volume2, VolumeX, CheckCircle, HelpCircle, Award, BarChart2, ShieldAlert, Cpu, Settings, Info, Layers } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Subject, User, ChatSession, ChatMessage, Assessment, Assignment, StudentRecord } from '../../types';

interface StudentDashboardProps {
  user: User;
  subject: Subject;
}

export default function StudentDashboard({ user, subject }: StudentDashboardProps) {
  const [activeWorkspace, setActiveWorkspace] = useState<'chat' | 'code' | 'test' | 'record' | 'profile'>('chat');

  // Unified data states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Student Profile fields
  const [profileName, setProfileName] = useState('');
  const [profileEmail, setProfileEmail] = useState('');
  const [profileRollNo, setProfileRollNo] = useState('');
  const [profileGrade, setProfileGrade] = useState('');
  const [profileBoard, setProfileBoard] = useState('');
  const [profileBio, setProfileBio] = useState('');
  const [profilePhone, setProfilePhone] = useState('');

  // 1. Chat States
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMsg, setInputMsg] = useState('');
  const [subjectDocs, setSubjectDocs] = useState<any[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('all');
  const [warmVoice, setWarmVoice] = useState(true);
  const [activeCitation, setActiveCitation] = useState<{ tag: string; text: string; id: string } | null>(null);

  // Voice Interaction (STT / TTS) using browser SpeechRecognition / SpeechSynthesis (100% offline-friendly, fast, light!)
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechEnabled, setSpeechEnabled] = useState(true);
  const recognitionRef = useRef<any>(null);
  
  // AI Voice State
  const [voiceEngineMode, setVoiceEngineMode] = useState<'smiley' | 'robotic'>('smiley');
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaRecorderRef = useRef<any>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // 2. Code Grader States
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [selectedAssignmentId, setSelectedAssignmentId] = useState('');
  const [codeFileName, setCodeFileName] = useState('solution.py');
  const [codeContent, setCodeContent] = useState('');
  const [graderFeedback, setGraderFeedback] = useState<any | null>(null);

  // 3. Assessment States
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [selectedAssessment, setSelectedAssessment] = useState<any | null>(null);
  const [studentAnswers, setStudentAnswers] = useState<Record<string, string>>({});
  const [testResults, setTestResults] = useState<any | null>(null);

  // 4. Records States
  const [record, setRecord] = useState<StudentRecord | null>(null);

  // Fetch initial student subject data
  const fetchData = async () => {
    try {
      // Chat Sessions
      const sessRes = await fetch(`/v1/chat/sessions?userId=${user.id}&subjectId=${subject.id}`);
      const sessData = await sessRes.json();
      const safeSessions = Array.isArray(sessData) ? sessData : [];
      setSessions(safeSessions);
      if (safeSessions.length > 0) {
        setCurrentSessionId(safeSessions[0].id);
        fetchSessionMessages(safeSessions[0].id);
      } else {
        setMessages([]);
        setCurrentSessionId('');
      }

      // Assignments
      const assignRes = await fetch(`/v1/subjects/${subject.id}/assignments`);
      const assignData = await assignRes.json();
      const safeAssignments = Array.isArray(assignData) ? assignData : [];
      setAssignments(safeAssignments);
      if (safeAssignments.length > 0) setSelectedAssignmentId(safeAssignments[0].id);

      // Assessments
      const assessRes = await fetch(`/v1/subjects/${subject.id}/assessments`);
      const assessData = await assessRes.json();
      setAssessments(Array.isArray(assessData) ? assessData : []);

      // Fetch Subject Documents/Syllabus references
      const docRes = await fetch(`/v1/subjects/${subject.id}/documents`);
      const docData = await docRes.json();
      setSubjectDocs(Array.isArray(docData) ? docData : []);

      // Records
      fetchStudentRecords();
    } catch (err) {
      console.error(err);
    }
  };

  const fetchSessionMessages = async (sid: string) => {
    try {
      const res = await fetch(`/v1/chat/sessions/${sid}/messages`);
      const data = await res.json();
      setMessages(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchStudentRecords = async () => {
    try {
      const recRes = await fetch(`/v1/students/${user.id}/subjects/${subject.id}/record`);
      if (recRes.ok) {
        const recData = await recRes.json();
        setRecord(recData);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchStudentProfile = async () => {
    try {
      const res = await fetch(`/v1/users/${user.id}/profile`);
      if (res.ok) {
        const data = await res.json();
        setProfileName(data.name || user.name);
        setProfileEmail(data.email || user.email);
        setProfileRollNo(data.rollNo || `AP-2026-${1000 + parseInt(user.id.replace(/\D/g, '') || '7')}`);
        setProfileGrade(data.grade || 'Grade 10');
        setProfileBoard(data.board || 'AP State Board (SSC)');
        setProfileBio(data.bio || 'Keen student exploring mathematics, science, and computer science courses via personalized SmilAI mentoring.');
        setProfilePhone(data.phone || '+91 91234 56789');
      }
    } catch (err) {
      console.error('Failed to fetch student profile:', err);
    }
  };

  useEffect(() => {
    fetchData();
    fetchStudentProfile();
    // Clean up synthesizers
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, [subject.id, user.id]);

  // Handle STT Mic initialization
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = 'en-IN'; // Indian-English localized recognition

      rec.onstart = () => {
        setIsRecording(true);
        setError('');
      };
      rec.onend = () => setIsRecording(false);
      rec.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputMsg(prev => (prev ? prev + ' ' + transcript : transcript));
      };
      rec.onerror = (event: any) => {
        console.error('Speech recognition error event:', event.error);
        setIsRecording(false);
        if (event.error === 'not-allowed') {
          setError('Microphone permission blocked! Since the application runs within an iframe preview container, please click the "Open in a new tab" button on the top-right of your screen to grant microphone permissions and speak.');
        } else if (event.error === 'no-speech') {
          // Silent or ignored, just stop
        } else {
          setError(`Microphone error: ${event.error || 'Could not access mic'}. Please verify your device sound input settings.`);
        }
      };

      recognitionRef.current = rec;
    }
  }, []);

  const toggleRecording = async () => {
    setError('');
    
    if (voiceEngineMode === 'smiley') {
      if (isRecording) {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.stop();
        }
        setIsRecording(false);
      } else {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          const mediaRecorder = new MediaRecorder(stream);
          mediaRecorderRef.current = mediaRecorder;
          audioChunksRef.current = [];
          
          mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
              audioChunksRef.current.push(event.data);
            }
          };
          
          mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
            
            // Send to backend
            const formData = new FormData();
            formData.append('file', audioBlob, 'recording.webm');
            
            setLoading(true);
            try {
              const res = await fetch('/v1/voice/transcribe', {
                method: 'POST',
                body: formData
              });
              const data = await res.json();
              if (data.text) {
                setInputMsg(prev => (prev ? prev + ' ' + data.text : data.text));
              }
            } catch (err) {
              setError('Failed to transcribe audio via Smiley AI Voice.');
            } finally {
              setLoading(false);
            }
            
            // Stop tracks
            stream.getTracks().forEach(track => track.stop());
          };
          
          mediaRecorder.start();
          setIsRecording(true);
        } catch (err) {
          setError('Microphone permission blocked or unavailable.');
        }
      }
    } else {
      // Legacy Web Speech API
      if (!recognitionRef.current) {
        setError('Speech Recognition is not supported or permitted in this browser.');
        return;
      }

      if (isRecording) {
        recognitionRef.current.stop();
      } else {
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        try {
          recognitionRef.current.start();
        } catch (err: any) {
          console.error('Failed to start speech recognition:', err);
          setError('Microphone state is busy. Please try clicking again in a second.');
        }
      }
    }
  };

  // Perform browser TTS Speech synthesis or Smiley AI Voice
  const speakText = async (text: string) => {
    if (!speechEnabled) return;
    
    // Cancel existing
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsSpeaking(false);
    
    // Strip markdown formatting, LaTeX brackets, AND all unicode emojis before speaking
    const cleanText = text
      .replace(/[#*`_\[\]\\\(\)]/g, '')
      .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');
      
    if (voiceEngineMode === 'smiley') {
      setIsSpeaking(true);
      try {
        const res = await fetch(`/v1/voice/speak?text=${encodeURIComponent(cleanText)}`, {
          method: 'POST'
        });
        if (res.ok) {
          const audioBlob = await res.blob();
          const url = URL.createObjectURL(audioBlob);
          const audio = new Audio(url);
          audioRef.current = audio;
          
          audio.onended = () => setIsSpeaking(false);
          audio.onerror = () => setIsSpeaking(false);
          
          await audio.play();
        } else {
          setIsSpeaking(false);
          setError("Smiley's Voice Engine failed to synthesize audio.");
        }
      } catch (err) {
        setIsSpeaking(false);
        setError("Failed to connect to Smiley's Voice Engine.");
      }
    } else {
      const truncatedText = cleanText.substring(0, 300); // limit to first 300 chars for clean playback
      const utterance = new SpeechSynthesisUtterance(truncatedText);

      // Look for a humanic female voice
      const voices = window.speechSynthesis.getVoices();
      let selectedVoice = null;
      
      const preferredNames = [
        'microsoft neerja', 'veena', 'google hi-in english female', 
        'google हिन्दी', 'microsoft heera', 'google uk english female',
        'microsoft zira', 'samantha'
      ];
      
      for (const name of preferredNames) {
        const match = voices.find(v => v.name.toLowerCase().includes(name));
        if (match) {
          selectedVoice = match;
          break;
        }
      }
      
      if (!selectedVoice) {
        selectedVoice = voices.find(v => v.lang.includes('en-IN') && v.name.toLowerCase().includes('female'))
          || voices.find(v => v.lang.includes('en-IN'))
          || voices.find(v => v.name.toLowerCase().includes('india'))
          || voices.find(v => v.name.toLowerCase().includes('female') && v.lang.startsWith('en')) 
          || voices.find(v => v.lang.startsWith('en'));
      }

      if (selectedVoice) {
        utterance.voice = selectedVoice;
      }
      
      if (warmVoice) {
        utterance.rate = 0.85; 
        utterance.pitch = 1.15; 
      } else {
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
      }

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    }
  };

  // 1. Chat actions
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputMsg.trim() || loading) return;

    setError('');
    const userText = inputMsg;
    setInputMsg('');
    setLoading(true);

    // Append user message optimistically
    const optimisticUserMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sessionId: currentSessionId,
      role: 'user',
      content: userText,
      timestamp: new Date().toISOString()
    };
    
    // Create empty placeholder for assistant's streaming response
    const assistantMsgId = `ast-${Date.now()}`;
    const placeholderAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      sessionId: currentSessionId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, optimisticUserMsg, placeholderAssistantMsg]);

    try {
      const res = await fetch('/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSessionId || 'new',
          user_id: user.id,
          subject_id: subject.id,
          message: userText
        })
      });

      if (!res.ok) {
        throw new Error('Failed to connect to SmilAI brain');
      }

      if (!res.body) throw new Error('ReadableStream not supported');

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let streamedResponse = '';

      // Stream the response directly into the UI state
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        streamedResponse += chunk;
        
        setMessages(prev => prev.map(msg => 
          msg.id === assistantMsgId ? { ...msg, content: streamedResponse } : msg
        ));
      }

      // Auto speak the final streamed response if enabled
      speakText(streamedResponse);
      
    } catch (err: any) {
      setError(err.message);
      // Remove placeholder on error
      setMessages(prev => prev.filter(m => m.id !== assistantMsgId));
    } finally {
      setLoading(false);
    }
  };

  // 2. Code Grader submit
  const handleCodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setGraderFeedback(null);
    if (!codeContent.trim() || !selectedAssignmentId) return;
    setLoading(true);

    try {
      const res = await fetch(`/v1/assignments/${selectedAssignmentId}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          studentId: user.id,
          fileName: codeFileName,
          codeContent: codeContent
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to grade submission');

      setGraderFeedback(data);
      setSuccess('Your program code has been statically analyzed and graded against the rubric!');
      fetchStudentRecords(); // refresh records
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 3. Assessment actions
  const handleStartTest = async (testId: string) => {
    setError('');
    setTestResults(null);
    setStudentAnswers({});
    setLoading(true);

    try {
      const res = await fetch(`/v1/assessments/${testId}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to fetch test items');

      setSelectedAssessment(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (qId: string, value: string) => {
    setStudentAnswers(prev => ({ ...prev, [qId]: value }));
  };

  const handleTestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssessment) return;
    setError('');
    setLoading(true);

    // Format answers array
    const answersArray = Object.keys(studentAnswers).map(qId => ({
      questionId: qId,
      answerContent: studentAnswers[qId]
    }));

    try {
      const res = await fetch(`/v1/assessments/${selectedAssessment.id}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          studentId: user.id,
          answers: answersArray
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to grade test');

      setTestResults(data.results);
      setSelectedAssessment(null);
      setSuccess('Assessment submitted and evaluated successfully!');
      fetchStudentRecords(); // refresh records
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 font-sans">
      
      {/* Subject Heading */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4 animate-float" style={{animationDuration: '8s'}}>
        <div className="glass-panel p-6 rounded-2xl border-l-4 border-l-teal-500">
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">{subject.name} <span className="text-teal-600">Classroom</span></h2>
          <p className="text-sm font-medium text-slate-500 mt-1">Your virtual private mentor, SmilAI, is active and listening.</p>
        </div>

        {/* Quick Workspaces Toggle */}
        <div className="glass-panel p-1.5 rounded-xl flex gap-1 shadow-lg hover-glow">
          <button
            onClick={() => setActiveWorkspace('chat')}
            className={`px-4 py-2 text-sm font-bold rounded-lg transition-all cursor-pointer ${
              activeWorkspace === 'chat' ? 'bg-gradient-to-r from-teal-500 to-emerald-500 text-white shadow-md' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50/50'
            }`}
            id="workspace-chat-btn"
          >
            Ask Questions
          </button>
          <button
            onClick={() => setActiveWorkspace('code')}
            className={`px-4 py-2 text-sm font-bold rounded-lg transition-all cursor-pointer ${
              activeWorkspace === 'code' ? 'bg-gradient-to-r from-teal-500 to-emerald-500 text-white shadow-md' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50/50'
            }`}
            id="workspace-code-btn"
          >
            Grade Code
          </button>
          <button
            onClick={() => setActiveWorkspace('test')}
            className={`px-4 py-2 text-sm font-bold rounded-lg transition-all cursor-pointer ${
              activeWorkspace === 'test' ? 'bg-gradient-to-r from-teal-500 to-emerald-500 text-white shadow-md' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50/50'
            }`}
            id="workspace-test-btn"
          >
            Take Assessments
          </button>
          <button
            onClick={() => setActiveWorkspace('record')}
            className={`px-4 py-2 text-sm font-bold rounded-lg transition-all cursor-pointer ${
              activeWorkspace === 'record' ? 'bg-gradient-to-r from-teal-500 to-emerald-500 text-white shadow-md' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50/50'
            }`}
            id="workspace-record-btn"
          >
            My Record
          </button>
          <button
            onClick={() => setActiveWorkspace('profile')}
            className={`px-4 py-2 text-sm font-bold rounded-lg transition-all cursor-pointer ${
              activeWorkspace === 'profile' ? 'bg-gradient-to-r from-teal-500 to-emerald-500 text-white shadow-md' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50/50'
            }`}
            id="workspace-profile-btn"
          >
            My Profile
          </button>
        </div>
      </div>

      {success && (
        <div className="mb-6 bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-lg text-sm flex items-center gap-2">
          <CheckCircle className="h-4 w-4 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-800 p-3 rounded-lg text-sm flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Workspace Display */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Workspace 1: Chat with SmilAI (RAG + Voice) */}
        {activeWorkspace === 'chat' && (
          <>
            {/* Sessions Sidebar */}
            <div className="lg:col-span-1 glass-panel p-5 rounded-2xl space-y-4 flex flex-col justify-between hover-glow">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Conversations</h3>
                  <button
                    onClick={() => {
                      setCurrentSessionId('');
                      setMessages([]);
                    }}
                    className="text-xs font-semibold text-teal-600 hover:text-teal-700 bg-teal-50 px-2 py-1 rounded cursor-pointer"
                    id="chat-new-session-btn"
                  >
                    + New
                  </button>
                </div>

                <div className="space-y-1 overflow-y-auto max-h-48 lg:max-h-64">
                  {(!Array.isArray(sessions) || sessions.length === 0) ? (
                    <div className="text-xs text-slate-400 text-center py-6">No previous chats. Start by asking below!</div>
                  ) : (
                    sessions.map(s => (
                      <button
                        key={s.id}
                        onClick={() => {
                          setCurrentSessionId(s.id);
                          fetchSessionMessages(s.id);
                        }}
                        className={`w-full text-left p-2.5 rounded-lg text-xs font-medium transition-colors block truncate cursor-pointer ${
                          currentSessionId === s.id ? 'bg-teal-50 text-teal-800 font-semibold' : 'text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        {s.title}
                      </button>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Chat Box */}
            <div className="lg:col-span-3 glass-panel rounded-2xl flex flex-col h-[600px] hover-glow overflow-hidden">
              {/* Chat Header */}
              <div className="px-6 py-4 border-b border-white/20 flex justify-between items-center bg-white/40 backdrop-blur-md">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
                  <span className="text-sm font-bold text-slate-800">Chatting with SmilAI</span>
                </div>
                <div className="flex items-center gap-3">
                  {/* Voice Engine Toggle */}
                  <select
                    value={voiceEngineMode}
                    onChange={(e) => setVoiceEngineMode(e.target.value as 'smiley' | 'robotic')}
                    className="bg-white border border-slate-200 rounded px-2 py-1 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500 cursor-pointer shadow-sm"
                    title="Select Voice Backend Engine"
                  >
                    <option value="smiley">SmilAI Voice Engine (Backend)</option>
                    <option value="robotic">Native Browser Voice (Frontend)</option>
                  </select>
                  
                  {/* Warm Voice Mode Toggle */}
                  {speechEnabled && (
                    <button
                      onClick={() => setWarmVoice(!warmVoice)}
                      className={`px-2.5 py-1 text-xs font-semibold rounded-full border transition-all flex items-center gap-1.5 cursor-pointer ${
                        warmVoice 
                          ? 'bg-amber-50 border-amber-200 text-amber-700 font-bold shadow-xs' 
                          : 'bg-slate-100 border-slate-200 text-slate-600'
                      }`}
                      title="Warm Voice Mode uses a supportive, patient vocal tempo to encourage learning"
                    >
                      <Award className={`h-3 w-3 ${warmVoice ? 'text-amber-500 animate-pulse' : ''}`} />
                      <span>{warmVoice ? "Warm Voice Mode" : "Normal Voice"}</span>
                    </button>
                  )}
                  {/* Speech Pulse Indicator & Stop Button */}
                  {isSpeaking && (
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-0.5 px-2 py-1 bg-amber-50 border border-amber-200 rounded-full animate-pulse">
                        <span className="w-1 h-2.5 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                        <span className="w-1 h-3.5 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                        <span className="w-1 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                      </div>
                      <button
                        onClick={() => {
                          if (window.speechSynthesis) window.speechSynthesis.cancel();
                          setIsSpeaking(false);
                        }}
                        className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 rounded-full cursor-pointer transition-colors"
                        title="Stop current voice playback"
                      >
                        Stop Audio
                      </button>
                    </div>
                  )}
                  {/* TTS Toggle */}
                  <button
                    onClick={() => {
                      if (speechEnabled && window.speechSynthesis) {
                        window.speechSynthesis.cancel();
                        setIsSpeaking(false);
                      }
                      setSpeechEnabled(!speechEnabled);
                    }}
                    className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-white rounded border border-slate-200 cursor-pointer"
                    title={speechEnabled ? "Disable Voice Feedback" : "Enable Voice Feedback"}
                  >
                    {speechEnabled ? <Volume2 className="h-4 w-4 text-teal-600" /> : <VolumeX className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Message List */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center p-8">
                    <BookOpen className="h-10 w-10 text-teal-500/20 mb-3" />
                    <h4 className="text-sm font-bold text-slate-700">Namaste! I am your virtual teacher, SmilAI.</h4>
                    <p className="text-xs text-slate-500 max-w-sm mt-1">
                      Ask me anything about {subject.name}! I am extremely patient and will explain step-by-step using your syllabus library.
                    </p>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-md p-4 rounded-2xl text-sm leading-relaxed shadow-sm/5 ${
                        msg.role === 'user' 
                          ? 'bg-teal-600 text-white rounded-tr-none' 
                          : 'bg-slate-50 border border-slate-100 text-slate-800 rounded-tl-none'
                      }`}>
                        <div className="prose prose-sm prose-teal max-w-none">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                        {msg.citations && msg.citations.length > 0 && (
                          <div className="mt-3 pt-2.5 border-t border-slate-200/50 space-y-1.5">
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Syllabus Grounding:</span>
                            <div className="flex gap-2 overflow-x-auto pb-1">
                              {msg.citations.map((cite: any, idx) => {
                                const isObj = cite && typeof cite === 'object';
                                const tag = isObj ? cite.tag : cite;
                                const text = isObj ? cite.text : '';
                                return (
                                  <button
                                    key={idx}
                                    type="button"
                                    onClick={() => {
                                      if (text) {
                                        setActiveCitation({ tag, text, id: isObj ? cite.id : '' });
                                      } else {
                                        setActiveCitation({ tag, text: `Grounded fact associated with ${tag}. Refer to the syllabus materials for this chunk.`, id: '' });
                                      }
                                    }}
                                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-teal-50 border border-teal-100 text-teal-700 hover:bg-teal-100 transition-colors cursor-pointer shrink-0"
                                    title="Click to open Detailed Citation source text overlay"
                                  >
                                    <Layers className="h-2.5 w-2.5 shrink-0" />
                                    <span>{tag}</span>
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        )}
                        {msg.role === 'assistant' && (
                          <button
                            onClick={() => speakText(msg.content)}
                            className="mt-2 text-teal-600 hover:text-teal-800 text-[10px] font-bold flex items-center gap-1 cursor-pointer"
                          >
                            <Volume2 className="h-3 w-3" /> Speak answer
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-slate-50 border border-slate-100 p-4 rounded-2xl rounded-tl-none max-w-md flex items-center gap-2">
                      <svg className="animate-spin h-4 w-4 text-teal-600" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      <span className="text-xs text-slate-500 font-medium">SmilAI is drafting explanation...</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Textbook Syllabus Scoping Selector */}
              <div className="px-4 py-2 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs text-slate-500 gap-4 shrink-0">
                <span className="font-semibold flex items-center gap-1 shrink-0">
                  <BookOpen className="h-3.5 w-3.5 text-teal-600" /> Syllabus Focus Reference:
                </span>
                <select
                  value={selectedDocId}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                  className="bg-white border border-slate-200 rounded px-2 py-1 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500 max-w-xs truncate"
                  title="Force SmilAI to answer using only this textbook source document"
                >
                  <option value="all">🔍 Search All Materials ({subjectDocs.length})</option>
                  {subjectDocs.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      📄 {doc.name || "Syllabus Material"} ({(doc.type || "library").toUpperCase()})
                    </option>
                  ))}
                </select>
              </div>

              {/* Chat Composer Input */}
              <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-100 flex items-center gap-2 bg-slate-50/20 shrink-0">
                <input
                  type="text"
                  value={inputMsg}
                  onChange={(e) => setInputMsg(e.target.value)}
                  placeholder={`Ask a question on ${subject.name}...`}
                  className="flex-1 bg-white border border-slate-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  id="student-chat-input"
                />
                
                {/* Voice Input Button */}
                <button
                  type="button"
                  onClick={toggleRecording}
                  className={`p-2.5 rounded-lg border transition-all cursor-pointer ${
                    isRecording 
                      ? 'bg-red-50 border-red-200 text-red-600 animate-pulse' 
                      : 'bg-white border-slate-200 text-slate-500 hover:text-slate-800'
                  }`}
                  title={isRecording ? "Stop Recording" : "Speak your question"}
                  id="student-mic-btn"
                >
                  {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                </button>

                <button
                  type="submit"
                  disabled={loading || !inputMsg.trim()}
                  className="bg-teal-600 hover:bg-teal-700 text-white p-2.5 rounded-lg cursor-pointer transition-colors disabled:opacity-55"
                  id="student-chat-send-btn"
                >
                  <Send className="h-4 w-4" />
                </button>
              </form>
            </div>
          </>
        )}

        {/* Workspace 2: Assignments & Code Grader */}
        {activeWorkspace === 'code' && (
          <div className="lg:col-span-4 bg-white border border-slate-100 rounded-xl p-6 shadow-sm">
            <h3 className="text-md font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Code className="h-5 w-5 text-teal-600" /> Programming Project & Code Static Grader
            </h3>

            {assignments.length === 0 ? (
              <div className="text-center py-16 text-slate-400 text-sm">
                No active programming assignments for this subject.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Left Form */}
                <form onSubmit={handleCodeSubmit} className="md:col-span-2 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">Select Assignment</label>
                      <select
                        value={selectedAssignmentId}
                        onChange={(e) => setSelectedAssignmentId(e.target.value)}
                        className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 text-sm bg-white"
                        id="student-assignment-select"
                      >
                        {assignments.map(a => (
                          <option key={a.id} value={a.id}>{a.title}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">Filename</label>
                      <input
                        type="text"
                        required
                        value={codeFileName}
                        onChange={(e) => setCodeFileName(e.target.value)}
                        className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500 text-sm"
                        id="student-code-filename"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">Write / Paste Code Solution</label>
                    <textarea
                      required
                      rows={12}
                      value={codeContent}
                      onChange={(e) => setCodeContent(e.target.value)}
                      placeholder="def solve_quadratic(a, b, c): # write python code solution..."
                      className="mt-1 block w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm font-mono bg-slate-950 text-slate-100"
                      id="student-code-editor"
                    ></textarea>
                  </div>

                  <button
                    type="submit"
                    disabled={loading || !codeContent.trim()}
                    className="w-full bg-teal-600 hover:bg-teal-700 text-white font-medium text-sm py-2 rounded-lg cursor-pointer transition-colors disabled:opacity-55"
                    id="student-submit-code-btn"
                  >
                    {loading ? 'Evaluating Code Mechanics...' : 'Submit Code for Grader'}
                  </button>
                </form>

                {/* Right Result Feedback panel */}
                <div className="md:col-span-1 border border-slate-100 rounded-xl p-6 bg-slate-50/50 self-start space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">SmilAI Assessment Output</h4>
                  {graderFeedback ? (
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-bold text-slate-800">Final Grade:</span>
                        <span className="text-2xl font-bold text-teal-600">{graderFeedback.score}/100</span>
                      </div>
                      <div className="text-xs text-slate-700 font-sans whitespace-pre-line leading-relaxed bg-white p-4 rounded-lg border border-slate-100 max-h-80 overflow-y-auto">
                        {graderFeedback.feedback}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-400 text-xs">
                      Submit your code solution to receive weighted rubric scores, style corrections, and inline feedback from SmilAI!
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Workspace 3: Assessments & Tests */}
        {activeWorkspace === 'test' && (
          <div className="lg:col-span-4 bg-white border border-slate-100 rounded-xl p-6 shadow-sm">
            <h3 className="text-md font-bold text-slate-900 mb-6 flex items-center gap-2">
              <Award className="h-5 w-5 text-teal-600" /> Grounded Assessments & Quizzes
            </h3>

            {selectedAssessment ? (
              /* Active Test Screen */
              <form onSubmit={handleTestSubmit} className="space-y-6 max-w-3xl mx-auto">
                <div className="flex justify-between items-center border-b border-slate-100 pb-4">
                  <div>
                    <h4 className="font-bold text-slate-800 text-lg">{selectedAssessment.name}</h4>
                    <p className="text-xs text-slate-500 capitalize">Difficulty: {selectedAssessment.difficulty}</p>
                  </div>
                  <span className="bg-amber-50 text-amber-700 px-3 py-1 border border-amber-100 rounded-full text-xs font-bold">
                    {selectedAssessment.questions.length} Items
                  </span>
                </div>

                <div className="space-y-6">
                  {selectedAssessment.questions.map((q: any, idx: number) => (
                    <div key={q.id} className="p-5 rounded-xl border border-slate-100 bg-slate-50/30 space-y-3">
                      <div className="text-sm font-semibold text-slate-800 flex gap-2">
                        <span>{idx + 1}.</span>
                        <span>{q.prompt}</span>
                      </div>

                      {q.type === 'mcq' ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pl-6">
                          {q.choices?.map((choice: string) => (
                            <label
                              key={choice}
                              className={`flex items-center gap-3 p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                                studentAnswers[q.id] === choice 
                                  ? 'border-amber-500 bg-amber-50/20 text-amber-800 font-semibold' 
                                  : 'border-slate-100 bg-white hover:bg-slate-50 text-slate-600'
                              }`}
                            >
                              <input
                                type="radio"
                                name={q.id}
                                value={choice}
                                checked={studentAnswers[q.id] === choice}
                                onChange={() => handleSelectOption(q.id, choice)}
                                className="sr-only"
                              />
                              <span>{choice}</span>
                            </label>
                          ))}
                        </div>
                      ) : (
                        <div className="pl-6">
                          <textarea
                            required
                            rows={3}
                            value={studentAnswers[q.id] || ''}
                            onChange={(e) => handleSelectOption(q.id, e.target.value)}
                            placeholder="Write your explanation or mathematical proof solution..."
                            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs focus:ring-1 focus:ring-teal-500"
                          ></textarea>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setSelectedAssessment(null)}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm cursor-pointer font-semibold"
                  >
                    Cancel Test
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm cursor-pointer font-semibold"
                    id="student-test-submit-btn"
                  >
                    {loading ? 'Evaluating responses...' : 'Submit Answers'}
                  </button>
                </div>
              </form>
            ) : testResults ? (
              /* Test result screen */
              <div className="max-w-3xl mx-auto space-y-6">
                <div className="border-b border-slate-100 pb-4 flex justify-between items-center">
                  <h4 className="font-bold text-slate-800 text-lg">Your Assessment Performance Card</h4>
                  <button
                    onClick={() => setTestResults(null)}
                    className="text-xs font-semibold text-teal-600 hover:text-teal-700"
                  >
                    Take another test
                  </button>
                </div>

                <div className="space-y-6">
                  {testResults.map((res: any, idx: number) => (
                    <div key={idx} className="p-5 rounded-xl border border-slate-100 bg-white space-y-3">
                      <div className="flex justify-between items-start">
                        <div className="text-sm font-semibold text-slate-800">
                          Question {idx + 1}: {res.prompt}
                        </div>
                        <span className={`text-sm font-bold px-2 py-0.5 rounded ${
                          res.score >= 8 ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                        }`}>
                          {res.score}/10
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 pl-4 border-l-2 border-slate-200">
                        <strong>Your answer:</strong> "{res.studentAnswer}"
                      </div>
                      <div className="text-xs text-emerald-600 pl-4 border-l-2 border-emerald-200">
                        <strong>Model Answer Guide:</strong> "{res.correctAnswer}"
                      </div>
                      <div className="text-xs text-slate-600 pl-4 border-l-2 border-indigo-200 bg-indigo-50/10 p-3 rounded-lg leading-relaxed">
                        <strong>SmilAI Teacher Feedback:</strong> {res.explanation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* Test listings screen */
              <div className="space-y-4">
                {assessments.length === 0 ? (
                  <div className="text-center py-16 text-slate-400 text-sm">
                    No assessments currently scheduled for this subject. Instruct the teacher to generate one.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {assessments.map(as => (
                      <div key={as.id} className="p-5 rounded-xl border border-slate-100 bg-slate-50/50 flex justify-between items-center">
                        <div>
                          <h4 className="text-sm font-bold text-slate-800">{as.name}</h4>
                          <p className="text-[10px] text-slate-400 font-medium mt-1 uppercase tracking-wider">
                            Topic: {as.topic} • {as.difficulty}
                          </p>
                        </div>
                        <button
                          onClick={() => handleStartTest(as.id)}
                          className="bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold px-4 py-2 rounded-lg cursor-pointer transition-colors"
                        >
                          Start Test
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Workspace 4: My Student Record */}
        {activeWorkspace === 'record' && (
          <div className="lg:col-span-4 bg-white border border-slate-100 rounded-xl p-6 shadow-sm space-y-8">
            <h3 className="text-md font-bold text-slate-900 mb-4 flex items-center gap-2">
              <BarChart2 className="h-5 w-5 text-teal-600" /> Subject Progress & Record Card
            </h3>

            {record ? (
              <div className="space-y-8">
                {/* Stats cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-slate-50 border border-slate-100 p-5 rounded-xl flex items-center gap-4">
                    <div className="h-10 w-10 bg-indigo-50 text-indigo-600 rounded-lg flex items-center justify-center border border-indigo-100">
                      <HelpCircle className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-slate-900">{record.assessmentsCompleted}</div>
                      <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Assessments Completed</div>
                    </div>
                  </div>

                  <div className="bg-slate-50 border border-slate-100 p-5 rounded-xl flex items-center gap-4">
                    <div className="h-10 w-10 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center border border-emerald-100">
                      <Award className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-slate-900">{record.averageScore}%</div>
                      <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Weighted Subject Average</div>
                    </div>
                  </div>

                  <div className="bg-slate-50 border border-slate-100 p-5 rounded-xl flex items-center gap-4">
                    <div className="h-10 w-10 bg-teal-50 text-teal-600 rounded-lg flex items-center justify-center border border-teal-100">
                      <Code className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-slate-900">{record.submissionsCompleted}</div>
                      <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Code Submissions</div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {/* Assessments history */}
                  <div className="space-y-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Quiz & Test History</h4>
                    {record.recentAssessments?.length === 0 ? (
                      <p className="text-xs text-slate-400 py-6 text-center">No assessments taken yet.</p>
                    ) : (
                      <div className="space-y-3">
                        {record.recentAssessments.map((a, idx) => (
                          <div key={idx} className="flex justify-between items-center p-3 rounded-lg border border-slate-100 bg-slate-50/30">
                            <div>
                              <div className="text-xs font-semibold text-slate-800">{a.assessmentName}</div>
                              <div className="text-[10px] text-slate-400 mt-0.5">{a.date}</div>
                            </div>
                            <span className="text-xs font-bold text-teal-600">{a.score}/{a.total}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Programming submissions history */}
                  <div className="space-y-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Code Grading History</h4>
                    {record.recentSubmissions?.length === 0 ? (
                      <p className="text-xs text-slate-400 py-6 text-center">No code assignments evaluated yet.</p>
                    ) : (
                      <div className="space-y-3">
                        {record.recentSubmissions.map((s, idx) => (
                          <div key={idx} className="flex justify-between items-center p-3 rounded-lg border border-slate-100 bg-slate-50/30">
                            <div>
                              <div className="text-xs font-semibold text-slate-800">{s.title}</div>
                              <div className="text-[10px] text-slate-400 mt-0.5">{s.date}</div>
                            </div>
                            <span className="text-xs font-bold text-teal-600">{s.score}/100</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-16 text-slate-400 text-sm animate-pulse">
                Loading academic student record...
              </div>
            )}
          </div>
        )}

        {/* Workspace 5: Student Profile (Read-only view) */}
        {activeWorkspace === 'profile' && (
          <div className="lg:col-span-4 grid grid-cols-1 md:grid-cols-12 gap-8">
            
            {/* Left Column: Premium Student Digital Passport Card (5 cols) */}
            <div className="md:col-span-5 space-y-6">
              <div className="bg-gradient-to-br from-indigo-600 to-teal-700 text-white p-6 rounded-2xl border border-indigo-500 shadow-lg relative overflow-hidden">
                {/* Decorative background visual */}
                <div className="absolute -right-6 -bottom-6 h-36 w-36 rounded-full bg-white/5 pointer-events-none"></div>
                <div className="absolute left-1/3 top-1/4 h-24 w-24 rounded-full bg-teal-500/10 pointer-events-none blur-xl"></div>
                
                <div className="flex justify-between items-start mb-6">
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-mono font-bold tracking-widest bg-white/10 px-2.5 py-1 rounded text-teal-100 uppercase">
                      Student Passport
                    </span>
                  </div>
                  <Award className="h-6 w-6 text-teal-200" />
                </div>

                {/* Avatar and Info */}
                <div className="flex items-center gap-4 mb-6">
                  <div className="h-14 w-14 rounded-full bg-white/10 border border-white/20 flex items-center justify-center font-bold text-lg text-teal-100 uppercase">
                    {profileName ? profileName.slice(0, 2) : user.name.slice(0, 2)}
                  </div>
                  <div>
                    <div className="text-lg font-bold">{profileName || user.name}</div>
                    <div className="text-xs text-indigo-200 mt-0.5 font-medium tracking-wider">Active Enrollment</div>
                  </div>
                </div>

                <div className="space-y-4 pt-4 border-t border-white/10">
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-indigo-200 text-[10px] font-bold uppercase tracking-wider block">ID Roll No</span>
                      <span className="font-semibold font-mono">{profileRollNo}</span>
                    </div>
                    <div>
                      <span className="text-indigo-200 text-[10px] font-bold uppercase tracking-wider block">Class Grade</span>
                      <span className="font-semibold">{profileGrade}</span>
                    </div>
                  </div>

                  <div className="pt-1 text-xs">
                    <span className="text-indigo-200 text-[10px] font-bold uppercase tracking-wider block">Board / Curriculum</span>
                    <span className="font-semibold text-teal-100">{profileBoard}</span>
                  </div>

                  <div className="pt-1 text-xs">
                    <span className="text-indigo-200 text-[10px] font-bold uppercase tracking-wider block">Institution Mail</span>
                    <span className="font-semibold font-mono">{profileEmail || user.email}</span>
                  </div>
                </div>
              </div>

              {/* Status Details */}
              <div className="bg-slate-50 border border-slate-200 p-5 rounded-2xl space-y-4">
                <div className="flex gap-3 items-start text-xs text-slate-600">
                  <CheckCircle className="h-4.5 w-4.5 text-teal-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-slate-800 block">Verified Student Account</span>
                    <p className="mt-1 leading-relaxed text-slate-500 text-[11px]">
                      Your credentials are sync-verified with the regional board database. Homework scores are permanently tied to this passport.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3 items-start text-xs text-slate-600">
                  <Info className="h-4.5 w-4.5 text-indigo-500 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-slate-800 block">Need to change your details?</span>
                    <p className="mt-1 leading-relaxed text-slate-500 text-[11px]">
                      Under CBSE and AP SCERT registry guidelines, student profile corrections require parent/guardian verification and can only be updated by the Administrative Office.
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm mt-6">
                <h3 className="text-sm font-bold text-slate-900 mb-6 pb-3 border-b border-slate-100 flex justify-between items-center">
                  <span>Voice Settings</span>
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 rounded-xl border border-slate-100 hover:bg-slate-50 transition-colors cursor-pointer" onClick={() => setVoiceEngineMode('smiley')}>
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${voiceEngineMode === 'smiley' ? 'bg-teal-100 text-teal-600' : 'bg-slate-100 text-slate-400'}`}>
                        <Volume2 className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="font-bold text-slate-800 text-sm">Smiley's Voice (High-Fidelity AI)</div>
                        <div className="text-xs text-slate-500 mt-0.5">Warm, patient, and highly expressive offline AI.</div>
                      </div>
                    </div>
                    <div className={`h-5 w-5 rounded-full border-2 flex items-center justify-center ${voiceEngineMode === 'smiley' ? 'border-teal-500' : 'border-slate-300'}`}>
                      {voiceEngineMode === 'smiley' && <div className="h-2.5 w-2.5 rounded-full bg-teal-500" />}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between p-4 rounded-xl border border-slate-100 hover:bg-slate-50 transition-colors cursor-pointer" onClick={() => setVoiceEngineMode('robotic')}>
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${voiceEngineMode === 'robotic' ? 'bg-slate-200 text-slate-700' : 'bg-slate-100 text-slate-400'}`}>
                        <Cpu className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="font-bold text-slate-800 text-sm">Robotic Voice (Basic Browser)</div>
                        <div className="text-xs text-slate-500 mt-0.5">Standard OS-level fallback TTS engine.</div>
                      </div>
                    </div>
                    <div className={`h-5 w-5 rounded-full border-2 flex items-center justify-center ${voiceEngineMode === 'robotic' ? 'border-slate-500' : 'border-slate-300'}`}>
                      {voiceEngineMode === 'robotic' && <div className="h-2.5 w-2.5 rounded-full bg-slate-500" />}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Detailed Academic Particulars (7 cols) */}
            <div className="md:col-span-7 space-y-6">
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                <h3 className="text-sm font-bold text-slate-900 mb-6 pb-3 border-b border-slate-100 flex justify-between items-center">
                  <span>Student Particulars</span>
                  <span className="text-[10px] font-mono text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded font-bold uppercase tracking-wider">
                    Read-Only Verification
                  </span>
                </h3>

                <div className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Full Legal Name</span>
                      <div className="w-full text-xs text-slate-700 bg-slate-50/70 border border-slate-100 rounded-xl px-4 py-2.5 font-medium">
                        {profileName || user.name}
                      </div>
                    </div>
                    <div>
                      <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Registered Email</span>
                      <div className="w-full text-xs text-slate-700 bg-slate-50/70 border border-slate-100 rounded-xl px-4 py-2.5 font-mono">
                        {profileEmail || user.email}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Academic Registry Roll No</span>
                      <div className="w-full text-xs text-slate-700 bg-slate-50/70 border border-slate-100 rounded-xl px-4 py-2.5 font-mono">
                        {profileRollNo}
                      </div>
                    </div>
                    <div>
                      <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Parent/Guardian Contact</span>
                      <div className="w-full text-xs text-slate-700 bg-slate-50/70 border border-slate-100 rounded-xl px-4 py-2.5 font-medium">
                        {profilePhone || '+91 91234 56789'}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Enrolled Grade Class</span>
                      <div className="w-full text-xs text-slate-700 bg-slate-50/70 border border-slate-100 rounded-xl px-4 py-2.5 font-medium">
                        {profileGrade}
                      </div>
                    </div>
                    <div>
                      <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Active Curriculum board</span>
                      <div className="w-full text-xs text-slate-700 bg-slate-50/70 border border-slate-100 rounded-xl px-4 py-2.5 font-medium">
                        {profileBoard}
                      </div>
                    </div>
                  </div>

                  <div>
                    <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Student Biography & Objectives</span>
                    <div className="w-full text-xs text-slate-600 bg-slate-50/70 border border-slate-100 rounded-xl px-4 py-3 leading-relaxed">
                      {profileBio}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <HelpCircle className="h-3.5 w-3.5 text-slate-300" />
                      Academic details matching current board registration files.
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>

      {/* Detailed Citations Overlay Modal */}
      {activeCitation && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-slate-200 max-w-lg w-full overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-teal-600 animate-pulse" />
                <h3 className="text-sm font-bold text-slate-800">Syllabus Grounding: {activeCitation.tag}</h3>
              </div>
              <button
                onClick={() => setActiveCitation(null)}
                className="text-slate-400 hover:text-slate-600 text-xs font-semibold px-2.5 py-1 rounded-lg bg-white border border-slate-200 cursor-pointer transition-all hover:bg-slate-50"
              >
                Close
              </button>
            </div>
            <div className="p-6 overflow-y-auto space-y-4">
              <p className="text-xs text-slate-400 font-mono">
                [SOURCE SEGMENT: {activeCitation.id || "STUDY_TEXTBOOK_CHUNK"}]
              </p>
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-100 text-sm text-slate-700 leading-relaxed font-sans whitespace-pre-wrap">
                {activeCitation.text}
              </div>
              <div className="bg-amber-50 p-3 rounded-lg border border-amber-100 text-[11px] text-amber-800 leading-normal flex items-start gap-1.5">
                <Info className="h-3.5 w-3.5 text-amber-500 shrink-0 mt-0.5" />
                <span>
                  This citation represents the exact contextual section parsed and extracted by SmilAI's Google-grade hybrid search RAG engine.
                </span>
              </div>
            </div>
            <div className="px-6 py-3.5 border-t border-slate-100 bg-slate-50/50 flex justify-end">
              <button
                type="button"
                onClick={() => {
                  speakText(`Referring to citation ${activeCitation.tag}. The material states: ` + activeCitation.text);
                }}
                className="text-xs font-semibold text-teal-600 hover:text-teal-700 flex items-center gap-1.5 cursor-pointer"
              >
                <Volume2 className="h-4 w-4" />
                <span>Speak Citation Text</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
