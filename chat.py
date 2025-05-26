import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from openai import OpenAI
import re
from visualization_generator import VisualizationGenerator, display_visualization

load_dotenv()

#Armazenei os dados na AWS (RDS MySQL)
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'port': int(os.getenv('MYSQL_PORT', 3306))
}

class DatabaseChatbot:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        connection_string = (
            f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@"
            f"{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
        )
        self.engine = create_engine(connection_string)
        
    def get_table_schema(self):
        try:
            with self.engine.connect() as conn:
                schema_query = """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'neurotech' AND TABLE_NAME = 'neurotech'
                ORDER BY ORDINAL_POSITION;
                """
                schema_df = pd.read_sql(schema_query, conn)
                
                sample_query = "SELECT * FROM neurotech LIMIT 5;"
                sample_df = pd.read_sql(sample_query, conn)
                
                return schema_df, sample_df
        except Exception as e:
            st.error(f"Erro ao obter esquema: {e}")
            return None, None

    def execute_sql_query(self, query):
        try:
            with self.engine.connect() as conn:
                return pd.read_sql(text(query), conn)
        except Exception as e:
            return f"Erro na execução da query: {e}"

    def generate_sql_from_question(self, question, schema_info):
        context = f"""
        Você é um especialista em SQL e análise de dados de inadimplência. 
        
        CONTEXTO DA BASE DE DADOS:
        - Tabela: neurotech.neurotech
        - Colunas disponíveis:
          * REF_DATE: data de referência do registro
          * TARGET: alvo binário de inadimplência (1: Mau Pagador - atraso > 60 dias em 2 meses, 0: Bom Pagador)
          * VAR2: sexo do cliente
          * IDADE: idade do indivíduo
          * VAR4: flag de óbito (indica se o indivíduo faleceu)
          * VAR5: unidade federativa (UF) brasileira
          * VAR8: classe social estimada
        
        ESQUEMA DA TABELA:
        {schema_info}
        
        INSTRUÇÕES:
        1. Gere APENAS a query SQL, sem explicações adicionais
        2. Use apenas as colunas que existem na tabela
        3. Para perguntas sobre inadimplência, use TARGET (1 = inadimplente, 0 = adimplente)
        4. Sempre limite os resultados quando apropriado (use LIMIT)
        5. Use nomes de colunas exatos conforme mostrado no esquema
        
        PERGUNTA DO USUÁRIO: {question}
        
        SQL:
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo", #não acho que nessa aplicação precisamos de um modelo mais robusto
                messages=[{"role": "user", "content": context}],
                max_tokens=200,
                temperature=0
            )
            sql_query = response.choices[0].message.content.strip()
            return re.sub(r'^```sql\s*|```\s*$', '', sql_query).strip()
        except Exception as e:
            return f"Erro ao gerar SQL: {e}"

    def explain_results(self, question, sql_query, results):
        if isinstance(results, str):
            return results
            
        results_text = results.to_string() if len(results) <= 10 else results.head(10).to_string() + f"\n... e mais {len(results)-10} registros"
        
        context = f"""
        O usuário fez a pergunta: "{question}"
        
        SQL gerado: {sql_query}
        
        Resultados obtidos:
        {results_text}
        
        Por favor, explique os resultados de forma clara e em português, destacando os insights principais sobre inadimplência quando relevante.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": context}],
                max_tokens=300,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Erro ao explicar resultados: {e}"

def main():
    st.set_page_config(page_title="Consulta SQL", layout="wide")
    
    st.title("Consulta SQL por Linguagem Natural")
    st.markdown("Converse com seus dados!")
    
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OPENAI_API_KEY não está configurada. Configure no arquivo .env")
        return
    
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = DatabaseChatbot()
    
    if 'viz_generator' not in st.session_state:
        st.session_state.viz_generator = VisualizationGenerator()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    st.subheader("💬 Converse com seus dados")
    
    with st.expander("💡 Exemplos de perguntas que você pode fazer"):
        st.write("""
        - Quantos clientes inadimplentes temos?
        - Qual a distribuição por idade dos inadimplentes?
        - Qual UF tem mais inadimplência?
        - Mostre a inadimplência por sexo
        """)
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "dataframe" in message:
                st.dataframe(message["dataframe"])
    
    if prompt := st.chat_input("Faça sua pergunta sobre os dados..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Analisando sua pergunta..."):
                schema_df, sample_df = st.session_state.chatbot.get_table_schema()
                schema_info = schema_df.to_string() if schema_df is not None else ""
                
                sql_query = st.session_state.chatbot.generate_sql_from_question(prompt, schema_info)
                
                st.code(sql_query, language="sql")
                
                results = st.session_state.chatbot.execute_sql_query(sql_query)
                
                if isinstance(results, pd.DataFrame):
                    st.dataframe(results, use_container_width=True)
                    
                    display_visualization(st.session_state.viz_generator, prompt, sql_query, results)
                    
                    explanation = st.session_state.chatbot.explain_results(prompt, sql_query, results)
                    st.markdown(explanation)
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"**SQL gerada:**\n```sql\n{sql_query}\n```\n\n**Explicação:**\n{explanation}",
                        "dataframe": results
                    })
                else:
                    st.error(results)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"**Erro:**\n{results}"
                    })

if __name__ == "__main__":
    main() 