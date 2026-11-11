import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  ShieldCheck, AlertTriangle, CheckCircle, XCircle, 
  FileText, Play, Download, Search, RefreshCw, Layers 
} from 'lucide-react';

export default function EntityListView({ entityType, onEvaluate }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);
  const [evalResult, setEvalResult] = useState(null);
  const [actionError, setActionError] = useState('');
  const [loadError, setLoadError] = useState('');

  const loadEntityData = async () => {
    setLoading(true);
    setLoadError('');
    try {
      let data = [];
      switch (entityType) {
        case 'Products': data = await api.getProducts(); break;
        case 'Shipments': data = await api.getShipments(); break;
        case 'Containers': data = await api.getContainers(); break;
        case 'Sensors': data = await api.getSensors(); break;
        case 'Readings': data = await api.getReadings(); break;
        case 'Route Tracking': data = await api.getRouteStops(); break;
        case 'Threshold Policies': data = await api.getThresholdPolicies(); break;
        case 'Excursions': data = await api.getExcursions(); break;
        case 'Alerts': data = await api.getAlerts(); break;
        case 'Custody History': data = await api.getCustodyEvents(); break;
        case 'Corrective Actions': data = await api.getCorrectiveActions(); break;
        case 'Data Validation': data = await api.getValidationSummary(); break;
        default: data = [];
      }
      setItems(data);
    } catch (err) {
      console.error(`Failed to load ${entityType}:`, err);
      setLoadError(err.response?.data?.detail || `Could not load ${entityType}. Check the API connection and access permissions.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEntityData();
  }, [entityType]);

  const handleRunEvaluation = async (shipmentId) => {
    try {
      const res = await api.evaluateExcursions(shipmentId);
      setEvalResult(res);
      loadEntityData();
    } catch (err) {
      alert(`Evaluation error: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleAcknowledge = async (alertId) => {
    try {
      await api.acknowledgeAlert(alertId);
      loadEntityData();
    } catch (err) {
      alert('Failed to acknowledge alert');
    }
  };

  const handleExcursionTransition = async (excursion, status) => {
    try {
      setActionError('');
      await api.transitionExcursion(excursion.excursion_id, status, `Updated from ${excursion.status} view`);
      await loadEntityData();
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Could not update excursion status. Check your role and the allowed status transitions.');
    }
  };

  const handleExcursionReview = async (excursion, review_status) => {
    try {
      setActionError('');
      await api.reviewExcursion(excursion.excursion_id, review_status);
      await loadEntityData();
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Could not save quality review.');
    }
  };

  const handleActionUpdate = async (action, status) => {
    try {
      setActionError('');
      await api.updateCorrectiveAction(action.action_id, { ...action, status });
      await loadEntityData();
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Could not update corrective action.');
    }
  };

  const handleRecalibrate = async (sensor) => {
    try {
      setActionError('');
      await api.updateSensorCalibration(sensor.sensor_id, 'Valid', new Date().toISOString(), 'Calibration completed from sensor monitoring');
      await loadEntityData();
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Could not update calibration. Maintenance or quality role required.');
    }
  };

  // Special view for Data Validation
  if (entityType === 'Data Validation') {
    const valData = items.details ? items : null;
    return (
      <div className="space-y-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Automated Data Validation & Integrity Audit</h1>
            <p className="text-sm text-slate-500 mt-1">Checks for labelled anomaly cases, lifecycle integrity, policy alignment, and telemetry continuity.</p>
          </div>
          <button
            onClick={loadEntityData}
            className="inline-flex items-center space-x-2 px-3 py-2 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg text-sm font-medium"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Re-run Audit</span>
          </button>
        </div>

        {valData && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <span className="text-xs text-slate-400 uppercase font-semibold">Overall Compliance Rate</span>
                <div className="text-3xl font-extrabold text-blue-600">{valData.success_rate}%</div>
              </div>
              <div className="text-right text-xs text-slate-500">
                <div>Passed: {valData.passed_tests} / {valData.total_tests}</div>
                <div>Audit Timestamp: {new Date(valData.timestamp).toLocaleString()}</div>
              </div>
            </div>

            <div className="space-y-3">
              {valData.details.map((d, i) => (
                <div key={i} className="p-4 rounded-lg border border-slate-100 bg-slate-50 flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-slate-900 text-sm">{d.scenario}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-200 text-slate-700">{d.issue_type}</span>
                    </div>
                    <p className="text-xs text-slate-600 mt-1">{d.expected_behavior}</p>
                    {d.violations_found !== undefined && (
                      <div className="text-xs text-blue-700 font-medium mt-1">
                        Violations Correctly Flagged / Trapped: {d.violations_found}
                      </div>
                    )}
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                    d.status === 'PASS' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {d.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // General Table View
  const filteredItems = Array.isArray(items) ? items.filter(it => 
    JSON.stringify(it).toLowerCase().includes(search.toLowerCase())
  ) : [];

  const headers = filteredItems.length > 0 ? Object.keys(filteredItems[0]).filter(k => !k.includes('id_') && k !== 'created_at' && k !== 'updated_at') : [];

  return (
    <div className="space-y-6">
      {/* Entity Title & Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{entityType}</h1>
          <p className="text-sm text-slate-500 mt-1">Comprehensive record management, audit tracking, and operational view.</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder={`Search ${entityType}...`}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={loadEntityData}
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {evalResult && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-900 flex justify-between items-center">
          <div>
            <strong>Evaluation completed for {evalResult.shipment_id}:</strong> {evalResult.detected_excursions} excursions, {evalResult.created_alerts} alerts, {evalResult.created_actions} CAPA actions.
          </div>
          <button onClick={() => setEvalResult(null)} className="text-xs text-blue-600 underline">Dismiss</button>
        </div>
      )}
      {actionError && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{actionError}</div>}
      {loadError && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{loadError}</div>}

      {/* Table Container */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500 text-sm">Loading records...</div>
        ) : filteredItems.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">No records found.</div>
        ) : (
          <div className="overflow-x-auto max-h-[600px]">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs text-slate-500 uppercase sticky top-0 border-b border-slate-200 z-10">
                <tr>
                  {headers.map(h => (
                    <th key={h} className="py-3 px-4 font-semibold whitespace-nowrap">{h.replace(/_/g, ' ')}</th>
                  ))}
                  {entityType === 'Shipments' && <th className="py-3 px-4 font-semibold">Actions</th>}
                  {entityType === 'Alerts' && <th className="py-3 px-4 font-semibold">Action</th>}
                  {entityType === 'Excursions' && <th className="py-3 px-4 font-semibold">Quality Workflow</th>}
                  {entityType === 'Corrective Actions' && <th className="py-3 px-4 font-semibold">Workflow</th>}
                  {entityType === 'Sensors' && <th className="py-3 px-4 font-semibold">Calibration</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredItems.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 transition-colors">
                    {headers.map(h => (
                      <td key={h} className="py-3 px-4 whitespace-nowrap text-slate-700">
                        {typeof item[h] === 'boolean' ? (
                          <span className={`px-2 py-0.5 rounded text-xs font-semibold ${item[h] ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>
                            {item[h] ? 'True' : 'False'}
                          </span>
                        ) : h.includes('time') || h.includes('date') ? (
                          item[h] ? new Date(item[h]).toLocaleString() : 'N/A'
                        ) : h === 'severity' ? (
                          <span className={`px-2 py-0.5 rounded text-xs font-semibold ${item[h] === 'CRITICAL' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}`}>
                            {item[h]}
                          </span>
                        ) : h === 'status' || h === 'shipment_status' ? (
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            item[h] === 'OPEN' || item[h] === 'In_Transit' ? 'bg-amber-100 text-amber-800' :
                            item[h] === 'Delivered' || item[h] === 'RESOLVED' || item[h] === 'Healthy' ? 'bg-emerald-100 text-emerald-800' :
                            'bg-slate-100 text-slate-700'
                          }`}>
                            {item[h]}
                          </span>
                        ) : (
                          String(item[h] ?? '—')
                        )}
                      </td>
                    ))}
                    {entityType === 'Shipments' && (
                      <td className="py-3 px-4 whitespace-nowrap">
                        <button
                          onClick={() => handleRunEvaluation(item.shipment_id)}
                          className="px-2.5 py-1 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded text-xs font-semibold"
                        >
                          Evaluate Excursions
                        </button>
                      </td>
                    )}
                    {entityType === 'Alerts' && (
                      <td className="py-3 px-4 whitespace-nowrap">
                        {item.acknowledgement_status === 'UNACKNOWLEDGED' && (
                          <button
                            onClick={() => handleAcknowledge(item.alert_id)}
                            className="px-2.5 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded text-xs font-semibold"
                          >
                            Acknowledge
                          </button>
                        )}
                      </td>
                    )}
                    {entityType === 'Excursions' && (
                      <td className="py-3 px-4 whitespace-nowrap space-x-1">
                        {item.status === 'OPEN' && <button onClick={() => handleExcursionTransition(item, 'ACKNOWLEDGED')} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">Acknowledge</button>}
                        {['OPEN', 'ACKNOWLEDGED'].includes(item.status) && <button onClick={() => handleExcursionTransition(item, 'UNDER_INVESTIGATION')} className="px-2 py-1 bg-amber-50 text-amber-700 rounded text-xs">Investigate</button>}
                        {item.status !== 'CLOSED' && item.status !== 'RESOLVED' && <button onClick={() => handleExcursionTransition(item, 'CORRECTIVE_ACTION_REQUIRED')} className="px-2 py-1 bg-purple-50 text-purple-700 rounded text-xs">Require CAPA</button>}
                        {!['RESOLVED', 'CLOSED'].includes(item.status) && <button onClick={() => handleExcursionTransition(item, 'RESOLVED')} className="px-2 py-1 bg-emerald-50 text-emerald-700 rounded text-xs">Resolve</button>}
                        {item.status === 'RESOLVED' && <button onClick={() => handleExcursionTransition(item, 'CLOSED')} className="px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs">Close</button>}
                        {item.review_status !== 'Accepted' && <button onClick={() => handleExcursionReview(item, 'Accepted')} className="px-2 py-1 bg-teal-50 text-teal-700 rounded text-xs">Quality approve</button>}
                      </td>
                    )}
                    {entityType === 'Corrective Actions' && (
                      <td className="py-3 px-4 whitespace-nowrap space-x-1">
                        {item.status === 'OPEN' && <button onClick={() => handleActionUpdate(item, 'ACKNOWLEDGED')} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">Acknowledge</button>}
                        {['OPEN', 'ACKNOWLEDGED'].includes(item.status) && <button onClick={() => handleActionUpdate(item, 'IN_PROGRESS')} className="px-2 py-1 bg-amber-50 text-amber-700 rounded text-xs">Start</button>}
                        {!['RESOLVED', 'CLOSED'].includes(item.status) && <button onClick={() => handleActionUpdate(item, 'RESOLVED')} className="px-2 py-1 bg-emerald-50 text-emerald-700 rounded text-xs">Resolve</button>}
                        {item.status === 'RESOLVED' && <button onClick={() => handleActionUpdate(item, 'CLOSED')} className="px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs">Close</button>}
                      </td>
                    )}
                    {entityType === 'Sensors' && (
                      <td className="py-3 px-4 whitespace-nowrap">
                        {item.calibration_status !== 'Valid' && <button onClick={() => handleRecalibrate(item)} className="px-2 py-1 bg-teal-50 text-teal-700 rounded text-xs">Record calibration</button>}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
