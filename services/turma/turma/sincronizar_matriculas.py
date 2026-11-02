from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from turma.identidade_client import definir_matricula
from turma.models import Aluno, Professor
from turma.settings import Settings


def sincronizar(session: Session, enviar) -> dict:
    registros = [
        *session.execute(select(Aluno.usuario_id, Aluno.matricula_id)).all(),
        *session.execute(
            select(Professor.usuario_id, Professor.matricula_id)
        ).all(),
    ]
    ok = sum(1 for r in registros if enviar(r.usuario_id, r.matricula_id))
    return {'total': len(registros), 'ok': ok, 'falhas': len(registros) - ok}


if __name__ == '__main__':
    engine = create_engine(Settings().DATABASE_URL)
    with Session(engine) as session:
        print(sincronizar(session, definir_matricula))
