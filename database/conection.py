# database/connection.py

import os
import streamlit as st
from sqlalchemy import create_engine, event, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Optional, Generator
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerenciador de conexões e configurações do banco de dados"""
    
    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._database_url = None
        self._initialized = False
        
    def initialize(self, database_url: Optional[str] = None, echo: bool = False):
        """
        Inicializa a conexão com o banco de dados
        
        Args:
            database_url: URL de conexão do banco
            echo: Se deve fazer log das queries SQL
        """
        if self._initialized:
            return
            
        # Determina URL do banco
        self._database_url = database_url or self._get_database_url()
        
        # Configurações específicas por tipo de banco
        engine_kwargs = {'echo': echo}
        
        if 'sqlite' in self._database_url:
            # Configurações para SQLite
            engine_kwargs.update({
                'poolclass': StaticPool,
                'connect_args': {
                    'check_same_thread': False,
                    'timeout': 30
                }
            })
        elif 'postgresql' in self._database_url:
            # Configurações para PostgreSQL
            engine_kwargs.update({
                'pool_size': 10,
                'max_overflow': 20,
                'pool_pre_ping': True,
                'pool_recycle': 3600
            })
        
        # Cria engine
        self._engine = create_engine(self._database_url, **engine_kwargs)
        
        # Configura session factory
        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False
        )
        
        # Configurações adicionais
        self._setup_event_listeners()
        
        self._initialized = True
        logger.info(f"Banco de dados inicializado: {self._database_url.split('@')[0]}...")
        
    def _get_database_url(self) -> str:
        """Determina a URL do banco baseada no ambiente"""
        
        # Primeira prioridade: variável de ambiente
        if os.getenv('DATABASE_URL'):
            return os.getenv('DATABASE_URL')
        
        # Segunda prioridade: configuração Streamlit secrets
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            db_config = st.secrets['database']
            if 'url' in db_config:
                return db_config['url']
            
            # Constrói URL a partir de componentes
            if all(key in db_config for key in ['host', 'database', 'username', 'password']):
                return (
                    f"postgresql://{db_config['username']}:{db_config['password']}"
                    f"@{db_config['host']}:{db_config.get('port', 5432)}"
                    f"/{db_config['database']}"
                )
        
        # Terceira prioridade: SQLite local
        db_path = os.getenv('SQLITE_PATH', 'data/risk_management.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return f"sqlite:///{db_path}"
        
    def _setup_event_listeners(self):
        """Configura listeners de eventos do SQLAlchemy"""
        
        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Configurações específicas para SQLite"""
            if 'sqlite' in str(self._engine.url):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.close()
                
    @property
    def engine(self):
        """Retorna a engine do banco"""
        if not self._initialized:
            self.initialize()
        return self._engine
        
    @property
    def session_factory(self):
        """Retorna a factory de sessões"""
        if not self._initialized:
            self.initialize()
        return self._session_factory
        
    def create_tables(self, drop_existing: bool = False):
        """
        Cria tabelas no banco de dados
        
        Args:
            drop_existing: Se deve dropar tabelas existentes
        """
        from .models import Base
        
        if not self._initialized:
            self.initialize()
            
        if drop_existing:
            logger.warning("Dropando tabelas existentes...")
            Base.metadata.drop_all(self._engine)
            
        logger.info("Criando tabelas...")
        Base.metadata.create_all(self._engine)
        
        # Cria índices personalizados
        try:
            from .models import criar_indices_personalizados
            criar_indices_personalizados(self._engine)
        except Exception as e:
            logger.warning(f"Erro ao criar índices personalizados: {e}")
            
        logger.info("Tabelas criadas com sucesso!")
        
    def get_session(self) -> Session:
        """Retorna uma nova sessão do banco"""
        if not self._initialized:
            self.initialize()
        return self._session_factory()
        
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Context manager para sessões com commit/rollback automático
        
        Usage:
            with db_manager.session_scope() as session:
                # operações com o banco
                pass
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            
    def health_check(self) -> dict:
        """Verifica saúde da conexão com banco"""
        try:
            with self.session_scope() as session:
                result = session.execute("SELECT 1").fetchone()
                return {
                    'status': 'healthy',
                    'database_url': self._database_url.split('@')[0] + '@***',
                    'connection_test': 'passed',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    def backup_database(self, backup_path: str = None) -> str:
        """
        Cria backup do banco (funciona melhor com SQLite)
        
        Args:
            backup_path: Caminho para salvar backup
            
        Returns:
            Caminho do arquivo de backup
        """
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backups/risk_management_backup_{timestamp}.db"
            
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        if 'sqlite' in self._database_url:
            import shutil
            source_path = self._database_url.replace('sqlite:///', '')
            shutil.copy2(source_path, backup_path)
            logger.info(f"Backup SQLite criado: {backup_path}")
            
        else:
            # Para PostgreSQL, usar pg_dump
            logger.warning("Backup automático não implementado para PostgreSQL")
            # Aqui você poderia implementar pg_dump
            
        return backup_path

# Instância global do gerenciador
db_manager = DatabaseManager()

def init_database(database_url: Optional[str] = None, create_tables: bool = True, echo: bool = False):
    """
    Inicializa o banco de dados
    
    Args:
        database_url: URL de conexão
        create_tables: Se deve criar tabelas
        echo: Se deve fazer log das queries
    """
    db_manager.initialize(database_url, echo)
    
    if create_tables:
        db_manager.create_tables()
        
    return db_manager

def get_session() -> Session:
    """Função conveniente para obter sessão"""
    return db_manager.get_session()

@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager conveniente para sessões"""
    with db_manager.session_scope() as session:
        yield session

# Decorador para injeção de dependência de sessão
def with_db_session(func):
    """
    Decorador que injeta uma sessão do banco como primeiro argumento
    
    Usage:
        @with_db_session
        def minha_funcao(session, outros_args):
            # usar session aqui
            pass
    """
    def wrapper(*args, **kwargs):
        with session_scope() as session:
            return func(session, *args, **kwargs)
    return wrapper

class DatabaseConfig:
    """Configurações do banco de dados"""
    
    # Configurações de desenvolvimento
    SQLITE_DEV = "sqlite:///data/risk_management_dev.db"
    SQLITE_TEST = "sqlite:///data/risk_management_test.db"
    
    # Configurações de produção
    @staticmethod
    def get_postgres_url(
        host: str, 
        database: str, 
        username: str, 
        password: str, 
        port: int = 5432,
        sslmode: str = "require"
    ) -> str:
        """Constrói URL do PostgreSQL"""
        return f"postgresql://{username}:{password}@{host}:{port}/{database}?sslmode={sslmode}"
    
    @staticmethod
    def get_azure_sql_url(
        server: str,
        database: str,
        username: str,
        password: str
    ) -> str:
        """Constrói URL do Azure SQL Server"""
        return f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"

def setup_streamlit_database():
    """Configuração específica para Streamlit"""
    
    # Cache da inicialização para evitar reconexões desnecessárias
    if 'db_initialized' not in st.session_state:
        try:
            # Tenta diferentes fontes de configuração
            database_url = None
            
            # 1. Streamlit secrets
            if hasattr(st, 'secrets') and 'database' in st.secrets:
                db_secrets = st.secrets['database']
                if 'url' in db_secrets:
                    database_url = db_secrets['url']
                elif all(k in db_secrets for k in ['host', 'database', 'username', 'password']):
                    database_url = DatabaseConfig.get_postgres_url(
                        host=db_secrets['host'],
                        database=db_secrets['database'],
                        username=db_secrets['username'],
                        password=db_secrets['password'],
                        port=db_secrets.get('port', 5432)
                    )
            
            # 2. Variáveis de ambiente
            if not database_url:
                database_url = os.getenv('DATABASE_URL')
            
            # 3. SQLite local como fallback
            if not database_url:
                database_url = DatabaseConfig.SQLITE_DEV
                st.info("📝 Usando banco SQLite local para desenvolvimento")
            
            # Inicializa
            init_database(database_url, create_tables=True)
            st.session_state['db_initialized'] = True
            
            # Verifica saúde da conexão
            health = db_manager.health_check()
            if health['status'] == 'healthy':
                st.success("✅ Banco de dados conectado com sucesso!")
            else:
                st.error(f"❌ Erro na conexão: {health['error']}")
                
        except Exception as e:
            st.error(f"❌ Erro ao inicializar banco: {str(e)}")
            st.session_state['db_initialized'] = False
            
    return st.session_state.get('db_initialized', False)

def get_streamlit_session():
    """Retorna sessão do banco otimizada para Streamlit"""
    
    # Cache da sessão por execução da página
    session_key = 'db_session'
    
    if session_key not in st.session_state:
        st.session_state[session_key] = get_session()
        
    return st.session_state[session_key]

def close_streamlit_session():
    """Fecha sessão do Streamlit (usar no final da página)"""
    session_key = 'db_session'
    
    if session_key in st.session_state:
        try:
            st.session_state[session_key].close()
        except:
            pass
        finally:
            del st.session_state[session_key]

# Context manager específico para Streamlit
@contextmanager
def streamlit_db_session():
    """Context manager otimizado para uso em Streamlit"""
    session = None
    try:
        session = get_streamlit_session()
        yield session
        session.commit()
    except Exception as e:
        if session:
            session.rollback()
        st.error(f"Erro no banco de dados: {str(e)}")
        raise
    # Note: não fechamos a sessão aqui para reutilização

def migrate_from_csv(csv_files: dict, session: Session = None):
    """
    Migra dados dos CSVs originais para o banco
    
    Args:
        csv_files: Dicionário com os DataFrames dos CSVs
        session: Sessão do banco (opcional)
    """
    from .models import (
        Risco, PlanoAcao, Usuario, EscalaReferencia, 
        TipoResposta as TipoRespostaModel
    )
    import pandas as pd
    from datetime import datetime
    import re
    
    if not session:
        with session_scope() as session:
            return migrate_from_csv(csv_files, session)
    
    try:
        logger.info("Iniciando migração dos dados CSV...")
        
        # 1. Cria usuário admin padrão
        admin_user = session.query(Usuario).filter_by(username='admin').first()
        if not admin_user:
            admin_user = Usuario(
                username='admin',
                email='admin@sistema.com',
                nome_completo='Administrador do Sistema',
                role='admin'
            )
            session.add(admin_user)
            session.flush()  # Para obter o ID
        
        # 2. Migra escalas de referência (do CSV "Escalas e Respostas")
        if 'escalas_respostas' in csv_files:
            escalas_df = csv_files['escalas_respostas']
            
            # Limpa escalas existentes
            session.query(EscalaReferencia).delete()
            session.query(TipoRespostaModel).delete()
            
            # Processa escalas de probabilidade e impacto
            # (Aqui você adaptaria baseado na estrutura real do CSV)
            escalas_prob = [
                ('Muito baixa', 1, 'Improvável. Em situações excepcionais...'),
                ('Baixa', 2, 'Rara. De forma inesperada ou casual...'),
                ('Média', 3, 'Possível. De alguma forma...'),
                ('Alta', 4, 'Provável. De forma até esperada...'),
                ('Muito alta', 5, 'Praticamente certa. De forma inequívoca...')
            ]
            
            for nivel, valor, desc in escalas_prob:
                escala = EscalaReferencia(
                    tipo_escala='probabilidade',
                    nivel=nivel,
                    valor_numerico=valor,
                    descricao=desc
                )
                session.add(escala)
            
            # Tipos de resposta
            respostas = [
                ('Evitar', 'Implica em descontinuar as atividades que geram esses riscos...'),
                ('Mitigar', 'São adotadas medidas para reduzir a probabilidade ou o impacto...'),
                ('Transferir', 'Redução da probabilidade ou do impacto pela transferência...'),
                ('Aceitar', 'Nenhuma medida é adotada para afetar a probabilidade...')
            ]
            
            for nome, desc in respostas:
                tipo_resp = TipoRespostaModel(
                    nome=nome,
                    descricao=desc
                )
                session.add(tipo_resp)
        
        # 3. Migra riscos (do CSV "Identificação de Risco" + "Avaliação dos Riscos")
        if 'identificacao_risco' in csv_files and 'avaliacao_riscos' in csv_files:
            ident_df = csv_files['identificacao_risco']
            aval_df = csv_files['avaliacao_riscos']
            
            # Limpa riscos existentes
            session.query(PlanoAcao).delete()
            session.query(Risco).delete()
            
            for idx, row_ident in ident_df.iterrows():
                # Encontra linha correspondente na avaliação
                row_aval = aval_df.iloc[idx] if idx < len(aval_df) else None
                
                risco = Risco(
                    eap=str(row_ident.get('ID', idx + 1)),
                    codigo_risco=f"RSK-{str(row_ident.get('ID', idx + 1)).zfill(3)}",
                    fonte=row_ident.get('FONTE', 'Operacional'),
                    etapas=row_ident.get('Etapas', ''),
                    categoria=row_ident.get('CATEGORIA', 'Conformidade'),
                    titulo_evento=row_ident.get('DESCRIÇÃO', ''),
                    descricao_evento=row_ident.get('DESCRIÇÃO', ''),
                    causas=row_ident.get('CAUSA', ''),
                    tipo_impacto=row_ident.get('TIPO', 'Objetivo do projeto'),
                    consequencias=row_ident.get('CONSEQUÊNCIA', ''),
                    criado_por_id=admin_user.id
                )
                
                # Adiciona dados da avaliação se disponível
                if row_aval is not None:
                    risco.probabilidade = row_aval.get('PROBABILIDADE', 'Média')
                    risco.impacto = row_aval.get('IMPACTO', 'Moderado')
                    risco.criticidade = row_aval.get('CRITICIDADE', 'Médio')
                    risco.resposta_sugerida = row_aval.get('RESPOSTA SUGERIDA', 'Mitigar')
                    risco.resposta_adotada = row_aval.get('RESPOSTA ADOTADA', 'Mitigar')
                
                session.add(risco)
                session.flush()  # Para obter ID do risco
                
                # 4. Migra planos de ação (do CSV "Plano de Ação")
                if 'plano_acao' in csv_files:
                    plano_df = csv_files['plano_acao']
                    
                    # Filtra ações para este risco (assumindo que EAP é o link)
                    acoes_risco = plano_df[plano_df['EAP'] == risco.eap]
                    
                    for _, row_acao in acoes_risco.iterrows():
                        # Parse das datas
                        data_inicio = None
                        data_conclusao = None
                        
                        try:
                            if pd.notna(row_acao.get('Data do Início')):
                                data_inicio = pd.to_datetime(row_acao['Data do Início'])
                        except:
                            pass
                            
                        try:
                            if pd.notna(row_acao.get('Data da Conclusão')):
                                data_conclusao = pd.to_datetime(row_acao['Data da Conclusão'])
                        except:
                            pass
                        
                        plano_acao = PlanoAcao(
                            risco_id=risco.id,
                            descricao_acao=row_acao.get('Descrição da Ação', ''),
                            area_responsavel=row_acao.get('Área Responsável pela Implementação', ''),
                            responsavel_implementacao=row_acao.get('Responsável Implementação', ''),
                            como_implementar=row_acao.get('Como será Implementado', ''),
                            data_inicio=data_inicio,
                            data_conclusao=data_conclusao,
                            status=row_acao.get('Status', 'Não Iniciado'),
                            tipo_monitoramento=row_acao.get('Monitoramento', 'Planejado'),
                            observacoes_monitoramento=row_acao.get('Monitoramento', ''),
                            criado_por_id=admin_user.id
                        )
                        
                        session.add(plano_acao)
        
        session.commit()
        logger.info("Migração concluída com sucesso!")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Erro na migração: {str(e)}")
        raise

# Função utilitária para popular banco com dados de exemplo
def seed_database():
    """Popula banco com dados de exemplo"""
    from .models import Usuario, EscalaReferencia, TipoResposta as TipoRespostaModel
    
    with session_scope() as session:
        # Verifica se já foi populado
        if session.query(Usuario).count() > 0:
            logger.info("Banco já foi populado")
            return
            
        logger.info("Populando banco com dados de exemplo...")
        
        # Usuários de exemplo
        usuarios = [
            Usuario(
                username='admin',
                email='admin@empresa.com',
                nome_completo='Administrador Sistema',
                role='admin'
            ),
            Usuario(
                username='gestor.risco',
                email='risco@empresa.com', 
                nome_completo='Gestor de Riscos',
                role='manager'
            ),
            Usuario(
                username='analista',
                email='analista@empresa.com',
                nome_completo='Analista de Riscos',
                role='user'
            )
        ]
        
        for usuario in usuarios:
            session.add(usuario)
            
        session.commit()
        logger.info("Dados de exemplo inseridos!")

if __name__ == "__main__":
    # Teste da conexão
    init_database(echo=True)
    health = db_manager.health_check()
    print(f"Status do banco: {health}")
    
    # Popula com dados de exemplo
    seed_database()
