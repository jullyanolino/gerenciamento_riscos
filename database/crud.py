# database/crud.py

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func, desc, asc, case, text
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd

from .models import (
    Risco, PlanoAcao, Usuario, AvaliacaoHistorica, 
    AtualizacaoPlanoAcao, MonitoramentoRisco, EscalaReferencia,
    TipoResposta, Configuracao,
    NivelProbabilidade, NivelImpacto, NivelCriticidade,
    StatusAcao, TipoResposta as TipoRespostaEnum,
    FonteRisco, CategoriaRisco, TipoImpacto
)

class RiscoCRUD:
    """Operações CRUD para riscos"""
    
    @staticmethod
    def criar_risco(session: Session, risco_data: dict, criado_por_id: int) -> Risco:
        """
        Cria um novo risco
        
        Args:
            session: Sessão do banco
            risco_data: Dados do risco
            criado_por_id: ID do usuário que está criando
            
        Returns:
            Risco criado
        """
        # Gera código único se não fornecido
        if 'codigo_risco' not in risco_data or not risco_data['codigo_risco']:
            ultimo_id = session.query(func.max(Risco.id)).scalar() or 0
            risco_data['codigo_risco'] = f"RSK-{str(ultimo_id + 1).zfill(3)}"
        
        # Calcula criticidade se não fornecida
        if 'criticidade' not in risco_data and all(k in risco_data for k in ['probabilidade', 'impacto']):
            risco_data['criticidade'] = RiscoCRUD._calcular_criticidade(
                risco_data['probabilidade'], 
                risco_data['impacto']
            )
        
        risco_data['criado_por_id'] = criado_por_id
        risco_data['data_identificacao'] = datetime.now()
        
        risco = Risco(**risco_data)
        session.add(risco)
        session.flush()
        
        return risco
    
    @staticmethod
    def _calcular_criticidade(probabilidade: NivelProbabilidade, impacto: NivelImpacto) -> NivelCriticidade:
        """Calcula criticidade baseada em probabilidade e impacto"""
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
        
        prob_num = prob_valores.get(probabilidade, 3)
        impacto_num = impacto_valores.get(impacto, 3)
        produto = prob_num * impacto_num
        
        if produto <= 4:
            return NivelCriticidade.BAIXO
        elif produto <= 9:
            return NivelCriticidade.MEDIO
        elif produto <= 16:
            return NivelCriticidade.ALTO
        else:
            return NivelCriticidade.CRITICO
    
    @staticmethod
    def listar_riscos(
        session: Session,
        filtros: dict = None,
        ordenacao: str = 'id',
        direcao: str = 'asc',
        limite: int = None,
        offset: int = 0,
        incluir_planos: bool = False
    ) -> Tuple[List[Risco], int]:
        """
        Lista riscos com filtros e paginação
        
        Args:
            session: Sessão do banco
            filtros: Dicionário com filtros (eap, fonte, categoria, criticidade, etc.)
            ordenacao: Campo para ordenação
            direcao: 'asc' ou 'desc'
            limite: Limite de registros
            offset: Offset para paginação
            incluir_planos: Se deve incluir planos de ação
            
        Returns:
            Tupla com (lista de riscos, total de registros)
        """
        query = session.query(Risco)
        
        # Aplicar filtros
        if filtros:
            if 'eap' in filtros and filtros['eap']:
                query = query.filter(Risco.eap.ilike(f"%{filtros['eap']}%"))
                
            if 'fonte' in filtros and filtros['fonte']:
                query = query.filter(Risco.fonte == filtros['fonte'])
                
            if 'categoria' in filtros and filtros['categoria']:
                query = query.filter(Risco.categoria == filtros['categoria'])
                
            if 'criticidade' in filtros and filtros['criticidade']:
                if isinstance(filtros['criticidade'], list):
                    query = query.filter(Risco.criticidade.in_(filtros['criticidade']))
                else:
                    query = query.filter(Risco.criticidade == filtros['criticidade'])
                    
            if 'responsavel_id' in filtros and filtros['responsavel_id']:
                query = query.join(Risco.responsaveis).filter(
                    Usuario.id == filtros['responsavel_id']
                )
                
            if 'texto_busca' in filtros and filtros['texto_busca']:
                texto = f"%{filtros['texto_busca']}%"
                query = query.filter(
                    or_(
                        Risco.titulo_evento.ilike(texto),
                        Risco.descricao_evento.ilike(texto),
                        Risco.causas.ilike(texto),
                        Risco.consequencias.ilike(texto)
                    )
                )
                
            if 'ativo' in filtros:
                query = query.filter(Risco.ativo == filtros['ativo'])
                
            if 'data_inicio' in filtros and filtros['data_inicio']:
                query = query.filter(Risco.data_identificacao >= filtros['data_inicio'])
                
            if 'data_fim' in filtros and filtros['data_fim']:
                query = query.filter(Risco.data_identificacao <= filtros['data_fim'])
        
        # Contar total antes da paginação
        total = query.count()
        
        # Aplicar ordenação
        if hasattr(Risco, ordenacao):
            if direcao.lower() == 'desc':
                query = query.order_by(desc(getattr(Risco, ordenacao)))
            else:
                query = query.order_by(asc(getattr(Risco, ordenacao)))
        
        # Eager loading para evitar N+1
        if incluir_planos:
            query = query.options(selectinload(Risco.planos_acao))
        
        query = query.options(selectinload(Risco.responsaveis))
        
        # Aplicar paginação
        if offset:
            query = query.offset(offset)
        if limite:
            query = query.limit(limite)
            
        riscos = query.all()
        return riscos, total
    
    @staticmethod
    def obter_risco_por_id(session: Session, risco_id: int, incluir_relacionamentos: bool = True) -> Optional[Risco]:
        """Obtém risco por ID com relacionamentos"""
        query = session.query(Risco).filter(Risco.id == risco_id)
        
        if incluir_relacionamentos:
            query = query.options(
                selectinload(Risco.planos_acao).selectinload(PlanoAcao.responsaveis),
                selectinload(Risco.responsaveis),
                selectinload(Risco.avaliacoes_historicas),
                selectinload(Risco.monitoramentos)
            )
            
        return query.first()
    
    @staticmethod
    def atualizar_risco(
        session: Session, 
        risco_id: int, 
        dados_atualizacao: dict, 
        atualizado_por_id: int,
        salvar_historico: bool = True
    ) -> Optional[Risco]:
        """
        Atualiza risco e salva histórico se necessário
        
        Args:
            session: Sessão do banco
            risco_id: ID do risco
            dados_atualizacao: Dados para atualizar
            atualizado_por_id: ID do usuário que está atualizando
            salvar_historico: Se deve salvar alterações de avaliação no histórico
        """
        risco = session.query(Risco).filter(Risco.id == risco_id).first()
        if not risco:
            return None
        
        # Salva estado anterior se mudou avaliação
        if salvar_historico and any(k in dados_atualizacao for k in ['probabilidade', 'impacto', 'criticidade']):
            RiscoCRUD._salvar_historico_avaliacao(
                session, risco, dados_atualizacao, atualizado_por_id
            )
        
        # Atualiza campos
        for campo, valor in dados_atualizacao.items():
            if hasattr(risco, campo):
                setattr(risco, campo, valor)
        
        # Recalcula criticidade se mudou probabilidade ou impacto
        if 'probabilidade' in dados_atualizacao or 'impacto' in dados_atualizacao:
            risco.criticidade = RiscoCRUD._calcular_criticidade(
                risco.probabilidade, risco.impacto
            )
        
        risco.atualizado_por_id = atualizado_por_id
        risco.atualizado_em = datetime.now()
        
        return risco
    
    @staticmethod
    def _salvar_historico_avaliacao(session: Session, risco: Risco, novos_dados: dict, usuario_id: int):
        """Salva histórico das mudanças na avaliação"""
        historico = AvaliacaoHistorica(
            risco_id=risco.id,
            probabilidade_anterior=risco.probabilidade,
            probabilidade_nova=novos_dados.get('probabilidade', risco.probabilidade),
            impacto_anterior=risco.impacto,
            impacto_novo=novos_dados.get('impacto', risco.impacto),
            criticidade_anterior=risco.criticidade,
            criticidade_nova=novos_dados.get('criticidade', risco.criticidade),
            motivo_mudanca=novos_dados.get('motivo_mudanca', 'Atualização'),
            avaliado_por_id=usuario_id
        )
        session.add(historico)
    
    @staticmethod
    def excluir_risco(session: Session, risco_id: int) -> bool:
        """Exclui risco (soft delete por padrão)"""
        risco = session.query(Risco).filter(Risco.id == risco_id).first()
        if not risco:
            return False
            
        risco.ativo = False
        return True
    
    @staticmethod
    def obter_dashboard_riscos(session: Session) -> dict:
        """Obtém dados para dashboard de riscos"""
        
        # Total de riscos por criticidade
        riscos_por_criticidade = session.query(
            Risco.criticidade,
            func.count(Risco.id).label('total')
        ).filter(Risco.ativo == True).group_by(Risco.criticidade).all()
        
        # Riscos por fonte
        riscos_por_fonte = session.query(
            Risco.fonte,
            func.count(Risco.id).label('total')
        ).filter(Risco.ativo == True).group_by(Risco.fonte).all()
        
        # Riscos por categoria
        riscos_por_categoria = session.query(
            Risco.categoria,
            func.count(Risco.id).label('total')
        ).filter(Risco.ativo == True).group_by(Risco.categoria).all()
        
        # Top 10 riscos mais críticos
        riscos_criticos = session.query(Risco).filter(
            and_(Risco.ativo == True, Risco.criticidade == NivelCriticidade.CRITICO)
        ).limit(10).all()
        
        # Estatísticas gerais
        total_riscos = session.query(Risco).filter(Risco.ativo == True).count()
        total_planos = session.query(PlanoAcao).join(Risco).filter(Risco.ativo == True).count()
        
        # Planos atrasados
        planos_atrasados = session.query(PlanoAcao).join(Risco).filter(
            and_(
                Risco.ativo == True,
                PlanoAcao.data_conclusao < datetime.now(),
                PlanoAcao.status != StatusAcao.CONCLUIDO
            )
        ).count()
        
        return {
            'total_riscos': total_riscos,
            'total_planos': total_planos,
            'planos_atrasados': planos_atrasados,
            'riscos_por_criticidade': {r.criticidade.value: r.total for r in riscos_por_criticidade},
            'riscos_por_fonte': {r.fonte.value: r.total for r in riscos_por_fonte},
            'riscos_por_categoria': {r.categoria.value: r.total for r in riscos_por_categoria},
            'riscos_criticos': riscos_criticos
        }

