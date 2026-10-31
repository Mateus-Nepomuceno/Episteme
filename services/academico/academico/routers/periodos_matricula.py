from http import HTTPStatus
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from academico.database import get_session
from academico.models import Curso, PeriodoMatricula
from academico.schemas import (
    PeriodoMatriculaCreate,
    PeriodoMatriculaCriadoResponse,
    PeriodoMatriculaResponse,
    PeriodosMatriculaList,
)
from academico.security import CurrentUser, exigir_admin, get_current_user
from academico.periodos import atualizar_status

router = APIRouter(
    prefix="/periodos-matricula",
    tags=["periodos-matricula"],
)


@router.post(
    "/",
    status_code=HTTPStatus.CREATED,
    response_model=PeriodoMatriculaCriadoResponse,
)
def configurar_periodo(
    dados: PeriodoMatriculaCreate,
    current_user: Annotated[
        CurrentUser, Depends(exigir_admin)
    ],
    session: Annotated[Session, Depends(get_session)],
):
    cursos = session.scalars(
        select(Curso).where(Curso.id.in_(dados.cursos_ids))
    ).all()

    cursos_encontrados = {curso.id for curso in cursos}

    if cursos_encontrados != set(dados.cursos_ids):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Um ou mais cursos não estão cadastrados",
        )

    if any(not curso.ativo for curso in cursos):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Não é permitido configurar cursos inativos",
        )

    periodo = PeriodoMatricula(
        periodo_letivo=dados.periodo_letivo,
        data_inicial=dados.data_inicial,
        data_final=dados.data_final,
        cursos_ids=[
            str(curso_id) for curso_id in dados.cursos_ids
        ],
        tipo=dados.tipo,
        turmas_ids=[
            str(turma_id) for turma_id in dados.turmas_ids
        ],
    )

    session.add(periodo)
    session.commit()
    session.refresh(periodo)

    atualizar_status(periodo, session)

    return {
        "mensagem": "Período de matrícula configurado com sucesso",
        "id": periodo.id,
        "periodo_letivo": periodo.periodo_letivo,
        "data_inicial": periodo.data_inicial,
        "data_final": periodo.data_final,
        "cursos_ids": periodo.cursos_ids,
        "tipo": periodo.tipo,
        "turmas_ids": periodo.turmas_ids,
        "status": periodo.status,
    }


@router.get(
    "/",
    response_model=PeriodosMatriculaList,
)
def listar_periodos(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[
        CurrentUser, Depends(get_current_user)
    ],
    periodo_letivo: str | None = None,
    status: Literal[
        "agendado", "aberto", "encerrado"
    ] | None = None,
):
    consulta = select(PeriodoMatricula)

    if periodo_letivo is not None:
        consulta = consulta.where(
            PeriodoMatricula.periodo_letivo == periodo_letivo
        )

    periodos = session.scalars(
        consulta.order_by(PeriodoMatricula.data_inicial)
    ).all()

    periodos = [
        atualizar_status(periodo, session)
        for periodo in periodos
    ]

    if status is not None:
        periodos = [
            periodo
            for periodo in periodos
            if periodo.status == status
        ]

    return {"periodos": periodos}


@router.get(
    "/{periodo_id}",
    response_model=PeriodoMatriculaResponse,
)
def consultar_periodo(
    periodo_id: UUID,
    current_user: Annotated[
        CurrentUser, Depends(get_current_user)
    ],
    session: Annotated[Session, Depends(get_session)],
):
    periodo = session.get(PeriodoMatricula, periodo_id)

    if periodo is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Período de matrícula não encontrado",
        )

    return atualizar_status(periodo, session)


@router.patch(
    "/{periodo_id}/encerrar",
    response_model=PeriodoMatriculaResponse,
)
def encerrar_periodo(
    periodo_id: UUID,
    current_user: Annotated[
        CurrentUser, Depends(exigir_admin)
    ],
    session: Annotated[Session, Depends(get_session)],
):
    periodo = session.get(PeriodoMatricula, periodo_id)

    if periodo is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Período de matrícula não encontrado",
        )

    periodo.status = "encerrado"
    session.commit()
    session.refresh(periodo)

    return periodo
