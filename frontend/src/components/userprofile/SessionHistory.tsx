import React, { useEffect, useState, useMemo } from 'react';
import { apiFetch } from '@/lib/api';
// import { useTheme } from '@/components/theme-provider'; // Assuming standard next-themes or similar if available, otherwise defaulting to system preference or class checks

interface SessionEntry {
  id?: number;
  created_at: string;
  active_seconds?: number;
  last_seen_at?: string | null;
  revoked_at?: string | null;
  meta?: Record<string, any>;
}

function formatSecondsToHMS(s: number) {
  const hrs = Math.floor(s / 3600);
  const mins = Math.floor((s % 3600) / 60);
  const secs = s % 60;
  return [hrs, mins, secs].map((n) => String(n).padStart(2, '0')).join(':');
}

export default function SessionHistory() {
  // const { theme } = useTheme(); // TODO: Verify theme provider
  const darkMode = false; // Placeholder, relying on 'dark:' classes if system supports it
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<SessionEntry[]>([]);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setLoading(true);
      try {
        const data = await apiFetch<SessionEntry[]>('/auth/sessions');
        if (!mounted) return;
        const list: SessionEntry[] = Array.isArray(data) ? data.map((it: any) => ({
          ...it,
          active_seconds: typeof it?.active_seconds === 'number' ? it.active_seconds : (it?.active_seconds ? Number(it.active_seconds) : 0),
          last_seen_at: it?.last_seen_at ?? null,
          revoked_at: it?.revoked_at ?? null,
        })) : [];
        setSessions(list);
        setError(null);
      } catch (e: any) {
        if (!mounted) return;
        setError(e?.message || 'Failed to load sessions');
        setSessions([]);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    const tickId = setInterval(() => {
      setSessions((prev) => {
        if (!prev || prev.length === 0) return prev;
        let activeIdx = -1;
        let activeTime = -1;
        prev.forEach((s, i) => {
          if (!s.revoked_at) {
            const ts = s.last_seen_at ? Date.parse(s.last_seen_at) : Date.parse(s.created_at);
            if (!isNaN(ts) && ts > activeTime) {
              activeTime = ts;
              activeIdx = i;
            }
          }
        });
        if (activeIdx === -1) return prev;
        const next = prev.slice();
        const s = next[activeIdx];
        next[activeIdx] = { ...s, active_seconds: (s.active_seconds || 0) + 1 };
        return next;
      });
    }, 1000);
    return () => { mounted = false; clearInterval(tickId); };
  }, []);

  const totalActive = useMemo(() => sessions.reduce((s, it) => s + (it.active_seconds || 0), 0), [sessions]);

  return (
    <div className="mt-2 text-sm">
      <div className="flex items-center justify-between px-1 mb-2">
        <h3 className="text-base font-medium text-slate-800 dark:text-gray-200">Session history</h3>
        <div className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-700 dark:bg-gray-800 dark:text-gray-200 border dark:border-gray-700">
          Total active: <span className="font-semibold ml-1">{formatSecondsToHMS(totalActive)}</span>
        </div>
      </div>

      <div className="rounded-sm border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
        <div className="relative p-2 overflow-x-auto">
          {loading && <div className="h-24 flex items-center justify-center text-sm opacity-80">Loading...</div>}
          {error && <div className="p-4 text-sm text-red-600">{error}</div>}
          {!loading && !error && (
            <table className="min-w-full text-xs sm:text-[13px] text-slate-700 dark:text-gray-300">
              <thead className="text-[10px] sm:text-[11px] uppercase tracking-wide">
                <tr className="bg-white text-slate-500 border-b border-slate-200 dark:bg-gray-900 dark:text-gray-400 dark:border-gray-800">
                  <th className="px-3 py-2 text-left">Date</th>
                  <th className="px-3 py-2 text-left">Active (hh:mm:ss)</th>
                  <th className="px-3 py-2 text-left">Seconds</th>
                </tr>
              </thead>
              <tbody>
                {sessions.length === 0 && (
                  <tr>
                    <td colSpan={3} className="h-24 text-center text-sm text-slate-500 dark:text-gray-400">No session records found</td>
                  </tr>
                )}
                {sessions.map((s, idx) => (
                  <tr
                    key={s.id || s.created_at}
                    className={`${idx % 2 === 0 ? 'bg-slate-50/40 dark:bg-gray-800/30' : ''} border-b border-slate-100 dark:border-gray-800 hover:bg-slate-50 dark:hover:bg-gray-800 transition-colors`}
                  >
                    <td className="px-3 py-2 align-middle whitespace-nowrap">{new Date(s.created_at).toLocaleString()}</td>
                    <td className="px-3 py-2 align-middle whitespace-nowrap font-mono">{formatSecondsToHMS(s.active_seconds || 0)}</td>
                    <td className="px-3 py-2 align-middle whitespace-nowrap">{s.active_seconds ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
