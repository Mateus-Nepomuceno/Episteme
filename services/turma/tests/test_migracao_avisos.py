import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config

RAIZ = Path(__file__).resolve().parent.parent
REVISAO_ANTERIOR = '3933ef2c8424'
REVISAO_AVISOS = '5c2f8a1d9e7b'
AVISOS_ORIGINAIS = ['Prova adiada', 'Leiam o slide']


def configuracao(url, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', url)
    config = Config(str(RAIZ / 'alembic.ini'))
    config.set_main_option('script_location', str(RAIZ / 'migrations'))
    return config


def inserir_turma(banco, avisos, criado_em='2026-10-01 10:00:00.000000'):
    conexao = sqlite3.connect(banco)
    conexao.execute(
        'insert into turmas (id, nome, materia, criado_em, documentos, avisos,'
        ' codigo, curso_id, periodo_letivo, capacidade)'
        ' values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (
            uuid4().hex,
            'Turma',
            'Matéria',
            criado_em,
            '[]',
            json.dumps(avisos),
            'COD1',
            None,
            '2026.2',
            30,
        ),
    )
    conexao.commit()
    conexao.close()


def avisos_gravados(banco):
    conexao = sqlite3.connect(banco)
    try:
        return [
            json.loads(linha[0])
            for linha in conexao.execute(
                'select avisos from turmas order by criado_em'
            )
        ]
    finally:
        conexao.close()


def test_migracao_com_banco_vazio(tmp_path, monkeypatch):
    banco = tmp_path / 'turma.db'
    config = configuracao(f'sqlite:///{banco}', monkeypatch)
    command.upgrade(config, REVISAO_ANTERIOR)

    command.upgrade(config, REVISAO_AVISOS)

    assert avisos_gravados(banco) == []


def test_migracao_converte_avisos_em_texto_para_objetos(tmp_path, monkeypatch):
    banco = tmp_path / 'turma.db'
    config = configuracao(f'sqlite:///{banco}', monkeypatch)
    command.upgrade(config, REVISAO_ANTERIOR)
    inserir_turma(banco, AVISOS_ORIGINAIS)
    inserir_turma(banco, [], criado_em='2026-09-15 08:00:00.000000')

    command.upgrade(config, REVISAO_AVISOS)

    antiga, recente = avisos_gravados(banco)
    assert [aviso['mensagem'] for aviso in recente] == AVISOS_ORIGINAIS
    for aviso in recente:
        assert set(aviso) == {'id', 'autor', 'data', 'titulo', 'mensagem'}
        assert aviso['autor'] == 'Não informado'
        assert aviso['titulo'] == 'Aviso'
        assert aviso['data'] == '2026-10-01'
    assert len({aviso['id'] for aviso in recente}) == len(AVISOS_ORIGINAIS)
    assert antiga == []


def test_migracao_mantem_avisos_ja_estruturados(tmp_path, monkeypatch):
    banco = tmp_path / 'turma.db'
    config = configuracao(f'sqlite:///{banco}', monkeypatch)
    command.upgrade(config, REVISAO_ANTERIOR)
    aviso = {
        'id': str(uuid4()),
        'autor': 'Prof',
        'data': '2026-10-02',
        'titulo': 'Título',
        'mensagem': 'Texto',
    }
    inserir_turma(banco, [aviso])

    command.upgrade(config, REVISAO_AVISOS)

    assert avisos_gravados(banco) == [[aviso]]


def test_downgrade_volta_avisos_para_texto(tmp_path, monkeypatch):
    banco = tmp_path / 'turma.db'
    config = configuracao(f'sqlite:///{banco}', monkeypatch)
    command.upgrade(config, REVISAO_ANTERIOR)
    inserir_turma(banco, ['Prova adiada'])
    command.upgrade(config, REVISAO_AVISOS)

    command.downgrade(config, REVISAO_ANTERIOR)

    assert avisos_gravados(banco) == [['Prova adiada']]
