import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Loader2 } from 'lucide-react';

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="auth-loading-screen">
        <div className="auth-loading-icon-wrapper">
          <Loader2 size={26} className="auth-loading-spinner" />
        </div>
        <p className="auth-loading-text">
          Validating authenticated session...
        </p>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Preserve requested location for seamless redirection after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children ? children : <Outlet />;
}
