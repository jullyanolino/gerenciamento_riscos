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
    Exemplo específico para migrar os CSVs
    """
    
    # Simulação dos dados dos CSVs
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
                        '
