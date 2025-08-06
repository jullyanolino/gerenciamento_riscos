# database/models.py

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, 
    ForeignKey, Enum as SQLEnum, Table, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

Base = declarative_base()

# Enums para padronização
class FonteRisco(Enum):
    JURIDICO = "Jurídico"
    OPERACIONAL = "Operacional"
    ESTRATEGICO = "Estratégico"
    FINANCEIRO = "Financeiro"
    TECNOLOGICO = "Tecnológico"
    REPUTACIONAL = "Reputacional"
    REGULATORIO = "Regulatório"

class CategoriaRisco(Enum):
    CONFORMIDADE = "Conformidade"
    PROCESSO = "Processo"
    PESSOAS = "Pessoas"
    TECNOLOGIA = "Tecnologia"
    AMBIENTE_EXTERNO = "Ambiente Externo"

class TipoImpacto(Enum):
    OBJETIVO_PROJETO = "Objetivo do projeto"
    FINANCEIRO = "Financeiro"
    REPUTACIONAL = "Reputacional"
    OPERACIONAL = "Operacional"
    ESTRATEGICO = "Estratégico"

class NivelProbabilidade(Enum):
    MUITO_BAIXA = "Muito baixa"
    BAIXA = "Baixa"
    MEDIA = "Média"
    ALTA = "Alta"
    MUITO_ALTA = "Muito alta"

class NivelImpacto(Enum):
    MUITO_BAIXO = "Muito baixo"
    BAIXO = "Baixo"
    MODERADO = "Moderado"
    ALTO = "Alto"
    MUITO_ALTO = "Muito alto"

class NivelCriticidade(Enum):
    BAIXO = "Baixo"
    MEDIO = "Médio"
    ALTO = "Alto"
    CRITICO = "Crítico"

class TipoResposta(Enum):
    EVITAR = "Evitar"
    MITIGAR = "Mitigar"
    TRANSFERIR = "Transferir"
    ACEITAR = "Aceitar"
    COMPARTILHAR = "Compartilhar"

class StatusAcao(Enum):
    NAO_INICIADO = "Não Iniciado"
    EM_ANDAMENTO = "Em andamento"
    CONCLUIDO = "Concluído"
    ATRASADO = "Atrasado"
    CANCELADO = "Cancelado"

class TipoMonitoramento(Enum):
    PLANEJADO = "Planejado"
    REAL = "Real"
    PREVENTIVO = "Preventivo"

# Tabelas de associação para relacionamentos many-to-many
risco_responsaveis = Table(
    'risco_responsaveis',
    Base.metadata,
    Column('risco_id', Integer, ForeignKey('riscos.id')),
    Column('usuario_id', Integer, ForeignKey('usuarios.id'))
)

acao_responsaveis = Table(
    'acao_responsaveis',
    Base.metadata,
    Column('acao_id', Integer, ForeignKey('planos_acao.id')),
    Column('usuario_id', Integer, ForeignKey('usuarios.id'))
)

acao_intervenientes = Table(
    'acao_intervenientes',
    Base.metadata,
    Column('acao_id', Integer, ForeignKey('planos_acao.id')),
    Column('usuario_id', Integer, ForeignKey('usuarios.id'))
)

class Usuario(Base):
    """Modelo para usuários do sistema"""
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    nome_completo = Column(String(200), nullable=False)
    cargo = Column(String(100))
    departamento = Column(String(100))
    telefone = Column(String(20))
    ativo = Column(Boolean, default=True)
    role = Column(String(20), default='user')  # admin, manager, user, viewer
    
    # Metadados
    criado_em = Column(DateTime, default=func.now())
    atualizado_em = Column(DateTime, default=func.now(), onupdate=func.now())
    criado_por = Column(Integer, ForeignKey('usuarios.id'))
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, username='{self.username}', nome='{self.nome_completo}')>"

