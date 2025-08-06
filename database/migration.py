# migration_example.py - Exemplo de como migrar seus dados CSV para o banco

import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from database.connection import init_database, session_scope
from database.crud import RiscoCRUD, PlanoAcaoCRUD, UsuarioCRUD
from database.models import (
    Usuario, Risco, PlanoAcao,
    FonteRisco, CategoriaRisco, TipoImpacto,
    NivelProbabilidade, NivelImpacto, NivelCriticidade,
    TipoResposta, StatusAcao, TipoMonitoramento
)

def processar_seus_csvs():
    """
    Exemplo específico para migrar os 4 CSVs que você forneceu
    """
    
    # Simulação dos dados dos seus CSVs (você substituiria pelos arquivos reais)
    csvs_data = {
        'identificacao_risco': pd.DataFrame({
            'ID': [1],
            'FONTE': ['Jurídico'],
            'Etapas': ['Edital, Procedimento para vagas reservadas'],
            'CAUSA': ['Inconsistências na redação do edital, com regras imprecisas ou contraditórias.\n\nInsuficiência na validação de documentos para autodeclaração de cotas...'],
            'CATEGORIA': ['Conformidade'],
            'DESCRIÇÃO': ['Devido a inconsistências no edital, insuficiência na validação de documentos, falta de transparência nos procedimentos de cotas...'],
            'TIPO': ['Objetivo do projeto'],
            'CONSEQUÊNCIA': ['Suspensão ou anulação do concurso,\n\nAtrasos no preenchimento das vagas...']
        }),
        
        'avaliacao_riscos': pd.DataFrame({
            'EAP': [1],
            'PROBABILIDADE': ['Alta'],
            'IMPACTO': ['Muito alto'],
            'CRITICIDADE': ['Crítico'],
            'RESPOSTA SUGERIDA': ['Evitar'],
            'RESPOSTA ADOTADA': ['Mitigar']
        }),
        
        'plano_acao': pd.DataFrame({
            'EAP': [1, 1, 1],
            'Descrição da Ação': [
                'Assinatura de termo de confidencialidade',
                'Atos do normativos do concurso criteriosos e bem elaborado',
                'Qualidade da definição dos blocos do concursos'
            ],
            'Área Responsável pela Implementação': [
                'AECI CG, CCD e GTOE',
                'Conjur Equipe do Projeto', 
                'CG, CCD e GTOE'
            ],
            'Responsável Implementação': ['Bessa', 'Karoline', 'Órgãos coordenadores'],
            'Interveniete': ['Equipe do Projeto', 'Equipe do Projeto', 'Equipe do Projeto'],
            'Como será Implementado': [
                'Elaboração do Termo de confidencialidade que vai ficando mais rígido em cada fase...',
                'Elaboração de Portaria, termo de adesão detalhando o funcionamento e regras do concurso',
                'Discussão e consenso sobre a estruturação de cada bloco temático'
            ],
            'Data do Início': ['2023-09-01', '2023-08-01', '2023-10-01'],
            'Data da Conclusão': ['2024-06-01', '2023-09-01', '2023-12-01'],
            'Status': ['Concluído', 'Em andamento', 'Concluído'],
            'Monitoramento': [
                'Todos os envolvidos na primeira fase assinaram os termo de nível 1...',
                'Decreto Nº 11.722, de 28/09/2023 e Portaria MGI Nº 6.017...',
                'Reunião para definição dos blocos nos dias 23 e 24/11/2023...'
            ]
        })
    }
    
    return csvs_data

