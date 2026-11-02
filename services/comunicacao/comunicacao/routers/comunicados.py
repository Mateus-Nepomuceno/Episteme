from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from comunicacao.database import get_session
from comunicacao.models import Comunicado
from comunicacao.schemas import ComunicadoCreate, ComunicadoList, ComunicadoPublic
from comunicacao.security import CurrentUser, exigir_admin, get_current_user

router = APIRouter(prefix='/comunicados', tags=['comunicados'])


@router.get('', response_model=ComunicadoList)
def read_comunicados(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    limite: Annotated[int, Query(ge=1, le=50)] = 3,
):
    comunicados = session.scalars(
        select(Comunicado)
        .where(Comunicado.publicado.is_(True))
        .order_by(Comunicado.publicado_em.desc())
        .limit(limite)
    ).all()
    return {'comunicados': comunicados}


@router.post(
    '',
    status_code=HTTPStatus.CREATED,
    response_model=ComunicadoPublic,
)
def create_comunicado(
    comunicado: ComunicadoCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(exigir_admin)],
):
    db_comunicado = Comunicado(
        titulo=comunicado.titulo,
        resumo=comunicado.resumo,
        corpo=comunicado.corpo,
        publicado=comunicado.publicado,
    )
    session.add(db_comunicado)
    session.commit()
    session.refresh(db_comunicado)

    return ComunicadoPublic.model_validate(db_comunicado)
