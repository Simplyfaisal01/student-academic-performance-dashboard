import React, { useState, useMemo } from 'react';
import {
  BarChart3,
  TrendingUp,
  PieChart as PieIcon,
  Filter,
  GraduationCap,
  AlertTriangle,
  Award,
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
} from 'chart.js';
import { Doughnut, Bar, Line } from 'react-chartjs-2';
import { useData } from '../context/DataContext';

export const Analytics = () => {
  const {
    currentSemesterEvaluations,
    studentEvaluations,
    courses,
    semesters,
    enrollments,
    selectedSemesterId,
  } = useData();

  const [activeTab, setActiveTab] = useState('overview');

  // 1. Standing Breakdown Data
  const standingCounts = useMemo(() => {
    const counts = { 'Good Standing': 0, 'At Risk': 0, 'Probation': 0, 'Critical Risk': 0 };
    currentSemesterEvaluations.forEach((e) => {
      if (counts[e.standing] !== undefined) {
        counts[e.standing]++;
      } else {
        counts['Good Standing']++;
      }
    });
    return counts;
  }, [currentSemesterEvaluations]);

  const standingChartData = {
    labels: ['Good Standing', 'At Risk', 'Probation', 'Critical Risk'],
    datasets: [
      {
        data: [
          standingCounts['Good Standing'],
          standingCounts['At Risk'],
          standingCounts['Probation'],
          standingCounts['Critical Risk'],
        ],
        backgroundColor: ['#16A34A', '#D97706', '#DC2626', '#7F1D1D'],
        borderWidth: 2,
        borderColor: '#FFFFFF',
      },
    ],
  };

  // 2. Performance Comparison by Level (Pass vs Fail)
  const levelPerformance = useMemo(() => {
    const levels = [100, 200, 300, 400];
    const passed = [];
    const failed = [];

    levels.forEach((lvl) => {
      const lvlStudents = currentSemesterEvaluations.filter((e) => e.level === lvl);
      let lvlPassed = 0;
      let lvlFailed = 0;
      lvlStudents.forEach((st) => {
        if (st.standing === 'Good Standing') lvlPassed++;
        else lvlFailed++;
      });
      passed.push(lvlPassed);
      failed.push(lvlFailed);
    });

    return { passed, failed };
  }, [currentSemesterEvaluations]);

  const levelComparisonData = {
    labels: ['100 Level', '200 Level', '300 Level', '400 Level'],
    datasets: [
      {
        label: 'Satisfactory Progress',
        data: levelPerformance.passed,
        backgroundColor: '#087B5B',
        borderRadius: 4,
      },
      {
        label: 'Flagged (At Risk / Probation)',
        data: levelPerformance.failed,
        backgroundColor: '#DC2626',
        borderRadius: 4,
      },
    ],
  };

  // 3. Top Failed Courses in active semester
  const topFailedCourses = useMemo(() => {
    const failsMap = new Map();
    const totalsMap = new Map();

    enrollments.forEach((e) => {
      if (e.semester_id !== selectedSemesterId || e.score === null) return;
      totalsMap.set(e.course_id, (totalsMap.get(e.course_id) || 0) + 1);
      if (e.grade === 'F' || e.score < 40) {
        failsMap.set(e.course_id, (failsMap.get(e.course_id) || 0) + 1);
      }
    });

    const courseMap = new Map(courses.map((c) => [c.course_id, c]));
    const list = [];
    failsMap.forEach((fails, cid) => {
      const c = courseMap.get(cid);
      if (c) {
        const total = totalsMap.get(cid) || 1;
        list.push({
          code: c.code,
          title: c.title,
          level: c.level,
          fails,
          total,
          rate: Math.round((fails / total) * 100),
        });
      }
    });

    return list.sort((a, b) => b.fails - a.fails).slice(0, 5);
  }, [enrollments, selectedSemesterId, courses]);

  const topFailedChartData = {
    labels: topFailedCourses.map((c) => c.code),
    datasets: [
      {
        label: 'Number of Fails',
        data: topFailedCourses.map((c) => c.fails),
        backgroundColor: '#DC2626',
        borderRadius: 4,
      },
    ],
  };

  // 4. Historical Trends across all semesters
  const completedSemesters = semesters.filter((s) => s.semester_id !== 4);
  const trendLabels = completedSemesters.map((s) => `${s.session} ${s.name.replace(' Semester', '')}`);

  const historicalTrendsData = {
    labels: trendLabels,
    datasets: [
      {
        label: 'Average GPA',
        data: completedSemesters.map((s) => {
          const evals = studentEvaluations.filter((e) => e.semester_id === s.semester_id && e.gpa !== null);
          if (!evals.length) return 0;
          return Number((evals.reduce((acc, curr) => acc + curr.gpa, 0) / evals.length).toFixed(2));
        }),
        borderColor: '#087B5B',
        backgroundColor: 'rgba(8, 123, 91, 0.1)',
        yAxisID: 'y',
        tension: 0.3,
      },
      {
        label: 'Flagged Cases',
        data: completedSemesters.map((s) => {
          return studentEvaluations.filter(
            (e) => e.semester_id === s.semester_id && e.isFlagged
          ).length;
        }),
        borderColor: '#DC2626',
        backgroundColor: 'rgba(220, 38, 38, 0.1)',
        yAxisID: 'y1',
        tension: 0.3,
      },
    ],
  };

  const trendOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        type: 'linear',
        position: 'left',
        max: 5.0,
        title: { display: true, text: 'Average GPA' },
        grid: { color: '#F1F5F9' },
      },
      y1: {
        type: 'linear',
        position: 'right',
        grid: { drawOnChartArea: false },
        title: { display: true, text: 'Flagged Students' },
      },
      x: { grid: { display: false } },
    },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header */}
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
            Institutional Academic Analytics
          </h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
            Visual diagnostic representations based on real student records and enrollment scores
          </p>
        </div>

        {/* Tab switcher */}
        <div style={{ display: 'flex', backgroundColor: '#FFFFFF', padding: '0.25rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', flexWrap: 'wrap', gap: '0.25rem' }}>
          <button
            onClick={() => setActiveTab('overview')}
            style={{
              padding: '0.45rem 0.85rem',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer',
              backgroundColor: activeTab === 'overview' ? 'var(--primary-green)' : 'transparent',
              color: activeTab === 'overview' ? '#FFFFFF' : 'var(--text-secondary)',
              flex: '1 1 auto',
            }}
          >
            Overview & Levels
          </button>
          <button
            onClick={() => setActiveTab('trends')}
            style={{
              padding: '0.45rem 0.85rem',
              border: 'none',
              borderRadius: '4px',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer',
              backgroundColor: activeTab === 'trends' ? 'var(--primary-green)' : 'transparent',
              color: activeTab === 'trends' ? '#FFFFFF' : 'var(--text-secondary)',
              flex: '1 1 auto',
            }}
          >
            Historical Trends
          </button>
        </div>
      </div>

      {activeTab === 'overview' ? (
        <div className="grid-lower-2" style={{ width: '100%' }}>
          {/* Chart 1: Standing Distribution */}
          <div className="card chart-card-box" style={{ height: '360px', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            <div className="card-header">
              <span className="card-title">Academic Standing Distribution</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Active Semester</span>
            </div>
            <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
              <Doughnut data={standingChartData} options={{ responsive: true, maintainAspectRatio: false, cutout: '65%' }} />
            </div>
          </div>

          {/* Chart 2: Level-by-Level Comparison */}
          <div className="card chart-card-box" style={{ height: '360px', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            <div className="card-header">
              <span className="card-title">Performance by Academic Level</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Good Standing vs Flagged</span>
            </div>
            <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
              <Bar
                data={levelComparisonData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: { x: { grid: { display: false } }, y: { beginAtZero: true, grid: { color: '#F1F5F9' } } },
                }}
              />
            </div>
          </div>

          {/* Chart 3: Top Failing Courses */}
          <div className="card chart-card-box" style={{ height: '360px', display: 'flex', flexDirection: 'column', minWidth: 0, gridColumn: '1 / -1' }}>
            <div className="card-header">
              <div>
                <div className="card-title">Top High-Deficiency Courses (Most Fails)</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Courses with the highest failure rates requiring departmental intervention
                </div>
              </div>
            </div>
            <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
              <Bar
                data={topFailedChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: { y: { beginAtZero: true, ticks: { stepSize: 2 } }, x: { grid: { display: false } } },
                }}
              />
            </div>
          </div>
        </div>
      ) : (
        /* Historical Trends Tab */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', width: '100%' }}>
          <div className="card chart-card-box" style={{ height: '420px', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            <div className="card-header">
              <div>
                <div className="card-title">Longitudinal Performance & Probation Trends</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Correlation between average departmental GPA and probation volumes
                </div>
              </div>
            </div>
            <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
              <Line data={historicalTrendsData} options={trendOptions} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;

