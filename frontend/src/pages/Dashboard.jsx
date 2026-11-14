import React from 'react';
import {
  Users,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  TrendingUp,
  FileText,
  Clock,
  ArrowRight,
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
import { Link } from 'react-router-dom';
import { useData } from '../context/DataContext';
import StatCard from '../components/common/StatCard';
import StatusBadge from '../components/common/StatusBadge';

// Register Chart.js modules
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

export const Dashboard = () => {
  const {
    loading,
    summaryMetrics,
    currentSemesterEvaluations,
    studentEvaluations,
    semesters,
    selectedSemesterId,
  } = useData();

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1rem', color: 'var(--text-secondary)' }}>
        Loading academic records and calculating student standings...
      </div>
    );
  }

  // 1. Academic Standing Distribution (Doughnut Chart)
  const standingData = {
    labels: ['Good Standing', 'At Risk', 'Probation', 'Critical Risk'],
    datasets: [
      {
        data: [
          summaryMetrics.goodStanding,
          summaryMetrics.atRisk,
          summaryMetrics.onProbation - summaryMetrics.criticalRisk,
          summaryMetrics.criticalRisk,
        ],
        backgroundColor: ['#16A34A', '#D97706', '#DC2626', '#7F1D1D'],
        borderWidth: 2,
        borderColor: '#FFFFFF',
      },
    ],
  };

  const standingOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { boxWidth: 12, font: { family: 'Plus Jakarta Sans', size: 12 } },
      },
    },
    cutout: '70%',
  };

  // 2. Academic Performance Overview by Level (Bar Chart)
  const levels = [100, 200, 300, 400];
  const levelAvgGpas = levels.map((lvl) => {
    const lvlStudents = currentSemesterEvaluations.filter((e) => e.level === lvl && e.gpa !== null);
    if (!lvlStudents.length) return 0;
    const sum = lvlStudents.reduce((acc, curr) => acc + curr.gpa, 0);
    return Number((sum / lvlStudents.length).toFixed(2));
  });

  const performanceData = {
    labels: ['100 Level', '200 Level', '300 Level', '400 Level'],
    datasets: [
      {
        label: 'Average GPA',
        data: levelAvgGpas,
        backgroundColor: '#087B5B',
        borderRadius: 6,
      },
    ],
  };

  const performanceOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        max: 5.0,
        ticks: { stepSize: 1.0 },
        grid: { color: '#F1F5F9' },
      },
      x: {
        grid: { display: false },
      },
    },
    plugins: {
      legend: { display: false },
    },
  };

  // 3. Probation Trends across all available semesters (Line Chart)
  const completedSemesters = semesters.filter((s) => s.semester_id !== 4); // sem 1, 2, 3 have grades
  const probationTrendData = {
    labels: completedSemesters.map((s) => `${s.session} ${s.name.replace(' Semester', '')}`),
    datasets: [
      {
        label: 'Flagged Probation Cases',
        data: completedSemesters.map((s) => {
          return studentEvaluations.filter(
            (e) => e.semester_id === s.semester_id && (e.standing === 'Probation' || e.standing === 'Critical Risk')
          ).length;
        }),
        borderColor: '#DC2626',
        backgroundColor: 'rgba(220, 38, 38, 0.1)',
        tension: 0.3,
        fill: true,
        pointBackgroundColor: '#DC2626',
        pointRadius: 5,
      },
    ],
  };

  const trendOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        ticks: { stepSize: 5 },
        grid: { color: '#F1F5F9' },
      },
      x: { grid: { display: false } },
    },
    plugins: {
      legend: { display: false },
    },
  };

  // Flagged students for quick review alerts
  const recentAlerts = currentSemesterEvaluations
    .filter((e) => e.isFlagged)
    .slice(0, 6);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner / Welcome Info */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem 1.5rem',
          border: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Academic Performance & Monitoring Dashboard
          </h2>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
            Real-time evaluation based on 143 students, 40 courses, and 2,460 recorded enrollments.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Link to="/probation" className="btn btn-primary" style={{ fontSize: '0.8125rem' }}>
            <AlertOctagon size={15} />
            Review Flagged Students ({summaryMetrics.onProbation})
          </Link>
          <Link to="/reports" className="btn btn-secondary" style={{ fontSize: '0.8125rem' }}>
            <FileText size={15} />
            Generate Reports
          </Link>
        </div>
      </div>

      {/* 4 Core Statistics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <StatCard
          title="TOTAL ENROLLED STUDENTS"
          value={summaryMetrics.totalStudents}
          subtitle="Registered this academic session"
          icon={Users}
          color="navy"
        />
        <StatCard
          title="GOOD STANDING"
          value={summaryMetrics.goodStanding}
          subtitle={`${Math.round((summaryMetrics.goodStanding / (summaryMetrics.totalStudents || 1)) * 100)}% satisfactory progress`}
          icon={CheckCircle2}
          color="green"
        />
        <StatCard
          title="STUDENTS AT RISK"
          value={summaryMetrics.atRisk}
          subtitle="Borderline GPA (1.50 - 1.99)"
          icon={AlertTriangle}
          color="amber"
        />
        <StatCard
          title="ON ACADEMIC PROBATION"
          value={summaryMetrics.onProbation}
          subtitle={`Requires academic advisor review`}
          icon={AlertOctagon}
          color="red"
        />
      </div>

      {/* 3 Main Visual Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
        {/* Chart 1: Standing Distribution */}
        <div className="card" style={{ height: '340px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-header">
            <span className="card-title">Academic Standing Distribution</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Active Semester</span>
          </div>
          <div style={{ flex: 1, position: 'relative' }}>
            <Doughnut data={standingData} options={standingOptions} />
          </div>
        </div>

        {/* Chart 2: Performance by Level */}
        <div className="card" style={{ height: '340px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-header">
            <span className="card-title">Average GPA by Level</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>5.0 Point Scale</span>
          </div>
          <div style={{ flex: 1, position: 'relative' }}>
            <Bar data={performanceData} options={performanceOptions} />
          </div>
        </div>

        {/* Chart 3: Probation Trends */}
        <div className="card" style={{ height: '340px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-header">
            <span className="card-title">Probation Trends</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Semester-on-Semester</span>
          </div>
          <div style={{ flex: 1, position: 'relative' }}>
            <Line data={probationTrendData} options={trendOptions} />
          </div>
        </div>
      </div>

      {/* Lower Grid: Recent Probation Alerts & Academic Activities */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1rem' }}>
        {/* Recent Probation Alerts */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Recent Probation Flags</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Flagged automatically by the automated evaluation engine
              </div>
            </div>
            <Link to="/probation" style={{ fontSize: '0.8125rem', color: 'var(--primary-green)', fontWeight: 600, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              View All <ArrowRight size={14} />
            </Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {recentAlerts.length === 0 ? (
              <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                No flagged students for this semester.
              </div>
            ) : (
              recentAlerts.map((st) => (
                <div
                  key={st.matric_no}
                  style={{
                    padding: '0.75rem',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--text-primary)' }}>
                      {st.name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      {st.matric_no} • Level {st.level} • GPA: {st.gpa !== null ? st.gpa.toFixed(2) : 'N/A'}
                    </div>
                    <div style={{ fontSize: '0.7125rem', color: '#DC2626', fontWeight: 600, marginTop: '2px' }}>
                      {st.reasons.join('; ')}
                    </div>
                  </div>
                  <StatusBadge standing={st.standing} />
                </div>
              ))
            )}
          </div>
        </div>

        {/* Academic Governance & System Summary */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Governance & Decision Log</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Workflow Actions</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <div style={{ width: 32, height: 32, borderRadius: '6px', backgroundColor: '#E8FBF5', color: '#087B5B', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <Clock size={16} />
              </div>
              <div style={{ fontSize: '0.8125rem' }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  Automated Engine Verification Complete
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                  Evaluated 143 student academic records across semesters against university thresholds.
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <div style={{ width: 32, height: 32, borderRadius: '6px', backgroundColor: '#FEF3C7', color: '#D97706', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <AlertTriangle size={16} />
              </div>
              <div style={{ fontSize: '0.8125rem' }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  Academic Advisor Alerts Dispatched
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                  Notifications routed to respective academic advisors for counseling and study plan review.
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <div style={{ width: 32, height: 32, borderRadius: '6px', backgroundColor: '#EDF2F9', color: '#142B4A', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <TrendingUp size={16} />
              </div>
              <div style={{ fontSize: '0.8125rem' }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  Probation Committee Panel Active
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                  Panel status recorded: Active cases can be reviewed or cleared in the Probation Monitoring module.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

