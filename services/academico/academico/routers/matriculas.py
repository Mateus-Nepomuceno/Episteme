
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from academico.database import get_session
from sqlalchemy import select
from academico.models import (
    Curso,
    PeriodoMatricula,
    SolicitacaoMatricula,
)
from academico.schemas import (
    SolicitacaoMatriculaCreate,
    SolicitacaoMatriculaResponse,
    SolicitacoesMatriculaList,
    ObservacaoMatriculaUpdate,
    SolicitacaoMatriculaCriadaResponse,
    TurmasDisponiveisResponse,
)
from academico.security import CurrentUser, get_current_user
from academico.settings import Settings
from academico.routers.periodos_matricula import atualizar_status

from academico.services.periodos_matricula_service import atualizar_status
settings = Settings()

router = APIRouter(prefix='/matricula', tags=['matricula'])


@router.post(
    '/solicitar',
    status_code=HTTPStatus.CREATED,
    response_model=SolicitacaoMatriculaCriadaResponse,
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

    periodos = session.scalars(
        select(PeriodoMatricula).where(
            PeriodoMatricula.periodo_letivo == dados.periodo_letivo
        )
    ).all()

    periodos = [
        atualizar_status(periodo, session)
        for periodo in periodos
    ]

    periodos_abertos = [
        periodo
        for periodo in periodos
        if periodo.status == 'aberto'
    ]

    if not periodos_abertos:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Não existe período de matrícula aberto para o período letivo informado',
        )

    periodos_do_curso = [
        periodo
        for periodo in periodos_abertos
        if str(curso_id) in periodo.cursos_ids
    ]

    if not periodos_do_curso:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='O curso do aluno não está autorizado neste período de matrícula',
        )

    turmas_solicitadas = {
        str(turma_id)
        for turma_id in dados.turmas_ids
    }

    periodos_compativeis = [
        periodo
        for periodo in periodos_do_curso
        if not periodo.turmas_ids
        or turmas_solicitadas.issubset(set(periodo.turmas_ids))
    ]

    if not periodos_compativeis:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='Uma ou mais turmas solicitadas não estão disponíveis neste período',
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
        'observacao': solicitacao.observacao,
    }


@router.get(
    '/solicitacoes',
    response_model=SolicitacoesMatriculaList,
)
def consultar_solicitacoes(
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    session: Annotated[Session, Depends(get_session)],
    protocolo: UUID | None = None,
    aluno_id: UUID | None = None,
    periodo_letivo: str | None = None,
):
    consulta = select(SolicitacaoMatricula)

    if not current_user.e_admin:
        consulta = consulta.where(
            SolicitacaoMatricula.usuario_id == current_user.id
        )

    if protocolo is not None:
        consulta = consulta.where(
            SolicitacaoMatricula.protocolo == protocolo
        )

    if aluno_id is not None:
        consulta = consulta.where(
            SolicitacaoMatricula.aluno_id == aluno_id
        )

    if periodo_letivo is not None:
        consulta = consulta.where(
            SolicitacaoMatricula.periodo_letivo == periodo_letivo
        )

    consulta = consulta.order_by(
        SolicitacaoMatricula.data_solicitacao.desc()
    )

    solicitacoes = session.scalars(consulta).all()

    return {'solicitacoes': solicitacoes}


@router.get(
    '/solicitacoes/{protocolo}',
    response_model=SolicitacaoMatriculaResponse,
)
def consultar_solicitacao(
    protocolo: UUID,
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    session: Annotated[Session, Depends(get_session)],
):
    solicitacao = session.scalar(
        select(SolicitacaoMatricula).where(
            SolicitacaoMatricula.protocolo == protocolo
        )
    )

    if (
        solicitacao is None
        or (
            not current_user.e_admin
            and solicitacao.usuario_id != current_user.id
        )
    ):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Solicitação de matrícula não encontrada',
        )

    return solicitacao

@router.patch('/solicitacoes/{protocolo}/observacao')
def atualizar_observacao(
    protocolo: UUID,
    dados: ObservacaoMatriculaUpdate,
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    session: Annotated[Session, Depends(get_session)],
):
    if not current_user.e_admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='Apenas a coordenação pode alterar a observação',
        )

    solicitacao = session.scalar(
        select(SolicitacaoMatricula).where(
            SolicitacaoMatricula.protocolo == protocolo
        )
    )

    if solicitacao is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Solicitação de matrícula não encontrada',
        )

    solicitacao.observacao = dados.observacao

    session.commit()
    session.refresh(solicitacao)

    return {
        'mensagem': 'Observação atualizada com sucesso',
        'protocolo': solicitacao.protocolo,
        'observacao': solicitacao.observacao,
    }


