'use client';

import React from 'react';

export default function DarkGradientHero() {
  const [mobileOpen, setMobileOpen] = React.useState(false);

  React.useEffect(() => {
    const onEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMobileOpen(false);
    };
    if (mobileOpen) {
      document.addEventListener('keydown', onEsc);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.removeEventListener('keydown', onEsc);
      document.body.style.overflow = '';
    };
  }, [mobileOpen]);

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap');
        * { font-family: 'Poppins', sans-serif; }
      `}</style>

      <section
        className="relative flex flex-col items-center justify-center 
                   w-full min-h-screen bg-black text-white 
                   bg-[url('https://cdn.21st.dev/assets/mirror/09/09bbb3e2821571d0229c113a8823333d32c9bf83242c9103a51b83495bf1a02f.svg')] 
                   bg-center bg-cover pb-16 pt-8"
      >
        <nav className="flex items-center border mx-auto w-full max-w-7xl px-6 py-4 border-slate-700 rounded-full text-white text-sm">
          {/* Logo */}
          <a href="/" aria-label="JobBridge home" className="flex items-center gap-2 font-semibold text-lg">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/>
              <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
            </svg>
            JobBridge
          </a>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-6 ml-7">
            {['Jobs', 'Onboarding', 'Settings', 'About'].map((label) => (
              <a key={label} href={`/${label.toLowerCase()}`} className="relative overflow-hidden h-6 group">
                <span className="block group-hover:-translate-y-full transition-transform duration-300">{label}</span>
                <span className="block absolute top-full left-0 group-hover:translate-y-[-100%] transition-transform duration-300">{label}</span>
              </a>
            ))}
          </div>

          {/* Desktop CTA buttons */}
          <div className="hidden ml-auto md:flex items-center gap-4">
            <a href="/login" className="border border-slate-600 hover:bg-slate-800 px-4 py-2 rounded-full text-sm font-medium transition">
              Sign In
            </a>
            <a href="/login" className="bg-white hover:shadow-[0px_0px_30px_14px] shadow-[0px_0px_30px_7px] hover:shadow-white/50 shadow-white/50 text-black px-4 py-2 rounded-full text-sm font-medium hover:bg-slate-100 transition duration-300">
              Get Started
            </a>
          </div>

          {/* Mobile hamburger */}
          <button
            aria-label="Open menu"
            className="md:hidden text-gray-400 hover:text-gray-200 ml-auto"
            onClick={() => setMobileOpen((v) => !v)}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {/* Mobile overlay */}
          <div
            role="dialog"
            aria-modal="true"
            className={[
              'absolute top-0 left-0 w-full h-screen bg-black text-base md:hidden flex-col items-center justify-center gap-4',
              mobileOpen ? 'flex' : 'hidden',
            ].join(' ')}
          >
            {['Jobs', 'Onboarding', 'Settings', 'About'].map((label) => (
              <a key={label} href={`/${label.toLowerCase()}`} className="hover:text-indigo-400" onClick={() => setMobileOpen(false)}>
                {label}
              </a>
            ))}
            <a href="/login" onClick={() => setMobileOpen(false)} className="border border-slate-600 hover:bg-slate-800 px-4 py-2 rounded-full text-sm font-medium transition">
              Sign In
            </a>
            <a href="/login" onClick={() => setMobileOpen(false)} className="bg-white hover:shadow-[0px_0px_30px_7px] shadow-white/50 text-black px-4 py-2 rounded-full text-sm font-medium hover:bg-slate-100 transition duration-300">
              Get Started
            </a>
            <button
              aria-label="Close menu"
              className="absolute top-5 right-5 p-2 rounded-full border border-white/10 hover:bg-white/10"
              onClick={() => setMobileOpen(false)}
            >
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="M18 6 6 18" />
                <path d="m6 6 12 12" />
              </svg>
            </button>
          </div>
        </nav>

        {/* Announcement pill */}
        <div className="flex items-center gap-2 border border-white/15 rounded-full px-4 py-2 text-sm mt-24 mx-auto">
          <p>🌏 Discover jobs that respect your visa & hours.</p>
          <a href="/jobs" className="flex items-center gap-1 font-medium">
            Browse jobs
            <svg className="mt-0.5" width="19" height="19" viewBox="0 0 19 19" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
              <path d="M3.959 9.5h11.083m0 0L9.501 3.96m5.541 5.54-5.541 5.542" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </a>
        </div>

        {/* Headline */}
        <h1 className="text-4xl md:text-6xl text-center font-semibold max-w-3xl mt-5 bg-gradient-to-r from-white to-[#748298] text-transparent bg-clip-text">
          Your Bridge to Jobs That Work for You
        </h1>
        <p className="text-slate-300 md:text-base line-clamp-3 max-md:px-2 text-center max-w-2xl mt-3">
          International student? We match you with flexible, visa-friendly jobs near your campus — filtered by your work-hour cap, skills, and language level.
        </p>

        {/* CTA buttons */}
        <div className="grid grid-cols-2 gap-2 mt-8 text-sm">
          <a href="/login" className="px-8 py-3 bg-indigo-600 hover:bg-indigo-700 transition rounded-full text-center">Get Started</a>
          <a href="/jobs" className="flex items-center gap-2 bg-white/10 border border-white/15 rounded-full px-6 py-3">
            <span>Browse Jobs</span>
            <svg className="mt-0.5" width="6" height="8" viewBox="0 0 6 8" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
              <path d="M1.25.5 4.75 4l-3.5 3.5" stroke="currentColor" strokeOpacity=".4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </a>
        </div>

        {/* Student/professional photos */}
        <div aria-label="Students working abroad" className="mt-12 flex max-md:overflow-x-auto gap-6 max-w-4xl w-full pb-6 mx-auto justify-center">
          <img
            alt="Student working"
            className="w-36 h-44 rounded-lg hover:-translate-y-1 transition duration-300 object-cover flex-shrink-0"
            height={140} width={120}
            src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=240&h=320&fit=crop"
          />
          <img
            alt="International student"
            className="w-36 h-44 rounded-lg hover:-translate-y-1 transition duration-300 object-cover flex-shrink-0"
            height={140} width={120}
            src="https://images.unsplash.com/photo-1529390079861-591de354faf5?w=240&h=320&fit=crop"
          />
          <img
            alt="Young professional"
            className="w-36 h-44 rounded-lg hover:-translate-y-1 transition duration-300 object-cover flex-shrink-0"
            height={140} width={120}
            src="https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=240&h=320&fit=crop"
          />
          <img
            alt="Student on laptop"
            className="w-36 h-44 rounded-lg hover:-translate-y-1 transition duration-300 object-cover flex-shrink-0"
            height={140} width={120}
            src="https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=240&h=320&fit=crop"
          />
          <img
            alt="Diverse students"
            className="w-36 h-44 rounded-lg hover:-translate-y-1 transition duration-300 object-cover flex-shrink-0"
            height={140} width={120}
            src="https://images.unsplash.com/photo-1543269865-cbf427effbad?w=240&h=320&fit=crop"
          />
        </div>
      </section>
    </>
  );
}
