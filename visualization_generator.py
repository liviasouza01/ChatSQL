import pandas as pd
import plotly.express as px
import streamlit as st
from openai import OpenAI
import os

class VisualizationGenerator:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def analyze_data_for_visualization(self, question, sql_query, data):
        if data is None or len(data) == 0:
            return None, "Não há dados para visualizar"
        
        numeric_columns = data.select_dtypes(include=['int64', 'float64']).columns.tolist()
        categorical_columns = data.select_dtypes(include=['object', 'category']).columns.tolist()
        
        #Lógica para determinar o tipo de gráfico
        if 'TARGET' in data.columns and 'IDADE' in data.columns:
            return self._create_histogram(data, "Distribuição de Idade por Status de Inadimplência")
        elif len(numeric_columns) >= 2:
            return self._create_scatter_plot(data, "Relação entre Variáveis Numéricas")
        elif len(categorical_columns) >= 1:
            return self._create_bar_chart(data, "Distribuição de Categorias")
        else:
            return None, "Visualização em tabela é mais apropriada para estes dados"
    
    def generate_visualization(self, data, chart_type, question):
        try:
            if chart_type == "bar_chart":
                return self._create_bar_chart(data, question)
            elif chart_type == "pie_chart":
                return self._create_pie_chart(data, question)
            elif chart_type == "line_chart":
                return self._create_line_chart(data, question)
            elif chart_type == "histogram":
                return self._create_histogram(data, question)
            elif chart_type == "scatter_plot":
                return self._create_scatter_plot(data, question)
            elif chart_type == "metric":
                return self._create_metrics(data, question)
            else:
                return None, "Visualização em tabela é mais apropriada para estes dados"
                
        except Exception as e:
            return None, f"Erro ao gerar visualização: {e}"
    
    def _create_bar_chart(self, data, question):
        if len(data.columns) >= 2:
            x_col, y_col = data.columns[:2]
            fig = px.bar(data, x=x_col, y=y_col, title=f"Gráfico de Barras: {question}")
            fig.update_layout(xaxis_tickangle=-45)
            return fig, "Gráfico de barras gerado com sucesso"
        return None, "Dados insuficientes para gráfico de barras"
    
    def _create_pie_chart(self, data, question):
        if len(data.columns) >= 2:
            labels_col, values_col = data.columns[:2]
            fig = px.pie(data, names=labels_col, values=values_col, title=f"Distribuição: {question}")
            return fig, "Gráfico de pizza gerado com sucesso"
        return None, "Dados insuficientes para gráfico de pizza"
    
    def _create_line_chart(self, data, question):
        if len(data.columns) >= 2:
            x_col, y_col = data.columns[:2]
            fig = px.line(data, x=x_col, y=y_col, title=f"Tendência: {question}", markers=True)
            return fig, "Gráfico de linha gerado com sucesso"
        return None, "Dados insuficientes para gráfico de linha"
    
    def _create_histogram(self, data, question):
        numeric_cols = data.select_dtypes(include=['int64', 'float64']).columns
        if numeric_cols:
            col = numeric_cols[0]
            fig = px.histogram(data, x=col, title=f"Distribuição de {col}: {question}", nbins=20)
            return fig, "Histograma gerado com sucesso"
        return None, "Nenhuma coluna numérica encontrada para histograma"
    
    def _create_scatter_plot(self, data, question):
        numeric_cols = data.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) >= 2:
            x_col, y_col = numeric_cols[:2]
            fig = px.scatter(data, x=x_col, y=y_col, title=f"Relação: {x_col} vs {y_col}", trendline="ols")
            return fig, "Gráfico de dispersão gerado com sucesso"
        return None, "Necessárias pelo menos 2 colunas numéricas para dispersão"
    
    def _create_metrics(self, data, question):
        metrics = {}
        for col in data.columns:
            if data[col].dtype in ['int64', 'float64']:
                metrics[col] = {
                    'Total': data[col].sum(),
                    'Média': data[col].mean(),
                    'Máximo': data[col].max(),
                    'Mínimo': data[col].min()
                }
        return metrics, "Métricas calculadas com sucesso"

def display_visualization(viz_generator, question, sql_query, data):
    if data is None or len(data) == 0:
        st.warning("Não há dados para visualizar")
        return
    
    chart, message = viz_generator.analyze_data_for_visualization(question, sql_query, data)
    
    if chart is not None:
        if isinstance(chart, dict):
            st.subheader("Métricas")
            cols = st.columns(len(chart))
            for i, (key, value) in enumerate(chart.items()):
                with cols[i]:
                    st.metric(f"{key} - Total", f"{value['Total']:,.0f}")
                    st.metric(f"{key} - Média", f"{value['Média']:,.2f}")
        else:
            st.subheader("Visualização")
            st.plotly_chart(chart, use_container_width=True)
    
    st.info(message)

