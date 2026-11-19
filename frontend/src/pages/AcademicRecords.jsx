import React, { useState, useMemo } from 'react';
import {
  Search,
  Filter,
  Upload,
  Download,
  FileSpreadsheet,
  CheckCircle,
  AlertTriangle,
  X,
  BookOpen,
} from 'lucide-react';
import { useData } from '../context/DataContext';
import { useAuth } from '../context/AuthContext';
import { parseRawCSV } from '../services/csvLoader';
import Modal from '../components/common/Modal';

export const AcademicRecords = () => {
  const {
    enrollments,
    students,
    courses,
    semesters,
    studentMap,
    courseMap,
    semesterMap,
    addUploadedEnrollments,
    selectedSemesterId,
    setSelectedSemesterId,
  } = useData();
  const { user, isLecturer } = useAuth();

  const [searchTerm, setSearchTerm] = useState('');
  const [courseFilter, setCourseFilter] = useState('all');
  const [gradeFilter, setGradeFilter] = useState('all');

  // CSV Upload modal states
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadTargetCourseId, setUploadTargetCourseId] = useState(courses[0]?.course_id || 1);
  const [uploadTargetSemesterId, setUploadTargetSemesterId] = useState(selectedSemesterId);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadPreview, setUploadPreview] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // If lecturer, identify courses assigned to them
  const lecturerCourseIds = useMemo(() => {
    if (!isLecturer || !user) return null;
    const uid = String(user.id).padStart(3, '0');
    const uStr = `U${uid}`;
    return courses
      .filter((c) => c.lecturer_id === uStr || c.lecturer_id === user.id)
      .map((c) => c.course_id);
  }, [courses, user, isLecturer]);

  // Enriched enrollment records with student name, course title, and units
  const enrichedRecords = useMemo(() => {
    return enrollments
      .filter((e) => {
        // If lecturer, only show their courses
        if (lecturerCourseIds && !lecturerCourseIds.includes(e.course_id)) {
          return false;
        }
        return true;
      })
      .map((e) => {
        const student = studentMap.get(e.student_id) || {};
        const course = courseMap.get(e.course_id) || {};
        const semester = semesterMap.get(e.semester_id) || {};

        return {
          ...e,
          matric_no: student.matric_no || 'Unknown',
          student_name: student.name || 'Unknown Student',
          level: student.level || '—',
          course_code: course.code || '—',
          course_title: course.title || '—',
          credit_units: course.credit_units || 3,
          semester_name: semester.name ? `${semester.session} ${semester.name}` : `Semester ${e.semester_id}`,
        };
      });
  }, [enrollments, studentMap, courseMap, semesterMap, lecturerCourseIds]);

  // Filter records
  const filteredRecords = useMemo(() => {
    return enrichedRecords.filter((rec) => {
      const matchesSearch =
        rec.matric_no?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        rec.student_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        rec.course_code?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesSemester =
        selectedSemesterId === 'all' || Number(rec.semester_id) === Number(selectedSemesterId);

      const matchesCourse =
        courseFilter === 'all' || String(rec.course_id) === String(courseFilter);

      const matchesGrade =
        gradeFilter === 'all' || rec.grade === gradeFilter;

      return matchesSearch && matchesSemester && matchesCourse && matchesGrade;
    });
  }, [enrichedRecords, searchTerm, selectedSemesterId, courseFilter, gradeFilter]);

  // Handle CSV file selection and client-side validation preview
  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadFile(file);

    try {
      setIsProcessing(true);
      const parsedRows = await parseRawCSV(file);

      // Validate rows against dataset rules
      const matricSet = new Set(students.map((s) => s.matric_no));
      const seenMatricsInFile = new Set();
      const valid = [];
      const errors = [];

      parsedRows.forEach((row, idx) => {
        const line = idx + 2;
        const matric = row.matric_no ? String(row.matric_no).trim() : '';
        const rawScore = row.score;

        if (!matric) {
          errors.push({ line, matric: '—', error: 'Missing matric_no' });
          return;
        }

        if (seenMatricsInFile.has(matric)) {
          errors.push({ line, matric, error: 'Duplicate matric number in this file' });
          return;
        }
        seenMatricsInFile.add(matric);

        if (!matricSet.has(matric)) {
          errors.push({ line, matric, error: 'Unknown student matric number (not in database)' });
          return;
        }

        const score = Number(rawScore);
        if (isNaN(score) || rawScore === '' || rawScore === null || rawScore === undefined) {
          errors.push({ line, matric, error: `Invalid non-numeric score '${rawScore}'` });
          return;
        }

        if (score < 0 || score > 100) {
          errors.push({ line, matric, error: `Score ${score} out of valid range (0-100)` });
          return;
        }

        // Determine grade & point
        let grade = 'F';
        let gradePoint = 0;
        if (score >= 70) { grade = 'A'; gradePoint = 5; }
        else if (score >= 60) { grade = 'B'; gradePoint = 4; }
        else if (score >= 50) { grade = 'C'; gradePoint = 3; }
        else if (score >= 45) { grade = 'D'; gradePoint = 2; }
        else if (score >= 40) { grade = 'E'; gradePoint = 1; }

        const matchedStudent = students.find((s) => s.matric_no === matric);
        valid.push({
          student_id: matchedStudent.student_id,
          matric_no: matric,
          student_name: matchedStudent.name,
          score,
          grade,
          grade_point: gradePoint,
          course_id: Number(uploadTargetCourseId),
          semester_id: Number(uploadTargetSemesterId),
        });
      });

      setUploadPreview({
        total: parsedRows.length,
        valid,
        errors,
      });
    } catch (err) {
      alert('Failed to parse CSV file: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCommitUpload = () => {
    if (!uploadPreview || !uploadPreview.valid.length) return;
    addUploadedEnrollments(uploadPreview.valid);
    alert(`Successfully ingested ${uploadPreview.valid.length} valid grade records!`);
    setShowUploadModal(false);
    setUploadFile(null);
    setUploadPreview(null);
  };

  const handleDownloadTemplate = () => {
    const csvContent =
      'data:text/csv;charset=utf-8,matric_no,score\nFT21BCMP0001,75\nFT21BCMP0002,68\nFT21BCMP0003,54\nFT21BCMP0004,38\n';
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'grades_upload_template.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header & Controls */}
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
            Academic Records & Grade Ingestion
          </h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
            Showing {filteredRecords.length} of {enrollments.length} raw student enrollment records from dataset
          </p>
        </div>

        <div className="action-buttons-wrap">
          <button
            className="btn btn-secondary"
            onClick={handleDownloadTemplate}
            title="Download CSV format template"
          >
            <Download size={15} />
            CSV Template
          </button>
          <button
            className="btn btn-primary"
            onClick={() => setShowUploadModal(true)}
          >
            <Upload size={15} />
            Bulk Grade Upload (CSV)
          </button>
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
            placeholder="Search by student, matric, course code..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Course Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flex: '0 1 auto' }}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
            Course:
          </span>
          <select
            className="form-control"
            style={{ width: 'auto', minWidth: '130px', maxWidth: '200px' }}
            value={courseFilter}
            onChange={(e) => setCourseFilter(e.target.value)}
          >
            <option value="all">All Courses (40)</option>
            {courses.map((c) => (
              <option key={c.course_id} value={c.course_id}>
                {c.code} - {c.title.substring(0, 20)}...
              </option>
            ))}
          </select>
        </div>

        {/* Grade Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flex: '0 1 auto' }}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
            Grade:
          </span>
          <select
            className="form-control"
            style={{ width: 'auto', minWidth: '110px' }}
            value={gradeFilter}
            onChange={(e) => setGradeFilter(e.target.value)}
          >
            <option value="all">All Grades</option>
            <option value="A">Grade A (70-100)</option>
            <option value="B">Grade B (60-69)</option>
            <option value="C">Grade C (50-59)</option>
            <option value="D">Grade D (45-49)</option>
            <option value="E">Grade E (40-44)</option>
            <option value="F">Grade F (&lt;40 Fail)</option>
          </select>
        </div>
      </div>

      {/* Main Records Table */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Matric No</th>
              <th>Student Name</th>
              <th>Course Code</th>
              <th>Course Title</th>
              <th style={{ textAlign: 'center' }}>Units</th>
              <th>Academic Session</th>
              <th style={{ textAlign: 'center' }}>Score</th>
              <th style={{ textAlign: 'center' }}>Grade</th>
              <th style={{ textAlign: 'center' }}>Points</th>
            </tr>
          </thead>
          <tbody>
            {filteredRecords.length === 0 ? (
              <tr>
                <td colSpan="9" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-secondary)' }}>
                  No enrollment records found matching your filters.
                </td>
              </tr>
            ) : (
              filteredRecords.slice(0, 100).map((rec, i) => (
                <tr key={`${rec.enrollment_id || i}_${rec.student_id}_${rec.course_id}`}>
                  <td style={{ fontWeight: 700, fontFamily: 'monospace' }}>{rec.matric_no}</td>
                  <td style={{ fontWeight: 600 }}>{rec.student_name}</td>
                  <td style={{ fontWeight: 700, color: 'var(--primary-green)' }}>{rec.course_code}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>{rec.course_title}</td>
                  <td style={{ textAlign: 'center', fontWeight: 600 }}>{rec.credit_units}</td>
                  <td style={{ fontSize: '0.8125rem' }}>{rec.semester_name}</td>
                  <td style={{ textAlign: 'center', fontWeight: 700 }}>
                    {rec.score !== null && rec.score !== undefined ? rec.score : '—'}
                  </td>
                  <td
                    style={{
                      textAlign: 'center',
                      fontWeight: 800,
                      color: rec.grade === 'F' ? '#DC2626' : rec.grade === 'A' ? '#16A34A' : 'var(--text-primary)',
                    }}
                  >
                    {rec.grade || '—'}
                  </td>
                  <td style={{ textAlign: 'center', fontWeight: 600 }}>
                    {rec.grade_point !== null && rec.grade_point !== undefined ? rec.grade_point : '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        {filteredRecords.length > 100 && (
          <div style={{ padding: '0.75rem 1rem', fontSize: '0.8125rem', color: 'var(--text-secondary)', backgroundColor: '#F8FAFC', borderTop: '1px solid var(--border-color)', textAlign: 'center' }}>
            Showing first 100 records for optimal display. Use search or filters above to refine results.
          </div>
        )}
      </div>

      {/* CSV Bulk Upload & Dry-Run Preview Modal */}
      <Modal
        isOpen={showUploadModal}
        onClose={() => {
          setShowUploadModal(false);
          setUploadFile(null);
          setUploadPreview(null);
        }}
        title="Bulk Grade Ingestion (CSV Upload)"
        maxWidth="700px"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Target Course & Semester */}
          <div className="grid-form-2">
            <div className="form-group">
              <label className="form-label">Target Course</label>
              <select
                className="form-control"
                value={uploadTargetCourseId}
                onChange={(e) => setUploadTargetCourseId(Number(e.target.value))}
              >
                {courses.map((c) => (
                  <option key={c.course_id} value={c.course_id}>
                    {c.code} - {c.title} ({c.level}L)
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Academic Semester</label>
              <select
                className="form-control"
                value={uploadTargetSemesterId}
                onChange={(e) => setUploadTargetSemesterId(Number(e.target.value))}
              >
                {semesters.map((s) => (
                  <option key={s.semester_id} value={s.semester_id}>
                    {s.session} - {s.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Drag & drop / upload area */}
          <div
            style={{
              border: '2px dashed var(--border-color)',
              borderRadius: 'var(--radius-md)',
              padding: '2rem',
              textAlign: 'center',
              backgroundColor: '#F8FAFC',
            }}
          >
            <FileSpreadsheet size={36} color="var(--primary-green)" style={{ margin: '0 auto 0.75rem' }} />
            <div style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '0.25rem' }}>
              Select CSV Grade Sheet to Validate & Ingest
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Must contain columns: <code>matric_no</code> and <code>score</code>.
            </p>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              style={{ display: 'none' }}
              id="csv-file-input"
            />
            <label htmlFor="csv-file-input" className="btn btn-primary" style={{ cursor: 'pointer' }}>
              Choose CSV File
            </label>
            {uploadFile && (
              <div style={{ marginTop: '0.75rem', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Selected: {uploadFile.name}
              </div>
            )}
          </div>

          {/* Dry Run Preview Section */}
          {uploadPreview && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 1rem',
                  backgroundColor: uploadPreview.errors.length > 0 ? '#FEF3C7' : '#DCFCE7',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                }}
              >
                <span>Validation Summary: {uploadPreview.valid.length} Valid Rows, {uploadPreview.errors.length} Errors</span>
                <span style={{ fontSize: '0.75rem' }}>Total in File: {uploadPreview.total}</span>
              </div>

              {/* Error messages if any */}
              {uploadPreview.errors.length > 0 && (
                <div style={{ maxHeight: '140px', overflowY: 'auto', border: '1px solid #FCA5A5', borderRadius: 'var(--radius-sm)', padding: '0.5rem', backgroundColor: '#FEF2F2' }}>
                  <div style={{ fontWeight: 700, fontSize: '0.75rem', color: '#DC2626', marginBottom: '0.25rem' }}>
                    Errors detected (these rows will be skipped):
                  </div>
                  {uploadPreview.errors.map((err, idx) => (
                    <div key={idx} style={{ fontSize: '0.75rem', color: '#DC2626' }}>
                      Row {err.line} ({err.matric}): {err.error}
                    </div>
                  ))}
                </div>
              )}

              {/* Valid rows preview */}
              {uploadPreview.valid.length > 0 && (
                <div style={{ maxHeight: '160px', overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }}>
                  <table style={{ width: '100%', fontSize: '0.75rem', borderCollapse: 'collapse' }}>
                    <thead style={{ backgroundColor: '#F8FAFC', position: 'sticky', top: 0 }}>
                      <tr>
                        <th style={{ padding: '0.4rem', textAlign: 'left' }}>Matric No</th>
                        <th style={{ padding: '0.4rem', textAlign: 'left' }}>Student Name</th>
                        <th style={{ padding: '0.4rem', textAlign: 'center' }}>Score</th>
                        <th style={{ padding: '0.4rem', textAlign: 'center' }}>Grade</th>
                        <th style={{ padding: '0.4rem', textAlign: 'center' }}>Points</th>
                      </tr>
                    </thead>
                    <tbody>
                      {uploadPreview.valid.map((r, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid #F1F5F9' }}>
                          <td style={{ padding: '0.35rem 0.4rem', fontFamily: 'monospace' }}>{r.matric_no}</td>
                          <td style={{ padding: '0.35rem 0.4rem' }}>{r.student_name}</td>
                          <td style={{ padding: '0.35rem 0.4rem', textAlign: 'center', fontWeight: 700 }}>{r.score}</td>
                          <td style={{ padding: '0.35rem 0.4rem', textAlign: 'center', fontWeight: 700 }}>{r.grade}</td>
                          <td style={{ padding: '0.35rem 0.4rem', textAlign: 'center' }}>{r.grade_point}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setUploadFile(null);
                    setUploadPreview(null);
                  }}
                >
                  Clear File
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={uploadPreview.valid.length === 0}
                  onClick={handleCommitUpload}
                >
                  Commit {uploadPreview.valid.length} Valid Records to Database
                </button>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default AcademicRecords;

