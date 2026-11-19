import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopNavbar from './TopNavbar';

export const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Map route path to page title
  const getPageTitle = (pathname) => {
    switch (pathname) {
      case '/':
        return 'Overview Dashboard';
      case '/students':
        return 'Student Directory & Profiles';
      case '/academic-records':
        return 'Academic Records & Dataset Ingestion';
      case '/probation':
        return 'Automated Probation Monitoring';
      case '/analytics':
        return 'Academic Performance Analytics';
      case '/reports':
        return 'Reports & Data Export';
      case '/users':
        return 'User & Access Management';
      case '/settings':
        return 'System & Threshold Settings';
      default:
        return 'AcadTrack Portal';
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg-main)', width: '100%', maxWidth: '100vw', overflowX: 'hidden' }}>
      {/* Collapsible Mobile & Desktop Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Workspace Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, width: '100%', maxWidth: '100vw', overflowX: 'hidden' }}>
        <TopNavbar
          title={getPageTitle(location.pathname)}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />
        <main className="main-content-area" style={{ flex: 1, padding: '1.5rem', overflowY: 'auto', minWidth: 0, width: '100%' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
