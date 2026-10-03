from http import HTTPStatus

from fastapi import FastAPI

from turma.routers import alunos, professores
from turma.schemas import Mensagem

app = FastAPI()

app.include_router(alunos.router)
app.include_router(professores.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Mensagem)
def read_root():
    return {'mensagem': 'OK'}
