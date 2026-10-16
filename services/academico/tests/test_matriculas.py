import httpx
from uuid import uuid4
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone

import pytest

from academico.app import app
from academico.models import (
    Curso,
    PeriodoMatricula,
    SolicitacaoMatricula,
)
from academico.security import CurrentUser, get_current_user


@pytest.fixture
def autenticar():
    def _autenticar(usuario_id=None, e_admin=False):
        usuario = CurrentUser(
            id=usuario_id or uuid4(),
            email="teste@teste.com",
            e_admin=e_admin,
        )

        app.dependency_overrides[get_current_user] = lambda: usuario

        return usuario

    return _autenticar


@pytest.fixture
def criar_solicitacao(session):
    def _criar(
        usuario_id,
        aluno_id=None,
        curso_id=None,
        periodo_letivo="2026.2",
    ):
        solicitacao = SolicitacaoMatricula(
            usuario_id=usuario_id,
            aluno_id=aluno_id or uuid4(),
            curso_id=curso_id or uuid4(),
            periodo_letivo=periodo_letivo,
            turmas_ids=[str(uuid4())],
        )

        session.add(solicitacao)
        session.commit()
        session.refresh(solicitacao)

        return solicitacao

    return _criar


def test_aluno_consulta_somente_suas_solicitacoes(
    client, autenticar, criar_solicitacao
):
    aluno = autenticar()
    propria = criar_solicitacao(usuario_id=aluno.id)
    criar_solicitacao(usuario_id=uuid4())

    resposta = client.get("/matricula/solicitacoes")

    assert resposta.status_code == 200

    solicitacoes = resposta.json()["solicitacoes"]

    assert len(solicitacoes) == 1
    assert solicitacoes[0]["protocolo"] == str(propria.protocolo)


def test_coordenacao_consulta_todas_as_solicitacoes(
    client, autenticar, criar_solicitacao
):
    autenticar(e_admin=True)

    criar_solicitacao(usuario_id=uuid4())
    criar_solicitacao(usuario_id=uuid4())

    resposta = client.get("/matricula/solicitacoes")

    assert resposta.status_code == 200
    assert len(resposta.json()["solicitacoes"]) == 2


def test_filtrar_solicitacoes_por_periodo(
    client, autenticar, criar_solicitacao
):
    autenticar(e_admin=True)

    criar_solicitacao(usuario_id=uuid4(), periodo_letivo="2026.1")
    criar_solicitacao(usuario_id=uuid4(), periodo_letivo="2026.2")

    resposta = client.get(
        "/matricula/solicitacoes",
        params={"periodo_letivo": "2026.2"},
    )

    assert resposta.status_code == 200

    solicitacoes = resposta.json()["solicitacoes"]

    assert len(solicitacoes) == 1
    assert solicitacoes[0]["periodo_letivo"] == "2026.2"


def test_filtrar_solicitacoes_por_protocolo(
    client, autenticar, criar_solicitacao
):
    autenticar(e_admin=True)

    solicitacao = criar_solicitacao(usuario_id=uuid4())

    resposta = client.get(
        "/matricula/solicitacoes",
        params={"protocolo": str(solicitacao.protocolo)},
    )

    assert resposta.status_code == 200

    solicitacoes = resposta.json()["solicitacoes"]

    assert len(solicitacoes) == 1
    assert solicitacoes[0]["protocolo"] == str(solicitacao.protocolo)


def test_protocolo_inexistente_retorna_404(
    client, autenticar
):
    autenticar(e_admin=True)

    resposta = client.get(
        f"/matricula/solicitacoes/{uuid4()}"
    )

    assert resposta.status_code == 404


def test_aluno_nao_consulta_solicitacao_de_outro(
    client, autenticar, criar_solicitacao
):
    aluno = autenticar()

    solicitacao_outro_aluno = criar_solicitacao(
        usuario_id=uuid4()
    )

    resposta = client.get(
        f"/matricula/solicitacoes/{solicitacao_outro_aluno.protocolo}"
    )

    assert resposta.status_code == 404


def test_coordenacao_consulta_solicitacao_por_protocolo(
    client, autenticar, criar_solicitacao
):
    autenticar(e_admin=True)

    solicitacao = criar_solicitacao(usuario_id=uuid4())

    resposta = client.get(
        f"/matricula/solicitacoes/{solicitacao.protocolo}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["protocolo"] == str(solicitacao.protocolo)


def test_solicitar_matricula_com_turma_simulada(
    client, session, autenticar
):
    usuario = autenticar()

    curso = Curso(
        codigo="TESTE001",
        nome="Curso de Teste",
        tipo_formacao="Bacharelado",
        modalidade="Presencial",
        nivel_academico="Superior",
        carga_horaria_total=3000,
        campus="Campus de Teste",
    )

    session.add(curso)
    session.commit()
    session.refresh(curso)

    agora = datetime.now(timezone.utc).replace(tzinfo=None)

    periodo = PeriodoMatricula(
        periodo_letivo="2026.2",
        data_inicial=agora - timedelta(days=1),
        data_final=agora + timedelta(days=5),
        cursos_ids=[str(curso.id)],
        tipo="regular",
        turmas_ids=[],
    )

    session.add(periodo)
    session.commit()

    aluno_id = uuid4()

    resposta_turma = Mock()
    resposta_turma.status_code = 200
    resposta_turma.is_error = False
    resposta_turma.json.return_value = {
        "id": str(aluno_id),
        "curso_id": str(curso.id),
    }

    with patch(
        "academico.routers.matriculas.httpx.get",
        return_value=resposta_turma,
    ) as requisicao:
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(uuid4())],
            },
        )

    assert resposta.status_code == 201
    assert resposta.json()["usuario_id"] == str(usuario.id)
    assert resposta.json()["aluno_id"] == str(aluno_id)
    assert resposta.json()["curso_id"] == str(curso.id)

    requisicao.assert_called_once()

