from http import HTTPStatus

from fastapi import FastAPI

from usuarios.routers import admins, alunos, auth, professores
from usuarios.schemas import Mensagem

app = FastAPI()

app.include_router(alunos.router)
app.include_router(professores.router)
app.include_router(admins.router)
app.include_router(auth.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Mensagem)
def read_root():
    return {'mensagem': 'OK'}
