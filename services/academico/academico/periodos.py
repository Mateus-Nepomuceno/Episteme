from datetime import datetime, timezone

from sqlalchemy.orm import Session

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
