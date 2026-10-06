'use client';

import React from 'react';
import Link from 'next/link';
import {
  MapPin, Zap, Shield, Coffee, ShoppingBag, Truck,
  BookOpen, Landmark, ArrowRight, CheckCircle2, Star
} from 'lucide-react';

/* ── Section wrapper ─────────────────────────────────────────────────────── */
function Section({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <section className={`relative py-24 px-6 md:px-12 lg:px-24 ${className}`}>
      {children}
    </section>
  );
}

/* ── Section heading ─────────────────────────────────────────────────────── */
function Heading({ eyebrow, title, sub }: { eyebrow: string; title: React.ReactNode; sub?: string }) {
  return (
    <div className="text-center mb-14">
      <p className="text-xs font-semibold tracking-[0.2em] uppercase text-sky-400 mb-3">{eyebrow}</p>
      <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight text-slate-100 leading-tight mb-4">
        {title}
      </h2>
      {sub && <p className="text-slate-400 max-w-xl mx-auto text-base">{sub}</p>}
    </div>
  );
}

/* ── How It Works ────────────────────────────────────────────────────────── */
const STEPS = [
  {
    n: '01',
    icon: <Shield className="w-6 h-6 text-sky-400" />,
    title: 'Sign in with Google',
    desc: 'One click — no passwords. We only ask for your name and email.',
  },
  {
    n: '02',
    icon: <BookOpen className="w-6 h-6 text-teal-400" />,
    title: 'Complete Onboarding',
    desc: 'Tell us your visa type, work-hour cap, location, and what kinds of jobs you want.',
  },
  {
    n: '03',
    icon: <MapPin className="w-6 h-6 text-violet-400" />,
    title: 'We Discover Employers',
    desc: 'JobBridge queries real map data to find cafés, retail stores, and campus roles near you.',
  },
  {
    n: '04',
    icon: <Zap className="w-6 h-6 text-amber-400" />,
    title: 'Get Matched Jobs',
    desc: 'Jobs are filtered by your visa restrictions and ranked by distance + fit.',
  },
];

