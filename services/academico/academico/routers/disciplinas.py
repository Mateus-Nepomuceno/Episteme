from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from academico.database import get_session
from academico.models import Disciplina
from academico.schemas import (
    DisciplinaCreate,
    DisciplinaList,
    DisciplinaPublic,
    FiltroPaginacao,
    Mensagem,
)
from academico.security import CurrentUser, get_current_user

router = APIRouter(prefix='/disciplinas', tags=['disciplinas'])


@router.post(
    '/', status_code=HTTPStatus.CREATED, response_model=DisciplinaPublic
)
def create_disciplina(
    disciplina: DisciplinaCreate,
    session: Annotated[Session, Depends(get_session)],
):
    db_disciplina = session.scalar(
        select(Disciplina).where(Disciplina.codigo == disciplina.codigo)
    )

    if db_disciplina:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Disciplina já cadastrada'
        )

    db_disciplina = Disciplina(
        codigo=disciplina.codigo,
        nome=disciplina.nome,
        carga_horaria=disciplina.carga_horaria,
        tipo=disciplina.tipo,
        departamento=disciplina.departamento,
        creditos=disciplina.creditos,
        periodo_curricular=disciplina.periodo_curricular,
        ementa=disciplina.ementa,
        bibliografia=disciplina.bibliografia,
        pre_requisitos=disciplina.pre_requisitos,
    )

    session.add(db_disciplina)
    session.commit()
    session.refresh(db_disciplina)

    return db_disciplina


@router.get('/', response_model=DisciplinaList)
def read_disciplinas(
    filter: Annotated[FiltroPaginacao, Depends()],
    session: Annotated[Session, Depends(get_session)],
):
    disciplinas = session.scalars(
        select(Disciplina).offset(filter.offset).limit(filter.limit)
    ).all()
    return {'disciplinas': disciplinas}


@router.get('/{disciplina_id}', response_model=DisciplinaPublic)
def read_disciplina(
    disciplina_id: UUID, session: Annotated[Session, Depends(get_session)]
):
    disciplina = session.scalar(
        select(Disciplina).where(Disciplina.id == disciplina_id)
    )

    if not disciplina:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Disciplina não encontrada',
        )

    return disciplina


@router.put('/{disciplina_id}', response_model=DisciplinaPublic)
def update_disciplina(
    disciplina_id: UUID,
    disciplina: DisciplinaCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    db_disciplina = session.scalar(
        select(Disciplina).where(Disciplina.id == disciplina_id)
    )

    if not db_disciplina:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Disciplina não encontrada',
        )

    if not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    db_disciplina.codigo = disciplina.codigo
    db_disciplina.nome = disciplina.nome
    db_disciplina.carga_horaria = disciplina.carga_horaria
    db_disciplina.tipo = disciplina.tipo
    db_disciplina.departamento = disciplina.departamento
    db_disciplina.creditos = disciplina.creditos
    db_disciplina.periodo_curricular = disciplina.periodo_curricular
    db_disciplina.ementa = disciplina.ementa
    db_disciplina.bibliografia = disciplina.bibliografia
    db_disciplina.pre_requisitos = disciplina.pre_requisitos
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Código já cadastrado'
        )
    else:
        session.refresh(db_disciplina)
        return db_disciplina


@router.delete('/{disciplina_id}', response_model=Mensagem)
def delete_disciplina(
    disciplina_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    db_disciplina = session.scalar(
        select(Disciplina).where(Disciplina.id == disciplina_id)
    )

    if not db_disciplina:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Disciplina não encontrada',
        )

    if not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Permissão negada'
        )

    session.delete(db_disciplina)
    session.commit()

    return {'mensagem': 'Disciplina deletada'}
