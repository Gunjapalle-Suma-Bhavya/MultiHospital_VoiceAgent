/**
 * API Client with automatic token & context header injection.
 */

export interface ApiResponse<T = any> {
  ok: boolean;
  status: number;
  data: T | null;
  error?: string;
}

export async function apiCall<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  let session: any = null;
  try {
    const raw = sessionStorage.getItem("nexus_health_session");
    if (raw) session = JSON.parse(raw);
  } catch (e) {
    // Ignore parse error
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (session?.access_token) {
    headers["Authorization"] = `Bearer ${session.access_token}`;
  }
  if (session?.headers) {
    Object.assign(headers, session.headers);
  }

  try {
    const response = await fetch(endpoint, {
      ...options,
      headers,
    });

    const contentType = response.headers.get("content-type") || "";
    let body: any = null;
    if (contentType.includes("application/json")) {
      body = await response.json();
    } else {
      body = await response.text();
    }

    return {
      ok: response.ok,
      status: response.status,
      data: body as T,
      error: response.ok ? undefined : (body?.detail || body?.message || "Request failed"),
    };
  } catch (err: any) {
    console.error(`API Error [${endpoint}]:`, err);
    return {
      ok: false,
      status: 0,
      data: null,
      error: err.message || "Network request failed",
    };
  }
}

// -----------------------------------------------------------------------------
// Specialized Typed API Helpers
// -----------------------------------------------------------------------------

export interface CatalogPage {
  page_id: string;
  page_number: number;
  title: string;
  description: string;
  category: string;
  icon: string;
  default_actions: string[];
}

export interface CatalogRole {
  role_id: string;
  display_title: string;
  total_pages: number;
  description: string;
  pages: CatalogPage[];
}

export interface CatalogResponse {
  total_roles: number;
  total_pages: number;
  roles: CatalogRole[];
}

export interface PageDataResponse {
  role_id: string;
  page_id: string;
  page_title: string;
  page_number: number;
  retrieved_at: string;
  context: {
    hospital_id?: string | null;
    doctor_id?: string | null;
    patient_id?: string | null;
  };
  kpis: Array<{
    label: string;
    value: string;
    trend: string;
    status: 'good' | 'neutral' | 'warning';
  }>;
  table_headers: string[];
  records: Array<Record<string, any>>;
  details: Record<string, any>;
  available_actions: string[];
}

export const api = {
  // 49-Page Catalog & Data
  getCatalog: () => apiCall<CatalogResponse>('/api/v1/dashboard-pages/catalog'),
  getPageData: (role: string, pageId: string, params?: { hospital_id?: string; doctor_id?: string; patient_id?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.hospital_id) searchParams.append('hospital_id', params.hospital_id);
    if (params?.doctor_id) searchParams.append('doctor_id', params.doctor_id);
    if (params?.patient_id) searchParams.append('patient_id', params.patient_id);
    const qs = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return apiCall<PageDataResponse>(`/api/v1/dashboard-pages/data/${role}/${pageId}${qs}`);
  },
  executePageAction: (role: string, pageId: string, action_name: string, action_payload: Record<string, any> = {}) =>
    apiCall(`/api/v1/dashboard-pages/action/${role}/${pageId}`, {
      method: 'POST',
      body: JSON.stringify({ action_name, action_payload }),
    }),

  // Telemetry & SRE
  getGoldenSignals: () => apiCall('/api/v1/should-have/golden-signals'),
  getCostEstimate: () => apiCall('/api/v1/should-have/cost-estimate'),
  getAuditTrail: (limit = 50, offset = 0, category?: string) => {
    const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (category) qs.append('category', category);
    return apiCall(`/api/v1/audit/trail?${qs.toString()}`);
  },

  // DoD & Compliance
  runCanonicalJourney: (payload: { hospital_name?: string; doctor_name?: string; patient_name?: string; patient_phone?: string }) =>
    apiCall('/api/v1/definition-of-done/execute-journey', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  simulateFailure: (mode: 'TRANSIENT_RECOVERY' | 'RECONCILIATION_ESCALATION') =>
    apiCall('/api/v1/definition-of-done/simulate-failure-recovery', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),
  run76Audit: () => apiCall('/api/v1/final-submission/run-verification-audit', { method: 'POST' }),

  // Escalations & Triage
  getEscalations: () => apiCall('/api/v1/should-have/escalations'),
  resolveEscalation: (ticket_id: string, resolution_notes: string, resolved_by: string) =>
    apiCall('/api/v1/should-have/escalations/resolve', {
      method: 'POST',
      body: JSON.stringify({ ticket_id, resolution_notes, resolved_by }),
    }),

  // Doctor Discovery & Booking
  searchDoctors: (payload: { specialty: string; query_text?: string; consultation_mode?: string; time_window?: string }) =>
    apiCall('/api/v1/discovery/search', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  bookSlot: (slot: any, patientPhone: string, idempotencyKey?: string) => {
    const key = idempotencyKey || `idemp-${Date.now()}-${Math.random().toString(36).substring(7)}`;
    return apiCall('/api/v1/capabilities/execute', {
      method: 'POST',
      headers: { 'Idempotency-Key': key },
      body: JSON.stringify({
        capability_name: 'book_appointment',
        parameters: {
          doctor_id: slot.doctor_id,
          slot_id: slot.slot_id,
          patient_phone: patientPhone,
          scheduled_time: slot.start_time,
          hospital_id: slot.hospital_id,
        },
      }),
    });
  },
  verifyRecord: (appointment_id: string) =>
    apiCall('/api/v1/ehr/verify-record', {
      method: 'POST',
      body: JSON.stringify({ appointment_id }),
    }),

  // Patient Actions
  getPatientAppointments: (patientId: string) => apiCall(`/api/v1/patients/${encodeURIComponent(patientId)}/appointments`),
  cancelAppointment: (patientId: string, apptId: string) =>
    apiCall(`/api/v1/patients/${encodeURIComponent(patientId)}/appointments/${apptId}/cancel`, { method: 'POST' }),
  submitQuestionnaire: (patientId: string, responses_json: Record<string, any>) =>
    apiCall(`/api/v1/patients/${encodeURIComponent(patientId)}/questionnaires/submit`, {
      method: 'POST',
      body: JSON.stringify({
        questionnaire_id: 'q-ortho-01',
        responses_json,
      }),
    }),

  // Doctor Dashboard
  getDoctorHome: (doctorId: string) => apiCall(`/api/v1/doctor-dashboard/${doctorId}/home`),
  blockSlot: (doctorId: string, start_date: string, end_date: string, reason: string) =>
    apiCall(`/api/v1/doctor-dashboard/${doctorId}/leaves`, {
      method: 'POST',
      body: JSON.stringify({
        start_date,
        end_date,
        leave_type: 'BLOCKED_SLOT',
        reason,
      }),
    }),

  // Hospital & Connectors
  testConnector: (connector_type: string, base_url: string) =>
    apiCall('/api/v1/should-have/connectors/test', {
      method: 'POST',
      body: JSON.stringify({ connector_type, base_url }),
    }),
  approveHospital: (hospitalId: string) =>
    apiCall(`/api/v1/admin/hospitals/${hospitalId}/approve`, { method: 'POST' }),
  draftHospital: (payload: { name: string; code: string; contact_email: string; admin_name: string; admin_email: string }) =>
    apiCall('/api/v1/onboarding/draft', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getDiscrepancies: () => apiCall('/api/v1/should-have/reconciliation/discrepancies'),
};
