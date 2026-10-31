from http import HTTPStatus

import httpx
from fastapi import FastAPI, HTTPException, Request, Response

from academico.routers import cursos, disciplinas, matriculas, situacao
from academico.routers.periodos_matricula import (
    router as periodos_matricula_router,
)
from academico.schemas import Mensagem
from academico.settings import Settings

settings = Settings()


app = FastAPI()


@app.post('/auth/token', include_in_schema=False)
async def encaminhar_token(request: Request):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resposta = await client.post(
                f'{settings.IDENTIDADE_API_URL.rstrip("/")}/auth/token',
                content=await request.body(),
                headers={
                    'content-type': request.headers.get(
                        'content-type',
                        'application/x-www-form-urlencoded',
                    )
                },
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail='Não foi possível acessar o serviço de identidade',
        ) from exc

    return Response(
        content=resposta.content,
        status_code=resposta.status_code,
        headers={
            'content-type': resposta.headers.get(
                'content-type',
                'application/json',
            )
        },
    )


app.include_router(cursos.router)
app.include_router(disciplinas.router)
app.include_router(matriculas.router)
app.include_router(situacao.router)
app.include_router(periodos_matricula_router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Mensagem)
def read_root():
    return {'mensagem': 'OK'}
