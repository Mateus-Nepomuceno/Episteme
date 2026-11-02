from http import HTTPStatus

from identidade.security import criar_token_servico


def autorizar(token):
    return {'Authorization': f'Bearer {token}'}


def test_servico_consulta_usuario_com_matricula(client, user):
    resposta = client.get(
        f'/internos/usuarios/{user.id}',
        headers=autorizar(criar_token_servico('turma')),
    )

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json() == {
        'id': str(user.id),
        'nome': user.nome,
        'matricula': user.matricula,
    }


def test_token_de_usuario_nao_acessa_rota_interna(client, user_token, user):
    resposta = client.get(
        f'/internos/usuarios/{user.id}',
        headers=autorizar(user_token),
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_servico_desconhecido_e_recusado(client, user):
    resposta = client.get(
        f'/internos/usuarios/{user.id}',
        headers=autorizar(criar_token_servico('outro')),
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_token_invalido_e_recusado(client, user):
    resposta = client.get(
        f'/internos/usuarios/{user.id}',
        headers=autorizar('token-invalido'),
    )

    assert resposta.status_code == HTTPStatus.UNAUTHORIZED


def test_usuario_inexistente_devolve_404(client):
    resposta = client.get(
        '/internos/usuarios/00000000-0000-0000-0000-000000000000',
        headers=autorizar(criar_token_servico('turma')),
    )

    assert resposta.status_code == HTTPStatus.NOT_FOUND


def test_servico_busca_usuario_por_matricula(client, user):
    resposta = client.get(
        f'/internos/usuarios/por-matricula/{user.matricula}',
        headers=autorizar(criar_token_servico('turma')),
    )

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json()['id'] == str(user.id)


def test_matricula_inexistente_devolve_404(client):
    resposta = client.get(
        '/internos/usuarios/por-matricula/NAO-EXISTE',
        headers=autorizar(criar_token_servico('turma')),
    )

    assert resposta.status_code == HTTPStatus.NOT_FOUND


def test_turma_define_matricula_do_usuario(client, user):
    resposta = client.put(
        f'/internos/usuarios/{user.id}/matricula',
        json={'matricula': '2023999999'},
        headers=autorizar(criar_token_servico('turma')),
    )

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json()['matricula'] == '2023999999'


def test_academico_nao_define_matricula(client, user):
    resposta = client.put(
        f'/internos/usuarios/{user.id}/matricula',
        json={'matricula': '2023999999'},
        headers=autorizar(criar_token_servico('academico')),
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN
