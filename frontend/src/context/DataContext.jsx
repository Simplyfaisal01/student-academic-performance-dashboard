import React, { createContext, useContext, useState, useEffect, useMemo } from 'react';
import { loadCSV } from '../services/csvLoader';
import { classifyStanding, DEFAULT_THRESHOLDS } from '../services/probationEngine';

const DataContext = createContext(null);

export const DataProvider = ({ children }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Raw dataset tables
  const [students, setStudents] = useState([]);
  const [courses, setCourses] = useState([]);
  const [semesters, setSemesters] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [usersList, setUsersList] = useState([]);
  const [expectedProbation, setExpectedProbation] = useState([]);

  // Selected academic session / semester filter
  const [selectedSemesterId, setSelectedSemesterId] = useState(3); // Default to Semester 3 (graded history)

  // Configurable thresholds for probation & academic standing
  const [thresholds, setThresholds] = useState(() => {
    const saved = localStorage.getItem('acadtrack_thresholds');
    return saved ? JSON.parse(saved) : DEFAULT_THRESHOLDS;
  });

  // Recorded Academic Panel Decisions (probation reviews, counseling, warnings)
  const [panelDecisions, setPanelDecisions] = useState(() => {
    const saved = localStorage.getItem('acadtrack_panel_decisions');
    return saved ? JSON.parse(saved) : {};
  });

  // Load all CSVs on startup
  useEffect(() => {
    const initData = async () => {
      try {
        setLoading(true);
        const [
          rawStudents,
          rawCourses,
          rawSemesters,
          rawEnrollments,
          rawUsers,
          rawProbation,
        ] = await Promise.all([
          loadCSV('students.csv'),
          loadCSV('courses.csv'),
          loadCSV('semesters.csv'),
          loadCSV('enrollments.csv'),
          loadCSV('users.csv'),
          loadCSV('expected_probation_results.csv'),
        ]);

        setStudents(rawStudents);
        setCourses(rawCourses);
        setSemesters(rawSemesters);
        setEnrollments(rawEnrollments);
        setUsersList(rawUsers);
        setExpectedProbation(rawProbation);
        
        // Pick current or latest semester
        const currentSem = rawSemesters.find((s) => s.is_current === 1 || s.is_current === true);
        if (currentSem) {
          // If current is sem 4 (blank scores), default view to sem 3 so data displays immediately
          setSelectedSemesterId(currentSem.semester_id === 4 ? 3 : currentSem.semester_id);
        }
      } catch (err) {
        console.error('Failed to load CSV dataset:', err);
        setError('Failed to load dataset files. Please ensure /data/ CSV files exist.');
      } finally {
        setLoading(false);
      }
    };

    initData();
  }, []);

  // Save thresholds to localStorage when changed
  const updateThresholds = (newThresholds) => {
    setThresholds(newThresholds);
    localStorage.setItem('acadtrack_thresholds', JSON.stringify(newThresholds));
  };

  // Record an academic panel decision
  const recordPanelDecision = (studentId, semesterId, decisionData) => {
    const key = `${studentId}_${semesterId}`;
    const updated = {
      ...panelDecisions,
      [key]: {
        ...decisionData,
        recordedAt: new Date().toISOString(),
      },
    };
    setPanelDecisions(updated);
    localStorage.setItem('acadtrack_panel_decisions', JSON.stringify(updated));
  };

  // Save or update student
  const saveStudent = (studentData) => {
    if (studentData.student_id) {
      setStudents((prev) =>
        prev.map((s) => (s.student_id === studentData.student_id ? { ...s, ...studentData } : s))
      );
    } else {
      const newId = Math.max(...students.map((s) => s.student_id || 0), 0) + 1;
      setStudents((prev) => [...prev, { ...studentData, student_id: newId }]);
    }
  };

  // Delete student
  const deleteStudent = (studentId) => {
    setStudents((prev) => prev.filter((s) => s.student_id !== studentId));
    setEnrollments((prev) => prev.filter((e) => e.student_id !== studentId));
  };

  // User management operations
  const saveUser = (userData) => {
    if (userData.user_id) {
      setUsersList((prev) =>
        prev.map((u) => (u.user_id === userData.user_id ? { ...u, ...userData } : u))
      );
    } else {
      const count = usersList.length + 1;
      const newUid = `U${String(count).padStart(3, '0')}`;
      setUsersList((prev) => [...prev, { ...userData, user_id: newUid, status: 'Active' }]);
    }
  };

  const toggleUserStatus = (userId) => {
    setUsersList((prev) =>
      prev.map((u) =>
        u.user_id === userId
          ? { ...u, status: u.status === 'Inactive' ? 'Active' : 'Inactive' }
          : u
      )
    );
  };

  // Add bulk enrollments from uploaded CSV
  const addUploadedEnrollments = (newRecords) => {
    setEnrollments((prev) => {
      // Upsert: replace if same student + course + semester, else append
      const existingMap = new Map();
      prev.forEach((e) => {
        existingMap.set(`${e.student_id}_${e.course_id}_${e.semester_id}`, e);
      });
      newRecords.forEach((r) => {
        existingMap.set(`${r.student_id}_${r.course_id}_${r.semester_id}`, r);
      });
      return Array.from(existingMap.values());
    });
  };

  // Helper maps for quick lookups
  const courseMap = useMemo(() => {
    const map = new Map();
    courses.forEach((c) => map.set(c.course_id, c));
    return map;
  }, [courses]);

  const studentMap = useMemo(() => {
    const map = new Map();
    students.forEach((s) => map.set(s.student_id, s));
    return map;
  }, [students]);

  const semesterMap = useMemo(() => {
    const map = new Map();
    semesters.forEach((sem) => map.set(sem.semester_id, sem));
    return map;
  }, [semesters]);

  const advisorMap = useMemo(() => {
    const map = new Map();
    usersList.forEach((u) => map.set(u.user_id, u));
    return map;
  }, [usersList]);

  // Evaluated student standing across semesters
  const studentEvaluations = useMemo(() => {
    if (!students.length || !enrollments.length) return [];

    // Group enrollments by student and semester
    const grouped = new Map();
    enrollments.forEach((e) => {
      if (e.score === null || e.score === undefined || e.score === '') return;
      const key = `${e.student_id}_${e.semester_id}`;
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      const course = courseMap.get(e.course_id) || {};
      grouped.get(key).push({
        ...e,
        credit_units: course.credit_units || 3,
        course_code: course.code,
        course_title: course.title,
      });
    });

    const evaluations = [];

    students.forEach((st) => {
      // Find all semesters student was enrolled in
      for (const sem of semesters) {
        const key = `${st.student_id}_${sem.semester_id}`;
        const studentSemEnrollments = grouped.get(key);

        if (studentSemEnrollments && studentSemEnrollments.length > 0) {
          let totalPoints = 0;
          let totalUnits = 0;
          let failedCount = 0;

          studentSemEnrollments.forEach((enr) => {
            const units = enr.credit_units || 3;
            totalPoints += Number(enr.grade_point || 0) * units;
            totalUnits += units;
            if (enr.grade === 'F' || enr.score < 40) {
              failedCount += 1;
            }
          });

          const gpa = totalUnits > 0 ? Number((totalPoints / totalUnits).toFixed(2)) : null;
          const classification = classifyStanding(gpa, failedCount, thresholds);
          const panelKey = `${st.student_id}_${sem.semester_id}`;
          const panelDecision = panelDecisions[panelKey] || null;

          evaluations.push({
            student_id: st.id || st.student_id,
            matric_no: st.matric_no,
            name: st.name,
            level: st.level,
            email: st.email,
            advisor_id: st.advisor_id,
            advisor_name: advisorMap.get(st.advisor_id)?.name || 'Departmental Advisor',
            semester_id: sem.semester_id,
            semester_name: `${sem.session} - ${sem.name}`,
            session: sem.session,
            gpa: gpa,
            total_units: totalUnits,
            failed_courses: failedCount,
            standing: panelDecision?.status || classification.standing,
            raw_standing: classification.standing,
            reasons: classification.reasons,
            isFlagged: classification.isFlagged,
            panelDecision: panelDecision,
            enrollments: studentSemEnrollments,
          });
        }
      }
    });

    return evaluations;
  }, [students, enrollments, semesters, courseMap, advisorMap, thresholds, panelDecisions]);

  // Current semester evaluations
  const currentSemesterEvaluations = useMemo(() => {
    return studentEvaluations.filter((ev) => ev.semester_id === selectedSemesterId);
  }, [studentEvaluations, selectedSemesterId]);

  // Overall metric counts for selected semester
  const summaryMetrics = useMemo(() => {
    const evals = currentSemesterEvaluations;
    const totalStudents = evals.length;
    const goodStanding = evals.filter((e) => e.standing === 'Good Standing').length;
    const atRisk = evals.filter((e) => e.standing === 'At Risk').length;
    const onProbation = evals.filter((e) => e.standing === 'Probation').length;
    const criticalRisk = evals.filter((e) => e.standing === 'Critical Risk').length;

    const gpas = evals.map((e) => e.gpa).filter((g) => g !== null && g !== undefined);
    const avgGpa = gpas.length > 0 ? Number((gpas.reduce((a, b) => a + b, 0) / gpas.length).toFixed(2)) : 0;

    return {
      totalStudents,
      goodStanding,
      atRisk,
      onProbation: onProbation + criticalRisk, // combined probation cases
      criticalRisk,
      avgGpa,
    };
  }, [currentSemesterEvaluations]);

  return (
    <DataContext.Provider
      value={{
        loading,
        error,
        students,
        courses,
        semesters,
        enrollments,
        usersList,
        expectedProbation,
        selectedSemesterId,
        setSelectedSemesterId,
        thresholds,
        updateThresholds,
        panelDecisions,
        recordPanelDecision,
        studentEvaluations,
        currentSemesterEvaluations,
        summaryMetrics,
        saveStudent,
        deleteStudent,
        saveUser,
        toggleUserStatus,
        addUploadedEnrollments,
        courseMap,
        studentMap,
        semesterMap,
        advisorMap,
      }}
    >
      {children}
    </DataContext.Provider>
  );
};

export const useData = () => {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};

