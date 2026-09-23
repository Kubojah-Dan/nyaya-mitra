"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Compass,
  ArrowLeft,
  FileText,
  ChevronRight,
  ChevronDown,
  Loader2,
  AlertTriangle,
  Globe,
  List,
  BookOpen,
  Hash,
} from "lucide-react";
import { getDocumentOutline, OutlineSection } from "@/lib/api";

type Language = "en" | "hi";

const EXAMPLE_LEGAL_TEXT = `THE BHARATIYA NYAYA SANHITA, 2023

CHAPTER I — PRELIMINARY

Section 1. Short title, commencement and application.
(1) This Sanhita may be called the Bharatiya Nyaya Sanhita, 2023.
(2) It shall come into force on such date as the Central Government may, by notification in the Official Gazette, appoint.
(3) It extends to the whole of India except the State of Jammu and Kashmir.

Section 2. Definitions.
In this Sanhita, unless the context otherwise requires,—
(1) "act" denotes as well a series of acts as a single act;
(2) "animal" denotes any living creature, other than a human being;
(3) "document" means any matter expressed or described upon any substance by means of letters, figures or marks.

CHAPTER II — GENERAL EXCEPTIONS

Section 15. Act of a person of unsound mind.
Nothing is an offence which is done by a person who, at the time of doing it, by reason of unsoundness of mind, is incapable of knowing the nature of the act, or that he is doing what is either wrong or contrary to law.

Section 16. Act of a child above seven and under twelve.
Nothing is an offence which is done by a child above seven years of age and under twelve, who has not attained sufficient maturity of understanding to judge of the nature and consequences of his conduct on that occasion.

CHAPTER III — PUNISHMENTS

Section 4. Punishments.
The punishments to which offenders are liable under the provisions of this Sanhita are—
(a) Death;
(b) Imprisonment for life;
(c) Imprisonment, which is of two descriptions, namely:
  (i) rigorous, that is, with hard labour;
  (ii) simple;
(d) Forfeiture of property;
(e) Fine;
(f) Community Service.

Section 5. Commutation of sentence.
The appropriate Government may, without the consent of the offender, commute any punishment under this Sanhita.

CHAPTER IV — OFFENCES AGAINST THE STATE

Section 147. Waging war against the Government of India.
Whoever wages war against the Government of India, or attempts to wage such war, or abets the waging of such war, shall be punished with death, or imprisonment for life and shall also be liable to fine.`;

interface SectionTreeProps {
  sections: OutlineSection[];
  depth?: number;
  onJump: (id: string, heading: string) => void;
  activeId: string | null;
}

function SectionTree({ sections, depth = 0, onJump, activeId }: SectionTreeProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const toggle = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <ul className="nm-outline-tree" style={{ paddingLeft: depth > 0 ? "1.25rem" : "0" }}>
      {sections.map((sec) => {
        const hasChildren = sec.children && sec.children.length > 0;
        const isExpanded = expanded[sec.section_id];
        const isActive = activeId === sec.section_id;

        return (
          <li key={sec.section_id} className={`nm-outline-node ${isActive ? "nm-outline-active" : ""}`}>
            <div className="nm-outline-node-row">
              {hasChildren && (
                <button
                  className="nm-outline-expand-btn"
                  onClick={() => toggle(sec.section_id)}
                  aria-label={isExpanded ? "Collapse section" : "Expand section"}
                  aria-expanded={isExpanded}
                >
                  {isExpanded ? <ChevronDown size={14} aria-hidden="true" /> : <ChevronRight size={14} aria-hidden="true" />}
                </button>
              )}
              {!hasChildren && <span className="nm-outline-leaf-indent" />}
              <button
                className="nm-outline-heading-btn"
                onClick={() => onJump(sec.section_id, sec.heading)}
                aria-label={`Jump to section: ${sec.heading}`}
              >
                <Hash size={12} aria-hidden="true" />
                <span className="nm-outline-heading">{sec.heading}</span>
                {sec.level === 1 && <span className="nm-outline-level-badge">Chapter</span>}
              </button>
            </div>
            {sec.summary && isActive && (
              <p className="nm-outline-summary">{sec.summary}</p>
            )}
            {hasChildren && isExpanded && (
              <SectionTree sections={sec.children} depth={depth + 1} onJump={onJump} activeId={activeId} />
            )}
          </li>
        );
      })}
    </ul>
  );
}

