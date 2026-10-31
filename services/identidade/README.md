# Serviço identidade

Cadastra usuários, valida senhas e emite os tokens JWT usados pelos demais
serviços. É o único serviço que guarda senhas.

## Relações com outros serviços

- `turma` (porta 8001) e `academico` (porta 8002) validam o token emitido aqui,
  usando a mesma `SECRET_KEY` e o mesmo `ALGORITHM`.
- Os tokens carregam `sub` (e-mail), `id` (identificador do usuário) e
  `e_admin`. Os demais serviços usam esses campos para autorizar.

## Configuração

Crie `services/identidade/.env` com estas variáveis:

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL do banco SQLAlchemy, por exemplo `sqlite:///./database.db`. |
| `SECRET_KEY` | Chave de assinatura do JWT. Deve ser igual nos três serviços. |
| `ALGORITHM` | Algoritmo do JWT, por exemplo `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do token em minutos. |

Não versione o `.env`. Ele já está no `.gitignore`.

## Execução

```bash
cd services/identidade
poetry install
poetry run alembic upgrade head
poetry run fastapi dev identidade/app.py --port 8000
```

A documentação interativa fica em `http://127.0.0.1:8000/docs`.

## Testes e lint

```bash
poetry run pytest
poetry run ruff check
```

## Regras de senha e cadastro

- Senha com no mínimo 8 caracteres. Ela é gravada como hash (argon2 via pwdlib).
- CPF é validado pelos dígitos verificadores e salvo no formato `xxx.xxx.xxx-xx`.
- Telefone é salvo no formato `+55DDNNNNNNNNN`. Aceita máscara e código do país.
- E-mail é normalizado e único.
- Cadastro público sempre cria usuário comum, mesmo que o corpo traga `e_admin`.

## Rotas

Regra de acesso:

- **Público:** sem token.
- **Autenticado:** exige token válido.
- **Dono ou administrador:** o próprio usuário ou um administrador. Os demais recebem 403.
- **Administrador:** exige token com `e_admin` verdadeiro. Os demais recebem 403.

| Método | Rota | Acesso |
|---|---|---|
| POST | `/auth/token` | Público. Recebe usuário e senha e devolve o token. |
| POST | `/usuarios/` | Público. Cria sempre usuário comum. |
| GET | `/usuarios/{usuario_id}` | Dono ou administrador. |
| PUT | `/usuarios/{usuario_id}` | Dono ou administrador. Só administrador altera `e_admin`. |
| DELETE | `/usuarios/{usuario_id}` | Administrador. |

## Migrações

As migrações ficam em `migrations/versions`. Gere uma nova revisão com
`poetry run alembic revision --autogenerate -m "descrição"` e aplique com
`poetry run alembic upgrade head`.
