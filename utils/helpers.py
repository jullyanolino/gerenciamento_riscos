from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd
from io import BytesIO

def generate_pdf_report(df):
    """
    Gera um relatório em PDF com os dados dos riscos.
    Argumentos:
        df (pandas.DataFrame): DataFrame com colunas 'id', 'titulo_evento', 'probabilidade', 
                              'impacto', 'categoria', 'resposta_adotada', 'criticidade'.
    Retorna:
        BytesIO: Buffer com o conteúdo do PDF.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title = Paragraph("Relatório de Gerenciamento de Riscos", styles["Title"])
    elements.append(title)
    
    # Tabela de dados
    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def export_to_csv(df):
    """
    Exporta os dados dos riscos para um arquivo CSV.
    Argumentos:
        df (pandas.DataFrame): DataFrame com os dados dos riscos.
    Retorna:
        BytesIO: Buffer com o conteúdo do CSV.
    """
    buffer = BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8")
    buffer.seek(0)
    return buffer
