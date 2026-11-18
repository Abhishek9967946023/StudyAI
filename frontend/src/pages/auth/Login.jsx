import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Sparkles, Mail, Lock, Eye, EyeOff, ArrowRight, AlertCircle, Loader2 } from 'lucide-react';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setErrorMessage('Please enter your email address.');
      return;
    }
    if (!password) {
      setErrorMessage('Please enter your password.');
      return;
    }

    try {
      setIsLoading(true);
      await login({ email: cleanEmail, password });
      navigate(from, { replace: true });
    } catch (err) {
      setErrorMessage(
        err?.message || 'Invalid email or password. Please verify your credentials.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        {/* Brand Header */}
        <div className="auth-brand">
          <Link to="/" className="auth-brand-link">
            <div className="auth-logo-badge">
              <Sparkles size={22} />
            </div>
            <span className="auth-brand-title">
              Study<span>AI</span>
            </span>
          </Link>
          <h1 className="auth-header-title">Welcome back</h1>
          <p className="auth-header-subtitle">
            Sign in to continue your intelligent study workspace
          </p>
        </div>

        {/* Card Container */}
        <div className="auth-card">
          {errorMessage && (
            <div role="alert" className="auth-alert-error">
              <AlertCircle size={18} />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form" noValidate>
            {/* Email or Username Field */}
            <div className="auth-field">
              <label htmlFor="login-email" className="auth-label">
                Email Address or Username
              </label>
              <div className="auth-input-wrapper">
                <span className="auth-input-icon-left">
                  <Mail size={16} />
                </span>
                <input
                  id="login-email"
                  type="text"
                  autoComplete="username email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="student@example.com or admin"
                  required
                  disabled={isLoading}
                  className="auth-input"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="auth-field">
              <div className="auth-label-row">
                <label htmlFor="login-password" className="auth-label">
                  Password
                </label>
                <Link to="/forgot-password" className="auth-forgot-link">
                  Forgot password?
                </Link>
              </div>
              <div className="auth-input-wrapper">
                <span className="auth-input-icon-left">
                  <Lock size={16} />
                </span>
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  disabled={isLoading}
                  className="auth-input"
                  style={{ paddingRight: '40px' }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="auth-toggle-pwd-btn"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              id="login-submit-btn"
              type="submit"
              disabled={isLoading}
              className="auth-btn-primary"
            >
              {isLoading ? (
                <>
                  <Loader2 size={16} className="auth-loading-spinner" />
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* Footer Navigation */}
          <div className="auth-card-footer">
            Don't have an account?{' '}
            <Link to="/register">Create free account</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
