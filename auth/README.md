## Configuração Básica (Local):
``` python
from auth.authenticator import StreamlitAuthenticator, create_sample_config

config = create_sample_config()
auth = StreamlitAuthenticator(config)

# Login
name, username, auth_status = auth.login()
```
## Configuração Azure AD
``` python
from auth.azure_ad import AzureADAuthenticator

config = {
    'client_id': 'SEU_CLIENT_ID',
    'tenant_id': 'SEU_TENANT',
    'redirect_uri': 'https://seuapp.streamlit.app'
}

auth = AzureADAuthenticator(config)
auth.login_button()
```
## Configuração Híbrida
``` python
from auth.azure_ad import HybridAuthenticator

auth = HybridAuthenticator(local_config=config_local, azure_config=config_azure)

if auth.require_authentication():
    st.write("Usuário autenticado!")
```
