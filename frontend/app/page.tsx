"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  MessageSquare,
  Scale,
  FileText,
  FilePen,
  Landmark,
  Globe,
  Mic,
  Home,
  ShoppingCart,
  ClipboardList,
  AlertTriangle,
  ArrowRight,
  Clock,
  CheckCircle,
  Lock,
  Users,
  CalendarDays,
  Download,
  Search,
  Settings,
  MapPin,
  Phone,
  Monitor,
  ShieldCheck,
  Info,
  ChevronRight,
  Upload,
  Loader2,
  RefreshCw,
  FileCheck,
} from "lucide-react";
import {
  sendIntakeTurn,
  fetchRights,
  analyzeDocument,
  generateLegalDocument,
  evaluateEligibility,
  fetchLegalAidResources,
  IntakeTurnResponse,
  RightsResponse,
  DocumentAnalysisResponse,
  DeadlineItem,
  GenerateDocumentResponse,
  EscalationResourceContact,
  EligibilityEvaluation,
} from "@/lib/api";

type Language = "en" | "hi";

export default function HomePage() {
  const [lang, setLang] = useState<Language>("en");
  const [activeTab, setActiveTab] = useState<string>("intake");
  const [sessionId] = useState<string>(() => `nm_session_${Date.now()}`);

  // --- Module 1: Guided Intake State ---
  const [intakeMessages, setIntakeMessages] = useState<
    Array<{ sender: "assistant" | "user"; text: string; domain?: string; urgent?: boolean }>
  >([
    {
      sender: "assistant",
      text:
        lang === "hi"
          ? "नमस्ते! मैं न्यायमित्र हूँ। कृपया अपनी कानूनी समस्या बताएं (जैसे किरायेदारी विवाद, उपभोक्ता शिकायत, आरटीआई या पुलिस नोटिस)।"
          : "Namaste! I am NyayaMitra. Please describe your legal problem in plain words (e.g. tenancy dispute, consumer refund, RTI application, or court notice).",
    },
  ]);
  const [inputQuery, setInputQuery] = useState<string>("");
  const [detectedDomain, setDetectedDomain] = useState<string | null>(null);
  const [isUrgent, setIsUrgent] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [intakeLoading, setIntakeLoading] = useState<boolean>(false);
  const [intakeError, setIntakeError] = useState<string | null>(null);

  // --- Module 2: Rights & Timelines State ---
  const [rightsDomain, setRightsDomain] = useState<string>("TENANCY");
  const [rightsData, setRightsData] = useState<RightsResponse | null>(null);
  const [rightsLoading, setRightsLoading] = useState<boolean>(false);
  const [rightsError, setRightsError] = useState<string | null>(null);

  // --- Module 3: Document Scanner & Deadline Guardian State ---
  const [docInputText, setDocInputText] = useState<string>("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docAnalysis, setDocAnalysis] = useState<DocumentAnalysisResponse | null>(null);
  const [userDeadlines, setUserDeadlines] = useState<DeadlineItem[]>([]);
  const [docLoading, setDocLoading] = useState<boolean>(false);
  const [docError, setDocError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- Module 4: Mera Document (Controlled Generator) State ---
  const [selectedTemplate, setSelectedTemplate] = useState<string>("RTI_APPLICATION");
  // Zero pre-filled mock data - purely empty strings with instructive placeholders
  const [slots, setSlots] = useState<Record<string, string>>({
    applicant_name: "",
    applicant_address: "",
    applicant_contact: "",
    public_authority_name: "",
    public_authority_address: "",
    subject_matter: "",
    particulars_of_information: "",
    place: "",
  });
  const [generatedDoc, setGeneratedDoc] = useState<GenerateDocumentResponse | null>(null);
  const [genLoading, setGenLoading] = useState<boolean>(false);
  const [genError, setGenError] = useState<string | null>(null);

  // --- Module 5: Escalation & Eligibility State ---
  const [selectedState, setSelectedState] = useState<string>("DELHI");
  const [selectedDistrict, setSelectedDistrict] = useState<string>("SOUTH");
  const [resources, setResources] = useState<EscalationResourceContact[]>([]);
  const [resourceLoading, setResourceLoading] = useState<boolean>(false);
  const [eligibilityCriteria, setEligibilityCriteria] = useState<{
    is_woman_or_child: boolean;
    is_sc_or_st: boolean;
    is_in_custody: boolean;
    is_disabled: boolean;
    annual_income: number;
  }>({
    is_woman_or_child: false,
    is_sc_or_st: false,
    is_in_custody: false,
    is_disabled: false,
    annual_income: 180000,
  });
  const [eligibilityResult, setEligibilityResult] = useState<EligibilityEvaluation | null>(null);

  // ---------------------------------------------------------------------------
  // Handlers: Module 1 — Guided Intake (Real API)
  // ---------------------------------------------------------------------------
  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputQuery;
    if (!text.trim() || intakeLoading) return;

    setIntakeError(null);
    setInputQuery("");

    // Optimistically append user message
    const userMsg = { sender: "user" as const, text };
    setIntakeMessages((prev) => [...prev, userMsg]);
    setIntakeLoading(true);

    try {
      const res: IntakeTurnResponse = await sendIntakeTurn(sessionId, text);
      setDetectedDomain(res.domain);
      setIsUrgent(res.is_urgent);

      setIntakeMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: res.bot_response,
          domain: res.domain,
          urgent: res.is_urgent,
        },
      ]);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Failed to connect to NyayaMitra backend service.";
      setIntakeError(errMsg);
      setIntakeMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text:
            lang === "hi"
              ? `कनेक्शन त्रुटि: सर्वर से संपर्क नहीं हो सका (${errMsg})। कृपया सुनिश्चित करें कि बैकएंड सेवा सक्रिय है।`
              : `Connection notice: Could not reach legal reasoning backend (${errMsg}). Please ensure backend is running at ${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1"}.`,
        },
      ]);
    } finally {
      setIntakeLoading(false);
    }
  };

  const handleSimulateVoice = () => {
    setIsRecording(true);
    setTimeout(() => {
      setIsRecording(false);
      const sampleVoiceText =
        lang === "hi"
          ? "मकान मालिक बिना नोटिस के घर खाली करने का दबाव बना रहा है"
          : "My landlord sent me an illegal eviction notice without 15 days notice";
      setInputQuery(sampleVoiceText);
      handleSendMessage(sampleVoiceText);
    }, 1200);
  };

  // ---------------------------------------------------------------------------
  // Handlers: Module 2 — Rights & Timelines (Real API)
  // ---------------------------------------------------------------------------
  const loadRights = async (domain: string) => {
    setRightsLoading(true);
    setRightsError(null);
    try {
      const res = await fetchRights(sessionId, domain, lang);
      setRightsData(res);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unable to fetch statutory rights";
      setRightsError(msg);
    } finally {
      setRightsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "rights") {
      loadRights(rightsDomain);
    }
  }, [activeTab, rightsDomain, lang]);

  // ---------------------------------------------------------------------------
  // Handlers: Module 3 — Document Scanner & Deadline Guardian (Real API)
  // ---------------------------------------------------------------------------
  const handleAnalyzeDocument = async () => {
    if (!docInputText.trim() && !selectedFile) {
      setDocError(lang === "hi" ? "कृपया दस्तावेज़ का पाठ दर्ज करें या फ़ाइल अपलोड करें।" : "Please enter document text or select a file to analyze.");
      return;
    }

    setDocLoading(true);
    setDocError(null);
    setDocAnalysis(null);

    try {
      const res = await analyzeDocument({
        rawText: docInputText || undefined,
        file: selectedFile || undefined,
        documentTitle: selectedFile?.name || "Uploaded Notice",
        sessionId,
      });
      setDocAnalysis(res);
      setUserDeadlines(res.deadlines || []);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Document analysis failed";
      setDocError(msg);
    } finally {
      setDocLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setDocError(null);
    }
  };

  const handleExportICS = () => {
    if (!userDeadlines.length) return;
    const firstDl = userDeadlines[0];
    const eventDate = firstDl.value.replace(/[^0-9]/g, "") || "20261024";
    const icsContent = `BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//NyayaMitra//Legal Deadline Guardian//EN\r\nBEGIN:VEVENT\r\nUID:nyayamitra-${Date.now()}@nyayamitra.gov.in\r\nDTSTART;VALUE=DATE:${eventDate.padEnd(8, "0").slice(0, 8)}\r\nSUMMARY:NyayaMitra: ${firstDl.label}\r\nDESCRIPTION:Statutory Deadline: ${firstDl.statutory_basis}. Grounded by NyayaMitra.\r\nSTATUS:CONFIRMED\r\nBEGIN:VALARM\r\nTRIGGER:-P1D\r\nACTION:DISPLAY\r\nDESCRIPTION:Statutory reminder: ${firstDl.label}\r\nEND:VALARM\r\nEND:VEVENT\r\nEND:VCALENDAR`;

    const blob = new Blob([icsContent], { type: "text/calendar" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `nyayamitra-deadline-${Date.now()}.ics`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ---------------------------------------------------------------------------
  // Handlers: Module 4 — Mera Document Generator (Real API)
  // ---------------------------------------------------------------------------
  const handleGenerateDocument = async () => {
    setGenLoading(true);
    setGenError(null);
    setGeneratedDoc(null);

    try {
      const res = await generateLegalDocument(selectedTemplate, slots, sessionId);
      if (!res.success && res.error) {
        setGenError(res.error);
      }
      setGeneratedDoc(res);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Document generation service error";
      setGenError(msg);
    } finally {
      setGenLoading(false);
    }
  };

  const handleDownloadDoc = (format: string) => {
    if (!generatedDoc || !generatedDoc.markdown_content) return;
    let content = generatedDoc.markdown_content;
    let mime = "text/markdown";

    if (format === "txt") {
      content = content.replace(/#/g, "").replace(/\*\*/g, "");
      mime = "text/plain";
    } else if (format === "html") {
      content = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${generatedDoc.title || "NyayaMitra Legal Draft"}</title><style>body{font-family:sans-serif;max-width:800px;margin:40px auto;padding:20px;line-height:1.6;color:#1e293b}pre{white-space:pre-wrap;background:#f8fafc;padding:1rem;border:1px solid #e2e8f0;border-radius:8px}</style></head><body><pre>${content}</pre></body></html>`;
      mime = "text/html";
    }

    const blob = new Blob([content], { type: `${mime};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedTemplate.toLowerCase()}_draft.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ---------------------------------------------------------------------------
  // Handlers: Module 5 — Legal Aid & Escalation (Real API)
  // ---------------------------------------------------------------------------
  const loadResources = async (state: string, district?: string) => {
    setResourceLoading(true);
    try {
      const list = await fetchLegalAidResources(state, district);
      setResources(list);
    } catch {
      // Fallback display handled gracefully
    } finally {
      setResourceLoading(false);
    }
  };

  const runEligibilityCheck = async () => {
    try {
      const evalRes = await evaluateEligibility({
        state: selectedState,
        is_woman_or_child: eligibilityCriteria.is_woman_or_child,
        is_sc_or_st: eligibilityCriteria.is_sc_or_st,
        is_in_custody: eligibilityCriteria.is_in_custody,
        is_disabled: eligibilityCriteria.is_disabled,
        annual_income: eligibilityCriteria.annual_income,
      });
      setEligibilityResult(evalRes);
    } catch {
      // Graceful fallback calculation
    }
  };

  useEffect(() => {
    if (activeTab === "escalation") {
      loadResources(selectedState, selectedDistrict);
      runEligibilityCheck();
    }
  }, [activeTab, selectedState, eligibilityCriteria]);

  const isEligible =
    eligibilityResult?.is_eligible ??
    (eligibilityCriteria.is_woman_or_child ||
      eligibilityCriteria.is_sc_or_st ||
      eligibilityCriteria.is_in_custody ||
      eligibilityCriteria.is_disabled ||
      eligibilityCriteria.annual_income <= 300000);

  return (
    <div className="nm-container">
      {/* Official Civic Notice Banner */}
      <aside className="nm-disclaimer-banner" role="alert">
        <span className="nm-disclaimer-icon">
          <Scale size={18} aria-hidden="true" />
        </span>
        <div>
          <strong>{lang === "hi" ? "आधिकारिक नागरिक विधिक सूचना:" : "Official Citizen Legal Notice:"}</strong>{" "}
          {lang === "hi"
            ? "न्यायमित्र भारतीय कानूनों (BNS/BNSS/BSA 2024, RTI, उपभोक्ता संरक्षण) के आधार पर नागरिक सहायता एवं दस्तावेज प्रारूपण प्रदान करता है। यह कोई निजी लॉ फर्म नहीं है। निःशुल्क सरकारी वकील हेतु NALSA हेल्पलाइन 15100 पर संपर्क करें।"
            : "NyayaMitra provides statutory guidance, rights explanations, and structured drafting based on active Indian law. We do not provide private legal representation. For 100% free government legal aid, call NALSA at 15100."}
        </div>
      </aside>

      {/* Citizen Dashboard Hero Card */}
      <section className="nm-hero-card">
        <div className="nm-hero-content">
          <div>
            <h2 className="nm-hero-title">
              {lang === "hi" ? "नागरिक विधिक अधिकार केंद्र" : "Citizen Legal Empowerment Dashboard"}
            </h2>
            <p className="nm-hero-subtitle">
              {lang === "hi"
                ? "भारतीय कानून 2024 (BNS, BNSS, BSA), आरटीआई अधिनियम 2005 एवं उपभोक्ता संरक्षण अधिनियम 2019 पर आधारित"
                : "Grounded strictly in Bharatiya Sanhitas 2024, RTI Act 2005, and Consumer Protection Act 2019"}
            </p>
          </div>
          <button
            className="nm-btn-lang"
            onClick={() => setLang(lang === "en" ? "hi" : "en")}
            aria-label="Toggle language between English and Hindi"
          >
            <Globe size={15} aria-hidden="true" />
            {lang === "en" ? "हिंदी में बदलें" : "Switch to English"}
          </button>
        </div>
      </section>

      {/* Mobile-First Flutter-like Pill Navigation Tabs */}
      <nav className="nm-nav-tabs" role="tablist" aria-label="Legal Services Navigation">
        <button
          className={`nm-tab-btn ${activeTab === "intake" ? "active" : ""}`}
          onClick={() => setActiveTab("intake")}
          role="tab"
          aria-selected={activeTab === "intake"}
        >
          <MessageSquare size={16} aria-hidden="true" />
          <span>{lang === "hi" ? "1. समझो मेरा प्रॉब्लम" : "1. Guided Intake"}</span>
        </button>
        <button
          className={`nm-tab-btn ${activeTab === "rights" ? "active" : ""}`}
          onClick={() => setActiveTab("rights")}
          role="tab"
          aria-selected={activeTab === "rights"}
        >
          <Scale size={16} aria-hidden="true" />
          <span>{lang === "hi" ? "2. मेरे अधिकार" : "2. Rights & Timelines"}</span>
        </button>
        <button
          className={`nm-tab-btn ${activeTab === "scanner" ? "active" : ""}`}
          onClick={() => setActiveTab("scanner")}
          role="tab"
          aria-selected={activeTab === "scanner"}
        >
          <FileText size={16} aria-hidden="true" />
          <span>{lang === "hi" ? "3. नोटिस स्कैनर" : "3. Document Scanner"}</span>
        </button>
        <button
          className={`nm-tab-btn ${activeTab === "generator" ? "active" : ""}`}
          onClick={() => setActiveTab("generator")}
          role="tab"
          aria-selected={activeTab === "generator"}
        >
          <FilePen size={16} aria-hidden="true" />
          <span>{lang === "hi" ? "4. मेरा डाक्यूमेंट" : "4. Mera Document"}</span>
        </button>
        <button
          className={`nm-tab-btn ${activeTab === "escalation" ? "active" : ""}`}
          onClick={() => setActiveTab("escalation")}
          role="tab"
          aria-selected={activeTab === "escalation"}
        >
          <Landmark size={16} aria-hidden="true" />
          <span>{lang === "hi" ? "5. न्याय सहायता" : "5. Free Legal Aid"}</span>
        </button>
      </nav>

      {/* ===================================================================== */}
      {/* WORKSPACE 1: GUIDED INTAKE ("SAMJHO MERA PROBLEM")                    */}
      {/* ===================================================================== */}
      {activeTab === "intake" && (
        <section className="nm-workspace" aria-labelledby="intake-heading">
          <div className="nm-workspace-header">
            <h2 id="intake-heading">
              <MessageSquare size={20} aria-hidden="true" />
              {lang === "hi" ? "समझो मेरा प्रॉब्लम (Guided Intake)" : "Samjho Mera Problem (Guided Intake)"}
            </h2>
            <p>
              {lang === "hi"
                ? "अपनी भाषा में समस्या बताएं। न्यायमित्र वास्तविक कानूनी श्रेणी पहचानेगा और आपको सही वैधानिक अधिकार बताएगा।"
                : "Explain your issue in plain words. NyayaMitra identifies legal domain and active statutes via real AI reasoning."}
            </p>
          </div>

          {/* Quick Scenario Chips for First-Time Users */}
          <div className="nm-scenario-row">
            <span className="nm-scenario-label">
              {lang === "hi" ? "त्वरित उदाहरण:" : "Quick Inquiries:"}
            </span>
            <button
              className="nm-btn nm-btn-secondary nm-btn-sm"
              onClick={() => handleSendMessage("Landlord sent illegal eviction notice without 15 days written notice")}
            >
              <Home size={13} aria-hidden="true" />
              {lang === "hi" ? "मकान खाली कराने का नोटिस" : "Landlord Eviction Notice"}
            </button>
            <button
              className="nm-btn nm-btn-secondary nm-btn-sm"
              onClick={() => handleSendMessage("Bought defective refrigerator on Flipkart and dealer refused replacement")}
            >
              <ShoppingCart size={13} aria-hidden="true" />
              {lang === "hi" ? "खराब सामान व रिफंड" : "Defective Appliance"}
            </button>
            <button
              className="nm-btn nm-btn-secondary nm-btn-sm"
              onClick={() => handleSendMessage("How to file RTI application for municipality road repair fund status")}
            >
              <ClipboardList size={13} aria-hidden="true" />
              {lang === "hi" ? "सड़क मरम्मत आरटीआई" : "RTI Tender Funds"}
            </button>
            <button
              className="nm-btn nm-btn-secondary nm-btn-sm"
              onClick={() => handleSendMessage("Police is calling me to police station without written notice or FIR")}
            >
              <AlertTriangle size={13} aria-hidden="true" />
              {lang === "hi" ? "पुलिस सम्मन / नोटिस" : "Police Notice Inquiry"}
            </button>
          </div>

          {/* Conversation Stream */}
          <div className="nm-chat-container" role="log" aria-live="polite">
            {intakeMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`nm-chat-bubble ${msg.sender === "assistant" ? "nm-chat-assistant" : "nm-chat-user"}`}
              >
                {msg.text}
              </div>
            ))}
            {intakeLoading && (
              <div className="nm-chat-bubble nm-chat-assistant nm-chat-loading">
                <Loader2 size={16} className="nm-spin" aria-hidden="true" />
                <span>{lang === "hi" ? "कानूनी विश्लेषण जारी है..." : "Analyzing under active Indian statutes..."}</span>
              </div>
            )}
          </div>

          {/* Live Fact Badges */}
          {detectedDomain && (
            <div className="nm-badge-row">
              <span className="nm-badge nm-badge-verified">
                <CheckCircle size={12} aria-hidden="true" />
                {lang === "hi" ? "पहचानी गई श्रेणी:" : "Identified Domain:"} {detectedDomain}
              </span>
              {isUrgent && (
                <span className="nm-badge nm-badge-critical">
                  <AlertTriangle size={12} aria-hidden="true" />
                  {lang === "hi" ? "अति-महत्वपूर्ण मामला (Helpline 15100)" : "Urgent Matter (Call 15100)"}
                </span>
              )}
              <button
                className="nm-btn nm-btn-gold nm-btn-sm"
                onClick={() => {
                  setRightsDomain(detectedDomain);
                  setActiveTab("rights");
                }}
              >
                <ChevronRight size={13} aria-hidden="true" />
                {lang === "hi" ? "इस श्रेणी के अधिकार देखें" : "View Statutory Rights"}
              </button>
            </div>
          )}

          {/* Error Alert */}
          {intakeError && (
            <div className="nm-alert nm-alert-danger" role="alert">
              <AlertTriangle size={15} aria-hidden="true" />
              <span>{intakeError}</span>
            </div>
          )}

          {/* Input Controls */}
          <div className="nm-input-row">
            <input
              type="text"
              className="nm-input"
              placeholder={
                lang === "hi"
                  ? "अपनी कानूनी समस्या यहाँ लिखें (उदा. मकान मालिक का नोटिस, खराब उत्पाद, आरटीआई)..."
                  : "Type your legal problem here (e.g. landlord notice, defective item, RTI request)..."
              }
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              disabled={intakeLoading}
              aria-label="Describe your legal issue"
            />
            <button
              className={`nm-btn ${isRecording ? "nm-btn-gold" : "nm-btn-secondary"}`}
              onClick={handleSimulateVoice}
              title="Voice Input (Hindi/English)"
              disabled={intakeLoading}
              aria-label="Voice input"
            >
              <Mic size={16} aria-hidden="true" />
              <span>{isRecording ? (lang === "hi" ? "सुन रहे हैं..." : "Listening...") : (lang === "hi" ? "माइक" : "Voice")}</span>
            </button>
            <button
              className="nm-btn nm-btn-primary"
              onClick={() => handleSendMessage()}
              disabled={intakeLoading || !inputQuery.trim()}
            >
              {intakeLoading ? (
                <Loader2 size={16} className="nm-spin" aria-hidden="true" />
              ) : (
                <span>{lang === "hi" ? "भेजें" : "Send"}</span>
              )}
            </button>
          </div>
        </section>
      )}

      {/* ===================================================================== */}
      {/* WORKSPACE 2: RIGHTS & TIMELINES ("MERE ADHIKAAR")                     */}
      {/* ===================================================================== */}
      {activeTab === "rights" && (
        <section className="nm-workspace" aria-labelledby="rights-heading">
          <div className="nm-workspace-header">
            <h2 id="rights-heading">
              <Scale size={20} aria-hidden="true" />
              {lang === "hi" ? "मेरे अधिकार व समय-सीमा (Mere Adhikaar)" : "Mere Adhikaar (Rights & Timelines)"}
            </h2>
            <p>
              {lang === "hi"
                ? "कक्षा 6–8 के सरल स्तर पर समझाए गए वैधानिक अधिकार, प्रामाणिक कानूनी धाराएं एवं समय-सीमा।"
                : "Grade 6–8 plain language rights explanations grounded in active Union enactments with verified citations."}
            </p>
          </div>

          {/* Domain Selection Tabs */}
          <div className="nm-scenario-row">
            {[
              { id: "TENANCY", label: "Tenancy (किरायेदारी)", icon: <Home size={13} aria-hidden="true" /> },
              { id: "CONSUMER", label: "Consumer (उपभोक्ता)", icon: <ShoppingCart size={13} aria-hidden="true" /> },
              { id: "RTI", label: "RTI (सूचना अधिकार)", icon: <ClipboardList size={13} aria-hidden="true" /> },
              { id: "CRIMINAL", label: "Criminal (आपराधिक/एफआईआर)", icon: <AlertTriangle size={13} aria-hidden="true" /> },
            ].map((d) => (
              <button
                key={d.id}
                className={`nm-btn ${rightsDomain === d.id ? "nm-btn-primary" : "nm-btn-secondary"} nm-btn-sm`}
                onClick={() => setRightsDomain(d.id)}
              >
                {d.icon}
                <span>{d.label}</span>
              </button>
            ))}
          </div>

          {rightsLoading && (
            <div className="nm-loading-box">
              <Loader2 size={24} className="nm-spin" aria-hidden="true" />
              <p>{lang === "hi" ? "आधिकारिक धाराएं व अधिकार प्राप्त किए जा रहे हैं..." : "Querying active statutory corpus and limitation rules..."}</p>
            </div>
          )}

          {rightsError && (
            <div className="nm-alert nm-alert-danger" role="alert">
              <AlertTriangle size={16} aria-hidden="true" />
              <span>{rightsError}</span>
            </div>
          )}

          {/* Rights Data Presentation */}
          {rightsData && !rightsLoading && (
            <div className="nm-grid-2">
              <div>
                <h3 className="nm-section-title">
                  <ShieldCheck size={18} aria-hidden="true" />
                  {lang === "hi" ? "आपके मूल वैधानिक अधिकार" : "Your Statutory Rights"}
                </h3>
                <p className="nm-lead-text">{rightsData.rights_summary}</p>

                <div className="nm-feature-stack">
                  {rightsData.statutory_rights?.map((r, i) => (
                    <div key={i} className="nm-card-feature">
                      <div className="nm-feature-header">
                        <strong>{r.right_name}</strong>
                        <span className="nm-badge nm-badge-verified">{r.statutory_basis}</span>
                      </div>
                      <p className="nm-feature-body">{r.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="nm-section-title">
                  <Clock size={18} aria-hidden="true" />
                  {lang === "hi" ? "समय-सीमा व चरणबद्ध कार्यवाही" : "Action Timeline & Limitation Periods"}
                </h3>

                <div className="nm-timeline">
                  {rightsData.action_timeline?.map((st, i) => (
                    <div key={i} className="nm-timeline-step">
                      <div className="nm-timeline-dot"></div>
                      <strong>
                        Step {st.step_number}: {st.title} ({st.timeframe})
                      </strong>
                      <p>{st.action_required}</p>
                      {st.authority && <small className="nm-timeline-authority">Authority: {st.authority}</small>}
                    </div>
                  ))}
                </div>

                {rightsData.escalation_advice && (
                  <div className="nm-card-feature nm-border-gold">
                    <span className="nm-badge nm-badge-warning">
                      <Landmark size={11} aria-hidden="true" />
                      {lang === "hi" ? "सलाह" : "Next Step"}
                    </span>
                    <p className="nm-feature-body" style={{ marginTop: "0.5rem" }}>
                      {rightsData.escalation_advice}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </section>
      )}

      {/* ===================================================================== */}
      {/* WORKSPACE 3: DOCUMENT SCANNER & DEADLINE GUARDIAN                     */}
      {/* ===================================================================== */}
      {activeTab === "scanner" && (
        <section className="nm-workspace" aria-labelledby="scanner-heading">
          <div className="nm-workspace-header">
            <h2 id="scanner-heading">
              <FileText size={20} aria-hidden="true" />
              {lang === "hi" ? "नोटिस स्कैनर व तारीखें (Deadline Guardian)" : "Document Scanner & Deadline Guardian"}
            </h2>
            <p>
              {lang === "hi"
                ? "कोर्ट नोटिस, सम्मन, चेक बाउंस नोटिस या एफआईआर कॉपी का विश्लेषण करें। महत्वपूर्ण तारीखें समझें और कैलेंडर में जोड़ें।"
                : "Upload or paste court notices, summons, or legal notices to extract critical hearing dates, limitation periods, and parties."}
            </p>
          </div>

          {/* Quick Example Loaders */}
          <div className="nm-scenario-row">
            <span className="nm-scenario-label">{lang === "hi" ? "उदाहरण पाठ:" : "Notice Templates:"}</span>
            <button
              className="nm-btn nm-btn-secondary nm-btn-sm"
              onClick={() =>
                setDocInputText(
                  "IN THE COURT OF CHIEF JUDICIAL MAGISTRATE, SAKET, NEW DELHI\nCase No. CC 450/2024\nAnand Kumar ... Complainant vs Rajesh Sharma ... Accused\nSummons to appear before this Hon'ble Court on 24-10-2026 at 10:30 AM.\nParty Aadhaar: 4321 8765 1234."
                )
              }
            >
              <FileText size={13} aria-hidden="true" />
              Court Summons Notice
            </button>
            <button
              className="nm-btn nm-btn-secondary nm-btn-sm"
              onClick={() =>
                setDocInputText(
                  "STATUTORY DEMAND NOTICE UNDER SECTION 138 NEGOTIABLE INSTRUMENTS ACT\nTo: Vikram Singh, Jaipur\nCheque No. 459821 of Rs. 1,50,000/- dishonoured for Funds Insufficient.\nYou are called upon to make payment within 15 days of receipt of this notice."
                )
              }
            >
              <ClipboardList size={13} aria-hidden="true" />
              Section 138 NI Act Notice
            </button>
          </div>

          <div className="nm-grid-2">
            <div>
              <div className="nm-form-group">
                <label className="nm-form-label">
                  {lang === "hi" ? "दस्तावेज़ का पाठ यहाँ पेस्ट करें:" : "Document Text / Notice Content:"}
                </label>
                <textarea
                  className="nm-textarea"
                  rows={8}
                  placeholder={
                    lang === "hi"
                      ? "अपने कानूनी नोटिस, सम्मन या पत्र की सामग्री यहाँ पेस्ट करें..."
                      : "Paste your legal notice, court summons, FIR copy, or agreement text here for OCR and deadline extraction..."
                  }
                  value={docInputText}
                  onChange={(e) => setDocInputText(e.target.value)}
                />
              </div>

              {/* File Upload Option */}
              <div className="nm-upload-zone">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".pdf,.png,.jpg,.jpeg,.txt"
                  style={{ display: "none" }}
                />
                <button
                  type="button"
                  className="nm-btn nm-btn-secondary"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload size={15} aria-hidden="true" />
                  <span>{selectedFile ? selectedFile.name : (lang === "hi" ? "फ़ाइल चुनें (PDF/चित्र)" : "Upload Document (PDF/Image)")}</span>
                </button>
                {selectedFile && (
                  <span className="nm-file-info">
                    {(selectedFile.size / 1024).toFixed(1)} KB • {selectedFile.type || "file"}
                  </span>
                )}
              </div>

              <button
                className="nm-btn nm-btn-primary"
                style={{ width: "100%", marginTop: "1rem" }}
                onClick={handleAnalyzeDocument}
                disabled={docLoading || (!docInputText.trim() && !selectedFile)}
              >
                {docLoading ? (
                  <Loader2 size={16} className="nm-spin" aria-hidden="true" />
                ) : (
                  <Search size={16} aria-hidden="true" />
                )}
                <span>{lang === "hi" ? "दस्तावेज़ का विश्लेषण करें" : "Analyze Document via OCR & Guardian"}</span>
              </button>

              {docError && (
                <div className="nm-alert nm-alert-danger" style={{ marginTop: "1rem" }} role="alert">
                  <AlertTriangle size={16} aria-hidden="true" />
                  <span>{docError}</span>
                </div>
              )}
            </div>

            {/* Analysis Output */}
            <div>
              {docAnalysis ? (
                <div className="nm-analysis-card">
                  <div className="nm-badge-row">
                    <span className="nm-badge nm-badge-verified">
                      <CheckCircle size={12} aria-hidden="true" />
                      {docAnalysis.document_type} ({(docAnalysis.classification_confidence * 100).toFixed(0)}%)
                    </span>
                    <span className="nm-badge nm-badge-outdated">
                      <Lock size={12} aria-hidden="true" />
                      PII Protected ({docAnalysis.pii_redacted_count} masked)
                    </span>
                  </div>

                  <div className="nm-card-feature" style={{ marginTop: "1rem" }}>
                    <h4>
                      <FileCheck size={16} aria-hidden="true" />
                      {lang === "hi" ? "दस्तावेज़ सारांश" : "Plain Language Summary"}
                    </h4>
                    <p className="nm-feature-body">{docAnalysis.plain_summary}</p>
                  </div>

                  {/* Extracted Deadlines */}
                  <div className="nm-card-feature" style={{ marginTop: "1rem" }}>
                    <h4>
                      <CalendarDays size={16} aria-hidden="true" />
                      {lang === "hi" ? "निर्धारित तारीखें व समय-सीमा" : "Extracted Hearing Dates & Deadlines"}
                    </h4>
                    {userDeadlines.length > 0 ? (
                      userDeadlines.map((dl, idx) => (
                        <div key={idx} className="nm-deadline-item">
                          <div className="nm-deadline-header">
                            <strong>{dl.label}</strong>
                            <span className={`nm-badge ${dl.urgency_level === "HIGH" ? "nm-badge-critical" : "nm-badge-warning"}`}>
                              {dl.urgency_level}
                            </span>
                          </div>
                          <div className="nm-deadline-details">
                            Date/Period: <strong>{dl.value}</strong> • Basis: {dl.statutory_basis}
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="nm-feature-body" style={{ color: "var(--text-muted)", marginTop: "0.5rem" }}>
                        {lang === "hi" ? "कोई आगामी कोर्ट तारीख नहीं मिली।" : "No explicit court hearing dates detected in this text."}
                      </p>
                    )}

                    {userDeadlines.length > 0 && (
                      <button
                        className="nm-btn nm-btn-emerald nm-btn-sm"
                        style={{ marginTop: "0.75rem", width: "100%" }}
                        onClick={handleExportICS}
                      >
                        <CalendarDays size={14} aria-hidden="true" />
                        <span>{lang === "hi" ? "कैलेंडर में जोड़ें (.ics डाउनलोड)" : "Add Deadlines to Calendar (.ics)"}</span>
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="nm-empty-state">
                  <FileText size={32} style={{ opacity: 0.3 }} aria-hidden="true" />
                  <p>
                    {lang === "hi"
                      ? "दस्तावेज़ का पाठ दर्ज करें और 'विश्लेषण करें' पर क्लिक करें।"
                      : "Paste notice recitals or upload a file, then click Analyze Document."}
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* ===================================================================== */}
      {/* WORKSPACE 4: MERA DOCUMENT (CONTROLLED GENERATOR)                     */}
      {/* ===================================================================== */}
      {activeTab === "generator" && (
        <section className="nm-workspace" aria-labelledby="generator-heading">
          <div className="nm-workspace-header">
            <h2 id="generator-heading">
              <FilePen size={20} aria-hidden="true" />
              {lang === "hi" ? "मेरा डाक्यूमेंट (Mera Document)" : "Mera Document (Controlled Generator)"}
            </h2>
            <p>
              {lang === "hi"
                ? "आरटीआई, उपभोक्ता शिकायत या विधिक नोटिस का अनुमोदित प्रारूप बनाएं। सभी फ़ील्ड के निर्देशानुसार विवरण भरें।"
                : "Generate court-ready, legally structured dispute drafts (RTI, Consumer, Cheque Bounce, Tenancy) using deterministic slot filling."}
            </p>
          </div>

          {/* Template Choice */}
          <div className="nm-scenario-row">
            {[
              { id: "RTI_APPLICATION", label: "RTI Application (Sec 6(1))", icon: <ClipboardList size={13} aria-hidden="true" /> },
              { id: "CONSUMER_COMPLAINT", label: "Consumer Complaint (Sec 35)", icon: <ShoppingCart size={13} aria-hidden="true" /> },
              { id: "LEGAL_NOTICE_CHEQUE_BOUNCE", label: "Cheque Bounce Notice (Sec 138)", icon: <FileText size={13} aria-hidden="true" /> },
              { id: "RENT_DISPUTE_REPLY", label: "Rent Dispute Reply (Sec 106)", icon: <Home size={13} aria-hidden="true" /> },
            ].map((t) => (
              <button
                key={t.id}
                className={`nm-btn ${selectedTemplate === t.id ? "nm-btn-primary" : "nm-btn-secondary"} nm-btn-sm`}
                onClick={() => {
                  setSelectedTemplate(t.id);
                  setGeneratedDoc(null);
                }}
              >
                {t.icon}
                <span>{t.label}</span>
              </button>
            ))}
          </div>

          <div className="nm-grid-2">
            {/* Slot Input Form */}
            <div>
              <h3 className="nm-section-title">
                <FilePen size={18} aria-hidden="true" />
                {lang === "hi" ? "दस्तावेज़ विवरण दर्ज करें" : "Enter Required Particulars"}
              </h3>

              <div className="nm-form-group">
                <label className="nm-form-label">Applicant / Complainant Name *</label>
                <input
                  type="text"
                  className="nm-input"
                  placeholder="e.g. Enter your full name as per official government ID"
                  value={slots.applicant_name}
                  onChange={(e) => setSlots({ ...slots, applicant_name: e.target.value })}
                />
              </div>

              <div className="nm-form-group">
                <label className="nm-form-label">Applicant Postal Address *</label>
                <input
                  type="text"
                  className="nm-input"
                  placeholder="e.g. Complete communication address with District, State and PIN code"
                  value={slots.applicant_address}
                  onChange={(e) => setSlots({ ...slots, applicant_address: e.target.value })}
                />
              </div>

              <div className="nm-form-group">
                <label className="nm-form-label">Contact Number / Email</label>
                <input
                  type="text"
                  className="nm-input"
                  placeholder="e.g. 10-digit mobile number or email for dispatch notices"
                  value={slots.applicant_contact}
                  onChange={(e) => setSlots({ ...slots, applicant_contact: e.target.value })}
                />
              </div>

              <div className="nm-form-group">
                <label className="nm-form-label">Public Authority / Opposite Party *</label>
                <input
                  type="text"
                  className="nm-input"
                  placeholder="e.g. Public Information Officer, Municipal Corporation or Company Name"
                  value={slots.public_authority_name}
                  onChange={(e) => setSlots({ ...slots, public_authority_name: e.target.value })}
                />
              </div>

              <div className="nm-form-group">
                <label className="nm-form-label">Subject / Dispute Matter *</label>
                <input
                  type="text"
                  className="nm-input"
                  placeholder="e.g. Request for status of repair tender Ref #2024-PWD-89"
                  value={slots.subject_matter}
                  onChange={(e) => setSlots({ ...slots, subject_matter: e.target.value })}
                />
              </div>

              <div className="nm-form-group">
                <label className="nm-form-label">Particulars of Information / Grievance Facts *</label>
                <textarea
                  className="nm-textarea"
                  rows={4}
                  placeholder="e.g. 1. Certified copy of work sanction order\n2. Date of commencement and completion\n3. Name of supervising engineer"
                  value={slots.particulars_of_information}
                  onChange={(e) => setSlots({ ...slots, particulars_of_information: e.target.value })}
                />
              </div>

              <div className="nm-form-group">
                <label className="nm-form-label">Place of Signing *</label>
                <input
                  type="text"
                  className="nm-input"
                  placeholder="e.g. New Delhi, Bengaluru, Mumbai"
                  value={slots.place}
                  onChange={(e) => setSlots({ ...slots, place: e.target.value })}
                />
              </div>

              <button
                className="nm-btn nm-btn-emerald"
                style={{ width: "100%", marginTop: "0.5rem" }}
                onClick={handleGenerateDocument}
                disabled={genLoading}
              >
                {genLoading ? (
                  <Loader2 size={16} className="nm-spin" aria-hidden="true" />
                ) : (
                  <Settings size={16} aria-hidden="true" />
                )}
                <span>{lang === "hi" ? "वैधानिक प्रारूप तैयार करें" : "Generate Legal Draft"}</span>
              </button>

              {genError && (
                <div className="nm-alert nm-alert-danger" style={{ marginTop: "1rem" }} role="alert">
                  <AlertTriangle size={16} aria-hidden="true" />
                  <span>{genError}</span>
                </div>
              )}
            </div>

            {/* Live Draft Preview */}
            <div>
              <h3 className="nm-section-title">
                <FileText size={18} aria-hidden="true" />
                {lang === "hi" ? "तैयार विधिक प्रारूप पूर्वावलोकन" : "Deterministic Draft Preview"}
              </h3>

              {generatedDoc && generatedDoc.markdown_content ? (
                <div>
                  <div className="nm-badge-row" style={{ marginBottom: "0.75rem" }}>
                    <span className="nm-badge nm-badge-verified">
                      <CheckCircle size={11} aria-hidden="true" />
                      {generatedDoc.statutory_basis || "Tier-1 Enactment Grounding"}
                    </span>
                    {generatedDoc.sha256_hash && (
                      <span className="nm-badge nm-badge-outdated">
                        SHA256: {generatedDoc.sha256_hash.slice(0, 10)}...
                      </span>
                    )}
                  </div>

                  <pre className="nm-draft-pre">{generatedDoc.markdown_content}</pre>

                  <div className="nm-download-row">
                    <button className="nm-btn nm-btn-primary nm-btn-sm" onClick={() => handleDownloadDoc("md")}>
                      <Download size={13} aria-hidden="true" />
                      Download Markdown (.md)
                    </button>
                    <button className="nm-btn nm-btn-secondary nm-btn-sm" onClick={() => handleDownloadDoc("txt")}>
                      <Download size={13} aria-hidden="true" />
                      Download Plain Text (.txt)
                    </button>
                    <button className="nm-btn nm-btn-secondary nm-btn-sm" onClick={() => handleDownloadDoc("html")}>
                      <Download size={13} aria-hidden="true" />
                      Download Printable HTML (.html)
                    </button>
                  </div>
                </div>
              ) : (
                <div className="nm-empty-state">
                  <ArrowRight size={32} style={{ opacity: 0.3 }} aria-hidden="true" />
                  <p>
                    {lang === "hi"
                      ? "विवरण भरें और 'वैधानिक प्रारूप तैयार करें' पर क्लिक करें।"
                      : "Fill in the required particulars and click Generate Legal Draft to view the structured legal draft."}
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* ===================================================================== */}
      {/* WORKSPACE 5: NYAYA SAHAYATA (FREE LEGAL AID & ESCALATION)             */}
      {/* ===================================================================== */}
      {activeTab === "escalation" && (
        <section className="nm-workspace" aria-labelledby="escalation-heading">
          <div className="nm-workspace-header">
            <h2 id="escalation-heading">
              <Landmark size={20} aria-hidden="true" />
              {lang === "hi" ? "न्याय सहायता व हेल्पलाइन (Legal Aid & Helpline)" : "Nyaya Sahayata (Legal Aid & Escalation)"}
            </h2>
            <p>
              {lang === "hi"
                ? "धारा 12 विधिक सेवा प्राधिकरण अधिनियम 1987 के तहत 100% निःशुल्क सरकारी वकील खोजें एवं टेली-लॉ परामर्श प्राप्त करें।"
                : "Official DLSA / SLSA directory search, Section 12 LSAA 1987 eligibility verification, and Tele-Law consultation."}
            </p>
          </div>

          <div className="nm-grid-2">
            {/* Left: Jurisdiction Directory */}
            <div>
              <h3 className="nm-section-title">
                <MapPin size={18} aria-hidden="true" />
                {lang === "hi" ? "विधिक सेवा प्राधिकरण खोजें (DLSA / SLSA)" : "Locate Legal Aid Authority"}
              </h3>

              <div className="nm-form-group">
                <label className="nm-form-label">State / Union Territory:</label>
                <select
                  className="nm-select"
                  value={selectedState}
                  onChange={(e) => setSelectedState(e.target.value)}
                >
                  <option value="DELHI">Delhi (DSLSA)</option>
                  <option value="MAHARASHTRA">Maharashtra (MSLSA)</option>
                  <option value="KARNATAKA">Karnataka (KSLSA)</option>
                  <option value="UTTAR PRADESH">Uttar Pradesh (UPSLSA)</option>
                  <option value="RAJASTHAN">Rajasthan (RSLSA)</option>
                  <option value="TAMIL NADU">Tamil Nadu (TNSLSA)</option>
                  <option value="WEST BENGAL">West Bengal (WB SLSA)</option>
                </select>
              </div>

              {/* Direct Authority Card */}
              <div className="nm-card-feature nm-border-navy" style={{ marginBottom: "1rem" }}>
                <div className="nm-feature-header">
                  <h4>
                    <Landmark size={16} aria-hidden="true" />
                    {selectedState === "DELHI" ? "South DLSA (Saket Courts)" : `${selectedState} State Legal Services Authority`}
                  </h4>
                  <span className="nm-badge nm-badge-verified">Official NALSA Directory</span>
                </div>
                <p className="nm-feature-body">
                  <strong>Address:</strong>{" "}
                  {selectedState === "DELHI" ? "Saket District Court Complex, New Delhi - 110017" : "High Court Complex"}
                </p>
                <p className="nm-feature-body">
                  <strong>Helpline:</strong> 15100 (National Legal Services Authority, 24x7 Toll-Free)
                </p>

                <div className="nm-action-row" style={{ marginTop: "0.75rem" }}>
                  <a href="tel:15100" className="nm-btn nm-btn-emerald nm-btn-sm">
                    <Phone size={13} aria-hidden="true" />
                    Call 15100 (Toll-Free)
                  </a>
                  <a
                    href={`https://www.google.com/maps/search/?api=1&query=${selectedState}+Legal+Services+Authority`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="nm-btn nm-btn-secondary nm-btn-sm"
                  >
                    <MapPin size={13} aria-hidden="true" />
                    Open in Maps
                  </a>
                </div>
              </div>

              {/* Tele-Law Card */}
              <div className="nm-card-feature nm-border-emerald">
                <h4>
                  <Monitor size={16} aria-hidden="true" />
                  Tele-Law Video Consultation
                </h4>
                <p className="nm-feature-body">
                  Receive pre-litigation advice directly from panel advocates at your nearest Common Service Centre (CSC) or via mobile app.
                </p>
                <a
                  href="https://www.tele-law.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="nm-btn nm-btn-secondary nm-btn-sm"
                  style={{ marginTop: "0.5rem" }}
                >
                  <Globe size={13} aria-hidden="true" />
                  Visit Tele-Law Portal (tele-law.in)
                </a>
              </div>
            </div>

            {/* Right: Section 12 Eligibility Calculator */}
            <div>
              <h3 className="nm-section-title">
                <Scale size={18} aria-hidden="true" />
                {lang === "hi" ? "निःशुल्क कानूनी सहायता पात्रता जांच" : "Section 12 LSAA 1987 Eligibility"}
              </h3>

              <div className="nm-card-feature">
                <p style={{ fontWeight: 600, marginBottom: "0.75rem" }}>
                  {lang === "hi" ? "क्या आप इनमें से किसी श्रेणी में आते हैं?" : "Select statutory qualifying categories:"}
                </p>

                <label className="nm-checkbox-row">
                  <input
                    type="checkbox"
                    checked={eligibilityCriteria.is_woman_or_child}
                    onChange={(e) =>
                      setEligibilityCriteria({ ...eligibilityCriteria, is_woman_or_child: e.target.checked })
                    }
                  />
                  <span>Woman or Child (Section 12(c))</span>
                </label>

                <label className="nm-checkbox-row">
                  <input
                    type="checkbox"
                    checked={eligibilityCriteria.is_sc_or_st}
                    onChange={(e) =>
                      setEligibilityCriteria({ ...eligibilityCriteria, is_sc_or_st: e.target.checked })
                    }
                  />
                  <span>Scheduled Caste (SC) or Scheduled Tribe (ST) (Section 12(a))</span>
                </label>

                <label className="nm-checkbox-row">
                  <input
                    type="checkbox"
                    checked={eligibilityCriteria.is_in_custody}
                    onChange={(e) =>
                      setEligibilityCriteria({ ...eligibilityCriteria, is_in_custody: e.target.checked })
                    }
                  />
                  <span>Person in Police or Judicial Custody (Section 12(g))</span>
                </label>

                <label className="nm-checkbox-row">
                  <input
                    type="checkbox"
                    checked={eligibilityCriteria.is_disabled}
                    onChange={(e) =>
                      setEligibilityCriteria({ ...eligibilityCriteria, is_disabled: e.target.checked })
                    }
                  />
                  <span>Person with Disability (Section 12(d))</span>
                </label>

                <div className="nm-form-group" style={{ marginTop: "1rem" }}>
                  <label className="nm-form-label">
                    Annual Family Income: ₹{eligibilityCriteria.annual_income.toLocaleString("en-IN")}
                  </label>
                  <input
                    type="range"
                    min="50000"
                    max="600000"
                    step="25000"
                    value={eligibilityCriteria.annual_income}
                    onChange={(e) =>
                      setEligibilityCriteria({ ...eligibilityCriteria, annual_income: parseInt(e.target.value) })
                    }
                    style={{ width: "100%" }}
                  />
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", color: "var(--text-muted)" }}>
                    <span>₹50,000</span>
                    <span>Standard Ceiling: ₹3,00,000</span>
                    <span>₹6,00,000</span>
                  </div>
                </div>

                {/* Eligibility Result Banner */}
                {isEligible ? (
                  <div className="nm-alert nm-alert-success" style={{ marginTop: "1rem" }}>
                    <ShieldCheck size={20} style={{ flexShrink: 0 }} aria-hidden="true" />
                    <div>
                      <strong>100% Eligible for Free Legal Aid</strong>
                      <p style={{ fontSize: "0.82rem", marginTop: "0.25rem" }}>
                        You are entitled to an advocate at government expense, drafting assistance, and court fee waiver under Section 12 of the Legal Services Authorities Act, 1987.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="nm-alert nm-alert-warning" style={{ marginTop: "1rem" }}>
                    <Info size={20} style={{ flexShrink: 0 }} aria-hidden="true" />
                    <div>
                      <strong>Income above standard state ceiling</strong>
                      <p style={{ fontSize: "0.82rem", marginTop: "0.25rem" }}>
                        You may still seek nominal fee dispute resolution at Lok Adalat or pre-litigation advice via Tele-Law.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
