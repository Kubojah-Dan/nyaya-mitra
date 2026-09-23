"use client";

import React, { useState } from "react";
import { ListTree, ChevronRight, Hash } from "lucide-react";
import { OutlineSection } from "@/lib/api";

interface OutlineNavProps {
  title?: string;
  sections: OutlineSection[];
  onSelectSection?: (sectionId: string) => void;
}

export function OutlineNav({ title = "Document Outline", sections, onSelectSection }: OutlineNavProps) {
  const [activeId, setActiveId] = useState<string>("");

  if (!sections || sections.length === 0) {
    return null;
  }

  const handleJump = (sectionId: string) => {
    setActiveId(sectionId);
    if (onSelectSection) {
      onSelectSection(sectionId);
    }

    if (typeof document !== "undefined") {
      const element = document.getElementById(sectionId);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
        element.focus({ preventScroll: true });
      }
    }
  };

  const renderItems = (items: OutlineSection[]) => {
    return (
      <ul className="nm-outline-list" role="list">
        {items.map((sec) => (
          <li key={sec.section_id}>
            <button
              type="button"
              className={`nm-outline-item-btn ${sec.level === 2 ? "level-2" : ""} ${
                activeId === sec.section_id ? "active" : ""
              }`}
              onClick={() => handleJump(sec.section_id)}
              aria-current={activeId === sec.section_id ? "location" : undefined}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <Hash size={12} style={{ color: "#64748b", flexShrink: 0 }} aria-hidden="true" />
                <strong style={{ color: "inherit" }}>{sec.heading}</strong>
              </span>
              {sec.summary && (
                <span style={{ fontSize: "0.76rem", color: "#64748b", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {sec.summary}
                </span>
              )}
            </button>
            {sec.children && sec.children.length > 0 && (
              <div style={{ marginLeft: "0.75rem", marginTop: "0.25rem" }}>
                {renderItems(sec.children)}
              </div>
            )}
          </li>
        ))}
      </ul>
    );
  };

  return (
    <nav className="nm-outline-sidebar" aria-label="Document Section Outline Navigator">
      <div className="nm-outline-title">
        <ListTree size={18} style={{ color: "#1d4ed8" }} aria-hidden="true" />
        <span>{title}</span>
      </div>
      {renderItems(sections)}
    </nav>
  );
}
