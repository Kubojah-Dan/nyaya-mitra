"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import {
  GitCompare,
  Upload,
  AlertTriangle,
  CheckCircle,
  Loader2,
  ArrowLeft,
  FileText,
  Plus,
  Minus,
  Edit3,
  Minus as MinusIcon,
  Globe,
  Info,
} from "lucide-react";
import { compareDocuments, compareDocumentsJson, SectionDelta } from "@/lib/api";

type Language = "en" | "hi";

const EXAMPLE_DOC_A = `LEASE AGREEMENT
This Lease Agreement is entered into on 1st January 2024 between Ramesh Kumar (Landlord) and Priya Sharma (Tenant).

SECTION 1 - PROPERTY
The Landlord agrees to lease the property at 42 Green Park, New Delhi - 110016.

SECTION 2 - RENT
Monthly rent shall be Rs. 15,000/- (Rupees Fifteen Thousand only) payable on or before the 5th of each month.

SECTION 3 - DEPOSIT
Security deposit of Rs. 45,000/- (Three months rent) to be paid at the time of execution.

SECTION 4 - NOTICE PERIOD
Either party shall give 30 days written notice before termination of the lease.

SECTION 5 - MAINTENANCE
Tenant shall be responsible for minor maintenance up to Rs. 500/-.`;

const EXAMPLE_DOC_B = `REVISED LEASE AGREEMENT
This Lease Agreement is entered into on 1st April 2024 between Ramesh Kumar (Landlord) and Priya Sharma (Tenant).

SECTION 1 - PROPERTY
The Landlord agrees to lease the property at 42 Green Park, New Delhi - 110016 (as-is condition).

SECTION 2 - RENT
Monthly rent shall be Rs. 18,500/- (Rupees Eighteen Thousand Five Hundred only) payable on or before the 1st of each month.

SECTION 3 - DEPOSIT
Security deposit of Rs. 55,500/- (Three months rent) to be paid at the time of execution.

SECTION 4 - NOTICE PERIOD
Either party shall give 15 days written notice before termination of the lease.

SECTION 5 - MAINTENANCE
Tenant shall be responsible for minor maintenance up to Rs. 1,000/-.

SECTION 6 - LATE PAYMENT FEE
A late payment fee of Rs. 500/- per day shall apply for rent paid after the 5th of each month.`;

