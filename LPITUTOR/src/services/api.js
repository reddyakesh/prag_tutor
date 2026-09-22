import axios from 'axios';

const API_BASE_URL = `http://${window.location.hostname}:8000/api`;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000,
});

api.interceptors.request.use((config) => {
  const user = JSON.parse(localStorage.getItem('pragtutor_user') || '{}');
  if (user.token) {
    config.headers.Authorization = `Bearer ${user.token}`;
  }
  return config;
});

export const authService = {
  login: async (email, password, portal = 'student') => {
    const res = await api.post('/auth/login', { email, password, portal, role: portal });
    return res.data;
  },
  requestOTP: async (email, name, role, department, subjects = []) => {
    const res = await api.post('/auth/request-otp', { email, name, role, department, subjects });
    return res.data;
  },
  verifyOTPRegister: async (email, otp, password) => {
    const res = await api.post('/auth/verify-otp-register', { email, otp, password });
    return res.data;
  },
  getMe: async (role) => {
    const res = await api.get(`/auth/me?role=${role}`);
    return res.data;
  }
};

export const adminService = {
  getDashboard: async () => {
    const res = await api.get('/admin/dashboard');
    return res.data;
  },
  getTeachers: async () => {
    const res = await api.get('/admin/teachers');
    return res.data;
  },
  updateTeacherAccess: async (teacherId, accessGranted) => {
    const res = await api.patch(`/admin/teachers/${teacherId}/access`, { access_granted: accessGranted });
    return res.data;
  },
  updateTeacherStatus: async (teacherId, status) => {
    const res = await api.patch(`/admin/teachers/${teacherId}/status`, { status });
    return res.data;
  },
  updateTeacherSubjects: async (teacherId, subjects) => {
    const res = await api.patch(`/admin/teachers/${teacherId}/subjects`, { subjects });
    return res.data;
  },
  clearKnowledgeBase: async (subjectId) => {
    const res = await api.post(`/admin/subjects/${subjectId}/clear`);
    return res.data;
  },
  getActivityStream: async () => {
    const res = await api.get('/admin/activity');
    return res.data;
  }
};

export const teacherService = {
  getSubjects: async () => {
    const res = await api.get('/teacher/subjects');
    return res.data;
  },
  uploadPDF: async (subjectId, files) => {
    const formData = new FormData();
    if (Array.isArray(files)) {
      files.forEach(f => formData.append('files', f));
    } else if (files) {
      formData.append('file', files);
    }
    const res = await api.post(`/teacher/subjects/${subjectId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },
  uploadPrerequisites: async (subjectId, fileOrData) => {
    if (fileOrData instanceof File) {
      const formData = new FormData();
      formData.append('file', fileOrData);
      const res = await api.post(`/teacher/subjects/${subjectId}/prerequisites`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return res.data;
    } else {
      const res = await api.post(`/teacher/subjects/${subjectId}/prerequisites`, fileOrData);
      return res.data;
    }
  },
  prepareKB: async (subjectId) => {
    const res = await api.post(`/teacher/subjects/${subjectId}/prepare`);
    return res.data;
  },
  getBuildStatus: async (subjectId) => {
    const res = await api.get(`/teacher/subjects/${subjectId}/status`);
    return res.data;
  }
};

export const studentService = {
  getSubjects: async () => {
    const res = await api.get('/student/subjects');
    return res.data;
  },
  queryTutor: async (query, subject = 'operating_systems', images = null, studentId = 'STU001', level = 'beginner') => {
    const res = await api.post('/chat/answer', {
      query,
      question: query,
      subject,
      images,
      student_id: studentId,
      level
    });
    return res.data;
  },
  getHistory: async (studentId = 'STU001') => {
    const res = await api.get(`/student/history?student_id=${studentId}`);
    return res.data;
  },
  markLearned: async (studentId = 'STU001', subject = 'operating_systems', topic = '') => {
    const res = await api.post('/student/mark_learned', {
      student_id: studentId,
      subject,
      topic
    });
    return res.data;
  }
};

export default api;
