import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import ProtectedRoute from '../components/auth/ProtectedRoute';
import { useAuth } from '../hooks/useAuth';

const lazyNamed = (loadModule, exportName) =>
  lazy(() => loadModule().then((module) => ({ default: module[exportName] })));

const Login = lazy(() => import('../pages/auth/Login'));
const Register = lazy(() => import('../pages/auth/Register'));
const ForgotPassword = lazy(() => import('../pages/auth/ForgotPassword'));

const Landing = lazyNamed(() => import('../pages/Landing'), 'Landing');
const Dashboard = lazy(() => import('../pages/Dashboard'));
const Upload = lazy(() => import('../pages/Upload'));
const Analysis = lazyNamed(() => import('../pages/Analysis'), 'Analysis');
const Summary = lazyNamed(() => import('../pages/Summary'), 'Summary');
const ExamConfig = lazyNamed(() => import('../pages/ExamConfig'), 'ExamConfig');
const Exam = lazyNamed(() => import('../pages/Exam'), 'Exam');
const Results = lazy(() => import('../pages/Results'));
const TopicIntelligence = lazy(() => import('../pages/TopicIntelligence'));
const Revision = lazy(() => import('../pages/Revision'));
const QuestionBank = lazy(() => import('../pages/QuestionBank'));
const History = lazy(() => import('../pages/History'));
const Settings = lazyNamed(() => import('../pages/Settings'), 'Settings');
const Workspace = lazy(() => import('../pages/Workspace'));
const MySummaries = lazy(() => import('../pages/MySummaries'));
const AiQualityEvaluationView = lazyNamed(
  () => import('../pages/AiQualityEvaluation'),
  'AiQualityEvaluationView'
);

function withPageSuspense(element) {
  return (
    <Suspense
      fallback={
        <div className="sa-card" role="status" aria-live="polite" aria-busy="true">
          Loading page...
        </div>
      }
    >
      {element}
    </Suspense>
  );
}

/**
 * Redirects already-authenticated users away from public auth pages
 */
function PublicAuthRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return null;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return children;
}

/**
 * Root route: sends authenticated users to /dashboard and guests to /landing
 */
function RootRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return null;
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <Landing />;
}

export function AppRoutes() {
  return (
    <Routes>
      {/* Public Authentication Pages */}
      <Route path="/login" element={withPageSuspense(<PublicAuthRoute><Login /></PublicAuthRoute>)} />
      <Route path="/register" element={withPageSuspense(<PublicAuthRoute><Register /></PublicAuthRoute>)} />
      <Route path="/forgot-password" element={withPageSuspense(<PublicAuthRoute><ForgotPassword /></PublicAuthRoute>)} />

      {/* Public Landing Pages */}
      <Route path="/" element={withPageSuspense(<RootRoute />)} />
      <Route path="/landing" element={withPageSuspense(<Landing />)} />

      {/* Protected Application Workspace (Requires Valid Session) */}
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={withPageSuspense(<Dashboard />)} />
        <Route path="/evaluation" element={withPageSuspense(<AiQualityEvaluationView />)} />
        <Route path="/workspace" element={withPageSuspense(<Workspace />)} />
        <Route path="/workspace/:materialId" element={withPageSuspense(<Workspace />)} />
        <Route path="/upload" element={withPageSuspense(<Upload />)} />
        <Route path="/my-summaries" element={withPageSuspense(<MySummaries />)} />
        <Route path="/analysis" element={withPageSuspense(<Analysis />)} />
        <Route path="/summary" element={withPageSuspense(<Summary />)} />
        <Route path="/generate-exam" element={withPageSuspense(<ExamConfig />)} />
        <Route path="/exam-config" element={withPageSuspense(<ExamConfig />)} />
        <Route path="/exam" element={withPageSuspense(<Exam />)} />
        <Route path="/exam/:examId" element={withPageSuspense(<Exam />)} />
        <Route path="/results" element={withPageSuspense(<Results />)} />
        <Route path="/results/:resultId" element={withPageSuspense(<Results />)} />
        <Route path="/topics" element={withPageSuspense(<TopicIntelligence />)} />
        <Route path="/revision" element={withPageSuspense(<Revision />)} />
        <Route path="/questions" element={withPageSuspense(<QuestionBank />)} />
        <Route path="/history" element={withPageSuspense(<History />)} />
        <Route path="/settings" element={withPageSuspense(<Settings />)} />

        {/* Catch-all route */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}

export default AppRoutes;

