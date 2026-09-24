import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AlertCircle, CheckCircle2, Lock, Mail, ShieldCheck, User } from 'lucide-react';
import { Button } from '../components/common/Button';
import { useAuth } from '../context/AuthContext';
import { loginModerator, register } from '../services/api';

export const ModeratorLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [mode, setMode] = useState<'signin' | 'register'>('signin');

  // Sign In State
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [password, setPassword] = useState('');

  // Register State
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const from = (location.state as any)?.from?.pathname || '/moderator/dashboard';

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

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
      await login(tokenData.access_token);
      navigate(from, { replace: true });
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!regEmail.trim() || !regPassword) {
      setErrorMessage('Email and password are required.');
      return;
    }

    if (regPassword.length < 8) {
      setErrorMessage('Password must be at least 8 characters in length.');
      return;
    }

    if (regPassword !== regConfirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    try {
      await register({
        name: regName.trim(),
        email: regEmail.trim(),
        password: regPassword,
        confirm_password: regConfirmPassword,
      });

      setSuccessMessage('Account registered successfully! You can now sign in.');
      setUsernameOrEmail(regEmail.trim());
      setPassword('');
      setRegPassword('');
      setRegConfirmPassword('');
      setMode('signin');
    } catch (err: any) {
      setErrorMessage(err.message || 'Registration failed. Please verify your inputs.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="py-12 px-4 max-w-sm mx-auto space-y-6">
      {/* Header */}
      <div className="space-y-1.5 text-center">
        <h1 className="text-xl font-semibold tracking-tight text-zinc-100">
          Staff & Moderator Portal
        </h1>
        <p className="text-xs text-zinc-400">
          Sign in or create an account to access reporting and administrative tools.
        </p>
      </div>

      {/* Mode Selector Tabs */}
      <div className="flex rounded-lg bg-zinc-900/80 p-1 border border-zinc-800">
        <button
          type="button"
          onClick={() => {
            setMode('signin');
            setErrorMessage(null);
          }}
          className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${
            mode === 'signin'
              ? 'bg-zinc-800 text-white shadow-sm'
              : 'text-zinc-400 hover:text-zinc-200'
          }`}
        >
          Sign In
        </button>
        <button
          type="button"
          onClick={() => {
            setMode('register');
            setErrorMessage(null);
          }}
          className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${
            mode === 'register'
              ? 'bg-zinc-800 text-white shadow-sm'
              : 'text-zinc-400 hover:text-zinc-200'
          }`}
        >
          Create Account
        </button>
      </div>

      {/* Card */}
      <div className="p-6 rounded-lg bg-zinc-900/40 border border-zinc-800 space-y-4">
        {errorMessage && (
          <div className="p-3 rounded-md bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="p-3 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400 mt-0.5" />
            <span>{successMessage}</span>
          </div>
        )}

        {mode === 'signin' ? (
          <form onSubmit={handleLoginSubmit} className="space-y-4">
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
                  placeholder="admin or user@domain.com"
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
          </form>
        ) : (
          <form onSubmit={handleRegisterSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label
                htmlFor="regName"
                className="block text-xs font-medium text-zinc-300"
              >
                Full name <span className="text-zinc-500 font-normal">(optional)</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                  <User className="w-3.5 h-3.5" />
                </div>
                <input
                  id="regName"
                  type="text"
                  value={regName}
                  onChange={(e) => setRegName(e.target.value)}
                  placeholder="Jane Doe"
                  autoComplete="name"
                  className="w-full rounded-md bg-zinc-900/50 border border-zinc-800 pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="regEmail"
                className="block text-xs font-medium text-zinc-300"
              >
                Email address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                  <Mail className="w-3.5 h-3.5" />
                </div>
                <input
                  id="regEmail"
                  type="email"
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                  placeholder="jane@university.edu"
                  required
                  autoComplete="email"
                  className="w-full rounded-md bg-zinc-900/50 border border-zinc-800 pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="regPassword"
                className="block text-xs font-medium text-zinc-300"
              >
                Password <span className="text-zinc-500 font-normal">(min 8 characters)</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                  <Lock className="w-3.5 h-3.5" />
                </div>
                <input
                  id="regPassword"
                  type="password"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  className="w-full rounded-md bg-zinc-900/50 border border-zinc-800 pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label
                htmlFor="regConfirmPassword"
                className="block text-xs font-medium text-zinc-300"
              >
                Confirm password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
                  <Lock className="w-3.5 h-3.5" />
                </div>
                <input
                  id="regConfirmPassword"
                  type="password"
                  value={regConfirmPassword}
                  onChange={(e) => setRegConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  className="w-full rounded-md bg-zinc-900/50 border border-zinc-800 pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 focus:ring-1 focus:ring-zinc-600 transition-colors"
                />
              </div>
            </div>

            <div className="text-[11px] text-zinc-400 bg-zinc-900/60 p-2.5 rounded border border-zinc-800/80">
              Note: New accounts receive <strong className="text-zinc-200">USER</strong> permissions. An administrator must approve moderator access before report triage is enabled.
            </div>

            <div className="pt-2">
              <Button
                type="submit"
                size="md"
                variant="primary"
                isLoading={isLoading}
                className="w-full"
              >
                Create Account
              </Button>
            </div>
          </form>
        )}

        <div className="pt-2 border-t border-zinc-800/80 flex items-center gap-1.5 text-[11px] text-zinc-500">
          <ShieldCheck className="w-3.5 h-3.5 shrink-0 text-zinc-400" />
          <span>Protected by signed JWT bearer authentication.</span>
        </div>
      </div>
    </div>
  );
};
