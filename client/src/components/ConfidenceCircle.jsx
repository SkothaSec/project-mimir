import React from "react";

export default function ConfidenceCircle({ value = 0, size = 44 }) {
  const val = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <svg viewBox="0 0 36 36" style={{ width: size, height: size }}>
      <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#e01cd5" />
          <stop offset="100%" stopColor="#1CB5E0" />
        </linearGradient>
      </defs>
      <path
        d="M18 2.0845
           a 15.9155 15.9155 0 0 1 0 31.831
           a 15.9155 15.9155 0 0 1 0 -31.831"
        fill="none"
        stroke="rgba(255,255,255,0.08)"
        strokeWidth="3"
      />
      <path
        stroke="url(#grad1)"
        strokeDasharray={`${val}, 100`}
        d="M18 2.0845
           a 15.9155 15.9155 0 0 1 0 31.831
           a 15.9155 15.9155 0 0 1 0 -31.831"
        fill="none"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <text x="18" y="21" fill="#e8edf7" fontSize="10" textAnchor="middle">
        {Math.round(val)}
      </text>
    </svg>
  );
}
