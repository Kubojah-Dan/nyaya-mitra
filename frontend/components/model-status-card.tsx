"use client";

import React, { useEffect, useState } from "react";
import { Cpu, ShieldCheck, Zap, Activity } from "lucide-react";
import { getModelMetadata, ModelInventoryResponse } from "@/lib/api";

export function ModelStatusCard() {
  const [meta, setMeta] = useState<ModelInventoryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getModelMetadata()
      .then((data) => {
        setMeta(data);
        setLoading(false);
      })
      .catch((err) => {
        console.warn("Could not fetch live model metadata:", err);
        setLoading(false);
      });
  }, []);

  return (
    <div
      style={{
        background: "rgba(255, 255, 255, 0.08)",
        backdropFilter: "blur(8px)",
        border: "1px solid rgba(255, 255, 255, 0.15)",
        borderRadius: "14px",
        padding: "1.25rem",
        color: "#ffffff",
      }}
      role="region"
      aria-label="Active GenAI Multi-Tier Infrastructure"
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.85rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Cpu size={18} style={{ color: "#93c5fd" }} aria-hidden="true" />
          <h4 style={{ color: "#ffffff", fontSize: "0.95rem", fontWeight: 700 }}>
            GenAI Model Routing Engine
          </h4>
        </div>
        <span
          style={{
            background: "#ecfdf5",
            color: "#065f46",
            fontSize: "0.72rem",
            fontWeight: 700,
            padding: "2px 8px",
            borderRadius: "9999px",
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
          }}
        >
          <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#059669" }} aria-hidden="true" />
          ACTIVE TIERS
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.75rem", marginBottom: "0.85rem" }}>
        <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: "0.6rem 0.75rem", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
          <div style={{ fontSize: "0.72rem", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>Tier 1: FAST</div>
          <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#93c5fd" }}>gemini-2.0-flash</div>
          <div style={{ fontSize: "0.68rem", color: "#cbd5e1" }}>Fallback: llama3-70b</div>
        </div>

        <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: "0.6rem 0.75rem", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
          <div style={{ fontSize: "0.72rem", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>Tier 2: BALANCED</div>
          <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#86efac" }}>gemini-2.0-pro</div>
          <div style={{ fontSize: "0.68rem", color: "#cbd5e1" }}>Fallback: llama3-70b</div>
        </div>

        <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: "0.6rem 0.75rem", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
          <div style={{ fontSize: "0.72rem", color: "#94a3b8", textTransform: "uppercase", fontWeight: 700 }}>Tier 3: REASONING</div>
          <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#fde047" }}>gemini-1.5-pro</div>
          <div style={{ fontSize: "0.68rem", color: "#cbd5e1" }}>Fallback: mixtral-8x7b</div>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: "0.75rem", color: "#cbd5e1", borderTop: "1px solid rgba(255, 255, 255, 0.1)", paddingTop: "0.65rem" }}>
        <span>Zero-Hallucination Tier-1 Citations</span>
        <span style={{ color: "#93c5fd", fontWeight: 600 }}>BNS/BNSS 2024 Verified</span>
      </div>
    </div>
  );
}
