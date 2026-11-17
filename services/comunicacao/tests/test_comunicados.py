from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from uuid import UUID, uuid4

from comunicacao.app import app
from comunicacao.models import Comunicado
from comunicacao.security import get_current_user
from tests.conftest import como

AGORA = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)


def publicar(
    session,
    titulo,
    dias_atras=0,
    publicado=True,
    inicio_em=None,
    expira_em=None,
):
    comunicado = Comunicado(
        titulo=titulo,
        resumo=f'Resumo de {titulo}',
        corpo=f'Corpo de {titulo}',
        publicado=publicado,
        inicio_em=inicio_em,
        expira_em=expira_em,
        versao=1,
    )
    comunicado.publicado_em = AGORA - timedelta(days=dias_atras)
    session.add(comunicado)
    session.commit()
    session.refresh(comunicado)
    return comunicado


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
    assert resposta.json()['versao'] == 1
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


# ==============================================================================
# Testes do Ciclo de Vida: Vigência, Rascunhos, Edição, Concorrência e Exclusão
# ==============================================================================


def test_admin_lista_comunicados_incluindo_rascunhos(client, session):
    publicar(session, 'Publicado 1', 1, publicado=True)
    publicar(session, 'Rascunho 1', 0, publicado=False)

    como(e_admin=True)

    # 1. Sem incluir rascunhos: lista apenas publicados
    resp_sem = client.get('/comunicados?incluir_rascunhos=false')
    assert resp_sem.status_code == HTTPStatus.OK
    titulos_sem = [c['titulo'] for c in resp_sem.json()['comunicados']]
    assert 'Publicado 1' in titulos_sem
    assert 'Rascunho 1' not in titulos_sem

    # 2. Com incluir rascunhos: lista todos
    resp_com = client.get('/comunicados?incluir_rascunhos=true')
    assert resp_com.status_code == HTTPStatus.OK
    titulos_com = [c['titulo'] for c in resp_com.json()['comunicados']]
    assert 'Publicado 1' in titulos_com
    assert 'Rascunho 1' in titulos_com


def test_usuario_comum_nao_recebe_rascunho_mesmo_solicitando(client, session):
    publicar(session, 'Publicado', 1, publicado=True)
    publicar(session, 'Rascunho Secreto', 0, publicado=False)

    como(e_admin=False)

    resposta = client.get('/comunicados?incluir_rascunhos=true')
    assert resposta.status_code == HTTPStatus.OK
    titulos = [c['titulo'] for c in resposta.json()['comunicados']]
    assert 'Publicado' in titulos
    assert 'Rascunho Secreto' not in titulos


def test_usuario_comum_nao_ve_comunicado_programado_futuro(client, session):
    hoje = datetime.now(UTC).replace(tzinfo=None)
    futuro = hoje + timedelta(days=5)

    publicar(session, 'Ativo Hoje', 1, publicado=True)
    publicar(session, 'Programado Futuro', 0, publicado=True, inicio_em=futuro)

    # 1. Aluno/Professor não recebe a notícia programada
    como(e_admin=False)
    resp_aluno = client.get('/comunicados')
    assert resp_aluno.status_code == HTTPStatus.OK
    titulos_aluno = [c['titulo'] for c in resp_aluno.json()['comunicados']]
    assert 'Ativo Hoje' in titulos_aluno
    assert 'Programado Futuro' not in titulos_aluno

    # 2. Administrador consegue visualizar no gerenciamento
    como(e_admin=True)
    resp_admin = client.get('/comunicados')
    assert resp_admin.status_code == HTTPStatus.OK
    titulos_admin = [c['titulo'] for c in resp_admin.json()['comunicados']]
    assert 'Programado Futuro' in titulos_admin


