/**
 * =============================================================================
 * StudyAI — Authentication Context & Provider
 * =============================================================================
 * Manages global user authentication state, tokens, login/logout, and registration.
 * Ensures zero content flashing on initial load and handles expired sessions.
 * =============================================================================
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AUTH_STORAGE_KEY = 'studyai_auth_token';
export const USER_STORAGE_KEY = 'studyai_user';

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(AUTH_STORAGE_KEY) || null;
    }
    return null;
  });

  const [user, setUser] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(USER_STORAGE_KEY);
      if (saved) {
        try {
          return JSON.parse(saved);
        } catch {
          return null;
        }
      }
    }
    return null;
  });

  const [isLoading, setIsLoading] = useState(true);

  // Clear local credentials helper
  const clearAuth = useCallback(() => {
    setToken(null);
    setUser(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      localStorage.removeItem(USER_STORAGE_KEY);
    }
  }, []);

  // Save credentials helper: in-memory token, localStorage fallback for SPA API requests
  const saveAuth = useCallback((authToken, authUser) => {
    setToken(authToken || null);
    setUser(authUser || null);
    if (typeof window !== 'undefined') {
      if (authToken) {
        localStorage.setItem(AUTH_STORAGE_KEY, authToken);
      } else {
        localStorage.removeItem(AUTH_STORAGE_KEY);
      }
      if (authUser) {
        localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(authUser));
      } else {
        localStorage.removeItem(USER_STORAGE_KEY);
      }
    }
  }, []);

  // Verify active session on mount via Bearer token or HttpOnly cookie
  useEffect(() => {
    let isMounted = true;

    async function initializeAuth() {
      try {
        const response = await authService.getCurrentUser();
        if (isMounted && response?.user) {
          setUser(response.user);
          if (typeof window !== 'undefined') {
            localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(response.user));
          }
        } else if (isMounted) {
          clearAuth();
        }
      } catch {
        if (isMounted) {
          clearAuth();
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initializeAuth();

    // Listen for global auth expired events triggered by apiClient
    const handleAuthExpired = () => {
      clearAuth();
    };
    window.addEventListener('studyai_auth_expired', handleAuthExpired);

    return () => {
      isMounted = false;
      window.removeEventListener('studyai_auth_expired', handleAuthExpired);
    };
  }, [clearAuth]);

  // Login handler
  const login = async ({ email, password }) => {
    const response = await authService.login({ email, password });
    if (response?.user) {
      saveAuth(response.token, response.user);
    }
    return response;
  };

  // Logout handler
  const logout = async () => {
    try {
      await authService.logout();
    } finally {
      clearAuth();
    }
  };

  // Complete registration handler (sets session immediately)
  const completeRegistration = async ({ email, verification_token, password, confirm_password }) => {
    const response = await authService.completeRegistration({
      email,
      verification_token,
      password,
      confirm_password
    });
    if (response?.user) {
      saveAuth(response.token, response.user);
    }
    return response;
  };

  // Confirm password reset handler
  const confirmPasswordReset = async ({ email, verification_token, password, confirm_password }) => {
    const response = await authService.confirmPasswordReset({
      email,
      verification_token,
      password,
      confirm_password
    });
    if (response?.user) {
      saveAuth(response.token, response.user);
    }
    return response;
  };

  const value = {
    user,
    token,
    isAuthenticated: Boolean(user),
    isLoading,
    login,
    logout,
    requestRegistrationOtp: authService.requestRegistrationOtp,
    verifyRegistrationOtp: authService.verifyRegistrationOtp,
    completeRegistration,
    requestPasswordResetOtp: authService.requestPasswordResetOtp,
    verifyPasswordResetOtp: authService.verifyPasswordResetOtp,
    confirmPasswordReset
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
