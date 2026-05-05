"""Initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-05-05 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")

    # 2. Create ENUMs
    department_enum = postgresql.ENUM('SHOP_ESTABLISHMENT', 'FACTORIES', 'LABOUR', 'KSPCB', 'BESCOM', name='department')
    department_enum.create(op.get_bind(), checkfirst=True)
    
    registry_status_enum = postgresql.ENUM('ACTIVE', 'DORMANT', 'CLOSED', 'UNCLASSIFIED', name='registrystatus')
    registry_status_enum.create(op.get_bind(), checkfirst=True)
    
    pair_status_enum = postgresql.ENUM('PENDING_REVIEW', 'AUTO_LINKED', 'REJECTED', 'MERGED', 'KEPT_SEPARATE', 'ESCALATED', name='pairstatus')
    pair_status_enum.create(op.get_bind(), checkfirst=True)
    
    decision_enum = postgresql.ENUM('MERGE', 'KEEP_SEPARATE', 'ESCALATE', name='decision')
    decision_enum.create(op.get_bind(), checkfirst=True)
    
    user_role_enum = postgresql.ENUM('REVIEWER', 'ADMIN', 'VIEWER', name='userrole')
    user_role_enum.create(op.get_bind(), checkfirst=True)
    
    attribution_status_enum = postgresql.ENUM('ATTRIBUTED', 'PENDING_REVIEW', 'UNATTRIBUTABLE', name='attributionstatus')
    attribution_status_enum.create(op.get_bind(), checkfirst=True)

    # 3. Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=128), nullable=False),
        sa.Column('hashed_password', sa.String(length=256), nullable=False),
        sa.Column('role', user_role_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # 4. Create ubid_registry table
    op.create_table('ubid_registry',
        sa.Column('ubid', sa.String(length=32), nullable=False),
        sa.Column('pan_anchor', sa.String(length=10), nullable=True),
        sa.Column('gstin_anchor', sa.String(length=15), nullable=True),
        sa.Column('anchor_pending', sa.Boolean(), nullable=True),
        sa.Column('status', registry_status_enum, nullable=True),
        sa.Column('status_confidence', sa.Float(), nullable=True),
        sa.Column('status_updated_at', sa.DateTime(), nullable=True),
        sa.Column('linkage_pending', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('ubid')
    )
    op.create_index(op.f('ix_ubid_registry_ubid'), 'ubid_registry', ['ubid'], unique=False)
    op.create_index('ix_ubid_registry_pan_anchor', 'ubid_registry', ['pan_anchor'], unique=False)
    op.create_index('ix_ubid_registry_gstin_anchor', 'ubid_registry', ['gstin_anchor'], unique=False)

    # 5. Create department_records table
    op.create_table('department_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('department', department_enum, nullable=False),
        sa.Column('original_record_id', sa.String(length=128), nullable=False),
        sa.Column('business_name', sa.String(length=512), nullable=False),
        sa.Column('business_name_normalized', sa.String(length=512), nullable=False),
        sa.Column('address_raw', sa.String(length=1024), nullable=False),
        sa.Column('address_street', sa.String(length=512), nullable=True),
        sa.Column('address_locality', sa.String(length=512), nullable=True),
        sa.Column('address_pincode', sa.String(length=10), nullable=False),
        sa.Column('address_district', sa.String(length=128), nullable=True),
        sa.Column('address_lat', sa.Float(), nullable=True),
        sa.Column('address_lng', sa.Float(), nullable=True),
        sa.Column('pan', sa.String(length=10), nullable=True),
        sa.Column('gstin', sa.String(length=15), nullable=True),
        sa.Column('nic_code', sa.String(length=10), nullable=True),
        sa.Column('registration_date', sa.Date(), nullable=True),
        sa.Column('phone', sa.String(length=32), nullable=True),
        sa.Column('email', sa.String(length=256), nullable=True),
        sa.Column('signatory_name', sa.String(length=256), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('ingested_at', sa.DateTime(), nullable=True),
        sa.Column('ubid', sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(['ubid'], ['ubid_registry.ubid'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_department_records_id'), 'department_records', ['id'], unique=False)
    op.create_index(op.f('ix_department_records_department'), 'department_records', ['department'], unique=False)
    op.create_index(op.f('ix_department_records_business_name_normalized'), 'department_records', ['business_name_normalized'], unique=False)
    op.create_index('ix_department_records_pan', 'department_records', ['pan'], unique=False)
    op.create_index('ix_department_records_gstin', 'department_records', ['gstin'], unique=False)
    op.create_index('ix_department_records_address_pincode', 'department_records', ['address_pincode'], unique=False)
    op.create_index(op.f('ix_department_records_ubid'), 'department_records', ['ubid'], unique=False)

    # 6. Create candidate_pairs table
    op.create_table('candidate_pairs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('record_a_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('record_b_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('blocking_signals', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('shap_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('feature_vector', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', pair_status_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['record_a_id'], ['department_records.id'], ),
        sa.ForeignKeyConstraint(['record_b_id'], ['department_records.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_candidate_pairs_id'), 'candidate_pairs', ['id'], unique=False)
    op.create_index(op.f('ix_candidate_pairs_record_a_id'), 'candidate_pairs', ['record_a_id'], unique=False)
    op.create_index(op.f('ix_candidate_pairs_record_b_id'), 'candidate_pairs', ['record_b_id'], unique=False)
    op.create_index(op.f('ix_candidate_pairs_status'), 'candidate_pairs', ['status'], unique=False)

    # 7. Create review_decisions table
    op.create_table('review_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pair_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decision', decision_enum, nullable=False),
        sa.Column('reason', sa.String(length=1024), nullable=False),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('score_at_decision', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['pair_id'], ['candidate_pairs.id'], ),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_review_decisions_id'), 'review_decisions', ['id'], unique=False)
    op.create_index(op.f('ix_review_decisions_pair_id'), 'review_decisions', ['pair_id'], unique=False)
    op.create_index(op.f('ix_review_decisions_reviewer_id'), 'review_decisions', ['reviewer_id'], unique=False)

    # 8. Create business_events table
    op.create_table('business_events',
        sa.Column('event_time', sa.DateTime(), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ubid', sa.String(length=32), nullable=True),
        sa.Column('department', department_enum, nullable=False),
        sa.Column('original_record_id', sa.String(length=128), nullable=False),
        sa.Column('event_type', sa.String(length=128), nullable=False),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('attribution_status', attribution_status_enum, nullable=False),
        sa.Column('attribution_confidence', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['ubid'], ['ubid_registry.ubid'], ),
        sa.PrimaryKeyConstraint('event_time', 'id')
    )
    op.create_index(op.f('ix_business_events_event_time'), 'business_events', ['event_time'], unique=False)
    op.create_index(op.f('ix_business_events_event_type'), 'business_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_business_events_ubid'), 'business_events', ['ubid'], unique=False)

    # 9. Convert business_events to TimescaleDB hypertable
    # Provide explicitly that event_time is the time column. 
    # Use if_not_exists=True to prevent errors on multiple runs.
    op.execute("SELECT create_hypertable('business_events', 'event_time', if_not_exists => TRUE);")

def downgrade() -> None:
    op.drop_table('business_events')
    op.drop_table('review_decisions')
    op.drop_table('candidate_pairs')
    op.drop_table('department_records')
    op.drop_table('ubid_registry')
    op.drop_table('users')

    # Drop ENUMs
    postgresql.ENUM(name='attributionstatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='userrole').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='decision').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='pairstatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='registrystatus').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='department').drop(op.get_bind(), checkfirst=True)
    
    op.execute("DROP EXTENSION IF EXISTS timescaledb CASCADE;")
