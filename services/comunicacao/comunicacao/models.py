from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_as_dataclass, mapped_column, registry

table_registry = registry()


@mapped_as_dataclass(table_registry)
class Comunicado:
    __tablename__ = 'comunicados'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    titulo: Mapped[str]
    resumo: Mapped[str]
    corpo: Mapped[str]
    publicado: Mapped[bool] = mapped_column(default=True)
    publicado_em: Mapped[datetime] = mapped_column(
        DateTime, init=False, default=datetime.now
    )
