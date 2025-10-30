"""llm_model_vendor

Revision ID: 07fd1bcafad1
Revises: 4c775a5d6fdc
Create Date: 2025-10-30 12:17:19.629221

"""
import sqlalchemy as sa
from typing import Sequence, Union
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '07fd1bcafad1'
down_revision: Union[str, None] = '4c775a5d6fdc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sa.Enum('ANTHROPIC', 'GOOGLE', 'OPENAI', name='llmmodelvendor').create(op.get_bind())
    op.add_column('llm_model', sa.Column('model_vendor', postgresql.ENUM('ANTHROPIC', 'GOOGLE', 'OPENAI', name='llmmodelvendor', create_type=False), nullable=True))
    
    op.execute("""
        UPDATE llm_model
        SET model_vendor = 'OPENAI'
        WHERE id IN ('gpt-4o-mini', 'gpt-4o', 'gpt-4.1-nano', 'o4-mini', 'gpt-4.1', 'gpt-5', 'gpt-5-mini', 'gpt-5-nano')
    """)
    
    op.execute("""
        UPDATE llm_model
        SET model_vendor = 'ANTHROPIC'
        WHERE id LIKE 'claude%'
    """)
    
    op.execute("""
        UPDATE llm_model
        SET model_vendor = 'GOOGLE'
        WHERE id LIKE 'gemini%'
    """)
    
    op.alter_column('llm_model', 'model_vendor', nullable=False)


def downgrade() -> None:
    op.drop_column('llm_model', 'model_vendor')
    sa.Enum('ANTHROPIC', 'GOOGLE', 'OPENAI', name='llmmodelvendor').drop(op.get_bind())