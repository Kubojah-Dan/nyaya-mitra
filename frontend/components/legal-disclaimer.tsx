import React from "react";
import { AlertCircle, ShieldAlert } from "lucide-react";

interface LegalDisclaimerProps {
  language?: "en" | "hi";
  customText?: string;
}

export function LegalDisclaimer({ language = "en", customText }: LegalDisclaimerProps) {
  const isHi = language === "hi";

  return (
    <div
      role="note"
      aria-label="Statutory Legal Disclaimer"
      style={{
        background: "var(--warning-light)",
        border: "1px solid #fde68a",
        borderRadius: "var(--radius-md)",
        padding: "0.85rem 1.15rem",
        display: "flex",
        alignItems: "flex-start",
        gap: "0.75rem",
        color: "#92400e",
        fontSize: "0.85rem",
        lineHeight: 1.5,
        margin: "1rem 0",
      }}
    >
      <ShieldAlert size={20} style={{ color: "#d97706", flexShrink: 0, marginTop: "2px" }} aria-hidden="true" />
      <div>
        <strong style={{ display: "block", marginBottom: "0.2rem", color: "#78350f" }}>
          {isHi ? "महत्वपूर्ण कानूनी सूचना (Non-Lawyer Legal Information Notice):" : "Statutory Notice & Legal Disclaimer:"}
        </strong>
        <p>
          {customText ||
            (isHi
              ? "न्यायमित्र सक्रिय भारतीय कानूनों (BNS/BNSS 2023) और आधिकारिक स्रोतों पर आधारित सामान्य वैधानिक जानकारी प्रदान करता है। यह कानूनी सलाह या वकील-मुवक्किल संबंध का गठन नहीं करता है। अदालत में प्रतिनिधित्व के लिए अपने निकटतम ज़िला कानूनी सेवा प्राधिकरण (DLSA) या 15100 पर संपर्क करें।"
              : "NyayaMitra provides general statutory information and procedural assistance grounded in current Indian legislation (BNS/BNSS 2023). It does not provide formal legal representation or establish an advocate-client relationship. For court representation, contact your nearest DLSA or call NALSA 15100.")}
        </p>
      </div>
    </div>
  );
}
