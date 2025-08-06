# auth/authenticator.py

import streamlit as st
import hashlib
import hmac
import jwt
import datetime
from typing import Optional, Dict, Tuple, List
import yaml
from yaml.loader import SafeLoader

class StreamlitAuthenticator:
    """
    Sistema de autenticação personalizado para Streamlit
    Suporta autenticação local e integração com Azure AD
    """
    
    def __init__(self, config: Dict):
        """
        Inicializa o autenticador com configurações
        
        Args:
            config: Dicionário com configurações de usuários e credenciais
        """
        self.credentials = config['credentials']
        self.cookie_name = config.get('cookie', {}).get('name', 'risk_management_auth')
        self.cookie_key = config.get('cookie', {}).get('key', 'risk_management_key')
        self.cookie_expiry_days = config.get('cookie', {}).get('expiry_days', 30)
        self.preauthorized = config.get('preauthorized', {}).get('emails', [])
        
    def _hash_password(self, password: str) -> str:
        """Gera hash da senha usando SHA256"""
        return hashlib.sha256(str.encode(password)).hexdigest()
        
    def _verify_password(self, stored_password: str, provided_password: str) -> bool:
        """Verifica se a senha fornecida corresponde à armazenada"""
        return stored_password == self._hash_password(provided_password)
        
    def _generate_token(self, username: str) -> str:
        """Gera token JWT para o usuário"""
        payload = {
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=self.cookie_expiry_days)
        }
        return jwt.encode(payload, self.cookie_key, algorithm='HS256')
        
    def _decode_token(self, token: str) -> Optional[Dict]:
        """Decodifica e verifica token JWT"""
        try:
            payload = jwt.decode(token, self.cookie_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
            
    def _set_cookie(self, token: str):
        """Define cookie no navegador (simulado via session_state)"""
        st.session_state[f'{self.cookie_name}_token'] = token
        
    def _get_cookie(self) -> Optional[str]:
        """Recupera token do cookie"""
        return st.session_state.get(f'{self.cookie_name}_token')
        
    def _delete_cookie(self):
        """Remove cookie de autenticação"""
        if f'{self.cookie_name}_token' in st.session_state:
            del st.session_state[f'{self.cookie_name}_token']
            
    def check_authentication(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Verifica se o usuário está autenticado
        
        Returns:
            Tuple com (nome, username, authentication_status)
            authentication_status: None (não verificado), False (falhou), True (sucesso)
        """
        # Verifica se já existe uma sessão ativa
        if 'authentication_status' in st.session_state:
            if st.session_state['authentication_status']:
                return (
                    st.session_state.get('name'),
                    st.session_state.get('username'), 
                    st.session_state['authentication_status']
                )
        
        # Verifica cookie/token
        token = self._get_cookie()
        if token:
            payload = self._decode_token(token)
            if payload:
                username = payload['username']
                if username in self.credentials['usernames']:
                    user_info = self.credentials['usernames'][username]
                    st.session_state['authentication_status'] = True
                    st.session_state['name'] = user_info['name']
                    st.session_state['username'] = username
                    st.session_state['user_role'] = user_info.get('role', 'user')
                    return user_info['name'], username, True
        
        return None, None, None
        
    def login(self, location: str = 'main') -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Renderiza formulário de login
        
        Args:
            location: Onde renderizar ('main', 'sidebar')
            
        Returns:
            Tuple com (nome, username, authentication_status)
        """
        # Se já autenticado, retorna informações
        name, username, auth_status = self.check_authentication()
        if auth_status:
            return name, username, auth_status
            
        # Renderiza formulário de login
        if location == 'sidebar':
            login_form = st.sidebar.form('Login')
        else:
            login_form = st.form('Login')
            
        with login_form:
            st.markdown('### 🔐 Login - Gerenciamento de Riscos')
            username = st.text_input('Usuário').lower()
            password = st.text_input('Senha', type='password')
            submit_button = st.form_submit_button('Entrar')
            
            if submit_button:
                if self._authenticate_user(username, password):
                    user_info = self.credentials['usernames'][username]
                    
                    # Gera token e define cookie
                    token = self._generate_token(username)
                    self._set_cookie(token)
                    
                    # Define sessão
                    st.session_state['authentication_status'] = True
                    st.session_state['name'] = user_info['name']
                    st.session_state['username'] = username
                    st.session_state['user_role'] = user_info.get('role', 'user')
                    
                    st.success(f'Bem-vindo(a), {user_info["name"]}!')
                    st.rerun()
                    
                else:
                    st.session_state['authentication_status'] = False
                    st.error('Usuário ou senha incorretos')
                    
        return None, None, st.session_state.get('authentication_status')
        
    def _authenticate_user(self, username: str, password: str) -> bool:
        """Autentica usuário com credenciais locais"""
        if username in self.credentials['usernames']:
            user_info = self.credentials['usernames'][username]
            return self._verify_password(user_info['password'], password)
        return False
        
    def logout(self, button_name: str = 'Logout', location: str = 'sidebar'):
        """
        Renderiza botão de logout
        
        Args:
            button_name: Texto do botão
            location: Onde renderizar ('main', 'sidebar')
        """
        if location == 'sidebar':
            if st.sidebar.button(button_name):
                self._perform_logout()
        else:
            if st.button(button_name):
                self._perform_logout()
                
    def _perform_logout(self):
        """Executa logout do usuário"""
        # Limpa cookie
        self._delete_cookie()
        
        # Limpa session_state
        keys_to_clear = [
            'authentication_status', 'name', 'username', 'user_role'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
                
        st.success('Logout realizado com sucesso!')
        st.rerun()
        
    def register_user(self, location: str = 'main') -> Tuple[bool, str]:
        """
        Renderiza formulário de registro de novo usuário
        
        Args:
            location: Onde renderizar ('main', 'sidebar')
            
        Returns:
            Tuple com (success, message)
        """
        if location == 'sidebar':
            register_form = st.sidebar.form('Register User')
        else:
            register_form = st.form('Register User')
            
        with register_form:
            st.markdown('### 📝 Cadastro de Usuário')
            name = st.text_input('Nome Completo')
            email = st.text_input('Email')
            username = st.text_input('Nome de Usuário').lower()
            password = st.text_input('Senha', type='password')
            password_confirm = st.text_input('Confirmar Senha', type='password')
            role = st.selectbox('Função', ['user', 'admin', 'viewer'])
            
            submit_button = st.form_submit_button('Cadastrar')
            
            if submit_button:
                return self._create_user(name, email, username, password, password_confirm, role)
                
        return False, ""
        
    def _create_user(self, name: str, email: str, username: str, 
                    password: str, password_confirm: str, role: str) -> Tuple[bool, str]:
        """Cria novo usuário"""
        # Validações
        if not all([name, email, username, password]):
            return False, "Todos os campos são obrigatórios"
            
        if password != password_confirm:
            return False, "Senhas não conferem"
            
        if len(password) < 6:
            return False, "Senha deve ter pelo menos 6 caracteres"
            
        if username in self.credentials['usernames']:
            return False, "Nome de usuário já existe"
            
        # Verifica se email está pré-autorizado (se lista existir)
        if self.preauthorized and email not in self.preauthorized:
            return False, "Email não está pré-autorizado para registro"
            
        # Adiciona usuário
        self.credentials['usernames'][username] = {
            'name': name,
            'email': email,
            'password': self._hash_password(password),
            'role': role,
            'created_at': datetime.datetime.now().isoformat()
        }
        
        return True, f"Usuário {username} criado com sucesso!"
        
    def get_user_info(self) -> Optional[Dict]:
        """Retorna informações do usuário logado"""
        if st.session_state.get('authentication_status'):
            username = st.session_state.get('username')
            if username and username in self.credentials['usernames']:
                return self.credentials['usernames'][username]
        return None
        
    def require_authentication(self, redirect_to_login: bool = True) -> bool:
        """
        Decorator/função para exigir autenticação em páginas
        
        Args:
            redirect_to_login: Se deve mostrar tela de login quando não autenticado
            
        Returns:
            True se autenticado, False caso contrário
        """
        name, username, auth_status = self.check_authentication()
        
        if not auth_status:
            if redirect_to_login:
                st.warning("⚠️ Acesso restrito. Faça login para continuar.")
                self.login()
            return False
            
        return True
        
    def require_role(self, required_roles: List[str]) -> bool:
        """
        Verifica se usuário tem uma das funções necessárias
        
        Args:
            required_roles: Lista de funções aceitas
            
        Returns:
            True se tem permissão, False caso contrário
        """
        if not self.require_authentication(redirect_to_login=False):
            return False
            
        user_role = st.session_state.get('user_role', 'user')
        if user_role not in required_roles:
            st.error(f"🚫 Acesso negado. Função necessária: {', '.join(required_roles)}")
            return False
            
        return True

def load_config_from_yaml(config_file: str) -> Dict:
    """Carrega configuração de arquivo YAML"""
    with open(config_file) as file:
        config = yaml.load(file, Loader=SafeLoader)
    return config

def create_sample_config() -> Dict:
    """Cria configuração de exemplo para testes"""
    return {
        'credentials': {
            'usernames': {
                'admin': {
                    'name': 'Administrador',
                    'email': 'admin@empresa.com',
                    'password': 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f',  # secret123
                    'role': 'admin'
                },
                'user1': {
                    'name': 'João Silva',
                    'email': 'joao@empresa.com', 
                    'password': 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f',  # secret123
                    'role': 'user'
                }
            }
        },
        'cookie': {
            'name': 'risk_management_auth',
            'key': 'sua_chave_secreta_super_forte_aqui_123',
            'expiry_days': 30
        },
        'preauthorized': {
            'emails': ['admin@empresa.com', 'user@empresa.com']
        }
    }
