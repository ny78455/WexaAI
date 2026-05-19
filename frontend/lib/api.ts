import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

// Attach Bearer token from localStorage
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const { data } = await axios.post(`${API_URL}/auth/refresh`, {}, { withCredentials: true });
        localStorage.setItem("access_token", data.access_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  signup: (data: any) => api.post("/auth/signup", data),
  login: (data: any) => api.post("/auth/login", data),
  me: () => api.get("/auth/me"),
  logout: () => api.post("/auth/logout"),
  invite: (data: any) => api.post("/auth/invite", data),
  acceptInvite: (data: any) => api.post("/auth/invite/accept", data),
};

// ── Events ────────────────────────────────────────────────────────────────────
export const eventsApi = {
  recent: (limit = 100) => api.get(`/events/recent?limit=${limit}`),
  ingest: (event: any, apiKey: string) =>
    api.post("/events/", event, { headers: { "X-API-Key": apiKey } }),
};

// ── API Keys ─────────────────────────────────────────────────────────────────
export const apiKeysApi = {
  list: () => api.get("/api-keys/"),
  create: (name: string) => api.post("/api-keys/", { name }),
  revoke: (id: string) => api.delete(`/api-keys/${id}`),
};

// ── Dashboards ────────────────────────────────────────────────────────────────
export const dashboardsApi = {
  list: () => api.get("/dashboards/"),
  get: (id: string) => api.get(`/dashboards/${id}`),
  create: (data: any) => api.post("/dashboards/", data),
  update: (id: string, data: any) => api.patch(`/dashboards/${id}`, data),
  delete: (id: string) => api.delete(`/dashboards/${id}`),
  share: (id: string) => api.post(`/dashboards/${id}/share`),
  getShared: (token: string) => api.get(`/dashboards/shared/${token}`),
  addWidget: (dashId: string, data: any) => api.post(`/dashboards/${dashId}/widgets`, data),
  updateWidget: (dashId: string, wid: string, data: any) => api.patch(`/dashboards/${dashId}/widgets/${wid}`, data),
  deleteWidget: (dashId: string, wid: string) => api.delete(`/dashboards/${dashId}/widgets/${wid}`),
  widgetData: (dashId: string, wid: string) => api.get(`/dashboards/${dashId}/widgets/${wid}/data`),
};

// ── Alerts ────────────────────────────────────────────────────────────────────
export const alertsApi = {
  list: () => api.get("/alerts/"),
  get: (id: string) => api.get(`/alerts/${id}`),
  create: (data: any) => api.post("/alerts/", data),
  update: (id: string, data: any) => api.patch(`/alerts/${id}`, data),
  delete: (id: string) => api.delete(`/alerts/${id}`),
  history: (id: string) => api.get(`/alerts/${id}/history`),
};
