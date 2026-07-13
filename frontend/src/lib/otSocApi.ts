export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type EvidenceEvent = {
  id: number;
  case?: number;
  timestamp: string | null;
  rule_id: string;
  description: string;
  agent: string;
  location: string;
  evidence_type: string;
  raw?: Record<string, unknown>;
};

export type OtCase = {
  id: number;
  case_type: string;
  classification: "validation_not_malicious" | "important_ot_operation" | "suspicious_ot_operation";
  tag: string;
  node_id: string;
  old_value: unknown;
  new_value: unknown;
  source_ip: string | null;
  destination_ip: string | null;
  destination_port: number | null;
  correlation_window_seconds: number | null;
  created_at_from_case: string | null;
  ingested_at: string;
  rule_ids: string[];
  evidence_count?: number;
  evidence?: EvidenceEvent[];
  raw?: Record<string, unknown>;
};

export type Rule = {
  id: number;
  rule_id: string;
  name: string;
  description: string;
  level: number;
  source: string;
  category: string;
  classification_hint: string;
};

export type Tag = {
  id: number;
  name: string;
  node_id: string;
  tag_type: string;
  criticality: string;
  station_or_area: string;
  is_writable: boolean;
  description: string;
};

export type Asset = {
  id: number;
  name: string;
  ip_address: string;
  role: string;
  platform: string;
  description: string;
};

export type CountByValue = {
  value: string;
  count: number;
};

export type DashboardSummary = {
  total_cases: number;
  total_evidence: number;
  total_rules: number;
  total_tags: number;
  total_assets: number;
  cases_by_classification: CountByValue[];
  cases_by_tag: CountByValue[];
  evidence_by_rule_id: CountByValue[];
  latest_cases: OtCase[];
};

export type ApiResult<T> =
  | { ok: true; data: T; error?: never }
  | { ok: false; data?: never; error: string };

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api";

export function getApiBaseUrl() {
  const configured =
    process.env.OT_SOC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_OT_SOC_API_BASE_URL ||
    DEFAULT_API_BASE_URL;

  return configured.replace(/\/$/, "");
}

export function getPublicApiBaseUrl() {
  const configured =
    process.env.NEXT_PUBLIC_OT_SOC_API_BASE_URL ||
    process.env.OT_SOC_PUBLIC_API_BASE_URL ||
    DEFAULT_API_BASE_URL;

  return configured.replace(/\/$/, "");
}

export function buildQuery(params: Record<string, string | number | undefined>) {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && String(value).trim() !== "") {
      query.set(key, String(value));
    }
  });

  const text = query.toString();
  return text ? `?${text}` : "";
}

export async function fetchApi<T>(path: string): Promise<ApiResult<T>> {
  const url = `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;

  try {
    const response = await fetch(url, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      return {
        ok: false,
        error: `Backend returned HTTP ${response.status} for ${url}`,
      };
    }

    return { ok: true, data: (await response.json()) as T };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Backend request failed",
    };
  }
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "Unknown";
  }

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatValue(value: unknown) {
  if (value === null || value === undefined) {
    return "null";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}
