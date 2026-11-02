from datetime import date, datetime, time
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from turma.database import engine
from turma.models import (
    AcessoMaterial,
    Aluno,
    Atividade,
    Avaliacao,
    Chamada,
    DiaSemana,
    Entrega,
    Horario,
    Material,
    Modulo,
    Nota,
    Presenca,
    Professor,
    Turma,
    TurmaAluno,
)

CURSO_ID = uuid5(NAMESPACE_URL, 'curso:CC-BACH')
ALUNO_LUCAS, ALUNO_BEATRIZ, ALUNO_GABRIEL = (
    '2023108420',
    '2023108421',
    '2023108422',
)


def usuario_id(matricula: str):
    return uuid5(NAMESPACE_URL, f'usuario:{matricula}')


def aluno_id(matricula: str):
    return uuid5(NAMESPACE_URL, f'aluno:{matricula}')


def professor_id(matricula: str):
    return uuid5(NAMESPACE_URL, f'professor:{matricula}')


def turma_id(codigo: str):
    return uuid5(NAMESPACE_URL, f'turma:{codigo}')


def _alunos(session: Session, matriculas):
    alunos = []
    for matricula in matriculas:
        aluno = Aluno(
            usuario_id=usuario_id(matricula),
            curso_id=str(CURSO_ID),
            ativo=True,
        )
        aluno.id = aluno_id(matricula)
        session.add(aluno)
        alunos.append(aluno)
    return alunos


def _professores(session: Session):
    professores = {}
    for matricula in ['P1000', 'P1001', 'P1002', 'P1003']:
        professor = Professor(usuario_id=usuario_id(matricula), ativo=True)
        professor.id = professor_id(matricula)
        session.add(professor)
        professores[matricula] = professor
    return professores


def _turma(session, dados, alunos, horarios, avisos):
    codigo, materia, periodo, professor = dados
    turma = Turma(
        nome=f'{codigo} - {periodo}',
        materia=materia,
        codigo=codigo,
        curso_id=CURSO_ID,
        periodo_letivo=periodo,
        capacidade=30,
        professor_id=professor.id,
        documentos=[],
        avisos=avisos,
    )
    turma.id = turma_id(codigo)
    turma.alunos = alunos
    session.add(turma)
    session.flush()
    for dia, inicio, fim, local in horarios:
        session.add(
            Horario(
                turma_id=turma.id,
                professor_id=professor.id,
                dia_semana=dia,
                horario_inicio=inicio,
                horario_fim=fim,
                local=local,
            )
        )
    return turma


def _aviso(codigo, indice, dados):
    autor, data, titulo, mensagem = dados
    return {
        'id': str(uuid5(NAMESPACE_URL, f'aviso:{codigo}:{indice}')),
        'autor': autor,
        'data': data,
        'titulo': titulo,
        'mensagem': mensagem,
    }


def _conteudo(
    session: Session, turma: Turma, professor_nome: str, prazo_futuro
):
    modulos = []
    for ordem, titulo in enumerate(
        ['Módulo 01: Fundamentos', 'Módulo 02: Conteúdo avançado'], start=1
    ):
        modulo = Modulo(
            turma_id=turma.id, titulo=titulo, ordem=ordem, publicado=True
        )
        session.add(modulo)
        session.flush()
        session.add(
            Material(
                modulo_id=modulo.id,
                titulo=f'Material de estudo {ordem}',
                tipo='link',
                ordem=1,
                descricao='Material de estudo • Link',
            )
        )
        session.add(
            Material(
                modulo_id=modulo.id,
                titulo=f'Gravação da aula {ordem}',
                tipo='video',
                ordem=2,
                descricao='Aula gravada • Vídeo',
            )
        )
        modulos.append(modulo)

    atividade = Atividade(
        turma_id=turma.id,
        titulo='Lista de exercícios 01',
        tipo='exercicio',
        categoria='Lista de Exercícios',
        prazo=prazo_futuro,
        pontos=2.5,
        descricao='Resolva os exercícios do módulo 1.',
        publicada=True,
        modulo_id=modulos[0].id,
    )
    session.add(atividade)
    session.add(
        Atividade(
            turma_id=turma.id,
            titulo='Leitura preparatória',
            tipo='leitura',
            categoria='Leitura Complementar',
            prazo=datetime(2026, 10, 20, 23, 59),
            descricao='Leitura do capítulo 1.',
            publicada=True,
            modulo_id=modulos[0].id,
        )
    )
    session.add(
        Avaliacao(
            turma_id=turma.id,
            nome='P1',
            tipo='prova',
            data=date(2026, 9, 16),
            peso=40,
        )
    )
    session.add(
        Avaliacao(
            turma_id=turma.id,
            nome='T1',
            tipo='trabalho',
            data=date(2026, 11, 20),
            peso=60,
        )
    )
    session.flush()
    return modulos, atividade


