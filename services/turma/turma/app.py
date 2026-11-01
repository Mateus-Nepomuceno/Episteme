from http import HTTPStatus

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from turma.routers import alunos, horarios, professores, turmas
from turma.schemas import Mensagem
from turma.settings import Settings

settings = Settings()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origens_cors,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(alunos.router)
app.include_router(professores.router)
app.include_router(turmas.router)
app.include_router(horarios.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Mensagem)
def read_root():
    return {'mensagem': 'OK'}
