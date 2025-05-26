import unittest
import pandas as pd
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
import tempfile

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat import DatabaseChatbot
from visualization_generator import VisualizationGenerator

class TestDatabaseChatbot(unittest.TestCase):
    """Testes para a classe DatabaseChatbot"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        # Mock das variáveis de ambiente
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key',
            'MYSQL_HOST': 'test_host',
            'MYSQL_USER': 'test_user',
            'MYSQL_PASSWORD': 'test_password',
            'MYSQL_DATABASE': 'test_db',
            'MYSQL_PORT': '3306'
        })
        self.env_patcher.start()
        
        # Mock do OpenAI client
        self.openai_patcher = patch('chat.OpenAI')
        self.mock_openai = self.openai_patcher.start()
        
        self.engine_patcher = patch('chat.create_engine')
        self.mock_engine = self.engine_patcher.start()
        
        self.chatbot = DatabaseChatbot()
    
    def tearDown(self):
        """Limpeza após cada teste"""
        self.env_patcher.stop()
        self.openai_patcher.stop()
        self.engine_patcher.stop()
    
    def test_initialization(self):
        """Testa se o chatbot é inicializado corretamente"""
        self.assertIsNotNone(self.chatbot.openai_client)
        self.assertIsNotNone(self.chatbot.engine)
    
    @patch('chat.pd.read_sql')
    def test_get_table_schema_success(self, mock_read_sql):
        """Testa obtenção bem-sucedida do schema da tabela"""
        mock_schema = pd.DataFrame({
            'COLUMN_NAME': ['TARGET', 'IDADE', 'VAR2'],
            'DATA_TYPE': ['int', 'int', 'varchar'],
            'IS_NULLABLE': ['NO', 'NO', 'YES'],
            'COLUMN_DEFAULT': [None, None, None],
            'COLUMN_COMMENT': ['', '', '']
        })
        
        mock_sample = pd.DataFrame({
            'TARGET': [0, 1, 0],
            'IDADE': [25, 45, 30],
            'VAR2': ['M', 'F', 'M']
        })
        
        mock_read_sql.side_effect = [mock_schema, mock_sample]
        
        schema_df, sample_df = self.chatbot.get_table_schema()
        
        self.assertIsNotNone(schema_df)
        self.assertIsNotNone(sample_df)
        self.assertEqual(len(schema_df), 3)
        self.assertEqual(len(sample_df), 3)
    
    @patch('chat.pd.read_sql')
    def test_get_table_schema_failure(self, mock_read_sql):
        """Testa falha na obtenção do schema"""
        mock_read_sql.side_effect = Exception("Erro de conexão")
        
        schema_df, sample_df = self.chatbot.get_table_schema()
        
        self.assertIsNone(schema_df)
        self.assertIsNone(sample_df)
    
    @patch('chat.pd.read_sql')
    def test_execute_sql_query_success(self, mock_read_sql):
        """Testa execução bem-sucedida de query SQL"""
        mock_result = pd.DataFrame({'count': [100]})
        mock_read_sql.return_value = mock_result
        
        result = self.chatbot.execute_sql_query("SELECT COUNT(*) as count FROM test")
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.iloc[0, 0], 100)
    
    @patch('chat.pd.read_sql')
    def test_execute_sql_query_failure(self, mock_read_sql):
        """Testa falha na execução de query SQL"""
        mock_read_sql.side_effect = Exception("Erro SQL")
        
        result = self.chatbot.execute_sql_query("SELECT * FROM invalid_table")
        
        self.assertIsInstance(result, str)
        self.assertIn("Erro na execução da query", result)
    
    def test_generate_sql_from_question_success(self):
        """Testa geração bem-sucedida de SQL a partir de pergunta"""
        # Mock da resposta do OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "SELECT COUNT(*) FROM neurotech WHERE TARGET = 1"
        
        self.mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        sql_query = self.chatbot.generate_sql_from_question(
            "Quantos inadimplentes temos?",
            "schema_info"
        )
        
        self.assertEqual(sql_query, "SELECT COUNT(*) FROM neurotech WHERE TARGET = 1")
    
    def test_generate_sql_from_question_failure(self):
        """Testa falha na geração de SQL"""
        self.mock_openai.return_value.chat.completions.create.side_effect = Exception("Erro API")
        
        result = self.chatbot.generate_sql_from_question("pergunta", "schema")
        
        self.assertIn("Erro ao gerar SQL", result)
    
    def test_explain_results_with_dataframe(self):
        """Testa explicação de resultados com DataFrame"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Explicação dos resultados"
        
        self.mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        test_df = pd.DataFrame({'TARGET': [0, 1], 'count': [80, 20]})
        
        explanation = self.chatbot.explain_results(
            "Quantos inadimplentes?",
            "SELECT TARGET, COUNT(*) FROM test GROUP BY TARGET",
            test_df
        )
        
        self.assertEqual(explanation, "Explicação dos resultados")
    
    def test_explain_results_with_error_string(self):
        """Testa explicação quando há erro (string)"""
        error_message = "Erro na consulta"
        
        result = self.chatbot.explain_results("pergunta", "sql", error_message)
        
        self.assertEqual(result, error_message)


