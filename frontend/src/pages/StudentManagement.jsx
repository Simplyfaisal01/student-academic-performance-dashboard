import React, { useState, useMemo } from 'react';
import {
  Search,
  Filter,
  Eye,
  Edit2,
  Trash2,
  Plus,
  GraduationCap,
  Mail,
  UserCheck,
  Calendar,
  AlertCircle,
  BookOpen,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/common/StatusBadge';
import Modal from '../components/common/Modal';

export const StudentManagement = () => {
  const {
    students,
    courses,
    advisorMap,
    currentSemesterEvaluations,
    studentEvaluations,
    saveStudent,
    deleteStudent,
  } = useData();
  const { isAdmin } = useAuth();

  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState('all');
  const [standingFilter, setStandingFilter] = useState('all');

  // Modal states
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [editingStudent, setEditingStudent] = useState(null);
  const [studentToDelete, setStudentToDelete] = useState(null);

  // Form state for edit/add
  const [formData, setFormData] = useState({
    matric_no: '',
    name: '',
    level: 100,
    email: '',
    advisor_id: 'U002',
  });

  // Combine student details with current evaluation standing
  const enrichedStudents = useMemo(() => {
    const evalMap = new Map();
    currentSemesterEvaluations.forEach((ev) => evalMap.set(ev.student_id, ev));

    return students.map((st) => {
      const evaluation = evalMap.get(st.student_id) || {
        standing: 'Good Standing',
        gpa: null,
        reasons: [],
      };
      return {
        ...st,
        standing: evaluation.standing,
        gpa: evaluation.gpa,
        reasons: evaluation.reasons,
        advisorName: advisorMap.get(st.advisor_id)?.name || 'Departmental Advisor',
      };
    });
  }, [students, currentSemesterEvaluations, advisorMap]);

  // Filter and search
  const filteredStudents = useMemo(() => {
    return enrichedStudents.filter((st) => {
      const matchesSearch =
        st.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        st.matric_no?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        st.email?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesLevel =
        levelFilter === 'all' || String(st.level) === String(levelFilter);

      const matchesStanding =
        standingFilter === 'all' || st.standing === standingFilter;

      return matchesSearch && matchesLevel && matchesStanding;
    });
  }, [enrichedStudents, searchTerm, levelFilter, standingFilter]);

  const handleOpenEdit = (student) => {
    setEditingStudent(student);
    setFormData({
      student_id: student.student_id,
      matric_no: student.matric_no,
      name: student.name,
      level: student.level,
      email: student.email,
      advisor_id: student.advisor_id,
    });
  };

  const handleSaveStudent = (e) => {
    e.preventDefault();
    saveStudent(formData);
    setEditingStudent(null);
  };

  const handleDeleteConfirm = () => {
    if (studentToDelete) {
      deleteStudent(studentToDelete.student_id);
      setStudentToDelete(null);
    }
  };

  // Get student's academic history across all semesters
  const studentHistory = useMemo(() => {
    if (!selectedStudent) return [];
    return studentEvaluations.filter((ev) => ev.student_id === selectedStudent.student_id);
  }, [selectedStudent, studentEvaluations]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Action Header */}
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
            Student Registry & Academic Profiles
          </h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
            Showing {filteredStudents.length} of {students.length} students enrolled in the department
          </p>
        </div>

        {isAdmin && (
          <button
            className="btn btn-primary"
            style={{ flexShrink: 0 }}
            onClick={() => {
              setEditingStudent({});
              setFormData({ matric_no: '', name: '', level: 100, email: '', advisor_id: 'U002' });
            }}
          >
            <Plus size={16} />
            Add New Student
          </button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div
        className="card"
        style={{
          padding: '1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          flexWrap: 'wrap',
        }}
      >
        {/* Search */}
        <div style={{ flex: '1 1 240px', position: 'relative', minWidth: '180px' }}>
          <Search
            size={16}
            color="var(--text-muted)"
            style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }}
          />
          <input
            type="text"
            className="form-control"
            style={{ paddingLeft: '36px' }}
            placeholder="Search by student name, matric no..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Level Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flex: '0 1 auto' }}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
            Level:
          </span>
          <select
            className="form-control"
            style={{ width: 'auto', minWidth: '110px' }}
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
          >
            <option value="all">All Levels</option>
            <option value="100">100 Level</option>
            <option value="200">200 Level</option>
            <option value="300">300 Level</option>
            <option value="400">400 Level</option>
          </select>
        </div>

        {/* Standing Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flex: '0 1 auto' }}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
            Standing:
          </span>
          <select
            className="form-control"
            style={{ width: 'auto', minWidth: '130px' }}
            value={standingFilter}
            onChange={(e) => setStandingFilter(e.target.value)}
          >
            <option value="all">All Standings</option>
            <option value="Good Standing">Good Standing</option>
            <option value="At Risk">At Risk</option>
            <option value="Probation">Probation</option>
            <option value="Critical Risk">Critical Risk</option>
          </select>
        </div>
      </div>

      {/* Main Student Table */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Matric No</th>
              <th>Student Name</th>
              <th>Level</th>
              <th>Academic Advisor</th>
              <th>Current GPA</th>
              <th>Academic Standing</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredStudents.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-secondary)' }}>
                  No student records matched your filter criteria.
                </td>
              </tr>
            ) : (
              filteredStudents.map((st) => (
                <tr key={st.student_id}>
                  <td style={{ fontWeight: 700, fontFamily: 'monospace', color: 'var(--text-primary)' }}>
                    {st.matric_no}
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{st.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{st.email}</div>
                  </td>
                  <td>
                    <span style={{ fontWeight: 600 }}>{st.level} Level</span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>
                    {st.advisorName}
                  </td>
                  <td style={{ fontWeight: 700, fontSize: '0.95rem' }}>
                    {st.gpa !== null ? st.gpa.toFixed(2) : '—'}
                  </td>
                  <td>
                    <StatusBadge standing={st.standing} />
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '0.35rem' }}>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                        title="View Academic Profile"
                        onClick={() => setSelectedStudent(st)}
                      >
                        <Eye size={14} />
                        Profile
                      </button>
                      {isAdmin && (
                        <>
                          <button
                            className="btn btn-secondary"
                            style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                            title="Edit Student"
                            onClick={() => handleOpenEdit(st)}
                          >
                            <Edit2 size={14} />
                          </button>
                          <button
                            className="btn btn-danger"
                            style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                            title="Delete Student"
                            onClick={() => setStudentToDelete(st)}
                          >
                            <Trash2 size={14} />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal 1: Student Profile & Complete Academic History */}
      <Modal
        isOpen={!!selectedStudent}
        onClose={() => setSelectedStudent(null)}
        title="Student Academic Profile"
        maxWidth="750px"
      >
        {selectedStudent && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Header info */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 180px), 1fr))',
                gap: '1rem',
                backgroundColor: '#F8FAFC',
                padding: '1rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
              }}
            >
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600 }}>NAME:</span>
                <div style={{ fontWeight: 800, fontSize: '1rem' }}>{selectedStudent.name}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600 }}>MATRIC NUMBER:</span>
                <div style={{ fontWeight: 800, fontFamily: 'monospace' }}>{selectedStudent.matric_no}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600 }}>CURRENT LEVEL:</span>
                <div style={{ fontWeight: 700 }}>{selectedStudent.level} Level</div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600 }}>ASSIGNED ADVISOR:</span>
                <div style={{ fontWeight: 600 }}>{selectedStudent.advisorName}</div>
              </div>
            </div>

            {/* Academic History Timeline */}
            <div>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
                Semester Academic History
              </h4>

              {studentHistory.length === 0 ? (
                <div style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  No graded semester history on file.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {studentHistory.map((hist) => (
                    <div
                      key={hist.semester_id}
                      style={{
                        border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '0.85rem',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          marginBottom: '0.5rem',
                          borderBottom: '1px solid var(--border-light)',
                          paddingBottom: '0.4rem',
                        }}
                      >
                        <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>
                          {hist.semester_name}
                        </span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <span style={{ fontSize: '0.8125rem', fontWeight: 700 }}>
                            GPA: {hist.gpa !== null ? hist.gpa.toFixed(2) : 'N/A'}
                          </span>
                          <StatusBadge standing={hist.standing} />
                        </div>
                      </div>

                      {/* Course breakdown for this semester */}
                      <div className="data-table-container">
                        <table style={{ width: '100%', fontSize: '0.8125rem', borderCollapse: 'collapse' }}>
                          <thead>
                            <tr style={{ color: 'var(--text-secondary)', borderBottom: '1px solid #F1F5F9' }}>
                              <th style={{ textAlign: 'left', padding: '0.35rem 0' }}>Course</th>
                              <th style={{ textAlign: 'center', padding: '0.35rem 0' }}>Units</th>
                              <th style={{ textAlign: 'center', padding: '0.35rem 0' }}>Score</th>
                              <th style={{ textAlign: 'center', padding: '0.35rem 0' }}>Grade</th>
                            </tr>
                          </thead>
                          <tbody>
                            {hist.enrollments?.map((e) => (
                              <tr key={e.enrollment_id} style={{ borderBottom: '1px solid #F8FAFC' }}>
                                <td style={{ padding: '0.35rem 0', fontWeight: 600 }}>
                                  {e.course_code} - {e.course_title}
                                </td>
                                <td style={{ textAlign: 'center', padding: '0.35rem 0' }}>{e.credit_units}</td>
                                <td style={{ textAlign: 'center', padding: '0.35rem 0', fontWeight: 700 }}>{e.score}</td>
                                <td
                                  style={{
                                    textAlign: 'center',
                                    padding: '0.35rem 0',
                                    fontWeight: 800,
                                    color: e.grade === 'F' ? '#DC2626' : 'var(--text-primary)',
                                  }}
                                >
                                  {e.grade}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* Modal 2: Edit / Add Student */}
      <Modal
        isOpen={!!editingStudent}
        onClose={() => setEditingStudent(null)}
        title={editingStudent?.student_id ? 'Edit Student Details' : 'Add New Student'}
        maxWidth="500px"
      >
        <form onSubmit={handleSaveStudent}>
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input
              type="text"
              className="form-control"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Matric Number</label>
            <input
              type="text"
              className="form-control"
              required
              placeholder="e.g. FT24BCMP0001"
              value={formData.matric_no}
              onChange={(e) => setFormData({ ...formData, matric_no: e.target.value })}
            />
          </div>

          <div className="grid-form-2">
            <div className="form-group">
              <label className="form-label">Level</label>
              <select
                className="form-control"
                value={formData.level}
                onChange={(e) => setFormData({ ...formData, level: Number(e.target.value) })}
              >
                <option value={100}>100 Level</option>
                <option value={200}>200 Level</option>
                <option value={300}>300 Level</option>
                <option value={400}>400 Level</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Advisor</label>
              <select
                className="form-control"
                value={formData.advisor_id}
                onChange={(e) => setFormData({ ...formData, advisor_id: e.target.value })}
              >
                <option value="U001">Dr. A. Dike</option>
                <option value="U002">Prof. M. Abdullahi</option>
                <option value="U003">Dr. S. Okonkwo</option>
                <option value="U004">Dr. H. Garba</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input
              type="email"
              className="form-control"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setEditingStudent(null)}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Save Student Record
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal 3: Delete Confirmation */}
      <Modal
        isOpen={!!studentToDelete}
        onClose={() => setStudentToDelete(null)}
        title="Confirm Student Deletion"
        maxWidth="440px"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <div style={{ width: 40, height: 40, borderRadius: '50%', backgroundColor: '#FEE2E2', color: '#DC2626', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <AlertCircle size={22} />
            </div>
            <div>
              <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                Delete {studentToDelete?.name}?
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                Matric No: {studentToDelete?.matric_no}
              </div>
            </div>
          </div>

          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Are you sure you want to delete this student record? This will permanently remove
            their profile and associated enrollments.
          </p>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setStudentToDelete(null)}
            >
              Cancel
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={handleDeleteConfirm}
            >
              Delete Permanently
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default StudentManagement;