def migrar_dados_completos():
    """Função principal de migração"""
    
    # Inicializa banco
    db_manager = init_database(create_tables=True)
    
    with session_scope() as session:
        try:
            st.info("🔄 Iniciando migração dos dados...")
            
            # 1. Criar usuário administrador
            admin_user = UsuarioCRUD.obter_usuario_por_username(session, 'admin')
            if not admin_user:
                admin_user = UsuarioCRUD.criar_usuario(session, {
                    'username': 'admin',
                    'email': 'admin@mgi.gov.br',
                    'nome_completo': 'Administrador CPNU',
                    'cargo': 'Coordenador de Projeto',
                    'departamento': 'MGI',
                    'role': 'admin'
                })
                st.success(f"✅ Usuário admin criado: {admin_user.nome_completo}")
            
            # 2. Criar outros usuários baseados nos responsáveis encontrados
            responsaveis_unicos = set()
            csvs = processar_seus_csvs()
            
            if 'plano_acao' in csvs:
                responsaveis_unicos.update(csvs['plano_acao']['Responsável Implementação'].dropna().unique())
                responsaveis_unicos.update(csvs['plano_acao']['Interveniete'].dropna().unique())
            
            for resp in responsaveis_unicos:
                if resp and resp.strip() and resp != 'Equipe do Projeto':
                    usuario_existente = UsuarioCRUD.obter_usuario_por_username(session, resp.lower().replace(' ', '.'))
                    if not usuario_existente:
                        novo_usuario = UsuarioCRUD.criar_usuario(session, {
                            'username': resp.lower().replace(' ', '.'),
                            'email': f"{resp.lower().replace(' ', '.')}@mgi.gov.br",
                            'nome_completo': resp,
                            'role': 'user'
                        })
                        st.success(f"✅ Usuário criado: {novo_usuario.nome_completo}")
            
            # 3. Migrar riscos
            if 'identificacao_risco' in csvs and 'avaliacao_riscos' in csvs:
                ident_df = csvs['identificacao_risco']
                aval_df = csvs['avaliacao_riscos']
                
                for idx, row_ident in ident_df.iterrows():
                    # Mapear valores dos seus CSVs para os enums do modelo
                    fonte_map = {
                        'Jurídico': FonteRisco.JURIDICO,
                        'Operacional': FonteRisco.OPERACIONAL,
                        'Estratégico': FonteRisco.ESTRATEGICO
                    }
                    
                    categoria_map = {
                        'Conformidade': CategoriaRisco.CONFORMIDADE,
                        'Processo': CategoriaRisco.PROCESSO
                    }
                    
                    prob_map = {
                        'Muito baixa': NivelProbabilidade.MUITO_BAIXA,
                        'Baixa': NivelProbabilidade.BAIXA,
                        'Média': NivelProbabilidade.MEDIA,
                        'Alta': NivelProbabilidade.ALTA,
                        'Muito alta': NivelProbabilidade.MUITO_ALTA
                    }
                    
                    impacto_map = {
                        'Muito baixo': NivelImpacto.MUITO_BAIXO,
                        'Baixo': NivelImpacto.BAIXO,
                        'Moderado': NivelImpacto.MODERADO,
                        'Alto': NivelImpacto.ALTO,
                        'Muito alto': NivelImpacto.MUITO_ALTO
                    }
                    
                    criticidade_map = {
                        'Baixo': NivelCriticidade.BAIXO,
                        'Médio': NivelCriticidade.MEDIO,
                        'Alto': NivelCriticidade.ALTO,
                        'Crítico': NivelCriticidade.CRITICO
                    }
                    
                    resposta_map = {
                        'Evitar': TipoResposta.EVITAR,
                        'Mitigar': TipoResposta.MITIGAR,
                        'Transferir': TipoResposta.TRANSFERIR,
                        'Aceitar': TipoResposta.ACEITAR
                    }
                    
                    # Dados da avaliação correspondente
                    row_aval = aval_df.iloc[idx] if idx < len(aval_df) else None
                    
                    # Cria o risco
                    risco_data = {
                        'eap': str(row_ident.get('ID', idx + 1)),
                        'codigo_risco': f"CPNU-RSK-{str(row_ident.get('ID', idx + 1)).zfill(3)}",
                        'fonte': fonte_map.get(row_ident.get('FONTE'), FonteRisco.OPERACIONAL),
                        'etapas': row_ident.get('Etapas', ''),
                        'categoria': categoria_map.get(row_ident.get('CATEGORIA'), CategoriaRisco.CONFORMIDADE),
                        'titulo_evento': 'Risco de Judicialização do CPNU',  # Título resumido
                        'descricao_evento': row_ident.get('DESCRIÇÃO', ''),
                        'causas': row_ident.get('CAUSA', ''),
                        'tipo_impacto': TipoImpacto.OBJETIVO_PROJETO,
                        'consequencias': row_ident.get('CONSEQUÊNCIA', ''),
                    }
                    
                    # Adiciona dados de avaliação se disponível
                    if row_aval is not None:
                        risco_data.update({
                            'probabilidade': prob_map.get(row_aval.get('PROBABILIDADE'), NivelProbabilidade.MEDIA),
                            'impacto': impacto_map.get(row_aval.get('IMPACTO'), NivelImpacto.MODERADO),
                            'criticidade': criticidade_map.get(row_aval.get('CRITICIDADE'), NivelCriticidade.MEDIO),
                            'resposta_sugerida': resposta_map.get(row_aval.get('RESPOSTA SUGERIDA'), TipoResposta.MITIGAR),
                            'resposta_adotada': resposta_map.get(row_aval.get('RESPOSTA ADOTADA'), TipoResposta.MITIGAR)
                        })
                    
                    # Cria o risco no banco
                    risco = RiscoCRUD.criar_risco(session, risco_data, admin_user.id)
                    st.success(f"✅ Risco criado: {risco.codigo_risco}")
                    
                    # 4. Migrar planos de ação para este risco
                    if 'plano_acao' in csvs:
                        planos_df = csvs['plano_acao']
                        
                        # Filtra ações para este risco
                        acoes_risco = planos_df[planos_df['EAP'] == risco_data['eap']]
                        
                        for _, row_acao in acoes_risco.iterrows():
                            # Mapear status
                            status_map = {
                                'Não Iniciado': StatusAcao.NAO_INICIADO,
                                'Em andamento': StatusAcao.EM_ANDAMENTO,
                                'Concluído': StatusAcao.CONCLUIDO,
                                'Atrasado': StatusAcao.ATRASADO,
                                'Cancelado': StatusAcao.CANCELADO
                            }
                            
                            # Parse das datas
                            data_inicio = None
                            data_conclusao = None
                            
                            try:
                                data_inicio_str = row_acao.get('Data do Início')
                                if pd.notna(data_inicio_str):
                                    # Tenta diferentes formatos de data
                                    if isinstance(data_inicio_str, str):
                                        if '-' in data_inicio_str and len(data_inicio_str) == 10:
                                            data_inicio = pd.to_datetime(data_inicio_str).date()
                                        else:
                                            # Formato 'setembro-23' -> converte para primeiro dia do mês
                                            import re
                                            match = re.match(r'(\w+)-(\d{2})', data_inicio_str)
                                            if match:
                                                mes_nome, ano = match.groups()
                                                meses = {
                                                    'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
                                                    'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
                                                    'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
                                                }
                                                if mes_nome in meses:
                                                    ano_completo = 2000 + int(ano)
                                                    data_inicio = datetime(ano_completo, meses[mes_nome], 1).date()
                            except Exception as e:
                                st.warning(f"⚠️ Erro ao processar data início: {data_inicio_str}")
                            
                            try:
                                data_conclusao_str = row_acao.get('Data da Conclusão')
                                if pd.notna(data_conclusao_str):
                                    if isinstance(data_conclusao_str, str):
                                        if '-' in data_conclusao_str and len(data_conclusao_str) == 10:
                                            data_conclusao = pd.to_datetime(data_conclusao_str).date()
                                        else:
                                            # Mesmo tratamento para data de conclusão
                                            import re
                                            match = re.match(r'(\w+)-(\d{2})', data_conclusao_str)
                                            if match:
                                                mes_nome, ano = match.groups()
                                                meses = {
                                                    'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
                                                    'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
                                                    'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
                                                }
                                                if mes_nome in meses:
                                                    ano_completo = 2000 + int(ano)
                                                    data_conclusao = datetime(ano_completo, meses[mes_nome], 28).date()  # Último dia do mês aproximadamente
                            except Exception as e:
                                st.warning(f"⚠️ Erro ao processar data conclusão: {data_conclusao_str}")
                            
                            # Calcula percentual baseado no status
                            percentual_map = {
                                'Não Iniciado': 0,
                                'Em andamento': 50,
                                'Concluído': 100,
                                'Atrasado': 30,
                                'Cancelado': 0
                            }
                            
                            plano_data = {
                                'risco_id': risco.id,
                                'descricao_acao': row_acao.get('Descrição da Ação', ''),
                                'area_responsavel': row_acao.get('Área Responsável pela Implementação', ''),
                                'responsavel_implementacao': row_acao.get('Responsável Implementação', ''),
                                'como_implementar': row_acao.get('Como será Implementado', ''),
                                'data_inicio': data_inicio,
                                'data_conclusao': data_conclusao,
                                'status': status_map.get(row_acao.get('Status'), StatusAcao.NAO_INICIADO),
                                'percentual_conclusao': percentual_map.get(row_acao.get('Status'), 0),
                                'tipo_monitoramento': TipoMonitoramento.PLANEJADO,
                                'observacoes_monitoramento': row_acao.get('Monitoramento', '')
                            }
                            
                            # Cria plano de ação
                            plano = PlanoAcaoCRUD.criar_plano_acao(session, plano_data, admin_user.id)
                            st.success(f"  ✅ Plano de ação criado: {plano.descricao_acao[:50]}...")
                            
                            # Associa responsáveis se encontrados
                            responsavel_nome = row_acao.get('Responsável Implementação')
                            if responsavel_nome and responsavel_nome.strip():
                                responsavel_user = UsuarioCRUD.obter_usuario_por_username(
                                    session, responsavel_nome.lower().replace(' ', '.')
                                )
                                if responsavel_user:
                                    plano.responsaveis.append(responsavel_user)
            
            # Commit das alterações
            session.commit()
            st.success("🎉 Migração concluída com sucesso!")
            
            # Mostra estatísticas
            total_riscos = session.query(Risco).count()
            total_planos = session.query(PlanoAcao).count()
            total_usuarios = session.query(Usuario).count()
            
            st.info(f"""
            📊 **Estatísticas da Migração:**
            - **Riscos criados:** {total_riscos}
            - **Planos de ação:** {total_planos}  
            - **Usuários:** {total_usuarios}
            """)
            
            return True
            
        except Exception as e:
            session.rollback()
            st.error(f"❌ Erro na migração: {str(e)}")
            st.exception(e)
            return False

