/**
 * NyayaMitra Real API Client
 * Strongly typed client for interacting with the NyayaMitra FastAPI backend.
 * Zero mock data - fully connected to statutory microservices.
 */

const configuredApiUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

export const API_BASE_URL =
  configuredApiUrl ||
  (process.env.NODE_ENV === "production" ? "" : "http://localhost:8000/api/v1");

function checkApiConfig(): void {
  if (!API_BASE_URL && typeof window !== "undefined" && process.env.NODE_ENV === "production") {
    throw new Error(
      "NEXT_PUBLIC_API_BASE_URL is not configured. Please configure the backend API URL in your deployment environment."
    );
  }
}

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
  qualifying_categories?: string[];
  state?: string;
  statutory_income_ceiling?: number;
  declared_income?: number;
  statutory_citation?: string;
  required_documents?: string[];
  free_services_included?: string[];
  statutory_ground?: string;
  explanation?: string;
  reason?: string;
}

export type EligibilityResult = EligibilityEvaluation;

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
  const data = await res.json();
  return {
    ...data,
    bot_response: data.bot_response || data.message || data.response || "",
  };
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

export async function generateDocument(payload: {
  template_id: string;
  slots: Record<string, string>;
  session_id?: string;
}): Promise<GenerateDocumentResponse> {
  return generateLegalDocument(payload.template_id, payload.slots, payload.session_id);
}

/**
 * Evaluates citizen eligibility for free legal aid under Section 12 of LSA Act 1987.
 */
