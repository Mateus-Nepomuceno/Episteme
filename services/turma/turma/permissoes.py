from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.models import Aluno, Turma, TurmaAluno
from turma.security import CurrentUser


def pode_gerenciar_turma(current_user: CurrentUser, turma: Turma) -> bool:
    if current_user.e_admin:
        return True
    return turma.professor is not None and turma.professor.usuario_id == current_user.id


def esta_matriculado(session: Session, current_user: CurrentUser, turma: Turma) -> bool:
    matricula = session.scalar(
        select(TurmaAluno)
        .join(Aluno, Aluno.id == TurmaAluno.aluno_id)
        .where(TurmaAluno.turma_id == turma.id, Aluno.usuario_id == current_user.id)
    )
    return matricula is not None


def pode_acessar_turma(session: Session, current_user: CurrentUser, turma: Turma) -> bool:
    return pode_gerenciar_turma(current_user, turma) or esta_matriculado(
        session, current_user, turma
    )
