/**
 * =============================================================================
 * StudyAI — Desktop Sidebar Navigation (Linear / Notion Aesthetic)
 * =============================================================================
 */

import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Sparkles,
  UploadCloud,
  FileSearch,
  BookOpen,
  GraduationCap,
  Award,
  Crosshair,
  RotateCcw,
  HelpCircle,
  History,
  Settings,
  Layers,
  Moon,
  Sun,
  ShieldCheck
} from 'lucide-react';

export function Sidebar({ isDark, toggleTheme }) {
  const location = useLocation();

  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: <Sparkles size={18} />, exact: true },
    { to: '/upload', label: '1. Upload Materials', icon: <UploadCloud size={18} />, badge: '' },
    { to: '/my-summaries', label: '2. My Summaries', icon: <BookOpen size={18} />, badge: '' },
    { to: '/generate-exam', label: '3. Generate Exam', icon: <GraduationCap size={18} /> },
    { to: '/results', label: '4. Result', icon: <Award size={18} /> },
    { to: '/revision', label: '5. Revision', icon: <RotateCcw size={18} />, badge: '' },
  ];

  const secondaryNavItems = [
    { to: '/workspace', label: 'Full Workspace', icon: <Layers size={16} /> },
    { to: '/settings', label: 'Settings', icon: <Settings size={16} /> }
  ];

  return (
    <aside
      className="sa-sidebar"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        bottom: 0,
        width: '240px',
        backgroundColor: 'var(--surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '20px 16px',
        zIndex: 100,
        overflowY: 'auto'
      }}
    >
      <div>
        {/* Brand */}
        <NavLink
          to="/dashboard"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            textDecoration: 'none',
            marginBottom: '28px',
            padding: '0 8px'
          }}
        >
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, var(--indigo), #8B5CF6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            boxShadow: 'var(--shadow-glow)'
          }}>
            <Layers size={18} />
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: '1.15rem', color: 'var(--ink)', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
              StudyAI
            </div>
            <span style={{ fontSize: '0.68rem', color: 'var(--muted)', fontWeight: 500 }}>
              Educational Intelligence
            </span>
          </div>
        </NavLink>

        {/* Friend's Menu Title */}
        <p className="menu-title" style={{ fontSize: '11px', color: 'var(--muted)', letterSpacing: '2px', margin: '0 0 10px 8px', fontWeight: 700 }}>
          MENU
        </p>

        {/* Navigation Links */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '9px 12px',
                borderRadius: 'var(--radius-btn)',
                textDecoration: 'none',
                fontSize: '0.865rem',
                fontWeight: isActive ? 700 : 500,
                color: isActive ? 'var(--indigo)' : 'var(--muted)',
                backgroundColor: isActive ? 'var(--indigo-tint)' : 'transparent',
                transition: 'all var(--transition-fast)'
              })}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {item.icon}
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span style={{
                  fontSize: '0.66rem',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '999px',
                  background: 'var(--surface)',
                  color: 'var(--indigo)',
                  border: '1px solid rgba(79, 63, 240, 0.2)'
                }}>
                  {item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Secondary Links */}
        <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px dashed var(--border)' }}>
          <p style={{ fontSize: '10px', color: 'var(--muted)', letterSpacing: '1.5px', margin: '0 0 6px 8px', fontWeight: 700 }}>
            MORE
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            {secondaryNavItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '7px 12px',
                  borderRadius: 'var(--radius-btn)',
                  textDecoration: 'none',
                  fontSize: '0.82rem',
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? 'var(--indigo)' : 'var(--muted)',
                  backgroundColor: isActive ? 'var(--indigo-tint)' : 'transparent',
                  transition: 'all var(--transition-fast)'
                })}
              >
                {item.icon}
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      </div>

      {/* Footer Info & Theme Toggle */}
      <div style={{ paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
        <div className="sidebar-bottom" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <p style={{ fontWeight: 600, fontSize: '0.82rem', margin: '0 0 2px 0', color: 'var(--ink)' }}>AI-powered learning</p>
            <small style={{ color: 'var(--muted)', fontSize: '0.74rem' }}>Learn smarter, every day.</small>
          </div>
          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle light/dark theme"
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--muted)',
              padding: '6px',
              borderRadius: '8px'
            }}
          >
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </div>
    </aside>
  );
}
