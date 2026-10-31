# Serviço turma

Gerencia alunos, professores, turmas e horários.

## Cadastro de aluno

`POST /alunos/` e `PUT /alunos/{id}` validam `curso_id` em duas etapas:

1. Formato: precisa ser um UUID, o mesmo identificador de curso do serviço
   acadêmico. Valores como `string`, `1` ou vazio retornam `422`.
2. Existência e situação: o serviço consulta `GET /cursos/{id}` no serviço
   acadêmico. Curso inexistente ou inativo retorna `422`. Se o serviço
   acadêmico não responder, a resposta é `503`.

A URL do serviço acadêmico vem da variável `ACADEMICO_API_URL`, por exemplo
`http://127.0.0.1:8002`. Sem essa variável, o cadastro de aluno retorna `503`.
