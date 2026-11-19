import React, { useState } from 'react';
import {
  UserCog,
  Plus,
  Shield,
  Mail,
  UserCheck,
  UserX,
  Edit2,
  CheckCircle,
  AlertCircle,
  Key,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useAuth } from '../context/AuthContext';
import Modal from '../components/common/Modal';

export const UserManagement = () => {
  const { usersList, saveUser, toggleUserStatus } = useData();
  const { isAdmin } = useAuth();

  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    user_id: '',
    name: '',
    email: '',
    role: 'lecturer',
    dev_password: 'Password@123',
    status: 'Active',
  });

  if (!isAdmin) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <AlertCircle size={48} color="#DC2626" style={{ margin: '0 auto 1rem' }} />
        <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Restricted Administrative Access</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          User management and staff account provisioning are restricted to System Administrators and Heads of Department.
        </p>
      </div>
    );
  }

  const handleOpenEdit = (user) => {
    setEditingUser(user);
    setFormData({
      user_id: user.user_id,
      name: user.name,
      email: user.email,
      role: user.role,
      dev_password: user.dev_password || 'Password@123',
      status: user.status || 'Active',
    });
  };

  const handleSave = (e) => {
    e.preventDefault();
    saveUser(formData);
    setEditingUser(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner */}
      <div
        className="action-header-stack"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Staff & System User Directory
          </h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
            Manage staff credentials, role-based access permissions, and account activation states
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => {
            setEditingUser({});
            setFormData({
              user_id: '',
              name: '',
              email: '',
              role: 'lecturer',
              dev_password: 'Password@123',
              status: 'Active',
            });
          }}
        >
          <Plus size={16} />
          Provision Staff Account
        </button>
      </div>

      {/* Users Table */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>User ID</th>
              <th>Staff Name</th>
              <th>Official Email</th>
              <th>System Role</th>
              <th style={{ textAlign: 'center' }}>Account Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {usersList.map((u) => (
              <tr key={u.user_id}>
                <td style={{ fontWeight: 700, fontFamily: 'monospace' }}>{u.user_id}</td>
                <td style={{ fontWeight: 600 }}>{u.name}</td>
                <td style={{ color: 'var(--text-secondary)' }}>{u.email}</td>
                <td>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.3rem',
                      padding: '0.2rem 0.55rem',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      backgroundColor: u.role === 'admin' ? '#E8FBF5' : '#EDF2F9',
                      color: u.role === 'admin' ? 'var(--primary-green)' : 'var(--dark-navy)',
                      textTransform: 'uppercase',
                    }}
                  >
                    <Shield size={12} />
                    {u.role}
                  </span>
                </td>
                <td style={{ textAlign: 'center' }}>
                  <span
                    style={{
                      padding: '0.2rem 0.55rem',
                      borderRadius: '999px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      backgroundColor: u.status === 'Inactive' ? '#FEE2E2' : '#DCFCE7',
                      color: u.status === 'Inactive' ? '#DC2626' : '#16A34A',
                    }}
                  >
                    {u.status || 'Active'}
                  </span>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <div style={{ display: 'inline-flex', gap: '0.35rem' }}>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                      title="Edit Account"
                      onClick={() => handleOpenEdit(u)}
                    >
                      <Edit2 size={13} />
                      Edit
                    </button>
                    <button
                      className={u.status === 'Inactive' ? 'btn btn-primary' : 'btn btn-secondary'}
                      style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                      title={u.status === 'Inactive' ? 'Activate Account' : 'Deactivate Account'}
                      onClick={() => toggleUserStatus(u.user_id)}
                    >
                      {u.status === 'Inactive' ? <UserCheck size={13} /> : <UserX size={13} />}
                      {u.status === 'Inactive' ? 'Activate' : 'Deactivate'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal: Add / Edit User */}
      <Modal
        isOpen={!!editingUser}
        onClose={() => setEditingUser(null)}
        title={editingUser?.user_id ? 'Edit Staff Credentials & Role' : 'Provision New Staff Account'}
        maxWidth="480px"
      >
        <form onSubmit={handleSave}>
          <div className="form-group">
            <label className="form-label">Full Name & Title</label>
            <input
              type="text"
              className="form-control"
              required
              placeholder="e.g. Dr. O. Adebayo"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">University Email</label>
            <input
              type="email"
              className="form-control"
              required
              placeholder="e.g. oadebayo@example.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Assigned Role</label>
            <select
              className="form-control"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            >
              <option value="lecturer">Lecturer (Course & Grade Access)</option>
              <option value="admin">Administrator (Full Institutional Access)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Temporary Initial Password</label>
            <input
              type="text"
              className="form-control"
              required
              value={formData.dev_password}
              onChange={(e) => setFormData({ ...formData, dev_password: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.25rem' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setEditingUser(null)}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Save Account
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default UserManagement;

