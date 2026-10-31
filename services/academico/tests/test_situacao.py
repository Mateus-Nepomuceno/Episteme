from http import HTTPStatus
from unittest.mock import Mock, patch


def _resposta(status_code=200, json_side_effect=None, json_value=None):
    resposta = Mock()
    resposta.status_code = status_code
    resposta.is_error = status_code >= HTTPStatus.BAD_REQUEST
    if json_side_effect is not None:
        resposta.json.side_effect = json_side_effect
    else:
        resposta.json.return_value = json_value
    return resposta


def test_situacao_escapa_matricula_na_url(client):
    with patch(
        'academico.routers.situacao.httpx.get',
        return_value=_resposta(status_code=HTTPStatus.NOT_FOUND),
    ) as requisicao:
        resposta = client.get('/matricula/situacao/2026001%3Fx%3D1')

    assert resposta.status_code == HTTPStatus.NOT_FOUND
    url = requisicao.call_args.args[0]
    assert url.endswith('/alunos/matricula_id/2026001%3Fx%3D1')


def test_situacao_resposta_que_nao_e_json_retorna_502(client):
    with patch(
        'academico.routers.situacao.httpx.get',
        return_value=_resposta(
            json_side_effect=ValueError('não é JSON'),
        ),
    ):
        resposta = client.get('/matricula/situacao/2026001')

    assert resposta.status_code == HTTPStatus.BAD_GATEWAY