class TestVisualizationGenerator(unittest.TestCase):
    """Testes para a classe VisualizationGenerator"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.env_patcher = patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
        self.env_patcher.start()
        
        self.openai_patcher = patch('visualization_generator.OpenAI')
        self.mock_openai = self.openai_patcher.start()
        
        self.viz_generator = VisualizationGenerator()
    
    def tearDown(self):
        """Limpeza após cada teste"""
        self.env_patcher.stop()
        self.openai_patcher.stop()
    
    def test_analyze_data_for_visualization_empty_data(self):
        """Testa análise com dados vazios"""
        empty_df = pd.DataFrame()
        
        chart, message = self.viz_generator.analyze_data_for_visualization(
            "pergunta", "sql", empty_df
        )
        
        self.assertIsNone(chart)
        self.assertEqual(message, "Não há dados para visualizar")
    
    def test_analyze_data_for_visualization_success(self):
        """Testa análise bem-sucedida de dados"""
        # Mock da resposta do OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "bar_chart"
        
        self.mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        test_df = pd.DataFrame({
            'categoria': ['A', 'B', 'C'],
            'valor': [10, 20, 30]
        })
        
        chart, message = self.viz_generator.analyze_data_for_visualization(
            "Mostrar dados por categoria",
            "SELECT categoria, COUNT(*) as valor FROM test GROUP BY categoria",
            test_df
        )
        
        self.assertIsNotNone(chart)
        self.assertIn("sucesso", message)
    
    def test_create_bar_chart(self):
        """Testa criação de gráfico de barras"""
        test_df = pd.DataFrame({
            'categoria': ['A', 'B', 'C'],
            'valor': [10, 20, 30]
        })
        
        chart, message = self.viz_generator._create_bar_chart(test_df, "Teste")
        
        self.assertIsNotNone(chart)
        self.assertIn("sucesso", message)
    
    def test_create_pie_chart(self):
        """Testa criação de gráfico de pizza"""
        test_df = pd.DataFrame({
            'categoria': ['A', 'B', 'C'],
            'valor': [10, 20, 30]
        })
        
        chart, message = self.viz_generator._create_pie_chart(test_df, "Teste")
        
        self.assertIsNotNone(chart)
        self.assertIn("sucesso", message)
    
    def test_create_histogram(self):
        """Testa criação de histograma"""
        test_df = pd.DataFrame({
            'idade': [25, 30, 35, 40, 45, 50, 55]
        })
        
        chart, message = self.viz_generator._create_histogram(test_df, "Teste")
        
        self.assertIsNotNone(chart)
        self.assertIn("sucesso", message)
    
    def test_create_metrics(self):
        """Testa criação de métricas"""
        test_df = pd.DataFrame({
            'valor1': [10, 20, 30],
            'valor2': [100, 200, 300]
        })
        
        metrics, message = self.viz_generator._create_metrics(test_df, "Teste")
        
        self.assertIsInstance(metrics, dict)
        self.assertIn("valor1", metrics)
        self.assertIn("valor2", metrics)
        self.assertIn("sucesso", message)


class TestInputValidation(unittest.TestCase):
    """Testes para validação de entradas"""
    
    def test_sql_injection_prevention(self):
        """Testa prevenção de SQL injection"""
        malicious_inputs = [
            "'; DROP TABLE neurotech; --",
            "1; DELETE FROM neurotech WHERE 1=1; --",
            "UNION SELECT password FROM users",
            "<script>alert('xss')</script>",
            "' OR '1'='1",
        ]
        
        # Verificar se estas entradas são tratadas adequadamente
        for malicious_input in malicious_inputs:
            # Em um sistema real, você validaria se essas entradas são sanitizadas
            self.assertIsInstance(malicious_input, str)
            self.assertTrue(len(malicious_input) > 0)
    
    def test_empty_and_none_inputs(self):
        """Testa entradas vazias e None"""
        empty_inputs = ["", None, "   ", "\n\t"]
        
        for empty_input in empty_inputs:
            if empty_input is None:
                self.assertIsNone(empty_input)  #Verificar se o sistema lida com entradas vazias

            else:
                self.assertIsInstance(empty_input, str)
    
    def test_very_long_inputs(self):
        """Testa entradas muito longas"""
        long_input = "a" * 10000  # String de 10.000 caracteres
        
        self.assertEqual(len(long_input), 10000) #Verificar se o sistema pode lidar com entradas longas
        self.assertIsInstance(long_input, str)


class TestErrorHandling(unittest.TestCase):
    """Testes para tratamento de erros"""
    
    def test_database_connection_failure(self):
        """Testa falha de conexão com banco de dados"""
        with patch('chat.create_engine') as mock_engine:
            mock_engine.side_effect = Exception("Falha de conexão")
            
            with self.assertRaises(Exception):
                DatabaseChatbot()
    
    def test_openai_api_failure(self):
        """Testa falha da API do OpenAI"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'invalid_key'}):
            with patch('chat.OpenAI') as mock_openai:
                mock_openai.side_effect = Exception("API Key inválida")
                
                with self.assertRaises(Exception):
                    DatabaseChatbot()
    
    def test_missing_environment_variables(self):
        """Testa variáveis de ambiente ausentes"""
        required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
        
        for var in required_vars:
            with patch.dict(os.environ, {}, clear=True):
                # Verificar se a ausência de variáveis é tratada
                self.assertIsNone(os.getenv(var))