def test_usuario_comum_nao_ve_comunicado_expirado(client, session):
    hoje = datetime.now(UTC).replace(tzinfo=None)
    passado = hoje - timedelta(days=2)

    publicar(session, 'Ativo', 0, publicado=True)
    publicar(session, 'Encerrado Expirado', 5, publicado=True, expira_em=passado)

    # 1. Aluno/Professor não recebe notícia expirada
    como(e_admin=False)
    resp_aluno = client.get('/comunicados')
    titulos_aluno = [c['titulo'] for c in resp_aluno.json()['comunicados']]
    assert 'Ativo' in titulos_aluno
    assert 'Encerrado Expirado' not in titulos_aluno

    # 2. Administrador consegue visualizar a notícia expirada
    como(e_admin=True)
    resp_admin = client.get('/comunicados')
    titulos_admin = [c['titulo'] for c in resp_admin.json()['comunicados']]
    assert 'Encerrado Expirado' in titulos_admin


def test_usuario_comum_ve_comunicado_em_vigencia_correta(client, session):
    hoje = datetime.now(UTC).replace(tzinfo=None)
    inicio = hoje - timedelta(days=1)
    termino = hoje + timedelta(days=3)

    publicar(
        session,
        'Em Vigência Perfeita',
        0,
        publicado=True,
        inicio_em=inicio,
        expira_em=termino,
    )

    como(e_admin=False)
    resp = client.get('/comunicados')
    titulos = [c['titulo'] for c in resp.json()['comunicados']]
    assert 'Em Vigência Perfeita' in titulos


def test_consulta_comunicado_por_id_ativo_e_inexistente(client, session):
    comunicado = publicar(session, 'Notícia Específica', 1, publicado=True)

    como(e_admin=False)
    resp_ok = client.get(f'/comunicados/{comunicado.id}')
    assert resp_ok.status_code == HTTPStatus.OK
    assert resp_ok.json()['id'] == str(comunicado.id)
    assert resp_ok.json()['titulo'] == 'Notícia Específica'

    resp_404 = client.get(f'/comunicados/{uuid4()}')
    assert resp_404.status_code == HTTPStatus.NOT_FOUND


def test_usuario_comum_nao_acessa_comunicado_futuro_ou_expirado_por_id(client, session):
    hoje = datetime.now(UTC).replace(tzinfo=None)
    futuro = hoje + timedelta(days=7)
    passado = hoje - timedelta(days=3)

    comunicado_futuro = publicar(session, 'Futuro', 0, publicado=True, inicio_em=futuro)
    comunicado_expirado = publicar(session, 'Expirado', 5, publicado=True, expira_em=passado)
    rascunho = publicar(session, 'Rascunho ID', 0, publicado=False)

    como(e_admin=False)
    # Aluno recebe 404 em comunicados não vigentes ou rascunhos
    assert client.get(f'/comunicados/{comunicado_futuro.id}').status_code == HTTPStatus.NOT_FOUND
    assert client.get(f'/comunicados/{comunicado_expirado.id}').status_code == HTTPStatus.NOT_FOUND
    assert client.get(f'/comunicados/{rascunho.id}').status_code == HTTPStatus.NOT_FOUND

    como(e_admin=True)
    # Administrador tem acesso a todos
    assert client.get(f'/comunicados/{comunicado_futuro.id}').status_code == HTTPStatus.OK
    assert client.get(f'/comunicados/{comunicado_expirado.id}').status_code == HTTPStatus.OK
    assert client.get(f'/comunicados/{rascunho.id}').status_code == HTTPStatus.OK


def test_admin_cria_comunicado_com_periodo_e_rascunho(client, session):
    como(e_admin=True)

    inicio = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    fim = (datetime.now(UTC) + timedelta(days=10)).isoformat()

    resposta = client.post(
        '/comunicados',
        json={
            'titulo': 'Semana Acadêmica',
            'resumo': 'Palestrantes confirmados',
            'corpo': 'Texto completo do cronograma.',
            'publicado': False,
            'inicio_em': inicio,
            'expira_em': fim,
        },
    )

    assert resposta.status_code == HTTPStatus.CREATED
    dados = resposta.json()
    assert dados['titulo'] == 'Semana Acadêmica'
    assert dados['publicado'] is False
    assert dados['versao'] == 1
    assert dados['inicio_em'] is not None
    assert dados['expira_em'] is not None


