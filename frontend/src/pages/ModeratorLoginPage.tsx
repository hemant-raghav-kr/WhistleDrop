import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AlertCircle, Lock, ShieldCheck, User } from 'lucide-react';
import { Button } from '../components/common/Button';
import { useAuth } from '../context/AuthContext';
import { loginModerator } from '../services/api';

export const ModeratorLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const from = (location.state as any)?.from?.pathname || '/moderator/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!usernameOrEmail.trim() || !password) {
      setErrorMessage('Please enter both your username/email and password.');
      return;
    }

    setIsLoading(true);
    try {
      const tokenData = await loginModerator({
        username_or_email: usernameOrEmail.trim(),
        password,
      });
      login(tokenData.access_token);
      navigate(from, { replace: true });
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="py-16 px-4 max-w-sm mx-auto space-y-6">
      {/* Header */}
      <div className="space-y-1.5 text-center">
        <h1 className="text-xl font-semibold tracking-tight text-zinc-100">Moderator portal</h1>
        <p className="text-xs text-zinc-400">
          Sign in with your staff account to review and update reports.
        </p>
      </div>

      {/* Login Card */}
      <div className="p-6 rounded-lg bg-zinc-900/40 border border-zinc-800 space-y-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          {errorMessage && (
            <div className="p-3 rounded-md bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div className="space-y-1.5">
            <label
              htmlFor="usernameOrEmail"
              className="block text-xs font-medium text-zinc-300"
            >
              Username or email
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                <User className="w-3.5 h-3.5" />
              </div>
              <input
                id="usernameOrEmail"
                type="text"
                value={usernameOrEmail}
                onChange={(e) => setUsernameOrEmail(e.target.value)}
                placeholder="admin"
                required
                autoComplete="username"
                className="w-full rounded-md bg-zinc-900/50 border border-zinc-800 pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="password"
              className="block text-xs font-medium text-zinc-300"
            >
              Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                <Lock className="w-3.5 h-3.5" />
              </div>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
                autoComplete="current-password"
                className="w-full rounded-md bg-zinc-900/50 border border-zinc-800 pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors"
              />
            </div>
          </div>

          <div className="pt-2">
            <Button
              type="submit"
              size="md"
              variant="primary"
              isLoading={isLoading}
              className="w-full"
            >
              Sign in
            </Button>
          </div>

          <div className="pt-2 border-t border-zinc-800/80 flex items-center gap-1.5 text-[11px] text-zinc-500">
            <ShieldCheck className="w-3.5 h-3.5 shrink-0 text-zinc-400" />
            <span>Protected by signed JWT bearer authentication.</span>
          </div>
        </form>
      </div>
    </div>
  );
};
