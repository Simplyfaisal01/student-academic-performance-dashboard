/**
 * Configurable Probation & Standing Classification Engine.
 * 
 * Default rules (matches university regulations & settings):
 * - Pass mark: 40
 * - Default Probation GPA threshold: 1.50
 * - Default Max failed courses: 2
 * - Default At-risk GPA range: 1.50 - 1.99
 * - Critical Risk: GPA < 1.00 OR failed courses >= 4
 */

export const DEFAULT_THRESHOLDS = {
  probationGpa: 1.50,
  maxFailedCourses: 2,
  atRiskGpaMin: 1.50,
  atRiskGpaMax: 1.99,
  criticalGpa: 1.00,
  criticalFails: 4,
};

/**
 * Evaluates student performance and returns their standing classification and reasons.
 * @param {number|null} gpa 
 * @param {number} failedCourses 
 * @param {object} thresholds 
 * @returns {{ standing: 'Good Standing' | 'At Risk' | 'Probation' | 'Critical Risk', reasons: string[], isFlagged: boolean }}
 */
export const classifyStanding = (gpa, failedCourses = 0, thresholds = DEFAULT_THRESHOLDS) => {
  const reasons = [];

  if (gpa === null || gpa === undefined) {
    return {
      standing: 'Good Standing',
      reasons: ['No graded courses yet for this session'],
      isFlagged: false,
    };
  }

  const isProbationGpa = gpa < thresholds.probationGpa;
  const isProbationFails = failedCourses > thresholds.maxFailedCourses;
  const isCriticalGpa = gpa < thresholds.criticalGpa;
  const isCriticalFails = failedCourses >= thresholds.criticalFails;

  if (isProbationGpa) {
    reasons.push(`GPA ${gpa.toFixed(2)} below threshold ${thresholds.probationGpa.toFixed(2)}`);
  }
  if (isProbationFails) {
    reasons.push(`${failedCourses} failed courses (max allowed: ${thresholds.maxFailedCourses})`);
  }

  // Classification logic
  if (isCriticalGpa || isCriticalFails) {
    return {
      standing: 'Critical Risk',
      reasons: reasons.length ? reasons : [`Severe academic deficiency detected (GPA: ${gpa.toFixed(2)})`],
      isFlagged: true,
    };
  }

  if (isProbationGpa || isProbationFails) {
    return {
      standing: 'Probation',
      reasons,
      isFlagged: true,
    };
  }

  if ((gpa >= thresholds.atRiskGpaMin && gpa <= thresholds.atRiskGpaMax) || failedCourses > 0) {
    const riskReasons = [];
    if (gpa >= thresholds.atRiskGpaMin && gpa <= thresholds.atRiskGpaMax) {
      riskReasons.push(`Borderline GPA (${gpa.toFixed(2)}) near probation margin`);
    }
    if (failedCourses > 0) {
      riskReasons.push(`${failedCourses} course(s) failed with carryover requirement`);
    }
    return {
      standing: 'At Risk',
      reasons: riskReasons,
      isFlagged: true,
    };
  }

  return {
    standing: 'Good Standing',
    reasons: ['Satisfactory academic progress'],
    isFlagged: false,
  };
};

/**
 * Computes Semester GPA from a list of enrollment records.
 * @param {Array} enrollments Array of { score, grade_point, course: { credit_units } }
 * @returns {number|null}
 */
export const calculateGPA = (enrollments) => {
  let weightedPoints = 0;
  let totalUnits = 0;

  for (const e of enrollments) {
    if (e.grade_point !== null && e.grade_point !== undefined && e.credit_units) {
      weightedPoints += Number(e.grade_point) * Number(e.credit_units);
      totalUnits += Number(e.credit_units);
    }
  }

  if (totalUnits === 0) return null;
  return Number((weightedPoints / totalUnits).toFixed(2));
};

