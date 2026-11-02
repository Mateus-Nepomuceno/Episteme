from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from comunicacao.database import engine
from comunicacao.models import Comunicado

COMUNICADOS = [
    (
        'Período de matrículas e ajustes 2026.2 aberto',
        'O processo de ajustes e inclusão de disciplinas está disponível até 22 de setembro.',
        'O período de matrícula e ajuste de disciplinas para o semestre 2026.2 está aberto.',
        datetime(2026, 9, 15, 9, 0, tzinfo=UTC),
    ),
    (
        'Edital de monitoria acadêmica para o semestre',
        'Inscrições abertas para monitor bolsista e voluntário no DComp.',
        'Estão abertas as inscrições para as vagas de monitor bolsista e voluntário no DComp.',
        datetime(2026, 9, 10, 9, 0, tzinfo=UTC),
    ),
    (
        'Biblioteca Central: horário estendido até as 22h',
        'Salas de estudo em grupo e acervo geral com atendimento estendido.',
        'A Biblioteca Central passa a funcionar até as 22h, com salas de estudo em grupo.',
        datetime(2026, 9, 4, 9, 0, tzinfo=UTC),
    ),
]


def main() -> None:
    with Session(engine) as session:
        if session.scalar(select(Comunicado.id).limit(1)) is not None:
            return
        for titulo, resumo, corpo, publicado_em in COMUNICADOS:
            comunicado = Comunicado(titulo=titulo, resumo=resumo, corpo=corpo, publicado=True)
            comunicado.publicado_em = publicado_em
            session.add(comunicado)
        session.commit()


if __name__ == '__main__':
    main()
