# Serviço turma

Gerencia alunos, professores, turmas e horários. Consulta o curso do aluno no
serviço `academico` antes de cadastrá-lo. Valida tokens emitidos pelo serviço
`identidade`.

## Relações com outros serviços

- `identidade` (porta 8000): emite os tokens. Este serviço valida as assinaturas.
- `academico` (porta 8002): consumidor principal. Consulta alunos por usuário
  e matrícula, e as ofertas de turma, sempre repassando o token do usuário.
  Este serviço também consulta `GET /cursos/{id}` no `academico` ao cadastrar
  ou alterar um aluno.

## Configuração

Crie `services/turma/.env` com estas variáveis:

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL do banco SQLAlchemy, por exemplo `sqlite:///./database.db`. |
| `SECRET_KEY` | Chave de validação do JWT. Deve ser igual à do `identidade`. |
| `ALGORITHM` | Algoritmo do JWT, por exemplo `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do token em minutos. |
| `ACADEMICO_API_URL` | URL base do serviço `academico`, por exemplo `http://127.0.0.1:8002`. Sem ela, o cadastro de aluno responde 503. |

Não versione o `.env`. Ele já está no `.gitignore`.

## Execução

```bash
cd services/turma
poetry install
poetry run alembic upgrade head
poetry run fastapi dev turma/app.py --port 8001
```

A documentação interativa fica em `http://127.0.0.1:8001/docs`.

## Testes e lint

```bash
poetry run pytest
poetry run ruff check
```

## Regras de dados

- Turma tem código, curso, período letivo (`AAAA.1` ou `AAAA.2`) e capacidade.
  O professor é opcional.
- `GET /turmas/ofertas` calcula `vagas_disponiveis` pelos alunos com `ativo` verdadeiro.
  A resposta não expõe dados de alunos.
- Ao cadastrar ou alterar um aluno, o `curso_id` precisa ser um UUID de curso
  existente e ativo no `academico`.
- Em uma atualização de turma, se `aluno_ids` não vier no corpo, as matrículas são mantidas.

## Rotas

Regra de acesso:

- **Público:** sem token.
- **Autenticado:** exige token válido.
- **Dono ou administrador:** o próprio usuário (aluno ou professor do registro) ou um administrador. Os demais recebem 403.
- **Professor responsável ou administrador:** o professor da turma edita só nome, matéria, documentos e avisos. Os demais campos exigem administrador.
- **Administrador:** exige token com `e_admin` verdadeiro. Os demais recebem 403.

Em `GET /turmas/` e `GET /turmas/{id}`, a lista de alunos vem preenchida só
para administrador ou para o professor da turma. Os demais recebem `alunos` vazio.

| Método | Rota | Acesso |
|---|---|---|
| POST | `/alunos/` | Administrador |
| GET | `/alunos/` | Administrador |
| GET | `/alunos/{aluno_id}` | Dono ou administrador |
| GET | `/alunos/usuario_id/{aluno_usuario_id}` | Dono ou administrador |
| GET | `/alunos/matricula_id/{aluno_matricula_id}` | Dono ou administrador |
| PUT | `/alunos/{aluno_id}` | Administrador |
| DELETE | `/alunos/{aluno_id}` | Administrador |
| POST | `/professores/` | Administrador |
| GET | `/professores/` | Administrador |
| GET | `/professores/{professor_id}` | Dono ou administrador |
| PUT | `/professores/{professor_id}` | Administrador |
| DELETE | `/professores/{professor_id}` | Administrador |
| POST | `/turmas/` | Administrador |
| GET | `/turmas/` | Público. Alunos aparecem só para administrador ou professor da turma. |
| GET | `/turmas/ofertas` | Autenticado. Filtros: curso, período, disciplina, código, dia e faixa de horário. |
| GET | `/turmas/{turma_id}` | Público. Alunos aparecem só para administrador ou professor da turma. |
| PUT | `/turmas/{turma_id}` | Professor responsável (conteúdo) ou administrador (demais campos). |
| DELETE | `/turmas/{turma_id}` | Administrador |
| POST | `/horarios/` | Administrador |
| GET | `/horarios/aluno/{aluno_id}` | Dono ou administrador |
| GET | `/horarios/professor/{professor_id}` | Dono ou administrador |
| PUT | `/horarios/{horario_id}` | Administrador |
| DELETE | `/horarios/{horario_id}` | Administrador |

## Migrações

As migrações ficam em `migrations/versions`. A revisão `3933ef2c8424` adiciona
`codigo`, `curso_id`, `periodo_letivo` e `capacidade` a `turmas` e torna
`professor_id` anulável. Bancos criados apenas pelas revisões anteriores precisam
dela para que o código funcione.

Gere uma nova revisão com `poetry run alembic revision --autogenerate -m "descrição"`
e aplique com `poetry run alembic upgrade head`.

### Banco local com esquema anterior

O arquivo `database.db` deste serviço foi criado fora das migrações deste
repositório. Ele tem a revisão `0eb32f467811` no `alembic_version` e tabelas
como `modulos`, `materiais` e `atividades`, que o código não usa. O código atual
não consegue ler esse arquivo, porque `turmas` não tem a coluna `codigo`.

Com o `DATABASE_URL` atual, `poetry run alembic upgrade head` falha com
`Can't locate revision identified by '0eb32f467811'`. O arquivo não é alterado
pelas migrações deste repositório. Para rodar o serviço
com o esquema atual, aponte `DATABASE_URL` para um arquivo novo e aplique as migrações:

```bash
DATABASE_URL=sqlite:///database_novo.db poetry run alembic upgrade head
```

Se os dados do arquivo antigo forem necessários, exporte-os manualmente antes.
