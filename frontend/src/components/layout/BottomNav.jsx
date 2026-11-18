/**
 * =============================================================================
 * StudyAI — Mobile Bottom Navigation (5 Key Items + More)
 * =============================================================================
 */

import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Sparkles, 
  UploadCloud, 
  GraduationCap, 
  Award, 
  RotateCcw, 
  MoreHorizontal,
  FileSearch,
  BookOpen,
  Crosshair,
  HelpCircle,
  History,
  Settings,
  X
} from 'lucide-react';

export function BottomNav() {
  const [showMore, setShowMore] = useState(false);

  const primaryItems = [
    { to: '/dashboard', label: 'Dashboard', icon: <Sparkles size={18} /> },
    { to: '/upload', label: 'Upload', icon: <UploadCloud size={18} /> },
    { to: '/my-summaries', label: 'Summaries', icon: <BookOpen size={18} /> },
    { to: '/generate-exam', label: 'Exam', icon: <GraduationCap size={18} /> },
    { to: '/results', label: 'Results', icon: <Award size={18} /> },
    { to: '/revision', label: 'Revision', icon: <RotateCcw size={18} /> }
  ];

  const moreItems = [
    { to: '/analysis', label: 'AI Analysis', icon: <FileSearch size={16} /> },
    { to: '/summary', label: 'Summary', icon: <BookOpen size={16} /> },
    { to: '/topics', label: 'Topic Intelligence', icon: <Crosshair size={16} /> },
    { to: '/questions', label: 'Question Bank', icon: <HelpCircle size={16} /> },
    { to: '/history', label: 'History', icon: <History size={16} /> },
    { to: '/settings', label: 'Settings', icon: <Settings size={16} /> }
  ];

  return (
    <>
      <nav
        className="sa-bottom-nav"
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: '64px',
          backgroundColor: 'var(--surface)',
          borderTop: '1px solid var(--border)',
          display: 'none', // Controlled via media query in CSS or inline style on mobile
          alignItems: 'center',
          justifyContent: 'space-around',
          zIndex: 90,
          padding: '0 8px'
        }}
      >
        {primaryItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            style={({ isActive }) => ({
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '3px',
              textDecoration: 'none',
              fontSize: '0.68rem',
              fontWeight: isActive ? 700 : 500,
              color: isActive ? 'var(--indigo)' : 'var(--muted)',
              minWidth: '48px'
            })}
          >
            {item.icon}
            <span>{item.label}</span>
          </NavLink>
        ))}

        <button
          type="button"
          onClick={() => setShowMore(true)}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '3px',
            background: 'transparent',
            border: 'none',
            fontSize: '0.68rem',
            color: 'var(--muted)',
            cursor: 'pointer'
          }}
        >
          <MoreHorizontal size={18} />
          <span>More</span>
        </button>
      </nav>

      {/* More Drawer */}
      {showMore && (
        <div 
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(23, 21, 43, 0.6)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'flex-end'
          }}
          onClick={() => setShowMore(false)}
        >
          <div 
            style={{
              width: '100%',
              backgroundColor: 'var(--surface)',
              borderTopLeftRadius: '20px',
              borderTopRightRadius: '20px',
              padding: '24px 20px',
              boxShadow: 'var(--shadow-lg)'
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700 }}>More Destinations</h4>
              <button onClick={() => setShowMore(false)} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
              {moreItems.map(m => (
                <NavLink
                  key={m.to}
                  to={m.to}
                  onClick={() => setShowMore(false)}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '12px 8px',
                    borderRadius: '12px',
                    backgroundColor: 'var(--bg)',
                    textDecoration: 'none',
                    color: 'var(--ink)',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    textAlign: 'center'
                  }}
                >
                  {m.icon}
                  <span>{m.label}</span>
                </NavLink>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
