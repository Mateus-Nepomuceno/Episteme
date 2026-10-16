from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from academico.app import app
from academico.models import Curso, PeriodoMatricula
from academico.security import CurrentUser, get_current_user
from unittest.mock import Mock, patch
from academico.services.periodos_matricula_service import (
    atualizar_status_periodos,
)

@pytest.fixture
def autenticar_periodo():
    def _autenticar(e_admin=False):
        usuario = CurrentUser(
            id=uuid4(),
            email="teste@teste.com",
            e_admin=e_admin,
        )
        app.dependency_overrides[get_current_user] = lambda: usuario
        return usuario

    return _autenticar


def criar_curso_teste(session):
    curso = Curso(
        codigo="TESTE001",
        nome="Curso de Teste",
        tipo_formacao="Bacharelado",
        modalidade="Presencial",
        nivel_academico="Superior",
        carga_horaria_total=3000,
        campus="Campus Teste",
    )

    session.add(curso)
    session.commit()
    session.refresh(curso)

    return curso


def test_coordenacao_configura_periodo(
    client, session, autenticar_periodo
):
    autenticar_periodo(e_admin=True)
    curso = criar_curso_teste(session)

    inicio = datetime.now(timezone.utc) + timedelta(days=2)
    fim = inicio + timedelta(days=5)

    resposta = client.post(
        "/periodos-matricula/",
        json={
            "periodo_letivo": "2026.2",
            "data_inicial": inicio.isoformat(),
            "data_final": fim.isoformat(),
            "cursos_ids": [str(curso.id)],
            "tipo": "regular",
            "turmas_ids": [],
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["mensagem"] == (
        "Período de matrícula configurado com sucesso"
    )
    assert resposta.json()["status"] == "agendado"


def test_aluno_nao_pode_configurar_periodo(
    client, session, autenticar_periodo
):
    autenticar_periodo(e_admin=False)
    curso = criar_curso_teste(session)

    inicio = datetime.now(timezone.utc) + timedelta(days=2)
    fim = inicio + timedelta(days=5)

    resposta = client.post(
        "/periodos-matricula/",
        json={
            "periodo_letivo": "2026.2",
            "data_inicial": inicio.isoformat(),
            "data_final": fim.isoformat(),
            "cursos_ids": [str(curso.id)],
            "tipo": "regular",
        },
    )

    assert resposta.status_code == 403


def test_periodo_rejeita_data_final_anterior_ao_inicio(
    client, session, autenticar_periodo
):
    autenticar_periodo(e_admin=True)
    curso = criar_curso_teste(session)

    inicio = datetime.now(timezone.utc) + timedelta(days=5)
    fim = inicio - timedelta(days=1)

    resposta = client.post(
        "/periodos-matricula/",
        json={
            "periodo_letivo": "2026.2",
            "data_inicial": inicio.isoformat(),
            "data_final": fim.isoformat(),
            "cursos_ids": [str(curso.id)],
            "tipo": "regular",
        },
    )

    assert resposta.status_code == 422


def test_periodo_rejeita_tipo_invalido(
    client, session, autenticar_periodo
):
    autenticar_periodo(e_admin=True)
    curso = criar_curso_teste(session)

    inicio = datetime.now(timezone.utc) + timedelta(days=2)
    fim = inicio + timedelta(days=5)

    resposta = client.post(
        "/periodos-matricula/",
        json={
            "periodo_letivo": "2026.2",
            "data_inicial": inicio.isoformat(),
            "data_final": fim.isoformat(),
            "cursos_ids": [str(curso.id)],
            "tipo": "emergencial",
        },
    )

    assert resposta.status_code == 422


def criar_periodo_teste(session, inicio, fim, status="agendado"):
    periodo = PeriodoMatricula(
        periodo_letivo="2026.2",
        data_inicial=inicio,
        data_final=fim,
        cursos_ids=[str(uuid4())],
        tipo="regular",
        turmas_ids=[],
        status=status,
    )
    session.add(periodo)
    session.commit()
    session.refresh(periodo)
    return periodo


def test_periodo_passou_a_data_inicial_fica_aberto(
    client, session, autenticar_periodo
):
    autenticar_periodo(e_admin=False)

    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    periodo = criar_periodo_teste(
        session,
        inicio=agora - timedelta(hours=1),
        fim=agora + timedelta(days=2),
    )

    resposta = client.get(
        f"/periodos-matricula/{periodo.id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "aberto"


def test_periodo_passou_a_data_final_fica_encerrado(
    client, session, autenticar_periodo
):
    autenticar_periodo(e_admin=False)

    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    periodo = criar_periodo_teste(
        session,
        inicio=agora - timedelta(days=3),
        fim=agora - timedelta(hours=1),
    )

    resposta = client.get(
        f"/periodos-matricula/{periodo.id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "encerrado"


def test_coordenacao_pode_encerrar_periodo_manualmente(
    client, session, autenticar_periodo
):
    autenticar_periodo(e_admin=True)

    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    periodo = criar_periodo_teste(
        session,
        inicio=agora + timedelta(days=2),
        fim=agora + timedelta(days=5),
    )

    resposta = client.patch(
        f"/periodos-matricula/{periodo.id}/encerrar"
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "encerrado"


from datetime import datetime, timedelta, timezone


def criar_curso_para_teste(session):
    curso = Curso(
        codigo=f"TESTE-{uuid4()}",
        nome="Curso de Teste",
        tipo_formacao="Bacharelado",
        modalidade="Presencial",
        nivel_academico="Superior",
        carga_horaria_total=3000,
        campus="Campus Teste",
    )
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return curso


def criar_periodo_aberto_para_teste(
    session,
    cursos_ids,
    turmas_ids=None,
):
    agora = datetime.now(timezone.utc).replace(tzinfo=None)

    periodo = PeriodoMatricula(
        periodo_letivo="2026.2",
        data_inicial=agora - timedelta(days=1),
        data_final=agora + timedelta(days=5),
        cursos_ids=[str(curso_id) for curso_id in cursos_ids],
        tipo="regular",
        turmas_ids=[
            str(turma_id) for turma_id in (turmas_ids or [])
        ],
        status="agendado",
    )

    session.add(periodo)
    session.commit()
    session.refresh(periodo)
    return periodo


def resposta_turma_simulada(curso_id):
    resposta = Mock()
    resposta.status_code = 200
    resposta.is_error = False
    resposta.json.return_value = {
        "id": str(uuid4()),
        "curso_id": str(curso_id),
    }
    return resposta


def test_solicitar_matricula_sem_periodo_aberto_retorna_conflito(
    client, session, autenticar_periodo
):
    autenticar_periodo()

    curso = criar_curso_para_teste(session)

    with patch(
        "academico.routers.matriculas.httpx.get",
        return_value=resposta_turma_simulada(curso.id),
    ):
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(uuid4())],
            },
        )

    assert resposta.status_code == 409
    assert "Não existe período de matrícula aberto" in (
        resposta.json()["detail"]
    )


def test_solicitar_matricula_curso_nao_autorizado_retorna_forbidden(
    client, session, autenticar_periodo
):
    autenticar_periodo()
    curso = criar_curso_para_teste(session)

    curso_nao_autorizado = uuid4()

    criar_periodo_aberto_para_teste(
        session,
        cursos_ids=[curso_nao_autorizado],
    )

    with patch(
        "academico.routers.matriculas.httpx.get",
        return_value=resposta_turma_simulada(curso.id),
    ):
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(uuid4())],
            },
        )

    assert resposta.status_code == 403
    assert resposta.json()["detail"] == (
        "O curso do aluno não está autorizado neste período de matrícula"
    )


