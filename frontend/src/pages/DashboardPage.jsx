import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  Truck, Package, Box, Cpu, AlertTriangle, ShieldCheck, 
  CheckCircle, ArrowUpRight, Activity, TrendingUp, RefreshCw 
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid, Legend, AreaChart, Area 
} from 'recharts';

export default function DashboardPage({ onNavigate }) {
  const [metrics, setMetrics] = useState(null);
  const [readings, setReadings] = useState([]);
  const [recentShipments, setRecentShipments] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [m, r, s] = await Promise.all([
        api.getMetrics(),
        api.getReadings(),
        api.getShipments()
      ]);
      setMetrics(m);
      setReadings(r.slice(-50)); // Last 50 readings for trend
      setRecentShipments(s.slice(0, 5));
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        <RefreshCw className="w-6 h-6 animate-spin mr-2" />
        <span>Loading Cold Chain Operations Telemetry...</span>
      </div>
    );
  }

  const metricCards = [
    { title: 'Total Shipments', value: metrics?.total_shipments || 0, icon: Truck, color: 'text-blue-600', bg: 'bg-blue-50' },
    { title: 'Active In-Transit', value: metrics?.active_shipments || 0, icon: Activity, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { title: 'Total Containers', value: metrics?.total_containers || 0, icon: Box, color: 'text-indigo-600', bg: 'bg-indigo-50' },
    { title: 'Healthy Sensors', value: metrics?.healthy_sensors || 0, icon: Cpu, color: 'text-teal-600', bg: 'bg-teal-50' },
    { title: 'Active Excursions', value: metrics?.active_excursions || 0, icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50' },
    { title: 'Critical Alarms', value: metrics?.critical_alerts || 0, icon: AlertTriangle, color: 'text-rose-600', bg: 'bg-rose-50' },
    { title: 'Open CAPA Actions', value: metrics?.open_corrective_actions || 0, icon: ShieldCheck, color: 'text-purple-600', bg: 'bg-purple-50' },
    { title: 'Integrity Rate', value: `${metrics?.data_validation_success_rate || 100}%`, icon: CheckCircle, color: 'text-cyan-600', bg: 'bg-cyan-50' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner / Summary */}
      <div className="flex justify-between items-center bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Cold Chain Operational Command</h1>
          <p className="text-sm text-slate-500 mt-1">Real-time GxP cold chain telemetries, threshold adherence, and excursion lifecycle monitoring.</p>
        </div>
        <button
          onClick={fetchData}
          className="inline-flex items-center space-x-2 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {metricCards.map((c, idx) => {
          const Icon = c.icon;
          return (
            <div key={idx} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow transition-shadow">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">{c.title}</span>
                <div className={`p-2 rounded-lg ${c.bg}`}>
                  <Icon className={`w-5 h-5 ${c.color}`} />
                </div>
              </div>
              <div className="text-2xl font-bold text-slate-900 mt-3">{c.value}</div>
            </div>
          );
        })}
      </div>

      {/* Interactive Charts: Temperature & Humidity Live Curves */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-900">Live Temperature Trend (°C)</h3>
              <p className="text-xs text-slate-500">Continuous 5-minute sampling interval across active container fleet</p>
            </div>
            <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-blue-100 text-blue-800">
              Dual Sensor
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={readings}>
                <defs>
                  <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="timestamp" tick={false} />
                <YAxis domain={['auto', 'auto']} stroke="#94a3b8" fontSize={11} />
                <Tooltip />
                <Area type="monotone" dataKey="temperature" stroke="#2563eb" strokeWidth={2} fillOpacity={1} fill="url(#tempGrad)" name="Temp (°C)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-900">Relative Humidity Profile (% RH)</h3>
              <p className="text-xs text-slate-500">Simultaneous environmental humidity surveillance</p>
            </div>
            <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800">
              Calibrated RH
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={readings}>
                <defs>
                  <linearGradient id="humGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#059669" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#059669" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="timestamp" tick={false} />
                <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} />
                <Tooltip />
                <Area type="monotone" dataKey="humidity" stroke="#059669" strokeWidth={2} fillOpacity={1} fill="url(#humGrad)" name="Humidity (%)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Active High-Priority Shipments */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-base font-semibold text-slate-900">Active High-Priority Shipments</h3>
          <button 
            onClick={() => onNavigate('Shipments')}
            className="text-xs text-blue-600 font-semibold hover:underline inline-flex items-center space-x-1"
          >
            <span>View All Shipments</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500 uppercase border-y border-slate-200">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Shipment ID</th>
                <th className="py-2.5 px-4 font-semibold">Product</th>
                <th className="py-2.5 px-4 font-semibold">Route</th>
                <th className="py-2.5 px-4 font-semibold">Departure</th>
                <th className="py-2.5 px-4 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recentShipments.map((s) => (
                <tr key={s.shipment_id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-4 font-mono font-medium text-blue-600">{s.shipment_id}</td>
                  <td className="py-3 px-4 text-slate-700">{s.product_id}</td>
                  <td className="py-3 px-4 text-slate-600">{s.origin} → {s.destination}</td>
                  <td className="py-3 px-4 text-slate-500 text-xs">{new Date(s.departure_time).toLocaleString()}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      s.shipment_status === 'In_Transit' ? 'bg-amber-100 text-amber-800' :
                      s.shipment_status === 'Delivered' ? 'bg-emerald-100 text-emerald-800' :
                      'bg-slate-100 text-slate-700'
                    }`}>
                      {s.shipment_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