export default function ComparePage() {
  const [lang, setLang] = useState<Language>("en");
  const [docA, setDocA] = useState<string>("");
  const [docB, setDocB] = useState<string>("");
  const [titleA, setTitleA] = useState<string>("");
  const [titleB, setTitleB] = useState<string>("");
  const [fileA, setFileA] = useState<File | null>(null);
  const [fileB, setFileB] = useState<File | null>(null);
  const [result, setResult] = useState<Awaited<ReturnType<typeof compareDocuments>> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileARef = useRef<HTMLInputElement>(null);
  const fileBRef = useRef<HTMLInputElement>(null);

  const isHi = lang === "hi";

  const loadExamples = () => {
    setDocA(EXAMPLE_DOC_A);
    setDocB(EXAMPLE_DOC_B);
    setTitleA("Lease Agreement — January 2024");
    setTitleB("Revised Lease Agreement — April 2024");
    setResult(null);
    setError(null);
  };

  const handleCompare = async () => {
    if ((!docA.trim() && !fileA) || (!docB.trim() && !fileB)) {
      setError(isHi ? "कृपया दोनों दस्तावेज़ दर्ज करें।" : "Please provide both documents to compare.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      let res;
      if (fileA || fileB) {
        res = await compareDocuments({
          fileA: fileA || undefined,
          fileB: fileB || undefined,
          documentA: docA || undefined,
          documentB: docB || undefined,
          titleA: titleA || "Document A",
          titleB: titleB || "Document B",
          language: lang,
          sessionId: `nm_compare_${Date.now()}`,
        });
      } else {
        res = await compareDocumentsJson({
          document_a: docA,
          document_b: docB,
          title_a: titleA || "Document A",
          title_b: titleB || "Document B",
          language: lang,
          session_id: `nm_compare_${Date.now()}`,
        });
      }
      setResult(res);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Comparison failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const getDeltaBadge = (type: SectionDelta["delta_type"]) => {
    switch (type) {
      case "ADDED": return <span className="nm-diff-badge nm-diff-added"><Plus size={11} aria-hidden="true" /> Added</span>;
      case "REMOVED": return <span className="nm-diff-badge nm-diff-removed"><Minus size={11} aria-hidden="true" /> Removed</span>;
      case "MODIFIED": return <span className="nm-diff-badge nm-diff-modified"><Edit3 size={11} aria-hidden="true" /> Modified</span>;
      case "UNCHANGED": return <span className="nm-diff-badge nm-diff-unchanged"><CheckCircle size={11} aria-hidden="true" /> Unchanged</span>;
      default: return null;
    }
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
          <div className="nm-page-icon-wrap" style={{ background: "linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%)" }}>
            <GitCompare size={24} aria-hidden="true" />
          </div>
          <div>
            <h1 id="compare-page-heading" className="nm-page-h1">
              {isHi ? "दस्तावेज़ तुलना (Document Compare)" : "Document Comparison — Side-by-Side Diff"}
            </h1>
            <p className="nm-page-desc">
              {isHi
                ? "दो कानूनी दस्तावेज़ों की धारावार तुलना करें। जोड़े गए, हटाए गए और बदले गए खंड स्वतः पहचानें।"
                : "Upload two versions of a legal document and get an automated section-by-section diff with statutory citations. Identify added, removed, and modified clauses instantly."}
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
        <button className="nm-btn nm-btn-secondary nm-btn-sm" onClick={loadExamples} id="compare-load-example">
          <FileText size={14} aria-hidden="true" />
          {isHi ? "किरायेदारी अनुबंध तुलना (Lease Agreement Diff)" : "Lease Agreement Version Comparison"}
        </button>
      </div>

      {/* Input Side-by-Side */}
      <div className="nm-compare-input-grid">
        {/* Document A */}
        <div className="nm-compare-input-col">
          <div className="nm-compare-col-header nm-compare-col-a">
            <div className="nm-compare-col-label">
              <FileText size={16} aria-hidden="true" />
              <span>{isHi ? "दस्तावेज़ A (पुराना / मूल)" : "Document A (Original / Older Version)"}</span>
            </div>
          </div>
          <div className="nm-form-group">
            <label className="nm-form-label" htmlFor="title-a">{isHi ? "दस्तावेज़ A का शीर्षक:" : "Document A Title:"}</label>
            <input
              id="title-a"
              type="text"
              className="nm-input"
              placeholder={isHi ? "उदा. किरायेदारी अनुबंध — जनवरी 2024" : "e.g. Lease Agreement — January 2024"}
              value={titleA}
              onChange={(e) => setTitleA(e.target.value)}
            />
          </div>
          <div className="nm-form-group">
            <label className="nm-form-label" htmlFor="doc-a-text">
              {isHi ? "दस्तावेज़ A का पाठ:" : "Document A Text:"}
            </label>
            <textarea
              id="doc-a-text"
              className="nm-textarea nm-compare-textarea"
              rows={12}
              placeholder={isHi ? "दस्तावेज़ A का पाठ यहाँ पेस्ट करें..." : "Paste Document A text here (lease agreement, FIR, legal notice, court order...)"}
              value={docA}
              onChange={(e) => setDocA(e.target.value)}
            />
          </div>
          <div className="nm-upload-zone">
            <input
              ref={fileARef}
              type="file"
              accept=".pdf,.txt,.docx"
              style={{ display: "none" }}
              aria-label="Upload Document A"
              onChange={(e) => e.target.files && setFileA(e.target.files[0])}
            />
            <button className="nm-btn nm-btn-secondary nm-btn-sm" onClick={() => fileARef.current?.click()}>
              <Upload size={14} aria-hidden="true" />
              {fileA ? fileA.name : (isHi ? "PDF/TXT अपलोड करें (A)" : "Upload PDF/TXT (A)")}
            </button>
          </div>
        </div>

        {/* Document B */}
        <div className="nm-compare-input-col">
          <div className="nm-compare-col-header nm-compare-col-b">
            <div className="nm-compare-col-label">
              <FileText size={16} aria-hidden="true" />
              <span>{isHi ? "दस्तावेज़ B (नया / संशोधित)" : "Document B (Revised / Newer Version)"}</span>
            </div>
          </div>
          <div className="nm-form-group">
            <label className="nm-form-label" htmlFor="title-b">{isHi ? "दस्तावेज़ B का शीर्षक:" : "Document B Title:"}</label>
            <input
              id="title-b"
              type="text"
              className="nm-input"
              placeholder={isHi ? "उदा. संशोधित किरायेदारी अनुबंध — अप्रैल 2024" : "e.g. Revised Lease Agreement — April 2024"}
              value={titleB}
              onChange={(e) => setTitleB(e.target.value)}
            />
          </div>
          <div className="nm-form-group">
            <label className="nm-form-label" htmlFor="doc-b-text">
              {isHi ? "दस्तावेज़ B का पाठ:" : "Document B Text:"}
            </label>
            <textarea
              id="doc-b-text"
              className="nm-textarea nm-compare-textarea"
              rows={12}
              placeholder={isHi ? "दस्तावेज़ B का पाठ यहाँ पेस्ट करें..." : "Paste Document B text here (updated version of the same document)"}
              value={docB}
              onChange={(e) => setDocB(e.target.value)}
            />
          </div>
          <div className="nm-upload-zone">
            <input
              ref={fileBRef}
              type="file"
              accept=".pdf,.txt,.docx"
              style={{ display: "none" }}
              aria-label="Upload Document B"
              onChange={(e) => e.target.files && setFileB(e.target.files[0])}
            />
            <button className="nm-btn nm-btn-secondary nm-btn-sm" onClick={() => fileBRef.current?.click()}>
              <Upload size={14} aria-hidden="true" />
              {fileB ? fileB.name : (isHi ? "PDF/TXT अपलोड करें (B)" : "Upload PDF/TXT (B)")}
            </button>
          </div>
        </div>
      </div>

      {/* Compare Button */}
      <div style={{ display: "flex", justifyContent: "center", margin: "1.5rem 0" }}>
        <button
          className="nm-btn nm-btn-primary"
          style={{ padding: "0.85rem 2.5rem", fontSize: "1rem", borderRadius: "9999px" }}
          onClick={handleCompare}
          disabled={loading}
          id="compare-submit-btn"
        >
          {loading ? <Loader2 size={20} className="nm-spin" aria-hidden="true" /> : <GitCompare size={20} aria-hidden="true" />}
          <span>{loading ? (isHi ? "तुलना हो रही है..." : "Comparing Documents...") : (isHi ? "दस्तावेज़ों की तुलना करें" : "Compare Documents")}</span>
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="nm-alert nm-alert-danger" role="alert">
          <AlertTriangle size={16} aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {result && (
        <div
          className="nm-compare-results"
          aria-live="polite"
          aria-atomic="false"
          aria-label={isHi ? "दस्तावेज़ तुलना परिणाम" : "Document comparison results"}
        >
          {/* Summary Banner */}
          <div className="nm-compare-summary-bar">
            <div className="nm-diff-stat nm-diff-added-stat">
              <Plus size={16} aria-hidden="true" />
              <span><strong>{result.added_count}</strong> {isHi ? "जोड़े गए" : "Added"}</span>
            </div>
            <div className="nm-diff-stat nm-diff-removed-stat">
              <Minus size={16} aria-hidden="true" />
              <span><strong>{result.removed_count}</strong> {isHi ? "हटाए गए" : "Removed"}</span>
            </div>
            <div className="nm-diff-stat nm-diff-modified-stat">
              <Edit3 size={16} aria-hidden="true" />
              <span><strong>{result.modified_count}</strong> {isHi ? "बदले गए" : "Modified"}</span>
            </div>
            <div className="nm-diff-stat nm-diff-unchanged-stat">
              <CheckCircle size={16} aria-hidden="true" />
              <span><strong>{result.unchanged_count}</strong> {isHi ? "अपरिवर्तित" : "Unchanged"}</span>
            </div>
          </div>

          {/* AI Summary */}
          {result.summary && (
            <div className="nm-card-feature nm-compare-ai-summary">
              <div className="nm-feature-header">
                <h2><Info size={18} aria-hidden="true" /> {isHi ? "AI सारांश" : "AI Comparison Summary"}</h2>
                <span className="nm-badge nm-badge-verified">
                  <CheckCircle size={11} aria-hidden="true" />
                  {result.model_used || "Tier-1 Model"}
                </span>
              </div>
              <p className="nm-feature-body">{result.summary}</p>
              {result.citations && result.citations.length > 0 && (
                <div className="nm-badge-row" style={{ marginTop: "0.5rem" }}>
                  {result.citations.map((c, i) => (
                    <span key={i} className="nm-badge nm-badge-outlined">{c}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div className="nm-alert nm-alert-warning" role="alert">
              <AlertTriangle size={16} aria-hidden="true" />
              <div>
                {result.warnings.map((w, i) => <p key={i}>{w}</p>)}
              </div>
            </div>
          )}

          {/* Section Deltas */}
          <h2 className="nm-section-title" style={{ marginTop: "1.5rem" }}>
            <GitCompare size={18} aria-hidden="true" />
            {isHi ? "धारावार अंतर (Section-by-Section Diff)" : "Section-by-Section Diff"}
          </h2>

          <div className="nm-deltas-list" role="list" aria-label="Document section differences">
            {result.deltas && result.deltas.length > 0 ? (
              result.deltas.map((delta, i) => (
                <div
                  key={i}
                  className={`nm-delta-item nm-delta-${delta.delta_type.toLowerCase()}`}
                  role="listitem"
                >
                  <div className="nm-delta-header">
                    <div className="nm-delta-title">
                      {getDeltaBadge(delta.delta_type)}
                      <strong>Section: {delta.section_id}</strong>
                    </div>
                    {delta.citations && delta.citations.length > 0 && (
                      <div className="nm-badge-row">
                        {delta.citations.map((c, ci) => (
                          <span key={ci} className="nm-badge nm-badge-verified" style={{ fontSize: "0.7rem" }}>{c}</span>
                        ))}
                      </div>
                    )}
                  </div>

                  {delta.description && (
                    <p className="nm-delta-desc">{delta.description}</p>
                  )}

                  {(delta.delta_type === "MODIFIED" || delta.delta_type === "REMOVED" || delta.delta_type === "UNCHANGED") && delta.text_a && (
                    <div className="nm-delta-text-block nm-delta-text-a">
                      <span className="nm-delta-text-label">
                        <MinusIcon size={12} aria-hidden="true" /> {titleA || "Document A"}
                      </span>
                      <pre>{delta.text_a}</pre>
                    </div>
                  )}

                  {(delta.delta_type === "MODIFIED" || delta.delta_type === "ADDED") && delta.text_b && (
                    <div className="nm-delta-text-block nm-delta-text-b">
                      <span className="nm-delta-text-label">
                        <Plus size={12} aria-hidden="true" /> {titleB || "Document B"}
                      </span>
                      <pre>{delta.text_b}</pre>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="nm-empty-state">
                <GitCompare size={32} style={{ opacity: 0.3 }} aria-hidden="true" />
                <p>{isHi ? "कोई अंतर नहीं मिला।" : "No differences detected — documents appear identical."}</p>
              </div>
            )}
          </div>

          {/* Disclaimer */}
          {result.disclaimer && (
            <p className="nm-compare-disclaimer">{result.disclaimer}</p>
          )}
        </div>
      )}

      {/* Empty State */}
      {!result && !loading && !error && (
        <div className="nm-empty-state" style={{ minHeight: "200px" }}>
          <GitCompare size={40} style={{ opacity: 0.2 }} aria-hidden="true" />
          <p style={{ maxWidth: "480px" }}>
            {isHi
              ? "दोनों दस्तावेज़ों का पाठ दर्ज करें और 'दस्तावेज़ों की तुलना करें' पर क्लिक करें। धारावार अंतर यहाँ दिखाई देगा।"
              : "Paste or upload two versions of a legal document, then click Compare Documents. The section-by-section diff will appear here."}
          </p>
        </div>
      )}
    </div>
  );
}