def test_solicitar_matricula_turma_nao_permitida_retorna_422(
    client, session, autenticar_periodo
):
    autenticar_periodo()
    curso = criar_curso_para_teste(session)

    turma_permitida = uuid4()
    turma_solicitada = uuid4()

    criar_periodo_aberto_para_teste(
        session,
        cursos_ids=[curso.id],
        turmas_ids=[turma_permitida],
    )

    with patch(
        "academico.routers.matriculas.httpx.get",
        return_value=resposta_turma_simulada(curso.id),
    ):
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(turma_solicitada)],
            },
        )

    assert resposta.status_code == 422
    assert resposta.json()["detail"] == (
        "Uma ou mais turmas solicitadas não estão disponíveis neste período"
    )

def test_scheduler_atualiza_status_dos_periodos(session):
    agora = datetime(2026, 10, 20, 12, 0, 0)

    periodo_para_abrir = PeriodoMatricula(
        periodo_letivo="2026.2",
        data_inicial=agora - timedelta(hours=1),
        data_final=agora + timedelta(days=2),
        cursos_ids=[str(uuid4())],
        tipo="regular",
        turmas_ids=[],
        status="agendado",
    )

    periodo_para_encerrar = PeriodoMatricula(
        periodo_letivo="2026.2",
        data_inicial=agora - timedelta(days=3),
        data_final=agora - timedelta(minutes=1),
        cursos_ids=[str(uuid4())],
        tipo="ajuste",
        turmas_ids=[],
        status="aberto",
    )

    periodo_encerrado_manualmente = PeriodoMatricula(
        periodo_letivo="2026.2",
        data_inicial=agora + timedelta(days=1),
        data_final=agora + timedelta(days=3),
        cursos_ids=[str(uuid4())],
        tipo="regular",
        turmas_ids=[],
        status="encerrado",
    )

    session.add_all([
        periodo_para_abrir,
        periodo_para_encerrar,
        periodo_encerrado_manualmente,
    ])
    session.commit()

    quantidade = atualizar_status_periodos(
        session,
        agora=agora,
    )

    session.refresh(periodo_para_abrir)
    session.refresh(periodo_para_encerrar)
    session.refresh(periodo_encerrado_manualmente)

    assert quantidade == 2
    assert periodo_para_abrir.status == "aberto"
    assert periodo_para_encerrar.status == "encerrado"
    assert periodo_encerrado_manualmente.status == "encerrado"
