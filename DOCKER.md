# Executando as APIs com Docker Compose

Sobe os quatro serviços (identidade, turma, academico e comunicacao) com dados de desenvolvimento.

## Subir

```bash
docker compose up -d --build
```

Para parar:

```bash
docker compose down
```

Para apagar os dados e recomeçar do zero:

```bash
docker compose down -v
```

## Portas

| Serviço | Porta no host | Variável para mudar |
|---|---|---|
| identidade | 9000 | `PORTA_IDENTIDADE` |
| turma | 9001 | `PORTA_TURMA` |
| academico | 9002 | `PORTA_ACADEMICO` |
| comunicacao | 9003 | `PORTA_COMUNICACAO` |

Exemplo: `PORTA_IDENTIDADE=8100 docker compose up -d`.

## Dados de desenvolvimento

O seed roda na primeira inicialização de cada serviço (`SEED=1`, padrão). Para desligar, use `SEED=0 docker compose up -d`.

Senha de todos os usuários: `senha123456` (mude com `SEED_SENHA=...`).

| Perfil | Matrícula | Nome |
|---|---|---|
| Administrador | ADM0001 | Administrador |
| Aluno | 2023108420 | Lucas Costa |
| Aluno | 2023108421 | Beatriz Rocha |
| Aluno | 2023108422 | Gabriel Lima |
| Professor | P1000 | Rafael Oliveira |
| Professor | P1001 | Mariana Silva |
| Professor | P1002 | Juliana Alves |
| Professor | P1003 | Tatiana Costa |

O login é feito pela matrícula, em `POST /auth/token` do serviço identidade, no campo `username`.

## Configurar o frontend

No `.env` do frontend, aponte para as portas acima:

```
VITE_IDENTIDADE_API_URL=http://localhost:9000
VITE_TURMA_API_URL=http://localhost:9001
VITE_ACADEMICO_API_URL=http://localhost:9002
VITE_COMUNICACAO_API_URL=http://localhost:9003
```

## Chave secreta

Os serviços compartilham a `SECRET_KEY` para validar tokens. O padrão do compose serve só para desenvolvimento. Para usar outra, defina `SECRET_KEY` antes de subir.