def test_criacao_com_periodo_invalido_rejeitada(client, session):
    como(e_admin=True)

    inicio = (datetime.now(UTC) + timedelta(days=5)).isoformat()
    fim_anterior = (datetime.now(UTC) + timedelta(days=2)).isoformat()

    resposta = client.post(
        '/comunicados',
        json={
            'titulo': 'Data Incoerente',
            'resumo': 'Resumo',
            'corpo': 'Corpo',
            'inicio_em': inicio,
            'expira_em': fim_anterior,
        },
    )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_admin_atualiza_comunicado(client, session):
    comunicado = publicar(session, 'Título Antigo', 2, publicado=True)

    como(e_admin=True)

    novo_fim = (datetime.now(UTC) + timedelta(days=15)).isoformat()

    resposta = client.put(
        f'/comunicados/{comunicado.id}',
        json={
            'titulo': 'Título Atualizado',
            'resumo': 'Novo resumo informativo',
            'expira_em': novo_fim,
            'versao': 1,
        },
    )

    assert resposta.status_code == HTTPStatus.OK
    dados = resposta.json()
    assert dados['titulo'] == 'Título Atualizado'
    assert dados['resumo'] == 'Novo resumo informativo'
    assert dados['corpo'] == f'Corpo de Título Antigo'  # preservado
    assert dados['versao'] == 2  # incrementado
    assert dados['expira_em'] is not None


def test_usuario_comum_e_visitante_nao_atualizam_comunicado(client, session):
    comunicado = publicar(session, 'Aviso Protegido', 1)

    # 1. Aluno / Professor: 403 Forbidden
    como(e_admin=False)
    resp_aluno = client.put(
        f'/comunicados/{comunicado.id}',
        json={'titulo': 'Alteração Indevida'},
    )
    assert resp_aluno.status_code == HTTPStatus.FORBIDDEN

    # 2. Sem token: 401 Unauthorized
    app.dependency_overrides.pop(get_current_user, None)
    resp_anon = client.put(
        f'/comunicados/{comunicado.id}',
        json={'titulo': 'Alteração Sem Token'},
    )
    assert resp_anon.status_code == HTTPStatus.UNAUTHORIZED


def test_atualizacao_comunicado_inexistente_retorna_404(client, session):
    como(e_admin=True)

    resposta = client.put(
        f'/comunicados/{uuid4()}',
        json={'titulo': 'Não Existe'},
    )

    assert resposta.status_code == HTTPStatus.NOT_FOUND


def test_atualizacao_com_periodo_invalido_rejeitada(client, session):
    comunicado = publicar(session, 'Teste Periodo Update', 1)

    como(e_admin=True)

    inicio = (datetime.now(UTC) + timedelta(days=10)).isoformat()
    fim_anterior = (datetime.now(UTC) + timedelta(days=2)).isoformat()

    resposta = client.put(
        f'/comunicados/{comunicado.id}',
        json={'inicio_em': inicio, 'expira_em': fim_anterior},
    )

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_concorrencia_otimista_rejeita_versao_desatualizada(client, session):
    comunicado = publicar(session, 'Documento Concorrente', 1)
    assert comunicado.versao == 1

    como(e_admin=True)

    # Administrador 1 salva com sucesso na versão 1 -> versão vai para 2
    resp_admin1 = client.put(
        f'/comunicados/{comunicado.id}',
        json={'titulo': 'Edição do Admin 1', 'versao': 1},
    )
    assert resp_admin1.status_code == HTTPStatus.OK
    assert resp_admin1.json()['versao'] == 2

    # Administrador 2 tenta salvar enviando versão desatualizada 1
    resp_admin2 = client.put(
        f'/comunicados/{comunicado.id}',
        json={'titulo': 'Edição Conflitante do Admin 2', 'versao': 1},
    )
    assert resp_admin2.status_code == HTTPStatus.CONFLICT
    assert 'concorrência' in resp_admin2.json()['detail'].lower()

    # Administrador 2 recarrega e envia versão 2 -> sucesso
    resp_admin2_ok = client.put(
        f'/comunicados/{comunicado.id}',
        json={'titulo': 'Edição Resolvida do Admin 2', 'versao': 2},
    )
    assert resp_admin2_ok.status_code == HTTPStatus.OK
    assert resp_admin2_ok.json()['versao'] == 3