class PlanoAcaoCRUD:
    """Operações CRUD para planos de ação"""
    
    @staticmethod
    def criar_plano_acao(session: Session, plano_data: dict, criado_por_id: int) -> PlanoAcao:
        """Cria novo plano de ação"""
        plano_data['criado_por_id'] = criado_por_id
        plano = PlanoAcao(**plano_data)
        session.add(plano)
        session.flush()
        return plano
    
    @staticmethod
    def listar_planos_acao(
        session: Session,
        risco_id: int = None,
        status: StatusAcao = None,
        responsavel_id: int = None,
        atrasados_apenas: bool = False,
        limite: int = None
    ) -> List[PlanoAcao]:
        """Lista planos de ação com filtros"""
        query = session.query(PlanoAcao).options(
            selectinload(PlanoAcao.responsaveis),
            selectinload(PlanoAcao.risco)
        )
        
        if risco_id:
            query = query.filter(PlanoAcao.risco_id == risco_id)
            
        if status:
            query = query.filter(PlanoAcao.status == status)
            
        if responsavel_id:
            query = query.join(PlanoAcao.responsaveis).filter(Usuario.id == responsavel_id)
            
        if atrasados_apenas:
            query = query.filter(
                and_(
                    PlanoAcao.data_conclusao < datetime.now(),
                    PlanoAcao.status != StatusAcao.CONCLUIDO
                )
            )
            
        if limite:
            query = query.limit(limite)
            
        return query.all()
    
    @staticmethod
    def atualizar_plano_acao(
        session: Session,
        plano_id: int,
        dados_atualizacao: dict,
        atualizado_por_id: int,
        salvar_historico: bool = True
    ) -> Optional[PlanoAcao]:
        """Atualiza plano de ação e salva histórico"""
        plano = session.query(PlanoAcao).filter(PlanoAcao.id == plano_id).first()
        if not plano:
            return None
            
        # Salva histórico se mudou status ou percentual
        if salvar_historico and ('status' in dados_atualizacao or 'percentual_conclusao' in dados_atualizacao):
            PlanoAcaoCRUD._salvar_historico_plano(session, plano, dados_atualizacao, atualizado_por_id)
        
        # Atualiza campos
        for campo, valor in dados_atualizacao.items():
            if hasattr(plano, campo):
                setattr(plano, campo, valor)
        
        # Verifica se está atrasado
        plano.atrasado = plano.is_atrasado()
        
        plano.atualizado_por_id = atualizado_por_id
        plano.atualizado_em = datetime.now()
        
        return plano
    
    @staticmethod
    def _salvar_historico_plano(session: Session, plano: PlanoAcao, novos_dados: dict, usuario_id: int):
        """Salva histórico de atualizações do plano"""
        atualizacao = AtualizacaoPlanoAcao(
            plano_acao_id=plano.id,
            status_anterior=plano.status,
            status_novo=novos_dados.get('status', plano.status),
            percentual_anterior=plano.percentual_conclusao,
            percentual_novo=novos_dados.get('percentual_conclusao', plano.percentual_conclusao),
            descricao_atualizacao=novos_dados.get('descricao_atualizacao', 'Atualização automática'),
            obstaculos_encontrados=novos_dados.get('obstaculos_encontrados'),
            solucoes_implementadas=novos_dados.get('solucoes_implementadas'),
            evidencias=novos_dados.get('evidencias'),
            atualizado_por_id=usuario_id
        )
        session.add(atualizacao)
    
    @staticmethod
    def obter_planos_atrasados(session: Session, dias_tolerancia: int = 0) -> List[PlanoAcao]:
        """Obtém planos de ação atrasados"""
        data_limite = datetime.now() - timedelta(days=dias_tolerancia)
        
        return session.query(PlanoAcao).options(
            selectinload(PlanoAcao.risco),
            selectinload(PlanoAcao.responsaveis)
        ).filter(
            and_(
                PlanoAcao.data_conclusao <= data_limite,
                PlanoAcao.status != StatusAcao.CONCLUIDO,
                PlanoAcao.status != StatusAcao.CANCELADO
            )
        ).order_by(PlanoAcao.data_conclusao).all()
    
    @staticmethod
    def obter_dashboard_planos(session: Session) -> dict:
        """Dashboard de planos de ação"""
        
        # Total por status
        planos_por_status = session.query(
            PlanoAcao.status,
            func.count(PlanoAcao.id).label('total')
        ).group_by(PlanoAcao.status).all()
        
        # Planos por responsável (top 10)
        planos_por_responsavel = session.query(
            Usuario.nome_completo,
            func.count(PlanoAcao.id).label('total')
        ).join(PlanoAcao.responsaveis).group_by(
            Usuario.id, Usuario.nome_completo
        ).order_by(desc('total')).limit(10).all()
        
        # Taxa de conclusão no prazo
        total_concluidos = session.query(PlanoAcao).filter(
            PlanoAcao.status == StatusAcao.CONCLUIDO
        ).count()
        
        concluidos_no_prazo = session.query(PlanoAcao).filter(
            and_(
                PlanoAcao.status == StatusAcao.CONCLUIDO,
                or_(
                    PlanoAcao.data_conclusao == None,
                    PlanoAcao.atualizado_em <= PlanoAcao.data_conclusao
                )
            )
        ).count()
        
        taxa_sucesso = (concluidos_no_prazo / total_concluidos * 100) if total_concluidos > 0 else 0
        
        return {
            'planos_por_status': {p.status.value: p.total for p in planos_por_status},
            'planos_por_responsavel': {p.nome_completo: p.total for p in planos_por_responsavel},
            'taxa_conclusao_prazo': round(taxa_sucesso, 1),
            'total_atrasados': len(PlanoAcaoCRUD.obter_planos_atrasados(session))
        }

