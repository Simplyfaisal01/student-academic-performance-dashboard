import React, { useState } from 'react';
import {
  Bell,
  ChevronDown,
  LogOut,
  Calendar,
  AlertTriangle,
  CheckCircle,
  Menu,
  Shield,
  User,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useData } from '../../context/DataContext';

export const TopNavbar = ({ onToggleSidebar, title }) => {
  const { user, logout, switchRole, isAdmin, canSwitchRole } = useAuth();
  const {
    semesters,
    selectedSemesterId,
    setSelectedSemesterId,
    currentSemesterEvaluations,
  } = useData();

  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showNotificationMenu, setShowNotificationMenu] = useState(false);

  // Active notifications (probation & at-risk flags for the active semester)
  const flaggedStudents = currentSemesterEvaluations.filter((e) => e.isFlagged);
  const unreadCount = flaggedStudents.length;

  return (
    <header
      className="top-navbar-header"
      style={{
        height: '64px',
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid var(--border-color)',
        padding: '0 1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 40,
        gap: '0.5rem',
      }}
    >
      {/* Left: Mobile hamburger & Page Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', minWidth: 0, flex: '1 1 auto' }}>
        <button
          onClick={onToggleSidebar}
          className="mobile-menu-btn"
          aria-label="Toggle navigation drawer"
        >
          <Menu size={22} />
        </button>
        <h1
          className="page-title-text"
          style={{
            fontSize: '1.25rem',
            fontWeight: 800,
            color: 'var(--text-primary)',
            margin: 0,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {title || 'Dashboard'}
        </h1>
      </div>

      {/* Right Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
        {/* Semester / Session Selector */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            backgroundColor: '#F8FAFC',
            padding: '0.35rem 0.55rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-color)',
            maxWidth: '180px',
          }}
        >
          <Calendar size={15} color="var(--primary-green)" style={{ flexShrink: 0 }} />
          <select
            value={selectedSemesterId}
            onChange={(e) => setSelectedSemesterId(Number(e.target.value))}
            className="semester-select-text"
            style={{
              background: 'transparent',
              border: 'none',
              fontSize: '0.8125rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
              cursor: 'pointer',
              outline: 'none',
              maxWidth: '145px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {semesters.map((sem) => (
              <option key={sem.semester_id} value={sem.semester_id}>
                {sem.session} — {sem.name} {sem.is_current ? '(Current)' : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Notifications Dropdown */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => {
              setShowNotificationMenu(!showNotificationMenu);
              setShowProfileMenu(false);
            }}
            aria-label="Notifications"
            style={{
              position: 'relative',
              background: '#F8FAFC',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              width: 38,
              height: 38,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              flexShrink: 0,
            }}
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  top: -4,
                  right: -4,
                  backgroundColor: '#DC2626',
                  color: '#FFFFFF',
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  width: 18,
                  height: 18,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {showNotificationMenu && (
            <div
              className="dropdown-responsive-menu"
              style={{
                position: 'absolute',
                right: 0,
                top: '48px',
                width: '340px',
                maxWidth: 'calc(100vw - 1.5rem)',
                backgroundColor: '#FFFFFF',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-lg)',
                border: '1px solid var(--border-color)',
                padding: '0.75rem',
                zIndex: 100,
              }}
            >
              <div
                style={{
                  padding: '0.5rem 0.5rem 0.75rem',
                  borderBottom: '1px solid var(--border-color)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>Automated Alerts</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--primary-green)', fontWeight: 600 }}>
                  {unreadCount} flagged
                </span>
              </div>
              <div style={{ maxHeight: '280px', overflowY: 'auto', padding: '0.25rem 0' }}>
                {flaggedStudents.length === 0 ? (
                  <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>
                    <CheckCircle size={28} color="#16A34A" style={{ margin: '0 auto 0.5rem' }} />
                    No probation alerts for this semester
                  </div>
                ) : (
                  flaggedStudents.slice(0, 5).map((ev) => (
                    <div
                      key={ev.matric_no}
                      style={{
                        padding: '0.65rem',
                        borderBottom: '1px solid var(--border-light)',
                        display: 'flex',
                        gap: '0.65rem',
                        alignItems: 'flex-start',
                      }}
                    >
                      <AlertTriangle size={16} color="#DC2626" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <div style={{ fontSize: '0.8125rem' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                          {ev.name} ({ev.matric_no})
                        </div>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                          GPA: {ev.gpa !== null ? ev.gpa.toFixed(2) : 'N/A'} • {ev.standing}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Profile Menu */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => {
              setShowProfileMenu(!showProfileMenu);
              setShowNotificationMenu(false);
            }}
            aria-label="User profile menu"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: '#F8FAFC',
              border: '1px solid var(--border-color)',
              padding: '0.35rem 0.55rem',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              flexShrink: 0,
            }}
          >
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                backgroundColor: 'var(--primary-green)',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '0.8125rem',
                flexShrink: 0,
              }}
            >
              {user?.name?.charAt(0) || 'U'}
            </div>
            <ChevronDown size={14} color="var(--text-secondary)" />
          </button>

          {showProfileMenu && (
            <div
              className="profile-dropdown-menu"
              style={{
                position: 'absolute',
                right: 0,
                top: '48px',
                width: '240px',
                maxWidth: 'calc(100vw - 1.5rem)',
                backgroundColor: '#FFFFFF',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-lg)',
                border: '1px solid var(--border-color)',
                padding: '0.5rem',
                zIndex: 100,
              }}
            >
              <div style={{ padding: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>
                <div style={{ fontWeight: 700, fontSize: '0.875rem' }}>{user?.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {user?.email}
                </div>
                <span
                  style={{
                    display: 'inline-block',
                    marginTop: '0.35rem',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '4px',
                    backgroundColor: 'var(--secondary-green-light)',
                    color: 'var(--primary-green)',
                    fontSize: '0.6875rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                  }}
                >
                  {user?.role} Role
                </span>
              </div>

              {/* Role preview: only available for Administrator accounts to preview Lecturer view */}
              {canSwitchRole && (
                <div style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-secondary)', padding: '0 0.5rem 0.25rem' }}>
                    ROLE PREVIEW (ADMIN ONLY)
                  </div>
                  <button
                    onClick={() => switchRole(isAdmin ? 'lecturer' : 'admin')}
                    style={{
                      width: '100%',
                      padding: '0.45rem 0.5rem',
                      textAlign: 'left',
                      background: 'none',
                      border: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      borderRadius: '4px',
                    }}
                    onMouseEnter={(e) => (e.target.style.backgroundColor = '#F8FAFC')}
                    onMouseLeave={(e) => (e.target.style.backgroundColor = 'transparent')}
                  >
                    <Shield size={14} color="var(--primary-green)" />
                    {isAdmin ? 'Preview as Lecturer' : 'Switch back to Administrator'}
                  </button>
                </div>
              )}

              <div style={{ paddingTop: '0.25rem' }}>
                <button
                  onClick={logout}
                  style={{
                    width: '100%',
                    padding: '0.45rem 0.5rem',
                    textAlign: 'left',
                    background: 'none',
                    border: 'none',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    color: '#DC2626',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    borderRadius: '4px',
                  }}
                  onMouseEnter={(e) => (e.target.style.backgroundColor = '#FEE2E2')}
                  onMouseLeave={(e) => (e.target.style.backgroundColor = 'transparent')}
                >
                  <LogOut size={14} />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default TopNavbar;