def exemplo_uso_crud():
    """Exemplos de como usar as operações CRUD"""
    
    with session_scope() as session:
        st.subheader("📋 Exemplos de Uso das Operações CRUD")
        
        # 1. Dashboard de riscos
        dashboard = RiscoCRUD.obter_dashboard_riscos(session)
        st.write("**Dashboard de Riscos:**", dashboard)
        
        # 2. Listar riscos críticos
        riscos_criticos, total = RiscoCRUD.listar_riscos(
            session, 
            filtros={'criticidade': [NivelCriticidade.CRITICO, NivelCriticidade.ALTO]},
            limite=5
        )
        st.write(f"**Riscos Críticos/Altos encontrados:** {len(riscos_criticos)}")
        for risco in riscos_criticos:
            st.write(f"- {risco.codigo_risco}: {risco.titulo_evento[:100]}...")
        
        # 3. Planos atrasados
        planos_atrasados = PlanoAcaoCRUD.obter_planos_atrasados(session)
        st.write(f"**Planos Atrasados:** {len(planos_atrasados)}")
        for plano in planos_atrasados[:3]:  # Mostra apenas os 3 primeiros
            st.write(f"- {plano.descricao_acao[:80]}... (Prazo: {plano.data_conclusao})")
        
        # 4. Busca textual
        riscos_encontrados = []
        termo_busca = "edital"
        if termo_busca:
            from database.crud import BuscaAvancadaCRUD
            riscos_encontrados = BuscaAvancadaCRUD.buscar_riscos_texto(session, termo_busca)
            st.write(f"**Busca por '{termo_busca}':** {len(riscos_encontrados)} riscos encontrados")
        
        # 5. Filtros dinâmicos disponíveis
        from database.crud import BuscaAvancadaCRUD
        filtros_disponiveis = BuscaAvancadaCRUD.filtros_dinamicos(session)
        st.write("**Filtros Disponíveis:**", filtros_disponiveis)

