# Serviço academico

Gerencia cursos, disciplinas, períodos de matrícula e solicitações de
matrícula. Consulta alunos e turmas no serviço `turma` e valida tokens emitidos
pelo serviço `identidade`.

## Relações com outros serviços

- `identidade` (porta 8000): emite os tokens. Este serviço encaminha
  `POST /auth/token` para ele, para que o Swagger deste serviço consiga autenticar.
- `turma` (porta 8001): fonte dos dados de aluno e das ofertas de turma. As
  chamadas levam o token do usuário, e o `turma` aplica as próprias regras.

## Configuração

Crie `services/academico/.env` com estas variáveis:

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL do banco SQLAlchemy, por exemplo `sqlite:///./database.db`. |
| `SECRET_KEY` | Chave usada para validar os tokens JWT. Deve ser a mesma do `identidade`. |
| `ALGORITHM` | Algoritmo do JWT, por exemplo `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do token em minutos. |
| `TURMA_API_URL` | URL base do serviço `turma`, por exemplo `http://127.0.0.1:8001`. |
| `IDENTIDADE_API_URL` | URL base do serviço `identidade`. Padrão `http://127.0.0.1:8000`. |

Não versione o `.env`. Ele já está no `.gitignore`.

## Execução

```bash
cd services/academico
poetry install
poetry run alembic upgrade head
poetry run fastapi dev academico/app.py --port 8002
```

A documentação interativa fica em `http://127.0.0.1:8002/docs`.

## Testes e lint

```bash
poetry run pytest
poetry run ruff check
```

## Migrações

As migrações ficam em `migrations/versions`. Gere uma nova revisão com
`poetry run alembic revision --autogenerate -m "descrição"` e aplique com
`poetry run alembic upgrade head`.

## Rotas

Regra de acesso:

- **Público:** sem token.
- **Autenticado:** exige token válido.
- **Administrador:** exige token com `e_admin` verdadeiro. Responde 403 para os demais.

| Método | Rota | Acesso |
|---|---|---|
| POST | `/cursos/` | Administrador |
| GET | `/cursos/` | Público |
| GET | `/cursos/{curso_id}` | Público |
| PUT | `/cursos/{curso_id}` | Administrador |
| DELETE | `/cursos/{curso_id}` | Administrador |
| POST | `/disciplinas/` | Administrador |
| GET | `/disciplinas/` | Público |
| GET | `/disciplinas/{disciplina_id}` | Público |
| PUT | `/disciplinas/{disciplina_id}` | Administrador |
| DELETE | `/disciplinas/{disciplina_id}` | Administrador |
| POST | `/matricula/solicitar` | Autenticado |
| GET | `/matricula/solicitacoes` | Autenticado. Aluno vê as próprias solicitações; administrador vê todas. |
| GET | `/matricula/solicitacoes/{protocolo}` | Autenticado. Aluno vê só a própria; administrador vê qualquer uma. |
| PATCH | `/matricula/solicitacoes/{protocolo}/observacao` | Administrador |
| GET | `/matricula/turmas-disponiveis` | Autenticado |
| GET | `/matricula/situacao/{matricula_aluno}` | Autenticado. Aluno vê a própria situação; administrador vê qualquer uma. |
| POST | `/periodos-matricula/` | Administrador |
| GET | `/periodos-matricula/` | Autenticado |
| GET | `/periodos-matricula/{periodo_id}` | Autenticado |
| PATCH | `/periodos-matricula/{periodo_id}/encerrar` | Administrador |
| POST | `/auth/token` | Público. Encaminha a requisição ao `identidade`. Existe para o Swagger. |

## Regras de período

O status de um período (`agendado`, `aberto` ou `encerrado`) é calculado a cada
leitura pelas datas de início e fim. Um encerramento manual é definitivo e não
reabre o período.
