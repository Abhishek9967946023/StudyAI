/**
 * =============================================================================
 * StudyAI — Authentication API Service
 * =============================================================================
 * Communicates with Django backend authentication endpoints:
 * - Email OTP Registration (Request -> Verify -> Complete)
 * - User Login, Logout & Session Check
 * - Password Reset Flow (Request -> Verify -> Confirm)
 * =============================================================================
 */

import { apiRequest } from './apiClient';

export const authService = {
  /**
   * Step 1: Request 6-digit registration OTP to user's email
   */
  async requestRegistrationOtp(email) {
    return apiRequest('/api/auth/register/request-otp/', {
      method: 'POST',
      body: JSON.stringify({ email: email?.trim() })
    });
  },

  /**
   * Step 2: Verify the 6-digit registration OTP
   */
  async verifyRegistrationOtp(email, otp) {
    return apiRequest('/api/auth/register/verify-otp/', {
      method: 'POST',
      body: JSON.stringify({
        email: email?.trim(),
        otp: String(otp).trim()
      })
    });
  },

  /**
   * Step 3: Complete registration and set account password
   */
  async completeRegistration({ email, verification_token, password, confirm_password }) {
    return apiRequest('/api/auth/register/complete/', {
      method: 'POST',
      body: JSON.stringify({
        email: email?.trim(),
        verification_token,
        password,
        confirm_password
      })
    });
  },

  /**
   * Returning-user Login
   */
  async login({ email, password }) {
    return apiRequest('/api/auth/login/', {
      method: 'POST',
      body: JSON.stringify({
        email: email?.trim(),
        password
      })
    });
  },

  /**
   * Revoke session and logout
   */
  async logout() {
    try {
      return await apiRequest('/api/auth/logout/', {
        method: 'POST'
      });
    } catch {
      // Continue client-side cleanup even if backend network fails
      return { success: true };
    }
  },

  /**
   * Fetch current authenticated user profile
   */
  async getCurrentUser() {
    return apiRequest('/api/auth/me/', {
      method: 'GET'
    });
  },

  /**
   * Step 1: Request Password Reset OTP
   */
  async requestPasswordResetOtp(email) {
    return apiRequest('/api/auth/password-reset/request-otp/', {
      method: 'POST',
      body: JSON.stringify({ email: email?.trim() })
    });
  },

  /**
   * Step 2: Verify Password Reset OTP
   */
  async verifyPasswordResetOtp(email, otp) {
    return apiRequest('/api/auth/password-reset/verify-otp/', {
      method: 'POST',
      body: JSON.stringify({
        email: email?.trim(),
        otp: String(otp).trim()
      })
    });
  },

  /**
   * Step 3: Set and confirm new password
   */
  async confirmPasswordReset({ email, verification_token, password, confirm_password }) {
    return apiRequest('/api/auth/password-reset/confirm/', {
      method: 'POST',
      body: JSON.stringify({
        email: email?.trim(),
        verification_token,
        password,
        confirm_password
      })
    });
  }
};
