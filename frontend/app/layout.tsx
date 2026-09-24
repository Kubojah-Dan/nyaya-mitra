import type { Metadata, Viewport } from "next";
import "./globals.css";
import Link from "next/link";
import {
  Landmark,
  AlertTriangle,
  Users,
  Shield,
  Phone,
  GitCompare,
  Compass,
  MessageSquare,
} from "lucide-react";

export const metadata: Metadata = {
  title: "NyayaMitra (न्यायमित्र) — AI for Legal Assistance & Access (India)",
  description: "Accessible, verified legal assistance grounded in current Indian law (BNS/BNSS/BSA 2023), official Tier-1 legal sources, structured document drafting, and human legal aid escalation under Section 12 LSAA 1987.",
  keywords: ["NyayaMitra", "Legal Aid India", "BNS 2023", "BNSS 2023", "RTI Application", "Consumer Complaint", "NALSA 15100", "Tele-Law"],
  authors: [{ name: "NyayaMitra Legal Access Platform" }],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <a href="#main-content" className="skip-link">
          Skip to main content (मुख्य सामग्री पर जाएं)
        </a>

        {/* 24x7 Emergency Helpline Ticker */}
        <div className="nm-emergency-bar" role="region" aria-label="Emergency Legal Helplines">
          <span>
            <Landmark size={14} aria-hidden="true" />
            <strong>NALSA Legal Aid:</strong> <a href="tel:15100">15100</a> (Toll-Free, 24x7)
          </span>
          <span>
            <AlertTriangle size={14} aria-hidden="true" />
            <strong>Police Emergency:</strong> <a href="tel:112">112</a>
          </span>
          <span>
            <Users size={14} aria-hidden="true" />
            <strong>Women in Distress:</strong> <a href="tel:181">181</a>
          </span>
          <span>
            <Shield size={14} aria-hidden="true" />
            <strong>Cyber Crime:</strong> <a href="tel:1930">1930</a>
          </span>
        </div>

        <header className="nm-header" role="banner">
          <div className="nm-header-inner">
            <Link href="/" className="nm-brand" aria-label="NyayaMitra Home">
              <div className="nm-emblem" aria-hidden="true">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/nyayamitra-logo.jpg"
                  alt="NyayaMitra Logo"
                  width={44}
                  height={44}
                  style={{ borderRadius: "50%", objectFit: "cover", display: "block" }}
                />
              </div>
              <div className="nm-title-group">
                <span className="nm-brand-title" style={{ fontSize: "1.25rem", fontWeight: 800, color: "#ffffff", display: "block" }}>
                  NyayaMitra
                </span>
                <p>Legal Rights For a Stronger Tomorrow</p>
              </div>
            </Link>
            <nav className="nm-header-nav" aria-label="Primary Navigation">
              <Link href="/app" className="nm-header-nav-link" aria-label="Understand legal problems">
                <MessageSquare size={15} aria-hidden="true" />
                <span>Understand</span>
              </Link>
              <Link href="/compare" className="nm-header-nav-link" aria-label="Compare legal documents">
                <GitCompare size={15} aria-hidden="true" />
                <span>Compare</span>
              </Link>
              <Link href="/navigate" className="nm-header-nav-link" aria-label="Navigate legal documents">
                <Compass size={15} aria-hidden="true" />
                <span>Navigate</span>
              </Link>
              <span className="nm-badge-current-law">
                <span className="nm-badge-dot" aria-hidden="true"></span> BNS/BNSS 2024
              </span>
            </nav>
          </div>
        </header>

        <main id="main-content" tabIndex={-1}>
          {children}
        </main>

        <footer className="nm-footer" role="contentinfo">
          <div className="nm-footer-inner">
            <div className="nm-footer-col" style={{ maxWidth: "360px" }}>
              <h2>NyayaMitra (न्यायमित्र)</h2>
              <p>
                An open-access legal empowerment platform helping citizens navigate
                rights, understand legal notices, draft statutory documents, and connect
                with official NALSA / DLSA legal aid across India.
              </p>
            </div>
            <div className="nm-footer-col">
              <h2>Essential Helplines</h2>
              <ul>
                <li><strong>NALSA Legal Aid:</strong> <a href="tel:15100">15100</a> (24x7)</li>
                <li><strong>Tele-Law Portal:</strong> <a href="https://www.tele-law.in" target="_blank" rel="noopener noreferrer">tele-law.in</a></li>
                <li><strong>National Consumer Helpline:</strong> <a href="tel:1915">1915</a></li>
                <li><strong>National Emergency:</strong> <a href="tel:112">112</a></li>
              </ul>
            </div>
            <div className="nm-footer-col">
              <h2>Official Tier-1 Sources</h2>
              <ul>
                <li><a href="https://www.indiacode.nic.in" target="_blank" rel="noopener noreferrer">India Code (Central Acts)</a></li>
                <li><a href="https://services.ecourts.gov.in" target="_blank" rel="noopener noreferrer">eCourts Services</a></li>
                <li><a href="https://nalsa.gov.in" target="_blank" rel="noopener noreferrer">NALSA Official Portal</a></li>
                <li><a href="https://edaakhil.nic.in" target="_blank" rel="noopener noreferrer">e-Daakhil (Consumer Forum)</a></li>
              </ul>
            </div>
          </div>
          <div className="nm-footer-bottom">
            <p>
              <strong>Non-Lawyer Legal Information Notice:</strong> NyayaMitra provides general statutory information and procedural assistance based on active Indian laws.
              It does not offer legal representation or constitute an advocate-client relationship. For formal court representation, please contact your nearest DLSA.
            </p>
            <p style={{ marginTop: "0.5rem" }}>
              © 2026 NyayaMitra • Built for Accessible Justice in India
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
