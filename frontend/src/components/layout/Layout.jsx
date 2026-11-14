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
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg-main)' }}>
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Workspace Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <TopNavbar
          title={getPageTitle(location.pathname)}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />
        <main style={{ flex: 1, padding: '1.5rem', overflowY: 'auto' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;

