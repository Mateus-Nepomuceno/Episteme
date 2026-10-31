from dataclasses import dataclass
from datetime import time
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.database import get_session
from turma.models import Aluno, DiaSemana, Horario, Professor, Turma
from turma.schemas import (
    PERIODO_LETIVO_PATTERN,
    FiltroPaginacao,
    HorarioTurmaPublic,
    Mensagem,
    ProfessorTurmaPublic,
    TurmaCreate,
    TurmaList,
    TurmaOfertaList,
    TurmaOfertaPublic,
    TurmaPublic,
)
from turma.security import CurrentUser, get_current_user, get_usuario_opcional

router = APIRouter(prefix='/turmas', tags=['turmas'])


@dataclass(frozen=True)
class FiltroOferta:
    disciplina: str | None = None
    codigo: str | None = None
    dia_semana: DiaSemana | None = None
    horario_inicio: time | None = None
    horario_fim: time | None = None


def _pode_gerenciar_turma(
    current_user: CurrentUser, professor: Professor | None
) -> bool:
    if current_user.e_admin:
        return True

    return professor is not None and professor.usuario_id == current_user.id


def _turma_visivel(turma: Turma, current_user: CurrentUser | None) -> TurmaPublic:
    dados = TurmaPublic.model_validate(turma)

    if current_user is not None and _pode_gerenciar_turma(current_user, turma.professor):
        return dados

    return dados.model_copy(update={'alunos': []})


def _buscar_professor(
    session: Session, professor_id: UUID | None
) -> Professor | None:
    if professor_id is None:
        return None

    return session.get(Professor, professor_id)


def _horario_corresponde(
    horario: Horario,
    dia_semana: DiaSemana | None,
    horario_inicio: time | None,
    horario_fim: time | None,
) -> bool:
    if dia_semana is not None and horario.dia_semana != dia_semana:
        return False

    if horario_inicio is not None and horario.horario_inicio < horario_inicio:
        return False

    return not (horario_fim is not None and horario.horario_fim > horario_fim)


def _turma_corresponde_filtros(turma: Turma, filtro: FiltroOferta) -> bool:
    if filtro.disciplina and (
        filtro.disciplina.casefold() not in turma.materia.casefold()
    ):
        return False

    if filtro.codigo and (
        (turma.codigo or '').casefold() != filtro.codigo.casefold()
    ):
        return False

    if (
        filtro.dia_semana is None
        and filtro.horario_inicio is None
        and filtro.horario_fim is None
    ):
        return True

    return any(
        _horario_corresponde(
            horario,
            filtro.dia_semana,
            filtro.horario_inicio,
            filtro.horario_fim,
        )
        for horario in turma.horarios
    )


def _montar_oferta(turma: Turma) -> TurmaOfertaPublic:
    vagas_disponiveis = None

    if turma.capacidade is not None:
        matriculados = sum(1 for aluno in turma.alunos if aluno.ativo)
        vagas_disponiveis = max(turma.capacidade - matriculados, 0)

    professor = (
        ProfessorTurmaPublic.model_validate(turma.professor)
        if turma.professor is not None
        else None
    )

    return TurmaOfertaPublic(
        id=turma.id,
        nome=turma.nome,
        codigo=turma.codigo,
        materia=turma.materia,
        curso_id=turma.curso_id,
        periodo_letivo=turma.periodo_letivo,
        capacidade=turma.capacidade,
        vagas_disponiveis=vagas_disponiveis,
        professor=professor,
        horarios=[
            HorarioTurmaPublic.model_validate(horario)
            for horario in turma.horarios
        ],
    )


@router.post('/', status_code=HTTPStatus.CREATED, response_model=TurmaPublic)
def create_turma(
    turma: TurmaCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    db_turma = session.scalar(
        select(Turma).where(
            (Turma.nome == turma.nome) & (Turma.professor_id == turma.professor_id)
        )
    )

    if db_turma:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Turma já existe'
        )

    professor = None

    if turma.professor_id is not None:
        professor = session.get(Professor, turma.professor_id)

        if not professor:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='Professor não existe'
            )

    if not _pode_gerenciar_turma(current_user, professor):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    alunos: list[Aluno] = list(
        session.scalars(
            select(Aluno).where(Aluno.id.in_(turma.aluno_ids))
        ).all()
    )

    if len(alunos) != len(turma.aluno_ids):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Um ou mais alunos não foram encontrados'
        )

    db_turma = Turma(
        nome=turma.nome,
        codigo=turma.codigo,
        materia=turma.materia,
        curso_id=turma.curso_id,
        periodo_letivo=turma.periodo_letivo,
        capacidade=turma.capacidade,
        professor_id=turma.professor_id,
        documentos=turma.documentos,
        avisos=turma.avisos,
        professor=professor,
        alunos=alunos
    )

    session.add(db_turma)
    session.commit()
    session.refresh(db_turma)

    return db_turma