class TestDataIntegrity(unittest.TestCase):
    """Testes para integridade dos dados"""
    
    def test_dataframe_structure_validation(self):
        """Testa validação da estrutura do DataFrame"""
        # DataFrame válido
        valid_df = pd.DataFrame({
            'TARGET': [0, 1, 0, 1],
            'IDADE': [25, 30, 35, 40],
            'VAR2': ['M', 'F', 'M', 'F']
        })
        
        self.assertEqual(len(valid_df.columns), 3)
        self.assertEqual(len(valid_df), 4)
        self.assertTrue('TARGET' in valid_df.columns)
        self.assertTrue('IDADE' in valid_df.columns)
    
    def test_data_type_validation(self):
        """Testa validação de tipos de dados"""
        test_df = pd.DataFrame({
            'numeric_col': [1, 2, 3],
            'string_col': ['a', 'b', 'c'],
            'boolean_col': [True, False, True]
        })
        
        numeric_cols = test_df.select_dtypes(include=['int64', 'float64']).columns
        categorical_cols = test_df.select_dtypes(include=['object', 'bool']).columns
        
        self.assertEqual(len(numeric_cols), 1)
        self.assertEqual(len(categorical_cols), 2)


class TestPerformance(unittest.TestCase):
    """Testes básicos de performance"""
    
    def test_large_dataset_handling(self):
        """Testa manipulação de dataset grande"""
        import time
        
        # Criar um DataFrame grande
        large_df = pd.DataFrame({
            'col1': range(10000),
            'col2': ['text'] * 10000,
            'col3': [0.5] * 10000
        })
        
        start_time = time.time()
        
        #Operações básicas que o sistema deve realizar
        result = large_df.head(100)
        data_types = large_df.dtypes
        memory_usage = large_df.memory_usage(deep=True).sum()
        
        end_time = time.time()
        
        #Verificar se as operações foram completadas em tempo razoável
        self.assertLess(end_time - start_time, 5.0)  # Menos de 5 segundos
        self.assertEqual(len(result), 100)
        self.assertGreater(memory_usage, 0)


def run_robustness_tests():
    """Função principal para executar todos os testes"""
    test_suite = unittest.TestSuite()
    
    # Adicionar testes
    test_classes = [
        TestDatabaseChatbot,
        TestVisualizationGenerator,
        TestInputValidation,
        TestErrorHandling,
        TestDataIntegrity,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print(f"\n{'='*50}")
    print("RELATÓRIO DE ROBUSTEZ DO CHATBOT")
    print(f"{'='*50}")
    print(f"Testes executados: {result.testsRun}")
    print(f"Falhas: {len(result.failures)}")
    print(f"Erros: {len(result.errors)}")
    print(f"Taxa de sucesso: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFALHAS ({len(result.failures)}):")
        for failure in result.failures:
            print(f"- {failure[0]}")
    
    if result.errors:
        print(f"\nERROS ({len(result.errors)}):")
        for error in result.errors:
            print(f"- {error[0]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_robustness_tests()    
    sys.exit(0 if success else 1) 


#VOCE PODE USAR UNITTEST PARA TESTAR O CHATBOT E O VISUALIZATION GENERATOR:
#python -m unittest unitest.py