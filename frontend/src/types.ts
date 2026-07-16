/**
 * SmilAI Shared Type Declarations
 */

export type Role = 'student' | 'teacher' | 'admin';

export interface Organization {
  id: string;
  name: string;
  boardType?: 'ap_govt_ssc' | 'private_ssc' | 'private_cbse';
  schoolCode?: string;
  contactEmail?: string;
  phone?: string;
  address?: string;
  mediumOfInstruction?: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  orgId: string;
  phone?: string;
  bio?: string;
  designation?: string;
  qualification?: string;
  specialization?: string;
  class?: string;
  rollNumber?: string;
  dob?: string;
  guardianName?: string;
  guardianPhone?: string;
  mediumOfInstruction?: string;
}

export interface ProfileApproval {
  id: string;
  userId: string;
  teacherName: string;
  name: string;
  phone: string;
  bio: string;
  qualification: string;
  specialization: string;
  status: 'pending' | 'approved' | 'rejected';
  createdAt: string;
  decidedAt?: string;
  adminNotes?: string;
}

export interface GradeBand {
  id: string;
  orgId: string;
  name: string; // e.g., "Class 8", "Class 10"
}

export interface Subject {
  id: string;
  orgId: string;
  gradeBandId: string;
  name: string; // e.g., "English", "Telugu", "Hindi", "Mathematics", "Science", "Social Studies"
  teacherId: string;
  teacherName?: string;
  gradeBandName?: string;
  category?: 'GENERAL' | 'PROGRAMMING' | 'SCIENCE' | 'LANGUAGE' | 'MEDICAL';
  supports_projects?: number;
  is_active?: number;
}

export interface Document {
  id: string;
  subjectId: string;
  orgId: string;
  name: string;
  content: string;
  type: 'library' | 'personal';
  chunkCount: number;
  uploadedAt: string;
  status?: string;
  confidenceScore?: string;
  confidence_score?: string;
}

export interface Chunk {
  id: string;
  docId: string;
  orgId: string;
  subjectId: string;
  text: string;
  index: number;
}

export interface ChatSession {
  id: string;
  userId: string;
  subjectId: string;
  title: string;
  createdAt: string;
}

export interface ChatMessage {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: string[]; // Source chunks cited
  audioUrl?: string; // Generated speech audio URL
}

export interface Assessment {
  id: string;
  subjectId: string;
  name: string;
  questionCount: number;
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
  createdAt: string;
  subjectName?: string;
  status?: 'draft' | 'published' | 'archived';
  publishedAt?: string;
}

export interface Question {
  id: string;
  assessmentId: string;
  type: 'mcq' | 'short_answer';
  prompt: string;
  choices?: string[]; // Used for MCQ, stored as JSON string in SQL
  correctAnswer?: string;
  sourceCitations?: string; // Explanation of where it's cited
}

export interface StudentAnswer {
  id: string;
  questionId: string;
  studentId: string;
  answerContent: string;
  score?: number; // Graded score out of 10 or 1
  explanation?: string; // Teacher or AI feedback
  gradedBy?: 'deterministic' | 'llm_rubric';
  teacherOverride?: number | null;
}

export interface Assignment {
  id: string;
  subjectId: string;
  title: string;
  description: string;
  rubric: string; // Rubric description/criteria
  dueDate: string;
  status?: 'draft' | 'published' | 'archived';
  publishedAt?: string;
}

export interface Submission {
  id: string;
  assignmentId: string;
  studentId: string;
  fileName: string;
  codeContent: string;
  submittedAt: string;
  assignmentTitle?: string;
  score?: number;
  feedback?: string;
  teacherOverride?: number | null;
}

export interface StudentRecord {
  studentId: string;
  studentName: string;
  subjectId: string;
  subjectName: string;
  assessmentsCompleted: number;
  averageScore: number;
  submissionsCompleted: number;
  recentAssessments: {
    assessmentName: string;
    score: number;
    total: number;
    date: string;
  }[];
  recentSubmissions: {
    title: string;
    score: number;
    date: string;
  }[];
}
