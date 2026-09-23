import React, { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, LogOut, Menu, Shield, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Header: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/moderator/login');
    setMobileMenuOpen(false);
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
      isActive
        ? 'text-zinc-100 bg-zinc-900 border border-zinc-800'
        : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60'
    }`;

  return (
    <header className="border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-sm sticky top-0 z-40">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Brand Logo */}
        <Link
          to="/"
          className="flex items-center gap-2.5 font-semibold text-base text-zinc-100 hover:text-white transition-colors"
        >
          <div className="w-7 h-7 rounded-md bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Shield className="w-3.5 h-3.5" />
          </div>
          <span className="tracking-tight">WhistleDrop</span>
          <span className="text-[10px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 ml-1">
            confidential
          </span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-1.5">
          <NavLink to="/report" className={navLinkClass}>
            Submit report
          </NavLink>

          <NavLink to="/track" className={navLinkClass}>
            Track report
          </NavLink>

          <div className="h-3.5 w-px bg-zinc-800 mx-2" />

          {isAuthenticated ? (
            <div className="flex items-center gap-2">
              <NavLink to="/moderator/dashboard" className={navLinkClass}>
                <span className="flex items-center gap-1.5">
                  <LayoutDashboard className="w-3.5 h-3.5 text-emerald-400" />
                  Dashboard
                </span>
              </NavLink>
              <button
                onClick={handleLogout}
                className="px-2.5 py-1.5 rounded-md text-sm font-medium text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors flex items-center gap-1.5"
                title="Log out"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Logout</span>
              </button>
            </div>
          ) : (
            <NavLink
              to="/moderator/login"
              className={({ isActive }) =>
                `text-xs px-2.5 py-1.5 rounded-md text-zinc-400 hover:text-zinc-200 transition-colors ${
                  isActive ? 'text-zinc-200 bg-zinc-900' : ''
                }`
              }
            >
              Moderator portal
            </NavLink>
          )}
        </nav>

        {/* Mobile Menu Button */}
        <div className="flex md:hidden">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 rounded-md text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900 focus:outline-none"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-zinc-800 bg-zinc-950 px-4 py-3 space-y-1">
          <NavLink
            to="/report"
            onClick={() => setMobileMenuOpen(false)}
            className={({ isActive }) =>
              `block px-3 py-2 rounded-md text-sm font-medium ${
                isActive ? 'text-zinc-100 bg-zinc-900' : 'text-zinc-400 hover:text-zinc-200'
              }`
            }
          >
            Submit report
          </NavLink>

          <NavLink
            to="/track"
            onClick={() => setMobileMenuOpen(false)}
            className={({ isActive }) =>
              `block px-3 py-2 rounded-md text-sm font-medium ${
                isActive ? 'text-zinc-100 bg-zinc-900' : 'text-zinc-400 hover:text-zinc-200'
              }`
            }
          >
            Track report
          </NavLink>

          <div className="border-t border-zinc-800/80 pt-2 mt-2">
            {isAuthenticated ? (
              <>
                <NavLink
                  to="/moderator/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 rounded-md text-sm font-medium text-emerald-400 hover:bg-zinc-900"
                >
                  Moderator Dashboard
                </NavLink>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-3 py-2 rounded-md text-sm font-medium text-rose-400 hover:bg-rose-500/10 flex items-center gap-2 mt-1"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Log out</span>
                </button>
              </>
            ) : (
              <NavLink
                to="/moderator/login"
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2 rounded-md text-sm text-zinc-400 hover:text-zinc-200"
              >
                Moderator portal
              </NavLink>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
