import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_risk_matrix(df):
    """
    Cria uma matriz de riscos (probabilidade vs. impacto) usando Plotly.
    Argumentos:
        df (pandas.DataFrame): DataFrame com colunas 'Probabilidade' e 'Impacto'.
    Retorna:
        plotly.graph_objects.Figure: Gráfico de dispersão para a matriz de riscos.
    """
    # Mapear valores categóricos para numéricos
    prob_map = {"Baixa": 1, "Média": 2, "Alta": 3}
    impact_map = {"Baixo": 1, "Médio": 2, "Alto": 3}
    
    df["Probabilidade_Num"] = df["Probabilidade"].map(prob_map)
    df["Impacto_Num"] = df["Impacto"].map(impact_map)
    
    # Criar gráfico de dispersão
    fig = px.scatter(
        df,
        x="Probabilidade_Num",
        y="Impacto_Num",
        text="Descrição",
        size_max=60,
        hover_data=["Descrição", "Categoria"],
        title="Matriz de Riscos"
    )
    
    # Configurar eixos
    fig.update_xaxes(
        title="Probabilidade",
        tickvals=[1, 2, 3],
        ticktext=["Baixa", "Média", "Alta"],
        gridcolor="lightgray"
    )
    fig.update_yaxes(
        title="Impacto",
        tickvals=[1, 2, 3],
        ticktext=["Baixo", "Médio", "Alto"],
        gridcolor="lightgray"
    )
    
    # Ajustar layout
    fig.update_traces(
        textposition="top center",
        marker=dict(size=12, opacity=0.8)
    )
    fig.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True)
    )
    
    return fig

def create_category_bar_chart(df):
    """
    Cria um gráfico de barras mostrando a distribuição de riscos por categoria.
    Argumentos:
        df (pandas.DataFrame): DataFrame com coluna 'Categoria'.
    Retorna:
        plotly.graph_objects.Figure: Gráfico de barras.
    """
    # Contar riscos por categoria
    category_counts = df["Categoria"].value_counts().reset_index()
    category_counts.columns = ["Categoria", "Quantidade"]
    
    # Criar gráfico de barras
    fig = px.bar(
        category_counts,
        x="Categoria",
        y="Quantidade",
        title="Distribuição de Riscos por Categoria",
        color="Categoria",
        text="Quantidade"
    )
    
    # Ajustar layout
    fig.update_traces(textposition="auto")
    fig.update_layout(
        xaxis_title="Categoria",
        yaxis_title="Quantidade de Riscos",
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    
    return fig
