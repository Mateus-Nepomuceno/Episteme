from datetime import date, datetime, time, timedelta
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from academico.database import get_session
from academico.models import AtividadeComplementar
from academico.schemas import (
    CompromissoAluno,
    CompromissosAluno,
    HistoricoAluno,
    NotaRecenteAluno,
    NotasRecentesAluno,
    PendenciaAluno,
    PendenciasAluno,
    ProximaAulaAluno,
    ProximasAulasAluno,
    ResumoAluno,
)
from academico.security import CurrentUser, get_current_user
from academico.turma_client import (
    buscar_aluno_por_usuario,
    consultar_turma,
    listar_turmas_do_aluno,
)

router = APIRouter(prefix='/alunos/me', tags=['alunos'])

DIAS_DA_SEMANA = {
    'Segunda': 0,
    'Terça': 1,
    'Quarta': 2,
    'Quinta': 3,
    'Sexta': 4,
}
SITUACOES_PENDENTES = ('pendente', 'vencida')
NOTA_MINIMA_APROVACAO = 7


def _aluno_e_turmas(current_user: CurrentUser):
    try:
        aluno = buscar_aluno_por_usuario(current_user.id, current_user.token)
    except HTTPException as exc:
        if exc.status_code == HTTPStatus.NOT_FOUND:
            return None, []
        raise

    aluno_id = UUID(str(aluno['id']))
    return aluno_id, listar_turmas_do_aluno(aluno_id, current_user.token)


def _media(valores: list[float]) -> float | None:
    return round(sum(valores) / len(valores), 2) if valores else None


