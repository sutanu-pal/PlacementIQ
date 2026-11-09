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
                <ModulePlaceholderPage
                  title="DSA Assessment Engine"
                  moduleNumber="3"
                  tech="Python Sandboxed Subprocess Runner + 20 Curated Problems"
                  description="Executes user-submitted algorithm solutions against isolated testcase suites with time & memory quotas, generating topic-wise mastery heatmaps."
                  pipelineSteps={[
                    { title: 'Problem Bank', desc: '20 problems across Arrays, Trees, Graphs, DP' },
                    { title: 'Sandboxed Runner', desc: 'subprocess.run with strict timeout and no network' },
                    { title: 'Test Evaluation', desc: 'Input/output assertion & timing telemetry' },
                    { title: 'Mastery Profiler', desc: 'Topic score weighted into composite readiness' },
                  ]}
                />
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
                <ModulePlaceholderPage
                  title="AI Mock Interview"
                  moduleNumber="4"
                  tech="Google Gemini 2.5 Flash + Multi-Turn Dialog State"
                  description="Simulates realistic technical, system design, and behavioral interviews (STAR method) with conversational adaptation and multi-dimensional rubric evaluation."
                  pipelineSteps={[
                    { title: 'Session Setup', desc: 'Technical, Behavioral, or HR selection' },
                    { title: 'Turn Execution', desc: 'Adaptive questions via Gemini 2.5 Flash' },
                    { title: 'Transcript Store', desc: 'Sequential chat history in PostgreSQL' },
                    { title: 'Rubric Scoring', desc: 'Communication, depth & problem-solving rating' },
                  ]}
                />
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
                <ModulePlaceholderPage
                  title="Personalized Learning Roadmap"
                  moduleNumber="5"
                  tech="Skill Gap Aggregator + Gemini Milestone Generator"
                  description="Consolidates weak signals from Resume, Job Matching, DSA, and Mock Interviews into an actionable, prioritized 4-week milestone curriculum."
                  pipelineSteps={[
                    { title: 'Gap Synthesis', desc: 'Cross-module weak signal aggregation' },
                    { title: 'Curriculum Gen', desc: 'Gemini prompts for targeted milestones' },
                    { title: 'Resource Links', desc: 'Curated problem and concept references' },
                    { title: 'Progress Tracking', desc: 'Checklist completion updating readiness score' },
                  ]}
                />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Admin Dashboard (Final Scope) */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
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
