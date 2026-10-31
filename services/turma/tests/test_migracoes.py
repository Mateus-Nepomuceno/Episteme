import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config

RAIZ = Path(__file__).resolve().parent.parent
REVISAO_ANTERIOR = '208bb74e499a'
REVISAO_OFERTA = '3933ef2c8424'
COLUNAS_OFERTA = {'codigo', 'curso_id', 'periodo_letivo', 'capacidade'}


def configuracao(url, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', url)
    config = Config(str(RAIZ / 'alembic.ini'))
    config.set_main_option('script_location', str(RAIZ / 'migrations'))
    return config


def colunas_turmas(banco):
    conexao = sqlite3.connect(banco)
    try:
        return {linha[1]: linha for linha in conexao.execute('pragma table_info(turmas)')}
    finally:
        conexao.close()


def test_migracao_adiciona_colunas_de_oferta_e_torna_professor_anulavel(tmp_path, monkeypatch):
    banco = tmp_path / 'turma.db'
    config = configuracao(f'sqlite:///{banco}', monkeypatch)

    command.upgrade(config, REVISAO_OFERTA)

    colunas = colunas_turmas(banco)
    assert COLUNAS_OFERTA <= set(colunas)
    assert colunas['professor_id'][3] == 0


def test_downgrade_remove_colunas_de_oferta(tmp_path, monkeypatch):
    banco = tmp_path / 'turma.db'
    config = configuracao(f'sqlite:///{banco}', monkeypatch)
    command.upgrade(config, REVISAO_OFERTA)

    command.downgrade(config, REVISAO_ANTERIOR)

    colunas = colunas_turmas(banco)
    assert not (COLUNAS_OFERTA & set(colunas))
    assert colunas['professor_id'][3] == 1
