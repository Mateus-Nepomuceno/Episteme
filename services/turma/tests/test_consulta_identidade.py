from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import patch
from uuid import uuid4

from tests.conftest import usuario_da
from tests.test_modulos import como, criar_aluno, criar_professor, criar_turma
from turma.models import Aluno as AlunoModelo
from turma.models import Professor, UsuarioCache
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

    consultas_do_professor = [
        chamada
        for chamada in consulta.call_args_list
        if chamada.args[0] == professor.usuario_id
    ]
    assert len(consultas_do_professor) == 1


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
        'turma.usuarios.buscar_usuario_por_matricula',
        return_value={'id': str(usuario_id), 'nome': 'Aluno', 'matricula': '2023777777'},
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
    envio.assert_called_once_with('2023777777')
    assert session.query(AlunoModelo).filter_by(usuario_id=usuario_id).count() == 1


def test_criar_aluno_falha_se_identidade_nao_recebe_matricula(client, session):
    usuario_id = uuid4()
    como(uuid4(), e_admin=True)

    with patch('turma.usuarios.buscar_usuario_por_matricula', return_value=None):
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


def test_turmas_do_aluno_trazem_matricula_de_cada_professor_com_cache_frio(
    client, session
):
    professor_a = Professor(usuario_id=usuario_da('P7001'), ativo=True)
    professor_b = Professor(usuario_id=usuario_da('P7002'), ativo=True)
    session.add_all([professor_a, professor_b])
    session.commit()
    session.refresh(professor_a)
    session.refresh(professor_b)
    aluno = criar_aluno(session)
    criar_turma(session, professor_a, [aluno])
    criar_turma(session, professor_b, [aluno])
    como(aluno.usuario_id)

    resposta = client.get(f'/turmas/aluno/{aluno.id}')

    matriculas = sorted(t['professor']['matricula_id'] for t in resposta.json()['turmas'])
    assert matriculas == ['P7001', 'P7002']