class Risco(Base):
    """Modelo principal para identificação e avaliação de riscos"""
    __tablename__ = 'riscos'
    
    # Identificação
    id = Column(Integer, primary_key=True, autoincrement=True)
    eap = Column(String(50), nullable=False, index=True)  # EAP do projeto
    codigo_risco = Column(String(20), unique=True, index=True)  # Código único do risco
    
    # Identificação do Risco
    fonte = Column(SQLEnum(FonteRisco), nullable=False)
    etapas = Column(Text)  # Ex: "Edital, Procedimento para vagas reservadas"
    categoria = Column(SQLEnum(CategoriaRisco), nullable=False)
    
    # Descrição do Evento de Risco
    titulo_evento = Column(String(500), nullable=False)
    descricao_evento = Column(Text, nullable=False)
    
    # Causas (Fatores de Risco)
    causas = Column(Text, nullable=False)
    
    # Consequências e Impactos
    tipo_impacto = Column(SQLEnum(TipoImpacto), nullable=False)
    consequencias = Column(Text, nullable=False)
    
    # Avaliação Qualitativa
    probabilidade = Column(SQLEnum(NivelProbabilidade), nullable=False)
    impacto = Column(SQLEnum(NivelImpacto), nullable=False)
    criticidade = Column(SQLEnum(NivelCriticidade), nullable=False)
    
    # Avaliação Quantitativa (opcional)
    valor_probabilidade = Column(Float)  # 0-1
    valor_impacto = Column(Float)  # escala definida
    valor_criticidade = Column(Float)  # calculado ou definido
    
    # Tratamento
    resposta_sugerida = Column(SQLEnum(TipoResposta))
    resposta_adotada = Column(SQLEnum(TipoResposta))
    justificativa_resposta = Column(Text)
    
    # Status e Controle
    ativo = Column(Boolean, default=True)
    aprovado = Column(Boolean, default=False)
    data_identificacao = Column(DateTime, default=func.now())
    data_aprovacao = Column(DateTime)
    
    # Responsáveis (Many-to-Many)
    responsaveis = relationship(
        "Usuario",
        secondary=risco_responsaveis,
        backref="riscos_responsavel"
    )
    
    # Relacionamentos
    planos_acao = relationship("PlanoAcao", back_populates="risco", cascade="all, delete-orphan")
    avaliacoes_historicas = relationship("AvaliacaoHistorica", back_populates="risco", cascade="all, delete-orphan")
    monitoramentos = relationship("MonitoramentoRisco", back_populates="risco", cascade="all, delete-orphan")
    
    # Metadados de auditoria
    criado_em = Column(DateTime, default=func.now())
    atualizado_em = Column(DateTime, default=func.now(), onupdate=func.now())
    criado_por_id = Column(Integer, ForeignKey('usuarios.id'))
    atualizado_por_id = Column(Integer, ForeignKey('usuarios.id'))
    
    # Relacionamentos para auditoria
    criado_por = relationship("Usuario", foreign_keys=[criado_por_id])
    atualizado_por = relationship("Usuario", foreign_keys=[atualizado_por_id])
    
    def __repr__(self):
        return f"<Risco(id={self.id}, eap='{self.eap}', criticidade='{self.criticidade}')>"
    
    def calcular_criticidade_numerica(self):
        """Calcula valor numérico da criticidade baseado em probabilidade e impacto"""
        prob_valores = {
            NivelProbabilidade.MUITO_BAIXA: 1,
            NivelProbabilidade.BAIXA: 2,
            NivelProbabilidade.MEDIA: 3,
            NivelProbabilidade.ALTA: 4,
            NivelProbabilidade.MUITO_ALTA: 5
        }
        
        impacto_valores = {
            NivelImpacto.MUITO_BAIXO: 1,
            NivelImpacto.BAIXO: 2,
            NivelImpacto.MODERADO: 3,
            NivelImpacto.ALTO: 4,
            NivelImpacto.MUITO_ALTO: 5
        }
        
        prob_num = prob_valores.get(self.probabilidade, 3)
        impacto_num = impacto_valores.get(self.impacto, 3)
        
        return prob_num * impacto_num

