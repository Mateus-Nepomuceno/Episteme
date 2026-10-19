
import asyncio
import logging

from academico.services.periodos_matricula_service import (
    sincronizar_status_periodos,
)

logger = logging.getLogger(__name__)

INTERVALO_SEGUNDOS = 5


async def executar_scheduler_periodos() -> None:
    while True:
        # A primeira verificação acontece após o intervalo.
        await asyncio.sleep(INTERVALO_SEGUNDOS)

        try:
            quantidade = await asyncio.to_thread(
                sincronizar_status_periodos
            )

            if quantidade:
                logger.info(
                    "%s período(s) de matrícula tiveram o status atualizado",
                    quantidade,
                )

        except Exception:
            # Um erro não deve encerrar definitivamente o scheduler.
            logger.exception(
                "Erro ao atualizar os status dos períodos de matrícula"
            )
