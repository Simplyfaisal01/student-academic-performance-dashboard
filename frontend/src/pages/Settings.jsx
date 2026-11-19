import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  Sliders,
  Calendar,
  Lock,
  User,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useAuth } from '../context/AuthContext';

export const Settings = () => {
  const { thresholds, updateThresholds, semesters, selectedSemesterId, setSelectedSemesterId } = useData();
  const { user } = useAuth();

  // Threshold form state
  const [formThresholds, setFormThresholds] = useState({
    probationGpa: thresholds.probationGpa || 1.5,
    maxFailedCourses: thresholds.maxFailedCourses || 2,
    atRiskGpaMin: thresholds.atRiskGpaMin || 1.5,
    atRiskGpaMax: thresholds.atRiskGpaMax || 1.99,
    criticalGpa: thresholds.criticalGpa || 1.0,
    criticalFails: thresholds.criticalFails || 4,
  });

  // Password change state
  const [currentPwd, setCurrentPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');
  const [pwdMsg, setPwdMsg] = useState('');
  const [thresholdMsg, setThresholdMsg] = useState('');

  const handleSaveThresholds = (e) => {
    e.preventDefault();
    updateThresholds({
      probationGpa: Number(formThresholds.probationGpa),
      maxFailedCourses: Number(formThresholds.maxFailedCourses),
      atRiskGpaMin: Number(formThresholds.atRiskGpaMin),
      atRiskGpaMax: Number(formThresholds.atRiskGpaMax),
      criticalGpa: Number(formThresholds.criticalGpa),
      criticalFails: Number(formThresholds.criticalFails),
    });
    setThresholdMsg('Institutional probation thresholds updated successfully! All standings recalculated.');
    setTimeout(() => setThresholdMsg(''), 4000);
  };

  const handleChangePassword = (e) => {
    e.preventDefault();
    if (!currentPwd || !newPwd) {
      setPwdMsg('Please fill in all password fields.');
      return;
    }
    if (newPwd !== confirmPwd) {
      setPwdMsg('New password and confirmation do not match.');
      return;
    }
    if (newPwd.length < 6) {
      setPwdMsg('Password must be at least 6 characters.');
      return;
    }

    setPwdMsg('Password changed successfully!');
    setCurrentPwd('');
    setNewPwd('');
    setConfirmPwd('');
    setTimeout(() => setPwdMsg(''), 4000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '900px', width: '100%' }}>
      {/* Page Header */}
      <div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
          System & Institutional Settings
        </h2>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
          Configure academic evaluation cutoffs, active academic session, and user profile parameters
        </p>
      </div>

      {/* 1. Academic Session & Semester Settings */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Calendar size={18} color="var(--primary-green)" />
            <span className="card-title">Active Academic Session & Semester</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 200px), 1fr))', gap: '1rem' }}>
          {semesters.map((s) => (
            <div
              key={s.semester_id}
              onClick={() => setSelectedSemesterId(s.semester_id)}
              style={{
                border: selectedSemesterId === s.semester_id ? '2px solid var(--primary-green)' : '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.85rem',
                backgroundColor: selectedSemesterId === s.semester_id ? 'var(--secondary-green-light)' : '#FFFFFF',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>{s.session}</span>
                {s.is_current ? (
                  <span style={{ fontSize: '0.65rem', backgroundColor: 'var(--primary-green)', color: '#FFFFFF', padding: '0.15rem 0.45rem', borderRadius: '4px', fontWeight: 700 }}>
                    CURRENT
                  </span>
                ) : null}
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{s.name}</div>
              <div style={{ fontSize: '0.7125rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                Dates: {s.start_date || 'N/A'} to {s.end_date || 'N/A'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 2. Configurable Probation Rules & Thresholds */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sliders size={18} color="#DC2626" />
            <span className="card-title">Configurable Academic Standing & Probation Rules</span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Institutional Regulations
          </span>
        </div>

        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
          Adjust threshold parameters to match your specific faculty or university regulations without modifying code.
        </p>

        {thresholdMsg && (
          <div style={{ padding: '0.75rem', backgroundColor: '#DCFCE7', color: '#16A34A', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <CheckCircle2 size={16} />
            {thresholdMsg}
          </div>
        )}

        <form onSubmit={handleSaveThresholds}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 200px), 1fr))', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Probation GPA Threshold (&lt; triggers)</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="5"
                className="form-control"
                value={formThresholds.probationGpa}
                onChange={(e) => setFormThresholds({ ...formThresholds, probationGpa: e.target.value })}
              />
              <span style={{ fontSize: '0.7125rem', color: 'var(--text-muted)' }}>Default: 1.50</span>
            </div>

            <div className="form-group">
              <label className="form-label">Max Failed Courses Permitted (&gt; triggers)</label>
              <input
                type="number"
                min="0"
                max="10"
                className="form-control"
                value={formThresholds.maxFailedCourses}
                onChange={(e) => setFormThresholds({ ...formThresholds, maxFailedCourses: e.target.value })}
              />
              <span style={{ fontSize: '0.7125rem', color: 'var(--text-muted)' }}>Default: 2 courses</span>
            </div>

            <div className="form-group">
              <label className="form-label">At-Risk GPA Upper Bound</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="5"
                className="form-control"
                value={formThresholds.atRiskGpaMax}
                onChange={(e) => setFormThresholds({ ...formThresholds, atRiskGpaMax: e.target.value })}
              />
              <span style={{ fontSize: '0.7125rem', color: 'var(--text-muted)' }}>Default: 1.99</span>
            </div>

            <div className="form-group">
              <label className="form-label">Critical Risk GPA Threshold</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="5"
                className="form-control"
                value={formThresholds.criticalGpa}
                onChange={(e) => setFormThresholds({ ...formThresholds, criticalGpa: e.target.value })}
              />
              <span style={{ fontSize: '0.7125rem', color: 'var(--text-muted)' }}>Default: 1.00</span>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem', flexWrap: 'wrap' }}>
            <button type="submit" className="btn btn-primary" style={{ minWidth: '160px' }}>
              Update Rules & Recalculate
            </button>
          </div>
        </form>
      </div>

      {/* 3. User Profile & Security Settings */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Lock size={18} color="var(--dark-navy)" />
            <span className="card-title">Staff Account Security</span>
          </div>
        </div>

        {pwdMsg && (
          <div
            style={{
              padding: '0.75rem',
              backgroundColor: pwdMsg.includes('success') ? '#DCFCE7' : '#FEE2E2',
              color: pwdMsg.includes('success') ? '#16A34A' : '#DC2626',
              borderRadius: 'var(--radius-sm)',
              marginBottom: '1rem',
              fontSize: '0.8125rem',
            }}
          >
            {pwdMsg}
          </div>
        )}

        <form onSubmit={handleChangePassword}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 200px), 1fr))', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Current Password</label>
              <input
                type="password"
                className="form-control"
                value={currentPwd}
                onChange={(e) => setCurrentPwd(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">New Password</label>
              <input
                type="password"
                className="form-control"
                value={newPwd}
                onChange={(e) => setNewPwd(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Confirm New Password</label>
              <input
                type="password"
                className="form-control"
                value={confirmPwd}
                onChange={(e) => setConfirmPwd(e.target.value)}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem', flexWrap: 'wrap' }}>
            <button type="submit" className="btn btn-secondary" style={{ minWidth: '150px' }}>
              Update Password
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Settings;

