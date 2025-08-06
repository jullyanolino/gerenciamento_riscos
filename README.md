# Ferramenta de Gerenciamento de Riscos

## Estrutura do Projeto

```
risk_management/
├── app.py                 # Aplicação principal
├── auth/
│   ├── authenticator.py   # Lógica de autenticação
│   └── azure_ad.py        # Integração Azure AD
├── database/
│   ├── models.py          # Modelos de dados
│   ├── crud.py           # Operações CRUD
│   └── connection.py     # Conexão com BD
├── pages/
│   ├── risk_register.py   # Cadastro de riscos
│   ├── dashboard.py       # Dashboards e gráficos
│   └── reports.py         # Relatórios
├── utils/
│   ├── charts.py          # Funções para gráficos
│   └── helpers.py         # Funções auxiliares
└── requirements.txt
```

## Dependências
```
streamlit==1.28.0
streamlit-authenticator==0.2.3
msal-streamlit==0.1.9
sqlalchemy==2.0.23
pandas==2.1.3
plotly==5.17.0
altair==5.1.2
psycopg2-binary==2.9.9  # Para PostgreSQL
python-dotenv==1.0.0
```
