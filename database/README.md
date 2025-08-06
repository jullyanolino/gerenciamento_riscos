1. Migração dos Dados:
```python
# Migra automaticamente os 4 CSVs para o banco
migrar_dados_completos()
```

2. Operações CRUD:
```python
# Lista riscos críticos
riscos, total = RiscoCRUD.listar_riscos(
    session, 
    filtros={'criticidade': ['Crítico', 'Alto']},
    limite=10
)

# Cria plano de ação
plano = PlanoAcaoCRUD.criar_plano_acao(session, {
    'risco_id': risco.id,
    'descricao_acao': 'Nova ação de mitigação',
    'data_conclusao': datetime(2024, 12, 31)
}, user_id)
```

3. Dashboards:
```python
# Dashboard automático
dashboard = RiscoCRUD.obter_dashboard_riscos(session)
# Retorna: riscos por criticidade, fonte, categoria, etc.
```
