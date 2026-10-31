from datetime import time
from http import HTTPStatus
from uuid import uuid4

from turma.models import Aluno, DiaSemana, Horario, Professor, Turma

PERIODO = '2026.2'
CAPACIDADE_PADRAO = 3
VAGAS_COM_UMA_MATRICULA_ATIVA = 2


def criar_professor(session, matricula='P001'):
    professor = Professor(
        usuario_id=uuid4(), matricula_id=matricula, ativo=True
    )
    session.add(professor)
    session.commit()
    session.refresh(professor)
    return professor


def criar_aluno(session, ativo=True):
    aluno = Aluno(
        usuario_id=uuid4(),
        matricula_id=f'A{uuid4().hex[:6]}',
        curso_id=str(uuid4()),
        ativo=ativo,
    )
    session.add(aluno)
    session.commit()
    session.refresh(aluno)
    return aluno


def criar_turma(session, curso_id, **campos):
    horarios = campos.pop('horarios', ())
    professor = campos.pop('professor', None)
    alunos = campos.pop('alunos', ())

    valores = {
        'nome': 'Turma A',
        'materia': 'Matemática',
        'codigo': 'MAT101',
        'periodo_letivo': PERIODO,
        'capacidade': CAPACIDADE_PADRAO,
    }
    valores.update(campos)

    turma = Turma(
        curso_id=curso_id,
        professor_id=professor.id if professor else None,
        professor=professor,
        alunos=list(alunos),
        avisos=[],
        documentos=[],
        **valores,
    )
    session.add(turma)
    session.commit()
    session.refresh(turma)

    for dia, inicio, fim, local in horarios:
        session.add(
            Horario(
                turma_id=turma.id,
                professor_id=professor.id if professor else _professor_padrao(session),
                dia_semana=dia,
                horario_inicio=inicio,
                horario_fim=fim,
                local=local,
            )
        )
    session.commit()
    session.refresh(turma)
    return turma


def _professor_padrao(session):
    professor = session.query(Professor).filter_by(matricula_id='PADRAO').first()
    if professor is None:
        professor = criar_professor(session, matricula='PADRAO')
    return professor.id


def consultar(client, curso_id, **params):
    return client.get(
        '/turmas/ofertas',
        params={'curso_id': str(curso_id), 'periodo_letivo': PERIODO, **params},
    )


def test_ofertas_retorna_turmas_do_curso_e_periodo(client, session):
    curso = uuid4()
    turma = criar_turma(session, curso_id=curso)
    criar_turma(session, curso_id=uuid4(), nome='Outro curso')
    criar_turma(session, curso_id=curso, nome='Outro período', periodo_letivo='2025.1')

    resposta = consultar(client, curso)

    assert resposta.status_code == HTTPStatus.OK
    turmas = resposta.json()['turmas']
    assert [item['id'] for item in turmas] == [str(turma.id)]


def test_ofertas_apresenta_identificacao_disciplina_codigo_professor_e_horarios(
    client, session
):
    curso = uuid4()
    professor = criar_professor(session, matricula='PROF-42')
    turma = criar_turma(
        session,
        curso_id=curso,
        nome='Turma A',
        materia='Cálculo I',
        codigo='MAT201',
        professor=professor,
        horarios=[
            (DiaSemana.segunda, time(8, 0), time(10, 0), 'Sala 101'),
            (DiaSemana.quarta, time(14, 0), time(16, 0), 'Lab 2'),
        ],
    )

    resposta = consultar(client, curso)

    assert resposta.status_code == HTTPStatus.OK
    item = resposta.json()['turmas'][0]
    assert item['id'] == str(turma.id)
    assert item['nome'] == 'Turma A'
    assert item['materia'] == 'Cálculo I'
    assert item['codigo'] == 'MAT201'
    assert item['curso_id'] == str(curso)
    assert item['periodo_letivo'] == PERIODO
    assert item['professor'] == {'id': str(professor.id), 'matricula_id': 'PROF-42'}
    assert sorted(item['horarios'], key=lambda h: h['dia_semana']) == [
        {
            'dia_semana': 'Quarta',
            'horario_inicio': '14:00:00',
            'horario_fim': '16:00:00',
            'local': 'Lab 2',
        },
        {
            'dia_semana': 'Segunda',
            'horario_inicio': '08:00:00',
            'horario_fim': '10:00:00',
            'local': 'Sala 101',
        },
    ]


def test_ofertas_sem_professor_retorna_professor_nulo(client, session):
    curso = uuid4()
    criar_turma(session, curso_id=curso, professor=None)

    resposta = consultar(client, curso)

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json()['turmas'][0]['professor'] is None


def test_ofertas_calcula_vagas_com_base_nas_matriculas_ativas(client, session):
    curso = uuid4()
    criar_turma(
        session,
        curso_id=curso,
        capacidade=3,
        alunos=[criar_aluno(session), criar_aluno(session, ativo=False)],
    )

    resposta = consultar(client, curso)

    turma = resposta.json()['turmas'][0]
    assert turma['capacidade'] == CAPACIDADE_PADRAO
    assert turma['vagas_disponiveis'] == VAGAS_COM_UMA_MATRICULA_ATIVA