class UsuarioCRUD:
    """Operações CRUD para usuários"""
    
    @staticmethod
    def criar_usuario(session: Session, usuario_data: dict) -> Usuario:
        """Cria novo usuário"""
        usuario = Usuario(**usuario_data)
        session.add(usuario)
        session.flush()
        return usuario
    
    @staticmethod
    def listar_usuarios(
        session: Session,
        ativo_apenas: bool = True,
        role: str = None
    ) -> List[Usuario]:
        """Lista usuários"""
        query = session.query(Usuario)
        
        if ativo_apenas:
            query = query.filter(Usuario.ativo == True)
            
        if role:
            query = query.filter(Usuario.role == role)
            
        return query.order_by(Usuario.nome_completo).all()
    
    @staticmethod
    def obter_usuario_por_username(session: Session, username: str) -> Optional[Usuario]:
        """Obtém usuário por username"""
        return session.query(Usuario).filter(Usuario.username == username).first()
    
    @staticmethod
    def obter_usuario_por_email(session: Session, email: str) -> Optional[Usuario]:
        """Obtém usuário por email"""
        return session.query(Usuario).filter(Usuario.email == email).first()
    
    @staticmethod
    def atualizar_usuario(session: Session, usuario_id: int, dados_atualizacao: dict) -> Optional[Usuario]:
        """Atualiza usuário"""
        usuario = session.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            return None
            
        for campo, valor in dados_atualizacao.items():
            if hasattr(usuario, campo):
                setattr(usuario, campo, valor)
                
        usuario.atualizado_em = datetime.now()
        return usuario

