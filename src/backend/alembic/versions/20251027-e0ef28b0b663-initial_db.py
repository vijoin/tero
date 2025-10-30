"""initial-db

Revision ID: e0ef28b0b663
Revises: 
Create Date: 2025-10-27 19:14:55.121451

"""
import sqlalchemy as sa
import sqlmodel
from typing import Sequence, Union
from alembic import op
from sqlalchemy.dialects import postgresql

from tero.core.env import env

# revision identifiers, used by Alembic.
revision: str = 'e0ef28b0b663'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sa.Enum('PENDING', 'RUNNING', 'SUCCESS', 'FAILURE', 'ERROR', name='testcaseresultstatus').create(op.get_bind())
    sa.Enum('BEARER', name='tooloauthtokentype').create(op.get_bind())
    sa.Enum('PROMPT_TOKENS', 'COMPLETION_TOKENS', 'PDF_PARSING', 'WEB_SEARCH', 'WEB_EXTRACT', 'EMBEDDING_TOKENS', name='usagetype').create(op.get_bind())
    sa.Enum('USER', 'AGENT', name='threadmessageorigin').create(op.get_bind())
    sa.Enum('BASIC', 'ENHANCED', name='fileprocessor').create(op.get_bind())
    sa.Enum('PENDING', 'PROCESSED', 'ERROR', 'QUOTA_EXCEEDED', name='filestatus').create(op.get_bind())
    sa.Enum('LOW', 'MEDIUM', 'HIGH', name='reasoningeffort').create(op.get_bind())
    sa.Enum('CREATIVE', 'NEUTRAL', 'PRECISE', name='llmtemperature').create(op.get_bind())
    sa.Enum('ACCEPTED', 'PENDING', 'REJECTED', name='teamrolestatus').create(op.get_bind())
    sa.Enum('TEAM_OWNER', 'TEAM_MEMBER', name='role').create(op.get_bind())
    sa.Enum('REASONING', 'CHAT', name='llmmodeltype').create(op.get_bind())
    op.create_table(
        'external_agent',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sqlmodel.AutoString(length=30), nullable=True),
        sa.Column('icon', sa.LargeBinary(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table(
        'jira_tool_config',
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('cloud_id', sqlmodel.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint('agent_id')
    )
    op.create_table(
        'llm_model',
        sa.Column('id', sqlmodel.AutoString(length=20), nullable=False),
        sa.Column('name', sqlmodel.AutoString(length=30), nullable=False),
        sa.Column('description', sqlmodel.AutoString(length=200), nullable=False),
        sa.Column('model_type', postgresql.ENUM('REASONING', 'CHAT', name='llmmodeltype', create_type=False), nullable=False),
        sa.Column('token_limit', sa.Integer(), nullable=False),
        sa.Column('output_token_limit', sa.Integer(), nullable=False),
        sa.Column('prompt_1k_token_usd', sa.Float(), nullable=False),
        sa.Column('completion_1k_token_usd', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'team',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sqlmodel.AutoString(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'tool_oauth_client_info',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sqlmodel.AutoString(), nullable=False),
        sa.Column('client_id', sqlmodel.AutoString(), nullable=False),
        sa.Column('client_secret', sqlmodel.AutoString(), nullable=False),
        sa.Column('scope', sqlmodel.AutoString(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'agent_id', 'tool_id')
    )
    op.create_index(op.f('ix_tool_oauth_client_info_updated_at'), 'tool_oauth_client_info', ['updated_at'], unique=False)
    op.create_table(
        'tool_oauth_state',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sqlmodel.AutoString(), nullable=False),
        sa.Column('state', sqlmodel.AutoString(), nullable=False),
        sa.Column('code_verifier', sqlmodel.AutoString(), nullable=False),
        sa.Column('token_endpoint', sqlmodel.AutoString(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'tool_id', 'state')
    )
    op.create_index(op.f('ix_tool_oauth_state_agent_id'), 'tool_oauth_state', ['agent_id'], unique=False)
    op.create_index(op.f('ix_tool_oauth_state_updated_at'), 'tool_oauth_state', ['updated_at'], unique=False)
    op.create_table(
        'tool_oauth_token',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sqlmodel.AutoString(), nullable=False),
        sa.Column('access_token', sqlmodel.AutoString(), nullable=False),
        sa.Column('token_type', postgresql.ENUM('BEARER', name='tooloauthtokentype', create_type=False), nullable=False),
        sa.Column('expires_in', sa.Integer(), nullable=True),
        sa.Column('scope', sqlmodel.AutoString(), nullable=True),
        sa.Column('refresh_token', sqlmodel.AutoString(), nullable=True),
        sa.Column('expires_at', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'agent_id', 'tool_id')
    )
    op.create_index(op.f('ix_tool_oauth_token_updated_at'), 'tool_oauth_token', ['updated_at'], unique=False)
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sqlmodel.AutoString(length=50), nullable=False),
        sa.Column('name', sqlmodel.AutoString(length=100), nullable=True),
        sa.Column('monthly_usd_limit', sa.Integer(), nullable=False),
        sa.Column('monthly_hours', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_name'), 'user', ['name'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=False)
    op.create_table(
        'agent',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sqlmodel.AutoString(length=30), nullable=True),
        sa.Column('description', sqlmodel.AutoString(length=100), nullable=True),
        sa.Column('icon_bg_color', sqlmodel.AutoString(length=6), nullable=True),
        sa.Column('last_update', sa.DateTime(), nullable=False),
        sa.Column('icon', sa.LargeBinary(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('model_id', sqlmodel.AutoString(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('temperature', postgresql.ENUM('CREATIVE', 'NEUTRAL', 'PRECISE', name='llmtemperature', create_type=False), nullable=False),
        sa.Column('reasoning_effort', postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', name='reasoningeffort', create_type=False), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['model_id'], ['llm_model.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_team_last_update', 'agent', ['team_id', 'last_update'], unique=False)
    op.create_index(op.f('ix_agent_user_id'), 'agent', ['user_id'], unique=False)
    op.create_index('ix_agent_user_id_last_update', 'agent', ['user_id', 'last_update'], unique=False)
    op.create_table(
        'external_agent_time_saving',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('external_agent_id', sa.Integer(), nullable=False),
        sa.Column('minutes_saved', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['external_agent_id'], ['external_agent.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_external_agent_time_saving_external_agent_id'), 'external_agent_time_saving', ['external_agent_id'], unique=False)
    op.create_index(op.f('ix_external_agent_time_saving_user_id'), 'external_agent_time_saving', ['user_id'], unique=False)
    op.create_table(
        'file',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sqlmodel.AutoString(length=200), nullable=False),
        sa.Column('content_type', sqlmodel.AutoString(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('content', sa.LargeBinary(), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'PROCESSED', 'ERROR', 'QUOTA_EXCEEDED', name='filestatus', create_type=False), nullable=False),
        sa.Column('processed_content', sqlmodel.AutoString(), nullable=True),
        sa.Column('file_processor', postgresql.ENUM('BASIC', 'ENHANCED', name='fileprocessor', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_status'), 'file', ['status'], unique=False)
    op.create_index(op.f('ix_file_timestamp'), 'file', ['timestamp'], unique=False)
    op.create_table(
        'team_role',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('role', postgresql.ENUM('TEAM_OWNER', 'TEAM_MEMBER', name='role', create_type=False), nullable=True),
        sa.Column('status', postgresql.ENUM('ACCEPTED', 'PENDING', 'REJECTED', name='teamrolestatus', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'team_id')
    )
    op.create_index(op.f('ix_team_role_team_id'), 'team_role', ['team_id'], unique=False)
    op.create_index(op.f('ix_team_role_user_id'), 'team_role', ['user_id'], unique=False)
    op.create_table(
        'agent_prompt',
        sa.Column('name', sqlmodel.AutoString(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('shared', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('last_update', sa.DateTime(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('starter', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agent.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_prompt_agent_id_user_id_shared', 'agent_prompt', ['agent_id', 'user_id', 'shared'], unique=False)
    op.create_index(op.f('ix_agent_prompt_shared'), 'agent_prompt', ['shared'], unique=False)
    op.create_index('ix_agent_prompt_user_id_last_update_shared', 'agent_prompt', ['user_id', 'last_update', 'shared'], unique=False)
    op.create_table(
        'agent_tool_config',
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sqlmodel.AutoString(length=60), nullable=False),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('draft', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agent.id'], ),
        sa.PrimaryKeyConstraint('agent_id', 'tool_id')
    )
    op.create_index(op.f('ix_agent_tool_config_draft'), 'agent_tool_config', ['draft'], unique=False)
    op.create_table(
        'agent_tool_config_file',
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sqlmodel.AutoString(length=60), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agent.id'], ),
        sa.ForeignKeyConstraint(['file_id'], ['file.id'], ),
        sa.PrimaryKeyConstraint('agent_id', 'tool_id', 'file_id')
    )
    op.create_table(
        'doc_tool_config',
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('description', sqlmodel.AutoString(length=200), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agent.id'], ),
        sa.PrimaryKeyConstraint('agent_id')
    )
    op.create_table(
        'doc_tool_file',
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column('description', sqlmodel.AutoString(length=200), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agent.id'], ),
        sa.ForeignKeyConstraint(['file_id'], ['file.id'], ),
        sa.PrimaryKeyConstraint('agent_id', 'file_id')
    )
    op.create_table(
        'thread',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sqlmodel.AutoString(length=80), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('deleted', sa.Boolean(), nullable=False),
        sa.Column('creation', sa.DateTime(), nullable=False),
        sa.Column('is_test_case', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agent.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_thread_user_id'), 'thread', ['user_id'], unique=False)
    op.create_index('ix_thread_user_id_agent_id_creation', 'thread', ['user_id', 'agent_id', 'creation', 'is_test_case'], unique=False)
    op.create_table(
        'usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('model_id', sqlmodel.AutoString(length=30), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('usd_cost', sa.Float(), nullable=False),
        sa.Column('type', postgresql.ENUM('PROMPT_TOKENS', 'COMPLETION_TOKENS', 'PDF_PARSING', 'WEB_SEARCH', 'WEB_EXTRACT', 'EMBEDDING_TOKENS', name='usagetype', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agent.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_agent_id'), 'usage', ['agent_id'], unique=False)
    op.create_index(op.f('ix_usage_model_id'), 'usage', ['model_id'], unique=False)
    op.create_index(op.f('ix_usage_timestamp'), 'usage', ['timestamp'], unique=False)
    op.create_index(op.f('ix_usage_user_id'), 'usage', ['user_id'], unique=False)
    op.create_table(
        'user_agent',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('creation', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agent.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'agent_id')
    )
    op.create_index('ix_user_agent_user_id_creation', 'user_agent', ['user_id', 'creation'], unique=False)
    op.create_table(
        'test_case',
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('last_update', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agent.id'], ),
        sa.ForeignKeyConstraint(['thread_id'], ['thread.id'], ),
        sa.PrimaryKeyConstraint('thread_id')
    )
    op.create_index('ix_test_case_agent_id_last_update', 'test_case', ['agent_id', 'last_update'], unique=False)
    op.create_table(
        'thread_message',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('origin', postgresql.ENUM('USER', 'AGENT', name='threadmessageorigin', create_type=False), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('stopped', sa.Boolean(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('minutes_saved', sa.Integer(), nullable=True),
        sa.Column('feedback_text', sqlmodel.AutoString(), nullable=True),
        sa.Column('has_positive_feedback', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['thread_message.id'], ),
        sa.ForeignKeyConstraint(['thread_id'], ['thread.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_thread_message_parent_id'), 'thread_message', ['parent_id'], unique=False)
    op.create_index(op.f('ix_thread_message_thread_id'), 'thread_message', ['thread_id'], unique=False)
    op.create_index('ix_thread_message_thread_id_timestamp', 'thread_message', ['thread_id', 'timestamp'], unique=False)
    op.create_table(
        'test_case_result',
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('test_case_id', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'RUNNING', 'SUCCESS', 'FAILURE', 'ERROR', name='testcaseresultstatus', create_type=False), nullable=False),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_case.thread_id'], ),
        sa.ForeignKeyConstraint(['thread_id'], ['thread.id'], ),
        sa.PrimaryKeyConstraint('thread_id')
    )
    op.create_index('ix_test_case_result_test_case_id_executed_at', 'test_case_result', ['test_case_id', 'executed_at'], unique=False)
    op.create_table(
        'thread_message_file',
        sa.Column('thread_message_id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['file_id'], ['file.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['thread_message_id'], ['thread_message.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('thread_message_id', 'file_id')
    )
    op.create_index(op.f('ix_thread_message_file_file_id'), 'thread_message_file', ['file_id'], unique=False)
    op.create_index(op.f('ix_thread_message_file_thread_message_id'), 'thread_message_file', ['thread_message_id'], unique=False)

    op.execute("""
        INSERT INTO llm_model(id, name, description, token_limit, output_token_limit, prompt_1k_token_usd, completion_1k_token_usd, model_type)
        VALUES 
            ('gpt-4o', 'GPT-4o', 'This is a good model for relatively complex tasks. This is more powerful than GPT-4o Mini, but slower and 17x more expensive.', 128000, 16384, 0.0025, 0.01, 'CHAT'),
            ('gpt-4o-mini', 'GPT-4o Mini', 'This is a good model for simple tasks like summaries, simple questions, etc.', 128000, 16384, 0.00015, 0.0006, 'CHAT'),
            ('gpt-4.1', 'GPT-4.1', 'This is a new model that is good for coding and will replace GPT-4o in the short term.', 1047576, 32768, 0.002, 0.008, 'CHAT'),
            ('gpt-4.1-nano', 'GPT-4.1 Nano', 'This is a new model that will replace GPT-4o Mini in the short term.', 1047576, 32768, 0.0001, 0.0004, 'CHAT'),
            ('o4-mini', 'O4 Mini', 'This is a reasoning model that is good for coding, math and some complex tasks. This model is slower than GPT-4o, but half the cost.', 200000, 100000, 0.0011, 0.0044, 'REASONING'),
            ('claude-sonnet-4', 'Claude Sonnet 4', 'This is a similar model to GPT-4o but with better reasoning. Good for complex analysis, coding, and creative writing. 20% more expensive than GPT-4o.', 200000, 64000, 0.003, 0.015, 'CHAT'),
            ('gemini-2.5-pro', 'Gemini 2.5 Pro', 'This is an advanced reasoning model, outperforming GPT-4o with a larger context while being more affordable.', 1048576, 65536, 0.00125, 0.01, 'CHAT'),
            ('gemini-2.5-flash', 'Gemini 2.5 Flash', 'This is a fast and efficient model, comparable to GPT-4.1 Nano, optimized for speed while maintaining high quality responses.', 1048576, 65536, 0.0003, 0.0025, 'CHAT'),
            ('gpt-5', 'GPT-5', 'This is the best reasoning model for coding and complex agentic tasks from OpenAI. It will replace GPT-4o and GPT-4.1 in the short term.', 400000, 128000, 0.00125, 0.002, 'REASONING'),
            ('gpt-5-mini', 'GPT-5 Mini', 'This is a new reasoning model that will replace GPT-4o Mini in the short term. It has a good balance between cost and intelligence.', 400000, 128000, 0.00025, 0.0004, 'REASONING'),
            ('gpt-5-nano', 'GPT-5 Nano', 'This is a new reasoning model that will replace GPT-4.1 Nano in the short term.', 400000, 128000, 0.00005, 0.0044, 'REASONING')
    """)
    op.execute("INSERT INTO team(name) VALUES ('Default')")
    
    system_prompt = """You are a helpful AI assistant.
        Use provided tools and information provided in context to answer user questions.
        Avoid generating responses that are not based on tools or previous context.
        Provide short, concise and correct answers.
        Answer in the same language as the user.
        Use markdown to format your responses. You can include code blocks, tables, plantuml diagrams code blocks, echarts configuration code blocks and any standard markdown format
        """
    icon = "89504e470d0a1a0a0000000d49484452000000300000003008060000005702f987000006f949444154789ced996b48d3df1fc75f6d59a9f3b766d8522a6f212229255dd0f04217f5c1c08452d7d568925a11c32e145a89d513abed4194e0a54549525a4af620231153831e549264583953b0ccc2db96a86dfb3f10bf34bc6c5e7e7ff9816f38b07d3e9ff339ef3767e79ccf395b6030182cfc87219a6b0233c5bc80b9c6bc80b9c6bc80b9c6ac09d0e974ecdfbf1f89442234a552c9d1a347676b8871b160a607d9a3478fb874e912cdcdcd93c6555757b361c386990c352e6634030f1f3ee4c0810334373713131343797939068341683f7ffe44a55201101919895c2eb79a218944427e7e3e1f3e7c98368719cdc0aa55abe8eeeee6c58b176cdebc798cdf6c36535959c9eeddbbb1584686f1f6f6c6cfcf8fb6b6369a9a9a84d8bcbc3c12131359b060c194382c9c2ef9952b57d2d3d3435555159b366d1ae37ffbf62d616161c2f7f5ebd7f3f2e5cb3171515151d4d7d7939c9c4c77773769696953e231ad19181c1cc4cdcd0db3d98cc160b0f2f5f7f71310104077773700cb972fa7b1b1112727a709f3994c2664321966b399828202121212ece632ad3510121282d96c66ddba7556768d468387878740beb7b79796969649c90388c562a1cfe1c387a7c4654a02020303914824c28e535c5c2cf84e9d3a45666626168b851b376e603018108bc556fd8f1c39828b8b0b72b99c13274e8c1111181808c09d3b77665fc0dab56bd1ebf5009496968ef18f2ed2dada5a929292ac7c070f1ec4c3c383a2a2222c160b46a391828202366edc28f403b870e10200c3c3c3b32b20313191d6d656828383e9eaea1af3d3f91bab57af163e0f0c0ce0e7e7476969297d7d7da4a6a6f2eedd3b1a1a1a58b162054d4d4db8b8b8b077ef5e8c462331313100fcf8f163f60494949450515181979717353535383a3ada4caad7eb51a954b8b9b9d1d1d10140454505393939ac59b3065f5f5f3e7ffeccd5ab5701282f2f472e9773f2e44900a452e9ec0978fefc39009999997625bc72e50a818181141717b368d122162d5a048042a1e0cc993356b1292929f4f6f6a256ab118944e4e6e602b078f162bb056030182c9335c00258d9be7cf962012c1f3f7e146c29292942ac4c26b3a8d56ac1a756ab2daeaeae825fa7d38d3b567c7cbc10f3ead5ab49798d36bbd6804864ff66a55028686f6f273b3b5bb0656767d3d6d6c6ae5dbb00484a4a62cb962dbc79f3c6aa6f616121a74f9f06e0e2c58b768d37eb026edebc39a14fa7d301b070e1421a1a1a080f0fc7d7d7975fbf7e0931e7cf9f2728288867cf9e919e9e6e9b9b3da4fefcf933aedddfdf9fa1a1217b525841a552515c5c8c9393139d9d9d787a7ad2d9d929f80b0b0b01e8eaeab299cba6803d7bf60070f6ecd971fdeeeeee545454d845fc6f28140abe7dfb262cecf6f676c1e7efef0f8c94eab66053c0685d72f7ee5dc12697cbe9ebeb23393999c1c141121313851d642a108bc51c3a7408c0ea400358b264895d396c0ad8b66d1b090909f4f4f4586da52291088d46434d4d0da1a1a1825da9544e984ba150d8450aec3f8ded5a0319191988c562341a0d212121566b22383898caca4a2a2b2b91c964d4d5d521954a85430946ea24994c467575b5dd024c26d3ec09f0f6f6e6dab56b00bc7fff9ea54b97929999497f7fbf10131a1a4a7b7b3b595959984c26727373717575c5d5d5955bb76e313c3c4c5656965da40a0a0a00d8b76fdfec08f81ba355a446a3c1dddd1dad566be54f4f4fa7acac0c80a1a121868686502a957cfffeddae6dd162b170eedc390076eedc69337eca022e5fbe8cc160202e2e0e914844464606128984a74f9ff2e9d327d2d3d38581636363e9eaea222f2f0f8944623377636323e1e1e1188d4652535385e26e324cf94af9e0c103e2e3e3855d69ebd6adbc7efddaea16f5cf3fffa0d56a898f8fb7eadbd2d23261def2f2726136bdbcbcc8c9c9b18b8fdd33e0ecec0cc0f5ebd7adec555555b4b6b622954a717676262d2d8d8e8e0e2bf2bf7fff262e2e8ea0a02060fc626d94fcf1e3c7696c6cb497d6d4eec42e2e2e582c167a7b7bc7dcb62682c96412ca639148445656166ab55af01f3b760c9d4e47595919dbb76fb79bf828a6b406eeddbb07804c26b3b9cdb5b5b5e1e3e3239057a9547476765a918791fa48241211111131152a02a62420363696fcfc7ccc663352a994b0b0b03127a8c96422242484808000e166555f5f8f56ab1d7319aaafaf07461ebd1c1c1ca625605acf2af7efdf273939d9cae6e3e3835eaf1704393a3a525454445454d4b839eaeaea888e8e66d9b2657cfdfa751ad44730ad6715a55289c16040abd50a0bb2a5a5058bc522bc7f0e0c0cf0f8f1636edfbe6dd5f7c99327ecd8b183e8e8681c1c1cec2ad826c38c1f77c7835eaf179e4826829f9f1fb5b5b536df8c6ce15f11308ad1a7f59292128c46239e9e9e44464612111131e68c982efe5501ff0fccff4333d7981730d7981730d7f8cf0bf81f572d23a0b21861bb0000000049454e44ae426082"
    icon_white = "89504e470d0a1a0a0000000d49484452000000300000003008060000005702f987000006f249444154789ced996d48936d1bc77f7bd18c55708b8608d1d81c3ad00c7a81b240044565cb340bc24453520bad34234db0a2840c5151894033c5b2a8d474233fd88b65602515342d539717447dc83e0452be6fcf07f17a9edd6adbd4fb911bfcc3053bcff3388ff3ffbfceb7e3b826d9b871a3957f31a4cb4d60b15811b0dc5811b0dc5811b0dc902f95a3bd7bf7b26bd72e2222225028144c4c4cd0d8d808c0993367966a9859902cf622f3f4f4e4ce9d3ba8d5ea3fda0507072308c262869a138b5a42818181747676a256abe9eaea22252505a552293e3b76ece0f6eddb00b4b7b7d3d6d6862008364f5c5c1c72f9c217c2a266e0eddbb7b8bbbbb37fff7ebababae6b4090e0ea6aaaa4a24393c3cccc78f1fd16834fcf5d75fa25d565696b8e49cc182a5d7d5d5e1eeee4e7c7cfc9ce4fdfdfd311a8d62b9a7a7079d4e87d56afbbe0c060301010114171763b55a696a6a728ac78266402e97d3d7d787542a45a954dab4b9b9b951565646585818003f7efc20323292efdfbfcfeb4f2693d1dfdf8f542a2523230383c1e0309705ed8183070f22954a676dcab4b4343e7cf8209257abd56cddbaf58fe401a6a6a6d068340094959539c5c529011515150882c0c58b1781692133c8cfcf27272707a9548ad168c4c7c787a9a9299bfe172e5ca0afaf8f9e9e1ee2e2e26689e8eded452291101b1bbbf4023a3a3ad0e974009c3a756ab623e9b42b9d4e477a7a3a939393625b5151112693898484045c5d5d512814141414d0dcdc6ce3a3a2a2028055ab562dad804b972eb161c3064c2613e1e1e13c7ffe7c5edbaf5fbf8abfdddcdca8acac24363696b56bd752535343484888f886030303110481ab57af2293c9c44daf50281c1660f7140a0909e1d0a1434c4e4e12151585c562c1d3d3f38f7dd6af5f4f6e6e2ed1d1d1625d626222ededed007cfefc19a55249525212f9f9f9444646121919c98d1b37006c66cf1eecce40787838303d0b168bc5aec3a4a4245ebf7e4d7474341313134c4c4c00505353437a7aba8d6d7575355aad966bd7ae0170f8f06100c6c6c6964ec081030744028e20232383b1b131ae5fbf8e46a341a3d1505555c5e8e828d9d9d90c0c0cb07bf76ed17e646484cb972fa3542ae9e8e800a0a0a0005f5fdfa5110038f4e667f0ead52b7c7d7dc5930aa667cfcfcf8f8e8e0ee47239757575dcbd7b974d9b36d9f48d8f8f17377246468643e32db980b4b4b479dbe2e3e301b05aad6cdfbe9d9696166eddba65130b151515313434844ea7232525c5ee780e09982fd832180cc86432475cd8a0b6b69623478e30323242505010030303360743494909007e7e7e767dd915d0d0d00030ebe201f0f0f0a0bbbb9bd0d05087c9cfa0adad0d7f7f7f06060600f0f6f616dbeaebeb01888989b1ebc7ae8077efde0170f2e449b16e686808ad56cbd0d010ab57afa6b2b292848404a704c0f4ed3bb3ac2412894ddbf8f8b8433eec0ab879f32646a3114f4f4fb2b3b3c5fa919111b66ddbc69e3d7b78f3e68d48606613ce85eaea6a8748c17f6f76bb768e1895979703909e9e4e6565a54ddbfbf7efd9b76f1fc9c9c9582c16828282e8e9e921373757b4c9cdcda5bbbb9b90901047f93b9ce43824e0d3a74fe4e5e501101a1a8a2008e4e4e4e0eaea2ada3c7efc18954a456969290a8582d4d454fafbfbe9efef27353595356bd6505a5aea10a99998cb9104c7e9707ae6424b4b4ba3afaf8fc4c4449bf6d2d252314a757171c1c5c585a6a6268282821c1690959505c0d3a74fedda3a2de0fcf9f3f8f8f8f0f0e143b12c08025aad16954ac5b973e7c43cb8b3b3133f3f3f3233336d82bcf9e0e6e6464b4b0b2a958ad6d65687121ba753ca8888085a5b5b3976ec1800cdcdcd040606d2dada2ada0c0f0ff3e8d1233233336dfafe3d7bfb5ff8fafaf2e0c10300be7cf9c2d1a3471de2e3f00c8c8e8e0270fcf8719bfaa8a8284e9c38c1af5fbf181f1fa7b6b6968080001bf2128984acac2c311afd7b5e0c50585808406f6faf4dac640f4ee5c4838383482412d46af5ac6c6b3ec86432cc6633301d925cb972458c3e61fa64cbcecee6debd7b9c3e7dda61e233704a805eafa7bcbc1c8bc58246a3f9a38875ebd6f1e4c9133c3c3c00309bcde8f57a7efffe6d63270802168b05ad56eb54183d03a7f680c160402e9753525282d96cc66432a1d7eb67d9198d46fcfdfdc5b25eafc76432cdb2dbbc793330bd6716421e16f85925262686e2e262b1fceddb37044140a552e1e5e5054c2f97e4e4649e3d7b366734bb65cb161a1a1af8f9f3a728642158d06795c6c6467c7c7cc4cbcddbdb9b9d3b77e2e5e5c5e0e0e0b463a994d0d0d059097a585818f5f5f5629078f6ecd905938725f8b83b17944aa578e2cc07b3d94c5e5e1e2f5fbe5cd458ff8880191416162297cb898e8e462a9562b55a696e6ee6c58b17dcbf7f7f49c6f84705fc3ff0afff876645c0726345c0726345c072e33fa0ed986c6017b4a40000000049454e44ae426082"
    
    op.execute(f"""
        INSERT INTO agent (name, description, icon, last_update, model_id, system_prompt, temperature, reasoning_effort, team_id)
        VALUES 
            ('GPT-5 Nano', 'I can help you with simple questions and tasks by using GPT-5 Nano.', '\\x{icon_white}', NOW(), 'gpt-5-nano', '{system_prompt}', 'NEUTRAL', 'MEDIUM', 1),
            ('GPT-5', 'I can help you with general questions and tasks by using GPT-5.', '\\x{icon}', NOW(), 'gpt-5', '{system_prompt}', 'NEUTRAL', 'MEDIUM', 1)
    """)
    op.execute("""
        INSERT INTO external_agent (name, icon)
        VALUES
            ('ChatGPT', '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'),
            ('Claude', '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'),
            ('Google Gemini', 'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAAAXNSR0IB2cksfwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAEtQTFRFAAAAICAgICAgICAgHh4eHh4eHx8fHx8fHx8fHR0dHBwcHh4eHx8fHh4eHx8fICAgHh4eHh4eGxsbHx8fHR0dICAgHh4eICAgICAgVPHvGQAAABl0Uk5TABAgMICQv//vUECgr4/ff3+fMMBgULBAgMMExMgAAAE1SURBVHic1ZZRc4IwDMeTgnSFgT7o5vf/dm63Qw8PUZFO9EBaEjV3vtgHoEd+zT9p0xZB2PB9AMRGBgRwkgEhHmVABAcZoHFvJYBpICglQFLDZCsA0jaAvQDIWuMDGQQN6PYRFU8DanJ5kWFTAKZX+bogRBHAtOo/zfoJYGBPESPAsSdy6wMYuf147cXhAXHoD6m3bmEMgVlFrzeH6QE0iqmA1nG1cwA1K1DRo/fNBia3HYAKp/TavClJMLfNUBIsypq1zvCnE+BkSRmKaeqhWi+t6nOUVrNyvfnevYkLy/sTB7DMne7DpeERp1FQVD0knVWcj3++ooAAvq9VcKT24zubACWIAz4s54ABUFvZRgZfG0YRB5zDzn4lwFkTrYg/UNI/GTBHWtHrDkVlmRp/o6sD2/4BwkhZMf86Cz0AAAAASUVORK5CYII='),
            ('Cursor', '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'),
            ('Github Copilot', 'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAAAXNSR0IB2cksfwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAiVQTFRFAAAAICAgHR0dHh4eHx8fHx8fHx8fHx8fHx8fHx8fHh4eHR0dICAgHR0dHh4eHh4eHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fICAgICAgHx8fHx8fICAgHx8fHx8fHx8fHx8fHx8fHx8fHh4eHx8fHx8fHx8fHx8fHx8fHx8fHx8fICAgHx8fICAgHx8fHx8fHh4eHBwcHx8fICAgHx8fHh4eICAgHx8fHx8fHh4eICAgHh4eHh4eHh4eHx8fHx8fHx8fHx8fHx8fHx8fHx8fHh4eHh4eHh4eHx8fHx8fICAgHx8fHx8fHx8fHx8fHBwcHx8fHx8fHx8fHx8fHx8fHx8fHh4eHx8fHx8fHR0dHx8fHx8fHR0dHh4eHh4eHBwcHh4eHx8fHR0dHh4eHBwcHR0dHh4eHx8fHx8fHh4eHBwcHR0dHh4eHx8fHh4eHR0dHx8fHx8fHx8fHx8fHx8fHx8fHx8fHx8fHR0dICAgHh4eHx8fICAgICAgICAgHx8fHR0dHx8fICAgICAgHx8fHh4eHx8fHh4eHh4eHh4eHh4eHx8fHx8fHx8fHx8fICAgHx8fHx8fHx8fHh4eHx8fHh4eHx8fHh4eHx8fHx8fHx8fHh4eHx8fHx8fHh4eHBwcHx8fHx8fHx8fHh4eHx8fHR0dHh4eHx8fHx8fHR0dGxsbHx8fICAgICAgHx8fHx8fICAgICAgHx8fHh4eHx8fICAgICAgvuVSZAAAALd0Uk5TABBwms/q//rkxKBQCwsubrjxv2NcsfhABxWqdSqKw5lqruOVcW58ldXhkUBwDlm6dRBTOa0sBP1aKwWAgxemzICOxRX7ULkOMpwMtqX03xXvOyJVytQkzitgRU5ARCoHTOhHQCs5VRyGWC4yS9NjJMawKUO87dbBFaXFwCtgVZAbhxkSzXq1j1w8R+vYLFgCrErwxzzAOTvaYK+1EYM1Dj545r9CHiPsyC4L3DsXs4k1i1Jro0sg8LTw4AAAAtlJREFUeJxjZCARMI5qoJMGRiTwhZAGXqCibwguNyPj70/4NPBwMDJ+QBHhZmFifIFTgyTj968Ybvgv9u85Dg0yjK/EGf+w/mZ7wgjlQ8H751g18PC9U74KZom/AwkrvX8J5km/Vbn6H4sG3c9MPJeggnrXgaQW43kwT0Lq++87WDQY31diPA1hmj2RPc9gyPjvFIRr+f6bzDFMDda31RgPQ9l2IJd/OAflOZ83YtyNqcHtgJzyTqgNr1/y6zOeVoLa4MW4220LpgbfnVJvoBEr+dOacZfrO5GNcC95bcDQELiVQdJ4HZjJ477Jk+01P/u/tRCpMMb1DEEr0DVErmXwY1sGYlkpbmXUl2F8fO2X3yIQP56RcSlDzDx0DcqPGewOiHsAPfvsmtJNr5kM6SvZ7IVBnt/tduo8Q8YkVA35v15vAlJMPvvidtznSmA8corBzJZxUj4j4/JnvKDkYqEh1IGkARK17jqb/C/vdNdjbIGaVvsXxGVm7ABFtP+hl3ANDR+mgahqxjoGbKD5I9g9dVuPwzS0NoIl4MGKBniqGsB0YyVMQ8A2ZA2S+YxrQVGmG3tnEzgrSPz9CJZvLYVpYIOYxAeJWvXUxXHFQFqYmyutCCTQz1gGUfALTYMvJKLYGNxd8sEWMijehFpNdw1+O5A1+O3I/9cL8ovazup6ZA09eTANFje/ImmwiN4mNxNIT9nhyZiFpIE7fAZMA8N0RpDmyQvh+QoFWCXkAMmpf1hT4BqAGdrk0Ic6SUbGRAzl/oGMjCmM3EKcl8FceGrVfm/y7dDcnKmMuxYiqY53L1SRPKT3VPn5WagIUqnBxuvSZJfMWMQYaMsYBsynvtuMDWuzGhnt0gsm9mEpBBj65Z539kUz2B35U6zcwKvkLpfyqX3nIQal9kefeAoZsGgAAZ4lxaV5SPz/a36HoKrAUtzXmDH2FacxzOp938qY9AJddmhUWcNfAwCdTO4xB9cjPAAAAABJRU5ErkJggg=='),
            ('v0 by Vercel', 'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAAAXNSR0IB2cksfwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAEVQTFRFAAAAHh4eHx8fHx8fHh4eICAgHx8fHh4eICAgHx8fHh4eICAgHBwcHh4eHh4eICAgICAgHh4eICAgHx8fHh4eICAgHx8f1bF6dAAAABd0Uk5TAID/z5Ag73AQ35+AQKCPYDB/cMCwQNAfJJM3AAABA0lEQVR4nO3TzRKCIBAA4IU0TWtqfP83rIOjlZo/BMuPkDjmqQ5yStlvXZaNwMpFNrCBfwSEWD9JuwrwNVgg4A8Ba8ewwQMgbAyIWwYQsdoGTnDYibS0NiWFvWBPG1AAxlR8IlPhs0pExyo9gKpi+xGklUh09wP8QNBB8LK6FJNGp/gAGJ6WuhfmbCHhBzsWE6DiYQLgXMrWuUDHe4C8jSR3gemGB+BmVDnAfMALLoWoLB/BwYT7AWS5eMNwZ9+JTpp4P8BjqKJ38hJ0/AzAoZIAr9LM6ByQt4E78YAD19q7bArsqaLOez0nE3B6aKCKWgKQ8b/jVdbHstsXYGFtYAM/A28KlnUxQCNV6QAAAABJRU5ErkJggg=='),
            ('NotebookLM', 'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAAAXNSR0IB2cksfwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAF1QTFRFAAAAICAgHR0dHh4eHx8fHx8fHh4eHBwcICAgHh4eHx8fHx8fHh4eICAgHx8fHx8fHx8fHx8fICAgICAgHh4eHx8fICAgICAgICAgGxsbHh4eHR0dICAgHh4eHh4evl7FlgAAAB90Uk5TABBQn7+vcEAwf8//kCDv4MDQUECg32BwfzCPYICAsI3DMQYAAAHESURBVHic7ZVrT4MwFIZ72QWKODNmZqL+//9loiYamXGuA8aoPaeUltsyv6nxfChNx3P6nhuj5JtG/4EfC1BK9bleC3UGEMDr1hT7PA0E5bznMg+3o0DI6g0HUYU9rvYjwMS459UsxZ+WlEo8YdtBIK5gnfI3z0eSwSqy7QAQB+BOvLYjSJhsEw0gYBe9kL6tIVNKdoAbcBGAmlgHu3z2iYDrZfHUAlC/9k+nwREPFIsdFMGyawHXcONufvTLcPVod3ebHgA+xKZTNRcqJLzmDWCyhxbygySC1RXIjECy0rUrcwesbC1dFYKLvaccYjSwAS6NIz5JPUUYl71Ci+IfDVArUrzVZuQCuvtgWur2vdaEwNo0sey2P2SHK/RCRc1SmwTdYnklQIBi1N5EV9IGq8PEaiOwKGHZsMZ1054gNi9rfdhnCGAlhSTOmhGIrNT71KTMAW2z2Yls3BB1D+CzeaaKUHoEJDx5GAa8UXDdhgncDQL+WGEFEGDhKOAPLo4TphNnYRCwURqDdFJQg4MyCLB2W+haYkyjAO184uCKY3YCOBRtAF6EIEYBN4/nAAkhaadT6dKcwZPgx2Rmnr/kH+jPA1+4GsIxRhgD2QAAAABJRU5ErkJggg==')
    """)
    if env.is_local_env():
        op.execute("INSERT INTO \"user\" (username, name, monthly_hours, monthly_usd_limit, created_at) VALUES ('test@test.com', 'John Doe', 160, 10, NOW())")
        op.execute("INSERT INTO user_agent (user_id, agent_id, creation) VALUES (1, 1, NOW())")
        op.execute("INSERT INTO team_role (team_id, user_id, role, status) VALUES (1, 1, 'TEAM_OWNER', 'ACCEPTED')")


def downgrade() -> None:
    op.drop_index(op.f('ix_thread_message_file_thread_message_id'), table_name='thread_message_file')
    op.drop_index(op.f('ix_thread_message_file_file_id'), table_name='thread_message_file')
    op.drop_table('thread_message_file')
    op.drop_index('ix_test_case_result_test_case_id_executed_at', table_name='test_case_result')
    op.drop_table('test_case_result')
    op.drop_index('ix_thread_message_thread_id_timestamp', table_name='thread_message')
    op.drop_index(op.f('ix_thread_message_thread_id'), table_name='thread_message')
    op.drop_index(op.f('ix_thread_message_parent_id'), table_name='thread_message')
    op.drop_table('thread_message')
    op.drop_index('ix_test_case_agent_id_last_update', table_name='test_case')
    op.drop_table('test_case')
    op.drop_index('ix_user_agent_user_id_creation', table_name='user_agent')
    op.drop_table('user_agent')
    op.drop_index(op.f('ix_usage_user_id'), table_name='usage')
    op.drop_index(op.f('ix_usage_timestamp'), table_name='usage')
    op.drop_index(op.f('ix_usage_model_id'), table_name='usage')
    op.drop_index(op.f('ix_usage_agent_id'), table_name='usage')
    op.drop_table('usage')
    op.drop_index('ix_thread_user_id_agent_id_creation', table_name='thread')
    op.drop_index(op.f('ix_thread_user_id'), table_name='thread')
    op.drop_table('thread')
    op.drop_table('doc_tool_file')
    op.drop_table('doc_tool_config')
    op.drop_table('agent_tool_config_file')
    op.drop_index(op.f('ix_agent_tool_config_draft'), table_name='agent_tool_config')
    op.drop_table('agent_tool_config')
    op.drop_index('ix_agent_prompt_user_id_last_update_shared', table_name='agent_prompt')
    op.drop_index(op.f('ix_agent_prompt_shared'), table_name='agent_prompt')
    op.drop_index('ix_agent_prompt_agent_id_user_id_shared', table_name='agent_prompt')
    op.drop_table('agent_prompt')
    op.drop_index(op.f('ix_team_role_user_id'), table_name='team_role')
    op.drop_index(op.f('ix_team_role_team_id'), table_name='team_role')
    op.drop_table('team_role')
    op.drop_index(op.f('ix_file_timestamp'), table_name='file')
    op.drop_index(op.f('ix_file_status'), table_name='file')
    op.drop_table('file')
    op.drop_index(op.f('ix_external_agent_time_saving_user_id'), table_name='external_agent_time_saving')
    op.drop_index(op.f('ix_external_agent_time_saving_external_agent_id'), table_name='external_agent_time_saving')
    op.drop_table('external_agent_time_saving')
    op.drop_index('ix_agent_user_id_last_update', table_name='agent')
    op.drop_index(op.f('ix_agent_user_id'), table_name='agent')
    op.drop_index('ix_agent_team_last_update', table_name='agent')
    op.drop_table('agent')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_name'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_tool_oauth_token_updated_at'), table_name='tool_oauth_token')
    op.drop_table('tool_oauth_token')
    op.drop_index(op.f('ix_tool_oauth_state_updated_at'), table_name='tool_oauth_state')
    op.drop_index(op.f('ix_tool_oauth_state_agent_id'), table_name='tool_oauth_state')
    op.drop_table('tool_oauth_state')
    op.drop_index(op.f('ix_tool_oauth_client_info_updated_at'), table_name='tool_oauth_client_info')
    op.drop_table('tool_oauth_client_info')
    op.drop_table('team')
    op.drop_table('llm_model')
    op.drop_table('jira_tool_config')
    op.drop_table('external_agent')
    sa.Enum('REASONING', 'CHAT', name='llmmodeltype').drop(op.get_bind())
    sa.Enum('TEAM_OWNER', 'TEAM_MEMBER', name='role').drop(op.get_bind())
    sa.Enum('ACCEPTED', 'PENDING', 'REJECTED', name='teamrolestatus').drop(op.get_bind())
    sa.Enum('CREATIVE', 'NEUTRAL', 'PRECISE', name='llmtemperature').drop(op.get_bind())
    sa.Enum('LOW', 'MEDIUM', 'HIGH', name='reasoningeffort').drop(op.get_bind())
    sa.Enum('PENDING', 'PROCESSED', 'ERROR', 'QUOTA_EXCEEDED', name='filestatus').drop(op.get_bind())
    sa.Enum('BASIC', 'ENHANCED', name='fileprocessor').drop(op.get_bind())
    sa.Enum('USER', 'AGENT', name='threadmessageorigin').drop(op.get_bind())
    sa.Enum('PROMPT_TOKENS', 'COMPLETION_TOKENS', 'PDF_PARSING', 'WEB_SEARCH', 'WEB_EXTRACT', 'EMBEDDING_TOKENS', name='usagetype').drop(op.get_bind())
    sa.Enum('BEARER', name='tooloauthtokentype').drop(op.get_bind())
    sa.Enum('PENDING', 'RUNNING', 'SUCCESS', 'FAILURE', 'ERROR', name='testcaseresultstatus').drop(op.get_bind())
