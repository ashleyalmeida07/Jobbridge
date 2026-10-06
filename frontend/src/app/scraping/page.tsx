'use client';
import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { getScrapeStatus, startScrape } from '@/lib/api';
import { Check, AlertCircle, Search, Briefcase, Globe, MapPin, CheckCircle2, Loader2, AlertTriangle } from "lucide-react";
import { AppSidebarLayout } from '@/components/ui/app-sidebar-layout';
import { useAuth } from '@/lib/auth-context';
import { Timeline } from '@/components/ui/timeline';

const SCAN_STEPS = [
  { id: 1, label: 'Initializing', description: 'Setting up scan parameters' },
  { id: 2, label: 'Searching', description: 'Scanning job boards' },
  { id: 3, label: 'Matching', description: 'Finding relevant jobs' },
  { id: 4, label: 'Complete', description: 'Finalizing results' },
];

export default function ScrapingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const autoStart = searchParams?.get('autostart') === 'true';
  const { user, loading } = useAuth();

  const [status, setStatus] = useState<'idle' | 'pending' | 'running' | 'done' | 'failed'>('idle');
  const [jobCount, setJobCount] = useState(0);
  const [message, setMessage] = useState('Ready to scan for jobs');
  const [dots, setDots] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [starting, setStarting] = useState(false);
  const [hasAutoStarted, setHasAutoStarted] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  /* Animated dots */
  useEffect(() => {
    const id = setInterval(() => setDots(d => d.length < 3 ? d + '.' : ''), 500);
    return () => clearInterval(id);
  }, []);

  /* Auto-start if coming from jobs page */
  useEffect(() => {
    if (!loading && user && autoStart && status === 'idle' && !starting && !hasAutoStarted) {
      setHasAutoStarted(true);
      handleStartScan();
    }
  }, [loading, user, autoStart, status, starting, hasAutoStarted]);

  /* Poll every 1 second when scanning */
  useEffect(() => {
    if (status === 'idle') return;

    const poll = async () => {
      try {
        const res = await getScrapeStatus();
        setStatus(res.status);
        setJobCount(res.job_count);

        if (res.message && res.message !== message) {
          setMessage(res.message);
          setLogs(prev => {
            if (prev.length === 0 || prev[prev.length - 1] !== res.message) {
              return [...prev, res.message!];
            }
            return prev;
          });
        }

        // Update step based on status and message
        if (res.status === 'done') {
          setCurrentStep(4);
        } else if (res.status === 'running') {
          if (res.message?.toLowerCase().includes('matching') || res.message?.toLowerCase().includes('filter')) {
            setCurrentStep(3);
          } else if (res.message?.toLowerCase().includes('scan') || res.message?.toLowerCase().includes('scraping')) {
            setCurrentStep(2);
          } else {
            setCurrentStep(1);
          }
        } else if (res.status === 'pending') {
          setCurrentStep(1);
        }

        if (res.status === 'done' || res.status === 'failed') {
          setTimeout(() => router.replace('/jobs'), 3000);
        }
      } catch (err: any) {
        console.error('Poll error:', err);
        // Don't show poll errors to user unless it's persistent
      }
    };

    poll();
    const id = setInterval(poll, 1000);
    return () => clearInterval(id);
  }, [router, message, status]);

  /* Auto-scroll logs */
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const handleStartScan = async () => {
    setStarting(true);
    setErrorDetails(null);
    try {
      await startScrape();
      setStatus('pending');
      setLogs(['Initializing scraping engine...']);
      setMessage('Initializing scraping engine');
      setCurrentStep(1);
    } catch (e: any) {
      console.error('Scan start error:', e);
      setStatus('failed');
      const errorMsg = e?.message || 'Failed to start scan';
      setMessage(errorMsg);
      setErrorDetails(errorMsg);
      setLogs([`Error: ${errorMsg}`]);
      setTimeout(() => {
        router.replace('/jobs');
      }, 5000);
    } finally {
      setStarting(false);
    }
  };

  const isDone = status === 'done';
  const isFailed = status === 'failed';
  const isScanning = status === 'pending' || status === 'running';

  if (loading) {
    return (
      <AppSidebarLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </AppSidebarLayout>
    );
  }

  return (
    <AppSidebarLayout>
      <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 text-slate-900 flex flex-col items-center justify-center px-4 py-12">
        {status === 'idle' ? (
          <div className="flex flex-col items-center gap-8 max-w-4xl w-full">
            {/* Header */}
            <div className="text-center space-y-3">
              <h1 className="text-4xl font-bold text-slate-900 tracking-tight">Job Scanner</h1>
              <p className="text-lg text-slate-600 max-w-2xl mx-auto">
                Discover opportunities perfectly matched to your profile, visa status, and location preferences
              </p>
            </div>

            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-8">
              <div className="group bg-white border border-slate-200 rounded-2xl p-8 shadow-sm hover:shadow-xl hover:border-indigo-200 transition-all duration-300">
                <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                  <Briefcase className="w-7 h-7 text-white" />
                </div>
                <h3 className="font-bold text-slate-900 mb-2 text-lg">Smart Matching</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Advanced algorithms match jobs to your skills, experience, and career preferences
                </p>
              </div>

              <div className="group bg-white border border-slate-200 rounded-2xl p-8 shadow-sm hover:shadow-xl hover:border-indigo-200 transition-all duration-300">
                <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                  <Globe className="w-7 h-7 text-white" />
                </div>
                <h3 className="font-bold text-slate-900 mb-2 text-lg">Multi-Source</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Aggregates opportunities from major job boards and company career pages
                </p>
              </div>

              <div className="group bg-white border border-slate-200 rounded-2xl p-8 shadow-sm hover:shadow-xl hover:border-indigo-200 transition-all duration-300">
                <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                  <MapPin className="w-7 h-7 text-white" />
                </div>
                <h3 className="font-bold text-slate-900 mb-2 text-lg">Location Filter</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Shows only positions within your specified commute radius
                </p>
              </div>
            </div>

            {/* CTA */}
            <div className="flex flex-col items-center gap-5 mt-8">
              <button
                onClick={handleStartScan}
                disabled={starting}
                className="group px-10 py-4 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white font-bold rounded-xl shadow-lg hover:shadow-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3 text-lg active:scale-[0.97]"
              >
                {starting ? (
                  <>
                    <Loader2 className="w-6 h-6 animate-spin" />
                    Starting Scan...
                  </>
                ) : (
                  <>
                    <Search className="w-6 h-6 group-hover:scale-110 transition-transform" />
                    Start Job Scan
                  </>
                )}
              </button>
              <p className="text-sm text-slate-500">
                Typically completes in 30-60 seconds
              </p>
            </div>

            {/* Back Link */}
            <button
              onClick={() => router.push('/jobs')}
              className="text-sm text-slate-500 hover:text-indigo-600 transition font-medium mt-4 hover:underline"
            >
              ← Back to Dashboard
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-8 max-w-4xl w-full">
            {/* Status Header */}
            <div className="text-center space-y-2">
              <h2 className="text-3xl font-bold text-slate-900">
                {isDone ? `✓ Found ${jobCount} Jobs` : isFailed ? 'Scan Encountered an Issue' : 'Scanning for Jobs'}
              </h2>
              <p className="text-slate-600 text-lg">
                {isDone
                  ? 'Great! Redirecting you to your personalized job feed...'
                  : isFailed
                  ? 'We encountered a technical issue. Taking you back to dashboard...'
                  : 'Searching for the best opportunities tailored to you'}
              </p>
            </div>

            {/* Timeline Progress */}
            {isScanning && (
              <div className="w-full bg-white border border-slate-200 rounded-2xl p-10 shadow-xl">
                <Timeline
                  variant="spacious"
                  items={SCAN_STEPS.map((step, index) => {
                    const isCompleted = index < currentStep;
                    const isCurrent = index === currentStep - 1;
                    
                    let stepStatus: "completed" | "active" | "pending" | "default" = "pending";
                    if (isCompleted) stepStatus = "completed";
                    if (isCurrent) stepStatus = "active";

                    return {
                      id: step.id.toString(),
                      title: step.label,
                      description: step.description,
                      status: stepStatus,
                      content: isCurrent && message ? (
                        <div className="flex items-center gap-2 text-sm text-blue-700 font-medium bg-slate-50/80 p-2.5 rounded-lg border border-slate-100/80 shadow-sm mt-1">
                          <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                          <span>{message}{dots}</span>
                        </div>
                      ) : undefined,
                    };
                  })}
                />
              </div>
            )}

            {/* Error State */}
            {isFailed && (
              <div className="w-full bg-gradient-to-br from-red-50 to-orange-50 border-2 border-red-200 rounded-2xl p-8 shadow-lg">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center shrink-0">
                    <AlertTriangle className="w-6 h-6 text-red-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-red-900 text-lg mb-2">Technical Issue Detected</h3>
                    <p className="text-red-800 text-sm leading-relaxed mb-3">
                      Our system encountered a temporary problem while scanning for jobs.
                      This is usually due to database connectivity or API rate limits.
                    </p>
                    {errorDetails && (
                      <details className="text-xs text-red-700 bg-red-100/50 rounded-lg p-3 font-mono">
                        <summary className="cursor-pointer font-semibold mb-2">Technical Details</summary>
                        <p className="whitespace-pre-wrap break-words">{errorDetails}</p>
                      </details>
                    )}
                    <p className="text-red-800 text-sm mt-4">
                      You'll be redirected to your dashboard shortly. Please try scanning again in a moment.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Success State */}
            {isDone && (
              <div className="w-full bg-gradient-to-br from-emerald-50 to-teal-50 border-2 border-emerald-200 rounded-2xl p-8 shadow-lg">
                <div className="flex items-center justify-center gap-4">
                  <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center">
                    <CheckCircle2 className="w-9 h-9 text-emerald-600" />
                  </div>
                  <div className="text-center">
                    <p className="font-bold text-emerald-900 text-xl">Scan Complete!</p>
                    <p className="text-emerald-800 mt-2">Found {jobCount} matching opportunities for you</p>
                  </div>
                </div>
              </div>
            )}

            {/* Skip Button */}
            {isScanning && (
              <button
                onClick={() => router.push('/jobs')}
                className="text-sm font-medium text-slate-500 hover:text-indigo-600 transition text-center hover:underline"
              >
                Skip to Dashboard (Scan continues in background)
              </button>
            )}
          </div>
        )}
      </main>
    </AppSidebarLayout>
  );
}
