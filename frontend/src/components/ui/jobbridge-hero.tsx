'use client';

import React, { useRef, useState } from 'react';
import { Component as AnimatedBackground } from '@/components/ui/raycast-animated-blue-background';
import HaosShowcase from '@/components/ui/tech-solutions-hero-section';
import { Briefcase, MapPin, GraduationCap, Globe, ArrowRight, Star, Users, Zap } from 'lucide-react';
import Link from 'next/link';

/* ── Floating badge ─────────────────────────────────────────────────────── */
function Badge({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs text-sky-300 font-medium backdrop-blur-sm">
      {icon}
      {text}
    </span>
  );
}

/* ── Stat card ──────────────────────────────────────────────────────────── */
function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <span className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-teal-300">
        {value}
      </span>
      <span className="text-xs text-slate-400 uppercase tracking-widest">{label}</span>
    </div>
  );
}

/* ── CTA button ─────────────────────────────────────────────────────────── */
function CTAButton({
  href,
  primary,
  children,
}: {
  href: string;
  primary?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={
        primary
          ? 'inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-200 bg-gradient-to-r from-sky-500 to-teal-400 text-white shadow-lg shadow-sky-500/20 hover:shadow-sky-500/40 hover:scale-105 active:scale-95'
          : 'inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-200 border border-white/15 text-slate-300 hover:border-sky-400/50 hover:text-sky-300 hover:bg-white/5 active:scale-95'
      }
    >
      {children}
    </Link>
  );
}

/* ── Main hero section ──────────────────────────────────────────────────── */
export default function JobBridgeHero() {
  const [pressed, setPressed] = useState(false);

  const handleAction = () => {
    setPressed(true);
    setTimeout(() => setPressed(false), 600);
    window.location.href = '/login';
  };

  const mainContent = (
    <div className="flex flex-col gap-5">
      {/* Pill badges */}
      <div className="flex flex-wrap gap-2">
        <Badge icon={<Globe className="w-3 h-3" />} text="Location-Aware" />
        <Badge icon={<GraduationCap className="w-3 h-3" />} text="Student-First" />
        <Badge icon={<Zap className="w-3 h-3" />} text="Instant Matches" />
      </div>

      {/* Headline */}
      <div>
        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight leading-[1.05] text-slate-100">
          Find Jobs That<br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-teal-300 to-violet-400">
            Fit Your Visa
          </span>
        </h1>
        <h2 className="mt-4 text-lg text-slate-400 font-normal max-w-sm">
          JobBridge discovers real employers near you — cafés, retail, campus roles — and checks if you can legally work there.
        </h2>
      </div>

      {/* CTA buttons */}
      <div className="flex flex-wrap gap-3 mt-2">
        <CTAButton href="/login" primary>
          Get Started Free
          <ArrowRight className="w-4 h-4" />
        </CTAButton>
        <CTAButton href="/jobs">
          <Briefcase className="w-4 h-4" />
          Browse Jobs
        </CTAButton>
      </div>

      {/* Stats row */}
      <div className="flex gap-6 mt-4 pt-4 border-t border-white/8">
        <StatCard value="2K+" label="Jobs Found" />
        <StatCard value="50+" label="Cities" />
        <StatCard value="98%" label="Visa Match" />
      </div>
    </div>
  );

  return (
    <div className="relative">
      <HaosShowcase
        bg={<AnimatedBackground />}
        category="STUDENT JOBS"
        year="2026"
        solutionLabel="PLATFORM"
        solutionValue="AI-POWERED MATCHING"
        title="Find Jobs That Fit Your Visa"
        subtitle="Location-Aware · Student-First · Instant Matches"
        statLabel="JOBS DISCOVERED"
        statValue="NEAR YOU"
        bottomValue="+2K"
        progressPercent={72}
        logoText="JB"
        onAction={handleAction}
      />

      {/* Overlay: rich landing content layered on top of the grid */}
      <div className="absolute inset-0 z-20 pointer-events-none">
        {/* Left column content */}
        <div
          className="absolute pointer-events-auto"
          style={{
            top: '50%',
            left: '2rem',
            transform: 'translateY(-50%)',
            width: 'min(480px, 40vw)',
          }}
        >
          {mainContent}
        </div>

        {/* Right column — feature cards */}
        <div
          className="absolute pointer-events-auto flex flex-col gap-3"
          style={{
            top: '50%',
            right: '2rem',
            transform: 'translateY(-50%)',
            width: 'min(280px, 25vw)',
          }}
        >
          <FeatureCard
            icon={<MapPin className="w-4 h-4 text-sky-400" />}
            title="Near You"
            desc="Discover employers within your commute radius using OpenStreetMap data."
          />
          <FeatureCard
            icon={<GraduationCap className="w-4 h-4 text-teal-400" />}
            title="Visa-Aware"
            desc="Every job is filtered against your visa's work-hour caps and restrictions."
          />
          <FeatureCard
            icon={<Users className="w-4 h-4 text-violet-400" />}
            title="Student Community"
            desc="Built by students, for international students navigating work in a new country."
          />
        </div>
      </div>

      {/* Mobile fallback — shown below the grid on small screens */}
      <div className="md:hidden bg-[#020817] px-6 py-10 border-t border-white/8">
        {mainContent}
        <div className="mt-8 flex flex-col gap-3">
          <FeatureCard
            icon={<MapPin className="w-4 h-4 text-sky-400" />}
            title="Near You"
            desc="Jobs discovered within your commute using real map data."
          />
          <FeatureCard
            icon={<GraduationCap className="w-4 h-4 text-teal-400" />}
            title="Visa-Aware"
            desc="Filtered by your visa type and weekly hour cap."
          />
        </div>
      </div>
    </div>
  );
}

/* ── Feature card ───────────────────────────────────────────────────────── */
function FeatureCard({
  icon,
  title,
  desc,
}: {
  icon: React.ReactNode;
  title: string;
  desc: string;
}) {
  return (
    <div className="rounded-xl border border-white/8 bg-white/3 backdrop-blur-sm p-4 hover:border-sky-400/30 hover:bg-white/6 transition-all duration-200">
      <div className="flex items-center gap-2 mb-1.5">
        {icon}
        <span className="text-sm font-semibold text-slate-200">{title}</span>
      </div>
      <p className="text-xs text-slate-400 leading-relaxed">{desc}</p>
    </div>
  );
}
