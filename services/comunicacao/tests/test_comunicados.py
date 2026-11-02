from datetime import UTC, datetime, timedelta
from http import HTTPStatus

from comunicacao.app import app
from comunicacao.models import Comunicado
from comunicacao.security import get_current_user
from tests.conftest import como

AGORA = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


def publicar(session, titulo, dias_atras, publicado=True):
    comunicado = Comunicado(
        titulo=titulo,
        resumo=f'Resumo de {titulo}',
        corpo=f'Corpo de {titulo}',
        publicado=publicado,
    )
    comunicado.publicado_em = AGORA - timedelta(days=dias_atras)
    session.add(comunicado)
    session.commit()


def test_lista_comunicados_publicados_do_mais_recente_ao_mais_antigo(client, session):
    publicar(session, 'Antigo', 5)
    publicar(session, 'Recente', 1)
    publicar(session, 'Rascunho', 0, publicado=False)
    como()

    resposta = client.get('/comunicados')

    assert resposta.status_code == HTTPStatus.OK
    titulos = [c['titulo'] for c in resposta.json()['comunicados']]
    assert titulos == ['Recente', 'Antigo']


def test_limite_restringe_quantidade(client, session):
    for indice in range(4):
        publicar(session, f'Aviso {indice}', indice)
    como()

    resposta = client.get('/comunicados?limite=2')

    assert len(resposta.json()['comunicados']) == 2


def test_admin_publica_comunicado(client, session):
    como(e_admin=True)

    resposta = client.post(
        '/comunicados',
        json={'titulo': 'Biblioteca', 'resumo': 'Novo horário', 'corpo': 'Até 22h'},
    )

    assert resposta.status_code == HTTPStatus.CREATED
    assert resposta.json()['titulo'] == 'Biblioteca'
    assert client.get('/comunicados').json()['comunicados'][0]['titulo'] == 'Biblioteca'


def test_usuario_comum_nao_publica_comunicado(client, session):
    como(e_admin=False)

    resposta = client.post(
        '/comunicados',
        json={'titulo': 'Indevido', 'resumo': 'x', 'corpo': 'y'},
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_comunicado_sem_titulo_e_rejeitado(client, session):
    como(e_admin=True)

    resposta = client.post('/comunicados', json={'titulo': '', 'resumo': 'x', 'corpo': 'y'})

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_sem_token_nao_lista(client, session):
    app.dependency_overrides.pop(get_current_user, None)

    resposta = client.get('/comunicados')

    assert resposta.status_code == HTTPStatus.UNAUTHORIZED