export async function evaluateEligibility(criteria: {
  state?: string;
  is_woman_or_child?: boolean;
  is_sc_or_st?: boolean;
  is_sc_st?: boolean;
  is_in_custody?: boolean;
  is_disabled?: boolean;
  is_disaster_victim?: boolean;
  is_industrial_workman?: boolean;
  is_trafficking_victim?: boolean;
  annual_income?: number;
  annual_income_inr?: number;
  district?: string;
  case_type?: string;
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

export const checkLegalAidEligibility = evaluateEligibility;

export function evaluateLegalAidEligibility(
  criteria: {
    is_woman_or_child?: boolean;
    is_sc_st?: boolean;
    is_disabled?: boolean;
    is_in_custody?: boolean;
    is_disaster_victim?: boolean;
    is_industrial_workman?: boolean;
    is_trafficking_victim?: boolean;
    annual_income_inr?: number;
    state?: string;
    case_type?: string;
  },
  lang: "en" | "hi" = "en"
): EligibilityEvaluation {
  const isSpecial =
    criteria.is_woman_or_child ||
    criteria.is_sc_st ||
    criteria.is_disabled ||
    criteria.is_in_custody ||
    criteria.is_disaster_victim ||
    criteria.is_industrial_workman ||
    criteria.is_trafficking_victim;

  const ceiling = 300000;
  const isIncomeOk = (criteria.annual_income_inr ?? 0) <= ceiling;
  const eligible = isSpecial || isIncomeOk;

  return {
    is_eligible: eligible,
    state: criteria.state || "DELHI",
    statutory_income_ceiling: ceiling,
    declared_income: criteria.annual_income_inr,
    statutory_ground: isSpecial
      ? "Section 12 (Special Priority Category)"
      : "Section 12(h) Income Criteria",
    reason: eligible
      ? lang === "hi"
        ? "आप विधिक सेवा प्राधिकरण अधिनियम (धारा 12) के तहत 100% निःशुल्क सरकारी वकील व विधिक सहायता के पात्र हैं।"
        : "You qualify for 100% free government legal counsel and court fee waivers under Section 12 LSAA 1987."
      : lang === "hi"
        ? "आपकी आय सीमा निःशुल्क कानूनी सहायता से अधिक है, किंतु टेली-लॉ परामर्श उपलब्ध है।"
        : "Your income exceeds the free legal aid limit. However, Tele-Law pre-litigation advice remains available.",
  };
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

export interface SectionDelta {
  section_id: string;
  section_a: string;
  section_b: string;
  delta_type: "ADDED" | "REMOVED" | "MODIFIED" | "UNCHANGED";
  description: string;
  text_a: string;
  text_b: string;
  citations: string[];
}

export interface DocumentCompareResponse {
  success: boolean;
  summary: string;
  total_sections_a: number;
  total_sections_b: number;
  added_count: number;
  removed_count: number;
  modified_count: number;
  unchanged_count: number;
  deltas: SectionDelta[];
  added_sections: string[];
  removed_sections: string[];
  modified_sections: string[];
  citations: string[];
  warnings: string[];
  model_used: string;
  tier: string;
  fallback_used: boolean;
  status: string;
  compared_at: string;
  disclaimer: string;
}

export interface OutlineSection {
  section_id: string;
  heading: string;
  start_char: number;
  end_char: number;
  level: number;
  summary: string;
  children: OutlineSection[];
}

export interface DocumentOutlineResponse {
  document_id?: string;
  title: string;
  total_sections: number;
  sections: OutlineSection[];
}

export interface ModelTierInfo {
  tier_name: string;
  primary_model: string;
  fallback_model: string;
  timeout_seconds: number;
  max_tokens: number;
  input_cost_per_1m_tokens_inr: number;
  output_cost_per_1m_tokens_inr: number;
  supported_tasks: string[];
}

export interface ModelInventoryResponse {
  architecture: string;
  primary_provider: string;
  fallback_provider: string;
  offline_fallback: string;
  tiers: Record<string, ModelTierInfo>;
  telemetry: Record<string, any>;
  verified_statutory_laws: string[];
  timestamp: string;
}

/**
 * Compares two legal documents with file uploads or text.
 */
export async function compareDocuments(payload: {
  fileA?: File;
  fileB?: File;
  documentA?: string;
  documentB?: string;
  titleA?: string;
  titleB?: string;
  language?: string;
  sessionId?: string;
}): Promise<DocumentCompareResponse> {
  const formData = new FormData();
  if (payload.fileA) formData.append("file_a", payload.fileA);
  if (payload.fileB) formData.append("file_b", payload.fileB);
  if (payload.documentA) formData.append("document_a", payload.documentA);
  if (payload.documentB) formData.append("document_b", payload.documentB);
  if (payload.titleA) formData.append("title_a", payload.titleA);
  if (payload.titleB) formData.append("title_b", payload.titleB);
  if (payload.language) formData.append("language", payload.language);
  if (payload.sessionId) formData.append("session_id", payload.sessionId);

  const res = await fetch(`${API_BASE_URL}/documents/compare`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Document comparison error (${res.status}): ${errText}`);
  }
  return res.json();
}

/**
 * Compares two legal documents via JSON payload.
 */
export async function compareDocumentsJson(payload: {
  document_a: string;
  document_b: string;
  title_a?: string;
  title_b?: string;
  language?: string;
  session_id?: string;
}): Promise<DocumentCompareResponse> {
  const res = await fetch(`${API_BASE_URL}/documents/compare-json`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Document comparison error (${res.status}): ${errText}`);
  }
  return res.json();
}

/**
 * Generates structured document outline for in-document navigation.
 */
export async function getDocumentOutline(payload: {
  raw_text?: string;
  document_id?: string;
  title?: string;
}): Promise<DocumentOutlineResponse> {
  const res = await fetch(`${API_BASE_URL}/documents/outline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Outline generation error (${res.status}): ${errText}`);
  }
  return res.json();
}

/**
 * In-memory client cache with TTL for static metadata endpoints to reduce network requests.
 */
const metaClientCache = new Map<string, { data: unknown; expiry: number }>();

function getCachedItem<T>(key: string): T | null {
  const item = metaClientCache.get(key);
  if (item && item.expiry > Date.now()) {
    return item.data as T;
  }
  return null;
}

function setCachedItem<T>(key: string, data: T, ttlMs: number = 300000): void {
  metaClientCache.set(key, { data, expiry: Date.now() + ttlMs });
}

/**
 * Fetches GenAI multi-tier inventory with client-side SWR caching.
 */
export async function getModelMetadata(): Promise<ModelInventoryResponse> {
  const cached = getCachedItem<ModelInventoryResponse>("meta_models");
  if (cached) return cached;

  const res = await fetch(`${API_BASE_URL}/meta/models`, {
    headers: { "Cache-Control": "max-age=300" },
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Model metadata error (${res.status}): ${errText}`);
  }
  const data: ModelInventoryResponse = await res.json();
  setCachedItem("meta_models", data, 300000);
  return data;
}

/**
 * Fetches general system metadata with client-side SWR caching.
 */
export async function getSystemMetadata(): Promise<{
  app_name: string;
  app_version: string;
  environment: string;
  supported_languages: string[];
  modules: Array<{ id: string; name: string; verb: string }>;
}> {
  const cached = getCachedItem<{
    app_name: string;
    app_version: string;
    environment: string;
    supported_languages: string[];
    modules: Array<{ id: string; name: string; verb: string }>;
  }>("meta_system");
  if (cached) return cached;

  const res = await fetch(`${API_BASE_URL}/meta/system`, {
    headers: { "Cache-Control": "max-age=300" },
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`System metadata error (${res.status}): ${errText}`);
  }
  const data = await res.json();
  setCachedItem("meta_system", data, 300000);
  return data;
}

export interface ECourtsCNRResult {
  valid: boolean;
  cnr: string;
  state_code?: string;
  state_name?: string;
  district_court_code?: string;
  case_number?: string;
  year?: string;
  court_level?: string;
  direct_lookup_url?: string;
  official_portal?: string;
  instructions?: string;
  error?: string;
}

/**
 * Performs eCourts CNR 16-character structural resolution and official portal routing.
 */
export async function lookupECourtsCNR(cnrNumber: string): Promise<ECourtsCNRResult> {
  const cleanCNR = cnrNumber.replace(/[^A-Za-z0-9]/g, "").toUpperCase();
  const res = await fetch(`${API_BASE_URL}/sources/ecourts/cnr/${cleanCNR}`);
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`eCourts lookup error (${res.status}): ${errText}`);
  }
  return res.json();
}

