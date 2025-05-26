# Converse com seu banco de dados!

Um chatbot inteligente que permite consultar bancos de dados MySQL usando linguagem natural em português. O sistema converte perguntas em SQL, executa as consultas e gera visualizações automáticas dos resultados.

## 🎥 Demonstração

**[📹 Assista à demonstração completa (NL2SQL.mp4)](./NL2SQL.mp4)**

<video width="100%" controls>
  <source src="./NL2SQL.mp4" type="video/mp4">
  Seu navegador não suporta a tag de vídeo. <a href="./NL2SQL.mp4">Clique aqui para baixar o vídeo</a>.
</video>

*Demonstração mostrando consultas em linguagem natural sendo convertidas em SQL e visualizações*

## Funcionalidades

- **Consultas em Linguagem Natural**: Faça perguntas em português sobre seus dados
- **Geração Automática de SQL**: Converte perguntas em consultas SQL otimizadas
- **Visualizações Inteligentes**: Gera gráficos automaticamente baseados nos resultados
- **Interface Streamlit**: Interface web intuitiva e responsiva
- **Explicações Contextuais**: Explica os resultados de forma clara
- **Testes de Robustez**: Suite completa de testes automatizados

## Tecnologias Utilizadas

- **Python 3.8+**
- **Streamlit** - Interface web
- **OpenAI GPT-3.5** - Processamento de linguagem natural
- **MySQL** - Banco de dados
- **SQLAlchemy** - ORM e conexão com banco
- **Pandas** - Manipulação de dados
- **Plotly** - Visualizações interativas
- **PyMySQL** - Driver MySQL

## Pré-requisitos

- Python 3.8 ou superior
- MySQL Server
- Conta OpenAI com API Key
- Pip para instalação de dependências

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/liviasouza01/ChatSQL.git
cd chatsql
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

### 4. Prepare seus dados

#### Opção A: Usar os dados de exemplo
Execute o script para baixar e processar os dados de exemplo:

#### Opção B: Usar seus próprios dados
1. Substitua a URL no `process_table.py` pela localização dos seus dados
2. Ajuste as colunas em `columns_to_select` conforme necessário
3. Execute o script

## 🎯 Como Usar

### 1. Inicie a aplicação

```bash
streamlit run chat.py
```

### 2. Acesse a interface
Abra seu navegador e vá para `http://localhost:8501`

### 3. Faça suas perguntas
Exemplos de perguntas que você pode fazer:

**Para dados de inadimplência:**
- "Quantos clientes inadimplentes temos?"
- "Qual a distribuição por idade dos inadimplentes?"
- "Qual UF tem mais inadimplência?"
- "Mostre a inadimplência por sexo"
- "Qual a média de idade dos clientes?"

**Para seus próprios dados:**
- "Quantos registros temos na tabela?"
- "Qual a distribuição de [sua_coluna]?"
- "Mostre os top 10 [critério]"
- "Compare [coluna1] com [coluna2]"

## Executando Testes

Execute a suite completa de testes:
```bash
python -m unittest unitest.py
```

Ou execute testes específicos:
```bash
python -m unittest unitest.TestDatabaseChatbot
python -m unittest unitest.TestVisualizationGenerator
```

## Estrutura do Projeto

```
chatsql/
├── chat.py                    # Aplicação principal Streamlit
├── visualization_generator.py # Gerador de visualizações
├── process_table.py          # Processamento e carregamento de dados
├── unitest.py               # Suite de testes
├── .env                     # Variáveis de ambiente (não incluído no repo)
├── requirements.txt         # Dependências (opcional)
└── README.md               # Este arquivo
```

## Segurança

### Proteção contra SQL Injection
O sistema inclui várias camadas de proteção:
- Uso de SQLAlchemy com queries parametrizadas
- Validação de entrada via OpenAI
- Limitação de operações (apenas SELECT)
- Sanitização de queries geradas

## 🚨 Troubleshooting

### Erro de conexão MySQL
```
Error: Can't connect to MySQL server
```
**Solução:**
- Verifique se o MySQL está rodando
- Confirme as credenciais no arquivo `.env`
- Teste a conexão manualmente

### Erro de API OpenAI
```
Error: Invalid API key
```
**Solução:**
- Verifique se a `OPENAI_API_KEY` está correta
- Confirme se há créditos disponíveis na conta OpenAI
- Teste a chave com uma requisição simples

### Problema com dependências
```
ModuleNotFoundError: No module named 'pymysql'
```
**Solução:**
```bash
pip install pymysql
# ou instale todas as dependências novamente
pip install -r requirements.txt
```

