from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from academico.app import app
from academico.models import Curso, PeriodoMatricula
from academico.security import CurrentUser, get_current_user


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

    assert resposta.status_code == HTTPStatus.CREATED
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

    assert resposta.status_code == HTTPStatus.FORBIDDEN


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

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


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

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


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

    assert resposta.status_code == HTTPStatus.OK
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

    assert resposta.status_code == HTTPStatus.OK
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

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json()["status"] == "encerrado"


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
        "academico.turma_client.httpx.get",
        return_value=resposta_turma_simulada(curso.id),
    ):
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(uuid4())],
            },
        )

    assert resposta.status_code == HTTPStatus.CONFLICT
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
        "academico.turma_client.httpx.get",
        return_value=resposta_turma_simulada(curso.id),
    ):
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(uuid4())],
            },
        )

    assert resposta.status_code == HTTPStatus.FORBIDDEN
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
        "academico.turma_client.httpx.get",
        return_value=resposta_turma_simulada(curso.id),
    ):
        resposta = client.post(
            "/matricula/solicitar",
            json={
                "periodo_letivo": "2026.2",
                "turmas_ids": [str(turma_solicitada)],
            },
        )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resposta.json()["detail"] == (
        "Uma ou mais turmas solicitadas não estão disponíveis neste período"
    )


CAPACIDADE_TURMA = 30
VAGAS_TURMA = 12


def criar_periodo_para_teste_listagem(session, curso_id, turma_ids, intervalo=None):
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    data_inicio, data_fim = intervalo or (
        agora - timedelta(hours=1),
        agora + timedelta(days=2),
    )

    periodo = PeriodoMatricula(
        periodo_letivo="2026.2",
        data_inicial=data_inicio,
        data_final=data_fim,
        cursos_ids=[str(curso_id)],
        tipo="regular",
        turmas_ids=[str(turma_id) for turma_id in turma_ids],
        status="agendado",
    )

    session.add(periodo)
    session.commit()
    session.refresh(periodo)
    return periodo


def mock_resposta_turma(payload, status_code=200):
    resposta = Mock()
    resposta.status_code = status_code
    resposta.is_error = status_code >= HTTPStatus.BAD_REQUEST
    resposta.json.return_value = payload
    return resposta


def turma_ofertada(turma_id, **campos):
    oferta = {
        "id": str(turma_id),
        "nome": "Turma A",
        "codigo": "MAT101",
        "materia": "Matemática",
        "curso_id": None,
        "periodo_letivo": "2026.2",
        "capacidade": 30,
        "vagas_disponiveis": 12,
        "professor": {"id": str(uuid4()), "matricula_id": "P001"},
        "horarios": [
            {
                "dia_semana": "Segunda",
                "horario_inicio": "08:00:00",
                "horario_fim": "10:00:00",
                "local": "Sala 101",
            }
        ],
    }
    oferta.update(campos)
    return oferta


def test_listar_turmas_disponiveis_retorna_oferta_completa(
    client, session, autenticar_periodo
):
    autenticar_periodo()

    curso = criar_curso_teste(session)
    turma_permitida = uuid4()

    criar_periodo_para_teste_listagem(session, curso.id, [turma_permitida])

    resposta_aluno = mock_resposta_turma({
        "id": str(uuid4()),
        "curso_id": str(curso.id),
    })
    resposta_turmas = mock_resposta_turma({
        "turmas": [
            turma_ofertada(turma_permitida),
            turma_ofertada(uuid4(), nome="Turma fora do período"),
        ],
    })

    with patch(
        "academico.turma_client.httpx.get",
        side_effect=[resposta_aluno, resposta_turmas],
    ):
        resposta = client.get(
            "/matricula/turmas-disponiveis",
            params={"periodo_letivo": "2026.2"},
        )

    assert resposta.status_code == HTTPStatus.OK
    assert len(resposta.json()["turmas"]) == 1
    turma = resposta.json()["turmas"][0]
    assert turma["id"] == str(turma_permitida)
    assert turma["nome"] == "Turma A"
    assert turma["codigo"] == "MAT101"
    assert turma["disciplina"] == "Matemática"
    assert turma["capacidade"] == CAPACIDADE_TURMA
    assert turma["vagas_disponiveis"] == VAGAS_TURMA
    assert turma["professor_matricula_id"] == "P001"
    assert turma["professor"]["matricula_id"] == "P001"
    assert turma["horarios"] == [
        {
            "dia_semana": "Segunda",
            "horario_inicio": "08:00:00",
            "horario_fim": "10:00:00",
            "local": "Sala 101",
        }
    ]


