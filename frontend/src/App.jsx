import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { ResumeAnalyzerPage } from './pages/ResumeAnalyzerPage';
import { AdminPage } from './pages/AdminPage';
import { JobMatchingPage } from './pages/JobMatchingPage';
import { DsaAssessmentPage } from './pages/DsaAssessmentPage';
import { MockInterviewPage } from './pages/MockInterviewPage';
import { LearningRoadmapPage } from './pages/LearningRoadmapPage';
import { NotFoundPage } from './pages/NotFoundPage';

const AppLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar onToggleSidebar={() => setSidebarOpen((prev) => !prev)} />
      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

export const App = () => {
  return (
    <AuthProvider>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected Dashboard */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <AppLayout>
                <DashboardPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Protected Module 1: AI Resume Analyzer */}
        <Route
          path="/resume"
          element={
            <ProtectedRoute>
              <AppLayout>
                <ResumeAnalyzerPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Protected Module 2: Intelligent Job Matching */}
        <Route
          path="/jobs"
          element={
            <ProtectedRoute>
              <AppLayout>
                <JobMatchingPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Protected Module 3: DSA Assessment Engine */}
        <Route
          path="/dsa"
          element={
            <ProtectedRoute>
              <AppLayout>
                <DsaAssessmentPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Protected Module 4: AI Mock Interview */}
        <Route
          path="/interview"
          element={
            <ProtectedRoute>
              <AppLayout>
                <MockInterviewPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Protected Module 5: Personalized Learning Roadmap */}
        <Route
          path="/roadmap"
          element={
            <ProtectedRoute>
              <AppLayout>
                <LearningRoadmapPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Admin Dashboard */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute requireAdmin={true}>
              <AppLayout>
                <AdminPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Redirect root to dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* 404 Route */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AuthProvider>
  );
};

export default App;