@router.get('/resumo', response_model=ResumoAluno)
def read_resumo(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    aluno_id, turmas = _aluno_e_turmas(current_user)

    desempenhos = [
        consultar_turma(
            f'/alunos/me/turmas/{turma["id"]}/desempenho', current_user.token
        )
        for turma in turmas
    ]
    medias = [d['media'] for d in desempenhos if d['media'] is not None]
    frequencias = [d['frequencia'] for d in desempenhos if d['frequencia'] is not None]

    horas = 0
    if aluno_id is not None:
        horas = session.scalar(
            select(func.coalesce(func.sum(AtividadeComplementar.horas), 0)).where(
                AtividadeComplementar.aluno_id == aluno_id,
                AtividadeComplementar.situacao == 'aprovada',
            )
        )

    frequencia = _media(frequencias)
    return ResumoAluno(
        media_geral=_media(medias),
        frequencia_geral=round(frequencia) if frequencia is not None else None,
        horas_complementares=horas,
    )


@router.get('/pendencias', response_model=PendenciasAluno)
def read_pendencias(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    _, turmas = _aluno_e_turmas(current_user)

    pendencias = []
    for turma in turmas:
        atividades = consultar_turma(
            f'/turmas/{turma["id"]}/atividades', current_user.token
        )['atividades']
        for atividade in atividades:
            if atividade['situacao'] in SITUACOES_PENDENTES:
                pendencias.append(
                    PendenciaAluno(
                        id=atividade['id'],
                        titulo=atividade['titulo'],
                        disciplina=turma['materia'],
                        turma_id=turma['id'],
                        tipo=atividade['tipo'],
                        prazo=atividade['prazo'],
                        situacao=atividade['situacao'],
                    )
                )

    pendencias.sort(key=lambda p: p.prazo)
    return {'pendencias': pendencias}


@router.get('/notas/recentes', response_model=NotasRecentesAluno)
def read_notas_recentes(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    limite: Annotated[int, Query(ge=1, le=50)] = 5,
):
    _, turmas = _aluno_e_turmas(current_user)

    notas = []
    for turma in turmas:
        registros = consultar_turma(
            f'/alunos/me/turmas/{turma["id"]}/notas', current_user.token
        )['notas']
        for registro in registros:
            if registro['valor'] is not None:
                notas.append(
                    NotaRecenteAluno(
                        avaliacao_id=registro['avaliacao_id'],
                        nome=registro['nome'],
                        disciplina=turma['materia'],
                        turma_id=turma['id'],
                        data=registro['data'],
                        valor=registro['valor'],
                    )
                )

    notas.sort(key=lambda n: n.data, reverse=True)
    return {'notas': notas[:limite]}


@router.get('/compromissos', response_model=CompromissosAluno)
def read_compromissos(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    limite: Annotated[int, Query(ge=1, le=50)] = 10,
):
    _, turmas = _aluno_e_turmas(current_user)
    hoje = date.today()
    agora = datetime.now()

    compromissos = []
    for turma in turmas:
        avaliacoes = consultar_turma(
            f'/turmas/{turma["id"]}/avaliacoes', current_user.token
        )['avaliacoes']
        for avaliacao in avaliacoes:
            data = date.fromisoformat(avaliacao['data'])
            if data >= hoje:
                compromissos.append(
                    CompromissoAluno(
                        id=avaliacao['id'],
                        titulo=avaliacao['nome'],
                        tipo='Avaliação',
                        data=datetime.combine(data, time.min),
                        disciplina=turma['materia'],
                        turma_id=turma['id'],
                    )
                )

        atividades = consultar_turma(
            f'/turmas/{turma["id"]}/atividades', current_user.token
        )['atividades']
        for atividade in atividades:
            prazo = datetime.fromisoformat(atividade['prazo'])
            if atividade['situacao'] == 'pendente' and prazo >= agora:
                compromissos.append(
                    CompromissoAluno(
                        id=atividade['id'],
                        titulo=atividade['titulo'],
                        tipo='Entrega',
                        data=prazo,
                        disciplina=turma['materia'],
                        turma_id=turma['id'],
                    )
                )

    compromissos.sort(key=lambda c: c.data)
    return {'compromissos': compromissos[:limite]}


@router.get('/proximas-aulas', response_model=ProximasAulasAluno)
def read_proximas_aulas(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    limite: Annotated[int, Query(ge=1, le=50)] = 5,
):
    aluno_id, _ = _aluno_e_turmas(current_user)
    if aluno_id is None:
        return {'aulas': []}

    horarios = consultar_turma(
        f'/horarios/aluno/{aluno_id}', current_user.token
    )['horarios']

    agora = datetime.now()
    aulas = []
    for horario in horarios:
        inicio = time.fromisoformat(horario['horario_inicio'])
        dias_ate = (DIAS_DA_SEMANA[horario['dia_semana']] - agora.weekday()) % 7
        data = datetime.combine(agora.date() + timedelta(days=dias_ate), inicio)
        if data < agora:
            data += timedelta(days=7)
        aulas.append(
            ProximaAulaAluno(
                turma_id=horario['turma']['id'],
                disciplina=horario['turma']['materia'],
                data=data,
                horario_fim=time.fromisoformat(horario['horario_fim']),
                local=horario['local'],
            )
        )

    aulas.sort(key=lambda a: a.data)
    return {'aulas': aulas[:limite]}


@router.get('/historico', response_model=HistoricoAluno)
def read_historico(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    _, turmas = _aluno_e_turmas(current_user)

    disciplinas = []
    for turma in turmas:
        if turma.get('encerrada_em') is None:
            continue

        desempenho = consultar_turma(
            f'/alunos/me/turmas/{turma["id"]}/desempenho', current_user.token
        )
        media = desempenho['media']
        situacao = (
            'aprovado'
            if media is not None and media >= NOTA_MINIMA_APROVACAO
            else 'reprovado'
        )
        disciplinas.append(
            {
                'turma_id': turma['id'],
                'disciplina': turma['materia'],
                'periodo_letivo': turma.get('periodo_letivo'),
                'nota_final': media,
                'frequencia_final': desempenho['frequencia'],
                'situacao': situacao,
            }
        )

    disciplinas.sort(key=lambda d: d['periodo_letivo'] or '')
    return {'disciplinas': disciplinas}
