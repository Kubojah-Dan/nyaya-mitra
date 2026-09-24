"use client";

import React from "react";
import Link from "next/link";
import { MessageSquare, GitCompare, Compass, FileCheck, Scale, CalendarDays, ArrowRight, Shield } from "lucide-react";
import { ModelStatusCard } from "./model-status-card";

interface LandingHeroProps {
  language?: "en" | "hi";
  onSelectTab?: (tabKey: string) => void;
}

export function LandingHero({ language = "en", onSelectTab }: LandingHeroProps) {
  const isHi = language === "hi";

  const handleNav = (tabKey: string) => {
    if (onSelectTab) {
      onSelectTab(tabKey);
      if (typeof window !== "undefined") {
        const workspace = document.getElementById("module-workspace");
        if (workspace) {
          workspace.scrollIntoView({ behavior: "smooth" });
        }
      }
    }
  };

  return (
    <section className="nm-landing-hero" aria-labelledby="hero-main-heading">
      <div className="nm-hero-grid">
        <div>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", background: "rgba(255, 255, 255, 0.12)", border: "1px solid rgba(255, 255, 255, 0.25)", padding: "4px 12px", borderRadius: "9999px", fontSize: "0.8rem", fontWeight: 600, marginBottom: "1rem" }}>
            <Shield size={14} style={{ color: "#86efac" }} aria-hidden="true" />
            <span>AI for Legal Assistance & Access</span>
          </div>

          <h2 id="hero-main-heading" className="nm-hero-title-main">
            {isHi ? (
              <span lang="hi">AI-संचालित कानूनी सहायता और अधिकारों के लिए भारत में AI </span>
            ) : (
              <>Understand, Compare & Navigate Indian Legal Documents with GenAI</>
            )}
          </h2>

          <p className="nm-hero-tagline">
            {isHi ? (
              <span lang="hi">
                भारतीय न्याय संहिता (BNS 2023), नागरिक सुरक्षा (BNSS), आधिकारिक भारत कोड, और NALSA 15100 विधिक सहायता के साथ 100% सत्यापित समाधान।
              </span>
            ) : (
              <>
                Grounded in current Indian Law (BNS/BNSS 2024), Tier-1 statutory enactments, and Section 12 Legal Services Authorities Act 1987. Zero hallucinations, automated diffs, and structured drafting.
              </>
            )}
          </p>

          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1.25rem" }}>
            <button
              type="button"
              onClick={() => handleNav("intake")}
              className="nm-btn nm-btn-primary"
              style={{ padding: "0.75rem 1.4rem", fontSize: "0.95rem", borderRadius: "9999px" }}
            >
              <MessageSquare size={18} aria-hidden="true" />
              <span>{isHi ? "समस्या बताएं (Guided Intake)" : "1. Understand Legal Problem"}</span>
            </button>

            <button
              type="button"
              onClick={() => handleNav("compare")}
              className="nm-btn"
              style={{
                background: "#ffffff",
                color: "#0f2942",
                fontWeight: 700,
                padding: "0.75rem 1.4rem",
                fontSize: "0.95rem",
                borderRadius: "9999px",
                border: "none",
              }}
            >
              <GitCompare size={18} style={{ color: "#1d4ed8" }} aria-hidden="true" />
              <span>{isHi ? "दस्तावेज़ तुलना (Compare)" : "2. Compare Documents"}</span>
            </button>
          </div>
        </div>

        <div>
          <ModelStatusCard />
        </div>
      </div>
    </section>
  );
}
