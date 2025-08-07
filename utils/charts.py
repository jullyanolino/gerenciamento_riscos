import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from database.models import NivelProbabilidade, NivelImpacto

def create_risk_matrix(df):
    """
    Cria uma matriz de riscos (probabilidade vs. impacto) usando Plotly.
    Argumentos:
        df (pandas.DataFrame): DataFrame com colunas 'probabilidade', 'impacto', 'titulo_evento', 'categoria'.
    Retorna:
        plotly.graph_objects.Figure: Gráfico de dispersão para a matriz de riscos.
    """
    # Mapear valores categóricos para numéricos
    prob_map = {
        NivelProbabilidade.MUITO_BAIXA.value: 1,
        NivelProbabilidade.BAIXA.value: 2,
        NivelProbabilidade.MEDIA.value: 3,
        NivelProbabilidade.ALTA.value: 4,
        NivelProbabilidade.MUITO_ALTA.value: 5
    }
    impact_map = {
        NivelImpacto.MUITO_BAIXO.value: 1,
        NivelImpacto.BAIXO.value: 2,
        NivelImpacto.MODERADO.value: 3,
        NivelImpacto.ALTO.value: 4,
        NivelImpacto.MUITO_ALTO.value: 5
    }
    
    df["Probabilidade_Num"] = df["probabilidade"].map(prob_map)
    df["Impacto_Num"] = df["impacto"].map(impact_map)
    
    # Criar gráfico de dispersão
    fig = px.scatter(
        df,
        x="Probabilidade_Num",
        y="Impacto_Num",
        text="titulo_evento",
        size_max=60,
        hover_data=["titulo_evento", "categoria"],
        title="Matriz de Riscos"
    )
    
    # Configurar eixos
    fig.update_xaxes(
        title="Probabilidade",
        tickvals=[1, 2, 3, 4, 5],
        ticktext=[NivelProbabilidade.MUITO_BAIXA.value, NivelProbabilidade.BAIXA.value,
                  NivelProbabilidade.MEDIA.value, NivelProbabilidade.ALTA.value,
                  NivelProbabilidade.MUITO_ALTA.value],
        gridcolor="lightgray"
    )
    fig.update_yaxes(
        title="Impacto",
        tickvals=[1, 2, 3, 4, 5],
        ticktext=[NivelImpacto.MUITO_BAIXO.value, NivelImpacto.BAIXO.value,
                  NivelImpacto.MODERADO.value, NivelImpacto.ALTO.value,
                  NivelImpacto.MUITO_ALTO.value],
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
        df (pandas.DataFrame): DataFrame com coluna 'categoria'.
    Retorna:
        plotly.graph_objects.Figure: Gráfico de barras.
    """
    # Contar riscos por categoria
    category_counts = df["categoria"].value_counts().reset_index()
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
