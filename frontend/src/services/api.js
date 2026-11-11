import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  login: async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const res = await axios.post(`${API_BASE}/auth/login`, formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return res.data;
  },
  getMe: () => apiClient.get('/auth/me').then(res => res.data),
  getMetrics: () => apiClient.get('/dashboard/metrics').then(res => res.data),
  getProducts: () => apiClient.get('/products').then(res => res.data),
  getShipments: () => apiClient.get('/shipments').then(res => res.data),
  getContainers: () => apiClient.get('/containers').then(res => res.data),
  getSensors: () => apiClient.get('/sensors').then(res => res.data),
  getReadings: (shipmentId) => apiClient.get(`/readings?limit=200${shipmentId ? `&shipment_id=${shipmentId}` : ''}`).then(res => res.data),
  getRouteStops: (shipmentId) => apiClient.get(`/route-stops${shipmentId ? `?shipment_id=${shipmentId}` : ''}`).then(res => res.data),
  getThresholdPolicies: () => apiClient.get('/threshold-policies').then(res => res.data),
  getExcursions: () => apiClient.get('/excursions').then(res => res.data),
  getAlerts: () => apiClient.get('/alerts').then(res => res.data),
  acknowledgeAlert: (alertId) => apiClient.put(`/alerts/${alertId}/acknowledge`).then(res => res.data),
  getCustodyEvents: (shipmentId) => apiClient.get(`/custody-events${shipmentId ? `?shipment_id=${shipmentId}` : ''}`).then(res => res.data),
  getCorrectiveActions: () => apiClient.get('/corrective-actions').then(res => res.data),
  getValidationSummary: () => apiClient.get('/validation/summary').then(res => res.data),
  evaluateExcursions: (shipmentId) => apiClient.post(`/excursions/evaluate/${shipmentId}`).then(res => res.data),
  transitionExcursion: (excursionId, status, note = '') => apiClient.put(`/excursions/${excursionId}/status`, { status, note }).then(res => res.data),
  reviewExcursion: (excursionId, review_status) => apiClient.put(`/excursions/${excursionId}/review`, { review_status }).then(res => res.data),
  getExcursionHistory: (excursionId) => apiClient.get(`/excursions/${excursionId}/history`).then(res => res.data),
  updateCorrectiveAction: (actionId, action) => apiClient.put(`/corrective-actions/${actionId}`, action).then(res => res.data),
  updateSensorCalibration: (sensorId, calibration_status, calibration_date, note = '') => apiClient.put(`/sensors/${sensorId}/calibration`, { calibration_status, calibration_date, note }).then(res => res.data),
  getHealth: () => axios.get('http://localhost:8000/health').then(res => res.data)
};
