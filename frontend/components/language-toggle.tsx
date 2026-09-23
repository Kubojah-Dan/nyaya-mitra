"use client";

import React, { useEffect, useState } from "react";
import { Languages } from "lucide-react";

interface LanguageToggleProps {
  currentLang: string;
  onLanguageChange: (lang: "en" | "hi") => void;
}

export function LanguageToggle({ currentLang, onLanguageChange }: LanguageToggleProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Synchronize html lang attribute dynamically for screen readers (WCAG 3.1.1)
    if (typeof document !== "undefined") {
      document.documentElement.lang = currentLang;
    }
  }, [currentLang]);

  const toggle = (lang: "en" | "hi") => {
    onLanguageChange(lang);
    if (typeof document !== "undefined") {
      document.documentElement.lang = lang;
    }
  };

  return (
    <div
      role="group"
      aria-label="Language Selector (भाषा चयन)"
      style={{
        display: "inline-flex",
        alignItems: "center",
        background: "rgba(255, 255, 255, 0.15)",
        border: "1px solid rgba(255, 255, 255, 0.3)",
        borderRadius: "9999px",
        padding: "2px 4px",
      }}
    >
      <Languages size={15} style={{ marginRight: "4px", marginLeft: "4px", color: "#ffffff" }} aria-hidden="true" />
      <button
        type="button"
        onClick={() => toggle("en")}
        aria-pressed={currentLang === "en"}
        style={{
          background: currentLang === "en" ? "#ffffff" : "transparent",
          color: currentLang === "en" ? "#0f2942" : "#ffffff",
          fontWeight: currentLang === "en" ? 700 : 500,
          border: "none",
          borderRadius: "9999px",
          padding: "3px 8px",
          fontSize: "0.78rem",
          cursor: "pointer",
          transition: "all 0.15s ease",
        }}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => toggle("hi")}
        aria-pressed={currentLang === "hi"}
        style={{
          background: currentLang === "hi" ? "#ffffff" : "transparent",
          color: currentLang === "hi" ? "#0f2942" : "#ffffff",
          fontWeight: currentLang === "hi" ? 700 : 500,
          border: "none",
          borderRadius: "9999px",
          padding: "3px 8px",
          fontSize: "0.78rem",
          cursor: "pointer",
          transition: "all 0.15s ease",
        }}
      >
        <span lang="hi">हिन्दी</span>
      </button>
    </div>
  );
}
