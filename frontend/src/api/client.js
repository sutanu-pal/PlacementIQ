import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach access token to outgoing requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('placementiq_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Intercept 401 responses to auto-refresh token if possible
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('placementiq_refresh_token');

      if (refreshToken) {
        try {
          const res = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token: newRefresh } = res.data;
          localStorage.setItem('placementiq_access_token', access_token);
          localStorage.setItem('placementiq_refresh_token', newRefresh);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshErr) {
          localStorage.removeItem('placementiq_access_token');
          localStorage.removeItem('placementiq_refresh_token');
          localStorage.removeItem('placementiq_user');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },
  register: async (data) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  updateMe: async (data) => {
    const response = await api.put('/auth/me', data);
    return response.data;
  },
  getAdminUsers: async () => {
    const response = await api.get('/auth/admin/users');
    return response.data;
  },
};

export const resumeAPI = {
  uploadResume: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/resumes/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  listResumes: async () => {
    const response = await api.get('/resumes/');
    return response.data;
  },
  getResume: async (id) => {
    const response = await api.get(`/resumes/${id}`);
    return response.data;
  },
  getResumeAnalysis: async (id) => {
    const response = await api.get(`/resumes/${id}/analysis`);
    return response.data;
  },
  deleteResume: async (id) => {
    const response = await api.delete(`/resumes/${id}`);
    return response.data;
  },
};

export const systemAPI = {
  getHealth: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export const jobAPI = {
  listJobs: async (params = {}) => {
    const response = await api.get('/jobs/', { params });
    return response.data;
  },
  getJob: async (id) => {
    const response = await api.get(`/jobs/${id}`);
    return response.data;
  },
  createJob: async (data) => {
    const response = await api.post('/jobs/', data);
    return response.data;
  },
  updateJob: async (id, data) => {
    const response = await api.put(`/jobs/${id}`, data);
    return response.data;
  },
  deleteJob: async (id) => {
    const response = await api.delete(`/jobs/${id}`);
    return response.data;
  },
  matchJob: async (jobId, resumeId = null) => {
    const response = await api.post(`/jobs/${jobId}/match`, resumeId ? { resume_id: resumeId } : {});
    return response.data;
  },
};

export const jobMatchAPI = {
  listMatches: async (params = {}) => {
    const response = await api.get('/job-matches/', { params });
    return response.data;
  },
  getMatch: async (id) => {
    const response = await api.get(`/job-matches/${id}`);
    return response.data;
  },
};

export default api;
