import React, { useState } from 'react';
import { api } from '../services/api';
import { ShieldCheck, Truck, Lock, User as UserIcon, AlertCircle } from 'lucide-react';

export default function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('AdminSecure2026!');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await api.login(username, password);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      onLoginSuccess(data.user);
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const setPresetUser = (u, p) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600 text-white shadow-lg mb-4">
          <Truck className="w-8 h-8" />
        </div>
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Cold Chain Monitoring</h2>
        <p className="mt-2 text-sm text-slate-600">Enterprise Temperature & Telemetry Compliance Platform</p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-xl sm:px-10">
          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-lg bg-red-50 p-4 border border-red-200 flex items-center space-x-3 text-red-700 text-sm">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">Username</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <UserIcon className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter username"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">Password</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-50"
            >
              {loading ? 'Authenticating...' : 'Sign In to Dashboard'}
            </button>
          </form>

          <div className="mt-6 border-t border-slate-100 pt-4">
            <p className="text-xs text-slate-500 font-medium mb-2">Quick Sign-in by Enterprise Role:</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => setPresetUser('admin', 'AdminSecure2026!')}
                className="p-2 border border-slate-200 rounded-md bg-slate-50 hover:bg-slate-100 text-left"
              >
                <div className="font-semibold text-slate-800">Admin</div>
                <div className="text-[10px] text-slate-500">OT/IT Admin</div>
              </button>
              <button
                type="button"
                onClick={() => setPresetUser('quality', 'Quality2026!')}
                className="p-2 border border-slate-200 rounded-md bg-slate-50 hover:bg-slate-100 text-left"
              >
                <div className="font-semibold text-slate-800">Quality Eng</div>
                <div className="text-[10px] text-slate-500">Excursions & CAPA</div>
              </button>
              <button
                type="button"
                onClick={() => setPresetUser('operator', 'Operator2026!')}
                className="p-2 border border-slate-200 rounded-md bg-slate-50 hover:bg-slate-100 text-left"
              >
                <div className="font-semibold text-slate-800">Operator</div>
                <div className="text-[10px] text-slate-500">Shipments & Alerts</div>
              </button>
              <button
                type="button"
                onClick={() => setPresetUser('planner', 'Planner2026!')}
                className="p-2 border border-slate-200 rounded-md bg-slate-50 hover:bg-slate-100 text-left"
              >
                <div className="font-semibold text-slate-800">Planner</div>
                <div className="text-[10px] text-slate-500">Routes & Logistics</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
