"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Landmark,
  ShieldCheck,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Phone,
  ArrowRight,
  FileText,
  UserCheck,
  Loader2,
  ExternalLink,
  Scale,
} from "lucide-react";
import { LanguageToggle } from "@/components/language-toggle";
import { evaluateLegalAidEligibility, checkLegalAidEligibility, type EligibilityResult } from "@/lib/api";

const STATE_INCOME_LIMITS: Record<string, number> = {
  DELHI: 300000,
  MAHARASHTRA: 300000,
  KARNATAKA: 300000,
  TAMIL_NADU: 300000,
  UTTAR_PRADESH: 150000,
  BIHAR: 150000,
  WEST_BENGAL: 150000,
  DEFAULT: 100000,
};

export default function LegalAidPage() {
  const [lang, setLang] = useState<"en" | "hi">("en");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EligibilityResult | null>(null);

  // Form State
  const [isWomanOrChild, setIsWomanOrChild] = useState(false);
  const [isScSt, setIsScSt] = useState(false);
  const [isDisabled, setIsDisabled] = useState(false);
  const [isInCustody, setIsInCustody] = useState(false);
  const [isDisasterVictim, setIsDisasterVictim] = useState(false);
  const [isIndustrialWorkman, setIsIndustrialWorkman] = useState(false);
  const [isTraffickingVictim, setIsTraffickingVictim] = useState(false);
  const [annualIncome, setAnnualIncome] = useState<number>(150000);
  const [state, setState] = useState("DELHI");
  const [district, setDistrict] = useState("");
  const [caseType, setCaseType] = useState("CIVIL");

  const handleEvaluate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await checkLegalAidEligibility({
        is_woman_or_child: isWomanOrChild,
        is_sc_st: isScSt,
        is_disabled: isDisabled,
        is_in_custody: isInCustody,
        is_disaster_victim: isDisasterVictim,
        is_industrial_workman: isIndustrialWorkman,
        is_trafficking_victim: isTraffickingVictim,
        annual_income_inr: Number(annualIncome),
        state: state,
        district: district.trim() || undefined,
        case_type: caseType,
      });
      setResult(res);
    } catch (err: unknown) {
      console.warn("Falling back to local eligibility engine", err);
      // Fallback local evaluation using official Section 12 criteria
      const localRes = evaluateLegalAidEligibility(
        {
          is_woman_or_child: isWomanOrChild,
          is_sc_st: isScSt,
          is_disabled: isDisabled,
          is_in_custody: isInCustody,
          is_disaster_victim: isDisasterVictim,
          is_industrial_workman: isIndustrialWorkman,
          is_trafficking_victim: isTraffickingVictim,
          annual_income_inr: Number(annualIncome),
          state,
          case_type: caseType,
        },
        lang
      );
      setResult(localRes);
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
              <ShieldCheck size={12} aria-hidden="true" />
              Sec 12 LSAA 1987
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <Link href="/app" className="nm-nav-link">
              {isHi ? "मुख्य ऐप (Dashboard)" : "Full App"}
            </Link>
            <Link href="/compare" className="nm-nav-link">
              {isHi ? "तुलना (Compare)" : "Compare"}
            </Link>
            <Link href="/cases" className="nm-nav-link">
              {isHi ? "ई-कोर्ट केस खोज" : "eCourts Lookup"}
            </Link>
            <LanguageToggle currentLang={lang} onLanguageChange={setLang} />
          </div>
        </div>
      </header>

      <main id="main-content" className="nm-main" role="main">
        {/* Hero Banner */}
        <section className="nm-hero-section" style={{ padding: "2.5rem 1.5rem 2rem" }}>
          <div style={{ maxWidth: "860px", margin: "0 auto", textAlign: "center" }}>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", background: "rgba(255,255,255,0.12)", padding: "4px 12px", borderRadius: "9999px", fontSize: "0.82rem", fontWeight: 600, marginBottom: "0.75rem" }}>
              <Scale size={14} style={{ color: "#86efac" }} aria-hidden="true" />
              <span>{isHi ? "100% निःशुल्क विधिक सहायता पात्रता जांच" : "100% Free Legal Aid Guided Eligibility Interview"}</span>
            </div>
            <h1 className="nm-hero-title-main" style={{ fontSize: "2.2rem", marginBottom: "0.75rem" }}>
              {isHi ? "विधिक सेवा प्राधिकरण अधिनियम (धारा 12) के तहत मुफ्त वकील" : "Free Legal Representation under Section 12, Legal Services Authorities Act, 1987"}
            </h1>
            <p style={{ color: "rgba(255,255,255,0.88)", fontSize: "1rem", maxWidth: "680px", margin: "0 auto" }}>
              {isHi
                ? "जांचें कि क्या आप डीएलएसए/एसएलएसए (DLSA/SLSA) के माध्यम से बिना किसी शुल्क के सरकारी अधिवक्ता व कानूनी सहायता के हकदार हैं।"
                : "Verify your statutory eligibility for 100% free legal counsel, court fee waivers, and drafting support funded by the Government of India."}
            </p>
          </div>
        </section>

        {/* Guided Interview Form */}
        <div className="nm-workspace-container" style={{ maxWidth: "1050px", margin: "2rem auto", padding: "0 1rem" }}>
          <div className="nm-grid-2" style={{ gap: "2rem", alignItems: "start" }}>
            {/* Form Column */}
            <div className="nm-card" style={{ padding: "1.75rem" }}>
              <h2 className="nm-section-title" style={{ marginBottom: "1.25rem" }}>
                <UserCheck size={20} aria-hidden="true" />
                {isHi ? "चरण 1: पात्रता प्रश्नोत्तरी" : "Step 1: Section 12 Eligibility Assessment"}
              </h2>

              <form onSubmit={handleEvaluate}>
                {/* Special Category Checkboxes */}
                <div style={{ marginBottom: "1.5rem" }}>
                  <label className="nm-form-label" style={{ fontWeight: 700, marginBottom: "0.75rem" }}>
                    {isHi ? "विशेष वैधानिक श्रेणियां (लागू होने पर चुनें):" : "Statutory Priority Categories (Select any that apply):"}
                  </label>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "0.6rem" }}>
                    {[
                      { id: "woman-child", checked: isWomanOrChild, set: setIsWomanOrChild, label: isHi ? "महिला अथवा 18 वर्ष से कम आयु का बच्चा [धारा 12(c)]" : "Woman or Child under 18 years [Sec 12(c)]" },
                      { id: "sc-st", checked: isScSt, set: setIsScSt, label: isHi ? "अनुसूचित जाति / अनुसूचित जनजाति (SC / ST) [धारा 12(a)]" : "Member of Scheduled Caste or Scheduled Tribe (SC/ST) [Sec 12(a)]" },
                      { id: "disabled", checked: isDisabled, set: setIsDisabled, label: isHi ? "दिव्यांगजन / विशेष रूप से सक्षम व्यक्ति [धारा 12(b)]" : "Person with Disabilities (PwD) [Sec 12(b)]" },
                      { id: "custody", checked: isInCustody, set: setIsInCustody, label: isHi ? "न्यायिक अथवा पुलिस हिरासत / कारागार में [धारा 12(g)]" : "Person in Judicial or Police Custody / Prison [Sec 12(g)]" },
                      { id: "disaster", checked: isDisasterVictim, set: setIsDisasterVictim, label: isHi ? "प्राकृतिक आपदा, दंगा या जातीय हिंसा पीड़ित [धारा 12(e)]" : "Victim of Mass Disaster, Violence, Flood or Drought [Sec 12(e)]" },
                      { id: "industrial", checked: isIndustrialWorkman, set: setIsIndustrialWorkman, label: isHi ? "औद्योगिक कर्मकार (Industrial Workman) [धारा 12(f)]" : "Industrial Workman [Sec 12(f)]" },
                      { id: "trafficking", checked: isTraffickingVictim, set: setIsTraffickingVictim, label: isHi ? "मानव तस्करी अथवा बेगार पीड़ित [धारा 12(d)]" : "Victim of Human Trafficking or Begar [Sec 12(d)]" },
                    ].map((item) => (
                      <label
                        key={item.id}
                        htmlFor={item.id}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "0.6rem",
                          background: item.checked ? "var(--emerald-light, #ecfdf5)" : "var(--neutral-subtle, #f8fafc)",
                          border: `1px solid ${item.checked ? "var(--emerald-green, #059669)" : "var(--border-color, #e2e8f0)"}`,
                          padding: "0.6rem 0.85rem",
                          borderRadius: "8px",
                          cursor: "pointer",
                          fontSize: "0.88rem",
                          transition: "all 0.15s ease",
                        }}
                      >
                        <input
                          id={item.id}
                          type="checkbox"
                          checked={item.checked}
                          onChange={(e) => item.set(e.target.checked)}
                          style={{ width: "16px", height: "16px", accentColor: "var(--emerald-green, #059669)" }}
                        />
                        <span>{item.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* State & Income */}
                <div className="nm-grid-2" style={{ gap: "1rem", marginBottom: "1.25rem" }}>
                  <div className="nm-form-group">
                    <label className="nm-form-label" htmlFor="state-select">
                      {isHi ? "राज्य (State):" : "State Jurisdiction:"}
                    </label>
                    <select
                      id="state-select"
                      className="nm-input"
                      value={state}
                      onChange={(e) => setState(e.target.value)}
                    >
                      <option value="DELHI">Delhi (₹3,00,000 limit)</option>
                      <option value="MAHARASHTRA">Maharashtra (₹3,00,000 limit)</option>
                      <option value="KARNATAKA">Karnataka (₹3,00,000 limit)</option>
                      <option value="TAMIL_NADU">Tamil Nadu (₹3,00,000 limit)</option>
                      <option value="UTTAR_PRADESH">Uttar Pradesh (₹1,50,000 limit)</option>
                      <option value="BIHAR">Bihar (₹1,50,000 limit)</option>
                      <option value="WEST_BENGAL">West Bengal (₹1,50,000 limit)</option>
                      <option value="DEFAULT">Other States (₹1,00,000 limit)</option>
                    </select>
                  </div>

                  <div className="nm-form-group">
                    <label className="nm-form-label" htmlFor="annual-income">
                      {isHi ? "वार्षिक पारिवारिक आय (₹):" : "Annual Household Income (₹):"}
                    </label>
                    <input
                      id="annual-income"
                      type="number"
                      className="nm-input"
                      value={annualIncome}
                      onChange={(e) => setAnnualIncome(Number(e.target.value))}
                      placeholder="e.g. 150000"
                      min={0}
                      step={5000}
                      required
                    />
                  </div>
                </div>

                {/* District and Case Type */}
                <div className="nm-grid-2" style={{ gap: "1rem", marginBottom: "1.5rem" }}>
                  <div className="nm-form-group">
                    <label className="nm-form-label" htmlFor="district-input">
                      {isHi ? "ज़िला / क्षेत्र (वैकल्पिक):" : "District (Optional):"}
                    </label>
                    <input
                      id="district-input"
                      type="text"
                      className="nm-input"
                      value={district}
                      onChange={(e) => setDistrict(e.target.value)}
                      placeholder="e.g. Saket, Pune, Bengaluru Urban"
                    />
                  </div>

                  <div className="nm-form-group">
                    <label className="nm-form-label" htmlFor="case-type">
                      {isHi ? "विवाद का प्रकार:" : "Case Nature:"}
                    </label>
                    <select
                      id="case-type"
                      className="nm-input"
                      value={caseType}
                      onChange={(e) => setCaseType(e.target.value)}
                    >
                      <option value="CIVIL">Civil / Property / Family / Tenancy</option>
                      <option value="CRIMINAL">Criminal / Bail / Police FIR</option>
                      <option value="CONSUMER">Consumer / RTI / Labour Grievance</option>
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  className="nm-btn nm-btn-emerald"
                  style={{ width: "100%", padding: "0.85rem", fontSize: "1rem", fontWeight: 700 }}
                  disabled={loading}
                >
                  {loading ? <Loader2 size={18} className="nm-spin" aria-hidden="true" /> : <Scale size={18} aria-hidden="true" />}
                  <span>{isHi ? "पात्रता सत्यापित करें" : "Evaluate Statutory Eligibility"}</span>
                </button>
              </form>
            </div>

            {/* Results Column */}
            <div>
              {result ? (
                <div
                  className="nm-card"
                  style={{
                    padding: "1.75rem",
                    borderLeft: `5px solid ${result.is_eligible ? "var(--emerald-green, #059669)" : "var(--warning-amber, #d97706)"}`,
                  }}
                  role="region"
                  aria-live="polite"
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
                    {result.is_eligible ? (
                      <CheckCircle size={28} style={{ color: "var(--emerald-green, #059669)" }} aria-hidden="true" />
                    ) : (
                      <AlertTriangle size={28} style={{ color: "var(--warning-amber, #d97706)" }} aria-hidden="true" />
                    )}
                    <div>
                      <h3 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 800 }}>
                        {result.is_eligible
                          ? (isHi ? "बधाई! आप 100% निःशुल्क कानूनी सहायता के पात्र हैं" : "Eligible for 100% Free Legal Aid")
                          : (isHi ? "आय सीमा से अधिक — विशेष राहत विकल्प उपलब्ध" : "Income Exceeds Standard Free Legal Aid Limit")}
                      </h3>
                      <p style={{ margin: "2px 0 0", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                        {result.statutory_ground || (result.is_eligible ? "Section 12, Legal Services Authorities Act, 1987" : "Section 12(h) Threshold")}
                      </p>
                    </div>
                  </div>

                  <div className="nm-card" style={{ background: "var(--neutral-subtle, #f8fafc)", padding: "1rem", marginBottom: "1rem", fontSize: "0.9rem" }}>
                    <strong>{isHi ? "पात्रता निष्कर्ष:" : "Evaluation Summary:"}</strong>
                    <p style={{ marginTop: "0.35rem", marginBottom: 0 }}>
                      {result.reason || result.explanation || (result.is_eligible ? "You qualify for free state-appointed counsel and zero court fees." : "Your income exceeds the ceiling for standard free legal aid.")}
                    </p>
                  </div>

                  <h4 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "0.75rem" }}>
                    {isHi ? "अगले कदम और आधिकारिक सहायता केंद्र:" : "Next Steps & Escalation Channels:"}
                  </h4>

                  <ul style={{ paddingLeft: "1.2rem", fontSize: "0.88rem", lineHeight: 1.6, marginBottom: "1.25rem" }}>
                    <li><strong>NALSA National Helpline:</strong> Dial <a href="tel:15100" style={{ color: "var(--emerald-green, #059669)", fontWeight: 700 }}>15100</a> (Toll-Free, 24x7).</li>
                    <li><strong>District Legal Services Authority (DLSA):</strong> Visit the Saket / Tis Hazari / Pune DLSA office with your identity proof.</li>
                    <li><strong>Tele-Law Portal:</strong> Free pre-litigation video consultation via CSC centers across India.</li>
                  </ul>

                  <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                    <a
                      href="https://nalsa.gov.in"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="nm-btn nm-btn-primary nm-btn-sm"
                    >
                      <ExternalLink size={14} aria-hidden="true" />
                      <span>{isHi ? "NALSA पोर्टल पर आवेदन करें" : "Apply on NALSA Portal"}</span>
                    </a>
                    <Link href="/app?tab=generator" className="nm-btn nm-btn-secondary nm-btn-sm">
                      <FileText size={14} aria-hidden="true" />
                      <span>{isHi ? "विधिक नोटिस प्रारूप तैयार करें" : "Draft Legal Notice"}</span>
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="nm-card" style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
                  <Landmark size={42} style={{ color: "var(--accent-gold, #c59b27)", margin: "0 auto 1rem" }} aria-hidden="true" />
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.5rem" }}>
                    {isHi ? "पात्रता परिणाम यहाँ प्रदर्शित होंगे" : "Eligibility Assessment Awaiting Input"}
                  </h3>
                  <p style={{ fontSize: "0.88rem", maxWidth: "380px", margin: "0 auto" }}>
                    {isHi
                      ? "बाईं ओर अपनी श्रेणियां व आय विवरण दर्ज करें और 'पात्रता सत्यापित करें' बटन दबाएं।"
                      : "Complete the questions on the left to verify statutory entitlement under Section 12 of the LSAA 1987."}
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
