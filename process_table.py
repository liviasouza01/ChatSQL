import pandas as pd
from sqlalchemy import create_engine
import pymysql #O SQLAlchemy precisa de um driver como pymysql ou mysqlclient
import os
from dotenv import load_dotenv

load_dotenv()

csv_url = 'https://github.com/Neurolake/challenge-data-scientist/raw/main/datasets/credit_01/train.gz'

columns_to_select = [
    'REF_DATE',
    'TARGET',
    'VAR2',
    'IDADE',
    'VAR4',
    'VAR5',
    'VAR8'
]

try:
    df = pd.read_csv(csv_url, compression='gzip')

    existing_columns = [col for col in columns_to_select if col in df.columns]
    
    if len(existing_columns) != len(columns_to_select):
        missing_cols = [col for col in columns_to_select if col not in df.columns]
        print(f"Warning: As seguintes colunas não foram encontradas no CSV: {', '.join(missing_cols)}")
        if not existing_columns:
            print("Nenhuma coluna especificada encontrada. Saindo.")
            exit()
        print(f"Processing with the available columns: {', '.join(existing_columns)}")

    df_selected = df[existing_columns]

    print("Primeiras 5 linhas da tabela com as colunas selecionadas:")
    print(df_selected.head())

    output_csv_path = 'neurodata.csv'
    df_selected.to_csv(output_csv_path, index=False)
    print(f"\nDados selecionados salvos em {output_csv_path}")

    mysql_host = os.getenv('MYSQL_HOST')
    mysql_user = os.getenv('MYSQL_USER')
    mysql_password = os.getenv('MYSQL_PASSWORD')
    mysql_database = os.getenv('MYSQL_DATABASE')
    table_name = 'neurotech'

    try:
        engine = create_engine(f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_database}')
        df_selected.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Data also saved to MySQL database '{mysql_database}' in table '{table_name}'.")
    except ImportError:
        print("Erro: pymysql library não encontrada. Instale usando 'pip install pymysql'")
    except Exception as e:
        print(f"Erro ao conectar-se ou escrever no MySQL: {e}")

except FileNotFoundError:
    print(f"Erro: O arquivo '{csv_url}' não foi encontrado.")
except Exception as e:
    print(f"Erro: {e}")