'use client';
import { useEffect, useState, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { getJobs, JobItem, JobsResponse, startScrape, EmailStats, getEmailStats, getProfile, ProfileData, autoApplyJob } from '@/lib/api';
import { AppSidebarLayout } from '@/components/ui/app-sidebar-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Briefcase, Users, ClipboardList, BarChart3, Search, Mail, ExternalLink, ChevronDown, ChevronUp, X, MapPin, Globe, ShieldCheck, FileText, AlertTriangle, CheckCircle2, ShieldAlert } from 'lucide-react';

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

function JobCard({ job, profile }: { job: JobItem; profile: ProfileData | null }) {
  const [expanded, setExpanded] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [autoApplying, setAutoApplying] = useState(false);
  const typeLabel = JOB_TYPE_LABELS[job.job_type] ?? job.job_type;
  const typeColor = JOB_TYPE_COLORS[job.job_type] ?? 'bg-slate-100 text-slate-700 border-slate-200';

  const handleAutoApply = async () => {
    setAutoApplying(true);
    try {
      await autoApplyJob(job.id);
    } catch (e) {
      alert("Failed to start auto-apply. Make sure you have completed your profile.");
    } finally {
      setTimeout(() => setAutoApplying(false), 2000);
    }
  };

  return (
    <>
      <div className="flex flex-col gap-3 p-5 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-shadow">
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
          <div className="mt-4 flex flex-col gap-4 animate-in slide-in-from-top-2 duration-200">
            {/* Analysis Grid */}
            {job.analysis && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* Visa-Smart Matching */}
                <div className="bg-indigo-50/50 rounded-xl p-3 border border-indigo-100 flex flex-col gap-2">
                  <div className="flex items-center gap-2 text-indigo-700 font-semibold text-xs uppercase tracking-wide">
                    <Globe className="w-3.5 h-3.5" /> Visa-Smart Match
                  </div>
                  <div className="flex flex-col gap-1.5 text-xs text-slate-600">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Sponsorship:</span>
                      <span className="font-medium text-slate-800">{job.analysis.sponsorship || 'Unknown'}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Work Rights Req:</span>
                      <span className="font-medium text-slate-800">{job.analysis.work_rights_required ? 'Yes' : 'No'}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Est. Hours:</span>
                      <span className="font-medium text-slate-800">{job.analysis.hours_per_week || '?'} hrs/wk</span>
                    </div>
                  </div>
                </div>

                {/* Trust & Pay Check */}
                <div className="bg-emerald-50/50 rounded-xl p-3 border border-emerald-100 flex flex-col gap-2">
                  <div className="flex items-center gap-2 text-emerald-700 font-semibold text-xs uppercase tracking-wide">
                    <ShieldCheck className="w-3.5 h-3.5" /> Trust & Pay Check
                  </div>
                  <div className="flex flex-col gap-1.5 text-xs text-slate-600">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Trust Score:</span>
                      <span className={`font-medium ${job.analysis.trust_score && job.analysis.trust_score >= 80 ? 'text-emerald-600' : 'text-amber-600'}`}>
                        {job.analysis.trust_score ? `${job.analysis.trust_score}/100` : 'Pending'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Pay Fairness:</span>
                      <span className="font-medium text-slate-800 capitalize">{job.analysis.pay_label || 'Unknown'}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Red Flags:</span>
                      <span className="font-medium text-slate-800">{job.analysis.red_flags?.length || 0}</span>
                    </div>
                  </div>
                </div>

                {/* Local Apply Kit */}
                <div className="bg-blue-50/50 rounded-xl p-3 border border-blue-100 flex flex-col gap-2">
                  <div className="flex items-center gap-2 text-blue-700 font-semibold text-xs uppercase tracking-wide">
                    <FileText className="w-3.5 h-3.5" /> Local Apply Kit
                  </div>
                  <div className="flex flex-col gap-1.5 text-xs text-slate-600">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Resume Match:</span>
                      <span className="font-medium text-blue-600">85% Match</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Language Req:</span>
                      <span className="font-medium text-slate-800">{job.analysis.language_requirement || 'English'}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Description */}
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
              <h4 className="font-semibold text-slate-800 text-xs uppercase tracking-wide mb-2 flex items-center gap-1.5">
                <ClipboardList className="w-3.5 h-3.5 text-slate-400" /> Job Description
              </h4>
              <p className="text-xs text-slate-600 leading-relaxed whitespace-pre-wrap max-h-40 overflow-y-auto pr-2">
                {job.description || 'No description available.'}
              </p>
            </div>
          </div>
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
                <div className="flex flex-col gap-3">
                  <h3 className="font-semibold text-slate-900 mb-1 text-sm uppercase tracking-wider flex items-center gap-2">
                    <Search className="w-4 h-4 text-indigo-500" />
                    Location Map
                  </h3>
                  <div className="rounded-xl overflow-hidden border border-slate-200 h-[220px] bg-slate-100 shadow-inner relative">
                    {job.distance_km !== null && job.distance_km !== undefined && (
                      <div className="absolute top-2 right-2 bg-white/90 backdrop-blur px-2 py-1 rounded-md text-xs font-bold text-indigo-700 shadow-sm z-10 border border-indigo-100">
                        {job.distance_km} km away
                      </div>
                    )}
                    <iframe
                      width="100%"
                      height="100%"
                      frameBorder="0"
                      style={{ border: 0 }}
                      src={`https://maps.google.com/maps?q=${encodeURIComponent(`${job.employer} ${job.location || ''}`.trim() || 'Australia')}&t=&z=14&ie=UTF8&iwloc=&output=embed`}
                      title="Job Location"
                    ></iframe>
                  </div>

                  {(profile?.campus_address || profile?.city) && (
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(`${profile.campus_address || profile.city}, ${profile.country || ''}`)}&destination=${encodeURIComponent(`${job.employer} ${job.location || ''}`.trim())}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 text-sm font-medium rounded-xl transition"
                    >
                      <MapPin className="w-4 h-4 text-slate-500" />
                      Get Directions from your address
                    </a>
                  )}
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
                className="flex items-center gap-2 px-6 py-2.5 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition shadow-md hover:shadow-lg active:scale-[0.98]"
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
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [fetching, setFetching] = useState(true);
  const [filter, setFilter] = useState('');
  const [filterPay, setFilterPay] = useState('');
  const [filterRadius, setFilterRadius] = useState('');
  const [filterVisa, setFilterVisa] = useState('');
  const [activeTab, setActiveTab] = useState<string>('All');
  const [startingScan, setStartingScan] = useState(false);

  const fetchJobs = useCallback(async (jobType?: string) => {
    setFetching(true);
    try {
      const [res, stats, prof] = await Promise.all([
        getJobs({ limit: 100, job_type: jobType || undefined }),
        getEmailStats().catch(() => null),
        getProfile().catch(() => null)
      ]);
      setData(res);
      if (stats) setEmailStats(stats);
      if (prof) setProfile(prof);
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

  const sponsorKeywords = ['sponsorship', 'sponsor', '482', 'tss', 'visa sponsor'];
  const noSponsorKeywords = ['no sponsorship', 'no sponsor', 'pr only', 'citizen only', 'permanent resident'];

  const filteredItems = useMemo(() => {
    if (!data) return [];
    return data.items.filter(job => {
      if (filter) {
        const lower = filter.toLowerCase();
        if (!job.title.toLowerCase().includes(lower) && 
            !job.employer.toLowerCase().includes(lower) && 
            !(job.location || '').toLowerCase().includes(lower)) {
          return false;
        }
      }
      if (filterPay) {
        const minPay = parseInt(filterPay);
        if (job.pay_min === null || job.pay_min < minPay) return false;
      }
      if (filterRadius) {
        const maxRadius = parseInt(filterRadius);
        if (job.distance_km === null || job.distance_km === undefined || job.distance_km > maxRadius) return false;
      }
      if (filterVisa) {
        const descLower = job.description?.toLowerCase() || '';
        if (filterVisa === 'sponsor') {
          const hasSponsor = sponsorKeywords.some(kw => descLower.includes(kw));
          const hasNoSponsor = noSponsorKeywords.some(kw => descLower.includes(kw));
          if (!hasSponsor || hasNoSponsor) return false;
        } else if (filterVisa === 'nosponsor') {
          const hasNoSponsor = noSponsorKeywords.some(kw => descLower.includes(kw));
          if (hasNoSponsor) return false;
        }
      }
      return true;
    });
  }, [data, filter, filterPay, filterRadius, filterVisa]);

  const categories = useMemo(() => {
    const cats = new Set<string>();
    filteredItems.forEach(job => cats.add(job.category || 'Other'));
    return Array.from(cats).sort();
  }, [filteredItems]);

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

        {/* Main Content Area */}
        <div className="flex flex-col gap-8">
          {/* Filter Toolbar */}
          <div className="bg-white border border-slate-200 p-4 rounded-xl flex flex-col xl:flex-row items-start xl:items-center gap-4 shadow-sm">
            <h3 className="font-bold text-slate-800 uppercase tracking-widest mr-auto whitespace-nowrap">Filter Jobs</h3>
            <div className="flex flex-wrap items-center gap-3 w-full xl:w-auto">
              <div className="relative flex-1 xl:flex-none">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search jobs..."
                  className="w-full xl:w-[200px] pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:bg-white transition-colors"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                />
              </div>
              <select
                value={filterRadius}
                onChange={(e) => setFilterRadius(e.target.value)}
                className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
              >
                <option value="">Any distance</option>
                <option value="5">Within 5 km</option>
                <option value="15">Within 15 km</option>
                <option value="30">Within 30 km</option>
              </select>
              <select
                value={filterPay}
                onChange={(e) => setFilterPay(e.target.value)}
                className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
              >
                <option value="">Any pay</option>
                <option value="20">$20+/hr</option>
                <option value="30">$30+/hr</option>
                <option value="60000">$60k+/yr</option>
              </select>
              <select
                value={filterVisa}
                onChange={(e) => setFilterVisa(e.target.value)}
                className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
              >
                <option value="">Visa: Any</option>
                <option value="sponsor">Sponsor Available</option>
                <option value="nosponsor">No Sponsorship</option>
              </select>
            </div>
          </div>

          {/* Jobs Feed */}
          <div>
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6">
              <h2 className="text-2xl font-bold text-slate-900">Recent Job Matches</h2>
            </div>
            
            <div className="flex gap-2 overflow-x-auto pb-4 mb-2 scrollbar-hide">
              <button
                onClick={() => setActiveTab('All')}
                className={`px-4 py-2 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${activeTab === 'All' ? 'bg-blue-600 text-white shadow-sm' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'}`}
              >
                All Matches ({filteredItems.length})
              </button>
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setActiveTab(cat)}
                  className={`px-4 py-2 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${activeTab === cat ? 'bg-blue-600 text-white shadow-sm' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'}`}
                >
                  {cat.replace(/_/g, ' ')} ({filteredItems.filter(j => (j.category || 'Other') === cat).length})
                </button>
              ))}
            </div>
            
            {fetching ? (
              <div className="flex items-center justify-center py-20">
                <div className="w-8 h-8 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin" />
              </div>
            ) : filteredItems.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-4 py-20 text-center border-2 border-dashed border-slate-200 bg-slate-50 rounded-xl">
                <Search className="w-8 h-8 text-slate-400" />
                <p className="text-base text-slate-600 font-medium">No jobs found. Run a scan!</p>
              </div>
            ) : (
              <div className="flex flex-col gap-10">
                {activeTab === 'All' ? (
                  categories.map(cat => (
                    <div key={cat} className="flex flex-col gap-4">
                      <h3 className="font-bold text-slate-800 text-sm uppercase tracking-widest border-b border-slate-200 pb-2">
                        {cat.replace(/_/g, ' ')}
                      </h3>
                      <div className="grid gap-4">
                        {filteredItems.filter(j => (j.category || 'Other') === cat).map(job => (
                          <JobCard key={job.id} job={job} profile={profile} />
                        ))}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="grid gap-4">
                    {filteredItems.filter(j => (j.category || 'Other') === activeTab).map(job => (
                      <JobCard key={job.id} job={job} profile={profile} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppSidebarLayout>
  );
}
