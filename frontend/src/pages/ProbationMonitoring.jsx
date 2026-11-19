import React, { useState, useMemo } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle,
  FileText,
  Search,
  Filter,
  Eye,
  Edit3,
  Calendar,
  Clock,
  UserCheck,
  ShieldAlert,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/common/StatusBadge';
import Modal from '../components/common/Modal';

export const ProbationMonitoring = () => {
  const {
    currentSemesterEvaluations,
    studentEvaluations,
    selectedSemesterId,
    semesters,
    recordPanelDecision,
    thresholds,
  } = useData();
  const { user, isAdmin } = useAuth();

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [levelFilter, setLevelFilter] = useState('all');

  // Modal states
  const [selectedCase, setSelectedCase] = useState(null);
  const [decisionModalStudent, setDecisionModalStudent] = useState(null);

  // Decision form state
  const [decisionForm, setDecisionForm] = useState({
    status: 'Probation',
    panelNotes: '',
    actionPlan: '',
    reviewDate: '',
    panelMembers: 'Departmental Academic Board',
  });

  // Filter students based on status and search
  const flaggedEvaluations = useMemo(() => {
    return currentSemesterEvaluations.filter((ev) => {
      const matchesSearch =
        ev.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ev.matric_no.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus =
        statusFilter === 'all'
          ? ev.isFlagged
          : statusFilter === 'all_students'
          ? true
          : ev.standing === statusFilter;

      const matchesLevel =
        levelFilter === 'all' || String(ev.level) === String(levelFilter);

      return matchesSearch && matchesStatus && matchesLevel;
    });
  }, [currentSemesterEvaluations, searchTerm, statusFilter, levelFilter]);

  // Handle recording panel decision
  const handleOpenDecision = (studentCase) => {
    setDecisionModalStudent(studentCase);
    setDecisionForm({
      status: studentCase.standing,
      panelNotes: studentCase.panelDecision?.panelNotes || '',
      actionPlan: studentCase.panelDecision?.actionPlan || 'Schedule mandatory advising session & reduce course load',
      reviewDate: studentCase.panelDecision?.reviewDate || new Date().toISOString().split('T')[0],
      panelMembers: studentCase.panelDecision?.panelMembers || 'Academic Board Panel',
    });
  };

  const handleSaveDecision = (e) => {
    e.preventDefault();
    if (!decisionModalStudent) return;
    recordPanelDecision(decisionModalStudent.student_id, selectedSemesterId, decisionForm);
    alert('Academic panel decision recorded successfully!');
    setDecisionModalStudent(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner with Threshold Reminder */}
      <div
        className="card action-header-stack"
        style={{
          backgroundColor: '#FFFFFF',
          borderLeft: '4px solid #DC2626',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <ShieldAlert size={20} color="#DC2626" style={{ flexShrink: 0 }} />
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Automated Academic Probation & Standing Monitor
            </h2>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
            Configured Active Rules: Flag if GPA &lt; {thresholds.probationGpa.toFixed(2)} OR failed courses &gt; {thresholds.maxFailedCourses}.
            Assistive monitoring tool for institutional academic review committees.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <span
            style={{
              padding: '0.35rem 0.75rem',
              backgroundColor: '#FEE2E2',
              color: '#DC2626',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.8125rem',
              fontWeight: 700,
              whiteSpace: 'nowrap',
            }}
          >
            {flaggedEvaluations.length} Cases Under Review
          </span>
        </div>
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
            placeholder="Search flagged students..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Classification Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flex: '0 1 auto' }}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
            Status:
          </span>
          <select
            className="form-control"
            style={{ width: 'auto', minWidth: '130px' }}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Flagged Cases</option>
            <option value="Probation">Probation Only</option>
            <option value="Critical Risk">Critical Risk Only</option>
            <option value="At Risk">At Risk Warning</option>
            <option value="all_students">All Students in Session</option>
          </select>
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
      </div>

      {/* Main Probation Registry Table */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Matric No</th>
              <th>Student Name</th>
              <th>Level</th>
              <th>Advisor</th>
              <th style={{ textAlign: 'center' }}>Semester GPA</th>
              <th style={{ textAlign: 'center' }}>Fails</th>
              <th>Automated Audit Reason</th>
              <th>Academic Standing</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {flaggedEvaluations.length === 0 ? (
              <tr>
                <td colSpan="9" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-secondary)' }}>
                  <CheckCircle size={32} color="#16A34A" style={{ margin: '0 auto 0.5rem' }} />
                  No students meet the probation / at-risk criteria for the selected filters.
                </td>
              </tr>
            ) : (
              flaggedEvaluations.map((ev) => (
                <tr key={`${ev.student_id}_${ev.semester_id}`}>
                  <td style={{ fontWeight: 700, fontFamily: 'monospace' }}>{ev.matric_no}</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{ev.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{ev.email}</div>
                  </td>
                  <td>{ev.level}L</td>
                  <td style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{ev.advisor_name}</td>
                  <td
                    style={{
                      textAlign: 'center',
                      fontWeight: 800,
                      color: ev.gpa < 1.5 ? '#DC2626' : 'var(--text-primary)',
                      fontSize: '0.95rem',
                    }}
                  >
                    {ev.gpa !== null ? ev.gpa.toFixed(2) : '—'}
                  </td>
                  <td
                    style={{
                      textAlign: 'center',
                      fontWeight: 700,
                      color: ev.failed_courses > 2 ? '#DC2626' : 'var(--text-secondary)',
                    }}
                  >
                    {ev.failed_courses}
                  </td>
                  <td style={{ fontSize: '0.8125rem', maxWidth: '280px' }}>
                    <div style={{ color: '#DC2626', fontWeight: 600 }}>
                      {ev.reasons.join('; ')}
                    </div>
                    {ev.panelDecision && (
                      <div style={{ fontSize: '0.7125rem', color: '#087B5B', marginTop: '2px', fontWeight: 600 }}>
                        Panel Action: {ev.panelDecision.actionPlan}
                      </div>
                    )}
                  </td>
                  <td>
                    <StatusBadge standing={ev.standing} />
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '0.35rem' }}>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                        title="View Case Details"
                        onClick={() => setSelectedCase(ev)}
                      >
                        <Eye size={14} />
                        Details
                      </button>
                      {isAdmin && (
                        <button
                          className="btn btn-primary"
                          style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                          title="Record Panel Decision"
                          onClick={() => handleOpenDecision(ev)}
                        >
                          <Edit3 size={14} />
                          Panel
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal 1: Case Detail Modal */}
      <Modal
        isOpen={!!selectedCase}
        onClose={() => setSelectedCase(null)}
        title="Probation Case Audit & Academic History"
        maxWidth="680px"
      >
        {selectedCase && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div
              style={{
                padding: '1rem',
                backgroundColor: '#F8FAFC',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 160px), 1fr))',
                gap: '0.75rem',
              }}
            >
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>STUDENT:</span>
                <div style={{ fontWeight: 800 }}>{selectedCase.name}</div>
                <div style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>{selectedCase.matric_no}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>SEMESTER GPA:</span>
                <div style={{ fontWeight: 800, fontSize: '1.1rem', color: '#DC2626' }}>
                  {selectedCase.gpa !== null ? selectedCase.gpa.toFixed(2) : 'N/A'}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>CURRENT STANDING:</span>
                <div><StatusBadge standing={selectedCase.standing} /></div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>ADVISOR:</span>
                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{selectedCase.advisor_name}</div>
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                Flagging Criteria & Diagnostic Reasons
              </h4>
              <div style={{ padding: '0.75rem', backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 'var(--radius-sm)', color: '#DC2626', fontSize: '0.8125rem' }}>
                {selectedCase.reasons.map((r, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600 }}>
                    <AlertOctagon size={14} />
                    {r}
                  </div>
                ))}
              </div>
            </div>

            {/* Panel Decision Record if present */}
            {selectedCase.panelDecision && (
              <div>
                <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                  Recorded Academic Panel Decisions
                </h4>
                <div style={{ padding: '0.75rem', backgroundColor: '#E8FBF5', border: '1px solid #16BD91', borderRadius: 'var(--radius-sm)', fontSize: '0.8125rem' }}>
                  <div><strong>Review Date:</strong> {selectedCase.panelDecision.reviewDate}</div>
                  <div><strong>Action Plan:</strong> {selectedCase.panelDecision.actionPlan}</div>
                  <div><strong>Panel Notes:</strong> {selectedCase.panelDecision.panelNotes || 'No notes provided'}</div>
                </div>
              </div>
            )}

            {/* Courses graded in this flagged semester */}
            <div>
              <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                Course Scores in {selectedCase.semester_name}
              </h4>
              <div className="data-table-container">
                <table style={{ width: '100%', fontSize: '0.8125rem', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                      <th style={{ textAlign: 'left', padding: '0.35rem' }}>Course Code</th>
                      <th style={{ textAlign: 'left', padding: '0.35rem' }}>Title</th>
                      <th style={{ textAlign: 'center', padding: '0.35rem' }}>Units</th>
                      <th style={{ textAlign: 'center', padding: '0.35rem' }}>Score</th>
                      <th style={{ textAlign: 'center', padding: '0.35rem' }}>Grade</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedCase.enrollments?.map((e) => (
                      <tr key={e.enrollment_id} style={{ borderBottom: '1px solid var(--border-light)' }}>
                        <td style={{ padding: '0.35rem', fontWeight: 700 }}>{e.course_code}</td>
                        <td style={{ padding: '0.35rem' }}>{e.course_title}</td>
                        <td style={{ padding: '0.35rem', textAlign: 'center' }}>{e.credit_units}</td>
                        <td style={{ padding: '0.35rem', textAlign: 'center', fontWeight: 700 }}>{e.score}</td>
                        <td style={{ padding: '0.35rem', textAlign: 'center', fontWeight: 800, color: e.grade === 'F' ? '#DC2626' : 'inherit' }}>
                          {e.grade}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal 2: Record Academic Panel Decision */}
      <Modal
        isOpen={!!decisionModalStudent}
        onClose={() => setDecisionModalStudent(null)}
        title="Record Academic Board / Panel Decision"
        maxWidth="550px"
      >
        {decisionModalStudent && (
          <form onSubmit={handleSaveDecision}>
            <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#F8FAFC', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontWeight: 700 }}>{decisionModalStudent.name} ({decisionModalStudent.matric_no})</div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                Session: {decisionModalStudent.semester_name} • GPA: {decisionModalStudent.gpa?.toFixed(2)}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Classification Decision</label>
              <select
                className="form-control"
                value={decisionForm.status}
                onChange={(e) => setDecisionForm({ ...decisionForm, status: e.target.value })}
              >
                <option value="Probation">Probation (Under Supervision)</option>
                <option value="At Risk">At Risk (Academic Warning Issued)</option>
                <option value="Critical Risk">Critical Risk (Formal Board Review)</option>
                <option value="Good Standing">Cleared / Good Standing (Remedied)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Mandated Action Plan</label>
              <input
                type="text"
                className="form-control"
                required
                value={decisionForm.actionPlan}
                onChange={(e) => setDecisionForm({ ...decisionForm, actionPlan: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Scheduled Review Date</label>
              <input
                type="date"
                className="form-control"
                required
                value={decisionForm.reviewDate}
                onChange={(e) => setDecisionForm({ ...decisionForm, reviewDate: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Panel Notes & Counseling Recommendations</label>
              <textarea
                className="form-control"
                rows="3"
                placeholder="Enter minutes of academic review panel meeting..."
                value={decisionForm.panelNotes}
                onChange={(e) => setDecisionForm({ ...decisionForm, panelNotes: e.target.value })}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.25rem' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setDecisionModalStudent(null)}
              >
                Cancel
              </button>
              <button type="submit" className="btn btn-primary">
                Save & Dispatch Advisor Alert
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};

export default ProbationMonitoring;

