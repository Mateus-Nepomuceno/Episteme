from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_as_dataclass, mapped_column, registry

table_registry = registry()


@mapped_as_dataclass(table_registry)
class Comunicado:
    __tablename__ = 'comunicados'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default_factory=uuid4, init=False
    )
    titulo: Mapped[str]
    resumo: Mapped[str]
    corpo: Mapped[str]
    publicado: Mapped[bool] = mapped_column(default=True)
    inicio_em: Mapped[datetime | None] = mapped_column(
        DateTime, default=None
    )
    expira_em: Mapped[datetime | None] = mapped_column(
        DateTime, default=None
    )
    versao: Mapped[int] = mapped_column(
        Integer, default=1
    )
    publicado_em: Mapped[datetime] = mapped_column(
        DateTime,
        init=False,
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None),
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        init=False,
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None),
    )
