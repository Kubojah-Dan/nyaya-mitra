"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Landmark,
  Search,
  CheckCircle,
  AlertTriangle,
  ExternalLink,
  Shield,
  Loader2,
  Calendar,
  Building,
  FileText,
  HelpCircle,
} from "lucide-react";
import { LanguageToggle } from "@/components/language-toggle";
import { lookupECourtsCNR, type ECourtsCNRResult } from "@/lib/api";

const SAMPLE_CNRS = [
  { cnr: "DLCT010012342024", label: "Delhi District Court (2024)" },
  { cnr: "MHPK020056782023", label: "Maharashtra District Court (2023)" },
  { cnr: "KABC030090122022", label: "Karnataka District Court (2022)" },
  { cnr: "DTHC010045672024", label: "Delhi High Court (2024)" },
];

export default function CasesPage() {
  const [lang, setLang] = useState<"en" | "hi">("en");
  const [cnrInput, setCnrInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ECourtsCNRResult | null>(null);

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cnrInput.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const data = await lookupECourtsCNR(cnrInput.trim());
      setResult(data);
    } catch (err: unknown) {
      console.error(err);
      setError(
        lang === "hi"
          ? "सीएनआर संख्या का सत्यापन करने में असमर्थ। कृपया 16-अंकीय प्रारूप जांचें।"
          : "Unable to verify CNR number. Please ensure valid 16-character format (e.g. DLCT010012342024)."
      );
    } finally {
      setLoading(false);
    }
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
              <Landmark size={12} aria-hidden="true" />
              eCourts Services (Tier-1)
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
              {isHi ? "मुफ्त विधिक सहायता" : "Free Legal Aid"}
            </Link>
            <LanguageToggle currentLang={lang} onLanguageChange={setLang} />
          </div>
        </div>
      </header>

      <main id="main-content" className="nm-main" role="main">
        {/* Hero Section */}
        <section className="nm-hero-section" style={{ padding: "2.5rem 1.5rem 2rem" }}>
          <div style={{ maxWidth: "860px", margin: "0 auto", textAlign: "center" }}>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", background: "rgba(255,255,255,0.12)", padding: "4px 12px", borderRadius: "9999px", fontSize: "0.82rem", fontWeight: 600, marginBottom: "0.75rem" }}>
              <Shield size={14} style={{ color: "#86efac" }} aria-hidden="true" />
              <span>{isHi ? "आधिकारिक ई-कोर्ट सीएनआर ट्रैकिंग गाइड" : "Official eCourts Services CNR Case Tracker"}</span>
            </div>
            <h1 className="nm-hero-title-main" style={{ fontSize: "2.2rem", marginBottom: "0.75rem" }}>
              {isHi ? "16-अंकीय सीएनआर (CNR) से अदालती केस व स्थिति खोजें" : "Track District & High Court Cases using 16-Character CNR"}
            </h1>
            <p style={{ color: "rgba(255,255,255,0.88)", fontSize: "1rem", maxWidth: "680px", margin: "0 auto" }}>
              {isHi
                ? "भारत के किसी भी ज़िला या उच्च न्यायालय के केस की आधिकारिक स्थिति, अगली सुनवाई तिथि और आदेश देखें।"
                : "Instantly resolve CNR jurisdiction, court complex code, and filing year with direct official routing to services.ecourts.gov.in."}
            </p>
          </div>
        </section>

        {/* Workspace Search */}
        <div className="nm-workspace-container" style={{ maxWidth: "980px", margin: "2rem auto", padding: "0 1rem" }}>
          <div className="nm-card" style={{ padding: "2rem", marginBottom: "2rem" }}>
            <form onSubmit={handleLookup}>
              <label htmlFor="cnr-input" className="nm-form-label" style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "0.5rem" }}>
                {isHi ? "16-अंकीय सीएनआर संख्या दर्ज करें (Enter 16-character CNR):" : "Enter 16-Character Case Number Record (CNR):"}
              </label>

              <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginBottom: "1rem" }}>
                <input
                  id="cnr-input"
                  type="text"
                  className="nm-input"
                  style={{ flex: "1 1 320px", fontSize: "1.1rem", fontFamily: "monospace", letterSpacing: "1px", textTransform: "uppercase" }}
                  placeholder="e.g. DLCT010012342024"
                  maxLength={16}
                  value={cnrInput}
                  onChange={(e) => setCnrInput(e.target.value.toUpperCase())}
                  required
                />
                <button
                  type="submit"
                  className="nm-btn nm-btn-primary"
                  style={{ padding: "0.75rem 1.5rem", fontSize: "1rem" }}
                  disabled={loading}
                >
                  {loading ? <Loader2 size={18} className="nm-spin" aria-hidden="true" /> : <Search size={18} aria-hidden="true" />}
                  <span>{isHi ? "केस खोजें" : "Lookup Case"}</span>
                </button>
              </div>

              {/* Sample CNR Chips */}
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                <span>{isHi ? "नमूना सीएनआर (क्लिक करें):" : "Try sample CNR:"}</span>
                {SAMPLE_CNRS.map((s) => (
                  <button
                    key={s.cnr}
                    type="button"
                    onClick={() => setCnrInput(s.cnr)}
                    style={{
                      background: "var(--neutral-subtle, #f1f5f9)",
                      border: "1px solid var(--border-color, #e2e8f0)",
                      borderRadius: "6px",
                      padding: "2px 8px",
                      fontSize: "0.8rem",
                      cursor: "pointer",
                      fontFamily: "monospace",
                    }}
                  >
                    {s.cnr}
                  </button>
                ))}
              </div>
            </form>

            {error && (
              <div className="nm-alert nm-alert-danger" style={{ marginTop: "1.25rem" }} role="alert">
                <AlertTriangle size={16} aria-hidden="true" />
                <span>{error}</span>
              </div>
            )}
          </div>

          {/* Results Box */}
          {result && (
            <div className="nm-card" style={{ padding: "2rem" }} role="region" aria-live="polite">
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem", borderBottom: "1px solid var(--border-color, #e2e8f0)", paddingBottom: "1rem", marginBottom: "1.5rem" }}>
                <div>
                  <span className="nm-badge nm-badge-verified" style={{ marginBottom: "0.5rem", display: "inline-flex" }}>
                    <CheckCircle size={12} aria-hidden="true" />
                    {isHi ? "सत्यापित सीएनआर संरचना" : "Validated CNR Structure"}
                  </span>
                  <h2 style={{ margin: 0, fontFamily: "monospace", fontSize: "1.6rem", color: "var(--primary-navy)" }}>
                    {result.cnr}
                  </h2>
                </div>

                <a
                  href={result.direct_lookup_url || result.official_portal || "https://services.ecourts.gov.in"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="nm-btn nm-btn-emerald"
                  style={{ fontSize: "0.95rem" }}
                >
                  <ExternalLink size={16} aria-hidden="true" />
                  <span>{isHi ? "आधिकारिक ई-कोर्ट्स पर स्थिति देखें" : "View Live on eCourts Portal"}</span>
                </a>
              </div>

              <div className="nm-grid-2" style={{ gap: "1.25rem", marginBottom: "1.5rem" }}>
                <div style={{ background: "var(--neutral-subtle, #f8fafc)", padding: "1.25rem", borderRadius: "8px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
                    <Building size={15} aria-hidden="true" />
                    <span>{isHi ? "राज्य / क्षेत्राधिकार" : "State Jurisdiction"}</span>
                  </div>
                  <strong style={{ fontSize: "1.1rem", color: "var(--text-main)" }}>
                    {result.state_name} ({result.state_code})
                  </strong>
                </div>

                <div style={{ background: "var(--neutral-subtle, #f8fafc)", padding: "1.25rem", borderRadius: "8px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
                    <Landmark size={15} aria-hidden="true" />
                    <span>{isHi ? "अदालत का स्तर" : "Court Level"}</span>
                  </div>
                  <strong style={{ fontSize: "1.1rem", color: "var(--text-main)" }}>
                    {result.court_level || "District Court"}
                  </strong>
                </div>

                <div style={{ background: "var(--neutral-subtle, #f8fafc)", padding: "1.25rem", borderRadius: "8px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
                    <FileText size={15} aria-hidden="true" />
                    <span>{isHi ? "केस अनुक्रम संख्या" : "Case Sequential Number"}</span>
                  </div>
                  <strong style={{ fontSize: "1.1rem", color: "var(--text-main)" }}>
                    {result.case_number}
                  </strong>
                </div>

                <div style={{ background: "var(--neutral-subtle, #f8fafc)", padding: "1.25rem", borderRadius: "8px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
                    <Calendar size={15} aria-hidden="true" />
                    <span>{isHi ? "दायर करने का वर्ष" : "Filing Year"}</span>
                  </div>
                  <strong style={{ fontSize: "1.1rem", color: "var(--text-main)" }}>
                    {result.year}
                  </strong>
                </div>
              </div>

              <div style={{ background: "#fef9ee", border: "1px solid #fde68a", padding: "1rem 1.25rem", borderRadius: "8px", fontSize: "0.88rem", color: "#92400e" }}>
                <strong>{isHi ? "प्रक्रियात्मक निर्देश (Procedural Guidelines):" : "Official Procedure Guidelines:"}</strong>
                <p style={{ marginTop: "0.4rem", marginBottom: 0, lineHeight: 1.5 }}>
                  {result.instructions ||
                    "1. Click the 'View Live on eCourts Portal' button above.\n2. Complete the CAPTCHA verification on services.ecourts.gov.in.\n3. View current case stage, next listing date, judge name, and download signed interim/final orders."}
                </p>
              </div>
            </div>
          )}

          {/* Explanatory Info Card */}
          <div className="nm-card" style={{ marginTop: "2rem", padding: "1.5rem" }}>
            <h3 style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "1.05rem", fontWeight: 700, margin: "0 0 0.75rem" }}>
              <HelpCircle size={18} style={{ color: "var(--primary-navy)" }} aria-hidden="true" />
              <span>{isHi ? "सीएनआर संख्या क्या है?" : "What is a CNR Number?"}</span>
            </h3>
            <p style={{ fontSize: "0.88rem", color: "var(--text-body)", lineHeight: 1.6, margin: 0 }}>
              {isHi
                ? "सीएनआर (Case Number Record) भारत के ई-कोर्ट्स प्रोजेक्ट के तहत प्रत्येक केस को दिया जाने वाला 16-अंकीय विशिष्ट पहचान कोड है। यह राज्य कोड (2 अक्षर), ज़िला/न्यायालय कोड (2 अक्षर), स्थापना कोड (2 अंक), केस संख्या (6 अंक) और वर्ष (4 अंक) से मिलकर बनता है।"
                : "CNR (Case Number Record) is the unique 16-character alphanumeric code assigned to every case filed in Indian District and High Courts under the Supreme Court e-Committee initiative. It uniquely tracks the case across its entire judicial lifecycle regardless of transfers or appeals."}
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
