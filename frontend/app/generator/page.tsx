"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FilePen,
  FileText,
  ClipboardList,
  ShoppingCart,
  Home,
  CheckCircle,
  AlertTriangle,
  Download,
  Settings,
  Loader2,
  Shield,
  Copy,
  Info,
} from "lucide-react";
import { LanguageToggle } from "@/components/language-toggle";
import { generateDocument, type GenerateDocumentResponse } from "@/lib/api";

const TEMPLATES = [
  {
    id: "RTI_APPLICATION",
    title: "RTI Application (सूचना का अधिकार)",
    act: "Right to Information Act, 2005 (Section 6(1))",
    icon: ClipboardList,
    fields: [
      { key: "applicant_name", label: "Applicant Name *", placeholder: "e.g. Rajesh Kumar" },
      { key: "applicant_address", label: "Postal Address *", placeholder: "e.g. Flat 402, Green Park, New Delhi - 110016" },
      { key: "applicant_contact", label: "Contact Phone / Email", placeholder: "e.g. +91 9876543210" },
      { key: "public_authority_name", label: "Public Authority (PIO) *", placeholder: "e.g. Central Public Information Officer, MCD" },
      { key: "subject_matter", label: "Subject of Information *", placeholder: "e.g. Tender allocation records for PWD Road Works" },
      { key: "place", label: "Place of Application *", placeholder: "e.g. New Delhi" },
    ],
  },
  {
    id: "CONSUMER_COMPLAINT",
    title: "Consumer Complaint (उपभोक्ता शिकायत)",
    act: "Consumer Protection Act, 2019 (Section 35)",
    icon: ShoppingCart,
    fields: [
      { key: "complainant_name", label: "Complainant Name *", placeholder: "e.g. Sunita Devi" },
      { key: "complainant_address", label: "Complainant Address *", placeholder: "e.g. 12, MG Road, Saket, New Delhi" },
      { key: "complainant_phone", label: "Phone Number", placeholder: "e.g. +91 9811223344" },
      { key: "opposite_party_name", label: "Opposite Party (Vendor/Company) *", placeholder: "e.g. QuickElectro Retail Pvt Ltd" },
      { key: "opposite_party_address", label: "Vendor Address *", placeholder: "e.g. Cyber City, Gurugram, Haryana" },
      { key: "product_or_service_description", label: "Product / Service Defect *", placeholder: "e.g. Defective 55-inch Smart TV with blank screen" },
      { key: "transaction_date", label: "Date of Transaction (DD-MM-YYYY) *", placeholder: "e.g. 15-08-2024" },
      { key: "total_amount_paid", label: "Total Amount Paid (₹) *", placeholder: "e.g. 45000" },
      { key: "relief_sought", label: "Relief / Compensation Claimed *", placeholder: "e.g. Full refund of ₹45,000 with 12% interest and ₹10,000 compensation" },
      { key: "commission_district", label: "District Commission Name *", placeholder: "e.g. Saket District Commission, New Delhi" },
    ],
  },
  {
    id: "LEGAL_NOTICE_CHEQUE_BOUNCE",
    title: "Cheque Bounce Notice (चेक बाउंस नोटिस)",
    act: "Negotiable Instruments Act, 1881 (Section 138)",
    icon: FileText,
    fields: [
      { key: "payee_name", label: "Payee (Creditor / Sender) *", placeholder: "e.g. Amit Sharma" },
      { key: "payee_address", label: "Payee Address *", placeholder: "e.g. B-12, Sector 62, Noida, UP" },
      { key: "drawer_name", label: "Drawer (Debtor / Signatory) *", placeholder: "e.g. Vijay Verma" },
      { key: "drawer_address", label: "Drawer Address *", placeholder: "e.g. 45, Rajouri Garden, New Delhi" },
      { key: "cheque_number", label: "Cheque Number *", placeholder: "e.g. 004521" },
      { key: "cheque_date", label: "Cheque Date (DD-MM-YYYY) *", placeholder: "e.g. 10-09-2024" },
      { key: "cheque_amount", label: "Cheque Amount (₹) *", placeholder: "e.g. 150000" },
      { key: "bank_name", label: "Bank Name & Branch *", placeholder: "e.g. State Bank of India, Saket Branch" },
      { key: "bounce_memo_date", label: "Bank Memo Date (DD-MM-YYYY) *", placeholder: "e.g. 15-09-2024" },
      { key: "bounce_reason", label: "Reason for Return *", placeholder: "e.g. Funds Insufficient" },
    ],
  },
  {
    id: "RENT_DISPUTE_REPLY",
    title: "Tenancy Notice Reply (किराया विवाद उत्तर)",
    act: "Transfer of Property Act, 1882 (Section 106)",
    icon: Home,
    fields: [
      { key: "tenant_name", label: "Tenant Name *", placeholder: "e.g. Priya Nair" },
      { key: "tenant_address", label: "Rented Premises Address *", placeholder: "e.g. House No. 88, 2nd Floor, Indiranagar, Bengaluru" },
      { key: "landlord_name", label: "Landlord Name *", placeholder: "e.g. Suresh Hegde" },
      { key: "landlord_address", label: "Landlord Address *", placeholder: "e.g. 14, 1st Cross, Bengaluru" },
      { key: "notice_date", label: "Date of Landlord's Notice *", placeholder: "e.g. 01-09-2024" },
      { key: "dispute_details", label: "Grounds of Defense / Disputed Facts *", placeholder: "e.g. All monthly rent paid up to date; illegal demand for rent hike without notice" },
      { key: "deposit_amount", label: "Security Deposit Held (₹) *", placeholder: "e.g. 60000" },
    ],
  },
];