class PlanoAcao(Base):
    """Modelo para planos de ação dos riscos"""
    __tablename__ = 'planos_acao'
    
    # Identificação
    id = Column(Integer, primary_key=True, autoincrement=True)
    risco_id = Column(Integer, ForeignKey('riscos.id'), nullable=False)
    
    # 5W2H - Estrutura do plano de ação
    # Por quê? (Why) - já está no risco
    # O que? (What)
    descricao_acao = Column(Text, nullable=False)
    
    # Onde? (Where)
    area_responsavel = Column(String(200))
    local_implementacao = Column(String(200))
    
    # Quem? (Who)
    responsavel_implementacao = Column(String(200))
    # Relacionamento many-to-many para múltiplos responsáveis
    responsaveis = relationship(
        "Usuario",
        secondary=acao_responsaveis,
        backref="acoes_responsavel"
    )
    
    # Intervenientes
    intervenientes = relationship(
        "Usuario", 
        secondary=acao_intervenientes,
        backref="acoes_interveniente"
    )
    
    # Como? (How)
    como_implementar = Column(Text)
    metodologia = Column(Text)
    recursos_necessarios = Column(Text)
    
    # Quando? (When)
    data_inicio = Column(DateTime)
    data_conclusao = Column(DateTime)
    
    # Quanto? (How much) - custos
    custo_estimado = Column(Float)
    custo_real = Column(Float)
    moeda = Column(String(3), default='BRL')
    
    # Status e Controle
    status = Column(SQLEnum(StatusAcao), default=StatusAcao.NAO_INICIADO)
    percentual_conclusao = Column(Integer, default=0)  # 0-100
    atrasado = Column(Boolean, default=False)
    
    # Monitoramento
    tipo_monitoramento = Column(SQLEnum(TipoMonitoramento), default=TipoMonitoramento.PLANEJADO)
    observacoes_monitoramento = Column(Text)
    
    # Eficácia da ação
    eficaz = Column(Boolean)
    justificativa_eficacia = Column(Text)
    
    # Relacionamentos
    risco = relationship("Risco", back_populates="planos_acao")
    atualizacoes = relationship("AtualizacaoPlanoAcao", back_populates="plano_acao", cascade="all, delete-orphan")
    
    # Metadados
    criado_em = Column(DateTime, default=func.now())
    atualizado_em = Column(DateTime, default=func.now(), onupdate=func.now())
    criado_por_id = Column(Integer, ForeignKey('usuarios.id'))
    atualizado_por_id = Column(Integer, ForeignKey('usuarios.id'))
    
    def __repr__(self):
        return f"<PlanoAcao(id={self.id}, risco_id={self.risco_id}, status='{self.status}')>"
    
    def is_atrasado(self):
        """Verifica se a ação está atrasada"""
        if self.data_conclusao and self.status != StatusAcao.CONCLUIDO:
            return datetime.now() > self.data_conclusao
        return False

class AvaliacaoHistorica(Base):
    """Histórico de mudanças na avaliação dos riscos"""
    __tablename__ = 'avaliacoes_historicas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    risco_id = Column(Integer, ForeignKey('riscos.id'), nullable=False)
    
    # Snapshot da avaliação
    probabilidade_anterior = Column(SQLEnum(NivelProbabilidade))
    probabilidade_nova = Column(SQLEnum(NivelProbabilidade))
    
    impacto_anterior = Column(SQLEnum(NivelImpacto))
    impacto_novo = Column(SQLEnum(NivelImpacto))
    
    criticidade_anterior = Column(SQLEnum(NivelCriticidade))
    criticidade_nova = Column(SQLEnum(NivelCriticidade))
    
    # Justificativa da mudança
    motivo_mudanca = Column(Text)
    evidencias = Column(Text)
    
    # Relacionamentos
    risco = relationship("Risco", back_populates="avaliacoes_historicas")
    
    # Metadados
    data_avaliacao = Column(DateTime, default=func.now())
    avaliado_por_id = Column(Integer, ForeignKey('usuarios.id'))
    avaliado_por = relationship("Usuario")
    
    def __repr__(self):
        return f"<AvaliacaoHistorica(id={self.id}, risco_id={self.risco_id}, data='{self.data_avaliacao}')>"