@router.get('/', response_model=TurmaList)
def read_turmas(
    filter: Annotated[FiltroPaginacao, Depends()],
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser | None, Depends(get_usuario_opcional)],
):
    turmas = session.scalars(select(Turma).offset(filter.offset).limit(filter.limit)).all()
    return {'turmas': [_turma_visivel(turma, current_user) for turma in turmas]}


@router.get('/ofertas', response_model=TurmaOfertaList)
def read_ofertas_turmas(
    curso_id: UUID,
    periodo_letivo: Annotated[str, Query(pattern=PERIODO_LETIVO_PATTERN)],
    session: Annotated[Session, Depends(get_session)],
    filter: Annotated[FiltroPaginacao, Depends()],
    filtro: Annotated[FiltroOferta, Depends()],
):
    if (
        filtro.horario_inicio
        and filtro.horario_fim
        and filtro.horario_inicio > filtro.horario_fim
    ):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='Horário de início deve ser anterior ao horário de fim',
        )

    turmas = session.scalars(
        select(Turma)
        .where(
            Turma.curso_id == curso_id,
            Turma.periodo_letivo == periodo_letivo,
        )
        .order_by(Turma.nome, Turma.id)
    ).all()

    turmas_filtradas = [
        turma for turma in turmas if _turma_corresponde_filtros(turma, filtro)
    ]

    pagina = turmas_filtradas[filter.offset : filter.offset + filter.limit]

    return {'turmas': [_montar_oferta(turma) for turma in pagina]}


@router.get('/{turma_id}', response_model=TurmaPublic)
def read_turma(
    turma_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser | None, Depends(get_usuario_opcional)],
):
    turma = session.scalar(select(Turma).where(Turma.id == turma_id))

    if not turma:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Turma não encontrada')

    return _turma_visivel(turma, current_user)


@router.put('/{turma_id}', response_model=TurmaPublic)
def update_turma(
    turma_id: UUID,
    turma: TurmaCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    db_turma = session.scalar(select(Turma).where(Turma.id == turma_id))

    if not db_turma:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Turma não encontrada'
        )

    professor_atual = _buscar_professor(session, db_turma.professor_id)

    if not _pode_gerenciar_turma(current_user, professor_atual):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    novo_professor = None

    if turma.professor_id is not None:
        novo_professor = session.get(Professor, turma.professor_id)

        if not novo_professor:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='Professor não existe'
            )

    alunos: list[Aluno] = list(
        session.scalars(
            select(Aluno).where(Aluno.id.in_(turma.aluno_ids))
        ).all()
    )

    if len(alunos) != len(turma.aluno_ids):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Um ou mais alunos não foram encontrados'
        )

    db_turma.nome = turma.nome
    db_turma.codigo = turma.codigo
    db_turma.materia = turma.materia
    db_turma.curso_id = turma.curso_id
    db_turma.periodo_letivo = turma.periodo_letivo
    db_turma.capacidade = turma.capacidade
    db_turma.professor_id = turma.professor_id
    db_turma.professor = novo_professor
    db_turma.documentos = turma.documentos
    db_turma.avisos = turma.avisos
    db_turma.alunos = alunos
    session.commit()
    session.refresh(db_turma)
    return db_turma


@router.delete('/{turma_id}', response_model=Mensagem)
def delete_turma(
    turma_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    db_turma = session.scalar(select(Turma).where(Turma.id == turma_id))

    if not db_turma:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Turma não encontrada'
        )

    professor = _buscar_professor(session, db_turma.professor_id)

    if not _pode_gerenciar_turma(current_user, professor):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    session.delete(db_turma)
    session.commit()

    return {'mensagem': 'Turma deletada'}
