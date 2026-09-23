"""
Phase 0 Verification Test Suite: Product Contract, Scope & Legal-Safety Boundaries
Validates PRD, SOURCE_POLICY, SAFETY_POLICY, and .gitignore consistency.
"""
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DOCS_DIR = REPO_ROOT / "docs"

def test_docs_exist():
    """Ensure all mandatory Phase 0 documents exist and are non-empty."""
    required_docs = [
        "PRD.md",
        "SOURCE_POLICY.md",
        "SAFETY_POLICY.md"
    ]
    for doc in required_docs:
        doc_path = DOCS_DIR / doc
        assert doc_path.exists(), f"Missing required document: {doc}"
        content = doc_path.read_text(encoding="utf-8")
        assert len(content.strip()) > 500, f"Document {doc} is too short or empty"

def test_prd_content_requirements():
    """Verify PRD contains personas, journeys, taxonomy, and metrics."""
    prd_text = (DOCS_DIR / "PRD.md").read_text(encoding="utf-8")
    
    # 3-5 Personas & High-Value Journeys
    assert "User Personas" in prd_text
    assert "Ramesh Kumar" in prd_text
    assert "Sunita Devi" in prd_text
    assert "Amit Patel" in prd_text
    
    # Core User Journeys
    assert "Tenancy & Eviction Defense" in prd_text
    assert "Defective Goods & Consumer Redressal" in prd_text
    assert "Right to Information" in prd_text
    assert "Deadline Guardian" in prd_text
    
    # Scope Matrix
    assert "In-Scope Domains" in prd_text
    assert "Consumer Protection" in prd_text
    assert "Bharatiya Nyaya Sanhita" in prd_text or "BNS" in prd_text
    assert "Explicitly Out-of-Scope" in prd_text
    
    # Risk Taxonomy: low, medium, high, emergency
    assert "Emergency (Tier 4)" in prd_text
    assert "High Risk (Tier 3)" in prd_text
    assert "Medium Risk (Tier 2)" in prd_text
    assert "Low Risk (Tier 1)" in prd_text
    
    # North Star & SLA Metrics
    assert "Zero Fabricated Citations" in prd_text
    assert "Grade 6–8" in prd_text or "Grade 6-8" in prd_text

def test_source_policy_requirements():
    """Verify SOURCE_POLICY contains Tier 1/2/3, BNS transition, and schema."""
    policy_text = (DOCS_DIR / "SOURCE_POLICY.md").read_text(encoding="utf-8")
    
    assert "Tier 1 — Authoritative Primary Sources" in policy_text
    assert "Tier 2 — Official Institutional Sources" in policy_text
    assert "Tier 3 — Trusted Secondary" in policy_text
    
    # 2024 Criminal Law Transition
    assert "Bharatiya Nyaya Sanhita" in policy_text or "BNS" in policy_text
    assert "Bharatiya Nagarik Suraksha Sanhita" in policy_text or "BNSS" in policy_text
    assert "Bharatiya Sakshya Adhiniyam" in policy_text or "BSA" in policy_text
    assert "Historical Concordance" in policy_text or "Historical" in policy_text
    
    # Metadata Schema fields
    required_fields = [
        "source_id", "source_url", "source_tier", "retrieved_at",
        "content_hash", "version_label", "jurisdiction", "verification_status"
    ]
    for field in required_fields:
        assert field in policy_text, f"Missing field {field} in source schema"

def test_safety_policy_requirements():
    """Verify SAFETY_POLICY covers disclaimer, escalation, injection, and PII."""
    safety_text = (DOCS_DIR / "SAFETY_POLICY.md").read_text(encoding="utf-8")
    
    # Mandatory Disclaimer
    assert "NOT a substitute for professional legal advice" in safety_text
    
    # Allowed vs Refusal
    assert "Permitted Operational Capabilities" in safety_text
    assert "Strictly Prohibited System Capabilities" in safety_text
    
    # Escalation Resources
    assert "15100" in safety_text or "NALSA" in safety_text
    assert "Tele-Law" in safety_text
    assert "DLSA" in safety_text
    
    # Prompt injection defense & PII
    assert "Prompt Injection" in safety_text
    assert "PII Protection" in safety_text
    assert "Zero Raw PII" in safety_text

def test_gitignore():
    """Verify .gitignore covers node_modules, env, logs, and build dirs."""
    gitignore_path = REPO_ROOT / ".gitignore"
    assert gitignore_path.exists(), ".gitignore does not exist"
    content = gitignore_path.read_text(encoding="utf-8")
    assert ".env" in content
    assert "node_modules" in content
    assert "__pycache__" in content
    assert ".next" in content

if __name__ == "__main__":
    test_docs_exist()
    test_prd_content_requirements()
    test_source_policy_requirements()
    test_safety_policy_requirements()
    test_gitignore()
    print("ALL PHASE 0 VERIFICATION CHECKS PASSED!")
