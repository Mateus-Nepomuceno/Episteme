
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from academico.database import get_session
from academico.models import PeriodoMatricula


def calcular_status(
    periodo: PeriodoMatricula,
    agora: datetime | None = None,
) -> str:
    if periodo.status == "encerrado":
        return "encerrado"

    if agora is None:
        agora = datetime.now(timezone.utc).replace(tzinfo=None)
    elif agora.tzinfo is not None:
        agora = agora.astimezone(timezone.utc).replace(tzinfo=None)

    if agora >= periodo.data_final:
        return "encerrado"

    if agora >= periodo.data_inicial:
        return "aberto"

    return "agendado"


def atualizar_status(
    periodo: PeriodoMatricula,
    session: Session,
) -> PeriodoMatricula:
    novo_status = calcular_status(periodo)

    if periodo.status != novo_status:
        periodo.status = novo_status
        session.commit()
        session.refresh(periodo)

    return periodo


def atualizar_status_periodos(
    session: Session,
    agora: datetime | None = None,
) -> int:
    periodos = session.scalars(
        select(PeriodoMatricula)
    ).all()

    quantidade_atualizada = 0

    for periodo in periodos:
        novo_status = calcular_status(periodo, agora)

        if periodo.status != novo_status:
            periodo.status = novo_status
            quantidade_atualizada += 1

    if quantidade_atualizada:
        session.commit()

    return quantidade_atualizada


def sincronizar_status_periodos() -> int:
    gerador_sessao = get_session()
    session = next(gerador_sessao)

    try:
        return atualizar_status_periodos(session)
    except Exception:
        session.rollback()
        raise
    finally:
        gerador_sessao.close()
