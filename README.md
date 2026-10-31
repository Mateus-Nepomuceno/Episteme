# Episteme Sistema Acadêmico

Sistema acadêmico dividido em três serviços HTTP (FastAPI), cada um com seu
próprio banco e sua própria suíte de testes.

## Serviços

| Serviço | Porta padrão | Responsabilidade |
|---|---|---|
| [identidade](services/identidade/README.md) | 8000 | Cadastro de usuários, senhas e emissão de tokens JWT. |
| [turma](services/turma/README.md) | 8001 | Alunos, professores, turmas e horários. |
| [academico](services/academico/README.md) | 8002 | Cursos, disciplinas, períodos e solicitações de matrícula. |

Os serviços se comunicam por HTTP. `turma` e `academico` validam o token
emitido por `identidade`, usando a mesma chave de assinatura.

## Como funciona a autorização

- Quem não tem token acessa só as rotas públicas.
- Usuário autenticado acessa as rotas de consulta permitidas.
- Criar e excluir registros acadêmicos (cursos, disciplinas, alunos, professores,
  turmas e horários) é atribuição do administrador. O administrador tem a claim
  `e_admin` no token.
- Dados pessoais de aluno e professor só ficam visíveis para o próprio titular
  ou para o administrador.
- Professor responsável edita o conteúdo da própria turma. Código, curso,
  período, capacidade, professor e lista de alunos continuam sendo do administrador.

Cada README de serviço traz a tabela de rotas com a regra de acesso de cada uma.

## Pré-requisitos

- Python 3.12
- Poetry

## Configuração

Cada serviço lê um arquivo `.env` na sua própria pasta. Esses arquivos não são
versionados. As variáveis estão descritas no README de cada serviço.

Pontos que precisam bater entre os serviços:

- `SECRET_KEY` e `ALGORITHM` são iguais em `identidade`, `turma` e `academico`.
- `turma` aponta para o `academico` em `ACADEMICO_API_URL`.
- `academico` aponta para o `turma` em `TURMA_API_URL`.

## Ordem de execução

Suba os serviços nesta ordem, porque cada um depende dos anteriores para
validar tokens ou consultar dados:

1. `identidade`
2. `turma`
3. `academico`

Em cada pasta de serviço, instale as dependências, aplique as migrações e
inicie o servidor. Os comandos completos estão no README do serviço.

## Testes

Cada serviço tem a própria suíte:

```bash
cd services/identidade && poetry run pytest
cd services/turma && poetry run pytest
cd services/academico && poetry run pytest
```

## Desenvolvimento

- Os serviços seguem gitflow: uma branch por módulo, partindo da `develop`.
- Commits seguem o padrão semântico (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`).
- O código não tem comentários. A documentação fica nos arquivos Markdown.