class RelatoriosCRUD:
    """Operações para geração de relatórios"""
    
    @staticmethod
    def relatorio_matriz_riscos(session: Session) -> pd.DataFrame:
        """Gera matriz de riscos para relatório"""
        riscos = session.query(
            Risco.codigo_risco,
            Risco.titulo_evento,
            Risco.fonte,
            Risco.categoria,
            Risco.probabilidade,
            Risco.impacto,
            Risco.criticidade,
            Risco.resposta_adotada,
            func.count(PlanoAcao.id).label('total_planos')
        ).outerjoin(PlanoAcao).filter(
            Risco.ativo == True
        ).group_by(
            Risco.id,
            Risco.codigo_risco,
            Risco.titulo_evento,
            Risco.fonte,
            Risco.categoria,
            Risco.probabilidade,
            Risco.impacto,
            Risco.criticidade,
            Risco.resposta_adotada
        ).all()
        
        return pd.DataFrame([
            {
                'Código': r.codigo_risco,
                'Título': r.titulo_evento,
                'Fonte': r.fonte.value,
                'Categoria': r.categoria.value,
                'Probabilidade': r.probabilidade.value,
                'Impacto': r.impacto.value,
                'Criticidade': r.criticidade.value,
                'Resposta': r.resposta_adotada.value if r.resposta_adotada else '',
                'Planos de Ação': r.total_planos
            } for r in riscos
        ])
    
    @staticmethod
    def relatorio_planos_acao(session: Session, risco_id: int = None) -> pd.DataFrame:
        """Relatório de planos de ação"""
        query = session.query(
            Risco.codigo_risco,
            Risco.titulo_evento,
            PlanoAcao.descricao_acao,
            PlanoAcao.area_responsavel,
            PlanoAcao.responsavel_implementacao,
            PlanoAcao.status,
            PlanoAcao.data_inicio,
            PlanoAcao.data_conclusao,
            PlanoAcao.percentual_conclusao
        ).join(Risco).filter(Risco.ativo == True)
        
        if risco_id:
            query = query.filter(Risco.id == risco_id)
            
        planos = query.order_by(Risco.codigo_risco, PlanoAcao.id).all()
        
        return pd.DataFrame([
            {
                'Código Risco': p.codigo_risco,
                'Risco': p.titulo_evento,
                'Ação': p.descricao_acao,
                'Área Responsável': p.area_responsavel,
                'Responsável': p.responsavel_implementacao,
                'Status': p.status.value,
                'Data Início': p.data_inicio.strftime('%d/%m/%Y') if p.data_inicio else '',
                'Data Conclusão': p.data_conclusao.strftime('%d/%m/%Y') if p.data_conclusao else '',
                'Progresso %': p.percentual_conclusao
            } for p in planos
        ])
    
    @staticmethod
    def relatorio_kpis_riscos(session: Session, periodo_dias: int = 30) -> dict:
        """KPIs de riscos para período específico"""
        data_inicio = datetime.now() - timedelta(days=periodo_dias)
        
        # Novos riscos identificados
        novos_riscos = session.query(Risco).filter(
            Risco.data_identificacao >= data_inicio
        ).count()
        
        # Riscos com mudança de criticidade
        mudancas_criticidade = session.query(AvaliacaoHistorica).filter(
            AvaliacaoHistorica.data_avaliacao >= data_inicio
        ).count()
        
        # Planos de ação criados
        novos_planos = session.query(PlanoAcao).filter(
            PlanoAcao.criado_em >= data_inicio
        ).count()
        
        # Planos concluídos
        planos_concluidos = session.query(PlanoAcao).filter(
            and_(
                PlanoAcao.status == StatusAcao.CONCLUIDO,
                PlanoAcao.atualizado_em >= data_inicio
            )
        ).count()
        
        # Taxa de resolução
        total_planos_periodo = session.query(PlanoAcao).filter(
            PlanoAcao.criado_em <= data_inicio
        ).count()
        
        taxa_resolucao = (planos_concluidos / total_planos_periodo * 100) if total_planos_periodo > 0 else 0
        
        return {
            'periodo_dias': periodo_dias,
            'novos_riscos': novos_riscos,
            'mudancas_criticidade': mudancas_criticidade,
            'novos_planos': novos_planos,
            'planos_concluidos': planos_concluidos,
            'taxa_resolucao': round(taxa_resolucao, 1)
        }
    
    @staticmethod
    def evolucao_riscos_tempo(session: Session, meses: int = 12) -> pd.DataFrame:
        """Evolução dos riscos ao longo do tempo"""
        data_inicio = datetime.now() - timedelta(days=meses * 30)
        
        # Query para contar riscos por mês e criticidade
        query = session.query(
            func.date_trunc('month', Risco.data_identificacao).label('mes'),
            Risco.criticidade,
            func.count(Risco.id).label('total')
        ).filter(
            Risco.data_identificacao >= data_inicio
        ).group_by(
            func.date_trunc('month', Risco.data_identificacao),
            Risco.criticidade
        ).order_by('mes')
        
        dados = query.all()
        
        return pd.DataFrame([
            {
                'Mês': d.mes.strftime('%Y-%m') if d.mes else '',
                'Criticidade': d.criticidade.value,
                'Total': d.total
            } for d in dados
        ])