def test_ofertas_vagas_nao_fica_negativa_com_turma_lotada(client, session):
    curso = uuid4()
    criar_turma(
        session,
        curso_id=curso,
        capacidade=1,
        alunos=[criar_aluno(session), criar_aluno(session)],
    )

    resposta = consultar(client, curso)

    assert resposta.json()['turmas'][0]['vagas_disponiveis'] == 0


def test_ofertas_nao_expoe_dados_de_alunos(client, session):
    curso = uuid4()
    aluno = criar_aluno(session)
    criar_turma(session, curso_id=curso, alunos=[aluno])

    resposta = consultar(client, curso)
    item = resposta.json()['turmas'][0]

    assert 'alunos' not in item
    texto = resposta.text
    assert str(aluno.usuario_id) not in texto
    assert aluno.matricula_id not in texto


def test_ofertas_filtra_por_disciplina_sem_diferenciar_maiusculas(
    client, session
):
    curso = uuid4()
    criar_turma(session, curso_id=curso, nome='A', materia='Matemática', codigo='MAT1')
    criar_turma(session, curso_id=curso, nome='B', materia='Física', codigo='FIS1')

    resposta = consultar(client, curso, disciplina='MATEM')

    nomes = [item['nome'] for item in resposta.json()['turmas']]
    assert nomes == ['A']


def test_ofertas_filtra_por_codigo_exato(client, session):
    curso = uuid4()
    criar_turma(session, curso_id=curso, nome='A', codigo='MAT101')
    criar_turma(session, curso_id=curso, nome='B', codigo='MAT1011')

    resposta = consultar(client, curso, codigo='mat101')

    nomes = [item['nome'] for item in resposta.json()['turmas']]
    assert nomes == ['A']


def test_ofertas_filtra_por_dia_da_semana(client, session):
    curso = uuid4()
    criar_turma(
        session,
        curso_id=curso,
        nome='Segunda',
        horarios=[(DiaSemana.segunda, time(8), time(10), 'Sala')],
    )
    criar_turma(
        session,
        curso_id=curso,
        nome='Sexta',
        horarios=[(DiaSemana.sexta, time(8), time(10), 'Sala')],
    )

    resposta = consultar(client, curso, dia_semana='Sexta')

    nomes = [item['nome'] for item in resposta.json()['turmas']]
    assert nomes == ['Sexta']


def test_ofertas_filtra_por_faixa_de_horario(client, session):
    curso = uuid4()
    criar_turma(
        session,
        curso_id=curso,
        nome='Manhã',
        horarios=[(DiaSemana.terca, time(8), time(10), 'Sala')],
    )
    criar_turma(
        session,
        curso_id=curso,
        nome='Noite',
        horarios=[(DiaSemana.terca, time(19), time(21), 'Sala')],
    )

    resposta = consultar(
        client,
        curso,
        horario_inicio='07:00:00',
        horario_fim='12:00:00',
    )

    nomes = [item['nome'] for item in resposta.json()['turmas']]
    assert nomes == ['Manhã']


def test_ofertas_combina_dia_e_horario_no_mesmo_encontro(client, session):
    curso = uuid4()
    # Turma com segunda de manhã e sexta à noite. O filtro "segunda à noite"
    # não deve casar, porque nenhum encontro atende aos dois critérios.
    criar_turma(
        session,
        curso_id=curso,
        nome='Mista',
        horarios=[
            (DiaSemana.segunda, time(8), time(10), 'Sala'),
            (DiaSemana.sexta, time(19), time(21), 'Sala'),
        ],
    )

    resposta = consultar(
        client,
        curso,
        dia_semana='Segunda',
        horario_inicio='18:00:00',
    )

    assert resposta.json()['turmas'] == []


def test_ofertas_combina_filtros_de_disciplina_e_horario(client, session):
    curso = uuid4()
    criar_turma(
        session,
        curso_id=curso,
        nome='Alvo',
        materia='Física',
        horarios=[(DiaSemana.quarta, time(9), time(11), 'Lab')],
    )
    criar_turma(
        session,
        curso_id=curso,
        nome='Outra',
        materia='Química',
        horarios=[(DiaSemana.quarta, time(9), time(11), 'Lab')],
    )

    resposta = consultar(
        client,
        curso,
        disciplina='física',
        dia_semana='Quarta',
        horario_inicio='08:00:00',
        horario_fim='12:00:00',
    )

    nomes = [item['nome'] for item in resposta.json()['turmas']]
    assert nomes == ['Alvo']


def test_ofertas_rejeita_faixa_de_horario_invertida(client, session):
    resposta = consultar(
        client,
        uuid4(),
        horario_inicio='12:00:00',
        horario_fim='08:00:00',
    )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_ofertas_exige_curso_e_periodo_validos(client, session):
    sem_curso = client.get('/turmas/ofertas', params={'periodo_letivo': PERIODO})
    periodo_invalido = client.get(
        '/turmas/ofertas',
        params={'curso_id': str(uuid4()), 'periodo_letivo': '2026-2'},
    )

    assert sem_curso.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert periodo_invalido.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_ofertas_pagina_resultados(client, session):
    curso = uuid4()
    for indice in range(3):
        criar_turma(session, curso_id=curso, nome=f'Turma {indice}')

    resposta = consultar(client, curso, offset=1, limit=1)

    nomes = [item['nome'] for item in resposta.json()['turmas']]
    assert nomes == ['Turma 1']
