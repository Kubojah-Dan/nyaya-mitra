"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  MessageSquare,
  Scale,
  FileText,
  FilePen,
  Landmark,
  Globe,
  GitCompare,
  Compass,
  Shield,
  CheckCircle,
  ArrowRight,
  Users,
  BookOpen,
  Mic,
  Zap,
  Lock,
  ChevronDown,
  Star,
  Phone,
  Gavel,
  BarChart3,
} from "lucide-react";

type Language = "en" | "hi";

export default function LandingPage() {
  const [lang, setLang] = useState<Language>("en");
  const [statsVisible, setStatsVisible] = useState(false);
  const [activeFeature, setActiveFeature] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setStatsVisible(true), 600);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveFeature((prev) => (prev + 1) % 3);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const isHi = lang === "hi";

  const modules = [
    {
      href: "/app?tab=intake",
      icon: "MessageSquare",
      color: "var(--primary-navy)",
      gradFrom: "#0f2942",
      gradTo: "#1e3a5f",
      title: isHi ? "1. समझो मेरा प्रॉब्लम" : "1. Understand",
      subtitle: isHi ? "Guided Intake" : "Guided Legal Intake",
      desc: isHi
        ? "अपनी कानूनी समस्या सरल भाषा में बताएं। AI कानूनी श्रेणी पहचानेगा।"
        : "Describe your legal problem in plain words — Hindi or English. AI identifies the legal domain and applicable statutes in real time.",
      badge: "AI Powered",
      iconEl: <MessageSquare size={28} aria-hidden="true" />,
    },
    {
      href: "/compare",
      icon: "GitCompare",
      color: "#1d4ed8",
      gradFrom: "#1d4ed8",
      gradTo: "#1e40af",
      title: isHi ? "2. दस्तावेज़ तुलना" : "2. Compare",
      subtitle: isHi ? "Document Diff" : "Document Comparison",
      desc: isHi
        ? "दो कानूनी दस्तावेज़ों की धारावार तुलना करें — जोड़े गए, हटाए गए और बदले गए खंड स्वतः पहचानें।"
        : "Upload two legal documents and get a section-by-section diff with added, removed, and modified clauses highlighted with statutory citations.",
      badge: "Side-by-Side Diff",
      iconEl: <GitCompare size={28} aria-hidden="true" />,
    },
    {
      href: "/navigate",
      icon: "Compass",
      color: "#059669",
      gradFrom: "#059669",
      gradTo: "#047857",
      title: isHi ? "3. दस्तावेज़ नेविगेट" : "3. Navigate",
      subtitle: isHi ? "Document Outline" : "Document Navigation",
      desc: isHi
        ? "किसी भी लंबे कानूनी दस्तावेज़ की संरचित रूपरेखा बनाएं और सीधे किसी भी धारा पर जाएं।"
        : "Generate a structured table-of-contents for any long legal document and jump directly to any section with smart anchor navigation.",
      badge: "AI Outline",
      iconEl: <Compass size={28} aria-hidden="true" />,
    },
    {
      href: "/app?tab=scanner",
      icon: "FileText",
      color: "#d97706",
      gradFrom: "#d97706",
      gradTo: "#b45309",
      title: isHi ? "4. नोटिस स्कैनर" : "4. Scanner",
      subtitle: isHi ? "Deadline Guardian" : "Notice & Deadline Guardian",
      desc: isHi
        ? "कोर्ट नोटिस, सम्मन या चेक बाउंस नोटिस का विश्लेषण करें। समय-सीमाएं निकालें।"
        : "Paste or upload a court summons, legal notice, or FIR copy. Extract parties, hearing dates, and limitation periods — export to calendar.",
      badge: "OCR + Deadlines",
      iconEl: <FileText size={28} aria-hidden="true" />,
    },
    {
      href: "/app?tab=generator",
      icon: "FilePen",
      color: "#7c3aed",
      gradFrom: "#7c3aed",
      gradTo: "#6d28d9",
      title: isHi ? "5. मेरा डाक्यूमेंट" : "5. Draft",
      subtitle: isHi ? "Legal Document Generator" : "Controlled Document Generator",
      desc: isHi
        ? "आरटीआई, उपभोक्ता शिकायत, किरायेदारी विवाद उत्तर — कोर्ट-रेडी प्रारूप बनाएं।"
        : "Generate court-ready RTI applications, consumer complaints, cheque bounce notices, and rent dispute replies using deterministic slot filling.",
      badge: "Slot-fill Drafting",
      iconEl: <FilePen size={28} aria-hidden="true" />,
    },
    {
      href: "/app?tab=escalation",
      icon: "Landmark",
      color: "#dc2626",
      gradFrom: "#dc2626",
      gradTo: "#b91c1c",
      title: isHi ? "6. निःशुल्क सहायता" : "6. Free Legal Aid",
      subtitle: isHi ? "NALSA / DLSA Escalation" : "NALSA / DLSA Directory",
      desc: isHi
        ? "धारा 12 विधिक सेवा प्राधिकरण अधिनियम के तहत निःशुल्क सरकारी वकील की पात्रता जांचें।"
        : "Verify Section 12 LSAA 1987 eligibility and locate your nearest DLSA / SLSA for 100% free government advocate assignment.",
      badge: "100% Free",
      iconEl: <Landmark size={28} aria-hidden="true" />,
    },
  ];

  const heroFeatures = [
    isHi ? "अपनी कानूनी समस्या समझें" : "Understand your legal problem",
    isHi ? "दो दस्तावेज़ों की तुलना करें" : "Compare two legal documents",
    isHi ? "लंबे कानूनों में नेविगेट करें" : "Navigate complex legal documents",
  ];

  const stats = [
    { value: "6+", label: isHi ? "कानूनी डोमेन" : "Legal Domains" },
    { value: "4", label: isHi ? "दस्तावेज़ प्रकार" : "Document Templates" },
    { value: "100%", label: isHi ? "वैधानिक आधार" : "Statutory-Grounded" },
    { value: "15100", label: isHi ? "NALSA हेल्पलाइन" : "NALSA Helpline" },
  ];

  const trustSignals = [
    { text: isHi ? "BNS/BNSS/BSA 2024 — आधिकारिक भारत कोड" : "BNS / BNSS / BSA 2024 — Official India Code" },
    { text: isHi ? "RTI अधिनियम 2005 एवं उपभोक्ता संरक्षण अधिनियम 2019" : "RTI Act 2005 & Consumer Protection Act 2019" },
    { text: isHi ? "ई-कोर्ट्स eCourts & eSewa सेवाएं" : "eCourts & eSewa Official Services" },
    { text: isHi ? "PII सुरक्षित — शून्य डेटा प्रतिधारण" : "PII-Redacted — Zero Data Retention" },
    { text: isHi ? "बहु-मॉडल AI (Primary + Fallback)" : "Multi-Model AI (Primary + Fallback Tier)" },
    { text: isHi ? "हिंदी एवं अंग्रेज़ी आवाज़ इनपुट" : "Hindi & English Voice Input" },
  ];

  return (
    <div className="nm-landing-page">
      {/* HERO */}
      <section className="nm-hero-section" aria-labelledby="landing-hero-heading">
        <div className="nm-hero-bg-pattern" aria-hidden="true" />
        <div className="nm-container-wide">
          <div className="nm-hero-layout">
            <div className="nm-hero-text">
              <div className="nm-hero-eyebrow">
                <Shield size={15} aria-hidden="true" />
                <span>PromptWars 2026 &middot; AI for Legal Assistance &amp; Access</span>
              </div>

              <h2 id="landing-hero-heading" className="nm-hero-h1">
                {isHi ? (
                  <span lang="hi">
                    कानूनी दस्तावेज़ों को{" "}
                    <span className="nm-hero-highlight">समझें, तुलना करें</span>
                    {" "}और{" "}
                    <span className="nm-hero-highlight">नेविगेट करें</span>
                  </span>
                ) : (
                  <>
                    <span className="nm-hero-highlight">Understand</span>,{" "}
                    <span className="nm-hero-highlight">Compare</span> &amp;{" "}
                    <span className="nm-hero-highlight">Navigate</span>{" "}
                    Indian Legal Documents
                  </>
                )}
              </h2>

              <p className="nm-hero-desc">
                {isHi
                  ? "न्यायमित्र — भारतीय नागरिकों के लिए AI-संचालित कानूनी सहायता। BNS/BNSS/BSA 2024 आधारित, शून्य मतिभ्रम, NALSA 15100 एकीकृत।"
                  : "NyayaMitra — AI-powered legal empowerment grounded strictly in current Indian law (BNS/BNSS/BSA 2024), Tier-1 statutory enactments, and NALSA 15100 free legal aid. Zero hallucinations."}
              </p>

              <div className="nm-hero-ticker" aria-live="polite" aria-atomic="true">
                <span className="nm-hero-ticker-label">{isHi ? "अभी करें:" : "Now:"}</span>
                <span className="nm-hero-ticker-text">{heroFeatures[activeFeature]}</span>
              </div>

              <div className="nm-hero-ctas">
                <Link href="/app" className="nm-btn nm-btn-primary nm-btn-lg" id="hero-cta-primary">
                  <MessageSquare size={20} aria-hidden="true" />
                  <span>{isHi ? "कानूनी सहायता शुरू करें" : "Start Legal Assistance"}</span>
                  <ArrowRight size={18} aria-hidden="true" />
                </Link>
                <Link href="/compare" className="nm-btn nm-btn-white nm-btn-lg" id="hero-cta-compare">
                  <GitCompare size={20} aria-hidden="true" />
                  <span>{isHi ? "दस्तावेज़ तुलना" : "Compare Documents"}</span>
                </Link>
              </div>

              <div className="nm-hero-trust">
                <span><CheckCircle size={14} aria-hidden="true" /> {isHi ? "सरकारी कानून आधारित" : "Govt. Law Grounded"}</span>
                <span><CheckCircle size={14} aria-hidden="true" /> {isHi ? "निःशुल्क उपयोग" : "Free to Use"}</span>
                <span><CheckCircle size={14} aria-hidden="true" /> {isHi ? "डेटा सुरक्षित" : "PII Protected"}</span>
              </div>
            </div>

            <div className="nm-hero-visual" aria-hidden="true">
              <div className="nm-hero-visual-card nm-hero-card-main">
                <div className="nm-hero-vc-header">
                  <MessageSquare size={18} />
                  <span>NyayaMitra AI</span>
                  <span className="nm-live-dot" />
                </div>
                <div className="nm-hero-vc-body">
                  <div className="nm-hero-chat-line user">मकान मालिक ने बिना नोटिस के निकाला</div>
                  <div className="nm-hero-chat-line ai">
                    <strong>Domain: TENANCY</strong> &middot; TP Act &sect;106 &mdash; 15-day written notice required under BNSS 2024 &sect;125...
                  </div>
                  <div className="nm-hero-chat-line badge-row">
                    <span className="nm-mini-badge green">&#10003; BNS 2024</span>
                    <span className="nm-mini-badge blue">&sect; TP Act</span>
                    <span className="nm-mini-badge amber">&#9888; Urgent</span>
                  </div>
                </div>
              </div>
              <div className="nm-hero-visual-card nm-hero-card-secondary">
                <div className="nm-hero-vc-header">
                  <GitCompare size={18} />
                  <span>Document Compare</span>
                </div>
                <div className="nm-compare-preview">
                  <div className="nm-cp-col">
                    <div className="nm-cp-label">Version A</div>
                    <div className="nm-cp-line removed">Section 12: Rent &#8377;15,000</div>
                    <div className="nm-cp-line">Section 13: Deposit &#8377;45,000</div>
                  </div>
                  <div className="nm-cp-divider" />
                  <div className="nm-cp-col">
                    <div className="nm-cp-label">Version B</div>
                    <div className="nm-cp-line added">Section 12: Rent &#8377;18,500</div>
                    <div className="nm-cp-line">Section 13: Deposit &#8377;55,500</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="nm-scroll-hint" aria-label="Scroll to explore features">
            <ChevronDown size={20} aria-hidden="true" />
            <span>{isHi ? "और जानें" : "Explore Features"}</span>
          </div>
        </div>
      </section>

      {/* STATS STRIP */}
      <section className="nm-stats-strip" aria-label="NyayaMitra Platform Statistics">
        <div className="nm-container-wide">
          <div className="nm-stats-grid">
            {stats.map((s, i) => (
              <div key={i} className={`nm-stat-item ${statsVisible ? "nm-stat-visible" : ""}`} style={{ transitionDelay: `${i * 0.12}s` }}>
                <span className="nm-stat-value">{s.value}</span>
                <span className="nm-stat-label">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SIX MODULES GRID */}
      <section className="nm-modules-section" aria-labelledby="modules-heading">
        <div className="nm-container-wide">
          <div className="nm-section-header">
            <span className="nm-section-eyebrow">
              <BarChart3 size={15} aria-hidden="true" />
              {isHi ? "छः शक्तिशाली मॉड्यूल" : "Six Powerful Modules"}
            </span>
            <h2 id="modules-heading" className="nm-section-title-lg">
              {isHi ? "हर नागरिक की कानूनी ज़रूरत के लिए" : "Everything you need for legal empowerment"}
            </h2>
            <p className="nm-section-desc">
              {isHi
                ? "समझें, तुलना करें, नेविगेट करें — तीन मूल क्षमताएं जो पूर्ण न्याय सहायता प्रदान करती हैं।"
                : "Understand, Compare, Navigate — the three core verbs, fully implemented with three additional power modules."}
            </p>
          </div>
          <div className="nm-modules-grid">
            {modules.map((mod, i) => (
              <Link key={i} href={mod.href} className="nm-module-card" aria-label={`${mod.title}: ${mod.subtitle}`}>
                <div className="nm-module-icon-wrap" style={{ background: `linear-gradient(135deg, ${mod.gradFrom} 0%, ${mod.gradTo} 100%)` }}>
                  {mod.iconEl}
                </div>
                <span className="nm-module-badge">{mod.badge}</span>
                <h3 className="nm-module-title">{mod.title}</h3>
                <p className="nm-module-subtitle">{mod.subtitle}</p>
                <p className="nm-module-desc">{mod.desc}</p>
                <span className="nm-module-cta">
                  {isHi ? "उपयोग करें" : "Get Started"} <ArrowRight size={14} aria-hidden="true" />
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="nm-how-section" aria-labelledby="how-heading">
        <div className="nm-container-wide">
          <div className="nm-section-header">
            <span className="nm-section-eyebrow">
              <Zap size={15} aria-hidden="true" />
              {isHi ? "यह कैसे काम करता है" : "How It Works"}
            </span>
            <h2 id="how-heading" className="nm-section-title-lg">
              {isHi ? "तीन आसान चरण" : "Three Simple Steps"}
            </h2>
          </div>
          <div className="nm-steps-grid">
            {[
              {
                n: "1",
                title: isHi ? "समस्या बताएं" : "Describe Your Problem",
                desc: isHi ? "हिंदी या अंग्रेज़ी में — टेक्स्ट या आवाज़ से। AI कानूनी श्रेणी और लागू कानून पहचानेगा।" : "Type or speak in Hindi or English. Our AI identifies the legal domain, applicable statutes, and urgency level.",
                iconEl: <MessageSquare size={28} aria-hidden="true" />,
              },
              {
                n: "2",
                title: isHi ? "AI विश्लेषण प्राप्त करें" : "Get AI Analysis",
                desc: isHi ? "BNS/BNSS/BSA 2024 आधारित अधिकार, समय-सीमाएं, और दस्तावेज़ तुलना।" : "Receive statutory rights explanations, document diffs, outline navigation, and deadline extraction — all grounded in Tier-1 law.",
                iconEl: <Scale size={28} aria-hidden="true" />,
              },
              {
                n: "3",
                title: isHi ? "कार्रवाई करें" : "Take Action",
                desc: isHi ? "प्रारूप डाउनलोड करें, NALSA से संपर्क करें, कैलेंडर में जोड़ें।" : "Download a court-ready draft, connect with your nearest DLSA, or export deadlines to your calendar.",
                iconEl: <CheckCircle size={28} aria-hidden="true" />,
              },
            ].map((step, i) => (
              <div key={i} className="nm-step-card">
                <div className="nm-step-number">{step.n}</div>
                <div className="nm-step-icon">{step.iconEl}</div>
                <h3>{step.title}</h3>
                <p>{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TRUST & SOURCES */}
      <section className="nm-trust-section" aria-labelledby="trust-heading">
        <div className="nm-container-wide">
          <div className="nm-trust-inner">
            <div>
              <span className="nm-section-eyebrow">
                <Shield size={15} aria-hidden="true" />
                {isHi ? "विश्वसनीयता" : "Trust & Sources"}
              </span>
              <h2 id="trust-heading" className="nm-section-title-lg">
                {isHi ? "100% वैधानिक आधार" : "100% Statutory-Grounded"}
              </h2>
              <p className="nm-section-desc">
                {isHi ? "सभी उत्तर केवल सरकारी अधिनियमों और आधिकारिक स्रोतों पर आधारित हैं।" : "Every answer is sourced exclusively from official Indian government enactments, with zero AI hallucination."}
              </p>
              <div className="nm-trust-signals">
                {trustSignals.map((t, i) => (
                  <div key={i} className="nm-trust-item">
                    <CheckCircle size={16} aria-hidden="true" />
                    <span>{t.text}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="nm-source-cards">
              {[
                { name: "India Code", url: "https://www.indiacode.nic.in", desc: "Central Legislation" },
                { name: "eCourts", url: "https://services.ecourts.gov.in", desc: "Case Status & Orders" },
                { name: "NALSA", url: "https://nalsa.gov.in", desc: "Legal Aid Authority" },
                { name: "e-Daakhil", url: "https://edaakhil.nic.in", desc: "Consumer Forum" },
              ].map((src, i) => (
                <a key={i} href={src.url} target="_blank" rel="noopener noreferrer" className="nm-source-card">
                  <Star size={14} aria-hidden="true" />
                  <div>
                    <strong>{src.name}</strong>
                    <span>{src.desc}</span>
                  </div>
                  <ArrowRight size={14} aria-hidden="true" />
                </a>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="nm-cta-banner" aria-labelledby="cta-heading">
        <div className="nm-container-wide">
          <div className="nm-cta-inner">
            <div className="nm-cta-text">
              <Users size={36} aria-hidden="true" />
              <div>
                <h2 id="cta-heading">{isHi ? "न्याय तक पहुंच — हर भारतीय का अधिकार" : "Justice Access — Every Indian's Right"}</h2>
                <p>{isHi ? "NALSA 15100 — 24x7 निःशुल्क टोल-फ्री कानूनी सहायता। अभी शुरू करें।" : "NALSA 15100 — 24x7 toll-free free legal aid for every eligible citizen under Sec 12 LSAA 1987."}</p>
              </div>
            </div>
            <div className="nm-cta-actions">
              <Link href="/app" className="nm-btn nm-btn-white nm-btn-lg" id="cta-start-btn">
                <MessageSquare size={18} aria-hidden="true" />
                {isHi ? "अभी शुरू करें" : "Start Now — Free"}
              </Link>
              <a href="tel:15100" className="nm-btn nm-btn-outline-white nm-btn-lg" id="cta-nalsa-btn">
                <Phone size={18} aria-hidden="true" />
                Call NALSA 15100
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Language Toggle FAB */}
      <button
        className="nm-lang-fab"
        onClick={() => setLang(lang === "en" ? "hi" : "en")}
        aria-label={isHi ? "Switch to English" : "हिंदी में बदलें"}
      >
        <Globe size={18} aria-hidden="true" />
        <span>{isHi ? "EN" : "हि"}</span>
      </button>
    </div>
  );
}
