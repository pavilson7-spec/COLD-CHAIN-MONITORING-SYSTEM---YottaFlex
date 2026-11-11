import React, { useEffect, useState } from 'react';
import { Database, Shield, RefreshCw, CircleCheck, CircleX } from 'lucide-react';
import { api } from '../services/api';

export default function SettingsPage() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    setLoading(true);
    setError('');
    try {
      setHealth(await api.getHealth());
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not reach the backend health endpoint.');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const healthy = health?.status === 'healthy' && health?.database_connected;

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">System Status</h1>
          <p className="text-sm text-slate-500 mt-1">Live backend and database connectivity.</p>
        </div>
        <button onClick={refresh} disabled={loading} className="inline-flex items-center gap-2 px-3 py-2 bg-slate-100 hover:bg-slate-200 disabled:opacity-50 text-slate-700 text-sm font-medium rounded-lg">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center gap-3 text-slate-900 font-semibold border-b pb-3">
            <Database className="w-5 h-5 text-blue-600" /> Backend and PostgreSQL
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-600">Service status</span>
            <span className={`inline-flex items-center gap-2 font-semibold ${healthy ? 'text-emerald-700' : 'text-rose-700'}`}>
              {healthy ? <CircleCheck className="w-4 h-4" /> : <CircleX className="w-4 h-4" />}
              {health?.status || (loading ? 'Checking…' : 'Unavailable')}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-600">Database connection</span>
            <span className="font-semibold text-slate-800">{health ? (health.database_connected ? 'Connected' : 'Disconnected') : '—'}</span>
          </div>
          {health?.system_time && <div className="text-xs text-slate-500 border-t pt-3">Last checked: {new Date(health.system_time * 1000).toLocaleString()}</div>}
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center gap-3 text-slate-900 font-semibold border-b pb-3">
            <Shield className="w-5 h-5 text-blue-600" /> Access control
          </div>
          <p className="text-sm text-slate-600">Changes to shipments, policies, sensor calibration, excursions, and corrective actions are authorized by server-side role checks.</p>
          <p className="text-xs text-slate-500">Current role: <span className="font-semibold text-slate-700">{JSON.parse(localStorage.getItem('user') || '{}').role || 'Unknown'}</span></p>
        </div>
      </div>
    </div>
  );
}
