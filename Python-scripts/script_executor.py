import subprocess
import os


class ExecutorScript:
    def __init__(
        self,
        diretorio_script: str,
        nome_script: str,
        nome_funcao: str,
        parametros: str,
    ) -> None:
        """
        Inicializa a classe ScriptRunner

        Args:
            diretorio_script (str): diretorio do script executado
            nome_script (str): nome do script que vai ser executado em subprocess
            nome_funcao (str): nome da função a ser executada dentro do script fornecido em `nome_script`
            parametros (str): dicionário serializado (formato de string) de parâmetros que vao ser utilizado na execução em subprocess
        """

        self.diretorio_script = diretorio_script
        self.nome_script = nome_script
        self.nome_funcao = nome_funcao
        self.parametros = parametros

        # Checa e configura POETRY_VIRTUALENVS_IN_PROJECT
        self.configura_criacao_ambiente_virtual_no_projeto()

    def configura_criacao_ambiente_virtual_no_projeto(self) -> None:
        """
        Configura variável de ambiente que garante que o ambiente virtual vai ser criado na pasta do projeto
        """
        env_variable = os.getenv("POETRY_VIRTUALENVS_IN_PROJECT")
        if env_variable is None or env_variable.lower() == "false":
            os.environ["POETRY_VIRTUALENVS_IN_PROJECT"] = "true"

    def criar_comando_python(self) -> list[str]:
        """
        Cria comando (no formato de lista) para executar script python usando o subprocess.
        """

        chamada_funcao = f"from {self.nome_script} import {self.nome_funcao}; {self.nome_funcao}({self.parametros});"
        comando = [
            "poetry",
            "run",
            "python",
            "-c",
            chamada_funcao,
        ]
        return comando

    def executar_script(self) -> str:
        """
        Ativa ambiente virtual, executa script e desativa ambiente virtual
        """

        try:
            # Ambiente virtual vai ser criado na mesma pasta em que os scripts estão localizados
            caminho_ambiente_virtual = self.diretorio_script

            # Instala dependências listadas no arquivo pyproject.toml, cria e ativa o ambiente virtual
            subprocess.run(["poetry", "install"], cwd=caminho_ambiente_virtual)

            # Cria comando para executar script
            comando_para_executar_script = self.criar_comando_python()

            # Executa script e salva output
            with open("output.txt", "w+") as arquivo_output:
                subprocess.run(
                    comando_para_executar_script,
                    cwd=caminho_ambiente_virtual,
                    stdout=arquivo_output,
                    text=True,
                    check=True,
                )

                # Recupera o retorno do arquivo output.txt
                arquivo_output.seek(0)
                output = arquivo_output.read()

            return output

        except FileNotFoundError as e:
            return f"Algum arquivo/pasta necessário para a execução não foi encontrado: {e}"

        except subprocess.CalledProcessError as e:
            return f"Erro ao executar o script: {e}"

        except Exception as e:
            return f"Um erro não previsto aconteceu ao executar o script: {e}"
