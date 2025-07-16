from pathlib import Path

from script_executor import ExecutorScript


# Recupera a pasta em que o script está sendo executado para que seja utilizado no instacimaneto da classe
DIRETORIO_SCRIPT = Path(__file__).resolve().parent


def main(nome_script: str, nome_funcao: str, parametros: str) -> str:
    """
    Função que executa um determinado script dentro do ambiente virtual utilizando os parâmetros passados

    Args:
        nome_script (str): nome do script que vai ser executado em subprocess
        nome_funcao (str): nome da função a ser executada dentro do script fornecido em `nome_script`
        parametros (str): dicionário serializado (formato de string) de parâmetros que vao ser utilizado na execução em subprocess
    """

    # Instancia classe do script runner, reponsável por executar o script em subprocess
    executor_script = ExecutorScript(
        DIRETORIO_SCRIPT, nome_script, nome_funcao, parametros
    )

    # Executa o script dentro do ambiente virtual
    return executor_script.executar_script()


#main(
#    "executar_acao_site_caixa",
#    "executar_acao",
#   '{"url_site_caixa": "https://conectividadesocialv2.caixa.gov.br/sicns/", "servico": "SALDO", "caminho_arquivo_input": "C:/Users/camila.caldas/Documents/RPA0010/Data/Temp/teste.xlsx", "ambiente_execucao": "DEV", "caminho_arquivo_dados_certificados": "C:/Users/camila.caldas/Documents/RPA0010/Data/Temp/Auxiliar.xlsx", "caminho_service_account":"C:/Users/camila.caldas/Documents/RPA0010/Data/Temp/GSuiteJSONFile.json", "email_usuario":"rpa.q.coe01@stone.com.br", "max_qtd_retry": 2, "max_qtd_falhas_consecutivas": 4, "caminho_relativo_output_scripts": "Data/Temp/OUTPUTS SCRIPTS", "caminho_relativo_relatorio_execucao": "Data/Temp/RELATORIO EXECUCAO SCRIPTS"}',
#)
