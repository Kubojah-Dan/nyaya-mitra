"""001_initial_schema

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-09-15 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. user_sessions
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_token', sa.String(64), nullable=False, unique=True),
        sa.Column('locale', sa.String(10), default='en'),
        sa.Column('disclaimer_accepted', sa.Boolean, default=False),
        sa.Column('disclaimer_accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_hash', sa.String(64), nullable=True),
        sa.Column('user_agent_hash', sa.String(64), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('metadata_json', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_user_sessions_session_token', 'user_sessions', ['session_token'])

    # 2. intake_states
    op.create_table(
        'intake_states',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('user_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('current_stage', sa.String(32), default='INITIAL'),
        sa.Column('domain', sa.String(64), nullable=True),
        sa.Column('subdomain', sa.String(64), nullable=True),
        sa.Column('collected_facts', sa.JSON, default=dict),
        sa.Column('missing_facts', sa.JSON, default=list),
        sa.Column('user_clarifications', sa.JSON, default=list),
        sa.Column('confidence_score', sa.Float, default=0.0),
        sa.Column('is_urgent', sa.Boolean, default=False),
        sa.Column('urgency_reason', sa.Text, nullable=True),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_intake_states_session_id', 'intake_states', ['session_id'])
    op.create_index('ix_intake_states_domain', 'intake_states', ['domain'])

    # 3. domain_classifications
    op.create_table(
        'domain_classifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), nullable=True),
        sa.Column('intake_id', sa.String(36), nullable=True),
        sa.Column('primary_domain', sa.String(64), nullable=False),
        sa.Column('secondary_domain', sa.String(64), nullable=True),
        sa.Column('confidence', sa.Float, default=0.0),
        sa.Column('rationale', sa.Text, default=''),
        sa.Column('detected_keywords', sa.JSON, default=list),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 4. sources
    op.create_table(
        'sources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_code', sa.String(32), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('tier', sa.Integer, default=1),
        sa.Column('publisher', sa.String(255), nullable=False),
        sa.Column('source_url', sa.String(512), nullable=False),
        sa.Column('jurisdiction', sa.String(128), default='Union of India'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('update_cadence_days', sa.Integer, default=7),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_healthy_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_sources_source_code', 'sources', ['source_code'])

    # 5. source_snapshots
    op.create_table(
        'source_snapshots',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('version_label', sa.String(64), nullable=False),
        sa.Column('raw_content_uri', sa.String(512), nullable=True),
        sa.Column('status', sa.String(32), default='SUCCESS'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('item_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_source_snapshots_source_id', 'source_snapshots', ['source_id'])

    # 6. legal_documents
    op.create_table(
        'legal_documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('act_code', sa.String(64), unique=True, nullable=False),
        sa.Column('act_name', sa.String(255), nullable=False),
        sa.Column('act_number', sa.String(32), nullable=True),
        sa.Column('act_year', sa.Integer, nullable=False),
        sa.Column('jurisdiction', sa.String(128), default='Union of India'),
        sa.Column('enacted_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(32), default='ACTIVE'),
        sa.Column('repeals_or_replaces', sa.String(128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_legal_documents_act_code', 'legal_documents', ['act_code'])

    # 7. legal_sections
    op.create_table(
        'legal_sections',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('legal_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chapter', sa.String(128), nullable=True),
        sa.Column('section_number', sa.String(32), nullable=False),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('subsections', sa.JSON, default=list),
        sa.Column('full_text', sa.Text, nullable=False),
        sa.Column('plain_english', sa.Text, nullable=True),
        sa.Column('plain_hindi', sa.Text, nullable=True),
        sa.Column('penalties', sa.Text, nullable=True),
        sa.Column('is_cognizable', sa.Boolean, nullable=True),
        sa.Column('is_bailable', sa.Boolean, nullable=True),
        sa.Column('is_compoundable', sa.Boolean, nullable=True),
        sa.Column('relevant_keywords', sa.JSON, default=list),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_legal_sections_section_number', 'legal_sections', ['section_number'])
    op.create_index('ix_legal_sections_document_id', 'legal_sections', ['document_id'])

    # 8. citations
    op.create_table(
        'citations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('section_id', sa.String(36), sa.ForeignKey('legal_sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('act_name', sa.String(255), nullable=False),
        sa.Column('section_number', sa.String(32), nullable=False),
        sa.Column('pinpoint', sa.String(128), nullable=True),
        sa.Column('verified_status', sa.String(32), default='VERIFIED_TIER_1'),
        sa.Column('statutory_quote', sa.Text, nullable=False),
        sa.Column('official_url', sa.String(512), nullable=False),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 9. retrieval_chunks
    op.create_table(
        'retrieval_chunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('section_id', sa.String(36), sa.ForeignKey('legal_sections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer, default=0),
        sa.Column('chunk_text', sa.Text, nullable=False),
        sa.Column('token_count', sa.Integer, default=0),
        sa.Column('embedding_ref', sa.String(128), nullable=True),
        sa.Column('metadata_json', sa.JSON, default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 10. uploaded_documents
    op.create_table(
        'uploaded_documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('user_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(128), nullable=False),
        sa.Column('file_size_bytes', sa.Integer, nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('storage_path', sa.String(512), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('retention_deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('redacted_content', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_uploaded_documents_retention_deadline', 'uploaded_documents', ['retention_deadline'])

    # 11. ocr_results
    op.create_table(
        'ocr_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('uploaded_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('text_extracted', sa.Text, nullable=False),
        sa.Column('confidence_score', sa.Float, default=0.0),
        sa.Column('detected_language', sa.String(10), default='en'),
        sa.Column('page_count', sa.Integer, default=1),
        sa.Column('ocr_engine', sa.String(64), default='mock'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 12. extracted_deadlines
    op.create_table(
        'extracted_deadlines',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), nullable=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('uploaded_documents.id', ondelete='CASCADE'), nullable=True),
        sa.Column('deadline_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('relative_days', sa.Integer, nullable=True),
        sa.Column('trigger_event', sa.String(255), nullable=False),
        sa.Column('label', sa.String(255), nullable=False),
        sa.Column('statutory_basis', sa.String(512), nullable=False),
        sa.Column('urgency_level', sa.String(32), default='MEDIUM'),
        sa.Column('is_firm', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 13. generated_documents
    op.create_table(
        'generated_documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('user_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.String(64), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('slots_data', sa.JSON, default=dict),
        sa.Column('markdown_content', sa.Text, nullable=False),
        sa.Column('pdf_path', sa.String(512), nullable=True),
        sa.Column('disclaimer_text', sa.Text, nullable=False),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 14. escalation_resources
    op.create_table(
        'escalation_resources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('resource_type', sa.String(32), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('state', sa.String(100), nullable=False),
        sa.Column('district', sa.String(100), nullable=True),
        sa.Column('address', sa.Text, nullable=False),
        sa.Column('contact_number', sa.String(128), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('website_url', sa.String(512), nullable=True),
        sa.Column('languages_supported', sa.JSON, default=list),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_escalation_resources_state', 'escalation_resources', ['state'])

    # 15. evaluation_results
    op.create_table(
        'evaluation_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('eval_run_id', sa.String(64), nullable=False),
        sa.Column('suite_name', sa.String(64), nullable=False),
        sa.Column('test_case_id', sa.String(64), nullable=False),
        sa.Column('query_prompt', sa.Text, nullable=False),
        sa.Column('domain', sa.String(64), nullable=False),
        sa.Column('passed', sa.Boolean, nullable=False),
        sa.Column('citation_accuracy', sa.Float, default=1.0),
        sa.Column('faithfulness_score', sa.Float, default=1.0),
        sa.Column('outdated_law_detected', sa.Boolean, default=False),
        sa.Column('latency_ms', sa.Integer, default=0),
        sa.Column('details_json', sa.JSON, default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('evaluation_results')
    op.drop_table('escalation_resources')
    op.drop_table('generated_documents')
    op.drop_table('extracted_deadlines')
    op.drop_table('ocr_results')
    op.drop_table('uploaded_documents')
    op.drop_table('retrieval_chunks')
    op.drop_table('citations')
    op.drop_table('legal_sections')
    op.drop_table('legal_documents')
    op.drop_table('source_snapshots')
    op.drop_table('sources')
    op.drop_table('domain_classifications')
    op.drop_table('intake_states')
    op.drop_table('user_sessions')