def test_admin_exclui_comunicado(client, session):
    comunicado = publicar(session, 'Comunicado para Exclusão', 1)

    como(e_admin=True)

    resp_del = client.delete(f'/comunicados/{comunicado.id}')
    assert resp_del.status_code == HTTPStatus.OK
    assert resp_del.json()['mensagem'] == 'Comunicado excluído com sucesso'

    # Confirmação de exclusão na persistência
    assert client.get(f'/comunicados/{comunicado.id}').status_code == HTTPStatus.NOT_FOUND


def test_usuario_comum_e_visitante_nao_excluem_comunicado(client, session):
    comunicado = publicar(session, 'Comunicado Protegido', 1)

    # 1. Aluno / Professor: 403 Forbidden
    como(e_admin=False)
    resp_aluno = client.delete(f'/comunicados/{comunicado.id}')
    assert resp_aluno.status_code == HTTPStatus.FORBIDDEN

    # 2. Sem token: 401 Unauthorized
    app.dependency_overrides.pop(get_current_user, None)
    resp_anon = client.delete(f'/comunicados/{comunicado.id}')
    assert resp_anon.status_code == HTTPStatus.UNAUTHORIZED

    # Confirma que o comunicado permanece intacto
    como(e_admin=True)
    assert client.get(f'/comunicados/{comunicado.id}').status_code == HTTPStatus.OK


def test_exclusao_comunicado_inexistente_retorna_404(client, session):
    como(e_admin=True)

    resposta = client.delete(f'/comunicados/{uuid4()}')

    assert resposta.status_code == HTTPStatus.NOT_FOUND


# ==============================================================================
# Validação Rigorosa, Separação de Consultas e Preservação de Caracteres
# ==============================================================================


def test_rejeicao_de_espacos_em_branco_puros_nos_campos(client, session):
    como(e_admin=True)

    # 1. Título com espaços
    resp_tit = client.post(
        '/comunicados',
        json={'titulo': '   \t  \n  ', 'resumo': 'Resumo válido', 'corpo': 'Corpo válido'},
    )
    assert resp_tit.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    # 2. Resumo com espaços
    resp_res = client.post(
        '/comunicados',
        json={'titulo': 'Título válido', 'resumo': '   ', 'corpo': 'Corpo válido'},
    )
    assert resp_res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    # 3. Corpo com espaços
    resp_corp = client.post(
        '/comunicados',
        json={'titulo': 'Título válido', 'resumo': 'Resumo válido', 'corpo': '   '},
    )
    assert resp_corp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_rejeicao_de_limites_maximos_de_tamanho(client, session):
    como(e_admin=True)

    # Título acima de 200 caracteres
    titulo_gigante = 'A' * 201
    resp_tit = client.post(
        '/comunicados',
        json={'titulo': titulo_gigante, 'resumo': 'Resumo válido', 'corpo': 'Corpo válido'},
    )
    assert resp_tit.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    # Resumo acima de 500 caracteres
    resumo_gigante = 'B' * 501
    resp_res = client.post(
        '/comunicados',
        json={'titulo': 'Título válido', 'resumo': resumo_gigante, 'corpo': 'Corpo válido'},
    )
    assert resp_res.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_preservacao_de_acentos_emojis_e_simbolos_especiais(client, session):
    como(e_admin=True)

    titulo_utf8 = '📢 Aviso: Ação & Reação — "100% Válido" (SP/BR) 🚀'
    resumo_utf8 = 'Atenção aos acentos: á, é, í, ó, ú, ç, ã, õ, â, ê, î, ô, û.'
    corpo_utf8 = '<p>Conteúdo com emojis 🎉 e caracteres: <>&"\'</p>'

    resp = client.post(
        '/comunicados',
        json={'titulo': titulo_utf8, 'resumo': resumo_utf8, 'corpo': corpo_utf8},
    )
    assert resp.status_code == HTTPStatus.CREATED
    dados = resp.json()
    assert dados['titulo'] == titulo_utf8
    assert dados['resumo'] == resumo_utf8
    assert dados['corpo'] == corpo_utf8

    # Confirmação de persistência
    comunicado_db = session.get(Comunicado, UUID(dados['id']))
    assert comunicado_db.titulo == titulo_utf8
    assert comunicado_db.resumo == resumo_utf8