function HowItWorks() {
  return (
    <Section className="border-t border-white/5">
      <Heading
        eyebrow="How It Works"
        title={<>Four steps to your<br /><span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-teal-300">next job</span></>}
        sub="No scraping job boards manually. JobBridge does the discovery for you."
      />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
        {STEPS.map((s) => (
          <div
            key={s.n}
            className="relative rounded-2xl border border-white/8 bg-white/2 p-6 hover:border-sky-400/30 hover:bg-white/4 transition-all duration-300 group"
          >
            <div className="absolute top-4 right-4 text-5xl font-black text-white/3 select-none group-hover:text-white/6 transition-colors">
              {s.n}
            </div>
            <div className="mb-4 w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
              {s.icon}
            </div>
            <h3 className="text-base font-bold text-slate-200 mb-2">{s.title}</h3>
            <p className="text-sm text-slate-400 leading-relaxed">{s.desc}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ── Job Categories ──────────────────────────────────────────────────────── */
const CATEGORIES = [
  { icon: <Coffee className="w-5 h-5" />, label: 'Cafés & Food', color: 'text-amber-400', bg: 'bg-amber-400/10' },
  { icon: <ShoppingBag className="w-5 h-5" />, label: 'Retail', color: 'text-sky-400', bg: 'bg-sky-400/10' },
  { icon: <Truck className="w-5 h-5" />, label: 'Delivery', color: 'text-teal-400', bg: 'bg-teal-400/10' },
  { icon: <BookOpen className="w-5 h-5" />, label: 'Tutoring', color: 'text-violet-400', bg: 'bg-violet-400/10' },
  { icon: <Landmark className="w-5 h-5" />, label: 'Campus Jobs', color: 'text-rose-400', bg: 'bg-rose-400/10' },
  { icon: <Shield className="w-5 h-5" />, label: 'Warehousing', color: 'text-orange-400', bg: 'bg-orange-400/10' },
];

function Categories() {
  return (
    <Section className="border-t border-white/5 bg-white/1">
      <Heading
        eyebrow="Job Categories"
        title="Every kind of student job"
        sub="From weekend barista shifts to on-campus research assistant roles — we cover them all."
      />
      <div className="flex flex-wrap justify-center gap-4 max-w-3xl mx-auto">
        {CATEGORIES.map((c) => (
          <div
            key={c.label}
            className={`flex items-center gap-2.5 px-5 py-3 rounded-2xl border border-white/8 ${c.bg} hover:border-white/20 transition-all duration-200 cursor-default`}
          >
            <span className={c.color}>{c.icon}</span>
            <span className="text-sm font-medium text-slate-200">{c.label}</span>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ── Features grid ───────────────────────────────────────────────────────── */
const FEATURES = [
  {
    title: 'Map-Based Discovery',
    desc: 'We use OpenStreetMap Overpass API to find real employers near your campus or home — no scraped brand lists.',
    icon: <MapPin className="w-5 h-5 text-sky-400" />,
  },
  {
    title: 'Visa Filter',
    desc: 'Your work-hour cap (e.g., 48 hrs/fortnight on a student visa) is applied to every job — no nasty surprises.',
    icon: <Shield className="w-5 h-5 text-teal-400" />,
  },
  {
    title: 'Careers Page Finder',
    desc: 'For each employer we find, JobBridge automatically locates their careers page and extracts live job listings.',
    icon: <Zap className="w-5 h-5 text-violet-400" />,
  },
  {
    title: 'Cold Email Drafts',
    desc: 'No online listing? No problem. Connect Gmail and we\'ll draft a personalised cold email for you.',
    icon: <Star className="w-5 h-5 text-amber-400" />,
  },
];

function Features() {
  return (
    <Section className="border-t border-white/5">
      <Heading
        eyebrow="Features"
        title={<>Built for the<br /><span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-sky-400">international student</span></>}
      />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 max-w-4xl mx-auto">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className="rounded-2xl border border-white/8 bg-white/2 p-7 hover:border-sky-400/25 hover:bg-white/4 transition-all duration-300"
          >
            <div className="mb-4 w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center">
              {f.icon}
            </div>
            <h3 className="text-base font-bold text-slate-200 mb-2">{f.title}</h3>
            <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ── CTA Banner ──────────────────────────────────────────────────────────── */
function CTABanner() {
  return (
    <Section className="border-t border-white/5">
      <div className="max-w-3xl mx-auto text-center relative">
        {/* Glow */}
        <div className="absolute inset-0 -z-10 bg-gradient-to-r from-sky-600/10 via-teal-500/10 to-violet-600/10 blur-3xl rounded-full" />

        <p className="text-xs font-semibold tracking-[0.2em] uppercase text-teal-400 mb-4">
          Ready to start?
        </p>
        <h2 className="text-3xl md:text-5xl font-extrabold text-slate-100 mb-5 tracking-tight">
          Your next job is<br />closer than you think
        </h2>
        <p className="text-slate-400 mb-8 text-base">
          Sign in with Google, complete your profile in 3 minutes, and let JobBridge find employers near you.
        </p>

        <div className="flex flex-wrap justify-center gap-4">
          <Link
            href="/login"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl font-bold text-sm bg-gradient-to-r from-sky-500 to-teal-400 text-white shadow-xl shadow-sky-500/25 hover:shadow-sky-500/40 hover:scale-105 transition-all duration-200"
          >
            Get Started — It&apos;s Free
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Trust signals */}
        <div className="mt-8 flex flex-wrap justify-center gap-5 text-xs text-slate-500">
          {['No credit card required', 'Works in AU, UK, US', 'Visa-aware from day 1'].map((t) => (
            <span key={t} className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-500" />
              {t}
            </span>
          ))}
        </div>
      </div>
    </Section>
  );
}

/* ── Footer ──────────────────────────────────────────────────────────────── */
function Footer() {
  return (
    <footer className="border-t border-white/5 py-10 px-6 text-center">
      <p className="text-slate-600 text-xs">
        © 2026 JobBridge — Built for international students.
      </p>
    </footer>
  );
}

/* ── Export ──────────────────────────────────────────────────────────────── */
export default function JobBridgeLanding() {
  return (
    <div className="bg-[#020817] text-slate-100">
      <HowItWorks />
      <Categories />
      <Features />
      <CTABanner />
      <Footer />
    </div>
  );
}
