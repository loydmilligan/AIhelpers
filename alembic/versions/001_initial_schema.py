"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2025-01-11 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('subscription_tier', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_users')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_subscription_tier', 'users', ['subscription_tier'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    op.create_index('ix_users_subscription_tier_created_at', 'users', ['subscription_tier', 'created_at'])
    op.create_index('ix_users_is_active_created_at', 'users', ['is_active', 'created_at'])

    # Create teams table
    op.create_table('teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('subscription_tier', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('max_members', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name='fk_teams_owner_id_users'),
        sa.PrimaryKeyConstraint('id', name='pk_teams')
    )
    op.create_index('ix_teams_name', 'teams', ['name'])
    op.create_index('ix_teams_owner_id', 'teams', ['owner_id'])
    op.create_index('ix_teams_created_at', 'teams', ['created_at'])
    op.create_index('ix_teams_owner_active', 'teams', ['owner_id', 'is_active'])
    op.create_index('ix_teams_name_active', 'teams', ['name', 'is_active'])

    # Create prompts table
    op.create_table('prompts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False),
        sa.Column('effectiveness_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name='fk_prompts_owner_id_users'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name='fk_prompts_team_id_teams'),
        sa.PrimaryKeyConstraint('id', name='pk_prompts')
    )
    op.create_index('ix_prompts_title', 'prompts', ['title'])
    op.create_index('ix_prompts_category', 'prompts', ['category'])
    op.create_index('ix_prompts_owner_id', 'prompts', ['owner_id'])
    op.create_index('ix_prompts_team_id', 'prompts', ['team_id'])
    op.create_index('ix_prompts_created_at', 'prompts', ['created_at'])
    op.create_index('ix_prompts_owner_category', 'prompts', ['owner_id', 'category'])
    op.create_index('ix_prompts_team_category', 'prompts', ['team_id', 'category'])
    op.create_index('ix_prompts_public_category', 'prompts', ['is_public', 'category'])
    op.create_index('ix_prompts_usage_effectiveness', 'prompts', ['usage_count', 'effectiveness_score'])
    op.create_index('ix_prompts_created_at_active', 'prompts', ['created_at', 'is_active'])

    # Create prompt_versions table
    op.create_table('prompt_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prompt_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_prompt_versions_created_by_users'),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], name='fk_prompt_versions_prompt_id_prompts'),
        sa.PrimaryKeyConstraint('id', name='pk_prompt_versions')
    )
    op.create_index('ix_prompt_versions_prompt_id', 'prompt_versions', ['prompt_id'])
    op.create_index('ix_prompt_versions_created_at', 'prompt_versions', ['created_at'])
    op.create_index('ix_prompt_versions_prompt_version', 'prompt_versions', ['prompt_id', 'version_number'])
    op.create_index('ix_prompt_versions_created_by', 'prompt_versions', ['created_by'])

    # Create session_contexts table
    op.create_table('session_contexts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('ai_tool', sa.String(length=50), nullable=False),
        sa.Column('context_data', sa.JSON(), nullable=False),
        sa.Column('session_metadata', sa.JSON(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_session_contexts_user_id_users'),
        sa.PrimaryKeyConstraint('id', name='pk_session_contexts')
    )
    op.create_index('ix_session_contexts_user_id', 'session_contexts', ['user_id'])
    op.create_index('ix_session_contexts_ai_tool', 'session_contexts', ['ai_tool'])
    op.create_index('ix_session_contexts_created_at', 'session_contexts', ['created_at'])
    op.create_index('ix_session_contexts_user_tool', 'session_contexts', ['user_id', 'ai_tool'])
    op.create_index('ix_session_contexts_tool_created', 'session_contexts', ['ai_tool', 'created_at'])
    op.create_index('ix_session_contexts_user_created', 'session_contexts', ['user_id', 'created_at'])

    # Create context_snapshots table
    op.create_table('context_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_context_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_data', sa.JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_context_id'], ['session_contexts.id'], name='fk_context_snapshots_session_context_id_session_contexts'),
        sa.PrimaryKeyConstraint('id', name='pk_context_snapshots')
    )
    op.create_index('ix_context_snapshots_session_context_id', 'context_snapshots', ['session_context_id'])
    op.create_index('ix_context_snapshots_created_at', 'context_snapshots', ['created_at'])
    op.create_index('ix_context_snapshots_session_created', 'context_snapshots', ['session_context_id', 'created_at'])

    # Create team_members table
    op.create_table('team_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('invited_by', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], name='fk_team_members_invited_by_users'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name='fk_team_members_team_id_teams'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_team_members_user_id_users'),
        sa.PrimaryKeyConstraint('id', name='pk_team_members')
    )
    op.create_index('ix_team_members_user_id', 'team_members', ['user_id'])
    op.create_index('ix_team_members_team_id', 'team_members', ['team_id'])
    op.create_index('ix_team_members_role', 'team_members', ['role'])
    op.create_index('ix_team_members_created_at', 'team_members', ['created_at'])
    op.create_index('ix_team_members_user_team', 'team_members', ['user_id', 'team_id'])
    op.create_index('ix_team_members_team_role', 'team_members', ['team_id', 'role'])
    op.create_index('ix_team_members_active_joined', 'team_members', ['is_active', 'joined_at'])

    # Create user_activities table
    op.create_table('user_activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_user_activities_user_id_users'),
        sa.PrimaryKeyConstraint('id', name='pk_user_activities')
    )
    op.create_index('ix_user_activities_user_id', 'user_activities', ['user_id'])
    op.create_index('ix_user_activities_activity_type', 'user_activities', ['activity_type'])
    op.create_index('ix_user_activities_timestamp', 'user_activities', ['timestamp'])
    op.create_index('ix_user_activities_created_at', 'user_activities', ['created_at'])
    op.create_index('ix_user_activities_user_type', 'user_activities', ['user_id', 'activity_type'])
    op.create_index('ix_user_activities_type_timestamp', 'user_activities', ['activity_type', 'timestamp'])
    op.create_index('ix_user_activities_user_timestamp', 'user_activities', ['user_id', 'timestamp'])

    # Create prompt_analytics table
    op.create_table('prompt_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prompt_id', sa.Integer(), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False),
        sa.Column('effectiveness_score', sa.Float(), nullable=True),
        sa.Column('avg_response_time', sa.Float(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('user_ratings', sa.JSON(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], name='fk_prompt_analytics_prompt_id_prompts'),
        sa.PrimaryKeyConstraint('id', name='pk_prompt_analytics')
    )
    op.create_index('ix_prompt_analytics_prompt_id', 'prompt_analytics', ['prompt_id'], unique=True)
    op.create_index('ix_prompt_analytics_usage_count', 'prompt_analytics', ['usage_count'])
    op.create_index('ix_prompt_analytics_created_at', 'prompt_analytics', ['created_at'])
    op.create_index('ix_prompt_analytics_usage_effectiveness', 'prompt_analytics', ['usage_count', 'effectiveness_score'])
    op.create_index('ix_prompt_analytics_score_updated', 'prompt_analytics', ['effectiveness_score', 'updated_at'])
    op.create_index('ix_prompt_analytics_last_used', 'prompt_analytics', ['last_used'])

    # Create usage_metrics table
    op.create_table('usage_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_data', sa.JSON(), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name='fk_usage_metrics_team_id_teams'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_usage_metrics_user_id_users'),
        sa.PrimaryKeyConstraint('id', name='pk_usage_metrics')
    )
    op.create_index('ix_usage_metrics_metric_name', 'usage_metrics', ['metric_name'])
    op.create_index('ix_usage_metrics_date', 'usage_metrics', ['date'])
    op.create_index('ix_usage_metrics_user_id', 'usage_metrics', ['user_id'])
    op.create_index('ix_usage_metrics_team_id', 'usage_metrics', ['team_id'])
    op.create_index('ix_usage_metrics_created_at', 'usage_metrics', ['created_at'])
    op.create_index('ix_usage_metrics_name_date', 'usage_metrics', ['metric_name', 'date'])
    op.create_index('ix_usage_metrics_user_date', 'usage_metrics', ['user_id', 'date'])
    op.create_index('ix_usage_metrics_team_date', 'usage_metrics', ['team_id', 'date'])
    op.create_index('ix_usage_metrics_name_value', 'usage_metrics', ['metric_name', 'metric_value'])


def downgrade() -> None:
    op.drop_table('usage_metrics')
    op.drop_table('prompt_analytics')
    op.drop_table('user_activities')
    op.drop_table('team_members')
    op.drop_table('context_snapshots')
    op.drop_table('session_contexts')
    op.drop_table('prompt_versions')
    op.drop_table('prompts')
    op.drop_table('teams')
    op.drop_table('users')