def test_separacao_de_consultas_administrativas_por_situacao(client, session):
    hoje = datetime.now(UTC).replace(tzinfo=None)
    futuro = hoje + timedelta(days=5)
    passado = hoje - timedelta(days=5)

    c_ativo = publicar(session, 'Notícia Ativa', 1, publicado=True)
    c_rascunho = publicar(session, 'Notícia Rascunho', 0, publicado=False)
    c_prog = publicar(session, 'Notícia Programada', 0, publicado=True, inicio_em=futuro)
    c_exp = publicar(session, 'Notícia Expirada', 10, publicado=True, expira_em=passado)

    como(e_admin=True)

    # 1. Admin sem filtro recebe TODOS os 4
    resp_todos = client.get('/comunicados')
    assert resp_todos.status_code == HTTPStatus.OK
    ids_todos = [c['id'] for c in resp_todos.json()['comunicados']]
    assert str(c_ativo.id) in ids_todos
    assert str(c_rascunho.id) in ids_todos
    assert str(c_prog.id) in ids_todos
    assert str(c_exp.id) in ids_todos

    # 2. Admin filtra apenas rascunhos
    resp_rasc = client.get('/comunicados?situacao=rascunhos')
    ids_rasc = [c['id'] for c in resp_rasc.json()['comunicados']]
    assert str(c_rascunho.id) in ids_rasc
    assert str(c_ativo.id) not in ids_rasc
    assert str(c_prog.id) not in ids_rasc

    # 3. Admin filtra apenas programados
    resp_prog = client.get('/comunicados?situacao=programados')
    ids_prog = [c['id'] for c in resp_prog.json()['comunicados']]
    assert str(c_prog.id) in ids_prog
    assert str(c_ativo.id) not in ids_prog
    assert str(c_rascunho.id) not in ids_prog

    # 4. Admin filtra apenas expirados
    resp_exp = client.get('/comunicados?situacao=expirados')
    ids_exp = [c['id'] for c in resp_exp.json()['comunicados']]
    assert str(c_exp.id) in ids_exp
    assert str(c_ativo.id) not in ids_exp
    assert str(c_prog.id) not in ids_exp

    # 5. Admin filtra apenas publicados vigentes
    resp_pub = client.get('/comunicados?situacao=publicados')
    ids_pub = [c['id'] for c in resp_pub.json()['comunicados']]
    assert str(c_ativo.id) in ids_pub
    assert str(c_rascunho.id) not in ids_pub
    assert str(c_prog.id) not in ids_pub
    assert str(c_exp.id) not in ids_pub

    # 6. Aluno tenta consultar 'rascunhos': recebe apenas os ativos vigentes (regra no servidor)
    como(e_admin=False)
    resp_aluno = client.get('/comunicados?situacao=rascunhos')
    ids_aluno = [c['id'] for c in resp_aluno.json()['comunicados']]
    assert str(c_ativo.id) in ids_aluno
    assert str(c_rascunho.id) not in ids_aluno
    assert str(c_prog.id) not in ids_aluno
    assert str(c_exp.id) not in ids_aluno


