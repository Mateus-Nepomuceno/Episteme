from http import HTTPStatus

from fastapi import FastAPI

from academico.routers import cursos, disciplinas
from academico.schemas import Mensagem

app = FastAPI()

app.include_router(cursos.router)
app.include_router(disciplinas.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Mensagem)
def read_root():
    return {'mensagem': 'OK'}