def test_listar_turmas_encaminha_filtros_ao_servico_turma(
    client, session, autenticar_periodo
):
    autenticar_periodo()

    curso = criar_curso_teste(session)
    turma_permitida = uuid4()
    criar_periodo_para_teste_listagem(session, curso.id, [turma_permitida])

    resposta_aluno = mock_resposta_turma({
        "id": str(uuid4()),
        "curso_id": str(curso.id),
    })
    resposta_turmas = mock_resposta_turma({"turmas": []})

    with patch(
        "academico.turma_client.httpx.get",
        side_effect=[resposta_aluno, resposta_turmas],
    ) as requisicao:
        resposta = client.get(
            "/matricula/turmas-disponiveis",
            params={
                "periodo_letivo": "2026.2",
                "disciplina": "Matemática",
                "codigo": "MAT101",
                "dia_semana": "Segunda",
                "horario_inicio": "08:00:00",
                "horario_fim": "12:00:00",
            },
        )

    assert resposta.status_code == HTTPStatus.OK
    url_ofertas = requisicao.call_args_list[1].args[0]
    parametros = requisicao.call_args_list[1].kwargs["params"]
    assert url_ofertas.endswith("/turmas/ofertas")
    assert parametros["curso_id"] == str(curso.id)
    assert parametros["periodo_letivo"] == "2026.2"
    assert parametros["disciplina"] == "Matemática"
    assert parametros["codigo"] == "MAT101"
    assert parametros["dia_semana"] == "Segunda"
    assert parametros["horario_inicio"] == "08:00:00"
    assert parametros["horario_fim"] == "12:00:00"


def test_listar_turmas_aceita_turma_sem_professor(
    client, session, autenticar_periodo
):
    autenticar_periodo()

    curso = criar_curso_teste(session)
    turma_permitida = uuid4()
    criar_periodo_para_teste_listagem(session, curso.id, [turma_permitida])

    resposta_aluno = mock_resposta_turma({
        "id": str(uuid4()),
        "curso_id": str(curso.id),
    })
    resposta_turmas = mock_resposta_turma({
        "turmas": [
            turma_ofertada(turma_permitida, professor=None, horarios=[]),
        ],
    })

    with patch(
        "academico.turma_client.httpx.get",
        side_effect=[resposta_aluno, resposta_turmas],
    ):
        resposta = client.get(
            "/matricula/turmas-disponiveis",
            params={"periodo_letivo": "2026.2"},
        )

    assert resposta.status_code == HTTPStatus.OK
    turma = resposta.json()["turmas"][0]
    assert turma["professor"] is None
    assert turma["professor_matricula_id"] is None
    assert turma["horarios"] == []


def test_listar_turmas_com_horario_invertido_retorna_erro(
    client, session, autenticar_periodo
):
    autenticar_periodo()

    with patch("academico.turma_client.httpx.get") as requisicao:
        resposta = client.get(
            "/matricula/turmas-disponiveis",
            params={
                "periodo_letivo": "2026.2",
                "horario_inicio": "12:00:00",
                "horario_fim": "08:00:00",
            },
        )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    requisicao.assert_not_called()


def test_listar_turmas_com_resposta_invalida_do_servico_turma(
    client, session, autenticar_periodo
):
    autenticar_periodo()

    curso = criar_curso_teste(session)
    turma_permitida = uuid4()
    criar_periodo_para_teste_listagem(session, curso.id, [turma_permitida])

    resposta_aluno = mock_resposta_turma({
        "id": str(uuid4()),
        "curso_id": str(curso.id),
    })
    resposta_turmas = mock_resposta_turma({
        "turmas": [turma_ofertada(turma_permitida, horarios="inválido")],
    })

    with patch(
        "academico.turma_client.httpx.get",
        side_effect=[resposta_aluno, resposta_turmas],
    ):
        resposta = client.get(
            "/matricula/turmas-disponiveis",
            params={"periodo_letivo": "2026.2"},
        )

    assert resposta.status_code == HTTPStatus.BAD_GATEWAY


def test_listar_turmas_sem_periodo_aberto_retorna_conflito(
    client, session, autenticar_periodo
):
    autenticar_periodo()

    curso = criar_curso_teste(session)
    agora = datetime.now(timezone.utc).replace(tzinfo=None)

    criar_periodo_para_teste_listagem(
        session,
        curso.id,
        [uuid4()],
        intervalo=(agora - timedelta(days=3), agora - timedelta(hours=1)),
    )

    with patch(
        "academico.turma_client.httpx.get"
    ) as requisicao:
        resposta = client.get(
            "/matricula/turmas-disponiveis",
            params={"periodo_letivo": "2026.2"},
        )

    assert resposta.status_code == HTTPStatus.CONFLICT
    requisicao.assert_not_called()


def test_listar_turmas_curso_nao_autorizado_retorna_forbidden(
    client, session, autenticar_periodo
):
    autenticar_periodo()

    curso = criar_curso_teste(session)

    criar_periodo_para_teste_listagem(
        session,
        uuid4(),
        [uuid4()],
    )

    resposta_aluno = mock_resposta_turma({
        "id": str(uuid4()),
        "curso_id": str(curso.id),
    })

    with patch(
        "academico.turma_client.httpx.get",
        return_value=resposta_aluno,
    ):
        resposta = client.get(
            "/matricula/turmas-disponiveis",
            params={"periodo_letivo": "2026.2"},
        )

    assert resposta.status_code == HTTPStatus.FORBIDDEN
    assert resposta.json()["detail"] == (
        "O curso do aluno não está autorizado neste período"
    )
