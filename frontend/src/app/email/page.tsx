'use client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { AppSidebarLayout } from '@/components/ui/app-sidebar-layout';
import { Mail, Send, Users, Settings, CheckCircle2, Clock, XCircle, AlertCircle } from 'lucide-react';
import {
  getEmailSettings,
  updateEmailSettings,
  getEmailQueue,
  getEmailStats,
  getEmailContacts,
  queueEmails,
  EmailSettings,
  EmailQueueItem,
  EmailContact,
  EmailStats,
} from '@/lib/api';

type Tab = 'compose' | 'queue' | 'contacts' | 'settings';

export default function EmailPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>('compose');

  // Settings
  const [settings, setSettings] = useState<EmailSettings | null>(null);
  const [settingsSaved, setSettingsSaved] = useState(false);

  // Queue
  const [queue, setQueue] = useState<EmailQueueItem[]>([]);
  const [queueFilter, setQueueFilter] = useState('');

  // Contacts
  const [contacts, setContacts] = useState<EmailContact[]>([]);

  // Stats
  const [stats, setStats] = useState<EmailStats | null>(null);

  // Compose
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [selectedContacts, setSelectedContacts] = useState<Set<number>>(new Set());
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState('');

  const loadData = useCallback(async () => {
    try {
      const [s, st, c] = await Promise.all([
        getEmailSettings(),
        getEmailStats(),
        getEmailContacts(),
      ]);
      setSettings(s);
      setStats(st);
      setContacts(c.items);
      if (!subject) setSubject(s.default_subject);
      if (!body) setBody(s.default_body);
    } catch {
      /* user not logged in */
    }
  }, []);

  const loadQueue = useCallback(async () => {
    try {
      const q = await getEmailQueue(queueFilter || undefined);
      setQueue(q.items);
    } catch { /* ignore */ }
  }, [queueFilter]);

  useEffect(() => {
    if (!loading && !user) { router.replace('/login'); return; }
    if (!loading && user) {
      loadData();
      loadQueue();
    }
  }, [user, loading, router, loadData, loadQueue]);

  useEffect(() => {
    if (tab === 'queue') loadQueue();
  }, [tab, loadQueue]);

  const handleSaveSettings = async () => {
    if (!settings) return;
    try {
      await updateEmailSettings(settings);
      setSettingsSaved(true);
      setTimeout(() => setSettingsSaved(false), 2000);
    } catch (e) {
      console.error(e);
    }
  };

  const toggleContact = (id: number) => {
    setSelectedContacts(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    if (selectedContacts.size === contacts.length) {
      setSelectedContacts(new Set());
    } else {
      setSelectedContacts(new Set(contacts.map(c => c.id)));
    }
  };

  const handleQueueEmails = async () => {
    if (selectedContacts.size === 0) return;
    setSending(true);
    setSendResult('');
    try {
      const items = contacts
        .filter(c => selectedContacts.has(c.id))
        .map(c => ({
          job_id: c.id,
          to_email: c.contact_email,
          subject: subject
            .replace('{company}', c.employer || 'your company')
            .replace('{job_title}', c.title || 'the open role'),
          body: body
            .replace('{company}', c.employer || 'your company')
            .replace('{job_title}', c.title || 'the open role')
            .replace('{city}', c.location || 'the area')
            .replace('{user_name}', user?.name || ''),
        }));
      const res = await queueEmails(items);
      setSendResult(`${res.queued} emails queued successfully`);
      setSelectedContacts(new Set());
      loadQueue();
      loadData();
    } catch (e: any) {
      setSendResult(`Error: ${e.message}`);
    } finally {
      setSending(false);
    }
  };

  const TABS: { key: Tab; label: string; icon: any }[] = [
    { key: 'compose', label: 'Compose', icon: Mail },
    { key: 'contacts', label: 'Contacts', icon: Users },
    { key: 'queue', label: 'Queue', icon: Send },
    { key: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <AppSidebarLayout>
      <div className="max-w-5xl mx-auto px-6 py-10 flex flex-col gap-8">
        {/* Header */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-indigo-600 to-indigo-700 rounded-xl flex items-center justify-center shadow-lg">
              <Mail className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Cold Email Outreach</h1>
              <p className="text-slate-500 text-sm">Send personalized emails to HR contacts discovered during scraping.</p>
            </div>
          </div>
        </div>

        {/* Stats cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Contacts Found', value: stats.total_contacts, color: 'text-indigo-600', bg: 'bg-indigo-50 border-indigo-100', icon: Users },
              { label: 'Emails Queued', value: stats.total_pending, color: 'text-amber-600', bg: 'bg-amber-50 border-amber-100', icon: Clock },
              { label: 'Emails Sent', value: stats.total_sent, color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-100', icon: CheckCircle2 },
              { label: 'Total Outreach', value: stats.total_queued, color: 'text-slate-600', bg: 'bg-slate-50 border-slate-100', icon: Send },
            ].map(s => {
              const Icon = s.icon;
              return (
                <div key={s.label} className={`${s.bg} border rounded-2xl p-5 flex flex-col gap-2 hover:shadow-md transition`}>
                  <div className="flex items-center justify-between">
                    <span className={`text-2xl font-bold ${s.color}`}>{s.value}</span>
                    <Icon className={`w-5 h-5 ${s.color} opacity-60`} />
                  </div>
                  <span className="text-xs text-slate-500 font-medium">{s.label}</span>
                </div>
              );
            })}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit">
          {TABS.map(t => {
            const Icon = t.icon;
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 ${
                  tab === t.key
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                {t.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        {tab === 'compose' && (
          <div className="flex flex-col gap-6">
            <div className="bg-white border border-slate-200 rounded-2xl p-6 flex flex-col gap-5">
              <h2 className="text-lg font-semibold text-slate-900">Email Template</h2>
              <p className="text-sm text-slate-500 -mt-3">
                Use placeholders: <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs">{'{company}'}</code>{' '}
                <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs">{'{job_title}'}</code>{' '}
                <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs">{'{city}'}</code>{' '}
                <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs">{'{user_name}'}</code>
              </p>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-slate-700">Subject Line</label>
                <input
                  value={subject}
                  onChange={e => setSubject(e.target.value)}
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition"
                  placeholder="Regarding open positions at {company}"
                />
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-slate-700">Email Body</label>
                <textarea
                  value={body}
                  onChange={e => setBody(e.target.value)}
                  rows={10}
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm font-mono leading-relaxed focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition resize-y"
                  placeholder="Hi {company} Team..."
                />
              </div>
            </div>

            {/* Select contacts to email */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">
                  Select Recipients ({selectedContacts.size} selected)
                </h2>
                <button
                  onClick={selectAll}
                  className="text-sm text-indigo-600 hover:text-indigo-700 font-medium transition"
                >
                  {selectedContacts.size === contacts.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>

              {contacts.length === 0 ? (
                <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
                  <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center">
                    <Users className="w-8 h-8 text-slate-300" />
                  </div>
                  <div>
                    <p className="text-slate-500 font-medium mb-1">No contacts found yet</p>
                    <p className="text-sm text-slate-400 max-w-sm">
                      Run a job scan to discover HR emails from job listings and employer websites automatically.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col divide-y divide-slate-100 max-h-80 overflow-y-auto">
                  {contacts.map(c => (
                    <label
                      key={c.id}
                      className="flex items-center gap-4 py-3 px-2 hover:bg-slate-50 rounded-lg cursor-pointer transition"
                    >
                      <input
                        type="checkbox"
                        checked={selectedContacts.has(c.id)}
                        onChange={() => toggleContact(c.id)}
                        className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-slate-900 truncate">{c.employer || 'Unknown'}</div>
                        <div className="text-xs text-slate-500 truncate">{c.title} - {c.location}</div>
                      </div>
                      <span className="text-xs text-indigo-600 font-mono bg-indigo-50 px-2.5 py-1 rounded-full border border-indigo-100 shrink-0">
                        {c.contact_email}
                      </span>
                    </label>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-4 pt-2">
                <button
                  onClick={handleQueueEmails}
                  disabled={selectedContacts.size === 0 || sending}
                  className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg shadow-md hover:shadow-lg transition-all flex items-center gap-2"
                >
                  {sending ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Queuing...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Queue {selectedContacts.size} Email{selectedContacts.size !== 1 ? 's' : ''}
                    </>
                  )}
                </button>
                {sendResult && (
                  <span className={`text-sm font-medium flex items-center gap-1.5 ${sendResult.startsWith('Error') ? 'text-red-600' : 'text-emerald-600'}`}>
                    {sendResult.startsWith('Error') ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                    {sendResult}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {tab === 'contacts' && (
          <div className="bg-white border border-slate-200 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Discovered Email Contacts</h2>
            {contacts.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
                <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center">
                  <Users className="w-8 h-8 text-slate-300" />
                </div>
                <div>
                  <p className="text-slate-500 font-medium mb-1">No contacts discovered yet</p>
                  <p className="text-sm text-slate-400 max-w-md">
                    The scraper will extract HR emails from job listings and employer websites automatically during your next scan.
                  </p>
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100">
                      <th className="text-left py-3 px-3 text-slate-500 font-medium">Company</th>
                      <th className="text-left py-3 px-3 text-slate-500 font-medium">Role</th>
                      <th className="text-left py-3 px-3 text-slate-500 font-medium">Location</th>
                      <th className="text-left py-3 px-3 text-slate-500 font-medium">Email</th>
                      <th className="text-left py-3 px-3 text-slate-500 font-medium">Source</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {contacts.map(c => (
                      <tr key={c.id} className="hover:bg-slate-50 transition">
                        <td className="py-3 px-3 font-medium text-slate-900">{c.employer || '-'}</td>
                        <td className="py-3 px-3 text-slate-600">{c.title}</td>
                        <td className="py-3 px-3 text-slate-500">{c.location || '-'}</td>
                        <td className="py-3 px-3">
                          <span className="text-indigo-600 font-mono text-xs bg-indigo-50 px-2 py-1 rounded-full border border-indigo-100">
                            {c.contact_email}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-slate-400 text-xs">{c.source}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {tab === 'queue' && (
          <div className="bg-white border border-slate-200 rounded-2xl p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Email Queue</h2>
              <div className="flex gap-1 bg-slate-100 p-0.5 rounded-lg">
                {['', 'queued', 'sent', 'failed'].map(f => (
                  <button
                    key={f}
                    onClick={() => setQueueFilter(f)}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition ${
                      queueFilter === f
                        ? 'bg-white text-slate-900 shadow-sm'
                        : 'text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    {f || 'All'}
                  </button>
                ))}
              </div>
            </div>

            {queue.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
                <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center">
                  <Send className="w-8 h-8 text-slate-300" />
                </div>
                <div>
                  <p className="text-slate-500 font-medium mb-1">No emails in queue</p>
                  <p className="text-sm text-slate-400 max-w-sm">
                    Compose and queue some emails from the Compose tab to get started with outreach.
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col divide-y divide-slate-100">
                {queue.map(eq => {
                  const statusConfig = {
                    sent: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', dot: 'bg-emerald-500', icon: CheckCircle2 },
                    failed: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', dot: 'bg-red-500', icon: XCircle },
                    queued: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', dot: 'bg-amber-400', icon: Clock },
                  }[eq.status] || { bg: 'bg-slate-50', text: 'text-slate-700', border: 'border-slate-200', dot: 'bg-slate-400', icon: AlertCircle };
                  
                  const StatusIcon = statusConfig.icon;
                  
                  return (
                    <div key={eq.id} className="flex items-start gap-4 py-4 hover:bg-slate-50 rounded-lg px-2 transition">
                      <div className={`mt-1.5 ${statusConfig.dot} w-2 h-2 rounded-full shrink-0`} />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-slate-900 truncate">{eq.subject}</div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          To: {eq.employer || 'Unknown'} {eq.contact_email ? `(${eq.contact_email})` : ''}
                        </div>
                        <div className="text-xs text-slate-400 mt-1 line-clamp-2">{eq.body}</div>
                      </div>
                      <span className={`text-xs px-2.5 py-1 rounded-full border shrink-0 flex items-center gap-1.5 ${statusConfig.bg} ${statusConfig.text} ${statusConfig.border}`}>
                        <StatusIcon className="w-3 h-3" />
                        {eq.status}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {tab === 'settings' && settings && (
          <div className="bg-white border border-slate-200 rounded-2xl p-6 flex flex-col gap-6">
            <h2 className="text-lg font-semibold text-slate-900">Email Settings</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-slate-700">Daily Send Limit</label>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={settings.daily_limit}
                  onChange={e => setSettings({ ...settings, daily_limit: parseInt(e.target.value) || 1 })}
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition"
                />
                <span className="text-xs text-slate-400">Max emails to send per day</span>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-slate-700">Send Time</label>
                <div className="flex gap-2">
                  <select
                    value={settings.send_hour}
                    onChange={e => setSettings({ ...settings, send_hour: parseInt(e.target.value) })}
                    className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition bg-white"
                  >
                    {Array.from({ length: 24 }, (_, i) => (
                      <option key={i} value={i}>
                        {i.toString().padStart(2, '0')}:00
                      </option>
                    ))}
                  </select>
                  <select
                    value={settings.send_minute}
                    onChange={e => setSettings({ ...settings, send_minute: parseInt(e.target.value) })}
                    className="w-24 px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition bg-white"
                  >
                    {[0, 15, 30, 45].map(m => (
                      <option key={m} value={m}>:{m.toString().padStart(2, '0')}</option>
                    ))}
                  </select>
                </div>
                <span className="text-xs text-slate-400">When to send queued emails daily</span>
              </div>

              <div className="flex flex-col gap-2 md:col-span-2">
                <label className="flex items-center gap-3 cursor-pointer">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={settings.auto_send}
                      onChange={e => setSettings({ ...settings, auto_send: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-10 h-6 bg-slate-200 peer-checked:bg-indigo-600 rounded-full transition" />
                    <div className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition peer-checked:translate-x-4" />
                  </div>
                  <div>
                    <span className="text-sm font-medium text-slate-700">Auto-send via n8n</span>
                    <p className="text-xs text-slate-400">Automatically send queued emails at the scheduled time</p>
                  </div>
                </label>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={handleSaveSettings}
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium transition shadow-sm flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                Save Settings
              </button>
              {settingsSaved && (
                <span className="text-sm text-emerald-600 font-medium flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  Settings saved
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </AppSidebarLayout>
  );
}
