'use client'
import React from 'react'
import { ChevronRight, Shield, Zap, BarChart3, Users, CheckCircle2, Star, ArrowRight } from 'lucide-react'
import { TimelineAnimation } from '@/components/ui/hero-financial-utils/timeline-animation'
import { useMediaQuery } from '@/components/ui/hero-financial-utils/use-media-query'
import MotionDrawer from '@/components/ui/hero-financial-utils/motion-drawer'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/lib/auth-context'

// Reusable scroll animation wrapper
const FadeIn = ({ children, delay = 0, className = "" }: { children: React.ReactNode, delay?: number, className?: string }) => (
  <motion.div
    initial={{ opacity: 0, y: 40 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-100px" }}
    transition={{ duration: 0.7, delay, ease: "easeOut" }}
    className={className}
  >
    {children}
  </motion.div>
);

export const HeroFinancial = () => {
  const timelineRef = React.useRef<HTMLDivElement>(null)
  const isMobile = useMediaQuery('(max-width: 768px)')
  const { user, loading } = useAuth()

  return (
    <div className="min-h-screen bg-[#f7f9fc] text-[#1e293b] font-sans overflow-x-hidden selection:bg-blue-200">
      
      {/* ─── HERO SECTION ──────────────────────────────────────────────────────── */}
      <section
        ref={timelineRef}
        className="relative flex flex-col items-center pt-4 pb-12 bg-gradient-to-b from-white via-blue-50/50 to-blue-300/40 overflow-hidden"
      >
        {/* Ambient glow effect */}
        <div className="absolute bottom-[-10%] left-1/2 -translate-x-1/2 w-[70%] h-72 bg-blue-500/30 blur-[120px] rounded-full pointer-events-none" />
        {/* Mobile Nav */}
        {isMobile && (
          <div className="flex gap-4 justify-between items-center px-5 w-full pt-4 relative z-20">
            <MotionDrawer
              direction="left"
              width={300}
              backgroundColor={'#ffffff'}
              clsBtnClassName="bg-neutral-800 border-r border-neutral-900 text-white"
              contentClassName="bg-white border-r border-neutral-200 text-black shadow-2xl"
              btnClassName="bg-white text-black relative w-fit p-2 left-0 top-0 rounded-full shadow-xs border border-neutral-200"
            >
              <nav className="space-y-4">
                <div className="flex items-center gap-2 text-black mb-8">
                  <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">J</div>
                  <span className="font-bold text-xl tracking-tight">JobBridge</span>
                </div>
                {user ? (
                  <>
                    <Link href="/jobs" className="block p-3 hover:bg-blue-50 text-neutral-600 hover:text-blue-600 font-medium rounded-lg transition-colors">Dashboard</Link>
                    <Link href="/emails" className="block p-3 hover:bg-blue-50 text-neutral-600 hover:text-blue-600 font-medium rounded-lg transition-colors">Cold Email</Link>
                    <Link href="/automations" className="block p-3 hover:bg-blue-50 text-neutral-600 hover:text-blue-600 font-medium rounded-lg transition-colors">Automations</Link>
                  </>
                ) : (
                  <>
                    <a href="#services" className="block p-3 hover:bg-blue-50 text-neutral-600 hover:text-blue-600 font-medium rounded-lg transition-colors">Our Services</a>
                    <a href="#how-it-works" className="block p-3 hover:bg-blue-50 text-neutral-600 hover:text-blue-600 font-medium rounded-lg transition-colors">How it works</a>
                    <a href="#pricing" className="block p-3 hover:bg-blue-50 text-neutral-600 hover:text-blue-600 font-medium rounded-lg transition-colors">Pricing</a>
                  </>
                )}
              </nav>
            </MotionDrawer>
            <div className="flex items-center gap-3 relative z-20">
              {loading ? (
                <div className="w-8 h-8 rounded-full bg-slate-200 animate-pulse" />
              ) : user ? (
                <Link href="/jobs" className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-full shadow-sm border border-slate-200">
                  <img src={user.avatar} alt={user.name} className="w-6 h-6 rounded-full" />
                  <span className="text-sm font-semibold text-slate-800">{user.name.split(' ')[0]}</span>
                </Link>
              ) : (
                <>
                  <Link href="/login" className="text-sm font-semibold text-slate-700 hover:text-blue-600 transition-colors hidden sm:block">
                    Log in
                  </Link>
                  <Link href="/signup" className="bg-neutral-900 text-white px-4 py-2.5 flex gap-1 items-center rounded-xl font-bold text-sm hover:bg-black transition shadow-[inset_2px_2px_5px_0px_rgba(0,0,0,0.5),inset_-2px_-2px_6px_1px_rgba(80,78,78,0.5)]">
                    Sign up <ChevronRight size={18} />
                  </Link>
                </>
              )}
            </div>
          </div>
        )}

        {/* Desktop Nav */}
        {!isMobile && (
          <header className="relative z-20 w-full max-w-6xl mx-auto px-4 mt-4">
            <TimelineAnimation
              animationNum={1}
              timelineRef={timelineRef}
              className="bg-white/80 backdrop-blur-xl p-3 px-6 rounded-2xl border border-white shadow-sm flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-400 rounded-lg flex items-center justify-center text-white font-bold text-xl shadow-md">J</div>
                <span className="text-xl font-bold tracking-tight text-slate-900">
                  JobBridge
                </span>
              </div>
              <nav className="hidden md:flex items-center gap-8 text-sm font-semibold text-neutral-500">
                {user ? (
                  <>
                    <Link href="/jobs" className="hover:text-blue-600 transition-colors">Dashboard</Link>
                    <Link href="/emails" className="hover:text-blue-600 transition-colors">Cold Email</Link>
                    <Link href="/automations" className="hover:text-blue-600 transition-colors">Automations</Link>
                  </>
                ) : (
                  <>
                    <a href="#services" className="hover:text-blue-600 transition-colors">Our Services</a>
                    <a href="#how-it-works" className="hover:text-blue-600 transition-colors">How it works</a>
                    <a href="#testimonials" className="hover:text-blue-600 transition-colors">Testimonials</a>
                    <a href="#pricing" className="hover:text-blue-600 transition-colors">Pricing</a>
                  </>
                )}
              </nav>
              <div className="flex items-center gap-4">
                {loading ? (
                  <div className="w-10 h-10 rounded-full bg-slate-200 animate-pulse" />
                ) : user ? (
                  <Link href="/jobs" className="flex items-center gap-2 bg-slate-50 hover:bg-slate-100 transition px-2 py-1.5 pr-4 rounded-full border border-slate-200 shadow-sm cursor-pointer active:scale-95">
                    <img src={user.avatar} alt={user.name} className="w-8 h-8 rounded-full border border-slate-200 object-cover" />
                    <span className="text-sm font-bold text-slate-700">{user.name}</span>
                  </Link>
                ) : (
                  <>
                    <Link href="/login" className="text-sm font-semibold text-slate-600 hover:text-blue-600 transition-colors">
                      Log in
                    </Link>
                    <Link href="/signup" className="bg-neutral-900 text-white px-5 py-2.5 flex gap-1 items-center rounded-xl font-bold text-sm hover:bg-black transition shadow-[inset_2px_2px_5px_0px_rgba(0,0,0,0.5),inset_-2px_-2px_6px_1px_rgba(80,78,78,0.5)] active:scale-95">
                      Sign up <ChevronRight size={18} />
                    </Link>
                  </>
                )}
              </div>
            </TimelineAnimation>
          </header>
        )}

        {/* Hero Content */}
        <div className="relative z-10 text-center pt-32 pb-16 px-4 flex flex-col items-center gap-8 w-full max-w-5xl mx-auto">
          
          <TimelineAnimation
            animationNum={1}
            timelineRef={timelineRef}
            className="bg-white w-fit mx-auto text-slate-600 px-4 py-1.5 rounded-full inline-flex items-center gap-2 shadow-sm border border-slate-100 text-xs font-semibold tracking-wide"
          >
            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
            Financial Operations Verified
          </TimelineAnimation>

          <TimelineAnimation
            as="h1"
            animationNum={2}
            timelineRef={timelineRef}
            className="text-6xl sm:text-7xl md:text-[5.5rem] font-normal tracking-tight text-slate-800 leading-[1.1] max-w-4xl"
          >
            Make your <span className="text-blue-500">financial</span> <br className="hidden md:block" /> 
            operations <span className="text-blue-500">seamless.</span>
          </TimelineAnimation>

          <TimelineAnimation
            as="p"
            animationNum={3}
            timelineRef={timelineRef}
            className="text-lg md:text-xl text-slate-500 font-light max-w-2xl mx-auto leading-relaxed px-4"
          >
            Take control of your finances with Startive — the next-generation finance software built to simplify, automate, and elevate your financial operations instantly.
          </TimelineAnimation>

          {/* Feature Chips */}
          <TimelineAnimation as="div" animationNum={4} timelineRef={timelineRef} className="flex flex-wrap justify-center gap-4 mt-8 max-w-4xl">
            {[
              { icon: Shield, label: "Bank-Grade Security" },
              { icon: Zap, label: "Lightning Fast Sync" },
              { icon: CheckCircle2, label: "Instantly Verifiable" },
              { icon: BarChart3, label: "Permanent Record" }
            ].map((chip, i) => (
              <div key={i} className="flex items-center gap-2 px-4 py-2.5 bg-white rounded-xl border border-slate-100 shadow-sm text-sm font-semibold text-slate-700 hover:shadow-md transition-shadow">
                <chip.icon size={16} className="text-blue-500" strokeWidth={2.5} />
                {chip.label}
              </div>
            ))}
          </TimelineAnimation>

        </div>
      </section>

      {/* ─── FEATURES / SERVICES ──────────────────────────────────────────────── */}
      <section id="services" className="py-24 px-6 bg-white relative z-20 border-t border-slate-100">
        <div className="max-w-6xl mx-auto">
          <FadeIn className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-blue-600 font-bold tracking-wide uppercase text-sm mb-3">Core Features</h2>
            <h3 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6 tracking-tight">Everything you need to run your business</h3>
            <p className="text-lg text-slate-500">We've built a comprehensive suite of tools to help you manage revenue, track expenses, and forecast growth.</p>
          </FadeIn>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: Zap, title: "Lightning Fast Sync", desc: "Connect your bank accounts once and we'll sync your transactions in real-time." },
              { icon: Shield, title: "Bank-grade Security", desc: "Your financial data is encrypted at rest and in transit using AES-256." },
              { icon: BarChart3, title: "Smart Analytics", desc: "Generate beautiful, actionable reports with a single click. No excel needed." }
            ].map((feat, i) => (
              <FadeIn key={i} delay={i * 0.15} className="bg-slate-50 border border-slate-100 rounded-3xl p-8 hover:shadow-xl hover:shadow-blue-500/5 transition-all duration-300 hover:-translate-y-1 group">
                <div className="w-14 h-14 bg-blue-100 text-blue-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <feat.icon size={28} strokeWidth={2} />
                </div>
                <h4 className="text-xl font-bold text-slate-900 mb-3">{feat.title}</h4>
                <p className="text-slate-500 leading-relaxed">{feat.desc}</p>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─────────────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-24 px-6 relative z-20">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col lg:flex-row gap-16 items-center">
            <FadeIn className="lg:w-1/2">
              <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-white">
                <img 
                  src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop" 
                  alt="Dashboard Preview" 
                  className="w-full h-auto"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
              </div>
            </FadeIn>
            
            <div className="lg:w-1/2 flex flex-col gap-10">
              <FadeIn>
                <h2 className="text-blue-600 font-bold tracking-wide uppercase text-sm mb-3">How it works</h2>
                <h3 className="text-4xl font-bold text-slate-900 mb-4 tracking-tight">Simplify your workflow in minutes</h3>
                <p className="text-lg text-slate-500">Stop wasting time on manual entry. Startive automates your bookkeeping so you can focus on growing.</p>
              </FadeIn>

              <div className="flex flex-col gap-8">
                {[
                  { num: "01", title: "Connect your accounts", desc: "Securely link your bank, credit cards, and payment processors." },
                  { num: "02", title: "Set your rules", desc: "Create custom categorization rules that match your business logic." },
                  { num: "03", title: "Automate everything", desc: "Watch as transactions are automatically categorized and reconciled." }
                ].map((step, i) => (
                  <FadeIn key={i} delay={i * 0.15} className="flex gap-6">
                    <div className="flex-shrink-0 w-12 h-12 bg-white rounded-full flex items-center justify-center font-bold text-blue-600 border border-blue-100 shadow-sm">
                      {step.num}
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-slate-900 mb-2">{step.title}</h4>
                      <p className="text-slate-500">{step.desc}</p>
                    </div>
                  </FadeIn>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── TESTIMONIALS ─────────────────────────────────────────────────────── */}
      <section id="testimonials" className="py-24 px-6 bg-slate-900 text-white relative z-20 overflow-hidden">
        {/* Dark mode glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-blue-600/20 blur-[120px] rounded-full pointer-events-none"></div>
        
        <div className="max-w-6xl mx-auto relative z-10">
          <FadeIn className="text-center max-w-2xl mx-auto mb-16">
            <h3 className="text-3xl md:text-5xl font-bold mb-6 tracking-tight">Trusted by modern teams</h3>
            <p className="text-lg text-slate-400">Join thousands of founders who have upgraded their financial stack.</p>
          </FadeIn>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { quote: "Startive completely changed how we handle our monthly close. What used to take 5 days now takes 5 hours.", author: "Sarah Jenkins", role: "CFO at TechNova" },
              { quote: "The most beautifully designed financial software I've ever used. The API is robust and the support team is incredible.", author: "Marcus Thorne", role: "Founder of Stacked" },
              { quote: "We migrated from our legacy system in less than a day. The automated categorization saves me hours every week.", author: "Elena Rodriguez", role: "VP Operations, ScaleUp" }
            ].map((test, i) => (
              <FadeIn key={i} delay={i * 0.15} className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-3xl p-8 flex flex-col justify-between">
                <div>
                  <div className="flex gap-1 mb-6 text-amber-400">
                    {[1,2,3,4,5].map(star => <Star key={star} size={18} fill="currentColor" />)}
                  </div>
                  <p className="text-lg text-slate-200 mb-8 leading-relaxed">"{test.quote}"</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full"></div>
                  <div>
                    <h5 className="font-bold text-white">{test.author}</h5>
                    <p className="text-sm text-slate-400">{test.role}</p>
                  </div>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ─── PRICING ──────────────────────────────────────────────────────────── */}
      <section id="pricing" className="py-24 px-6 bg-white relative z-20">
        <div className="max-w-6xl mx-auto">
          <FadeIn className="text-center max-w-2xl mx-auto mb-16">
            <h3 className="text-4xl font-bold text-slate-900 mb-4 tracking-tight">Simple, transparent pricing</h3>
            <p className="text-lg text-slate-500">No hidden fees. No surprise charges. Cancel anytime.</p>
          </FadeIn>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Standard Plan */}
            <FadeIn delay={0.1} className="bg-white border border-slate-200 rounded-3xl p-8 sm:p-10 shadow-lg shadow-slate-200/50 flex flex-col">
              <h4 className="text-2xl font-bold text-slate-900 mb-2">Starter</h4>
              <p className="text-slate-500 mb-6">Perfect for freelancers and solo founders.</p>
              <div className="mb-8">
                <span className="text-5xl font-extrabold text-slate-900">$29</span>
                <span className="text-slate-500 font-medium">/month</span>
              </div>
              <ul className="flex flex-col gap-4 mb-10 flex-1">
                {['Up to 5 bank connections', 'Basic categorization', 'Standard reports', 'Email support'].map((feat, i) => (
                  <li key={i} className="flex items-center gap-3 text-slate-700">
                    <CheckCircle2 size={20} className="text-blue-500 flex-shrink-0" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
              <button className="w-full py-3.5 rounded-xl border-2 border-slate-200 text-slate-700 font-bold hover:border-slate-300 hover:bg-slate-50 transition-colors">
                Start 14-day trial
              </button>
            </FadeIn>

            {/* Pro Plan */}
            <FadeIn delay={0.2} className="bg-slate-900 rounded-3xl p-8 sm:p-10 shadow-xl shadow-blue-900/20 flex flex-col relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-blue-600 text-white text-xs font-bold px-4 py-1.5 rounded-bl-xl uppercase tracking-wider">
                Most Popular
              </div>
              <h4 className="text-2xl font-bold text-white mb-2">Pro</h4>
              <p className="text-slate-400 mb-6">For scaling teams that need more power.</p>
              <div className="mb-8">
                <span className="text-5xl font-extrabold text-white">$99</span>
                <span className="text-slate-400 font-medium">/month</span>
              </div>
              <ul className="flex flex-col gap-4 mb-10 flex-1">
                {['Unlimited connections', 'Custom API access', 'Advanced forecasting', 'Priority 24/7 support', 'Multi-user access'].map((feat, i) => (
                  <li key={i} className="flex items-center gap-3 text-slate-200">
                    <CheckCircle2 size={20} className="text-blue-400 flex-shrink-0" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
              <button className="w-full py-3.5 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-500 transition-colors shadow-lg shadow-blue-600/30">
                Start 14-day trial
              </button>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ─── CTA & FOOTER ─────────────────────────────────────────────────────── */}
      <section className="bg-[#0f172a] text-white pt-24 pb-10 px-6 relative z-20">
        <div className="max-w-4xl mx-auto text-center mb-20">
          <FadeIn>
            <h3 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight">Ready to streamline your finances?</h3>
            <p className="text-xl text-slate-400 mb-10">Join thousands of businesses already using Startive.</p>
            <button className="px-8 bg-blue-600 text-white text-lg font-semibold rounded-xl shadow-lg shadow-blue-600/30 hover:shadow-blue-600/50 transition-all py-4 hover:-translate-y-1 inline-flex items-center gap-2">
              Get Started for Free <ArrowRight size={20} />
            </button>
          </FadeIn>
        </div>

        <div className="max-w-6xl mx-auto border-t border-slate-800 pt-10 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center text-white font-bold text-xs">S</div>
            <span className="font-bold tracking-tight">Startive</span>
          </div>
          
          <div className="flex gap-8 text-sm text-slate-400">
            <a href="#" className="hover:text-white transition">Privacy Policy</a>
            <a href="#" className="hover:text-white transition">Terms of Service</a>
            <a href="#" className="hover:text-white transition">Contact Us</a>
          </div>

          <p className="text-sm text-slate-500">
            © {new Date().getFullYear()} Startive Inc. All rights reserved.
          </p>
        </div>
      </section>

    </div>
  )
}

export default HeroFinancial;
