import React, { useState } from 'react';
import { Download, FileSpreadsheet, FileJson, Database, Check } from 'lucide-react';

export default function ReportsPage() {
  const [downloading, setDownloading] = useState('');

  const triggerDownload = (type, entity) => {
    const url = `http://localhost:8000/api/v1/exports/${type}/${entity}`;
    window.open(url, '_blank');
  };

  const exportEntities = [
    { name: 'Products', id: 'products', desc: 'Product catalog and approved handling ranges' },
    { name: 'Shipments', id: 'shipments', desc: 'Shipment movements, schedules, routes, and lifecycle status' },
    { name: 'Containers', id: 'containers', desc: 'Reusable containers and current assignments' },
    { name: 'Sensors', id: 'sensors', desc: 'Sensor inventory, calibration, and health status' },
    { name: 'Readings', id: 'readings', desc: 'Temperature and humidity telemetry with anomaly provenance' },
    { name: 'Threshold Policies', id: 'threshold-policies', desc: 'Product linked policies and effective dates' },
    { name: 'Excursions', id: 'excursions', desc: 'Environmental and operational exceptions with quality status' },
    { name: 'Excursion History', id: 'excursion-status-events', desc: 'Append only excursion status transition history' },
    { name: 'Custody Events', id: 'custody-events', desc: 'Shipment chain of custody and lifecycle events' },
    { name: 'Corrective Actions', id: 'corrective-actions', desc: 'CAPA ownership, priority, and resolution status' },
    { name: 'Alerts', id: 'alerts', desc: 'Notifications and acknowledgement status' }
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">Regulatory Reports & Data Exports</h1>
        <p className="text-sm text-slate-500 mt-1">Export complete validated audit archives in CSV, JSON, and GxP compliance formats.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {exportEntities.map((ent) => (
          <div key={ent.id} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg inline-block mb-3">
                <FileSpreadsheet className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">{ent.name} Master Dataset</h3>
              <p className="text-xs text-slate-500 mt-2">{ent.desc}</p>
            </div>

            <div className="mt-6 flex space-x-3">
              <button
                onClick={() => triggerDownload('csv', ent.id)}
                className="flex-1 py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export CSV</span>
              </button>
              <button
                onClick={() => triggerDownload('json', ent.id)}
                className="flex-1 py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition-colors"
              >
                <FileJson className="w-3.5 h-3.5" />
                <span>Export JSON</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h3 className="text-base font-bold text-slate-900 mb-2">Ground Truth & Reproducibility</h3>
        <p className="text-xs text-slate-600 leading-relaxed">
          Ground-truth evaluation datasets are generated with deterministic seed <code>20261022</code> and stored separately at 
          <code>data/generated/ground_truth.csv</code> and <code>ground_truth.json</code>.
          Raw anomaly injection occurs completely isolated from inference rules, ensuring zero feature leakage.
        </p>
      </div>
    </div>
  );
}
