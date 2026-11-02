from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from turma.identidade_client import buscar_usuario
from turma.models import UsuarioCache

VALIDADE_CACHE = timedelta(hours=1)


def dados_usuario(session: Session, usuario_id: UUID) -> UsuarioCache | None:
    cache = session.get(UsuarioCache, usuario_id)
    if cache is not None and datetime.now() - cache.atualizado_em < VALIDADE_CACHE:
        return cache

    dados = buscar_usuario(usuario_id)
    if dados is None:
        return cache

    agora = datetime.now()
    if cache is None:
        cache = UsuarioCache(
            usuario_id=usuario_id,
            nome=dados['nome'],
            matricula=dados['matricula'],
            atualizado_em=agora,
        )
        session.add(cache)
    else:
        cache.nome = dados['nome']
        cache.matricula = dados['matricula']
        cache.atualizado_em = agora
    session.commit()
    return cache


def preencher_nome_professor(session: Session, turma) -> None:
    if turma is None or turma.professor is None:
        return
    dados = dados_usuario(session, turma.professor.usuario_id)
    if dados is not None:
        turma.professor.nome = dados.nome