export default function NavigatePage() {
  const [lang, setLang] = useState<Language>("en");
  const [docText, setDocText] = useState<string>("");
  const [docTitle, setDocTitle] = useState<string>("");
  const [outline, setOutline] = useState<Awaited<ReturnType<typeof getDocumentOutline>> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [activeContent, setActiveContent] = useState<OutlineSection | null>(null);

  const isHi = lang === "hi";

  const loadExample = () => {
    setDocText(EXAMPLE_LEGAL_TEXT);
    setDocTitle("Bharatiya Nyaya Sanhita, 2023 (BNS)");
    setOutline(null);
    setError(null);
    setActiveSection(null);
    setActiveContent(null);
  };

  const handleGenerateOutline = async () => {
    if (!docText.trim()) {
      setError(isHi ? "कृपया दस्तावेज़ का पाठ दर्ज करें।" : "Please enter document text to generate outline.");
      return;
    }
    setLoading(true);
    setError(null);
    setOutline(null);
    setActiveSection(null);
    setActiveContent(null);
    try {
      const res = await getDocumentOutline({
        raw_text: docText,
        title: docTitle || "Legal Document",
      });
      setOutline(res);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Outline generation failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const findSection = (sections: OutlineSection[], id: string): OutlineSection | null => {
    for (const sec of sections) {
      if (sec.section_id === id) return sec;
      if (sec.children) {
        const found = findSection(sec.children, id);
        if (found) return found;
      }
    }
    return null;
  };

  const handleJump = (id: string, heading: string) => {
    setActiveSection(id);
    if (outline) {
      const sec = findSection(outline.sections, id);
      if (sec) setActiveContent(sec);
    }

    // Highlight text in document
    const start = docText.indexOf(heading);
    if (start !== -1) {
      const textArea = document.getElementById("navigate-textarea") as HTMLTextAreaElement;
      if (textArea) {
        textArea.focus();
        textArea.setSelectionRange(start, start + heading.length);
        textArea.scrollTop = textArea.scrollHeight * (start / docText.length);
      }
    }
  };

  const extractSectionText = (sec: OutlineSection) => {
    if (!sec) return "";
    return docText.slice(sec.start_char, sec.end_char);
  };

  return (
    <div className="nm-container">
      {/* Page Header */}
      <div className="nm-page-header">
        <Link href="/" className="nm-back-link">
          <ArrowLeft size={16} aria-hidden="true" />
          <span>{isHi ? "होम पर वापस" : "Back to Home"}</span>
        </Link>
        <div className="nm-page-title-row">
          <div className="nm-page-icon-wrap" style={{ background: "linear-gradient(135deg, #059669 0%, #047857 100%)" }}>
            <Compass size={24} aria-hidden="true" />
          </div>
          <div>
            <h2 id="navigate-page-heading" className="nm-page-h1">
              {isHi ? "दस्तावेज़ नेविगेशन (Document Navigate)" : "Document Navigation — AI-Powered Outline"}
            </h2>
            <p className="nm-page-desc">
              {isHi
                ? "किसी भी लंबे कानूनी दस्तावेज़ की संरचित रूपरेखा बनाएं और सीधे किसी भी धारा पर जाएं।"
                : "Paste any lengthy legal document — an Act, court order, or agreement — and instantly generate a structured table of contents with section summaries. Click any heading to jump directly to it."}
            </p>
          </div>
          <button className="nm-btn-lang" onClick={() => setLang(isHi ? "en" : "hi")} aria-label="Toggle language">
            <Globe size={15} aria-hidden="true" />
            {isHi ? "English" : "हिंदी"}
          </button>
        </div>
      </div>

      {/* Example Loader */}
      <div className="nm-scenario-row" style={{ marginBottom: "1.25rem" }}>
        <span className="nm-scenario-label">{isHi ? "उदाहरण:" : "Try Example:"}</span>
        <button className="nm-btn nm-btn-secondary nm-btn-sm" onClick={loadExample} id="navigate-load-example">
          <BookOpen size={14} aria-hidden="true" />
          {isHi ? "भारतीय न्याय संहिता 2023 (BNS)" : "Bharatiya Nyaya Sanhita 2023 (BNS)"}
        </button>
      </div>

      {/* Input Section */}
      <div className="nm-navigate-input-section">
        <div className="nm-form-group">
          <label className="nm-form-label" htmlFor="navigate-title">{isHi ? "दस्तावेज़ का शीर्षक:" : "Document Title:"}</label>
          <input
            id="navigate-title"
            type="text"
            className="nm-input"
            placeholder={isHi ? "उदा. भारतीय न्याय संहिता 2023, किरायेदारी अनुबंध, शपथपत्र..." : "e.g. Bharatiya Nyaya Sanhita 2023, Lease Agreement, Affidavit..."}
            value={docTitle}
            onChange={(e) => setDocTitle(e.target.value)}
          />
        </div>
        <div className="nm-form-group">
          <label className="nm-form-label" htmlFor="navigate-textarea">
            {isHi ? "दस्तावेज़ का पाठ (पेस्ट करें):" : "Document Text (Paste Here):"}
          </label>
          <textarea
            id="navigate-textarea"
            className="nm-textarea nm-navigate-textarea"
            rows={12}
            placeholder={isHi ? "कोई भी लंबा कानूनी दस्तावेज़ यहाँ पेस्ट करें — अधिनियम, न्यायालय आदेश, अनुबंध, शपथपत्र..." : "Paste any long legal document here — Acts, court orders, contracts, agreements, FIRs, or affidavits. The AI will generate a structured outline with chapter and section headings."}
            value={docText}
            onChange={(e) => setDocText(e.target.value)}
          />
        </div>
        <button
          className="nm-btn nm-btn-primary"
          style={{ padding: "0.85rem 2rem", fontSize: "0.95rem", borderRadius: "9999px" }}
          onClick={handleGenerateOutline}
          disabled={loading || !docText.trim()}
          id="navigate-generate-btn"
        >
          {loading ? <Loader2 size={18} className="nm-spin" aria-hidden="true" /> : <List size={18} aria-hidden="true" />}
          <span>{loading ? (isHi ? "रूपरेखा बन रही है..." : "Generating Outline...") : (isHi ? "दस्तावेज़ रूपरेखा बनाएं" : "Generate Document Outline")}</span>
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="nm-alert nm-alert-danger" role="alert">
          <AlertTriangle size={16} aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {/* Outline Results */}
      {outline && (
        <div className="nm-navigate-results">
          <div className="nm-navigate-outline-header">
            <h3>
              <List size={18} aria-hidden="true" />
              {isHi ? "दस्तावेज़ रूपरेखा" : "Document Outline"} — {outline.title}
            </h3>
            <span className="nm-badge nm-badge-verified">
              <FileText size={11} aria-hidden="true" />
              {outline.total_sections} {isHi ? "खंड" : "Sections"}
            </span>
          </div>

          <div className="nm-navigate-layout">
            {/* Left: Outline Tree */}
            <div className="nm-navigate-sidebar">
              <p className="nm-navigate-sidebar-hint">
                {isHi ? "किसी भी शीर्षक पर क्लिक करें:" : "Click any heading to navigate:"}
              </p>
              <nav aria-label="Document outline navigation">
                <SectionTree
                  sections={outline.sections}
                  onJump={handleJump}
                  activeId={activeSection}
                />
              </nav>
            </div>

            {/* Right: Section Content */}
            <div className="nm-navigate-content">
              {activeContent ? (
                <div className="nm-navigate-section-view">
                  <div className="nm-navigate-section-header">
                    <h4>{activeContent.heading}</h4>
                    <div className="nm-badge-row">
                      <span className="nm-badge nm-badge-verified">Level {activeContent.level}</span>
                      {activeContent.children && activeContent.children.length > 0 && (
                        <span className="nm-badge nm-badge-outlined">{activeContent.children.length} sub-sections</span>
                      )}
                    </div>
                  </div>
                  {activeContent.summary && (
                    <div className="nm-card-feature" style={{ marginBottom: "1rem" }}>
                      <p className="nm-feature-body"><strong>{isHi ? "AI सारांश:" : "AI Summary:"}</strong> {activeContent.summary}</p>
                    </div>
                  )}
                  <div className="nm-navigate-section-text">
                    <pre>{extractSectionText(activeContent)}</pre>
                  </div>
                </div>
              ) : (
                <div className="nm-navigate-select-hint">
                  <Compass size={40} style={{ opacity: 0.2 }} aria-hidden="true" />
                  <p>{isHi ? "बाईं ओर से कोई भी धारा चुनें।" : "Select any section from the outline on the left to view its content and AI summary here."}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!outline && !loading && !error && (
        <div className="nm-empty-state" style={{ minHeight: "200px" }}>
          <Compass size={40} style={{ opacity: 0.2 }} aria-hidden="true" />
          <p style={{ maxWidth: "480px" }}>
            {isHi
              ? "कोई भी लंबा कानूनी दस्तावेज़ पेस्ट करें और 'दस्तावेज़ रूपरेखा बनाएं' पर क्लिक करें।"
              : "Paste any lengthy legal document or try the BNS example, then click Generate Document Outline. The structured navigation tree will appear here."}
          </p>
        </div>
      )}
    </div>
  );
}