@router.get(
    "/turmas-disponiveis",
    response_model=TurmasDisponiveisResponse,
)
def consultar_turmas_disponiveis(
    periodo_letivo: Annotated[
        str,
        Query(pattern=r"^\d{4}\.[12]$"),
    ],
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
    session: Annotated[Session, Depends(get_session)],
    disciplina: str | None = None,
    turma: str | None = None,
):

    periodos = session.scalars(
        select(PeriodoMatricula).where(
            PeriodoMatricula.periodo_letivo == periodo_letivo
        )
    ).all()

    if not periodos:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Não há período de matrícula configurado para este semestre",
        )

    periodos = [
        atualizar_status(periodo, session)
        for periodo in periodos
    ]

    periodos_abertos = [
        periodo
        for periodo in periodos
        if periodo.status == "aberto"
    ]

    if not periodos_abertos:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Não há período de matrícula aberto para este semestre",
        )

    url_aluno = (
        f'{settings.TURMA_API_URL.rstrip("/")}'
        f'/alunos/usuario_id/{current_user.id}'
    )

    try:
        resposta_aluno = httpx.get(url_aluno, timeout=5.0)
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=HTTPStatus.GATEWAY_TIMEOUT,
            detail="O serviço de turma demorou para responder",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="Não foi possível acessar o serviço de turma",
        ) from exc

    if resposta_aluno.status_code == HTTPStatus.NOT_FOUND:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Cadastro de aluno não encontrado",
        )

    if resposta_aluno.is_error:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail="O serviço de turma retornou um erro",
        )

    try:
        aluno = resposta_aluno.json()
        curso_id = str(UUID(str(aluno["curso_id"])))
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(
            status_code=HTTPStatus.BAD_GATEWAY,
            detail="O serviço de turma retornou dados de aluno inválidos",
        ) from exc

    periodos_autorizados = [
        periodo
        for periodo in periodos_abertos
        if curso_id in periodo.cursos_ids
    ]

    if not periodos_autorizados:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="O curso do aluno não está autorizado neste período",
        )

    turmas_permitidas = {
        str(UUID(str(turma_id)))
        for periodo in periodos_autorizados
        for turma_id in periodo.turmas_ids
    }

    if not turmas_permitidas:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=(
                "Este período não possui turmas específicas configuradas. "
                "O serviço de turma ainda não permite filtrar as ofertas "
                "diretamente por curso e período letivo."
            ),
        )

    url_turmas = f'{settings.TURMA_API_URL.rstrip("/")}/turmas/'
    limite = 100
    offset = 0
    turmas_remotas = []

    while True:
        try:
            resposta_turmas = httpx.get(
                url_turmas,
                params={"offset": offset, "limit": limite},
                timeout=5.0,
            )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=HTTPStatus.GATEWAY_TIMEOUT,
                detail="O serviço de turma demorou para responder",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="Não foi possível acessar o serviço de turma",
            ) from exc

        if resposta_turmas.is_error:
            raise HTTPException(
                status_code=HTTPStatus.BAD_GATEWAY,
                detail="O serviço de turma retornou um erro",
            )

        try:
            pagina = resposta_turmas.json()["turmas"]
        except (ValueError, KeyError, TypeError) as exc:
            raise HTTPException(
                status_code=HTTPStatus.BAD_GATEWAY,
                detail="O serviço de turma retornou uma resposta inválida",
            ) from exc

        if not isinstance(pagina, list):
            raise HTTPException(
                status_code=HTTPStatus.BAD_GATEWAY,
                detail="A listagem de turmas retornada é inválida",
            )

        turmas_remotas.extend(pagina)

        if len(pagina) < limite:
            break

        offset += limite

    turmas_disponiveis = []

    for item in turmas_remotas:
        try:
            turma_id = str(UUID(str(item["id"])))
        except (ValueError, TypeError, KeyError) as exc:
            raise HTTPException(
                status_code=HTTPStatus.BAD_GATEWAY,
                detail="O serviço de turma retornou uma turma com ID inválido",
            ) from exc

        if turma_id not in turmas_permitidas:
            continue

        nome_turma = str(item.get("nome", ""))
        materia = str(item.get("materia", ""))

        if disciplina and disciplina.casefold() not in materia.casefold():
            continue

        if turma and turma.casefold() not in nome_turma.casefold():
            continue

        professor = item.get("professor") or {}

        turmas_disponiveis.append({
            "id": turma_id,
            "nome": nome_turma,
            "disciplina": materia,
            "periodo_letivo": periodo_letivo,
            "professor_matricula_id": professor.get("matricula_id"),
        })

    return {
        "periodo_letivo": periodo_letivo,
        "turmas": turmas_disponiveis,
    }
