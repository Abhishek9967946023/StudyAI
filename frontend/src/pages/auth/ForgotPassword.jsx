import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
  Sparkles,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  RotateCw,
  Loader2,
  KeyRound,
  ShieldCheck
} from 'lucide-react';

export default function ForgotPassword() {
  const {
    requestPasswordResetOtp,
    verifyPasswordResetOtp,
    confirmPasswordReset
  } = useAuth();
  const navigate = useNavigate();

  // 1 = Enter Email, 2 = Verify Code, 3 = Reset Password, 4 = Success
  const [step, setStep] = useState(1);

  const [email, setEmail] = useState('');
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [verificationToken, setVerificationToken] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [cooldownSeconds, setCooldownSeconds] = useState(0);
  const [devOtp, setDevOtp] = useState('');
  const [devNote, setDevNote] = useState('');

  const otpInputRefs = useRef([]);

  useEffect(() => {
    let timer = null;
    if (cooldownSeconds > 0) {
      timer = setInterval(() => {
        setCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [cooldownSeconds]);

  useEffect(() => {
    if (step === 2) {
      setTimeout(() => {
        otpInputRefs.current[0]?.focus();
      }, 150);
    }
  }, [step]);

  // Step 1: Request Reset OTP
  const handleRequestOtp = async (e) => {
    e?.preventDefault();
    setErrorMessage('');

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail) {
      setErrorMessage('Please enter your email address.');
      return;
    }

    try {
      setIsLoading(true);
      const res = await requestPasswordResetOtp(cleanEmail);
      setCooldownSeconds(res?.cooldown_seconds || 60);
      if (res?.dev_otp) setDevOtp(res.dev_otp);
      if (res?.dev_note) setDevNote(res.dev_note);
      setStep(2);
    } catch (err) {
      setErrorMessage(
        err?.message || 'Could not send reset code. Please check your email and try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleAutoFillOtp = (code) => {
    if (!code) return;
    const clean = String(code).replace(/\D/g, '').slice(0, 6);
    const digits = clean.split('');
    while (digits.length < 6) digits.push('');
    setOtpDigits(digits);
    setTimeout(() => {
      otpInputRefs.current[5]?.focus();
    }, 50);
  };

  // Step 2: OTP Inputs & Paste
  const handleOtpChange = (index, value) => {
    const cleanVal = value.replace(/\D/g, '');
    if (!cleanVal) {
      const updated = [...otpDigits];
      updated[index] = '';
      setOtpDigits(updated);
      return;
    }

    const char = cleanVal.slice(-1);
    const updated = [...otpDigits];
    updated[index] = char;
    setOtpDigits(updated);

    if (index < 5 && char) {
      otpInputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      otpInputRefs.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasted) return;

    const updated = [...otpDigits];
    for (let i = 0; i < 6; i++) {
      updated[i] = pasted[i] || '';
    }
    setOtpDigits(updated);

    const focusIdx = Math.min(pasted.length, 5);
    otpInputRefs.current[focusIdx]?.focus();
  };

  // Step 2: Verify Reset OTP
  const handleVerifyOtp = async (e) => {
    e?.preventDefault();
    setErrorMessage('');

    const fullOtp = otpDigits.join('');
    if (fullOtp.length !== 6) {
      setErrorMessage('Please enter all 6 digits of the reset code.');
      return;
    }

    try {
      setIsLoading(true);
      const res = await verifyPasswordResetOtp(email.trim().toLowerCase(), fullOtp);
      const token = res?.reset_token || res?.verification_token;
      if (token) {
        setVerificationToken(token);
        setStep(3);
      } else {
        setErrorMessage('Reset verification failed. Please request a new code.');
      }
    } catch (err) {
      setErrorMessage(
        err?.message || 'Invalid or expired reset code. Please verify and try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Resend OTP
  const handleResendOtp = async () => {
    if (cooldownSeconds > 0 || isLoading) return;
    setErrorMessage('');
    try {
      setIsLoading(true);
      const res = await requestPasswordResetOtp(email.trim().toLowerCase());
      setCooldownSeconds(res?.cooldown_seconds || 60);
      if (res?.dev_otp) setDevOtp(res.dev_otp);
      if (res?.dev_note) setDevNote(res.dev_note);
      setOtpDigits(['', '', '', '', '', '']);
      otpInputRefs.current[0]?.focus();
    } catch (err) {
      setErrorMessage(err?.message || 'Could not resend code. Please wait a moment.');
    } finally {
      setIsLoading(false);
    }
  };

  // Step 3: Confirm Password Reset
  const handleConfirmReset = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match. Please re-type your confirmation password.');
      return;
    }

    try {
      setIsLoading(true);
      await confirmPasswordReset({
        email: email.trim().toLowerCase(),
        verification_token: verificationToken,
        password,
        confirm_password: confirmPassword
      });
      setStep(4);
      setTimeout(() => {
        navigate('/dashboard', { replace: true });
      }, 1600);
    } catch (err) {
      setErrorMessage(
        err?.message || 'Failed to reset password. Please request a new code and try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const passLength = password.length >= 8;
  const passUpper = /[A-Z]/.test(password);
  const passLower = /[a-z]/.test(password);
  const passNumber = /[0-9]/.test(password);
  const passMatch = password.length > 0 && password === confirmPassword;

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
          <h1 className="auth-header-title">Reset your password</h1>
          <p className="auth-header-subtitle">
            Verify your email with a 6-digit code to securely regain access
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

          {/* STEP 1: Enter Registered Email */}
          {step === 1 && (
            <form onSubmit={handleRequestOtp} className="auth-form" noValidate>
              <div className="auth-field">
                <label htmlFor="reset-email" className="auth-label">
                  Registered Email Address
                </label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon-left">
                    <Mail size={16} />
                  </span>
                  <input
                    id="reset-email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="student@example.com"
                    required
                    disabled={isLoading}
                    className="auth-input"
                  />
                </div>
                <p className="auth-field-hint">
                  We'll send a single-use 6-digit reset code if an account exists with this email.
                </p>
              </div>

              <button
                id="reset-request-otp-btn"
                type="submit"
                disabled={isLoading}
                className="auth-btn-primary"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={16} className="auth-loading-spinner" />
                    <span>Sending Reset Code...</span>
                  </>
                ) : (
                  <>
                    <span>Send Reset Code</span>
                    <ArrowRight size={16} />
                  </>
                )}
              </button>

              <div style={{ textAlign: 'center', marginTop: '10px' }}>
                <Link to="/login" className="auth-link-btn secondary">
                  <ArrowLeft size={14} />
                  <span>Back to Sign In</span>
                </Link>
              </div>
            </form>
          )}

          {/* STEP 2: Verify Reset OTP */}
          {step === 2 && (
            <div className="auth-form">
              <div style={{ textAlign: 'center', marginBottom: '8px' }}>
                <div
                  style={{
                    width: '46px',
                    height: '46px',
                    borderRadius: '50%',
                    background: 'var(--indigo-tint)',
                    color: 'var(--indigo)',
                    margin: '0 auto 10px auto',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <KeyRound size={22} />
                </div>
                <p style={{ fontWeight: 600, color: 'var(--ink)', fontSize: '0.92rem', margin: 0 }}>
                  Enter 6-digit reset code
                </p>
                <p style={{ color: 'var(--muted)', fontSize: '0.8rem', marginTop: '4px' }}>
                  Sent to <strong style={{ color: 'var(--ink)' }}>{email}</strong>
                </p>
              </div>

              {devNote && (
                <div className="auth-dev-note-banner">
                  {devNote}
                </div>
              )}

              {devOtp && (
                <div className="auth-dev-badge">
                  <div className="auth-dev-badge-content">
                    <span className="auth-dev-badge-title">Local Dev Code</span>
                    <span className="auth-dev-code">{devOtp}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleAutoFillOtp(devOtp)}
                    className="auth-dev-fill-btn"
                  >
                    Auto-fill
                  </button>
                </div>
              )}

              <div className="auth-otp-row" onPaste={handleOtpPaste}>
                {otpDigits.map((digit, index) => (
                  <input
                    key={index}
                    ref={(el) => (otpInputRefs.current[index] = el)}
                    id={`reset-otp-box-${index}`}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleOtpChange(index, e.target.value)}
                    onKeyDown={(e) => handleOtpKeyDown(index, e)}
                    disabled={isLoading}
                    aria-label={`Digit ${index + 1}`}
                    className="auth-otp-box"
                  />
                ))}
              </div>

              <button
                id="reset-verify-otp-btn"
                type="button"
                onClick={handleVerifyOtp}
                disabled={isLoading || otpDigits.join('').length !== 6}
                className="auth-btn-primary"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={16} className="auth-loading-spinner" />
                    <span>Verifying Code...</span>
                  </>
                ) : (
                  <>
                    <span>Verify & Continue</span>
                    <ArrowRight size={16} />
                  </>
                )}
              </button>

              <div className="auth-cooldown-bar">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="auth-link-btn secondary"
                >
                  <ArrowLeft size={14} />
                  <span>Change email</span>
                </button>

                {cooldownSeconds > 0 ? (
                  <span className="auth-cooldown-badge">
                    Resend in <strong>{cooldownSeconds}s</strong>
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={handleResendOtp}
                    disabled={isLoading}
                    className="auth-link-btn"
                  >
                    <RotateCw size={14} />
                    <span>Resend code</span>
                  </button>
                )}
              </div>
            </div>
          )}

          {/* STEP 3: Create New Password */}
          {step === 3 && (
            <form onSubmit={handleConfirmReset} className="auth-form" noValidate>
              <div style={{ textAlign: 'center', marginBottom: '8px' }}>
                <div
                  style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '50%',
                    background: 'var(--teal-tint)',
                    color: 'var(--teal)',
                    margin: '0 auto 8px auto',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <ShieldCheck size={22} />
                </div>
                <p style={{ fontWeight: 600, color: 'var(--ink)', fontSize: '0.92rem', margin: 0 }}>
                  Create New Password
                </p>
                <p style={{ color: 'var(--muted)', fontSize: '0.78rem', marginTop: '2px' }}>
                  Ensure it is strong and distinct from past passwords
                </p>
              </div>

              <div className="auth-field">
                <label htmlFor="reset-new-password" className="auth-label">
                  New Password
                </label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon-left">
                    <Lock size={16} />
                  </span>
                  <input
                    id="reset-new-password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min 8 characters"
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

              <div className="auth-field">
                <label htmlFor="reset-confirm-password" className="auth-label">
                  Confirm New Password
                </label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon-left">
                    <Lock size={16} />
                  </span>
                  <input
                    id="reset-confirm-password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-type your new password"
                    required
                    disabled={isLoading}
                    className="auth-input"
                    style={{ paddingRight: '40px' }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                    className="auth-toggle-pwd-btn"
                  >
                    {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div className="auth-checklist">
                <div className={`auth-check-item ${passLength ? 'valid' : ''}`}>
                  <CheckCircle2 size={14} />
                  <span>At least 8 characters long</span>
                </div>
                <div className={`auth-check-item ${passUpper && passLower ? 'valid' : ''}`}>
                  <CheckCircle2 size={14} />
                  <span>Uppercase & lowercase letters</span>
                </div>
                <div className={`auth-check-item ${passNumber ? 'valid' : ''}`}>
                  <CheckCircle2 size={14} />
                  <span>Includes at least one number</span>
                </div>
                <div className={`auth-check-item ${passMatch ? 'valid' : ''}`}>
                  <CheckCircle2 size={14} />
                  <span>Passwords match</span>
                </div>
              </div>

              <button
                id="reset-confirm-btn"
                type="submit"
                disabled={isLoading || !passLength || !passMatch}
                className="auth-btn-primary"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={16} className="auth-loading-spinner" />
                    <span>Saving New Password...</span>
                  </>
                ) : (
                  <>
                    <span>Reset Password & Enter StudyAI</span>
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>
          )}

          {/* STEP 4: Success Message */}
          {step === 4 && (
            <div className="auth-success-card">
              <div className="auth-success-badge">
                <CheckCircle2 size={32} />
              </div>
              <h3 className="auth-success-title">Password Reset Complete!</h3>
              <p className="auth-success-desc">
                Your credentials have been securely updated. Entering your workspace...
              </p>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', color: 'var(--indigo)', fontSize: '0.82rem', fontWeight: 600 }}>
                <Loader2 size={16} className="auth-loading-spinner" />
                <span>Redirecting to Dashboard...</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
