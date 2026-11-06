"""migra metadados legados do corpo para colunas

Revision ID: a1b2c3d4e5f6
Revises: 8f12a9c3d4e5
Create Date: 2026-11-05 23:55:00.000000

"""
from collections.abc import Sequence
from datetime import UTC, datetime
import json
import re

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: str | Sequence[str] | None = '8f12a9c3d4e5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def parse_data_iso(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        s = valor.replace('Z', '+00:00')
        dt = datetime.fromisoformat(s)
        if dt.tzinfo:
            dt = dt.astimezone(UTC).replace(tzinfo=None)
        return dt
    except Exception:
        return None


def upgrade() -> None:
    conn = op.get_bind()
    query = sa.text("SELECT id, corpo, inicio_em, expira_em FROM comunicados WHERE corpo LIKE '%<!--epis_validade:%'")
    resultados = conn.execute(query).fetchall()

    padrao = re.compile(r'<!--epis_validade:([\s\S]*?)-->')

    for row in resultados:
        cid, corpo_atual, inicio_atual, expira_atual = row
        match = padrao.search(corpo_atual)
        if match:
            novo_inicio = inicio_atual
            novo_expira = expira_atual
            try:
                meta = json.loads(match.group(1))
                if not novo_inicio and meta.get('inicio_em'):
                    novo_inicio = parse_data_iso(meta['inicio_em'])
                if not novo_expira and meta.get('expira_em'):
                    novo_expira = parse_data_iso(meta['expira_em'])
            except Exception:
                pass

            corpo_limpo = padrao.sub('', corpo_atual).rstrip()

            conn.execute(
                sa.text(
                    "UPDATE comunicados SET corpo = :corpo, inicio_em = :inicio, expira_em = :expira WHERE id = :id"
                ),
                {"corpo": corpo_limpo, "inicio": novo_inicio, "expira": novo_expira, "id": cid},
            )


def downgrade() -> None:
    conn = op.get_bind()
    query = sa.text(
        "SELECT id, corpo, inicio_em, expira_em FROM comunicados WHERE inicio_em IS NOT NULL OR expira_em IS NOT NULL"
    )
    resultados = conn.execute(query).fetchall()
    for row in resultados:
        cid, corpo_atual, inicio, expira = row
        if '<!--epis_validade:' not in corpo_atual and (inicio or expira):
            meta = {
                'inicio_em': inicio.isoformat() if inicio else None,
                'expira_em': expira.isoformat() if expira else None,
            }
            corpo_com_tag = f"{corpo_atual}\n\n<!--epis_validade:{json.dumps(meta)}-->"
            conn.execute(
                sa.text("UPDATE comunicados SET corpo = :corpo WHERE id = :id"),
                {"corpo": corpo_com_tag, "id": cid},
            )
