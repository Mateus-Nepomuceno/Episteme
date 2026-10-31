# Serviço turma

Gerencia alunos, professores, turmas e horários. Os demais serviços consomem
os dados por HTTP. O academico, por exemplo, não guarda cópia das turmas.

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
| `horario_inicio` | não         | Início da faixa (`HH:MM:SS`). Considera encontros que começam nesse horário ou depois.     |
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
```

Regras:

- `professor` é `null` quando a turma ainda não tem professor alocado.
- `vagas_disponiveis` é `capacidade` menos a quantidade de alunos com
  `ativo = true` matriculados na turma. O valor nunca fica negativo. Se a
  turma não tem capacidade cadastrada, o campo é `null`.
- A resposta não inclui `usuario_id`, matrícula ou outros dados de alunos.

### Criação e atualização de turma

`POST /turmas/` e `PUT /turmas/{id}` exigem:

- `nome`, `materia` e `codigo` (texto);
- `curso_id` (UUID do curso no academico);
- `periodo_letivo` (formato `AAAA.1` ou `AAAA.2`);
- `capacidade` (inteiro maior que zero).

`professor_id` é opcional. Quando informado, o professor precisa existir.

Os campos `alunos`, `horarios` e `professor` continuam presentes em
`GET /turmas/{id}` e `GET /turmas/`. Esses endpoints expõem os alunos
matriculados, por isso não devem ser usados para a consulta de matrícula.
Use `GET /turmas/ofertas`.

## Observações sobre o esquema

As migrações Alembic deste serviço não criam a tabela `turmas`. O esquema
dessa tabela vem de `table_registry.metadata`. Bancos que já existem precisam
ganhar as colunas `codigo`, `curso_id`, `periodo_letivo` e `capacidade`, e a
coluna `professor_id` precisa aceitar nulo.
