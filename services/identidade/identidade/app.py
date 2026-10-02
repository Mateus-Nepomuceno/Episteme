from http import HTTPStatus

from fastapi import FastAPI

from identidade.routers import auth, usuarios
from identidade.schemas import Mensagem

app = FastAPI()

app.include_router(auth.router)
app.include_router(usuarios.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Mensagem)
def read_root():
    return {'mensagem': 'OK'}
