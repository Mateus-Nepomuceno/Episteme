from datetime import time
from http import HTTPStatus
from uuid import UUID, uuid4

from turma.app import app
from turma.models import Aluno, DiaSemana, Horario, Professor, Turma
from turma.security import CurrentUser, get_current_user

CURSO_ID = '11111111-1111-1111-1111-111111111111'


def como(usuario_id, e_admin=False):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=usuario_id, email='usuario@teste.com', e_admin=e_admin
    )


def criar_aluno(session):
    aluno = Aluno(
        usuario_id=uuid4(),
        curso_id=CURSO_ID,
        ativo=True,
    )
    session.add(aluno)
    session.commit()
    session.refresh(aluno)
    return aluno


def criar_professor(session):
    professor = Professor(usuario_id=uuid4(), ativo=True)
    session.add(professor)
    session.commit()
    session.refresh(professor)
    return professor


def criar_turma(session, professor, alunos):
    turma = Turma(
        nome='Turma Redes',
        materia='Redes',
        codigo=f'RED{uuid4().hex[:4]}',
        curso_id=UUID(CURSO_ID),
        periodo_letivo='2026.2',
        capacidade=30,
        professor_id=professor.id,
        professor=professor,
        alunos=alunos,
        documentos=[],
        avisos=[],
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)
    session.add(
        Horario(
            turma_id=turma.id,
            professor_id=professor.id,
            dia_semana=DiaSemana.segunda,
            horario_inicio=time(8),
            horario_fim=time(10),
            local='Sala 101',
        )
    )
    session.commit()
    session.refresh(turma)
    return turma


def criar_modulo(client, turma_id, titulo, ordem, publicado=True):
    resposta = client.post(
        f'/turmas/{turma_id}/modulos',
        json={'titulo': titulo, 'ordem': ordem, 'publicado': publicado},
    )
    assert resposta.status_code == HTTPStatus.CREATED
    return resposta.json()


def criar_material(client, modulo_id, titulo, ordem):
    resposta = client.post(
        f'/modulos/{modulo_id}/materiais',
        json={'titulo': titulo, 'tipo': 'arquivo', 'ordem': ordem},
    )
    assert resposta.status_code == HTTPStatus.CREATED
    return resposta.json()


def test_professor_da_turma_cria_modulo_e_material(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)

    modulo = criar_modulo(client, turma.id, 'Módulo 1', 1)
    material = criar_material(client, modulo['id'], 'Slides', 1)

    assert material['tipo'] == 'arquivo'
    assert material['titulo'] == 'Slides'


def test_lista_modulos_com_materiais_ordenados(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)
    segundo = criar_modulo(client, turma.id, 'Módulo 2', 2)
    primeiro = criar_modulo(client, turma.id, 'Módulo 1', 1)
    criar_material(client, primeiro['id'], 'Material B', 2)
    criar_material(client, primeiro['id'], 'Material A', 1)

    resposta = client.get(f'/turmas/{turma.id}/modulos')

    modulos = resposta.json()['modulos']
    assert [m['titulo'] for m in modulos] == ['Módulo 1', 'Módulo 2']
    assert [m['titulo'] for m in modulos[0]['materiais']] == [
        'Material A',
        'Material B',
    ]
    assert modulos[1]['id'] == segundo['id']


def test_aluno_matriculado_ve_apenas_modulos_publicados(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    criar_modulo(client, turma.id, 'Publicado', 1)
    criar_modulo(client, turma.id, 'Rascunho', 2, publicado=False)
    como(aluno.usuario_id)

    resposta = client.get(f'/turmas/{turma.id}/modulos')

    assert [m['titulo'] for m in resposta.json()['modulos']] == ['Publicado']


def test_professor_ve_modulos_nao_publicados(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)
    criar_modulo(client, turma.id, 'Rascunho', 1, publicado=False)

    resposta = client.get(f'/turmas/{turma.id}/modulos')

    assert [m['titulo'] for m in resposta.json()['modulos']] == ['Rascunho']


def test_aluno_fora_da_turma_nao_le_modulos(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    intruso = criar_aluno(session)
    como(intruso.usuario_id)

    resposta = client.get(f'/turmas/{turma.id}/modulos')

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_outro_professor_nao_cria_modulo_em_turma_alheia(client, session):
    professor = criar_professor(session)
    outro = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(outro.usuario_id)

    resposta = client.post(
        f'/turmas/{turma.id}/modulos',
        json={'titulo': 'Invasão', 'ordem': 1, 'publicado': True},
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_aluno_nao_cria_material(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    modulo = criar_modulo(client, turma.id, 'Módulo 1', 1)
    como(aluno.usuario_id)

    resposta = client.post(
        f'/modulos/{modulo["id"]}/materiais',
        json={'titulo': 'Indevido', 'tipo': 'link', 'ordem': 1},
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_material_com_tipo_invalido_e_rejeitado(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)
    modulo = criar_modulo(client, turma.id, 'Módulo 1', 1)

    resposta = client.post(
        f'/modulos/{modulo["id"]}/materiais',
        json={'titulo': 'X', 'tipo': 'pdf', 'ordem': 1},
    )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_aluno_registra_acesso_ao_material_uma_vez(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    modulo = criar_modulo(client, turma.id, 'Módulo 1', 1)
    material = criar_material(client, modulo['id'], 'Slides', 1)
    como(aluno.usuario_id)

    primeiro = client.post(f'/materiais/{material["id"]}/acesso')
    segundo = client.post(f'/materiais/{material["id"]}/acesso')

    assert primeiro.status_code == HTTPStatus.OK
    assert primeiro.json()['material_id'] == material['id']
    assert segundo.json()['aberto_em'] == primeiro.json()['aberto_em']


def test_acesso_a_material_de_modulo_nao_publicado_nao_existe_para_aluno(
    client, session
):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    modulo = criar_modulo(client, turma.id, 'Rascunho', 1, publicado=False)
    material = criar_material(client, modulo['id'], 'Escondido', 1)
    como(aluno.usuario_id)

    resposta = client.post(f'/materiais/{material["id"]}/acesso')

    assert resposta.status_code == HTTPStatus.NOT_FOUND


def test_aluno_fora_da_turma_nao_registra_acesso(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)
    modulo = criar_modulo(client, turma.id, 'Módulo 1', 1)
    material = criar_material(client, modulo['id'], 'Slides', 1)
    intruso = criar_aluno(session)
    como(intruso.usuario_id)

    resposta = client.post(f'/materiais/{material["id"]}/acesso')

    assert resposta.status_code == HTTPStatus.NOT_FOUND