class BuscaAvancadaCRUD:
    """Operações de busca avançada"""
    
    @staticmethod
    def buscar_riscos_texto(session: Session, termo_busca: str, campos: list = None) -> List[Risco]:
        """Busca textual em riscos"""
        if not campos:
            campos = ['titulo_evento', 'descricao_evento', 'causas', 'consequencias']
        
        filtros = []
        termo = f"%{termo_busca}%"
        
        for campo in campos:
            if hasattr(Risco, campo):
                filtros.append(getattr(Risco, campo).ilike(termo))
        
        if not filtros:
            return []
            
        return session.query(Risco).filter(
            and_(Risco.ativo == True, or_(*filtros))
        ).options(selectinload(Risco.responsaveis)).all()
    
    @staticmethod
    def riscos_similares(session: Session, risco_id: int, limite: int = 5) -> List[Risco]:
        """Encontra riscos similares baseado em características"""
        risco_base = session.query(Risco).filter(Risco.id == risco_id).first()
        if not risco_base:
            return []
        
        # Busca por riscos com mesma fonte, categoria ou nível similar
        similares = session.query(Risco).filter(
            and_(
                Risco.id != risco_id,
                Risco.ativo == True,
                or_(
                    Risco.fonte == risco_base.fonte,
                    Risco.categoria == risco_base.categoria,
                    and_(
                        Risco.probabilidade == risco_base.probabilidade,
                        Risco.impacto == risco_base.impacto
                    )
                )
            )
        ).limit(limite).all()
        
        return similares
    
    @staticmethod
    def filtros_dinamicos(session: Session) -> dict:
        """Retorna opções para filtros dinâmicos"""
        
        # Valores únicos para cada campo de filtro
        fontes = session.query(Risco.fonte).distinct().all()
        categorias = session.query(Risco.categoria).distinct().all()
        criticidades = session.query(Risco.criticidade).distinct().all()
        responsaveis = session.query(Usuario.id, Usuario.nome_completo).join(
            Risco.responsaveis
        ).distinct().all()
        
        return {
            'fontes': [f.fonte.value for f in fontes],
            'categorias': [c.categoria.value for c in categorias],
            'criticidades': [c.criticidade.value for c in criticidades],
            'responsaveis': [{'id': r.id, 'nome': r.nome_completo} for r in responsaveis]
        }