export default function GeneratorStandalonePage() {
  const [lang, setLang] = useState<"en" | "hi">("en");
  const [selectedId, setSelectedId] = useState("RTI_APPLICATION");
  const [slots, setSlots] = useState<Record<string, string>>({
    particulars_of_information: "1. Certified copy of tender award\n2. Date of completion\n3. Inspection report",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedDoc, setGeneratedDoc] = useState<GenerateDocumentResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const currentTemplate = TEMPLATES.find((t) => t.id === selectedId) || TEMPLATES[0];

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await generateDocument({
        template_id: selectedId,
        slots: slots,
      });
      setGeneratedDoc(res);
    } catch (err: unknown) {
      console.error(err);
      setError(
        lang === "hi"
          ? "दस्तावेज़ तैयार करने में त्रुटि। कृपया सभी आवश्यक फ़ील्ड भरें।"
          : "Failed to generate document. Please ensure all mandatory fields are filled."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (format: "md" | "txt") => {
    if (!generatedDoc?.markdown_content) return;
    const blob = new Blob([generatedDoc.markdown_content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selectedId.toLowerCase()}_draft.${format}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleCopy = () => {
    if (!generatedDoc?.markdown_content) return;
    navigator.clipboard.writeText(generatedDoc.markdown_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const isHi = lang === "hi";

  return (
    <div className="nm-page-container">
      {/* Top Header */}
      <header className="nm-header" role="banner">
        <div className="nm-header-inner">
          <div className="nm-logo-group">
            <Link href="/" className="nm-logo-link">
              <span className="nm-logo-icon">⚖️</span>
              <span className="nm-logo-text">NyayaMitra</span>
            </Link>
            <span className="nm-badge nm-badge-verified">
              <FilePen size={12} aria-hidden="true" />
              Controlled Drafting Engine
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <Link href="/app" className="nm-nav-link">
              {isHi ? "मुख्य ऐप" : "Dashboard"}
            </Link>
            <Link href="/compare" className="nm-nav-link">
              {isHi ? "तुलना" : "Compare"}
            </Link>
            <Link href="/legal-aid" className="nm-nav-link">
              {isHi ? "मुफ्त विधिक सहायता" : "Legal Aid"}
            </Link>
            <Link href="/cases" className="nm-nav-link">
              {isHi ? "ई-कोर्ट्स" : "eCourts"}
            </Link>
            <LanguageToggle currentLang={lang} onLanguageChange={setLang} />
          </div>
        </div>
      </header>

      <main id="main-content" className="nm-main" role="main">
        {/* Hero */}
        <section className="nm-hero-section" style={{ padding: "2.5rem 1.5rem 2rem" }}>
          <div style={{ maxWidth: "860px", margin: "0 auto", textAlign: "center" }}>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", background: "rgba(255,255,255,0.12)", padding: "4px 12px", borderRadius: "9999px", fontSize: "0.82rem", fontWeight: 600, marginBottom: "0.75rem" }}>
              <Shield size={14} style={{ color: "#86efac" }} aria-hidden="true" />
              <span>{isHi ? "वैधानिक टेम्पलेट प्रारूप जनरेटर" : "Deterministic Statutory Legal Draft Generator"}</span>
            </div>
            <h1 className="nm-hero-title-main" style={{ fontSize: "2.2rem", marginBottom: "0.75rem" }}>
              {isHi ? "अदालती व वैधानिक नोटिस का सटीक प्रारूप तैयार करें" : "Court-Ready Legal Notice & Dispute Drafting"}
            </h1>
            <p style={{ color: "rgba(255,255,255,0.88)", fontSize: "1rem", maxWidth: "680px", margin: "0 auto" }}>
              {isHi
                ? "आरटीआई आवेदन, उपभोक्ता शिकायत, चेक बाउंस नोटिस या किरायेदारी प्रत्युत्तर का आधिकारिक प्रारूप बिना किसी त्रुटि के बनाएं।"
                : "Zero hallucination legal drafts grounded directly in Indian Acts (RTI Act 2005, CPA 2019, NI Act 1881, TP Act 1882)."}
            </p>
          </div>
        </section>

        {/* Template Selector Row */}
        <div className="nm-workspace-container" style={{ maxWidth: "1100px", margin: "2rem auto", padding: "0 1rem" }}>
          <div className="nm-scenario-row" style={{ marginBottom: "1.5rem", display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            {TEMPLATES.map((t) => {
              const Icon = t.icon;
              const isSelected = selectedId === t.id;
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => {
                    setSelectedId(t.id);
                    setGeneratedDoc(null);
                  }}
                  className={`nm-btn ${isSelected ? "nm-btn-primary" : "nm-btn-secondary"}`}
                  style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", fontSize: "0.88rem" }}
                  aria-pressed={isSelected}
                >
                  <Icon size={16} aria-hidden="true" />
                  <span>{t.title}</span>
                </button>
              );
            })}
          </div>

          <div className="nm-grid-2" style={{ gap: "2rem", alignItems: "start" }}>
            {/* Form Box */}
            <div className="nm-card" style={{ padding: "1.75rem" }}>
              <div style={{ borderBottom: "1px solid var(--border-color, #e2e8f0)", paddingBottom: "0.75rem", marginBottom: "1.25rem" }}>
                <span className="nm-badge nm-badge-verified" style={{ marginBottom: "0.35rem", display: "inline-flex" }}>
                  <CheckCircle size={12} aria-hidden="true" />
                  {currentTemplate.act}
                </span>
                <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700 }}>
                  {isHi ? "दस्तावेज़ विवरण दर्ज करें" : "Enter Required Particulars"}
                </h2>
              </div>

              <form onSubmit={handleGenerate}>
                {currentTemplate.fields.map((f) => (
                  <div key={f.key} className="nm-form-group" style={{ marginBottom: "0.85rem" }}>
                    <label htmlFor={`field-${f.key}`} className="nm-form-label" style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                      {f.label}
                    </label>
                    <input
                      id={`field-${f.key}`}
                      type="text"
                      className="nm-input"
                      placeholder={f.placeholder}
                      value={slots[f.key] || ""}
                      onChange={(e) => setSlots({ ...slots, [f.key]: e.target.value })}
                      required={f.label.includes("*")}
                    />
                  </div>
                ))}

                <button
                  type="submit"
                  className="nm-btn nm-btn-emerald"
                  style={{ width: "100%", marginTop: "1rem", padding: "0.85rem", fontSize: "1rem", fontWeight: 700 }}
                  disabled={loading}
                >
                  {loading ? <Loader2 size={18} className="nm-spin" aria-hidden="true" /> : <Settings size={18} aria-hidden="true" />}
                  <span>{isHi ? "वैधानिक प्रारूप तैयार करें" : "Generate Legal Draft"}</span>
                </button>
              </form>

              {error && (
                <div className="nm-alert nm-alert-danger" style={{ marginTop: "1rem" }} role="alert">
                  <AlertTriangle size={16} aria-hidden="true" />
                  <span>{error}</span>
                </div>
              )}
            </div>

            {/* Preview Box */}
            <div className="nm-card" style={{ padding: "1.75rem" }} role="region" aria-live="polite">
              <h2 style={{ margin: "0 0 1rem", fontSize: "1.2rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <FileText size={18} aria-hidden="true" />
                <span>{isHi ? "प्रारूप पूर्वावलोकन" : "Draft Preview"}</span>
              </h2>

              {generatedDoc && generatedDoc.markdown_content ? (
                <div>
                  <div className="nm-badge-row" style={{ marginBottom: "0.75rem" }}>
                    <span className="nm-badge nm-badge-verified">
                      <CheckCircle size={11} aria-hidden="true" />
                      {generatedDoc.statutory_basis || currentTemplate.act}
                    </span>
                    {generatedDoc.sha256_hash && (
                      <span className="nm-badge nm-badge-outdated">SHA256: {generatedDoc.sha256_hash.slice(0, 10)}...</span>
                    )}
                  </div>

                  <pre className="nm-draft-pre" style={{ maxHeight: "380px", overflowY: "auto", fontSize: "0.82rem", background: "#f8fafc", padding: "1rem", border: "1px solid #e2e8f0", borderRadius: "8px" }}>
                    {generatedDoc.markdown_content}
                  </pre>

                  {/* Prominent Legal Advice Caveat Banner */}
                  <div
                    style={{
                      background: "#fffbeb",
                      border: "1px solid #fde68a",
                      borderRadius: "8px",
                      padding: "0.85rem 1rem",
                      margin: "1rem 0",
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "0.75rem",
                      fontSize: "0.84rem",
                      color: "#92400e",
                    }}
                    role="note"
                    aria-label="Statutory Disclaimer"
                  >
                    <Info size={20} style={{ flexShrink: 0, marginTop: "2px", color: "#d97706" }} aria-hidden="true" />
                    <div>
                      <strong>
                        {isHi
                          ? "महत्वपूर्ण वैधानिक सूचना (यह कानूनी सलाह का विकल्प नहीं है):"
                          : "Important Statutory Disclaimer (Not Legal Advice):"}
                      </strong>
                      <p style={{ margin: "3px 0 0", lineHeight: 1.45 }}>
                        {isHi
                          ? "यह कंप्यूटर-जनरेटेड प्रारंभिक प्रारूप केवल आपकी सुविधा के लिए है। इसे कोर्ट या प्राधिकारी के समक्ष प्रस्तुत करने से पहले किसी पंजीकृत अधिवक्ता अथवा डीएलएसए (DLSA) पैनल वकील से सत्यापित अवश्य कराएं।"
                          : "This generated draft is a starting structural template and does not constitute formal legal counsel. Always have it reviewed and verified by a licensed advocate or DLSA legal aid counsel before signature or filing."}
                      </p>
                    </div>
                  </div>

                  {/* Actions Row */}
                  <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                    <button className="nm-btn nm-btn-primary nm-btn-sm" onClick={() => handleDownload("md")}>
                      <Download size={14} aria-hidden="true" />
                      <span>Download .md</span>
                    </button>
                    <button className="nm-btn nm-btn-secondary nm-btn-sm" onClick={() => handleDownload("txt")}>
                      <Download size={14} aria-hidden="true" />
                      <span>Download .txt</span>
                    </button>
                    <button className="nm-btn nm-btn-secondary nm-btn-sm" onClick={handleCopy}>
                      <Copy size={14} aria-hidden="true" />
                      <span>{copied ? (isHi ? "कॉपी हो गया!" : "Copied!") : (isHi ? "कॉपी करें" : "Copy Draft")}</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: "3rem 1rem", color: "var(--text-muted)" }}>
                  <FilePen size={44} style={{ margin: "0 auto 0.75rem", color: "var(--accent-gold, #c59b27)" }} aria-hidden="true" />
                  <h3 style={{ margin: "0 0 0.35rem", fontSize: "1.05rem", fontWeight: 700, color: "var(--text-main)" }}>
                    {isHi ? "प्रारूप तैयार करने के लिए फ़ॉर्म भरें" : "Draft Preview Awaiting Generation"}
                  </h3>
                  <p style={{ fontSize: "0.85rem", maxWidth: "340px", margin: "0 auto" }}>
                    {isHi
                      ? "बाईं ओर आवश्यक विवरण दर्ज करें और 'वैधानिक प्रारूप तैयार करें' पर क्लिक करें।"
                      : "Fill in the required party particulars on the left to deterministically render a verified draft."}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
