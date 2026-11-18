/**
 * =============================================================================
 * StudyAI — AppShell Layout Component
 * =============================================================================
 * Orchestrates:
 * - Desktop Sidebar (240px)
 * - Sticky TopBar
 * - Mobile BottomNav
 * - Floating Study Copilot (hidden on distraction-free exam screen)
 * =============================================================================
 */

import React, { useState } from 'react';
import { useLocation, Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { BottomNav } from './BottomNav';
import { CopilotPanel, CopilotFab } from '../copilot/CopilotPanel';
import { useTheme } from '../../hooks/useTheme';
import { getActiveMaterialId } from '../../services/materialsService';

export function AppShell() {
  const location = useLocation();
  const { theme, toggleTheme, isDark } = useTheme();
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);

  // Check if current screen is the distraction-free Exam
  const isExamScreen = location.pathname.startsWith('/exam/') || location.pathname === '/exam';

  return (
    <div className="app-shell">
      {/* 1. Left Sidebar (Hidden on Exam screen) */}
      {!isExamScreen && <Sidebar isDark={isDark} toggleTheme={toggleTheme} />}

      {/* 2. Main Content Viewport */}
      <div className={`app-main ${isExamScreen ? 'no-sidebar' : ''}`}>
        {!isExamScreen && <TopBar />}

        <main className="content-container">
          <Outlet />
        </main>

        {!isExamScreen && <BottomNav />}
      </div>

      {/* 3. Floating Study Copilot (Hidden on Exam screen) */}
      {!isExamScreen && (
        <>
          <CopilotFab 
            isOpen={isCopilotOpen} 
            onClick={() => setIsCopilotOpen(!isCopilotOpen)} 
          />
          <CopilotPanel 
            isOpen={isCopilotOpen} 
            onClose={() => setIsCopilotOpen(false)} 
            materialId={getActiveMaterialId()} 
          />
        </>
      )}
    </div>
  );
}
