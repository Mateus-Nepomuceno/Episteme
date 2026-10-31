# Serviço turma

Gerencia alunos, professores, turmas e horários. Os demais serviços consomem
os dados por HTTP. O academico, por exemplo, não guarda cópia das turmas.

## Cadastro de aluno

`POST /alunos/` e `PUT /alunos/{id}` validam `curso_id` em duas etapas:

1. Formato: precisa ser um UUID, o mesmo identificador de curso do serviço
   acadêmico. Valores como `string`, `1` ou vazio retornam `422`.
2. Existência e situação: o serviço consulta `GET /cursos/{id}` no serviço
   acadêmico. Curso inexistente ou inativo retorna `422`. Se o serviço
   acadêmico não responder, a resposta é `503`.

A URL do serviço acadêmico vem da variável `ACADEMICO_API_URL`, por exemplo
`http://127.0.0.1:8002`. Sem essa variável, o cadastro de aluno retorna `503`.

## Contrato de turmas ofertadas

### `GET /turmas/ofertas`

Lista as turmas ofertadas para um curso em um período letivo. Não exige
autenticação e não expõe alunos matriculados.

Parâmetros de consulta:

| Parâmetro        | Obrigatório | Descrição                                                                                 |
|------------------|-------------|-------------------------------------------------------------------------------------------|
| `curso_id`       | sim         | Identificador do curso no serviço academico (UUID).                                       |
| `periodo_letivo` | sim         | Período no formato `AAAA.1` ou `AAAA.2`, por exemplo `2026.2`.                            |
| `disciplina`     | não         | Trecho do nome da disciplina, sem diferenciar maiúsculas de minúsculas.                   |
| `codigo`         | não         | Código institucional da disciplina, comparado de forma exata e sem diferenciar maiúsculas. |
| `dia_semana`     | não         | `Segunda`, `Terça`, `Quarta`, `Quinta` ou `Sexta`.                                        |
| `horario_inicio` | não         | Início da faixa (`HH:MM:SS`). Considera encontros que começam nesse horário ou depois.      |
| `horario_fim`    | não         | Fim da faixa (`HH:MM:SS`). Considera encontros que terminam nesse horário ou antes.       |
| `offset`         | não         | Paginação. Padrão `0`.                                                                    |
| `limit`          | não         | Tamanho da página. Padrão `100`.                                                          |

Os filtros de horário são aplicados a cada encontro separadamente. Quando
`dia_semana` e a faixa são informados juntos, um mesmo encontro precisa
atender a todos os critérios. `horario_inicio` maior que `horario_fim`
retorna `422`.

Resposta:

```json
{
  "turmas": [
    {
      "id": "uuid",
      "nome": "Turma A",
      "codigo": "MAT101",
      "materia": "Matemática",
      "curso_id": "uuid",
      "periodo_letivo": "2026.2",
      "capacidade": 30,
      "vagas_disponiveis": 12,
      "professor": {"id": "uuid", "matricula_id": "P001"},
      "horarios": [
        {
          "dia_semana": "Segunda",
          "horario_inicio": "08:00:00",
          "horario_fim": "10:00:00",
          "local": "Sala 101"
        }
      ]
    }
  ]
}