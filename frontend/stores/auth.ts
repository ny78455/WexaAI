import { create } from 'zustand';
import { authApi } from '../lib/api';

interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: 'owner' | 'admin' | 'analyst' | 'viewer';
  organization_id: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  fetchUser: () => Promise<void>;
  login: (data: any) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  
  fetchUser: async () => {
    try {
      const response = await authApi.me();
      set({ user: response.data, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  login: async (data: any) => {
    const response = await authApi.login(data);
    localStorage.setItem('access_token', response.data.access_token);
    set({ user: response.data.user, isAuthenticated: true });
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch (e) {
      // Ignore errors on logout
    }
    localStorage.removeItem('access_token');
    set({ user: null, isAuthenticated: false });
  }
}));
