import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, ProtectedRoute, AdminProtectedRoute } from './context/AuthContext';
import { Header } from './components/common/Header';
import { Footer } from './components/common/Footer';
import { HomePage } from './pages/HomePage';
import { SubmitReportPage } from './pages/SubmitReportPage';
import { TrackReportPage } from './pages/TrackReportPage';
import { ModeratorLoginPage } from './pages/ModeratorLoginPage';
import { ModeratorDashboardPage } from './pages/ModeratorDashboardPage';
import { ModeratorReportDetailPage } from './pages/ModeratorReportDetailPage';
import { AdminUsersPage } from './pages/AdminUsersPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen flex flex-col bg-zinc-950 text-zinc-100 font-sans selection:bg-emerald-500/20 selection:text-emerald-300">
          <Header />
          <main className="flex-1 flex flex-col">
            <Routes>
              {/* Public Anonymous Reporter Routes */}
              <Route path="/" element={<HomePage />} />
              <Route path="/report" element={<SubmitReportPage />} />
              <Route path="/track" element={<TrackReportPage />} />
              <Route path="/track/:caseCode" element={<TrackReportPage />} />

              {/* Moderator & User Portal Authentication */}
              <Route path="/moderator/login" element={<ModeratorLoginPage />} />

              {/* Protected Staff Moderator Routes */}
              <Route
                path="/moderator/dashboard"
                element={
                  <ProtectedRoute>
                    <ModeratorDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/moderator/reports"
                element={
                  <ProtectedRoute>
                    <ModeratorDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/moderator/reports/:id"
                element={
                  <ProtectedRoute>
                    <ModeratorReportDetailPage />
                  </ProtectedRoute>
                }
              />

              {/* Protected Administrator Routes */}
              <Route
                path="/admin/users"
                element={
                  <AdminProtectedRoute>
                    <AdminUsersPage />
                  </AdminProtectedRoute>
                }
              />

              {/* Catch-all Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
