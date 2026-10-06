'use client';

import React from 'react';
import Link from 'next/link';

interface HaosShowcaseProps {
  bg?: React.ReactNode;
  category?: string;
  year?: string | number;
  solutionLabel?: string;
  solutionValue?: string;
  title?: string;
  subtitle?: string;
  statLabel?: string;
  statValue?: string;
  bottomValue?: string;
  progressPercent?: number;
  logoText?: string;
  onAction?: () => void;
  className?: string;
}

export default function HaosShowcase({
  bg,
  category = 'CATEGORY',
  year = 'YEAR',
  solutionLabel = 'TECH SOLUTIONS',
  solutionValue = 'AUTOMATION & ROBOTICS',
  title = 'HAOS Tech Solutions',
  subtitle = 'Brand Concept & Identity',
  statLabel = 'HIGH-QUALITY',
  statValue = 'DEVELOPMENT',
  bottomValue = '+2K',
  progressPercent = 60,
  logoText = 'hAOS',
  onAction = () => {},
  className = '',
}: HaosShowcaseProps) {
  return (
    <section
      className={`haos-container ${className}`}
      role="region"
      aria-label="JobBridge hero showcase"
    >
      {/* Animated canvas background — renders behind everything */}
      {bg && <div className="bg">{bg}</div>}

      {/* ── Top bar ─────────────────────────────────────────────────────── */}
      <div className="grid-item top-left">
        <span className="label">{category}</span>
        <span className="value">{solutionValue}</span>
      </div>

      <div className="grid-item top-center">
        <span className="label">YEAR</span>
        <span className="value">{year}</span>
      </div>

      <div className="grid-item top-right">
        <span className="label">{solutionLabel}</span>
        <span className="value">{solutionValue}</span>
      </div>

      {/* ── Main content (left) ──────────────────────────────────────────── */}
      <div className="grid-item main-content">
        <h1>{title}</h1>
        <h2>{subtitle}</h2>

        <div className="stats-block">
          <span className="label">{statLabel}</span>
          <div className="value">{statValue}</div>
        </div>

        {/* CTA buttons — only shown when this is JobBridge home */}
        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '2rem', flexWrap: 'wrap' }}>
          <Link
            href="/login"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.65rem 1.4rem',
              borderRadius: '0.75rem',
              fontSize: '0.8rem',
              fontWeight: 700,
              background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
              color: '#fff',
              textDecoration: 'none',
              transition: 'opacity 0.2s, transform 0.2s',
              letterSpacing: '0.03em',
            }}
            onMouseOver={e => (e.currentTarget.style.opacity = '0.85')}
            onMouseOut={e => (e.currentTarget.style.opacity = '1')}
          >
            Get Started Free →
          </Link>
          <Link
            href="/jobs"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.65rem 1.4rem',
              borderRadius: '0.75rem',
              fontSize: '0.8rem',
              fontWeight: 600,
              border: '1px solid rgba(255,255,255,0.15)',
              color: '#95bdc9',
              textDecoration: 'none',
              transition: 'border-color 0.2s, color 0.2s',
              letterSpacing: '0.03em',
            }}
            onMouseOver={e => { e.currentTarget.style.borderColor = '#63b3ed'; e.currentTarget.style.color = '#63b3ed'; }}
            onMouseOut={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)'; e.currentTarget.style.color = '#95bdc9'; }}
          >
            Browse Jobs
          </Link>
        </div>
      </div>

      {/* ── Center logo ──────────────────────────────────────────────────── */}
      <div className="grid-item center-logo">
        <div className="haos-logo">{logoText}</div>
      </div>

      {/* ── Bottom bar ───────────────────────────────────────────────────── */}
      <div className="grid-item bottom-left">
        <div className="stats-value">{bottomValue}</div>
        <div
          className="progress-bar"
          role="progressbar"
          aria-valuenow={progressPercent}
          aria-valuemin={0}
          aria-valuemax={100}
          style={{ '--progress': `${progressPercent}%` } as React.CSSProperties}
        />
        <span className="label" style={{ whiteSpace: 'nowrap' }}>Jobs found near you</span>
      </div>

      <div className="grid-item bottom-right">
        <div
          className="action-icon"
          role="button"
          tabIndex={0}
          aria-label="Go to sign in"
          onClick={onAction}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onAction();
            }
          }}
        />
      </div>
    </section>
  );
}
