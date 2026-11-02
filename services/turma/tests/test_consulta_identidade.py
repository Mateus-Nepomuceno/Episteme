from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import patch
from uuid import uuid4

from tests.test_modulos import como, criar_aluno, criar_professor, criar_turma
from turma.models import Aluno as AlunoModelo
from turma.models import UsuarioCache
from turma.usuarios import dados_usuario

NOME_NO_IDENTIDADE = 'Rafael Oliveira'


def dados(usuario_id):
    return {
        'id': str(usuario_id),
        'nome': NOME_NO_IDENTIDADE,
        'matricula': 'P000999',
    }


def test_turma_mostra_nome_do_professor_vindo_do_identidade(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(aluno.usuario_id)

    with patch(
        'turma.usuarios.buscar_usuario',
        return_value=dados(professor.usuario_id),
    ):
        resposta = client.get(f'/turmas/{turma.id}')

    assert resposta.json()['professor']['nome'] == NOME_NO_IDENTIDADE


def test_cache_evita_nova_consulta_dentro_da_validade(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(aluno.usuario_id)

    with patch(
        'turma.usuarios.buscar_usuario',
        return_value=dados(professor.usuario_id),
    ) as consulta:
        client.get(f'/turmas/{turma.id}')
        client.get(f'/turmas/{turma.id}')

    assert consulta.call_count == 1


def test_sem_identidade_usa_ultimo_valor_em_cache(session):
    usuario_id = uuid4()
    session.add(
        UsuarioCache(
            usuario_id=usuario_id,
            nome='Nome antigo',
            matricula='P000111',
            atualizado_em=datetime_antigo(),
        )
    )
    session.commit()

    with patch('turma.usuarios.buscar_usuario', return_value=None):
        cache = dados_usuario(session, usuario_id)

    assert cache.nome == 'Nome antigo'


def test_sem_identidade_e_sem_cache_nao_inventa_nome(session):
    with patch('turma.usuarios.buscar_usuario', return_value=None):
        cache = dados_usuario(session, uuid4())

    assert cache is None


def datetime_antigo():
    return datetime.now() - timedelta(days=2)


def test_criar_aluno_envia_matricula_ao_identidade(client, session):
    usuario_id = uuid4()
    como(uuid4(), e_admin=True)

    with patch(
        'turma.routers.alunos.definir_matricula', return_value=True
    ) as envio:
        resposta = client.post(
            '/alunos/',
            json={
                'usuario_id': str(usuario_id),
                'matricula_id': '2023777777',
                'curso_id': '11111111-1111-1111-1111-111111111111',
                'ativo': True,
            },
        )

    assert resposta.status_code == HTTPStatus.CREATED
    envio.assert_called_once_with(usuario_id, '2023777777')
    assert session.query(AlunoModelo).filter_by(usuario_id=usuario_id).count() == 1


def test_criar_aluno_falha_se_identidade_nao_recebe_matricula(client, session):
    usuario_id = uuid4()
    como(uuid4(), e_admin=True)

    with patch('turma.routers.alunos.definir_matricula', return_value=False):
        resposta = client.post(
            '/alunos/',
            json={
                'usuario_id': str(usuario_id),
                'matricula_id': '2023888888',
                'curso_id': '11111111-1111-1111-1111-111111111111',
                'ativo': True,
            },
        )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert session.query(AlunoModelo).filter_by(usuario_id=usuario_id).count() == 0