def exemplo_relatorios():
    """Exemplos de relatórios"""
    
    from database.crud import RelatoriosCRUD
    
    with session_scope() as session:
        st.subheader("📊 Exemplos de Relatórios")
        
        # 1. Matriz de riscos
        if st.button("Gerar Matriz de Riscos"):
            df_matriz = RelatoriosCRUD.relatorio_matriz_riscos(session)
            st.dataframe(df_matriz)
            
            # Download como CSV
            csv = df_matriz.to_csv(index=False)
            st.download_button(
                label="📥 Download Matriz de Riscos (CSV)",
                data=csv,
                file_name="matriz_riscos.csv",
                mime="text/csv"
            )
        
        # 2. KPIs do período
        kpis = RelatoriosCRUD.relatorio_kpis_riscos(session, periodo_dias=30)
        st.write("**KPIs dos últimos 30 dias:**", kpis)
        
        # 3. Dashboard de planos
        dashboard_planos = PlanoAcaoCRUD.obter_dashboard_planos(session)
        st.write("**Dashboard de Planos de Ação:**", dashboard_planos)

def main():
    """Função principal para demonstração"""
    st.title("🛡️ Sistema de Gestão de Riscos - Migração de Dados")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🔄 Migração", "📊 Dashboard", "🔍 Exemplos CRUD", "📋 Relatórios"])
    
    with tab1:
        st.header("Migração dos Dados CSV")
        st.write("""
        Esta seção demonstra como migrar os dados das suas 4 planilhas CSV:
        - **Identificação de Risco.csv**
        - **Avaliação dos Riscos.csv** 
        - **Plano de Ação.csv**
        - **Escalas e Respostas.csv**
        """)
        
        if st.button("🚀 Executar Migração", type="primary"):
            with st.spinner("Migrando dados..."):
                sucesso = migrar_dados_completos()
                if sucesso:
                    st.balloons()
                    
        # Opção de resetar banco
        if st.button("⚠️ Resetar Banco (CUIDADO!)"):
            if st.checkbox("Confirmo que quero resetar todos os dados"):
                with session_scope() as session:
                    # Aqui você implementaria a limpeza do banco
                    st.warning("Funcionalidade de reset seria implementada aqui")
    
    with tab2:
        st.header("Dashboard do Sistema")
        try:
            exemplo_uso_crud()
        except Exception as e:
            st.error(f"Erro ao carregar dashboard: {str(e)}")
            st.info("Execute primeiro a migração dos dados na aba 'Migração'")
    
    with tab3:
        st.header("Exemplos de Operações CRUD")
        try:
            exemplo_uso_crud()
        except Exception as e:
            st.error(f"Erro: {str(e)}")
    
    with tab4:
        st.header("Relatórios")
        try:
            exemplo_relatorios()
        except Exception as e:
            st.error(f"Erro: {str(e)}")

if __name__ == "__main__":
    # Configuração da página Streamlit
    st.set_page_config(
        page_title="Gestão de Riscos - Migração",
        page_icon="🛡️",
        layout="wide"
    )
    
    # Executa aplicação
    main()
                        '
