from datetime import date, datetime, time
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from turma.models import DiaSemana


class Mensagem(BaseModel):
    mensagem: str


class FiltroPaginacao(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1)


class AlunoCreate(BaseModel):
    usuario_id: UUID
    matricula_id: str
    curso_id: str
    ativo: bool = True

    @field_validator('curso_id')
    @classmethod
    def validar_curso_id(cls, valor: str) -> str:
        try:
            return str(UUID(valor))
        except ValueError:
            mensagem = (
                'curso_id deve ser o identificador (UUID) do curso '
                'cadastrado no serviço acadêmico'
            )
            raise ValueError(mensagem)


class AlunoPublic(BaseModel):
    id: UUID
    usuario_id: UUID
    matricula_id: str
    curso_id: str
    ativo: bool
    model_config = ConfigDict(from_attributes=True)


class AlunoList(BaseModel):
    alunos: list[AlunoPublic]


class ProfessorCreate(BaseModel):
    usuario_id: UUID
    matricula_id: str
    ativo: bool = True


class ProfessorPublic(BaseModel):
    id: UUID
    usuario_id: UUID
    matricula_id: str
    ativo: bool
    model_config = ConfigDict(from_attributes=True)


class ProfessorList(BaseModel):
    professores: list[ProfessorPublic]


PERIODO_LETIVO_PATTERN = r'^\d{4}\.[12]$'


class AvisoTurma(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    autor: str = Field(min_length=1)
    data: date
    titulo: str = Field(min_length=1)
    mensagem: str = Field(min_length=1)


class TurmaCreate(BaseModel):
    nome: str
    codigo: str
    materia: str
    curso_id: UUID
    periodo_letivo: str = Field(pattern=PERIODO_LETIVO_PATTERN)
    capacidade: int = Field(gt=0)
    professor_id: UUID | None = None

    aluno_ids: list[UUID] = Field(default_factory=list)
    documentos: list[str] = Field(default_factory=list)
    avisos: list[AvisoTurma] = Field(default_factory=list)


class HorarioTurmaPublic(BaseModel):
    dia_semana: DiaSemana
    horario_inicio: time
    horario_fim: time
    local: str
    model_config = ConfigDict(from_attributes=True)


class ProfessorTurmaPublic(BaseModel):
    id: UUID
    matricula_id: str
    model_config = ConfigDict(from_attributes=True)


class TurmaPublic(BaseModel):
    id: UUID
    nome: str
    codigo: str | None
    materia: str
    curso_id: UUID | None
    periodo_letivo: str | None
    capacidade: int | None
    professor: ProfessorPublic | None
    alunos: list[AlunoPublic]
    horarios: list[HorarioTurmaPublic]
    documentos: list[str]
    avisos: list[AvisoTurma]
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class TurmaList(BaseModel):
    turmas: list[TurmaPublic]


class TurmaAlunoPublic(BaseModel):
    id: UUID
    nome: str
    codigo: str | None
    materia: str
    curso_id: UUID | None
    periodo_letivo: str | None
    capacidade: int | None
    professor: ProfessorTurmaPublic | None
    horarios: list[HorarioTurmaPublic]
    encerrada_em: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class TurmaAlunoList(BaseModel):
    turmas: list[TurmaAlunoPublic]


class TurmaOfertaPublic(BaseModel):
    id: UUID
    nome: str
    codigo: str | None
    materia: str
    curso_id: UUID | None
    periodo_letivo: str | None
    capacidade: int | None
    vagas_disponiveis: int | None
    professor: ProfessorTurmaPublic | None
    horarios: list[HorarioTurmaPublic]


class TurmaOfertaList(BaseModel):
    turmas: list[TurmaOfertaPublic]


class HorarioCreate(BaseModel):
    turma_id: UUID
    professor_id: UUID
    dia_semana: DiaSemana
    horario_inicio: time
    horario_fim: time
    local: str


class HorarioPublic(BaseModel):
    id: UUID
    turma: TurmaPublic
    professor: ProfessorPublic
    dia_semana: DiaSemana
    horario_inicio: time
    horario_fim: time
    local: str
    model_config = ConfigDict(from_attributes=True)


class HorarioList(BaseModel):
    horarios: list[HorarioPublic]


class AvisoAluno(AvisoTurma):
    turma_id: UUID
    disciplina: str


class AvisosAlunoList(BaseModel):
    avisos: list[AvisoAluno]


TipoMaterial = Literal['arquivo', 'video', 'link']


class ModuloCreate(BaseModel):
    titulo: str = Field(min_length=1)
    ordem: int = Field(ge=0)
    publicado: bool = True


class MaterialCreate(BaseModel):
    titulo: str = Field(min_length=1)
    descricao: str | None = None
    tipo: TipoMaterial
    ordem: int = Field(ge=0)


class MaterialPublic(BaseModel):
    id: UUID
    titulo: str
    descricao: str | None
    tipo: str
    ordem: int
    model_config = ConfigDict(from_attributes=True)


class ModuloPublic(BaseModel):
    id: UUID
    titulo: str
    ordem: int
    publicado: bool
    materiais: list[MaterialPublic]


class ModuloList(BaseModel):
    modulos: list[ModuloPublic]


class AcessoMaterialPublic(BaseModel):
    material_id: UUID
    aberto_em: datetime
    model_config = ConfigDict(from_attributes=True)


TipoAtividade = Literal['leitura', 'exercicio', 'pratica', 'forum', 'questionario']


class AtividadeCreate(BaseModel):
    titulo: str = Field(min_length=1)
    tipo: TipoAtividade
    categoria: str = Field(min_length=1)
    pontos: float | None = Field(default=None, ge=0)
    prazo: datetime
    descricao: str | None = None
    publicada: bool = True
    modulo_id: UUID | None = None


class AtividadePublic(BaseModel):
    id: UUID
    titulo: str
    tipo: str
    categoria: str
    pontos: float | None
    prazo: datetime
    descricao: str | None
    publicada: bool
    modulo_id: UUID | None
    situacao: str | None = None
    model_config = ConfigDict(from_attributes=True)


class AtividadeList(BaseModel):
    atividades: list[AtividadePublic]


class EntregaPublic(BaseModel):
    atividade_id: UUID
    situacao: str
    entregue_em: datetime
    model_config = ConfigDict(from_attributes=True)


TipoAvaliacao = Literal['prova', 'trabalho', 'atividade', 'outra']


class AvaliacaoCreate(BaseModel):
    nome: str = Field(min_length=1)
    tipo: TipoAvaliacao
    data: date
    peso: float = Field(gt=0, le=100)


class AvaliacaoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1)
    tipo: TipoAvaliacao | None = None
    data: date | None = None
    peso: float | None = Field(default=None, gt=0, le=100)