def test_filtrar_solicitacoes_por_aluno(
    client, autenticar, criar_solicitacao
):
    autenticar(e_admin=True)

    aluno_id = uuid4()

    criar_solicitacao(
        usuario_id=uuid4(),
        aluno_id=aluno_id,
    )
    criar_solicitacao(usuario_id=uuid4())

    resposta = client.get(
        "/matricula/solicitacoes",
        params={"aluno_id": str(aluno_id)},
    )

    assert resposta.status_code == 200

    solicitacoes = resposta.json()["solicitacoes"]

    assert len(solicitacoes) == 1
    assert solicitacoes[0]["aluno_id"] == str(aluno_id)

def test_coordenacao_atualiza_observacao(
    client, autenticar, criar_solicitacao
):
    autenticar(e_admin=True)

    solicitacao = criar_solicitacao(usuario_id=uuid4())

    resposta = client.patch(
        f"/matricula/solicitacoes/{solicitacao.protocolo}/observacao",
        json={"observacao": "Documentação conferida."},
    )

    assert resposta.status_code == 200
    assert resposta.json()["observacao"] == "Documentação conferida."
    assert resposta.json()["protocolo"] == str(solicitacao.protocolo)

def test_aluno_nao_pode_atualizar_observacao(
    client, autenticar, criar_solicitacao
):
    aluno = autenticar()

    solicitacao = criar_solicitacao(
        usuario_id=aluno.id,
    )

    resposta = client.patch(
        f"/matricula/solicitacoes/{solicitacao.protocolo}/observacao",
        json={"observacao": "Tentativa de alteração."},
    )

    assert resposta.status_code == 403
    assert solicitacao.observacao is None

def test_atualizar_observacao_protocolo_inexistente(
    client, autenticar
):
    autenticar(e_admin=True)

    protocolo_inexistente = uuid4()

    resposta = client.patch(
        f"/matricula/solicitacoes/{protocolo_inexistente}/observacao",
        json={"observacao": "Teste."},
    )

    assert resposta.status_code == 404

def test_solicitar_matricula_timeout_turma(client, autenticar):
    autenticar()

    with patch(
        "academico.routers.matriculas.httpx.get",
        side_effect=httpx.TimeoutException("timeout"),
    ):
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(uuid4())],
            },
        )

    assert resposta.status_code == 504
    assert resposta.json()["detail"] == (
        "O serviço de turma demorou para responder"
    )

def test_solicitar_matricula_falha_conexao_turma(
    client, autenticar
):
    autenticar()

    with patch(
        "academico.routers.matriculas.httpx.get",
        side_effect=httpx.ConnectError("conexão recusada"),
    ):
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(uuid4())],
            },
        )

    assert resposta.status_code == 503
    assert resposta.json()["detail"] == (
        "Não foi possível acessar o serviço de turma"
    )

def test_solicitar_matricula_aluno_nao_encontrado(
    client, autenticar
):
    autenticar()

    resposta_turma = Mock()
    resposta_turma.status_code = 404
    resposta_turma.is_error = True

    with patch(
        "academico.routers.matriculas.httpx.get",
        return_value=resposta_turma,
    ):
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(uuid4())],
            },
        )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == (
        "Cadastro de aluno não encontrado"
    )

def test_solicitar_matricula_erro_interno_turma(
    client, autenticar
):
    autenticar()

    resposta_turma = Mock()
    resposta_turma.status_code = 500
    resposta_turma.is_error = True

    with patch(
        "academico.routers.matriculas.httpx.get",
        return_value=resposta_turma,
    ):
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(uuid4())],
            },
        )

    assert resposta.status_code == 502
    assert resposta.json()["detail"] == (
        "O serviço de turma retornou um erro"
    )

def test_solicitar_matricula_ids_invalidos_turma(
    client, autenticar
):
    autenticar()

    resposta_turma = Mock()
    resposta_turma.status_code = 200
    resposta_turma.is_error = False
    resposta_turma.json.return_value = {
        "id": "id-invalido",
        "curso_id": "curso-invalido",
    }

    with patch(
        "academico.routers.matriculas.httpx.get",
        return_value=resposta_turma,
    ):
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(uuid4())],
            },
        )

    assert resposta.status_code == 502
    assert resposta.json()["detail"] == (
        "O serviço de turma retornou identificadores inválidos"
    )

def test_solicitar_matricula_curso_nao_cadastrado(
    client, autenticar
):
    autenticar()

    resposta_turma = Mock()
    resposta_turma.status_code = 200
    resposta_turma.is_error = False
    resposta_turma.json.return_value = {
        "id": str(uuid4()),
        "curso_id": str(uuid4()),
    }

    with patch(
        "academico.routers.matriculas.httpx.get",
        return_value=resposta_turma,
    ):
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(uuid4())],
            },
        )

    assert resposta.status_code == 422
    assert resposta.json()["detail"] == (
        "O curso do aluno não está cadastrado no serviço acadêmico"
    )