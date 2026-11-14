import React from 'react';
import { CheckCircle2, AlertTriangle, AlertOctagon, XCircle } from 'lucide-react';

export const StatusBadge = ({ standing }) => {
  switch (standing) {
    case 'Good Standing':
      return (
        <span className="badge badge-good">
          <CheckCircle2 size={13} />
          Good Standing
        </span>
      );
    case 'At Risk':
      return (
        <span className="badge badge-risk">
          <AlertTriangle size={13} />
          At Risk
        </span>
      );
    case 'Probation':
      return (
        <span className="badge badge-probation">
          <AlertOctagon size={13} />
          Probation
        </span>
      );
    case 'Critical Risk':
      return (
        <span className="badge badge-critical">
          <XCircle size={13} />
          Critical Risk
        </span>
      );
    default:
      return <span className="badge">{standing || 'Unknown'}</span>;
  }
};

export default StatusBadge;