def _notas_e_frequencia(session: Session, turma: Turma, notas, chamadas):
    avaliacoes = session.scalars(
        select(Avaliacao)
        .where(Avaliacao.turma_id == turma.id)
        .order_by(Avaliacao.nome)
    ).all()
    p1 = next(a for a in avaliacoes if a.nome == 'P1')
    for matricula, valor in notas.items():
        session.add(
            Nota(avaliacao_id=p1.id, aluno_id=aluno_id(matricula), valor=valor)
        )

    for data, presentes, matriculados in chamadas:
        chamada = Chamada(turma_id=turma.id, data=data)
        session.add(chamada)
        session.flush()
        for matricula in matriculados:
            session.add(
                Presenca(
                    chamada_id=chamada.id,
                    aluno_id=aluno_id(matricula),
                    presente=matricula in presentes,
                )
            )


def main() -> None:
    with Session(engine) as session:
        if session.scalar(select(Turma.id).limit(1)) is not None:
            return

        professores = _professores(session)
        alunos = {
            m: a
            for m, a in zip(
                [ALUNO_LUCAS, ALUNO_BEATRIZ, ALUNO_GABRIEL],
                _alunos(session, [ALUNO_LUCAS, ALUNO_BEATRIZ, ALUNO_GABRIEL]),
            )
        }
        session.flush()

        bd = _turma(
            session,
            ('DCOMP0045', 'Banco de Dados II', '2026.2', professores['P1000']),
            [alunos[ALUNO_LUCAS], alunos[ALUNO_BEATRIZ]],
            [
                (DiaSemana.segunda, time(14), time(16), 'Sala 204, Bloco B'),
                (DiaSemana.quarta, time(14), time(16), 'Sala 204, Bloco B'),
            ],
            [
                _aviso(
                    'DCOMP0045',
                    1,
                    (
                        'Prof. Dr. Rafael Oliveira',
                        '2026-10-28',
                        'Material de apoio: índices',
                        'Scripts SQL de benchmark disponíveis.',
                    ),
                )
            ],
        )
        es = _turma(
            session,
            (
                'DCOMP0038',
                'Engenharia de Software I',
                '2026.2',
                professores['P1001'],
            ),
            [alunos[ALUNO_LUCAS], alunos[ALUNO_GABRIEL]],
            [(DiaSemana.terca, time(8), time(10), 'Lab 04, Bloco C')],
            [
                _aviso(
                    'DCOMP0038',
                    1,
                    (
                        'Profa. Dra. Mariana Silva',
                        '2026-10-27',
                        'Feedback do Sprint 2',
                        'Os apontamentos já estão disponíveis.',
                    ),
                )
            ],
        )
        redes = _turma(
            session,
            (
                'DCOMP0052',
                'Redes de Computadores',
                '2026.2',
                professores['P1002'],
            ),
            [
                alunos[ALUNO_LUCAS],
                alunos[ALUNO_BEATRIZ],
                alunos[ALUNO_GABRIEL],
            ],
            [(DiaSemana.sexta, time(10), time(12), 'Lab Redes, Bloco C')],
            [],
        )
        cc = _turma(
            session,
            (
                'CC001',
                'Introdução à Ciência da Computação',
                '2025.1',
                professores['P1003'],
            ),
            [alunos[ALUNO_LUCAS]],
            [(DiaSemana.segunda, time(8), time(10), 'Sala 101, Bloco A')],
            [],
        )
        cc.encerrada_em = datetime(2025, 7, 1, 10, 0)
        session.flush()

        for turma in (bd, es, redes):
            _conteudo(session, turma, '', datetime(2026, 11, 20, 23, 59))

        _notas_e_frequencia(
            session,
            bd,
            {ALUNO_LUCAS: 8.5, ALUNO_BEATRIZ: 6.0},
            [
                (
                    date(2026, 9, 1),
                    {ALUNO_LUCAS, ALUNO_BEATRIZ},
                    [ALUNO_LUCAS, ALUNO_BEATRIZ],
                ),
                (
                    date(2026, 9, 3),
                    {ALUNO_LUCAS},
                    [ALUNO_LUCAS, ALUNO_BEATRIZ],
                ),
                (
                    date(2026, 9, 8),
                    {ALUNO_LUCAS, ALUNO_BEATRIZ},
                    [ALUNO_LUCAS, ALUNO_BEATRIZ],
                ),
            ],
        )
        _notas_e_frequencia(session, es, {ALUNO_LUCAS: 7.0}, [])

        atividade_lucas = session.scalar(
            select(Atividade).where(
                Atividade.turma_id == bd.id, Atividade.tipo == 'leitura'
            )
        )
        session.add(
            Entrega(
                atividade_id=atividade_lucas.id, aluno_id=aluno_id(ALUNO_LUCAS)
            )
        )
        material = session.scalar(
            select(Material)
            .join(Modulo, Modulo.id == Material.modulo_id)
            .where(Modulo.turma_id == bd.id, Material.tipo == 'link')
        )
        session.add(
            AcessoMaterial(
                material_id=material.id, aluno_id=aluno_id(ALUNO_LUCAS)
            )
        )

        vinculo = session.get(TurmaAluno, (cc.id, aluno_id(ALUNO_LUCAS)))
        vinculo.nota_final = 8.2
        vinculo.frequencia_final = 95
        vinculo.situacao = 'aprovado'

        session.commit()


if __name__ == '__main__':
    main()
