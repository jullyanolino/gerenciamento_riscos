import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from pathlib import Path

# Initializing session state for data persistence
if 'risk_identification' not in st.session_state:
    st.session_state.risk_identification = pd.DataFrame()
if 'risk_assessment' not in st.session_state:
    st.session_state.risk_assessment = pd.DataFrame()
if 'action_plan' not in st.session_state:
    st.session_state.action_plan = pd.DataFrame()

# File paths for saving data
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
RISK_IDENTIFICATION_PATH = os.path.join(DATA_DIR, "Identificação de Risco.csv")
RISK_ASSESSMENT_PATH = os.path.join(DATA_DIR, "Avaliação dos Riscos.csv")
ACTION_PLAN_PATH = os.path.join(DATA_DIR, "Plano de Ação.csv")

# Helper function to save DataFrame to CSV
def save_to_csv(df, path):
    if not df.empty:
        df.to_csv(path, index=False, encoding='utf-8')

# Helper function to load CSV with error handling
def load_csv(uploaded_file, default_path):
    try:
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        else:
            df = pd.read_csv(default_path, encoding='utf-8') if os.path.exists(default_path) else pd.DataFrame()
        return df.fillna('')
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

# Home page
def home_page():
    st.title("Risk Management Dashboard")
    st.write("Welcome to the Risk Management Dashboard. Use the sidebar to navigate between pages to view, edit, or visualize risk data.")
    
    # Displaying summary metrics
    if not st.session_state.risk_assessment.empty:
        st.header("Summary Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Risks", len(st.session_state.risk_assessment))
        with col2:
            critical_risks = len(st.session_state.risk_assessment[st.session_state.risk_assessment['CRITICIDADE'] == 'Crítico'])
            st.metric("Critical Risks", critical_risks)
        with col3:
            actions_in_progress = len(st.session_state.action_plan[st.session_state.action_plan['Status'] == 'Em andamento'])
            st.metric("Actions In Progress", actions_in_progress)

# Risk Identification page
def risk_identification_page():
    st.title("Risk Identification")
    st.write("View and edit risk identification data. Upload a new CSV or edit the table below.")

    # File uploader
    uploaded_file = st.file_uploader("Upload Identificação de Risco CSV", type="csv", key="risk_id_upload")
    if uploaded_file:
        st.session_state.risk_identification = load_csv(uploaded_file, RISK_IDENTIFICATION_PATH)
        save_to_csv(st.session_state.risk_identification, RISK_IDENTIFICATION_PATH)

    # Displaying and editing data
    if not st.session_state.risk_identification.empty:
        st.subheader("Edit Risk Identification Data")
        edited_df = st.data_editor(
            st.session_state.risk_identification,
            num_rows="dynamic",
            column_config={
                "ID": st.column_config.NumberColumn("ID", min_value=1, step=1),
                "FONTE": st.column_config.TextColumn("Source"),
                "Etapas": st.column_config.TextColumn("Stages"),
                "CAUSA": st.column_config.TextColumn("Cause"),
                "CATEGORIA": st.column_config.SelectboxColumn("Category", options=["Conformidade", "Integridade", "Operacional", "Estratégico", "Orçamentário", "Imagem"]),
                "DESCRIÇÃO": st.column_config.TextColumn("Description"),
                "TIPO": st.column_config.TextColumn("Type"),
                "CONSEQUÊNCIA": st.column_config.TextColumn("Consequence")
            },
            use_container_width=True
        )
        st.session_state.risk_identification = edited_df
        save_to_csv(edited_df, RISK_IDENTIFICATION_PATH)
    else:
        st.warning("No data available. Please upload a CSV file.")

