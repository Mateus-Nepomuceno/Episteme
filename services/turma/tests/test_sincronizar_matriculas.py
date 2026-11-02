from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from turma.models import Aluno, Professor, table_registry
from turma.sincronizar_matriculas import sincronizar


def test_sincronizar_envia_matricula_de_alunos_e_professores():
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    table_registry.metadata.create_all(engine)
    enviados = []

    with Session(engine) as session:
        session.add_all(
            [
                Aluno(
                    usuario_id=uuid4(),
                    matricula_id='2023000100',
                    curso_id='11111111-1111-1111-1111-111111111111',
                    ativo=True,
                ),
                Professor(
                    usuario_id=uuid4(), matricula_id='P0001', ativo=True
                ),
            ]
        )
        session.commit()

        def enviar(usuario_id, matricula):
            enviados.append(matricula)
            return matricula != 'P0001'

        resultado = sincronizar(session, enviar)

    assert resultado == {'total': 2, 'ok': 1, 'falhas': 1}
    assert sorted(enviados) == ['2023000100', 'P0001']
