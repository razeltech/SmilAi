import React, { useState, useEffect } from 'react';
import { 
  Layers, Plus, BookOpen, Users, Award, CheckCircle, PlusCircle, AlertCircle, 
  Trash2, Shield, Settings, Sliders, Book, RefreshCw, BarChart2, Check, UserPlus,
  Search, ChevronDown, Bookmark, School, CheckSquare, Zap
} from 'lucide-react';
import { GradeBand, Subject, User, ProfileApproval } from '../../types';

interface AdminDashboardProps {
  user: User;
  onRefreshSubjects: () => void;
  onRefreshOrgSettings?: () => void;
}

interface SelectOption {
  id: string;
  name: string;
  detail?: string;
}

// Reusable Search-enabled Premium Custom Dropdown Component
function CustomSelect({
  label,
  options,
  value,
  onChange,
  placeholder = "Select an option",
  icon: IconComponent
}: {
  label: string;
  options: SelectOption[];
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  icon?: React.ComponentType<{ className?: string }>;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  
  const selectedOption = options.find(o => o.id === value);
  const filteredOptions = options.filter(o => 
    o.name.toLowerCase().includes(search.toLowerCase()) || 
    (o.detail && o.detail.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="relative">
      <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
        {label}
      </label>
      
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2.5 bg-slate-50 hover:bg-white border border-slate-200 hover:border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all text-left text-sm text-slate-700 shadow-sm"
      >
        <span className="flex items-center gap-2 truncate">
          {IconComponent && <IconComponent className="h-4 w-4 text-slate-400 shrink-0" />}
          {selectedOption ? (
            <span className="truncate">
              <span className="font-semibold text-slate-800">{selectedOption.name}</span>
              {selectedOption.detail && (
                <span className="text-[10px] text-slate-400 ml-1.5 bg-slate-100 px-1.5 py-0.5 rounded font-mono">
                  {selectedOption.detail}
                </span>
              )}
            </span>
          ) : (
            <span className="text-slate-400">{placeholder}</span>
          )}
        </span>
        <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform duration-200 shrink-0 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          
          <div className="absolute left-0 right-0 mt-1.5 bg-white border border-slate-200 rounded-xl shadow-lg z-20 overflow-hidden animate-fade-in max-h-60 flex flex-col">
            <div className="p-2 border-b border-slate-100 shrink-0 flex items-center bg-slate-50/50">
              <Search className="h-3.5 w-3.5 text-slate-400 mr-2 shrink-0" />
              <input
                type="text"
                placeholder="Type to filter..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-transparent border-none text-xs focus:outline-none focus:ring-0 text-slate-700 p-0 placeholder:text-slate-400"
                autoFocus
              />
            </div>
            
            <div className="overflow-y-auto py-1 divide-y divide-slate-50 max-h-44">
              {filteredOptions.length === 0 ? (
                <div className="px-3 py-3 text-xs text-slate-400 text-center italic">No results matched your search</div>
              ) : (
                filteredOptions.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => {
                      onChange(opt.id);
                      setIsOpen(false);
                      setSearch('');
                    }}
                    className={`w-full text-left px-3 py-2 text-xs transition-colors flex items-center justify-between hover:bg-teal-50/60 ${opt.id === value ? 'bg-teal-50 text-teal-800 font-bold' : 'text-slate-600'}`}
                  >
                    <span className="truncate mr-2">{opt.name}</span>
                    {opt.detail && (
                      <span className="text-[9px] text-slate-400 font-mono shrink-0 bg-slate-100/80 px-1 py-0.2 rounded">
                        {opt.detail}
                      </span>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function AdminDashboard({ user, onRefreshSubjects, onRefreshOrgSettings }: AdminDashboardProps) {
  const [gradeBands, setGradeBands] = useState<GradeBand[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [teachers, setTeachers] = useState<User[]>([]);
  const [students, setStudents] = useState<User[]>([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'curriculum' | 'roster' | 'rag' | 'profile_settings'>('curriculum');

  // School profile state
  const [schoolCategory, setSchoolCategory] = useState<'govt' | 'pvt'>('govt');

  // Org Settings State
  const [orgName, setOrgName] = useState('');
  const [orgBoardType, setOrgBoardType] = useState<'ap_govt_ssc' | 'private_ssc' | 'private_cbse'>('ap_govt_ssc');
  const [orgSchoolCode, setOrgSchoolCode] = useState('');
  const [orgContactEmail, setOrgContactEmail] = useState('');
  const [orgPhone, setOrgPhone] = useState('');
  const [orgAddress, setOrgAddress] = useState('');
  const [orgMedium, setOrgMedium] = useState('');

  // Admin Profile State
  const [adminName, setAdminName] = useState('');
  const [adminPhone, setAdminPhone] = useState('');
  const [adminBio, setAdminBio] = useState('');
  const [adminDesignation, setAdminDesignation] = useState('');

  // Approvals list
  const [approvals, setApprovals] = useState<ProfileApproval[]>([]);
  const [adminDecisionNotes, setAdminDecisionNotes] = useState<Record<string, string>>({});

  // AP preset active template tab
  const [presetTab, setPresetTab] = useState<'ssc' | 'cbse'>('ssc');

  // Form states
  const [newBandName, setNewBandName] = useState('');
  const [newSubjectName, setNewSubjectName] = useState('');
  const [selectedBandId, setSelectedBandId] = useState('');
  const [selectedTeacherId, setSelectedTeacherId] = useState('');

  // User generation states
  const [newUserName, setNewUserName] = useState('');
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('password');
  const [newUserRole, setNewUserRole] = useState<'teacher' | 'student'>('student');

  // Enrollment states
  const [enrollStudentId, setEnrollStudentId] = useState('');
  const [enrollSubjectId, setEnrollSubjectId] = useState('');

  // State-based delete confirmation instead of native window.confirm
  const [deleteConfirm, setDeleteConfirm] = useState<{ type: 'subject' | 'user'; id: string; name: string } | null>(null);

  // Standard Andhra Pradesh Predefined Subjects Library
  const AP_SSC_GOVT_SUBJECTS = [
    { code: 'AP-SSC-101', name: 'First Language Telugu (తెలుగు ప్రథమ భాష)', group: 'Languages' },
    { code: 'AP-SSC-102', name: 'Second Language Hindi (ద్వితీయ భాష హిందీ)', group: 'Languages' },
    { code: 'AP-SSC-103', name: 'Third Language English (ఆంగ్ల భాష)', group: 'Languages' },
    { code: 'AP-SSC-104', name: 'Mathematics (గణితము)', group: 'Core' },
    { code: 'AP-SSC-105', name: 'Physical Science (భౌతిక రసాయన శాస్త్రం)', group: 'Core Science' },
    { code: 'AP-SSC-106', name: 'Biological Science (జీవ శాస్త్రం)', group: 'Core Science' },
    { code: 'AP-SSC-107', name: 'Social Studies (సంఘిక శాస్త్రం)', group: 'Core' }
  ];

  const AP_SSC_PRIVATE_SUBJECTS = [
    { code: 'AP-PVT-101', name: 'First Language Telugu (Private SSC)', group: 'Languages' },
    { code: 'AP-PVT-102', name: 'Second Language Hindi (Private SSC)', group: 'Languages' },
    { code: 'AP-PVT-103', name: 'Third Language English (Private SSC)', group: 'Languages' },
    { code: 'AP-PVT-104', name: 'Mathematics (Private SSC)', group: 'Core' },
    { code: 'AP-PVT-105', name: 'Physical Science (Private SSC)', group: 'Core Science' },
    { code: 'AP-PVT-106', name: 'Biological Science (Private SSC)', group: 'Core Science' },
    { code: 'AP-PVT-107', name: 'Social Studies (Private SSC)', group: 'Core' }
  ];

  const AP_CBSE_PVT_SUBJECTS = [
    { code: 'AP-CBSE-184', name: 'English Language & Literature', group: 'Languages' },
    { code: 'AP-CBSE-007', name: 'Telugu Course A (తెలుగు)', group: 'Languages' },
    { code: 'AP-CBSE-085', name: 'Hindi Course B (हिन्दी)', group: 'Languages' },
    { code: 'AP-CBSE-041', name: 'Mathematics Standard', group: 'Core' },
    { code: 'AP-CBSE-086', name: 'Science (Physics/Chemistry/Biology)', group: 'Core Science' },
    { code: 'AP-CBSE-087', name: 'Social Science (Hist/Civ/Geog)', group: 'Core' },
    { code: 'AP-CBSE-402', name: 'Information Technology', group: 'Electives' }
  ];

  const fetchData = async () => {
    setLoading(true);
    try {
      // Get Grade Bands
      const bandRes = await fetch('/v1/grade-bands');
      const bandData = await bandRes.json();
      const sortedBands = bandRes.ok ? [...bandData].sort((a: any, b: any) => {
        const isATenth = /10|tenth/i.test(a.name);
        const isBTenth = /10|tenth/i.test(b.name);
        if (isATenth && !isBTenth) return -1;
        if (!isATenth && isBTenth) return 1;
        return a.name.localeCompare(b.name);
      }) : [];
      setGradeBands(sortedBands);

      if (sortedBands.length > 0 && !selectedBandId) {
        setSelectedBandId(sortedBands[0].id);
      }

      // Get Subjects
      const subjRes = await fetch('/v1/subjects');
      const subjData = await subjRes.json();
      setSubjects(subjRes.ok ? subjData : []);

      // Fetch all users
      const usersRes = await fetch('/v1/users');
      const usersData: any[] = await usersRes.json();
      
      if (usersRes.ok) {
        setTeachers(usersData.filter(u => u.role === 'teacher'));
        setStudents(usersData.filter(u => u.role === 'student'));
      } else {
        // Fallback simulated list if route fails
        setTeachers([
          { id: 'user-teacher', name: 'Mr. Sharma', email: 'sharma@school.org', role: 'teacher', orgId: user.orgId }
        ]);
        setStudents([
          { id: 'user-student', name: 'Rahul Kumar', email: 'student@school.org', role: 'student', orgId: user.orgId }
        ]);
      }
    } catch (err: any) {
      console.error(err);
      setError('Could not fetch dashboard directories.');
    } finally {
      setLoading(false);
    }
  };

  const fetchOrgAndProfile = async () => {
    try {
      const orgRes = await fetch('/v1/org-settings');
      if (orgRes.ok) {
        const orgData = await orgRes.json();
        setOrgName(orgData.name || '');
        setOrgBoardType(orgData.boardType || 'ap_govt_ssc');
        setOrgSchoolCode(orgData.schoolCode || '');
        setOrgContactEmail(orgData.contactEmail || '');
        setOrgPhone(orgData.phone || '');
        setOrgAddress(orgData.address || '');
        setOrgMedium(orgData.mediumOfInstruction || '');
        if (orgData.boardType === 'ap_govt_ssc') {
          setSchoolCategory('govt');
        } else {
          setSchoolCategory('pvt');
        }
      }

      const adminRes = await fetch(`/v1/users/${user.id}/profile`);
      if (adminRes.ok) {
        const adminData = await adminRes.json();
        setAdminName(adminData.name || '');
        setAdminPhone(adminData.phone || '');
        setAdminBio(adminData.bio || '');
        setAdminDesignation(adminData.designation || '');
      }

      const approvalsRes = await fetch('/v1/admin/profile-approvals');
      if (approvalsRes.ok) {
        const approvalsData = await approvalsRes.json();
        setApprovals(approvalsData);
      }
    } catch (err) {
      console.error('Failed to load profile settings and approvals:', err);
    }
  };

  useEffect(() => {
    fetchData();
    fetchOrgAndProfile();
  }, []);

  const handleSaveOrgSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      const res = await fetch('/v1/org-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: orgName,
          boardType: orgBoardType,
          schoolCode: orgSchoolCode,
          contactEmail: orgContactEmail,
          phone: orgPhone,
          address: orgAddress,
          mediumOfInstruction: orgMedium
        })
      });
      if (!res.ok) throw new Error('Failed to update organization settings');
      const data = await res.json();
      setSuccess('Organization profile and board type updated successfully!');
      if (data.boardType === 'ap_govt_ssc') {
        setSchoolCategory('govt');
      } else {
        setSchoolCategory('pvt');
      }
      onRefreshOrgSettings?.();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAdminProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      const res = await fetch(`/v1/users/${user.id}/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: adminName,
          phone: adminPhone,
          bio: adminBio,
          designation: adminDesignation
        })
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Failed to update administrative profile');
      }
      setSuccess('Administrative staff profile updated successfully!');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDecideApproval = async (approvalId: string, decision: 'approved' | 'rejected') => {
    setError('');
    setSuccess('');
    const notes = adminDecisionNotes[approvalId] || '';
    setLoading(true);
    try {
      const res = await fetch(`/v1/admin/profile-approvals/${approvalId}/decide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision,
          adminNotes: notes
        })
      });
      if (!res.ok) throw new Error('Failed to submit approval decision');
      setSuccess(`Teacher profile change request has been ${decision}!`);
      
      // Clear decision notes for this ID
      setAdminDecisionNotes(prev => {
        const copied = { ...prev };
        delete copied[approvalId];
        return copied;
      });

      // Refresh data and approvals
      fetchData();
      fetchOrgAndProfile();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddGradeBand = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (!newBandName.trim()) return;

    try {
      const res = await fetch('/v1/grade-bands', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newBandName, orgId: user.orgId }),
      });
      if (!res.ok) throw new Error('Failed to create Grade Band');
      
      setSuccess(`Grade Band "${newBandName}" created successfully!`);
      setNewBandName('');
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (!newSubjectName.trim() || !selectedBandId || !selectedTeacherId) {
      setError('Please fill in all subject fields');
      return;
    }

    try {
      const res = await fetch('/v1/subjects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newSubjectName,
          gradeBandId: selectedBandId,
          teacherId: selectedTeacherId,
          orgId: user.orgId
        }),
      });
      if (!res.ok) throw new Error('Failed to create Subject');

      setSuccess(`Subject "${newSubjectName}" created successfully and teacher assigned!`);
      setNewSubjectName('');
      fetchData();
      onRefreshSubjects(); // Trigger parent refresh
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (!newUserName.trim() || !newUserEmail.trim()) {
      setError('Please provide user name and email');
      return;
    }

    try {
      const res = await fetch('/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newUserName,
          email: newUserEmail,
          password: newUserPassword,
          role: newUserRole,
          orgId: user.orgId
        }),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.error || 'Failed to register new user');
      }

      setSuccess(`New ${newUserRole} "${newUserName}" registered successfully!`);
      setNewUserName('');
      setNewUserEmail('');
      setNewUserPassword('password');
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteUser = (userId: string, userName: string) => {
    setDeleteConfirm({ type: 'user', id: userId, name: userName });
  };

  const handleDeleteSubject = (subjId: string, subjName: string) => {
    setDeleteConfirm({ type: 'subject', id: subjId, name: subjName });
  };

  const handleConfirmDelete = async () => {
    if (!deleteConfirm) return;
    const { type, id, name } = deleteConfirm;
    setDeleteConfirm(null);
    setError('');
    setSuccess('');

    try {
      if (type === 'subject') {
        const res = await fetch(`/v1/subjects/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete subject');
        setSuccess(`Subject "${name}" deleted successfully.`);
        fetchData();
        onRefreshSubjects?.();
      } else {
        const res = await fetch(`/v1/users/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete user');
        setSuccess(`User "${name}" deleted successfully.`);
        fetchData();
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleEnrollStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (!enrollStudentId || !enrollSubjectId) {
      setError('Please select both a student and a subject for enrollment');
      return;
    }

    try {
      const res = await fetch(`/v1/subjects/${enrollSubjectId}/enroll`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: enrollStudentId }),
      });
      if (!res.ok) throw new Error('Failed to enroll student');

      const s = students.find(x => x.id === enrollStudentId);
      const sub = subjects.find(x => x.id === enrollSubjectId);
      setSuccess(`Successfully enrolled student "${s?.name || 'Student'}" in "${sub?.name || 'Subject'}"!`);
      setEnrollStudentId('');
      setEnrollSubjectId('');
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Extract Andhra Pradesh Standard subject codes like [AP-SSC-104] or [AP-CBSE-086] from subject names
  const parseSubjectCode = (fullName: string) => {
    const match = fullName.match(/^\[(.*?)\]\s*(.*)$/);
    if (match) {
      return { code: match[1], name: match[2] };
    }
    return { code: null, name: fullName };
  };

  // Click handler to load template details into form fields
  const applyPresetTemplate = (preset: { code: string; name: string }) => {
    setNewSubjectName(`[${preset.code}] ${preset.name}`);
    
    // Auto match Tenth Class grade band if loaded
    const tenthBand = gradeBands.find(gb => 
      gb.name.toLowerCase().includes('10th') || 
      gb.name.toLowerCase().includes('ssc') || 
      gb.name.toLowerCase().includes('class-10')
    );
    if (tenthBand) {
      setSelectedBandId(tenthBand.id);
    } else if (gradeBands.length > 0) {
      setSelectedBandId(gradeBands[0].id);
    }

    setSuccess(`Loaded ${preset.code} standard template. Assigned code and subject name!`);
    setTimeout(() => setSuccess(''), 3000);
  };

  const handleQuickToggleCategory = async (category: 'govt' | 'pvt') => {
    const targetBoard = category === 'govt' ? 'ap_govt_ssc' : 'private_cbse';
    const targetName = category === 'govt' ? 'Andhra Pradesh Government High School' : 'Prerana Private Corporate Academy';
    setSchoolCategory(category);
    setOrgBoardType(targetBoard);
    setOrgName(targetName);
    
    try {
      await fetch('/v1/org-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: targetName,
          boardType: targetBoard
        })
      });
      onRefreshOrgSettings?.();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 font-sans">
      {/* Upper Header Profile Controller */}
      <div className="bg-slate-50 rounded-2xl p-6 md:p-8 text-slate-800 mb-8 border border-slate-200 shadow-sm relative overflow-hidden">
        <div className="absolute right-0 top-0 opacity-20 transform translate-x-12 -translate-y-12 select-none pointer-events-none">
          <Shield className="h-64 w-64 text-slate-200" />
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200/60 uppercase tracking-wider">
                System Administrator
              </span>
              <span className="text-xs text-slate-300">|</span>
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <Sliders className="h-3 w-3 text-slate-400" /> AP Academic Control Portals
              </span>
            </div>
            <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              {orgName || (schoolCategory === 'govt' 
                ? 'Andhra Pradesh Govt High School Board' 
                : 'Prerana Private Corporate Academy')}
            </h2>
            <p className="text-slate-500 text-sm mt-1 max-w-2xl font-normal leading-relaxed">
              Configure curriculum structural bounds, assign verified regional educators, manage student registries, and monitor high-performance pre-clustered RAG indices.
            </p>
          </div>

          <div className="flex items-center gap-2 px-4 py-2 bg-slate-100/80 rounded-xl border border-slate-200/50 select-none shrink-0 self-start md:self-center shadow-xs">
            <span className="h-2 w-2 rounded-full bg-teal-500 animate-pulse"></span>
            <span className="text-[10px] font-extrabold text-slate-600 uppercase tracking-wider">
              {orgBoardType === 'ap_govt_ssc' ? 'AP Govt (SSC)' : 
               orgBoardType === 'private_ssc' ? 'Private (SSC)' : 'Private (CBSE)'}
            </span>
          </div>
        </div>
      </div>

      {/* Success / Error Notification banners */}
      {success && (
        <div className="mb-6 bg-teal-50 border border-teal-200 text-teal-900 p-4 rounded-xl text-sm flex items-center gap-2.5 shadow-sm animate-fade-in">
          <CheckCircle className="h-5 w-5 text-teal-600 shrink-0" />
          <span className="font-medium">{success}</span>
        </div>
      )}

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-900 p-4 rounded-xl text-sm flex items-center gap-2.5 shadow-sm">
          <AlertCircle className="h-5 w-5 text-red-600 shrink-0" />
          <span className="font-medium">{error}</span>
        </div>
      )}

      {/* Numerical Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4 transition-all hover:border-slate-300 hover:shadow-md">
          <div className="h-11 w-11 bg-teal-50 text-teal-600 rounded-xl flex items-center justify-center border border-teal-100">
            <Layers className="h-5 w-5" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900">{gradeBands.length}</div>
            <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Class Grade Bands</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4 transition-all hover:border-slate-300 hover:shadow-md">
          <div className="h-11 w-11 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center border border-indigo-100">
            <BookOpen className="h-5 w-5" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900">{subjects.length}</div>
            <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Syllabus Subjects</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4 transition-all hover:border-slate-300 hover:shadow-md">
          <div className="h-11 w-11 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center border border-amber-100">
            <Users className="h-5 w-5" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900">{teachers.length}</div>
            <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Assigned Educators</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4 transition-all hover:border-slate-300 hover:shadow-md">
          <div className="h-11 w-11 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center border border-emerald-100">
            <Award className="h-5 w-5" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900">{students.length}</div>
            <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Registered Pupils</div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-slate-200 mb-8 gap-2">
        <button
          onClick={() => setActiveTab('curriculum')}
          className={`pb-3 px-4 font-semibold text-sm transition-all border-b-2 relative -mb-[2px] ${
            activeTab === 'curriculum'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-400 hover:text-slate-600'
          }`}
        >
          Curriculum & Subjects
        </button>
        <button
          onClick={() => setActiveTab('roster')}
          className={`pb-3 px-4 font-semibold text-sm transition-all border-b-2 relative -mb-[2px] ${
            activeTab === 'roster'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-400 hover:text-slate-600'
          }`}
        >
          Staff & Student Roster
        </button>
        <button
          onClick={() => setActiveTab('rag')}
          className={`pb-3 px-4 font-semibold text-sm transition-all border-b-2 relative -mb-[2px] ${
            activeTab === 'rag'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-400 hover:text-slate-600'
          }`}
        >
          Pre-Clustered Ingestion Metrics
        </button>
        <button
          onClick={() => setActiveTab('profile_settings')}
          className={`pb-3 px-4 font-semibold text-sm transition-all border-b-2 relative -mb-[2px] ${
            activeTab === 'profile_settings'
              ? 'border-teal-600 text-teal-600'
              : 'border-transparent text-slate-400 hover:text-slate-600'
          }`}
        >
          Settings & Approvals
        </button>
      </div>

      {/* Tab content */}
      <div className="animate-fade-in">
        {activeTab === 'curriculum' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column forms */}
            <div className="space-y-6 lg:col-span-1">
              
              {/* Predefined AP School Subject Template Fast-Filler */}
              <div className="bg-gradient-to-br from-slate-50 to-teal-50/20 p-5 rounded-2xl border border-teal-100 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <Bookmark className="h-4 w-4 text-teal-600" />
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    {orgBoardType === 'ap_govt_ssc' ? 'AP Govt (SSC)' : 
                     orgBoardType === 'private_ssc' ? 'AP Private (SSC)' : 'Private (CBSE)'} Syllabus Templates
                  </h3>
                </div>
                <p className="text-xs text-slate-500 mb-4 leading-relaxed">
                  Quick-load standard syllabus subjects with pre-assigned codes matching your organization's board type setting.
                </p>

                {/* Templates List */}
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1" id="template-library-container">
                  {orgBoardType === 'ap_govt_ssc' && (
                    AP_SSC_GOVT_SUBJECTS.map((item) => (
                      <button
                        key={item.code}
                        type="button"
                        onClick={() => applyPresetTemplate(item)}
                        className="w-full text-left p-2 bg-white hover:bg-teal-50/50 border border-slate-150 rounded-lg text-xs transition-colors flex items-center justify-between group cursor-pointer"
                        id={`template-btn-${item.code}`}
                      >
                        <div className="truncate mr-2">
                          <div className="font-semibold text-slate-700 group-hover:text-teal-900 truncate">
                            {item.name}
                          </div>
                          <span className="text-[9px] text-slate-400 uppercase tracking-wider">{item.group}</span>
                        </div>
                        <span className="font-mono text-[9px] bg-teal-50 text-teal-700 border border-teal-100 px-1.5 py-0.5 rounded font-bold shrink-0">
                          {item.code}
                        </span>
                      </button>
                    ))
                  )}

                  {orgBoardType === 'private_ssc' && (
                    AP_SSC_PRIVATE_SUBJECTS.map((item) => (
                      <button
                        key={item.code}
                        type="button"
                        onClick={() => applyPresetTemplate(item)}
                        className="w-full text-left p-2 bg-white hover:bg-teal-50/50 border border-slate-150 rounded-lg text-xs transition-colors flex items-center justify-between group cursor-pointer"
                        id={`template-btn-${item.code}`}
                      >
                        <div className="truncate mr-2">
                          <div className="font-semibold text-slate-700 group-hover:text-teal-900 truncate">
                            {item.name}
                          </div>
                          <span className="text-[9px] text-slate-400 uppercase tracking-wider">{item.group}</span>
                        </div>
                        <span className="font-mono text-[9px] bg-teal-50 text-teal-700 border border-teal-100 px-1.5 py-0.5 rounded font-bold shrink-0">
                          {item.code}
                        </span>
                      </button>
                    ))
                  )}

                  {orgBoardType === 'private_cbse' && (
                    AP_CBSE_PVT_SUBJECTS.map((item) => (
                      <button
                        key={item.code}
                        type="button"
                        onClick={() => applyPresetTemplate(item)}
                        className="w-full text-left p-2 bg-white hover:bg-indigo-50/50 border border-slate-150 rounded-lg text-xs transition-colors flex items-center justify-between group cursor-pointer"
                        id={`template-btn-${item.code}`}
                      >
                        <div className="truncate mr-2">
                          <div className="font-semibold text-slate-700 group-hover:text-indigo-900 truncate">
                            {item.name}
                          </div>
                          <span className="text-[9px] text-slate-400 uppercase tracking-wider">{item.group}</span>
                        </div>
                        <span className="font-mono text-[9px] bg-indigo-50 text-indigo-700 border border-indigo-100 px-1.5 py-0.5 rounded font-bold shrink-0">
                          {item.code}
                        </span>
                      </button>
                    ))
                  )}
                </div>
              </div>

              {/* Create Subject */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <PlusCircle className="h-4 w-4 text-indigo-600" /> Configure Academic Subject
                </h3>
                <form onSubmit={handleAddSubject} className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                      Subject Title
                    </label>
                    <input
                      type="text"
                      required
                      value={newSubjectName}
                      onChange={(e) => setNewSubjectName(e.target.value)}
                      placeholder="e.g. Physical Science (భౌతిక శాస్త్రం) or select template"
                      className="block w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 text-sm placeholder:text-slate-400"
                      id="admin-new-subj-input"
                    />
                  </div>

                  {/* Class dropdown utilizing beautiful custom search select */}
                  <CustomSelect
                    label="Class/Grade Band"
                    placeholder="Select Academic Class"
                    options={gradeBands.map(gb => ({ id: gb.id, name: gb.name }))}
                    value={selectedBandId}
                    onChange={(val) => setSelectedBandId(val)}
                    icon={Layers}
                  />

                  {/* Teacher dropdown utilizing beautiful custom search select */}
                  <CustomSelect
                    label="Assign Owning Educator"
                    placeholder="Select School Teacher"
                    options={teachers.map(t => ({ id: t.id, name: t.name, detail: t.email }))}
                    value={selectedTeacherId}
                    onChange={(val) => setSelectedTeacherId(val)}
                    icon={Users}
                  />

                  <button
                    type="submit"
                    className="w-full flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs py-2.5 rounded-xl cursor-pointer transition-colors"
                  >
                    <Plus className="h-4 w-4" /> Create & Setup Subject
                  </button>
                </form>
              </div>

              {/* Create Grade Band */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <PlusCircle className="h-4 w-4 text-teal-600" /> Establish Grade Band
                </h3>
                <form onSubmit={handleAddGradeBand} className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Class Range / Band Name</label>
                    <input
                      type="text"
                      required
                      value={newBandName}
                      onChange={(e) => setNewBandName(e.target.value)}
                      placeholder="e.g. 10th Class (SSC)"
                      className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm bg-slate-50 placeholder:text-slate-400"
                      id="admin-new-band-input"
                    />
                    <p className="text-[11px] text-slate-400 mt-1">Nursery to Intermediate (12th Class) are suggested bounds.</p>
                  </div>
                  <button
                    type="submit"
                    className="w-full flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs py-2.5 rounded-xl cursor-pointer transition-colors"
                  >
                    <Plus className="h-4 w-4" /> Add Grade Band
                  </button>
                </form>
              </div>
            </div>

            {/* Right Column Subjects Table */}
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                      <Book className="h-4 w-4 text-slate-600" /> In-Place Curriculum Subjects ({subjects.length})
                    </h3>
                    <p className="text-xs text-slate-400">Classrooms configured for virtual teacher assistance.</p>
                  </div>
                  <button 
                    onClick={fetchData} 
                    className="p-1.5 hover:bg-slate-50 border border-slate-200 rounded-lg text-slate-400 hover:text-slate-600"
                    title="Refresh data"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </button>
                </div>

                <div className="overflow-x-auto">
                  {subjects.length === 0 ? (
                    <div className="text-center py-12 text-slate-400 text-sm">
                      No subjects configured. Set up a Grade Band and Subject to get started.
                    </div>
                  ) : (
                    <table className="min-w-full divide-y divide-slate-100">
                      <thead>
                        <tr className="bg-slate-50/50">
                          <th className="px-4 py-3 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider">Subject Code & Name</th>
                          <th className="px-4 py-3 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider">Grade/Class</th>
                          <th className="px-4 py-3 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider">Assigned Teacher</th>
                          <th className="px-4 py-3 text-center text-[10px] font-bold text-slate-400 uppercase tracking-wider">Brain Status</th>
                          <th className="px-4 py-3 text-right text-[10px] font-bold text-slate-400 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {subjects.map((subj) => {
                          const { code, name } = parseSubjectCode(subj.name);
                          const isCBSE = code?.includes('CBSE');
                          const isSSC = code?.includes('SSC');

                          return (
                            <tr key={subj.id} className="hover:bg-slate-50/50 transition-colors">
                              <td className="px-4 py-3.5">
                                <div className="flex items-center gap-2 flex-wrap">
                                  {code ? (
                                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-extrabold font-mono border ${
                                      isSSC 
                                        ? 'bg-teal-50 text-teal-700 border-teal-200/60' 
                                        : isCBSE 
                                          ? 'bg-indigo-50 text-indigo-700 border-indigo-200/60' 
                                          : 'bg-amber-50 text-amber-700 border-amber-200/60'
                                    }`}>
                                      {code}
                                    </span>
                                  ) : (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-slate-100 text-slate-500 border border-slate-200/60">
                                      CUSTOM
                                    </span>
                                  )}
                                  <span className="font-semibold text-slate-800 text-sm">{name}</span>
                                </div>
                                <div className="text-[10px] text-slate-400 font-mono mt-0.5">Database ID: {subj.id}</div>
                              </td>
                              <td className="px-4 py-3.5 whitespace-nowrap text-sm text-slate-500">
                                <span className="inline-block px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-medium text-xs">
                                  {subj.gradeBandName || 'Class 10'}
                                </span>
                              </td>
                              <td className="px-4 py-3.5 whitespace-nowrap text-sm text-slate-600">
                                {subj.teacherName || 'Unassigned Educator'}
                              </td>
                              <td className="px-4 py-3.5 whitespace-nowrap text-center">
                                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-100">
                                  SmilAI Active
                                </span>
                              </td>
                              <td className="px-4 py-3.5 whitespace-nowrap text-right">
                                <button
                                  onClick={() => handleDeleteSubject(subj.id, subj.name)}
                                  className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                                  title="Delete Subject"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'roster' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Create Users and Enrollments forms */}
            <div className="space-y-6 lg:col-span-1">
              
              {/* Register User */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <UserPlus className="h-4 w-4 text-teal-600" /> Register Student / Staff
                </h3>
                <form onSubmit={handleAddUser} className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Account Role</label>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setNewUserRole('student')}
                        className={`flex-1 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                          newUserRole === 'student'
                            ? 'bg-teal-50 border-teal-200 text-teal-700 font-bold'
                            : 'border-slate-200 text-slate-500 hover:bg-slate-50'
                        }`}
                      >
                        Student Pupil
                      </button>
                      <button
                        type="button"
                        onClick={() => setNewUserRole('teacher')}
                        className={`flex-1 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                          newUserRole === 'teacher'
                            ? 'bg-indigo-50 border-indigo-200 text-indigo-700 font-bold'
                            : 'border-slate-200 text-slate-500 hover:bg-slate-50'
                        }`}
                      >
                        Teacher Staff
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Full Name</label>
                    <input
                      type="text"
                      required
                      value={newUserName}
                      onChange={(e) => setNewUserName(e.target.value)}
                      placeholder="e.g. Sree Lekha"
                      className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm bg-slate-50 placeholder:text-slate-400"
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">School Email Address</label>
                    <input
                      type="email"
                      required
                      value={newUserEmail}
                      onChange={(e) => setNewUserEmail(e.target.value)}
                      placeholder="e.g. lekha@school.org"
                      className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm bg-slate-50 placeholder:text-slate-400"
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Temporary Password</label>
                    <input
                      type="text"
                      required
                      value={newUserPassword}
                      onChange={(e) => setNewUserPassword(e.target.value)}
                      placeholder="password"
                      className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm bg-slate-50 placeholder:text-slate-400"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs py-2.5 rounded-xl cursor-pointer transition-colors"
                  >
                    <Plus className="h-4 w-4" /> Add Register Account
                  </button>
                </form>
              </div>

              {/* Quick Enroll Student to Subject */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-emerald-600" /> Quick Pupil Enrollment
                </h3>
                <form onSubmit={handleEnrollStudent} className="space-y-4">
                  {/* Student Custom Select */}
                  <CustomSelect
                    label="Choose Student"
                    placeholder="Select Student"
                    options={students.map(s => ({ id: s.id, name: s.name, detail: s.email }))}
                    value={enrollStudentId}
                    onChange={(val) => setEnrollStudentId(val)}
                    icon={Users}
                  />

                  {/* Subject Custom Select */}
                  <CustomSelect
                    label="Target Syllabus Subject"
                    placeholder="Select Subject"
                    options={subjects.map(sub => ({ id: sub.id, name: sub.name, detail: sub.gradeBandName }))}
                    value={enrollSubjectId}
                    onChange={(val) => setEnrollSubjectId(val)}
                    icon={BookOpen}
                  />

                  <button
                    type="submit"
                    className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs py-2.5 rounded-xl cursor-pointer transition-colors"
                  >
                    <Check className="h-4 w-4" /> Confirm Enrollment
                  </button>
                </form>
              </div>
            </div>

            {/* Right Column Users List */}
            <div className="lg:col-span-2 space-y-6">
              {/* Teachers Section */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Users className="h-4 w-4 text-amber-500" /> Regional School Staff & Educators ({teachers.length})
                </h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-100">
                    <thead>
                      <tr className="bg-slate-50/50">
                        <th className="px-4 py-3 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider">Staff Educator</th>
                        <th className="px-4 py-3 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider">Institutional Email</th>
                        <th className="px-4 py-3 text-right text-[10px] font-bold text-slate-400 uppercase tracking-wider">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {teachers.map((t) => (
                        <tr key={t.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-4 py-3 whitespace-nowrap font-semibold text-slate-800 text-sm">{t.name}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-500 font-mono">{t.email}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-right">
                            {t.email !== 'sharma@school.org' ? (
                              <button
                                onClick={() => handleDeleteUser(t.id, t.name)}
                                className="p-1 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-all"
                                title="Delete Teacher"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            ) : (
                              <span className="text-[10px] text-slate-400 font-medium italic">Seeded Root</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Students Section */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Users className="h-4 w-4 text-teal-500" /> Enrolled Pupils & Students ({students.length})
                </h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-100">
                    <thead>
                      <tr className="bg-slate-50/50">
                        <th className="px-4 py-3 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider">Student Name</th>
                        <th className="px-4 py-3 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider">Student Email</th>
                        <th className="px-4 py-3 text-right text-[10px] font-bold text-slate-400 uppercase tracking-wider">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {students.map((s) => (
                        <tr key={s.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-4 py-3 whitespace-nowrap font-semibold text-slate-800 text-sm">{s.name}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-500 font-mono">{s.email}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-right">
                            {s.email !== 'student@school.org' ? (
                              <button
                                onClick={() => handleDeleteUser(s.id, s.name)}
                                className="p-1 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-all"
                                title="Delete Student"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            ) : (
                              <span className="text-[10px] text-slate-400 font-medium italic">Seeded Root</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'rag' && (
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-8">
            <div>
              <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2 mb-1.5">
                <BarChart2 className="h-4 w-4 text-teal-600" /> High-Performance Pre-Clustered Ingestion Routing Plan
              </h3>
              <p className="text-xs text-slate-500">
                Performance indicators showing how SmilAI scales up to **10,000+ textbooks (50,000+ pages)** instantly utilizing metadata pre-filtering without slow scans.
              </p>
            </div>

            {/* Performance Metric Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200/80">
                <div className="text-2xl font-black text-slate-900">&lt; 4ms</div>
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mt-1">Metadata Hash Routing Latency</div>
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed font-light">
                  Bypasses linear scans. Prunes candidates from 10,000+ documents down to exactly 1 relevant match in O(1) time before embedding lookup.
                </p>
              </div>

              <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200/80">
                <div className="text-2xl font-black text-slate-900">99.4%</div>
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mt-1">Memory-Cache Hit Ratio</div>
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed font-light">
                  Common educational curriculum pages and unit chapters are cached in-memory, eliminating database query bottlenecks entirely.
                </p>
              </div>

              <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200/80">
                <div className="text-2xl font-black text-slate-900">1:5 Ratio</div>
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mt-1">Hierarchical Chunk Optimization</div>
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed font-light">
                  Queries occur against ultra-fast micro child chunks (400 chars) while LLM receives full grounded contextual parent chapters (2000 chars).
                </p>
              </div>
            </div>

            {/* Ingestion Pipeline Visualization Grid */}
            <div className="border border-slate-200 rounded-2xl p-6 bg-slate-50/50">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-4">Active Pre-Routing Channels & Medium Indexes</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200/60 shadow-sm">
                  <div className="text-xs font-bold text-teal-600 mb-1 flex items-center justify-between">
                    <span>Nursery - UKG</span>
                    <span className="text-[10px] font-mono font-bold bg-teal-50 px-1.5 py-0.5 rounded text-teal-700">Pre-Primary</span>
                  </div>
                  <div className="text-[11px] text-slate-600 space-y-1.5 mt-2 font-light">
                    <p>• Mediums: English / Telugu</p>
                    <p>• Visual Cards: Ingestion active</p>
                    <p>• Index Partition: <code className="bg-slate-100 px-1 rounded text-[10px]">p_pprimary</code></p>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200/60 shadow-sm">
                  <div className="text-xs font-bold text-indigo-600 mb-1 flex items-center justify-between">
                    <span>1st - 5th Class</span>
                    <span className="text-[10px] font-mono font-bold bg-indigo-50 px-1.5 py-0.5 rounded text-indigo-700">Primary</span>
                  </div>
                  <div className="text-[11px] text-slate-600 space-y-1.5 mt-2 font-light">
                    <p>• Mediums: Telugu / Eng / Semi</p>
                    <p>• Interactive Maths & Moral stories</p>
                    <p>• Index Partition: <code className="bg-slate-100 px-1 rounded text-[10px]">p_primary</code></p>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200/60 shadow-sm">
                  <div className="text-xs font-bold text-amber-600 mb-1 flex items-center justify-between">
                    <span>6th - 10th Class</span>
                    <span className="text-[10px] font-mono font-bold bg-amber-50 px-1.5 py-0.5 rounded text-amber-700">High School</span>
                  </div>
                  <div className="text-[11px] text-slate-600 space-y-1.5 mt-2 font-light">
                    <p>• Mediums: State SSC Board</p>
                    <p>• Physics, biology, maths, social</p>
                    <p>• Index Partition: <code className="bg-slate-100 px-1 rounded text-[10px]">p_highschool</code></p>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200/60 shadow-sm">
                  <div className="text-xs font-bold text-emerald-600 mb-1 flex items-center justify-between">
                    <span>11th - 12th Class</span>
                    <span className="text-[10px] font-mono font-bold bg-emerald-50 px-1.5 py-0.5 rounded text-emerald-700">Intermediate</span>
                  </div>
                  <div className="text-[11px] text-slate-600 space-y-1.5 mt-2 font-light">
                    <p>• M.Bi.C / M.P.C / H.E.C options</p>
                    <p>• Advanced coding, sciences</p>
                    <p>• Index Partition: <code className="bg-slate-100 px-1 rounded text-[10px]">p_intermediate</code></p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'profile_settings' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Column: Organization and Admin Settings (7 cols) */}
            <div className="lg:col-span-7 space-y-8">
              {/* Organization Profile and Board Affiliation Form */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                <div className="flex items-center gap-2.5 mb-6 pb-4 border-b border-slate-100">
                  <div className="h-9 w-9 rounded-lg bg-teal-50 border border-teal-100 flex items-center justify-center">
                    <School className="h-5 w-5 text-teal-600" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">Organization Settings</h3>
                    <p className="text-[11px] text-slate-400 mt-0.5">Configure school identity and board affiliations</p>
                  </div>
                </div>

                <form onSubmit={handleSaveOrgSettings} className="space-y-5" id="org-settings-form">
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">School / Institution Name</label>
                    <input
                      type="text"
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value)}
                      placeholder="e.g. Andhra Pradesh Government High School"
                      className="w-full text-sm text-slate-800 bg-slate-50 border border-slate-200 focus:bg-white rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                      required
                    />
                  </div>

                  {/* Segmented Board Selector Cards (as requested: select ap govt ssc or privte ssc or private cbse) */}
                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2.5">
                      Board Affiliation / Category
                    </label>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {/* Option 1: AP Govt SSC */}
                      <label 
                        className={`flex flex-col p-4 rounded-xl border cursor-pointer transition-all ${
                          orgBoardType === 'ap_govt_ssc' 
                            ? 'border-teal-500 bg-teal-50/10 shadow-sm' 
                            : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                        id="board-type-ap-govt-label"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-800">AP Govt SSC</span>
                          <input
                            type="radio"
                            name="boardType"
                            value="ap_govt_ssc"
                            checked={orgBoardType === 'ap_govt_ssc'}
                            onChange={() => setOrgBoardType('ap_govt_ssc')}
                            className="text-teal-600 focus:ring-teal-500"
                          />
                        </div>
                        <span className="text-[10px] text-slate-400 mt-2 leading-relaxed">
                          Andhra Pradesh State Syllabus Board. Governed by AP Dept of School Education.
                        </span>
                      </label>

                      {/* Option 2: Private SSC */}
                      <label 
                        className={`flex flex-col p-4 rounded-xl border cursor-pointer transition-all ${
                          orgBoardType === 'private_ssc' 
                            ? 'border-teal-500 bg-teal-50/10 shadow-sm' 
                            : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                        id="board-type-private-ssc-label"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-800">Private SSC</span>
                          <input
                            type="radio"
                            name="boardType"
                            value="private_ssc"
                            checked={orgBoardType === 'private_ssc'}
                            onChange={() => setOrgBoardType('private_ssc')}
                            className="text-teal-600 focus:ring-teal-500"
                          />
                        </div>
                        <span className="text-[10px] text-slate-400 mt-2 leading-relaxed">
                          State Board Syllabus for recognized private aided & unaided schools.
                        </span>
                      </label>

                      {/* Option 3: Private CBSE */}
                      <label 
                        className={`flex flex-col p-4 rounded-xl border cursor-pointer transition-all ${
                          orgBoardType === 'private_cbse' 
                            ? 'border-teal-500 bg-teal-50/10 shadow-sm' 
                            : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                        id="board-type-private-cbse-label"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-800">Private CBSE</span>
                          <input
                            type="radio"
                            name="boardType"
                            value="private_cbse"
                            checked={orgBoardType === 'private_cbse'}
                            onChange={() => setOrgBoardType('private_cbse')}
                            className="text-teal-600 focus:ring-teal-500"
                          />
                        </div>
                        <span className="text-[10px] text-slate-400 mt-2 leading-relaxed">
                          Central Board of Secondary Education curriculum affiliated private schools.
                        </span>
                      </label>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">School Affiliation Code</label>
                      <input
                        type="text"
                        value={orgSchoolCode}
                        onChange={(e) => setOrgSchoolCode(e.target.value)}
                        placeholder="e.g. AP-GOVT-522001"
                        className="w-full text-sm text-slate-800 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Medium of Instruction</label>
                      <input
                        type="text"
                        value={orgMedium}
                        onChange={(e) => setOrgMedium(e.target.value)}
                        placeholder="e.g. Telugu, English, or bilingual"
                        className="w-full text-sm text-slate-800 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Contact Email</label>
                      <input
                        type="email"
                        value={orgContactEmail}
                        onChange={(e) => setOrgContactEmail(e.target.value)}
                        placeholder="admin@school.org"
                        className="w-full text-sm text-slate-800 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">School Contact Phone</label>
                      <input
                        type="text"
                        value={orgPhone}
                        onChange={(e) => setOrgPhone(e.target.value)}
                        placeholder="+91 866 254124"
                        className="w-full text-sm text-slate-800 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Physical Address</label>
                    <textarea
                      value={orgAddress}
                      onChange={(e) => setOrgAddress(e.target.value)}
                      placeholder="Enter school location details..."
                      rows={2}
                      className="w-full text-sm text-slate-800 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none"
                    />
                  </div>

                  <div className="flex justify-end pt-2">
                    <button
                      type="submit"
                      disabled={loading}
                      className="px-5 py-2.5 bg-teal-600 text-white font-bold text-xs uppercase tracking-wider rounded-xl hover:bg-teal-700 transition-colors shadow-sm disabled:opacity-50 cursor-pointer"
                      id="save-org-settings-btn"
                    >
                      {loading ? 'Saving...' : 'Save Organization Settings'}
                    </button>
                  </div>
                </form>
              </div>

              {/* Administrative Staff Profile Form */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
                <div className="flex items-center gap-2.5 mb-6 pb-4 border-b border-slate-100">
                  <div className="h-9 w-9 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center">
                    <Shield className="h-5 w-5 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">My Administrative Profile</h3>
                    <p className="text-[11px] text-slate-400 mt-0.5">Manage your personal credentials and designation</p>
                  </div>
                </div>

                <form onSubmit={handleSaveAdminProfile} className="space-y-5" id="admin-profile-form">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Staff Full Name</label>
                      <input
                        type="text"
                        value={adminName}
                        onChange={(e) => setAdminName(e.target.value)}
                        placeholder="Admin Principal"
                        className="w-full text-sm text-slate-800 bg-slate-50 border border-slate-200 focus:bg-white rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Official Designation</label>
                      <input
                        type="text"
                        value={adminDesignation}
                        onChange={(e) => setAdminDesignation(e.target.value)}
                        placeholder="e.g. Principal / Chief Administrator"
                        className="w-full text-sm text-slate-800 bg-slate-50 border border-slate-200 focus:bg-white rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Registered Email</label>
                      <input
                        type="email"
                        value={user.email}
                        className="w-full text-sm text-slate-400 bg-slate-100 border border-slate-100 rounded-xl px-4 py-2.5 cursor-not-allowed"
                        disabled
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Direct Contact Phone</label>
                      <input
                        type="text"
                        value={adminPhone}
                        onChange={(e) => setAdminPhone(e.target.value)}
                        placeholder="+91 98480 22338"
                        className="w-full text-sm text-slate-800 bg-slate-50 border border-slate-200 focus:bg-white rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Staff Profile Bio</label>
                    <textarea
                      value={adminBio}
                      onChange={(e) => setAdminBio(e.target.value)}
                      placeholder="Describe your role and background..."
                      rows={3}
                      className="w-full text-sm text-slate-800 bg-slate-50 border border-slate-200 focus:bg-white rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all resize-none"
                    />
                  </div>

                  <div className="flex justify-end pt-2">
                    <button
                      type="submit"
                      disabled={loading}
                      className="px-5 py-2.5 bg-indigo-600 text-white font-bold text-xs uppercase tracking-wider rounded-xl hover:bg-indigo-700 transition-colors shadow-sm disabled:opacity-50 cursor-pointer"
                      id="save-admin-profile-btn"
                    >
                      {loading ? 'Saving...' : 'Save Staff Profile'}
                    </button>
                  </div>
                </form>
              </div>
            </div>

            {/* Right Column: Pending Teacher Approvals (5 cols) */}
            <div className="lg:col-span-5 space-y-6">
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm h-full">
                <div className="flex items-center gap-2.5 mb-6 pb-4 border-b border-slate-100">
                  <div className="h-9 w-9 rounded-lg bg-amber-50 border border-amber-100 flex items-center justify-center">
                    <CheckSquare className="h-5 w-5 text-amber-600" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">Teacher Profile Approvals</h3>
                    <p className="text-[11px] text-slate-400 mt-0.5">Staff details updates waiting for principal authorization</p>
                  </div>
                </div>

                {/* Displaying Active Requests */}
                {approvals.filter(a => a.status === 'pending').length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
                    <div className="h-12 w-12 rounded-full bg-slate-50 border border-slate-100 flex items-center justify-center mb-4">
                      <CheckCircle className="h-6 w-6 text-slate-300" />
                    </div>
                    <h4 className="text-xs font-bold text-slate-700">All Profiles Synced</h4>
                    <p className="text-[11px] text-slate-400 mt-1 leading-relaxed max-w-xs">
                      No staff profile changes are pending approval at this time.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {approvals.filter(a => a.status === 'pending').map((request) => {
                      // Find original teacher if possible to compare fields
                      const origTeacher = teachers.find(t => t.id === request.userId) || {};
                      
                      const fieldsToCompare = [
                        { label: 'Name', key: 'name', current: origTeacher.name || '(unassigned)', requested: request.name },
                        { label: 'Phone', key: 'phone', current: origTeacher.phone || '(unassigned)', requested: request.phone },
                        { label: 'Specialization', key: 'specialization', current: origTeacher.specialization || '(unassigned)', requested: request.specialization },
                        { label: 'Qualification', key: 'qualification', current: origTeacher.qualification || '(unassigned)', requested: request.qualification },
                        { label: 'Biography', key: 'bio', current: origTeacher.bio || '(unassigned)', requested: request.bio }
                      ].filter(f => f.current !== f.requested); // Only show changed items

                      return (
                        <div key={request.id} className="p-4 rounded-xl border border-amber-100 bg-amber-50/10 space-y-4" id={`approval-item-${request.id}`}>
                          <div className="flex justify-between items-start">
                            <div>
                              <h4 className="text-xs font-bold text-slate-800">{request.teacherName}</h4>
                              <p className="text-[9px] text-slate-400 mt-0.5">Submitted: {new Date(request.createdAt).toLocaleDateString()} {new Date(request.createdAt).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
                            </div>
                            <span className="text-[9px] font-mono font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-100 uppercase tracking-wider">
                              Pending Review
                            </span>
                          </div>

                          {/* Profile comparison list */}
                          <div className="bg-white rounded-lg border border-slate-100 overflow-hidden divide-y divide-slate-50">
                            {fieldsToCompare.map((f, i) => (
                              <div key={i} className="p-2.5 text-[11px] space-y-1">
                                <span className="font-bold text-[9px] text-slate-400 uppercase tracking-wider block">{f.label}</span>
                                <div className="grid grid-cols-2 gap-2 text-slate-600 leading-normal">
                                  <div className="line-through text-slate-350 pr-2 border-r border-slate-50 truncate" title={f.current}>
                                    {f.current}
                                  </div>
                                  <div className="text-emerald-600 font-medium truncate" title={f.requested}>
                                    {f.requested}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>

                          {/* Action Forms */}
                          <div className="space-y-3">
                            <div>
                              <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Decision Comments / Notes</label>
                              <textarea
                                value={adminDecisionNotes[request.id] || ''}
                                onChange={(e) => setAdminDecisionNotes(prev => ({ ...prev, [request.id]: e.target.value }))}
                                placeholder="Provide optional remarks for staff feedback..."
                                rows={2}
                                className="w-full text-xs text-slate-800 bg-white border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
                              />
                            </div>

                            <div className="flex gap-2 justify-end">
                              <button
                                onClick={() => handleDecideApproval(request.id, 'rejected')}
                                className="flex-1 sm:flex-none px-3 py-2 border border-rose-200 hover:bg-rose-50 text-rose-600 font-bold text-[10px] uppercase tracking-wider rounded-lg transition-colors cursor-pointer"
                                id={`reject-btn-${request.id}`}
                              >
                                Reject Changes
                              </button>
                              <button
                                onClick={() => handleDecideApproval(request.id, 'approved')}
                                className="flex-1 sm:flex-none px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[10px] uppercase tracking-wider rounded-lg transition-colors shadow-sm cursor-pointer"
                                id={`approve-btn-${request.id}`}
                              >
                                Approve & Update
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* History of Decisions */}
                {approvals.filter(a => a.status !== 'pending').length > 0 && (
                  <div className="mt-8 pt-6 border-t border-slate-100 space-y-3">
                    <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Past Approvals Log</h4>
                    <div className="space-y-2.5 max-h-[300px] overflow-y-auto pr-1">
                      {approvals.filter(a => a.status !== 'pending').sort((a,b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()).slice(0, 5).map((log) => (
                        <div key={log.id} className="p-3 bg-slate-50 border border-slate-200/60 rounded-xl flex items-start justify-between gap-3 text-slate-600">
                          <div className="space-y-0.5 min-w-0">
                            <span className="text-[10px] font-bold text-slate-700 block truncate">{log.teacherName}</span>
                            <span className="text-[9px] text-slate-400 block">Decided: {new Date(log.decidedAt || log.createdAt).toLocaleDateString()}</span>
                            {log.adminNotes && (
                              <span className="text-[9px] text-slate-500 italic block mt-1 truncate">"{log.adminNotes}"</span>
                            )}
                          </div>
                          <span className={`shrink-0 text-[8px] font-mono font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${
                            log.status === 'approved' 
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-150' 
                              : 'bg-rose-50 text-rose-700 border-rose-150'
                          }`}>
                            {log.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* State-Based Delete Confirmation Dialog Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in" id="delete-confirmation-modal">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 animate-scale-up">
            <div className="flex items-start gap-4">
              <div className="h-10 w-10 bg-red-50 text-red-600 rounded-xl flex items-center justify-center shrink-0 border border-red-100">
                <Trash2 className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <h3 className="text-base font-bold text-slate-900">Confirm Deletion</h3>
                <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
                  Are you sure you want to delete the {deleteConfirm.type === 'subject' ? 'subject' : 'account'} <strong className="text-slate-800">"{deleteConfirm.name}"</strong>?
                </p>
                <p className="text-[11px] text-red-600 mt-2 bg-red-50/50 p-2 rounded-lg border border-red-100/50">
                  ⚠️ This action is permanent. All linked records, academic files, student enrollments, or performance data will be deleted immediately.
                </p>
              </div>
            </div>
            
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl cursor-pointer transition-colors"
                id="delete-cancel-btn"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold text-xs rounded-xl cursor-pointer transition-colors shadow-sm shadow-red-200"
                id="delete-confirm-btn"
              >
                Delete permanently
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
