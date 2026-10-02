from http import HTTPStatus

from fastapi import FastAPI

from usuarios.routers import auth, users
from usuarios.schemas import Mensagem

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Mensagem)
def read_root():
    return {'message': 'OK'}