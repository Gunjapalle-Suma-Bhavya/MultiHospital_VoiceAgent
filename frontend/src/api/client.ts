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
