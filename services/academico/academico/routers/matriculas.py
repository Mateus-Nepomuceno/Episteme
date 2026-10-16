
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from academico.database import get_session
from academico.models import Curso, SolicitacaoMatricula
from academico.schemas import (
    SolicitacaoMatriculaCreate,
    SolicitacaoMatriculaResponse,
)
from academico.security import CurrentUser, get_current_user
from academico.settings import Settings

settings = Settings()

router = APIRouter(prefix='/matricula', tags=['matricula'])


@router.post(
    '/solicitar',
    status_code=HTTPStatus.CREATED,
    response_model=SolicitacaoMatriculaResponse,
)
def solicitar_matricula(
    dados: SolicitacaoMatriculaCreate,
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    session: Annotated[Session, Depends(get_session)],
):
    url = (
        f'{settings.TURMA_API_URL.rstrip("/")}'
        f'/alunos/usuario_id/{current_user.id}'
    )

    try:
        response = httpx.get(url, timeout=5.0)
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=HTTPStatus.GATEWAY_TIMEOUT,
            detail='O serviço de turma demorou para responder',
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail='Não foi possível acessar o serviço de turma',
        ) from exc

    if response.status_code == HTTPStatus.NOT_FOUND:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Cadastro de aluno não encontrado',
        )

    if response.is_error:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail='O serviço de turma retornou um erro',
        )

    aluno = response.json()

    try:
        aluno_id = UUID(str(aluno['id']))
        curso_id = UUID(str(aluno['curso_id']))
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail='O serviço de turma retornou identificadores inválidos',
        ) from exc

    curso = session.get(Curso, curso_id)

    if curso is None:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='O curso do aluno não está cadastrado no serviço acadêmico',
        )

    solicitacao = SolicitacaoMatricula(
        usuario_id=current_user.id,
        aluno_id=aluno_id,
        curso_id=curso_id,
        periodo_letivo=dados.periodo_letivo,
        turmas_ids=[str(turma_id) for turma_id in dados.turmas_ids],
    )

    session.add(solicitacao)
    session.commit()
    session.refresh(solicitacao)

    return {
        'mensagem': 'Solicitação de matrícula registrada com sucesso',
        'id': solicitacao.id,
        'protocolo': solicitacao.protocolo,
        'usuario_id': solicitacao.usuario_id,
        'aluno_id': solicitacao.aluno_id,
        'curso_id': solicitacao.curso_id,
        'periodo_letivo': solicitacao.periodo_letivo,
        'turmas_ids': solicitacao.turmas_ids,
        'situacao': solicitacao.situacao,
        'data_solicitacao': solicitacao.data_solicitacao,
    }