def test_criacao_com_periodo_exatamente_igual_rejeitada(client, session):
    como(e_admin=True)
    instante = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    resp = client.post(
        '/comunicados',
        json={
            'titulo': 'Periodo Nulo',
            'resumo': 'Resumo',
            'corpo': 'Corpo',
            'inicio_em': instante,
            'expira_em': instante,
        },
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_atualizacao_com_periodo_exatamente_igual_rejeitada(client, session):
    comunicado = publicar(session, 'Periodo Igual Update', 1)
    como(e_admin=True)
    instante = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    resp = client.put(
        f'/comunicados/{comunicado.id}',
        json={'inicio_em': instante, 'expira_em': instante},
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_tratamento_de_fuso_horario_e_deslocamento(client, session):
    como(e_admin=True)
    # 15:00 no fuso de Brasília (-03:00) equivale a 18:00 UTC
    inicio_sp = '2026-11-20T15:00:00-03:00'
    # 20:00 UTC é posterior a 18:00 UTC (duração positiva de 2 horas)
    fim_utc = '2026-11-20T20:00:00Z'

    resp = client.post(
        '/comunicados',
        json={
            'titulo': 'Fuso Horario Valido',
            'resumo': 'Resumo fuso',
            'corpo': 'Corpo fuso',
            'inicio_em': inicio_sp,
            'expira_em': fim_utc,
        },
    )
    assert resp.status_code == HTTPStatus.CREATED
    dados = resp.json()
    assert dados['titulo'] == 'Fuso Horario Valido'

    # Se envio término em Brasília que na verdade é anterior ao início em UTC:
    # início 18:00 UTC, término 14:00 Brasília = 17:00 UTC (17:00 < 18:00 -> rejeitado!)
    fim_sp_anterior = '2026-11-20T14:00:00-03:00'
    resp_invalido = client.post(
        '/comunicados',
        json={
            'titulo': 'Fuso Horario Invalido',
            'resumo': 'Resumo fuso',
            'corpo': 'Corpo fuso',
            'inicio_em': inicio_sp,
            'expira_em': fim_sp_anterior,
        },
    )
    assert resp_invalido.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_limites_temporais_exatos_e_um_segundo_de_diferenca(client, session):
    agora = datetime.now(UTC).replace(tzinfo=None)

    # 1. Notícia 1 segundo no futuro: oculta para aluno
    c_futuro_1s = publicar(session, 'Futuro 1s', 0, publicado=True, inicio_em=agora + timedelta(seconds=1))

    # 2. Notícia no instante exato de início: visível para aluno
    c_inicio_exato = publicar(session, 'Inicio Exato', 0, publicado=True, inicio_em=agora)

    # 3. Notícia 1 segundo antes do encerramento: visível para aluno
    c_fim_1s_futuro = publicar(session, 'Fim 1s Futuro', 0, publicado=True, expira_em=agora + timedelta(seconds=1))

    # 4. Notícia no instante exato de encerramento: expirada, oculta para aluno
    c_fim_exato = publicar(session, 'Fim Exato', 0, publicado=True, expira_em=agora)

    # 5. Notícia 1 segundo após o encerramento: expirada, oculta para aluno
    c_expirada_1s = publicar(session, 'Expirada 1s Passado', 0, publicado=True, expira_em=agora - timedelta(seconds=1))

    # 6. Notícia sem data de encerramento: vigência perpétua ativa
    c_perpetua = publicar(session, 'Vigencia Perpetua', 0, publicado=True, expira_em=None)

    # Validação da perspectiva do Aluno
    como(e_admin=False)
    resp = client.get('/comunicados?limite=100')
    assert resp.status_code == HTTPStatus.OK
    ids_aluno = [c['id'] for c in resp.json()['comunicados']]

    assert str(c_futuro_1s.id) not in ids_aluno
    assert str(c_inicio_exato.id) in ids_aluno
    assert str(c_fim_1s_futuro.id) in ids_aluno
    assert str(c_fim_exato.id) not in ids_aluno
    assert str(c_expirada_1s.id) not in ids_aluno
    assert str(c_perpetua.id) in ids_aluno

    # Validação direta por ID
    assert client.get(f'/comunicados/{c_futuro_1s.id}').status_code == HTTPStatus.NOT_FOUND
    assert client.get(f'/comunicados/{c_inicio_exato.id}').status_code == HTTPStatus.OK
    assert client.get(f'/comunicados/{c_fim_1s_futuro.id}').status_code == HTTPStatus.OK
    assert client.get(f'/comunicados/{c_fim_exato.id}').status_code == HTTPStatus.NOT_FOUND
    assert client.get(f'/comunicados/{c_expirada_1s.id}').status_code == HTTPStatus.NOT_FOUND
    assert client.get(f'/comunicados/{c_perpetua.id}').status_code == HTTPStatus.OK


def test_semantica_timestamps_publicado_em_e_atualizado_em(client, session):
    """Garante que atualizado_em modifica a cada PUT e que publicado_em não é alterado indevidamente."""
    como(e_admin=True)

    # 1. Cria notícia publicada imediatamente
    resp_criacao = client.post(
        '/comunicados',
        json={
            'titulo': 'Semântica Original',
            'resumo': 'Resumo do teste',
            'corpo': 'Corpo do teste',
            'publicado': True,
        },
    )
    assert resp_criacao.status_code == HTTPStatus.CREATED
    dados_criados = resp_criacao.json()
    id_noticia = dados_criados['id']
    publicado_em_original = dados_criados['publicado_em']
    atualizado_em_original = dados_criados['atualizado_em']
    assert publicado_em_original is not None
    assert atualizado_em_original is not None

    # 2. Edita apenas o título da notícia já publicada
    resp_update = client.put(
        f'/comunicados/{id_noticia}',
        json={
            'titulo': 'Semântica Atualizada',
            'versao': 1,
        },
    )
    assert resp_update.status_code == HTTPStatus.OK
    dados_atualizados = resp_update.json()

    # publicado_em DEVE ser rigorosamente mantido inalterado
    assert dados_atualizados['publicado_em'] == publicado_em_original
    # atualizado_em DEVE ser atualizado para o instante da edição
    assert dados_atualizados['atualizado_em'] is not None
    assert dados_atualizados['versao'] == 2

    # 3. Cria rascunho (publicado = False)
    resp_rascunho = client.post(
        '/comunicados',
        json={
            'titulo': 'Rascunho Inicial',
            'resumo': 'Resumo rascunho',
            'corpo': 'Corpo rascunho',
            'publicado': False,
        },
    )
    assert resp_rascunho.status_code == HTTPStatus.CREATED
    id_rascunho = resp_rascunho.json()['id']
    publicado_em_rascunho = resp_rascunho.json()['publicado_em']

    # 4. Publica o rascunho através do PUT
    resp_pub_rascunho = client.put(
        f'/comunicados/{id_rascunho}',
        json={
            'publicado': True,
            'versao': 1,
        },
    )
    assert resp_pub_rascunho.status_code == HTTPStatus.OK
    dados_pub = resp_pub_rascunho.json()
    assert dados_pub['publicado'] is True
    assert dados_pub['versao'] == 2


def test_parsing_offsets_fuso_horario_e_precisao_segundos(client, session):
    """Verifica compatibilidade entre offsets de fuso (+02:00, -03:00, +05:30), UTC 'Z' e segundos."""
    como(e_admin=True)

    # Início em Tóquio (+09:00) correspondente a 10:00 UTC
    inicio_tokyo = '2026-11-10T19:00:00+09:00'
    # Fim em Fernando de Noronha (-02:00) correspondente a 18:00 UTC
    fim_noronha = '2026-11-10T16:00:00-02:00'

    resp = client.post(
        '/comunicados',
        json={
            'titulo': 'Fusos Múltiplos e Precisão',
            'resumo': 'Resumo com offsets explícitos',
            'corpo': 'Corpo com offsets explícitos',
            'publicado': True,
            'inicio_em': inicio_tokyo,
            'expira_em': fim_noronha,
        },
    )
    assert resp.status_code == HTTPStatus.CREATED
    dados = resp.json()

    # O retorno serializado em UTC deve normalizar exatamente:
    # 19:00 (+09:00) -> 10:00:00Z
    # 16:00 (-02:00) -> 18:00:00Z
    assert dados['inicio_em'] == '2026-11-10T10:00:00Z'
    assert dados['expira_em'] == '2026-11-10T18:00:00Z'

    # Teste de edição preservando fração e offset
    id_item = dados['id']
    resp_put = client.put(
        f'/comunicados/{id_item}',
        json={
            'inicio_em': '2026-11-10T11:30:45.500Z',
            'versao': 1,
        },
    )
    assert resp_put.status_code == HTTPStatus.OK
    dados_put = resp_put.json()
    assert '2026-11-10T11:30:45' in dados_put['inicio_em']
    assert dados_put['expira_em'] == '2026-11-10T18:00:00Z'




