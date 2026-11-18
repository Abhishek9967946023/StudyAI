# 💻 Frontend Subsystem (Member 2: Frontend Developer)

Welcome to the **StudyAI Frontend** module. This directory contains the complete React 19 single-page application built on Vite, with modern glassmorphic UI, responsive layouts, interactive charts, and API client integrations.

---

## 👥 Module Ownership: Member 2 (Frontend Developer)
- **Primary Responsibility**: UI/UX design, React components, state management (`AuthContext`), navigation routing, interactive charts (Heatmap, Priority Matrix, Radar Chart), Copilot assistant, and API integrations with backend.
- **Key Files & Folders**:
  - `src/main.jsx`: Vite React root rendering.
  - `src/App.jsx`: Global router and layout provider.
  - `src/pages/`:
    - `Landing.jsx`: Product landing hero & feature highlights.
    - `Dashboard.jsx`: Student analytics, streak counter, upcoming exams, priority matrix.
    - `Upload.jsx`: Multi-document ingestion dropzone with PDF/DOCX preview.
    - `Summary.jsx`: Hierarchical study notes viewer with Mermaid flowcharts & flashcards.
    - `MySummaries.jsx`: History of generated revision notes.
    - `Settings.jsx`: Server-configured AI provider status, local Ollama model display, and preferences.
    - `auth/Login.jsx` & `auth/Register.jsx`: User authentication screens.
  - `src/components/`:
    - `layout/`: `TopBar.jsx`, `Sidebar.jsx`, `BottomNav.jsx`, `AppShell.jsx`.
    - `charts/`: `Heatmap.jsx`, `PriorityMatrix.jsx`, `RadarChart.jsx`, `TrendBars.jsx`.
    - `copilot/`: `CopilotPanel.jsx` (interactive AI tutor assistant).
    - `ui/`: Buttons, Cards, Modal dialogs, Chips, Badges.
  - `src/services/apiClient.js`: Centralized API client handling requests to `http://127.0.0.1:8000`.
  - `src/context/AuthContext.jsx`: Authentication state, user profile, and session management.

---

## 🚀 Quick Setup for Member 2

### 1. Install Dependencies (if not already installed)
```bash
cd frontend
npm install
```

### 2. Start the Vite Development Server
```bash
npm run dev
```
The React frontend will be accessible at `http://127.0.0.1:5173/`.

### 3. Production Build
```bash
npm run build
```

---

## 🎨 Design & Styling Guidelines
- **Color Tokens**: CSS custom variables defined in `src/index.css`.
- **Glassmorphism**: Backdrop blur with subtle borders for high-end dark/light themes.
- **Icons**: [Lucide React](https://lucide.dev/) icon set.
- **Charts & Diagrams**: Custom SVG charts and [Mermaid.js](https://mermaid.js.org/) for educational concepts.