class AvaliacaoPublic(BaseModel):
    id: UUID
    nome: str
    tipo: str
    data: date
    peso: float
    model_config = ConfigDict(from_attributes=True)


class AvaliacaoList(BaseModel):
    avaliacoes: list[AvaliacaoPublic]
    soma_pesos: float


class NotaCreate(BaseModel):
    valor: float = Field(ge=0, le=10)


class NotaPublic(BaseModel):
    avaliacao_id: UUID
    aluno_id: UUID
    valor: float
    lancada_em: datetime
    model_config = ConfigDict(from_attributes=True)


class NotaAluno(BaseModel):
    avaliacao_id: UUID
    nome: str
    tipo: str
    data: date
    peso: float
    valor: float | None


class NotasAlunoList(BaseModel):
    notas: list[NotaAluno]


class PresencaItem(BaseModel):
    aluno_id: UUID
    presente: bool


class ChamadaCreate(BaseModel):
    data: date
    presencas: list[PresencaItem] = Field(default_factory=list)


class ChamadaPublic(BaseModel):
    id: UUID
    turma_id: UUID
    data: date
    presentes: int
    matriculados: int


class FrequenciaAluno(BaseModel):
    aulas: int
    presencas: int
    percentual: int | None


class DesempenhoAluno(BaseModel):
    media: float | None
    frequencia: int | None
    progresso: int | None


class AvisoCreate(BaseModel):
    autor: str = Field(min_length=1)
    data: date
    titulo: str = Field(min_length=1)
    mensagem: str = Field(min_length=1)


class EncerramentoTurma(BaseModel):
    id: UUID
    encerrada_em: datetime
