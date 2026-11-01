from http import HTTPStatus

from identidade.settings import Settings

ORIGEM_PERMITIDA = 'http://localhost:5173'
ORIGEM_NAO_PERMITIDA = 'http://site-externo.example'


def _preflight(client, origem):
    return client.options(
        '/auth/token',
        headers={
            'Origin': origem,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'authorization',
        },
    )


def test_preflight_de_origem_permitida_recebe_cabecalho_cors(client):
    resposta = _preflight(client, ORIGEM_PERMITIDA)

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.headers['access-control-allow-origin'] == ORIGEM_PERMITIDA


def test_preflight_de_origem_fora_da_lista_nao_recebe_cabecalho_cors(client):
    resposta = _preflight(client, ORIGEM_NAO_PERMITIDA)

    assert resposta.status_code == HTTPStatus.BAD_REQUEST
    assert 'access-control-allow-origin' not in resposta.headers


def test_origens_cors_sao_lidas_da_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv(
        'CORS_ORIGINS', ' http://a.example , ,http://b.example '
    )

    assert Settings().origens_cors == [
        'http://a.example',
        'http://b.example',
    ]


def test_origem_padrao_e_o_frontend_vite():
    assert Settings.model_fields['CORS_ORIGINS'].default == ORIGEM_PERMITIDA
