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

export default function Register() {
  const {
    requestRegistrationOtp,
    verifyRegistrationOtp,
    completeRegistration
  } = useAuth();
  const navigate = useNavigate();

  // Wizard Step: 1 = Email, 2 = Verify OTP, 3 = Create Password, 4 = Success
  const [step, setStep] = useState(1);

  // Form states
  const [email, setEmail] = useState('');
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [verificationToken, setVerificationToken] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Status & Timers
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [cooldownSeconds, setCooldownSeconds] = useState(0);
  const [devOtp, setDevOtp] = useState('');

  // OTP Input Refs
  const otpInputRefs = useRef([]);

  // Countdown timer for resend code
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

  // Focus first OTP box when entering Step 2
  useEffect(() => {
    if (step === 2) {
      setTimeout(() => {
        otpInputRefs.current[0]?.focus();
      }, 150);
    }
  }, [step]);

  // Step 1: Request OTP
  const handleRequestOtp = async (e) => {
    e?.preventDefault();
    setErrorMessage('');

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail) {
      setErrorMessage('Please enter your email address.');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(cleanEmail)) {
      setErrorMessage('Please enter a valid email address (e.g., student@university.edu).');
      return;
    }

    try {
      setIsLoading(true);
      const res = await requestRegistrationOtp(cleanEmail);
      setCooldownSeconds(res?.cooldown_seconds || 60);
      if (res?.dev_otp) {
        setDevOtp(res.dev_otp);
      }
      setStep(2);
    } catch (err) {
      setErrorMessage(
        err?.message || 'Could not send verification code. Please check your email and try again.'
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

  // Step 2: Handle OTP input changes, paste, and backspace
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

  // Step 2: Verify OTP
  const handleVerifyOtp = async (e) => {
    e?.preventDefault();
    setErrorMessage('');

    const fullOtp = otpDigits.join('');
    if (fullOtp.length !== 6) {
      setErrorMessage('Please enter all 6 digits of the verification code.');
      return;
    }

    try {
      setIsLoading(true);
      const res = await verifyRegistrationOtp(email.trim().toLowerCase(), fullOtp);
      if (res?.verification_token) {
        setVerificationToken(res.verification_token);
        setStep(3);
      } else {
        setErrorMessage('Verification failed. Please request a new code.');
      }
    } catch (err) {
      setErrorMessage(
        err?.message || 'Invalid or expired verification code. Please verify and try again.'
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
      const res = await requestRegistrationOtp(email.trim().toLowerCase());
      setCooldownSeconds(res?.cooldown_seconds || 60);
      if (res?.dev_otp) {
        setDevOtp(res.dev_otp);
      }
      setOtpDigits(['', '', '', '', '', '']);
      otpInputRefs.current[0]?.focus();
    } catch (err) {
      setErrorMessage(err?.message || 'Could not resend code. Please wait a moment.');
    } finally {
      setIsLoading(false);
    }
  };

  // Step 3: Complete Registration
  const handleCompleteRegistration = async (e) => {
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
      await completeRegistration({
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
        err?.message || 'Failed to complete registration. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Password rules validation flags
  const passLength = password.length >= 8;
  const passUpper = /[A-Z]/.test(password);
  const passLower = /[a-z]/.test(password);
  const passNumber = /[0-9]/.test(password);
  const passMatch = password.length > 0 && password === confirmPassword;

  return (
    <div className="auth-page">
      <div className="auth-container">
        {/* Header Logo */}
        <div className="auth-brand">
          <Link to="/" className="auth-brand-link">
            <div className="auth-logo-badge">
              <Sparkles size={22} />
            </div>
            <span className="auth-brand-title">
              Study<span>AI</span>
            </span>
          </Link>
          <h1 className="auth-header-title">Create your account</h1>
          <p className="auth-header-subtitle">
            Personalized exam generator & adaptive study intelligence
          </p>
        </div>

        {/* Step Indicator Progress Bar */}
        <div className="auth-step-progress">
          {[
            { num: 1, label: 'Email' },
            { num: 2, label: 'Verify' },
            { num: 3, label: 'Password' },
            { num: 4, label: 'Ready' }
          ].map((s, idx) => (
            <React.Fragment key={s.num}>
              <div className="auth-step-node">
                <div
                  className={`auth-step-circle ${
                    step === s.num ? 'active' : step > s.num ? 'completed' : ''
                  }`}
                >
                  {step > s.num ? <CheckCircle2 size={15} /> : s.num}
                </div>
                <span className={`auth-step-label ${step >= s.num ? 'active' : ''}`}>
                  {s.label}
                </span>
              </div>
              {idx < 3 && (
                <div
                  className={`auth-step-line ${step > s.num ? 'completed' : ''}`}
                />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Form Card Container */}
        <div className="auth-card">
          {errorMessage && (
            <div role="alert" className="auth-alert-error">
              <AlertCircle size={18} />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* STEP 1: Enter Email */}
          {step === 1 && (
            <form onSubmit={handleRequestOtp} className="auth-form" noValidate>
              <div className="auth-field">
                <label htmlFor="reg-email" className="auth-label">
                  Academic or Personal Email
                </label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon-left">
                    <Mail size={16} />
                  </span>
                  <input
                    id="reg-email"
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
                  We'll send a 6-digit verification code to confirm your email address.
                </p>
              </div>

              <button
                id="reg-request-otp-btn"
                type="submit"
                disabled={isLoading}
                className="auth-btn-primary"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={16} className="auth-loading-spinner" />
                    <span>Sending Code...</span>
                  </>
                ) : (
                  <>
                    <span>Continue to Verification</span>
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>
          )}

          {/* STEP 2: Verify OTP */}
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
                  Enter 6-digit verification code
                </p>
                <p style={{ color: 'var(--muted)', fontSize: '0.8rem', marginTop: '4px' }}>
                  Sent to <strong style={{ color: 'var(--ink)' }}>{email}</strong>
                </p>
              </div>

              {/* Dev Mode OTP Banner */}
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

              {/* 6-Digit Boxes */}
              <div className="auth-otp-row" onPaste={handleOtpPaste}>
                {otpDigits.map((digit, index) => (
                  <input
                    key={index}
                    ref={(el) => (otpInputRefs.current[index] = el)}
                    id={`otp-box-${index}`}
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

              {/* Verify Button */}
              <button
                id="reg-verify-otp-btn"
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
                    <span>Verify Code</span>
                    <ArrowRight size={16} />
                  </>
                )}
              </button>

              {/* Cooldown & Resend Controls */}
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

          {/* STEP 3: Create Password */}
          {step === 3 && (
            <form onSubmit={handleCompleteRegistration} className="auth-form" noValidate>
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
                  Email Verified
                </p>
                <p style={{ color: 'var(--muted)', fontSize: '0.78rem', marginTop: '2px' }}>
                  Choose a strong password to protect your study materials
                </p>
              </div>

              {/* Password */}
              <div className="auth-field">
                <label htmlFor="reg-password" className="auth-label">
                  Create Password
                </label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon-left">
                    <Lock size={16} />
                  </span>
                  <input
                    id="reg-password"
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

              {/* Confirm Password */}
              <div className="auth-field">
                <label htmlFor="reg-confirm-password" className="auth-label">
                  Confirm Password
                </label>
                <div className="auth-input-wrapper">
                  <span className="auth-input-icon-left">
                    <Lock size={16} />
                  </span>
                  <input
                    id="reg-confirm-password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-type your password"
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

              {/* Password Checklist */}
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
                id="reg-complete-btn"
                type="submit"
                disabled={isLoading || !passLength || !passMatch}
                className="auth-btn-primary"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={16} className="auth-loading-spinner" />
                    <span>Creating Account...</span>
                  </>
                ) : (
                  <>
                    <span>Complete & Enter StudyAI</span>
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>
          )}

          {/* STEP 4: Success & Entering Dashboard */}
          {step === 4 && (
            <div className="auth-success-card">
              <div className="auth-success-badge">
                <CheckCircle2 size={32} />
              </div>
              <h3 className="auth-success-title">Registration Complete!</h3>
              <p className="auth-success-desc">
                Your secure account has been created. Redirecting to your study dashboard...
              </p>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', color: 'var(--indigo)', fontSize: '0.82rem', fontWeight: 600 }}>
                <Loader2 size={16} className="auth-loading-spinner" />
                <span>Entering workspace...</span>
              </div>
            </div>
          )}

          {/* Footer Navigation */}
          {step < 4 && (
            <div className="auth-card-footer">
              Already have an account?{' '}
              <Link to="/login">Sign in</Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
