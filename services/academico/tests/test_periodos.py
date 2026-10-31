from datetime import datetime, timedelta, timezone
from uuid import uuid4

from academico.models import PeriodoMatricula
from academico.periodos import calcular_status

AGORA = datetime(2026, 10, 20, 12, 0, 0)


def criar_periodo(status, data_inicial, data_final):
    return PeriodoMatricula(
        periodo_letivo='2026.2',
        data_inicial=data_inicial,
        data_final=data_final,
        cursos_ids=[str(uuid4())],
        tipo='regular',
        turmas_ids=[],
        status=status,
    )


def test_calcular_status_agendado_antes_da_data_inicial():
    periodo = criar_periodo(
        'agendado', AGORA + timedelta(days=1), AGORA + timedelta(days=3)
    )

    assert calcular_status(periodo, AGORA) == 'agendado'


def test_calcular_status_aberto_entre_as_datas():
    periodo = criar_periodo(
        'agendado', AGORA - timedelta(hours=1), AGORA + timedelta(days=2)
    )

    assert calcular_status(periodo, AGORA) == 'aberto'


def test_calcular_status_encerrado_apos_data_final():
    periodo = criar_periodo(
        'aberto', AGORA - timedelta(days=3), AGORA - timedelta(minutes=1)
    )

    assert calcular_status(periodo, AGORA) == 'encerrado'


def test_calcular_status_manter_encerramento_manual():
    periodo = criar_periodo(
        'encerrado', AGORA + timedelta(days=1), AGORA + timedelta(days=3)
    )

    assert calcular_status(periodo, AGORA) == 'encerrado'


def test_calcular_status_normaliza_agora_com_fuso():
    periodo = criar_periodo(
        'agendado', AGORA - timedelta(hours=1), AGORA + timedelta(days=2)
    )
    agora_com_fuso = AGORA.replace(tzinfo=timezone(timedelta(hours=-3)))

    assert calcular_status(periodo, agora_com_fuso) == 'aberto'
