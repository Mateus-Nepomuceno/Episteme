from http import HTTPStatus

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from identidade.routers import auth, internos, usuarios
from identidade.schemas import Mensagem
from identidade.settings import Settings

settings = Settings()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origens_cors,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(internos.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Mensagem)
def read_root():
    return {'mensagem': 'OK'}
