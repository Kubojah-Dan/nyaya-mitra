/**
 * NyayaMitra Real API Client
 * Strongly typed client for interacting with the NyayaMitra FastAPI backend.
 * Zero mock data - fully connected to statutory microservices.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export interface IntakeTurnResponse {
  session_id: string;
  stage: string;
  domain: string;
  is_urgent: boolean;
  urgency_reason?: string;
  bot_response: string;
  collected_facts: Record<string, string | number | boolean>;
  next_questions: string[];
  can_generate_document: boolean;
  recommended_template?: string;
}

export interface StatutoryRightItem {
  right_name: string;
  statutory_basis: string;
  tier: number;
  description: string;
  source_url?: string;
}

export interface ActionTimelineStep {
  step_number: number;
  title: string;
  timeframe: string;
  action_required: string;
  authority?: string;
}

export interface RightsResponse {
  domain: string;
  language: string;
  rights_summary: string;
  statutory_rights: StatutoryRightItem[];
  action_timeline: ActionTimelineStep[];
  practical_steps: string[];
  escalation_advice?: string;
}

export interface DeadlineItem {
  label: string;
  value: string;
  source_text: string;
  page_number: number;
  confidence: number;
  assumptions: string;
  requires_verification: boolean;
  urgency_level: string;
  statutory_basis: string;
}

export interface DocumentAnalysisResponse {
  document_id: string;
  session_id?: string;
  filename: string;
  detected_language: string;
  document_type: string;
  document_description: string;
  classification_confidence: number;
  parties: Record<string, string>;
  deadlines: DeadlineItem[];
  plain_summary: string;
  rights_and_next_steps: string[];
  redacted_preview: string;
  pii_redacted_count: number;
  page_count: number;
  ocr_engine: string;
  sha256_hash: string;
  processed_at: string;
}

export interface MissingFieldItem {
  field_name: string;
  description: string;
}

export interface GenerateDocumentResponse {
  success: boolean;
  document_id?: string;
  session_id?: string;
  template_id?: string;
  title?: string;
  statutory_basis?: string;
  markdown_content?: string;
  disclaimer?: string;
  slots_used?: Record<string, string>;
  version?: string;
  sha256_hash?: string;
  created_at?: string;
  error?: string;
  missing_fields?: MissingFieldItem[];
}

export interface EscalationResourceContact {
  authority_name: string;
  jurisdiction: string;
  authority_level: string;
  toll_free_number: string;
  direct_contact: string;
  email: string;
  address: string;
  official_website: string;
  working_hours: string;
}

export interface EligibilityEvaluation {
  is_eligible: boolean;
  qualifying_categories: string[];
  state: string;
  statutory_income_ceiling: number;
  declared_income?: number;
  statutory_citation: string;
  required_documents: string[];
  free_services_included: string[];
}

/**
 * Sends a citizen turn to the guided intake engine.
 */
export async function sendIntakeTurn(
  sessionId: string,
  message: string,
  voiceInput: boolean = false
): Promise<IntakeTurnResponse> {
  const res = await fetch(`${API_BASE_URL}/intake/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      voice_input: voiceInput,
    }),
  });
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Intake service error (${res.status}): ${errorBody}`);
  }
  return res.json();
}

/**
 * Fetches verified statutory rights and action timeline for a domain.
 */
export async function fetchRights(
  sessionId: string,
  domain: string,
  language: string = "en",
  triggerDate?: string
): Promise<RightsResponse> {
  const res = await fetch(`${API_BASE_URL}/intake/rights`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      domain,
      language,
      trigger_date: triggerDate,
    }),
  });
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Rights service error (${res.status}): ${errorBody}`);
  }
  return res.json();
}

/**
 * Analyzes uploaded document text or file via OCR and Deadline Guardian.
 */
export async function analyzeDocument(
  payload: { rawText?: string; file?: File; documentTitle?: string; sessionId?: string }
): Promise<DocumentAnalysisResponse> {
  const formData = new FormData();
  if (payload.file) {
    formData.append("file", payload.file);
  }
  if (payload.rawText) {
    formData.append("raw_text", payload.rawText);
  }
  if (payload.documentTitle) {
    formData.append("document_title", payload.documentTitle);
  }
  if (payload.sessionId) {
    formData.append("session_id", payload.sessionId);
  }

  const res = await fetch(`${API_BASE_URL}/documents/analyze`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Document analysis error (${res.status}): ${errorBody}`);
  }
  return res.json();
}

/**
 * Generates a deterministically verified legal draft.
 */
export async function generateLegalDocument(
  templateId: string,
  slots: Record<string, string>,
  sessionId?: string
): Promise<GenerateDocumentResponse> {
  const res = await fetch(`${API_BASE_URL}/generator/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      template_id: templateId,
      slots,
      session_id: sessionId,
    }),
  });
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Generator error (${res.status}): ${errorBody}`);
  }
  return res.json();
}

/**
 * Evaluates citizen eligibility for free legal aid under Section 12 of LSA Act 1987.
 */
export async function evaluateEligibility(criteria: {
  state?: string;
  is_woman_or_child: boolean;
  is_sc_or_st: boolean;
  is_in_custody: boolean;
  is_disabled: boolean;
  annual_income?: number;
}): Promise<EligibilityEvaluation> {
  const res = await fetch(`${API_BASE_URL}/escalation/eligibility`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(criteria),
  });
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Eligibility check error (${res.status}): ${errorBody}`);
  }
  return res.json();
}

/**
 * Retrieves official legal aid resources (DLSA/SLSA/NALSA) for jurisdiction.
 */
export async function fetchLegalAidResources(
  state: string = "DELHI",
  district?: string
): Promise<EscalationResourceContact[]> {
  const params = new URLSearchParams({ state });
  if (district) params.append("district", district);

  const res = await fetch(`${API_BASE_URL}/escalation/resources?${params.toString()}`);
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Resource directory error (${res.status}): ${errorBody}`);
  }
  return res.json();
}
