import React, { useState, useMemo } from 'react';
import {
  FileText,
  Download,
  Printer,
  CheckCircle,
  AlertTriangle,
  AlertOctagon,
  GraduationCap,
  Calendar,
  Filter,
} from 'lucide-react';
import { useData } from '../context/DataContext';

export const Reports = () => {
  const {
    currentSemesterEvaluations,
    studentEvaluations,
    semesters,
    selectedSemesterId,
    students,
  } = useData();

  const [reportType, setReportType] = useState('probation'); // 'overall', 'probation', 'at_risk', 'individual'
  const [selectedStudentId, setSelectedStudentId] = useState(students[0]?.student_id || 1);
  const [selectedLevel, setSelectedLevel] = useState('all');

  const currentSemester = semesters.find((s) => s.semester_id === selectedSemesterId) || {};

  // Filter report data based on chosen report type
  const reportData = useMemo(() => {
    let data = currentSemesterEvaluations;

    if (selectedLevel !== 'all') {
      data = data.filter((e) => String(e.level) === String(selectedLevel));
    }

    if (reportType === 'probation') {
      return data.filter((e) => e.standing === 'Probation' || e.standing === 'Critical Risk');
    }
    if (reportType === 'at_risk') {
      return data.filter((e) => e.standing === 'At Risk');
    }
    if (reportType === 'individual') {
      return studentEvaluations.filter((e) => e.student_id === Number(selectedStudentId));
    }
    return data; // 'overall'
  }, [reportType, currentSemesterEvaluations, studentEvaluations, selectedLevel, selectedStudentId]);

  // Export to CSV
  const handleExportCSV = () => {
    let headers = ['Matric No', 'Student Name', 'Level', 'Semester', 'GPA', 'Failed Courses', 'Academic Standing', 'Reasons'];
    let rows = reportData.map((r) => [
      `"${r.matric_no}"`,
      `"${r.name}"`,
      r.level,
      `"${r.semester_name || ''}"`,
      r.gpa !== null ? r.gpa.toFixed(2) : 'N/A',
      r.failed_courses || 0,
      `"${r.standing}"`,
      `"${r.reasons.join('; ')}"`,
    ]);

    const csvString = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${reportType}_report_${currentSemester.session || 'academic'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Download official backend ReportLab PDF
  const handleDownloadBackendPDF = () => {
    let url = `/api/v1/reports/probation/pdf?semester_id=${selectedSemesterId}`;
    if (reportType === 'individual') {
      url = `/api/v1/reports/transcript/${selectedStudentId}/pdf`;
    }
    const token = localStorage.getItem('acadtrack_token');
    
    // Open in new tab or trigger download via direct fetch
    fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => {
        if (!res.ok) throw new Error('Backend service currently offline. Using client print dialog.');
        return res.blob();
      })
      .then((blob) => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = reportType === 'individual' ? `Transcript_Student_${selectedStudentId}.pdf` : `Official_Probation_Report_Sem${selectedSemesterId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      })
      .catch((err) => {
        console.warn(err.message);
        // Seamless fallback to client browser print / PDF save
        window.print();
      });
  };

  // Print / PDF Export
  const handlePrint = () => {
    window.print();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Configuration & Generation Bar */}
      <div
        className="card"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          {/* Report Type Selector */}
          <div>
            <label className="form-label">Report Category</label>
            <select
              className="form-control"
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
            >
              <option value="probation">Academic Probation Report</option>
              <option value="at_risk">At-Risk Student Diagnostic Report</option>
              <option value="overall">Overall Semester Performance Report</option>
              <option value="individual">Individual Student Transcript & Standing</option>
            </select>
          </div>

          {/* Level Filter (if not individual) */}
          {reportType !== 'individual' && (
            <div>
              <label className="form-label">Target Level</label>
              <select
                className="form-control"
                value={selectedLevel}
                onChange={(e) => setSelectedLevel(e.target.value)}
              >
                <option value="all">All Levels (100L - 400L)</option>
                <option value="100">100 Level</option>
                <option value="200">200 Level</option>
                <option value="300">300 Level</option>
                <option value="400">400 Level</option>
              </select>
            </div>
          )}

          {/* Student Selector (if individual) */}
          {reportType === 'individual' && (
            <div>
              <label className="form-label">Select Student</label>
              <select
                className="form-control"
                value={selectedStudentId}
                onChange={(e) => setSelectedStudentId(Number(e.target.value))}
              >
                {students.map((s) => (
                  <option key={s.student_id} value={s.student_id}>
                    {s.matric_no} - {s.name} ({s.level}L)
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '0.5rem', alignSelf: 'flex-end', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={handleExportCSV}>
            <Download size={15} />
            Export CSV
          </button>
          <button className="btn btn-secondary" onClick={handleDownloadBackendPDF} title="Download ReportLab Generated PDF from API">
            <Download size={15} />
            Download PDF
          </button>
          <button className="btn btn-primary" onClick={handlePrint}>
            <Printer size={15} />
            Print Document
          </button>
        </div>
      </div>

      {/* Official Report Document Preview Canvas */}
      <div
        className="card report-print-area"
        style={{
          backgroundColor: '#FFFFFF',
          padding: '2.5rem',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-md)',
        }}
      >
        {/* Document Header */}
        <div
          style={{
            borderBottom: '2px solid var(--primary-green)',
            paddingBottom: '1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
          }}
        >
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--dark-navy)', letterSpacing: '-0.01em' }}>
              ACADEMIC PERFORMANCE & PROBATION MONITORING SYSTEM
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--primary-green)', textTransform: 'uppercase', marginTop: '2px' }}>
              {reportType.replace('_', ' ')} OFFICIAL REPORT
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Session: {currentSemester.session} • {currentSemester.name}
            </div>
          </div>

          <div style={{ textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            <div>Date Generated: {new Date().toLocaleDateString()}</div>
            <div>Classification Rule: 5-Point System</div>
            <div>Classification Status: Official Academic Audit</div>
          </div>
        </div>

        {/* Statistical Summary Box */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '1rem',
            backgroundColor: '#F8FAFC',
            padding: '1rem',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '1.5rem',
            border: '1px solid var(--border-color)',
          }}
        >
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)', fontWeight: 700 }}>RECORDS EVALUATED</span>
            <div style={{ fontSize: '1.25rem', fontWeight: 800 }}>{reportData.length}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)', fontWeight: 700 }}>PROBATION CASES</span>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#DC2626' }}>
              {reportData.filter((r) => r.standing === 'Probation' || r.standing === 'Critical Risk').length}
            </div>
          </div>
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)', fontWeight: 700 }}>AT RISK CASES</span>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#D97706' }}>
              {reportData.filter((r) => r.standing === 'At Risk').length}
            </div>
          </div>
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)', fontWeight: 700 }}>AVERAGE GPA</span>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary-green)' }}>
              {reportData.length
                ? (reportData.reduce((acc, c) => acc + (c.gpa || 0), 0) / reportData.length).toFixed(2)
                : '—'}
            </div>
          </div>
        </div>

        {/* Report Table */}
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
          <thead>
            <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid var(--border-color)' }}>
              <th style={{ padding: '0.6rem', textAlign: 'left' }}>Matric No</th>
              <th style={{ padding: '0.6rem', textAlign: 'left' }}>Student Name</th>
              <th style={{ padding: '0.6rem', textAlign: 'center' }}>Level</th>
              <th style={{ padding: '0.6rem', textAlign: 'center' }}>GPA</th>
              <th style={{ padding: '0.6rem', textAlign: 'center' }}>Fails</th>
              <th style={{ padding: '0.6rem', textAlign: 'left' }}>Academic Standing</th>
              <th style={{ padding: '0.6rem', textAlign: 'left' }}>Diagnosis / Reason</th>
            </tr>
          </thead>
          <tbody>
            {reportData.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                  No student records matched this report specification.
                </td>
              </tr>
            ) : (
              reportData.map((row, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #F1F5F9' }}>
                  <td style={{ padding: '0.55rem', fontFamily: 'monospace', fontWeight: 700 }}>{row.matric_no}</td>
                  <td style={{ padding: '0.55rem', fontWeight: 600 }}>{row.name}</td>
                  <td style={{ padding: '0.55rem', textAlign: 'center' }}>{row.level}L</td>
                  <td style={{ padding: '0.55rem', textAlign: 'center', fontWeight: 800 }}>
                    {row.gpa !== null ? row.gpa.toFixed(2) : '—'}
                  </td>
                  <td style={{ padding: '0.55rem', textAlign: 'center', fontWeight: 600 }}>{row.failed_courses}</td>
                  <td style={{ padding: '0.55rem', fontWeight: 700 }}>
                    <span style={{ color: row.standing === 'Good Standing' ? '#16A34A' : row.standing === 'At Risk' ? '#D97706' : '#DC2626' }}>
                      {row.standing}
                    </span>
                  </td>
                  <td style={{ padding: '0.55rem', color: 'var(--text-secondary)' }}>
                    {row.reasons.join('; ')}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Institutional Sign-off Footer */}
        <div
          style={{
            marginTop: '3rem',
            paddingTop: '1.5rem',
            borderTop: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
          }}
        >
          <div>
            <div style={{ width: '180px', borderBottom: '1px solid #94A3B8', marginBottom: '4px' }}></div>
            <div>Head of Department / Exam Officer</div>
          </div>
          <div>
            <div style={{ width: '180px', borderBottom: '1px solid #94A3B8', marginBottom: '4px' }}></div>
            <div>Academic Board Verification</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports;

