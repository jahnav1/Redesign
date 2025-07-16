import logging
import sys
import datetime
from pathlib import Path


class ConfiguradorLog:
    def __init__(self, script_directory: str) -> None:
        """
        Inicializa a classe logger

        Args:
            script_directory: diretório que contém script principal
        """

        self.script_directory = Path(script_directory)
        self.registrador_log = logging.getLogger(__name__)

    def configurar_arquivo_log(self) -> None:
        """
        Configura arquivo de log
        """
        try:
            # Formato da data
            datetime_atual = datetime.datetime.now()
            datetime_str = datetime_atual.strftime("%Y-%m-%d_%H-%M-%S")

            # Caminho para salvar o log (Cria a pasta caso não exista)
            pasta_projeto = self.script_directory.parent
            caminho_pasta_log = pasta_projeto / "Data" / "Temp" / "EVIDENCIAS PYTHON"
            caminho_pasta_log.mkdir(parents=True, exist_ok=True)

            caminho_arquivo_log = (
                caminho_pasta_log / f"EvidencePython_{datetime_str}.log"
            )
            caminho_arquivo_log = caminho_arquivo_log.resolve()

            # Configuração do arquivo de log
            logging.basicConfig(
                filename=caminho_arquivo_log,
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s: %(message)s",
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            msg_erro = f"Erro ao configurar arquivo de log: {e}"
            raise Exception(msg_erro)

    def incluir_info_execucao(self) -> None:
        """
        Inclui no arquivo de log informação sobre qual python está sendo utilizado.
        """
        try:
            # Include information related to python executable
            caminho_executavel_python = sys.executable
            self.registrador_log.info(
                f"Caminho para o executável do python: {caminho_executavel_python}"
            )
        except Exception as e:
            self.registrador_log.error(
                f"Erro ao incluir caminho do executável do python: {e}"
            )


instancia_log = logging.getLogger(__name__)