# Risk Assessment page
def risk_assessment_page():
    st.title("Risk Assessment")
    st.write("View and edit risk assessment data. Visualize risk distribution with charts.")

    # File uploader
    uploaded_file = st.file_uploader("Upload Avaliação dos Riscos CSV", type="csv", key="risk_assess_upload")
    if uploaded_file:
        st.session_state.risk_assessment = load_csv(uploaded_file, RISK_ASSESSMENT_PATH)
        save_to_csv(st.session_state.risk_assessment, RISK_ASSESSMENT_PATH)

    # Displaying and editing data
    if not st.session_state.risk_assessment.empty:
        st.subheader("Edit Risk Assessment Data")
        edited_df = st.data_editor(
            st.session_state.risk_assessment,
            num_rows="dynamic",
            column_config={
                "EAP": st.column_config.NumberColumn("EAP", min_value=1, step=1),
                "RISCO": st.column_config.TextColumn("Risk"),
                "CAUSA": st.column_config.TextColumn("Cause"),
                "CONSEQUÊNCIAS": st.column_config.TextColumn("Consequences"),
                "IMPACTO": st.column_config.SelectboxColumn("Impact", options=["Muito baixo", "Baixo", "Moderado", "Alto", "Muito alto"]),
                "PROBABILIDADE": st.column_config.SelectboxColumn("Probability", options=["Muito baixa", "Baixa", "Média", "Alta", "Muito alta"]),
                "CRITICIDADE": st.column_config.SelectboxColumn("Criticality", options=["Baixo", "Alto", "Crítico"]),
                "RESPOSTA SUGERIDA": st.column_config.SelectboxColumn("Suggested Response", options=["Evitar", "Compartilhar", "Mitigar", "Aceitar"]),
                "RESPOSTA ADOTADA": st.column_config.SelectboxColumn("Adopted Response", options=["Evitar", "Compartilhar", "Mitigar", "Aceitar", "Sem Resposta"])
            },
            use_container_width=True
        )
        st.session_state.risk_assessment = edited_df
        save_to_csv(edited_df, RISK_ASSESSMENT_PATH)

        # Visualizations
        st.subheader("Risk Visualizations")
        col1, col2 = st.columns(2)

        with col1:
            # Heatmap for Probability vs Impact
            st.write("Probability vs Impact Heatmap")
            heatmap_data = st.session_state.risk_assessment.groupby(['PROBABILIDADE', 'IMPACTO']).size().reset_index(name='Count')
            heatmap_pivot = heatmap_data.pivot(index="PROBABILIDADE", columns="IMPACTO", values="Count").fillna(0)
            fig = px.imshow(
                heatmap_pivot,
                labels=dict(x="Impact", y="Probability", color="Count"),
                x=["Muito baixo", "Baixo", "Moderado", "Alto", "Muito alto"],
                y=["Muito baixa", "Baixa", "Média", "Alta", "Muito alta"],
                color_continuous_scale="Reds"
            )
            fig.update_layout(font=dict(size=12))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Criticality Distribution
            st.write("Criticality Distribution")
            crit_counts = st.session_state.risk_assessment['CRITICIDADE'].value_counts().reset_index()
            crit_counts.columns = ['Criticality', 'Count']
            fig = px.pie(crit_counts, names='Criticality', values='Count', title="Criticality Distribution")
            fig.update_layout(font=dict(size=12))
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("No data available. Please upload a CSV file.")

# Action Plan page
def action_plan_page():
    st.title("Action Plan")
    st.write("View and edit action plan data. Track progress with charts.")

    # File uploader
    uploaded_file = st.file_uploader("Upload Plano de Ação CSV", type="csv", key="action_plan_upload")
    if uploaded_file:
        st.session_state.action_plan = load_csv(uploaded_file, ACTION_PLAN_PATH)
        save_to_csv(st.session_state.action_plan, ACTION_PLAN_PATH)

    # Displaying and editing data
    if not st.session_state.action_plan.empty:
        st.subheader("Edit Action Plan Data")
        edited_df = st.data_editor(
            st.session_state.action_plan,
            num_rows="dynamic",
            column_config={
                "EAP": st.column_config.NumberColumn("EAP", min_value=1, step=1),
                "Evento de Risco": st.column_config.TextColumn("Risk Event"),
                "Fator de Risco": st.column_config.TextColumn("Risk Factor"),
                "Descrição da Ação": st.column_config.TextColumn("Action Description"),
                "Área Responsável pela Implementação": st.column_config.TextColumn("Responsible Area"),
                "Responsável Implementação": st.column_config.TextColumn("Responsible Person"),
                "Interveniete": st.column_config.TextColumn("Intervener"),
                "Como será Implementado": st.column_config.TextColumn("Implementation Method"),
                "Data do Início": st.column_config.TextColumn("Start Date"),
                "Data da Conclusão": st.column_config.TextColumn("End Date"),
                "Status": st.column_config.SelectboxColumn("Status", options=["Concluído", "Em andamento", "Não Iniciado", "Atrasado"]),
                "Monitoramento": st.column_config.TextColumn("Monitoring")
            },
            use_container_width=True
        )
        st.session_state.action_plan = edited_df
        save_to_csv(edited_df, ACTION_PLAN_PATH)

        # Visualization: Action Plan Status
        st.subheader("Action Plan Progress")
        status_counts = st.session_state.action_plan['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig = px.bar(status_counts, x='Status', y='Count', title="Action Plan Status Distribution", color='Status')
        fig.update_layout(font=dict(size=12))
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("No data available. Please upload a CSV file.")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Risk Identification", "Risk Assessment", "Action Plan"])

# Page routing
if page == "Home":
    home_page()
elif page == "Risk Identification":
    risk_identification_page()
elif page == "Risk Assessment":
    risk_assessment_page()
elif page == "Action Plan":
    action_plan_page()
