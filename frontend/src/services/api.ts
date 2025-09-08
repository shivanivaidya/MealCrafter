import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Only redirect to login if we're not already on login/register pages
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/register') {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  register: async (username: string, email: string, password: string) => {
    const response = await api.post('/auth/register', {
      username,
      email,
      password,
    });
    return response.data;
  },
};

export const recipeService = {
  create: async (recipe: any) => {
    const response = await api.post('/recipes/', recipe);
    return response.data;
  },
  
  createFromImage: async (formData: FormData) => {
    const response = await api.post('/recipes/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  getAll: async () => {
    const response = await api.get('/recipes/');
    return response.data;
  },
  
  getById: async (id: number) => {
    const response = await api.get(`/recipes/${id}`);
    return response.data;
  },
  
  updateRating: async (id: number, rating: number) => {
    const response = await api.patch(`/recipes/${id}/rating`, {
      taste_rating: rating,
    });
    return response.data;
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/recipes/${id}`);
    return response.data;
  },
  
  search: async (query: any) => {
    const response = await api.post('/search/', query);
    return response.data;
  },
};

export default api;