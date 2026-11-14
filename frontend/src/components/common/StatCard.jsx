import React from 'react';

export const StatCard = ({ title, value, subtitle, icon: Icon, color = 'green', trend }) => {
  const colorMap = {
    green: { bg: '#E8FBF5', text: '#087B5B' },
    navy: { bg: '#EDF2F9', text: '#142B4A' },
    amber: { bg: '#FEF3C7', text: '#D97706' },
    red: { bg: '#FEE2E2', text: '#DC2626' },
  };

  const selectedColor = colorMap[color] || colorMap.green;

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          {title}
        </span>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: '8px',
            backgroundColor: selectedColor.bg,
            color: selectedColor.text,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {Icon && <Icon size={18} />}
        </div>
      </div>
      <div>
        <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1.1 }}>
          {value}
        </div>
        {subtitle && (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
            {subtitle}
          </div>
        )}
      </div>
    </div>
  );
};

export default StatCard;

