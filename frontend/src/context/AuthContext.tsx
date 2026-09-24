import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Navigate, useLocation, Link } from 'react-router-dom';
import { clearAuthToken, getAuthToken, getCurrentUser, setAuthToken } from '../services/api';
import { UserRead, UserRole } from '../types';

interface AuthContextType {
  token: string | null;
  user: UserRead | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isModerator: boolean;
  isUser: boolean;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => getAuthToken());
  const [user, setUser] = useState<UserRead | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = useCallback(async () => {
    const currentToken = getAuthToken();
    if (!currentToken) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const profile = await getCurrentUser();
      setUser(profile);
    } catch (err) {
      console.warn('Failed to load user session:', err);
      clearAuthToken();
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (newToken: string) => {
    setAuthToken(newToken);
    setToken(newToken);
    try {
      const profile = await getCurrentUser();
      setUser(profile);
    } catch {
      // Token might be malformed or invalid
      clearAuthToken();
      setToken(null);
      setUser(null);
    }
  };

  const logout = () => {
    clearAuthToken();
    setToken(null);
    setUser(null);
  };

  const role = user?.role || null;
  const isAdmin = role === 'ADMIN';
  const isModerator = role === 'MODERATOR' || role === 'ADMIN';
  const isUser = role === 'USER';

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        role,
        isAuthenticated: !!token && !!user,
        isAdmin,
        isModerator,
        isUser,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Route guard component protecting staff moderator areas.
 * Allows MODERATOR and ADMIN. If role is USER, displays informative access request screen.
 */
export const ModeratorProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isModerator, isUser, user, isLoading, logout } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="flex items-center gap-3 text-zinc-500 font-mono text-sm">
          <div className="w-4 h-4 border-2 border-zinc-400 border-t-transparent rounded-full animate-spin" />
          Verifying authorization credentials...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/moderator/login" state={{ from: location }} replace />;
  }

  // If user is authenticated but only has standard USER role (not MODERATOR or ADMIN)
  if (isUser && !isModerator) {
    return (
      <div className="max-w-xl mx-auto py-16 px-4">
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-8 text-zinc-200">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 text-xs font-mono font-medium mb-4">
            Role: USER (Standard Access)
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">
            Moderator Privileges Required
          </h2>
          <p className="text-sm text-zinc-300 mb-6 leading-relaxed">
            Welcome, <strong className="text-white">{user?.name || user?.email}</strong>. Your account is registered, but you do not currently have moderator or administrator permissions. An administrator must elevate your account to <code className="bg-zinc-800 text-amber-300 px-1.5 py-0.5 rounded text-xs">MODERATOR</code> before you can view and triage submitted reports.
          </p>
          <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-4 mb-6 text-xs font-mono text-zinc-400 space-y-1">
            <div>Account Email: <span className="text-zinc-200">{user?.email}</span></div>
            <div>Account Status: <span className="text-emerald-400">Active</span></div>
            <div>Permissions: <span className="text-amber-400">Restricted (Public & Submission Tracking Only)</span></div>
          </div>
          <div className="flex items-center gap-4">
            <Link
              to="/"
              className="px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-sm font-medium text-white transition-colors"
            >
              Return Home
            </Link>
            <button
              onClick={logout}
              className="px-4 py-2 rounded-lg border border-zinc-700 hover:bg-zinc-800 text-sm font-medium text-zinc-300 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

/**
 * Route guard component protecting administrator-only management areas.
 */
export const AdminProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isAdmin, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="flex items-center gap-3 text-zinc-500 font-mono text-sm">
          <div className="w-4 h-4 border-2 border-zinc-400 border-t-transparent rounded-full animate-spin" />
          Verifying administrator credentials...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/moderator/login" state={{ from: location }} replace />;
  }

  if (!isAdmin) {
    return <Navigate to="/moderator/reports" replace />;
  }

  return <>{children}</>;
};

// Backwards compatibility alias
export const ProtectedRoute = ModeratorProtectedRoute;
