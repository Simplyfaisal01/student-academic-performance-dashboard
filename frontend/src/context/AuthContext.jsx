import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('acadtrack_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('acadtrack_token') || null);
  const [loading, setLoading] = useState(false);

  // Authorised demo accounts — must match users.csv dataset exactly.
  // Passwords: admins → Admin@123 | lecturers → Lecturer@123
  const DEMO_USERS = [
    {
      id: 1,
      name: 'Dr. A. Dike',
      email: 'adike@example.com',
      role: 'admin',
      title: 'Head of Department / Admin',
      _password: 'Admin@123',
    },
    {
      id: 2,
      name: 'Prof. M. Abdullahi',
      email: 'mabdullahi@example.com',
      role: 'admin',
      title: 'Exam Officer / Academic Advisor',
      _password: 'Admin@123',
    },
    {
      id: 5,
      name: 'Dr. B. Yakubu',
      email: 'yakubu5@example.com',
      role: 'lecturer',
      title: 'Senior Lecturer',
      _password: 'Lecturer@123',
    },
    {
      id: 6,
      name: 'Mr. T. Ogunleye',
      email: 'ogunleye6@example.com',
      role: 'lecturer',
      title: 'Lecturer II',
      _password: 'Lecturer@123',
    },
  ];

  const login = async (email, password, remember = false) => {
    setLoading(true);
    try {
      // ── Tier 1: Live backend API login ────────────────────────────────────
      try {
        const response = await api.post('/auth/login', { email, password });
        if (response.data && response.data.access_token) {
          const authToken = response.data.access_token;
          const authUser = response.data.user;
          setToken(authToken);
          setUser(authUser);
          localStorage.setItem('acadtrack_token', authToken);
          localStorage.setItem('acadtrack_user', JSON.stringify(authUser));
          return { success: true, user: authUser };
        }
      } catch (apiErr) {
        // Backend offline or returned an HTTP error — fall through to offline demo check.
        // If the backend IS reachable but returned 401 we must NOT let the user in.
        if (apiErr.response && apiErr.response.status === 401) {
          throw new Error('Invalid email or password. Please check your credentials.');
        }
        console.warn('Backend unavailable — checking offline demo credentials:', apiErr.message);
      }

      // ── Tier 2: Offline demo fallback (backend not running) ───────────────
      // Find the account by email first.
      const matchedUser = DEMO_USERS.find(
        (u) => u.email.toLowerCase() === email.trim().toLowerCase()
      );

      if (!matchedUser) {
        // Email is not in the authorised list — deny immediately.
        throw new Error('Access denied. This email address is not registered in the system.');
      }

      // Email matched — now verify password.
      if (password !== matchedUser._password) {
        throw new Error('Invalid password. Please check your credentials.');
      }

      // Both email and password correct — issue offline mock token.
      // Strip the internal _password field before storing.
      const { _password, ...safeUser } = matchedUser;
      const mockToken = 'mock_jwt_' + btoa(JSON.stringify(safeUser));
      setUser(safeUser);
      setToken(mockToken);
      localStorage.setItem('acadtrack_token', mockToken);
      localStorage.setItem('acadtrack_user', JSON.stringify(safeUser));
      return { success: true, user: safeUser };

      // ── NO generic fallback — any unrecognised email is rejected above ────
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('acadtrack_token');
    localStorage.removeItem('acadtrack_user');
  };

  const switchRole = (newRole) => {
    if (!user) return;
    const updated = { ...user, role: newRole };
    setUser(updated);
    localStorage.setItem('acadtrack_user', JSON.stringify(updated));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        switchRole,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin',
        isLecturer: user?.role === 'lecturer',
        // Strip internal _password field before exposing to consumers
        DEMO_USERS: DEMO_USERS.map(({ _password, ...u }) => u),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

