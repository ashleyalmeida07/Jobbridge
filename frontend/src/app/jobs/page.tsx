'use client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { getJobs, JobItem, JobsResponse, startScrape, EmailStats, getEmailStats } from '@/lib/api';
import { AppSidebarLayout } from '@/components/ui/app-sidebar-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Briefcase, Users, ClipboardList, BarChart3, Search, Mail, ExternalLink, ChevronDown, ChevronUp, X } from 'lucide-react';

const JOB_TYPE_LABELS: Record<string, string> = {
  full_time: 'Full Time',
  part_time: 'Part Time',
  contract: 'Contract',
  internship: 'Internship',
};

const JOB_TYPE_COLORS: Record<string, string> = {
  full_time: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  part_time: 'bg-amber-100 text-amber-800 border-amber-200',
  contract: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  internship: 'bg-purple-100 text-purple-800 border-purple-200',
};

function JobCard({ job }: { job: JobItem }) {
  const [expanded, setExpanded] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const typeLabel = JOB_TYPE_LABELS[job.job_type] ?? job.job_type;
  const typeColor = JOB_TYPE_COLORS[job.job_type] ?? 'bg-slate-100 text-slate-700 border-slate-200';

  return (
    <>
      <div className="flex flex-col gap-2 py-4 border-b border-slate-100 last:border-0 hover:bg-slate-50/50 transition px-2 -mx-2 rounded-lg">
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-col gap-1 min-w-0">
            <h3 className="font-medium text-sm text-slate-900 truncate">
              {job.title}
            </h3>
            <p className="text-xs text-muted-foreground truncate">{job.employer} · {job.location}</p>
          </div>
          <span className={`flex-shrink-0 text-[10px] font-medium px-2 py-0.5 rounded-full border ${typeColor}`}>
            {typeLabel}
          </span>
        </div>

        {job.pay_text && (
          <p className="text-xs text-emerald-600 font-medium">{job.pay_text}</p>
        )}

        {expanded && (
          <p className="text-xs text-slate-600 leading-relaxed mt-2 p-3 bg-slate-50 rounded-md border border-slate-100">
            {job.description || 'No description available.'}
          </p>
        )}

        <div className="flex items-center justify-between mt-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-[11px] font-medium text-slate-500 hover:text-slate-900 transition"
          >
            {expanded ? (
              <><ChevronUp className="w-3.5 h-3.5" /> Show less</>
            ) : (
              <><ChevronDown className="w-3.5 h-3.5" /> Show description</>
            )}
          </button>
          <div className="flex items-center gap-2">
            {job.contact_email && (
              <span className="flex items-center gap-1 text-[11px] font-medium text-indigo-600 bg-indigo-50 px-2 py-1 rounded-md border border-indigo-100">
                <Mail className="w-3 h-3" /> {job.contact_email}
              </span>
            )}
            <button
              onClick={() => setShowModal(true)}
              className="flex items-center gap-1 text-[11px] font-medium text-white bg-slate-900 hover:bg-slate-800 px-3 py-1 rounded-md transition"
            >
              Apply <ExternalLink className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-4xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center p-5 sm:p-6 border-b border-slate-100 bg-white">
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 leading-tight">{job.title}</h2>
                <p className="text-sm font-medium text-slate-500 mt-1">{job.employer} · {job.location}</p>
              </div>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-slate-100 rounded-full transition text-slate-400 hover:text-slate-700">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-5 sm:p-6 overflow-y-auto flex-1 grid lg:grid-cols-5 gap-8 bg-slate-50/30">
              <div className="lg:col-span-3 flex flex-col gap-6">
                <div>
                  <h3 className="font-semibold text-slate-900 mb-3 text-sm uppercase tracking-wider flex items-center gap-2">
                    <Briefcase className="w-4 h-4 text-indigo-500" />
                    Role Overview
                  </h3>
                  <div className="flex flex-wrap items-center gap-2 mb-4">
                    <span className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${typeColor} border`}>
                      {typeLabel}
                    </span>
                    {job.pay_text && (
                      <span className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {job.pay_text}
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="flex-1">
                  <h3 className="font-semibold text-slate-900 mb-3 text-sm uppercase tracking-wider flex items-center gap-2">
                    <ClipboardList className="w-4 h-4 text-indigo-500" />
                    Job Description
                  </h3>
                  <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap bg-white border border-slate-200 p-5 rounded-xl shadow-sm max-h-[400px] overflow-y-auto">
                    {job.description || 'No detailed description found. Please click apply to read more on the source website.'}
                  </div>
                </div>
              </div>

              <div className="lg:col-span-2 flex flex-col gap-6">
                <div>
                  <h3 className="font-semibold text-slate-900 mb-3 text-sm uppercase tracking-wider flex items-center gap-2">
                    <Search className="w-4 h-4 text-indigo-500" />
                    Location Map
                  </h3>
                  <div className="rounded-xl overflow-hidden border border-slate-200 h-[220px] bg-slate-100 shadow-inner">
                    <iframe
                      width="100%"
                      height="100%"
                      frameBorder="0"
                      style={{ border: 0 }}
                      src={`https://www.google.com/maps?q=${encodeURIComponent(job.location || 'Australia')}&output=embed`}
                      title="Job Location"
                    ></iframe>
                  </div>
                </div>

                {job.contact_email && (
                  <div>
                    <h3 className="font-semibold text-slate-900 mb-3 text-sm uppercase tracking-wider flex items-center gap-2">
                      <Mail className="w-4 h-4 text-indigo-500" />
                      Recruiter Contact
                    </h3>
                    <div className="flex items-center gap-3 text-sm text-indigo-900 bg-indigo-50/80 p-4 rounded-xl border border-indigo-100 shadow-sm">
                      <div className="p-2 bg-indigo-100 rounded-lg">
                        <Mail className="w-5 h-5 text-indigo-600" />
                      </div>
                      <div className="flex flex-col">
                        <span className="font-semibold">{job.contact_email}</span>
                        <span className="text-xs text-indigo-600 font-medium mt-0.5">Direct HR Email</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="p-5 sm:p-6 border-t border-slate-100 flex justify-end gap-3 bg-white">
              <button 
                onClick={() => setShowModal(false)}
                className="px-5 py-2.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition shadow-sm"
              >
                Cancel
              </button>
              <a
                href={job.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-6 py-2.5 text-sm font-bold text-white bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 rounded-xl transition shadow-md hover:shadow-lg active:scale-[0.98]"
              >
                Apply on Company Site <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default function JobsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<JobsResponse | null>(null);
  const [emailStats, setEmailStats] = useState<EmailStats | null>(null);
  const [fetching, setFetching] = useState(true);
  const [filter, setFilter] = useState('');
  const [startingScan, setStartingScan] = useState(false);

  const fetchJobs = useCallback(async (jobType?: string) => {
    setFetching(true);
    try {
      const [res, stats] = await Promise.all([
        getJobs({ limit: 100, job_type: jobType || undefined }),
        getEmailStats().catch(() => null)
      ]);
      setData(res);
      if (stats) setEmailStats(stats);
    } catch {
      /* leave null */
    } finally {
      setFetching(false);
    }
  }, []);

  useEffect(() => {
    if (!loading && !user) { router.replace('/login'); return; }
    if (!loading && user && !user.onboarding_done) { router.replace('/onboarding'); return; }
    if (!loading && user) fetchJobs();
  }, [user, loading, router, fetchJobs]);

  const STATS = [
    {
      label: "Total Job Matches",
      value: data?.total || 0,
      hint: "Scraped recently",
      icon: Briefcase,
    },
    {
      label: "HR Contacts Found",
      value: emailStats?.total_contacts || 0,
      hint: "Available for outreach",
      icon: Users,
    },
    { 
      label: "Emails Queued", 
      value: emailStats?.total_pending || 0, 
      hint: "Pending schedule via n8n", 
      icon: ClipboardList 
    },
    {
      label: "Outreach Completed",
      value: emailStats?.total_sent || 0,
      hint: "Total cold emails sent",
      icon: BarChart3,
    },
  ];

  return (
    <AppSidebarLayout>
      <div className="flex flex-1 flex-col gap-6 p-4 sm:p-6 lg:p-8 max-w-[1400px] mx-auto w-full">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-2">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Dashboard</h1>
            <p className="text-sm text-muted-foreground mt-1">Overview of your job matches and cold email campaigns.</p>
          </div>
          <div className="flex items-center gap-2">
            {/* Filter Pills */}
            <div className="hidden md:flex bg-slate-100/80 p-1 rounded-lg border border-slate-200/60 mr-2">
              {[
                { val: '',           label: 'All' },
                { val: 'internship', label: 'Interns' },
                { val: 'full_time',  label: 'Full-time' },
              ].map(f => (
                <button
                  key={f.val}
                  onClick={() => { setFilter(f.val); fetchJobs(f.val || undefined); }}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                    filter === f.val
                      ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                      : 'text-slate-500 hover:text-slate-900 border border-transparent'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
            <button 
              onClick={() => { setStartingScan(true); router.push('/scraping?autostart=true'); }}
              disabled={startingScan}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-slate-900 text-primary-foreground shadow hover:bg-slate-900/90 h-9 px-4 py-2 gap-2"
            >
              {startingScan ? 'Starting...' : 'Rescan Boards'}
            </button>
          </div>
        </div>

        {/* 4 Stats Cards (Same as requested layout) */}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {STATS.map((stat) => (
            <Card key={stat.label} className="shadow-sm border-slate-200/60">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">
                  {stat.label}
                </CardTitle>
                <stat.icon
                  aria-hidden
                  className="size-4 text-muted-foreground/70"
                />
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold tabular-nums text-slate-900">
                  {stat.value}
                </p>
                <p className="text-xs text-muted-foreground mt-1">{stat.hint}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content Area (Two Columns) */}
        <div className="grid gap-6 lg:grid-cols-7 xl:grid-cols-3">
          {/* Active Job Matches */}
          <Card className="lg:col-span-4 xl:col-span-2 shadow-sm border-slate-200/60 flex flex-col min-h-[500px]">
            <CardHeader className="border-b border-slate-100 pb-4">
              <CardTitle>Recent Job Matches</CardTitle>
              <CardDescription>The latest roles found by the scraper matching your profile.</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-4 max-h-[600px]">
              {fetching ? (
                <div className="flex items-center justify-center py-20">
                  <div className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : !data || data.items.length === 0 ? (
                <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
                  <div className="size-12 bg-slate-50 flex items-center justify-center rounded-full border border-slate-100">
                    <Search className="w-5 h-5 text-slate-400" />
                  </div>
                  <p className="text-sm text-slate-500 font-medium">No jobs found. Run a scan!</p>
                </div>
              ) : (
                <div className="flex flex-col gap-6">
                  {Object.entries(
                    data.items.reduce((acc, job) => {
                      const cat = job.category || 'Other';
                      if (!acc[cat]) acc[cat] = [];
                      acc[cat].push(job);
                      return acc;
                    }, {} as Record<string, typeof data.items>)
                  ).map(([cat, jobs]) => (
                    <div key={cat} className="flex flex-col">
                      <div className="sticky top-0 bg-white/95 backdrop-blur z-10 py-2 border-b border-slate-100 mb-2">
                        <h3 className="font-semibold text-slate-900 text-xs uppercase tracking-wider">
                          {cat.replace(/_/g, ' ')} ({jobs.length})
                        </h3>
                      </div>
                      <div className="flex flex-col">
                        {jobs.map(job => <JobCard key={job.id} job={job} />)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Activity / Quick Actions */}
          <Card className="lg:col-span-3 xl:col-span-1 shadow-sm border-slate-200/60">
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Manage your automation</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 bg-slate-50 hover:bg-slate-100/50 transition cursor-pointer" onClick={() => router.push('/email')}>
                <div className="size-8 bg-indigo-100 text-indigo-600 rounded-md flex items-center justify-center shrink-0 border border-indigo-200/50">
                  <Mail className="size-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <h4 className="text-sm font-medium text-slate-900">Cold Email Outreach</h4>
                  <p className="text-xs text-muted-foreground mt-0.5">Queue personalized emails to newly discovered HR contacts.</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 bg-slate-50 hover:bg-slate-100/50 transition cursor-pointer" onClick={() => router.push('/scraping')}>
                <div className="size-8 bg-emerald-100 text-emerald-600 rounded-md flex items-center justify-center shrink-0 border border-emerald-200/50">
                  <Search className="size-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <h4 className="text-sm font-medium text-slate-900">System Logs</h4>
                  <p className="text-xs text-muted-foreground mt-0.5">View real-time scraping progress and automated logs.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppSidebarLayout>
  );
}
