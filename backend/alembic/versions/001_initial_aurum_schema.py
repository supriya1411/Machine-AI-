"""Initial AURUM schema

Revision ID: 001_initial_aurum_schema
Revises: 
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_aurum_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Sites
    op.create_table(
        'sites',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), unique=True, nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # 2. Roles
    op.create_table(
        'roles',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=100), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 3. Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), unique=True, nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role_id', sa.String(length=36), sa.ForeignKey('roles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE'),
        sa.Column('site_id', sa.String(length=36), sa.ForeignKey('sites.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # 4. Assets
    op.create_table(
        'assets',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('asset_id', sa.String(length=100), unique=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('serial_number', sa.String(length=100), unique=True, nullable=True),
        sa.Column('manufacturer', sa.String(length=100), nullable=True),
        sa.Column('site_id', sa.String(length=36), sa.ForeignKey('sites.id', ondelete='CASCADE'), nullable=False),
        sa.Column('floor', sa.String(length=50), nullable=True),
        sa.Column('installation_date', sa.Date(), nullable=True),
        sa.Column('warranty_expiry', sa.Date(), nullable=True),
        sa.Column('criticality', sa.String(length=50), server_default='MEDIUM'),
        sa.Column('status', sa.String(length=50), server_default='OPERATIONAL'),
        sa.Column('health_score', sa.Float(), server_default='100.0'),
        sa.Column('risk_score', sa.Float(), server_default='0.0'),
        sa.Column('risk_level', sa.String(length=50), server_default='LOW'),
        sa.Column('last_risk_assessment', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # 5. Fault Categories
    op.create_table(
        'fault_categories',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('code', sa.String(length=100), unique=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('severity', sa.String(length=50), server_default='MEDIUM'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 6. Service Calls
    op.create_table(
        'service_calls',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('asset_id', sa.String(length=36), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('raw_fault', sa.Text(), nullable=False),
        sa.Column('normalized_fault_id', sa.String(length=36), sa.ForeignKey('fault_categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('fault_code', sa.String(length=100), nullable=True),
        sa.Column('severity', sa.String(length=50), server_default='MEDIUM'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('engineer_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('downtime', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 7. Sensor Devices
    op.create_table(
        'sensor_devices',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('asset_id', sa.String(length=36), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_id', sa.String(length=100), unique=True, nullable=False),
        sa.Column('sensor_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ONLINE'),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('configuration', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 8. Sensor Readings
    op.create_table(
        'sensor_readings',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('sensor_id', sa.String(length=36), sa.ForeignKey('sensor_devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False)
    )

    # 9. Sensor Anomalies
    op.create_table(
        'sensor_anomalies',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('sensor_id', sa.String(length=36), sa.ForeignKey('sensor_devices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('threshold_breached', sa.String(length=100), nullable=False),
        sa.Column('duration_minutes', sa.Float(), server_default='0.0'),
        sa.Column('resolved', sa.String(length=10), server_default='FALSE'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 10. Contracts
    op.create_table(
        'contracts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('contract_id', sa.String(length=100), unique=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('customer', sa.String(length=255), nullable=False),
        sa.Column('vendor', sa.String(length=255), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('value', sa.Float(), server_default='0.0'),
        sa.Column('pm_frequency_days', sa.Integer(), server_default='90'),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE'),
        sa.Column('compliance_score', sa.Float(), server_default='100.0'),
        sa.Column('renewal_risk', sa.String(length=50), server_default='LOW'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # 11. Contract Assets
    op.create_table(
        'contract_assets',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('contract_id', sa.String(length=36), sa.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_id', sa.String(length=36), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 12. Maintenance
    op.create_table(
        'maintenance',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('asset_id', sa.String(length=36), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contract_id', sa.String(length=36), sa.ForeignKey('contracts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('pm_type', sa.String(length=100), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('completed_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='SCHEDULED'),
        sa.Column('engineer_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('evidence_document_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # 13. Work Orders
    op.create_table(
        'work_orders',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('asset_id', sa.String(length=36), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(length=50), server_default='CORRECTIVE'),
        sa.Column('priority', sa.String(length=50), server_default='MEDIUM'),
        sa.Column('assigned_engineer_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='OPEN'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # 14. Alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=50), server_default='MEDIUM'),
        sa.Column('asset_id', sa.String(length=36), sa.ForeignKey('assets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('sensor_id', sa.String(length=36), sa.ForeignKey('sensor_devices.id', ondelete='SET NULL'), nullable=True),
        sa.Column('contract_id', sa.String(length=36), sa.ForeignKey('contracts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('current_value', sa.String(length=100), nullable=True),
        sa.Column('threshold', sa.String(length=100), nullable=True),
        sa.Column('duration', sa.String(length=100), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True)
    )

    # 15. Documents
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), server_default='0'),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('uploaded_by', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 16. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('actor_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('changes', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('documents')
    op.drop_table('alerts')
    op.drop_table('work_orders')
    op.drop_table('maintenance')
    op.drop_table('contract_assets')
    op.drop_table('contracts')
    op.drop_table('sensor_anomalies')
    op.drop_table('sensor_readings')
    op.drop_table('sensor_devices')
    op.drop_table('service_calls')
    op.drop_table('fault_categories')
    op.drop_table('assets')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('sites')
