"use client";

import React from "react";
import {
  MessageSquare,
  Scale,
  CalendarDays,
  FileCheck,
  Users,
  GitCompare,
  type LucideIcon,
} from "lucide-react";

export interface TabItem {
  id: string;
  name: string;
  nameHi: string;
  verb: string;
  icon: LucideIcon;
  badge?: string;
}

export const MODULE_TABS: TabItem[] = [
  {
    id: "intake",
    name: "1. Guided Intake",
    nameHi: "1. समस्या मार्गदर्शन",
    verb: "UNDERSTAND",
    icon: MessageSquare,
  },
  {
    id: "rights",
    name: "2. Rights & Timelines",
    nameHi: "2. अधिकार व समयसीमा",
    verb: "UNDERSTAND",
    icon: Scale,
  },
  {
    id: "scanner",
    name: "3. Document Scanner",
    nameHi: "3. स्कैनर व तारीखें",
    verb: "UNDERSTAND",
    icon: CalendarDays,
  },
  {
    id: "generator",
    name: "4. Controlled Generator",
    nameHi: "4. विधिक प्रारूप",
    verb: "DRAFT",
    icon: FileCheck,
  },
  {
    id: "escalation",
    name: "5. Legal Aid Escalation",
    nameHi: "5. मुफ़्त कानूनी सहायता",
    verb: "ESCALATE",
    icon: Users,
    badge: "15100",
  },
  {
    id: "compare",
    name: "6. Compare Documents",
    nameHi: "6. दस्तावेज़ तुलना",
    verb: "COMPARE",
    icon: GitCompare,
    badge: "NEW",
  },
];

interface ModuleNavProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
  language?: "en" | "hi";
}

export function ModuleNav({ activeTab, onTabChange, language = "en" }: ModuleNavProps) {
  const isHi = language === "hi";

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const currentIndex = MODULE_TABS.findIndex((t) => t.id === activeTab);
    let nextIndex = -1;

    if (e.key === "ArrowRight" || e.key === "ArrowDown") {
      e.preventDefault();
      nextIndex = (currentIndex + 1) % MODULE_TABS.length;
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      e.preventDefault();
      nextIndex = (currentIndex - 1 + MODULE_TABS.length) % MODULE_TABS.length;
    } else if (e.key === "Home") {
      e.preventDefault();
      nextIndex = 0;
    } else if (e.key === "End") {
      e.preventDefault();
      nextIndex = MODULE_TABS.length - 1;
    }

    if (nextIndex !== -1 && MODULE_TABS[nextIndex]) {
      const nextTab = MODULE_TABS[nextIndex];
      onTabChange(nextTab.id);
      const tabBtn = document.getElementById(`tab-button-${nextTab.id}`);
      if (tabBtn) {
        tabBtn.focus();
      }
    }
  };

  return (
    <div
      role="tablist"
      aria-label="NyayaMitra Legal Services Workspace Tabs"
      className="nm-tab-bar"
      onKeyDown={handleKeyDown}
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "0.5rem",
        background: "var(--neutral-card)",
        padding: "0.5rem",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--border-color)",
        boxShadow: "var(--shadow-sm)",
        marginBottom: "1.5rem",
      }}
    >
      {MODULE_TABS.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            id={`tab-button-${tab.id}`}
            role="tab"
            type="button"
            aria-selected={isActive}
            aria-controls={`tabpanel-${tab.id}`}
            tabIndex={isActive ? 0 : -1}
            onClick={() => onTabChange(tab.id)}
            className={`nm-tab-btn ${isActive ? "active" : ""}`}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.65rem 1.1rem",
              borderRadius: "var(--radius-sm)",
              border: isActive ? "1px solid #93c5fd" : "1px solid transparent",
              background: isActive ? "#eff6ff" : "transparent",
              color: isActive ? "#1d4ed8" : "var(--text-body)",
              fontWeight: isActive ? 700 : 500,
              fontSize: "0.88rem",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            <Icon size={16} aria-hidden={true} />
            <span>{isHi ? tab.nameHi : tab.name}</span>
            {tab.badge && (
              <span
                style={{
                  fontSize: "0.68rem",
                  fontWeight: 800,
                  padding: "1px 6px",
                  borderRadius: "9999px",
                  background: tab.badge === "NEW" ? "#10b981" : "#dbeafe",
                  color: tab.badge === "NEW" ? "#ffffff" : "#1e40af",
                }}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
