from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from academico.database import engine
from academico.models import (
    AtividadeComplementar,
    Curso,
    Disciplina,
    PeriodoMatricula,
)

CURSO_ID = uuid5(NAMESPACE_URL, 'curso:CC-BACH')
ALUNO_LUCAS_ID = uuid5(NAMESPACE_URL, 'aluno:2023108420')

DISCIPLINAS = [
    ('DCOMP0045', 'Banco de Dados II', 60, 'Obrigatória', 'DCC'),
    ('DCOMP0038', 'Engenharia de Software I', 60, 'Obrigatória', 'DCC'),
    ('DCOMP0052', 'Redes de Computadores', 60, 'Obrigatória', 'DCC'),
    ('CC001', 'Introdução à Ciência da Computação', 60, 'Obrigatória', 'DCC'),
]


def main() -> None:
    with Session(engine) as session:
        if session.scalar(select(Curso.id).where(Curso.codigo == 'CC-BACH')) is not None:
            return

        curso = Curso(
            codigo='CC-BACH',
            nome='Ciência da Computação',
            tipo_formacao='Bacharelado',
            modalidade='Presencial',
            nivel_academico='Graduação',
            carga_horaria_total=3000,
            campus='Campus Central',
            duracao=8,
            documentacao=None,
            ativo=True,
        )
        curso.id = CURSO_ID
        session.add(curso)

        for codigo, nome, carga, tipo, departamento in DISCIPLINAS:
            session.add(
                Disciplina(
                    codigo=codigo,
                    nome=nome,
                    carga_horaria=carga,
                    tipo=tipo,
                    departamento=departamento,
                )
            )

        periodo = PeriodoMatricula(
            periodo_letivo='2026.2',
            data_inicial=datetime(2026, 10, 1, 8, 0),
            data_final=datetime(2026, 12, 15, 23, 59),
            cursos_ids=[str(CURSO_ID)],
            tipo='regular',
            turmas_ids=[],
            status='aberto',
        )
        session.add(periodo)

        session.add(
            AtividadeComplementar(
                aluno_id=ALUNO_LUCAS_ID,
                descricao='Monitoria em Estruturas de Dados',
                horas=20,
                situacao='aprovada',
            )
        )
        session.add(
            AtividadeComplementar(
                aluno_id=ALUNO_LUCAS_ID,
                descricao='Semana de Tecnologia',
                horas=5,
                situacao='pendente',
            )
        )
        session.commit()


if __name__ == '__main__':
    main()