# Funções utilitárias
def backup_to_excel(session: Session, arquivo_saida: str = None) -> str:
    """Exporta todos os dados para Excel"""
    if not arquivo_saida:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_saida = f"backup_riscos_{timestamp}.xlsx"
    
    with pd.ExcelWriter(arquivo_saida, engine='openpyxl') as writer:
        # Exporta riscos
        df_riscos = RelatoriosCRUD.relatorio_matriz_riscos(session)
        df_riscos.to_excel(writer, sheet_name='Riscos', index=False)
        
        # Exporta planos de ação
        df_planos = RelatoriosCRUD.relatorio_planos_acao(session)
        df_planos.to_excel(writer, sheet_name='Planos de Ação', index=False)
        
        # Exporta usuários
        usuarios = UsuarioCRUD.listar_usuarios(session)
        df_usuarios = pd.DataFrame([
            {
                'ID': u.id,
                'Username': u.username,
                'Nome': u.nome_completo,
                'Email': u.email,
                'Cargo': u.cargo,
                'Departamento': u.departamento,
                'Role': u.role,
                'Ativo': u.ativo
            } for u in usuarios
        ])
        df_usuarios.to_excel(writer, sheet_name='Usuários', index=False)
    
    return arquivo_saida

def importar_de_excel(session: Session, arquivo: str) -> dict:
    """Importa dados de arquivo Excel"""
    resultado = {'sucesso': 0, 'erro': 0, 'mensagens': []}
    
    try:
        # Lê planilhas
        dfs = pd.read_excel(arquivo, sheet_name=None)
        
        # Importa usuários primeiro (se existir)
        if 'Usuários' in dfs:
            df_usuarios = dfs['Usuários']
            for _, row in df_usuarios.iterrows():
                try:
                    usuario = UsuarioCRUD.criar_usuario(session, {
                        'username': row['Username'],
                        'nome_completo': row['Nome'],
                        'email': row['Email'],
                        'cargo': row.get('Cargo'),
                        'departamento': row.get('Departamento'),
                        'role': row.get('Role', 'user'),
                        'ativo': row.get('Ativo', True)
                    })
                    resultado['sucesso'] += 1
                except Exception as e:
                    resultado['erro'] += 1
                    resultado['mensagens'].append(f"Erro ao importar usuário {row['Username']}: {str(e)}")
        
        session.commit()
        
        # Importa riscos
        if 'Riscos' in dfs:
            df_riscos = dfs['Riscos']
            admin = session.query(Usuario).filter_by(role='admin').first()
            admin_id = admin.id if admin else 1
            
            for _, row in df_riscos.iterrows():
                try:
                    risco = RiscoCRUD.criar_risco(session, {
                        'codigo_risco': row.get('Código'),
                        'titulo_evento': row['Título'],
                        'fonte': row.get('Fonte', 'Operacional'),
                        'categoria': row.get('Categoria', 'Processo'),
                        'probabilidade': row.get('Probabilidade', 'Média'),
                        'impacto': row.get('Impacto', 'Moderado'),
                        'resposta_adotada': row.get('Resposta', 'Mitigar')
                    }, admin_id)
                    resultado['sucesso'] += 1
                except Exception as e:
                    resultado['erro'] += 1
                    resultado['mensagens'].append(f"Erro ao importar risco {row.get('Código', '')}: {str(e)}")
        
        session.commit()
        return resultado
        
    except Exception as e:
        session.rollback()
        resultado['mensagens'].append(f"Erro geral na importação: {str(e)}")
        return resultado
