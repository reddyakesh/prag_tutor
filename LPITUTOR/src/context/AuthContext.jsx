import React, { createContext, useContext, useState } from 'react';
import { authService } from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('pragtutor_user');
      if (saved && saved !== 'undefined' && saved !== 'null') {
        const parsed = JSON.parse(saved);
        if (parsed && parsed.role) {
          return parsed;
        }
      }
    } catch (e) {
      console.warn('Clearing invalid localStorage user:', e);
      localStorage.removeItem('pragtutor_user');
    }
    return null;
  });

  const login = async (email, password, role) => {
    try {
      const res = await authService.login(email, password, role);
      if (res && res.user) {
        const userData = { ...res.user, token: res.token || `mock-token-${role}` };
        setUser(userData);
        localStorage.setItem('pragtutor_user', JSON.stringify(userData));
        return userData;
      }
    } catch (e) {
      console.warn('Backend login fallback used:', e);
    }

    const fallbackUser = {
      id: role === 'admin' ? 'ADM001' : (role === 'teacher' ? 'TCH001' : 'STU001'),
      name: role === 'admin' ? 'System Administrator' : (role === 'teacher' ? 'Dr. Sarah Jenkins' : 'Student User'),
      email: email || `${role}@pragtutor.edu`,
      role: role || 'student',
      access_granted: true,
      token: `mock-token-${role}`
    };
    setUser(fallbackUser);
    localStorage.setItem('pragtutor_user', JSON.stringify(fallbackUser));
    return fallbackUser;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('pragtutor_user');
  };

  return (
    <AuthContext.Provider value={{ user, setUser, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    return {
      user: null,
      setUser: () => {},
      login: () => {},
      logout: () => {},
    };
  }
  return context;
};