class AtualizacaoPlanoAcao(Base):
    """Atualizações e progresso dos planos de ação"""
    __tablename__ = 'atualizacoes_planos_acao'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plano_acao_id = Column(Integer, ForeignKey('planos_acao.id'), nullable=False)
    
    # Dados da atualização
    status_anterior = Column(SQLEnum(StatusAcao))
    status_novo = Column(SQLEnum(StatusAcao))
    
    percentual_anterior = Column(Integer)
    percentual_novo = Column(Integer)
    
    # Descrição da atualização
    descricao_atualizacao = Column(Text, nullable=False)
    obstaculos_encontrados = Column(Text)
    solucoes_implementadas = Column(Text)
    
    # Anexos/Evidências (JSON com links ou base64)
    evidencias = Column(JSON)
    
    # Relacionamentos
    plano_acao = relationship("AtualizacaoPlanoAcao", back_populates="atualizacoes")
    
    # Metadados
    data_atualizacao = Column(DateTime, default=func.now())
    atualizado_por_id = Column(Integer, ForeignKey('usuarios.id'))
    atualizado_por = relationship("Usuario")
    
    def __repr__(self):
        return f"<AtualizacaoPlanoAcao(id={self.id}, plano_id={self.plano_acao_id})>"

class MonitoramentoRisco(Base):
    """Indicadores e monitoramento contínuo dos riscos"""
    __tablename__ = 'monitoramentos_risco'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    risco_id = Column(Integer, ForeignKey('riscos.id'), nullable=False)
    
    # Dados do monitoramento
    data_monitoramento = Column(DateTime, default=func.now())
    
    # Indicadores
    kpis = Column(JSON)  # Indicadores chave de performance
    metricas = Column(JSON)  # Métricas específicas
    
    # Status atual
    status_atual = Column(String(50))
    tendencia = Column(String(20))  # 'melhorando', 'estável', 'piorando'
    
    # Observações
    observacoes = Column(Text)
    recomendacoes = Column(Text)
    alertas = Column(Text)
    
    # Próxima revisão
    proxima_revisao = Column(DateTime)
    
    # Relacionamentos
    risco = relationship("Risco", back_populates="monitoramentos")
    
    # Metadados
    monitorado_por_id = Column(Integer, ForeignKey('usuarios.id'))
    monitorado_por = relationship("Usuario")
    
    def __repr__(self):
        return f"<MonitoramentoRisco(id={self.id}, risco_id={self.risco_id}, data='{self.data_monitoramento}')>"

class EscalaReferencia(Base):
    """Escalas de referência para probabilidade e impacto"""
    __tablename__ = 'escalas_referencia'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo_escala = Column(String(20), nullable=False)  # 'probabilidade' ou 'impacto'
    nivel = Column(String(20), nullable=False)
    valor_numerico = Column(Integer, nullable=False)
    descricao = Column(Text)
    exemplos = Column(Text)
    
    # Metadados
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<EscalaReferencia(tipo='{self.tipo_escala}', nivel='{self.nivel}')>"

class TipoResposta(Base):
    """Tipos de resposta aos riscos e suas descrições"""
    __tablename__ = 'tipos_resposta'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), unique=True, nullable=False)
    descricao = Column(Text)
    exemplos = Column(Text)
    quando_usar = Column(Text)
    
    # Metadados
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<TipoResposta(nome='{self.nome}')>"

class Configuracao(Base):
    """Configurações gerais do sistema"""
    __tablename__ = 'configuracoes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chave = Column(String(100), unique=True, nullable=False)
    valor = Column(Text)
    descricao = Column(Text)
    tipo_dado = Column(String(20))  # 'string', 'int', 'float', 'bool', 'json'
    
    # Metadados
    atualizado_em = Column(DateTime, default=func.now(), onupdate=func.now())
    atualizado_por_id = Column(Integer, ForeignKey('usuarios.id'))
    atualizado_por = relationship("Usuario")
    
    def __repr__(self):
        return f"<Configuracao(chave='{self.chave}', valor='{self.valor}')>"

# Views e consultas complexas poderiam ser adicionadas aqui
# Por exemplo, uma view materializada para dashboard de riscos críticos

def criar_indices_personalizados(engine):
    """Cria índices personalizados para otimizar consultas"""
    from sqlalchemy import Index
    
    # Índices compostos para consultas comuns
    Index('idx_risco_eap_criticidade', Risco.eap, Risco.criticidade)
    Index('idx_risco_fonte_categoria', Risco.fonte, Risco.categoria)
    Index('idx_acao_status_data', PlanoAcao.status, PlanoAcao.data_conclusao)
    Index('idx_monitoramento_data_risco', MonitoramentoRisco.data_monitoramento, MonitoramentoRisco.risco_id)
    
    # Criar os índices no banco
    Base.metadata.create_all(engine)
