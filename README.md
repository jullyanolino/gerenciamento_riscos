# Ferramenta de Gerenciamento de Riscos

## Estrutura do Projeto

```
gerenciamento_riscos/
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
# Interface web e autenticação
streamlit>=1.28.0,<2.0.0  # Framework para a aplicação web, versão estável
streamlit-authenticator>=0.2.3,<0.3.0  # Autenticação de usuários
msal>=1.24.0,<2.0.0  # Microsoft Authentication Library para Azure AD
msal-streamlit>=0.1.9,<0.2.0  # Integração do MSAL com Streamlit

# Banco de dados
sqlalchemy>=2.0.23,<3.0.0  # ORM para manipulação de banco de dados
psycopg2-binary>=2.9.9,<3.0.0  # Conector para PostgreSQL

# Manipulação e visualização de dados
pandas>=2.1.3,<3.0.0  # Manipulação de dados em DataFrames
plotly>=5.17.0,<6.0.0  # Gráficos interativos para dashboard

# Geração de relatórios
reportlab>=4.0.7,<5.0.0  # Geração de relatórios em PDF

# Utilitários
python-dotenv>=1.0.0,<2.0.0  # Carregamento de variáveis de ambiente
```
### Instalação das Dependências:
``` bash
pip install -r requirements.txt
```

## Popular Banco de Dados
``` bash
python -c "from database.connection import seed_database; seed_database()"
```

## Execução
``` bash
streamlit run app.py
```
