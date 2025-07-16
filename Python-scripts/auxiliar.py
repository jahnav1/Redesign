from fpdf import FPDF
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import hashlib
import pandas as pd
import datetime
import traceback
from openpyxl import Workbook

from registrador_logs import instancia_log


ESCOPO_DRIVE = ["https://www.googleapis.com/auth/drive"]


def gerar_pdf(caminho_imagem: Path) -> str:
    """
    Gera arquivo no formato PDF a partir de print da tela

    Args:
        caminho_imagem (Path): caminho da imagem no formato png que vai ser utilizada para montar o pdf
    """
    if not caminho_imagem.exists():
        raise FileNotFoundError(
            f"Erro não previsto na etapa de geração do pdf: a imagem não foi encontrada no caminho sugerido: {caminho_imagem}"
        )

    pdf = FPDF()
    pdf.add_page()
    pdf.image(str(caminho_imagem), w=190)
    caminho_pdf = caminho_imagem.with_suffix(".pdf")
    pdf.output(caminho_pdf, "F")

    return str(caminho_pdf)


def instanciar_drive() -> webdriver:
    """
    Cria instancia do webdriver para se comunicar com o browser

    """

    # Configura as opçoes de abertura do drive
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--ignore-certificate-errors")

    tentativas = 0
    max_tentativas = 3

    while tentativas < max_tentativas:
        try:
            # Cria instancia do driver
            service = ChromeService(
                ChromeDriverManager().install()
            )
            
            driver = webdriver.Chrome(service=service, options=chrome_options)

            instancia_log.info(f"O driver foi instanciado na tentativa: {tentativas}")

            return driver
        
        except (WebDriverException, SystemExit, KeyboardInterrupt):
            tentativas +=1
            msg_erro = f"Tentativa {tentativas}/{max_tentativas}  de instanciar o drive falhou: {traceback.format_exc()}"
            instancia_log.error(msg_erro)
    raise


def gerar_chave_md5(caminho_arquivo: Path) -> str:
    """
    Geração da chave de criptografia MD5

    Args:
        caminho_arquivo (Path): caminho local do arquivo que vai ser utilizado para a geração da chave md5

    """
    if not caminho_arquivo.exists():
        raise FileNotFoundError(
            f"Erro não previsto na geração de chave MD5: a imagem não foi encontrada no caminho sugerido: {caminho_arquivo}"
        )

    md5 = hashlib.md5()
    with open(caminho_arquivo, "rb") as arquivo:
        conteudo = arquivo.read()
        md5.update(conteudo)
    chave_md5 = md5.hexdigest()

    return chave_md5


def upload_arquivo_drive(
    caminho_arquivo_a_ser_inserido: str,
    caminho_service_account: str,
    id_pasta: str,
    email_usuario: str,
) -> str:
    """
    Geração da chave de criptografia MD5 e upload do arquivo no drive

    Args:
        caminho_arquivo_a_ser_inserido (str): caminho local do arquivo que vai ser inserido no drive
        caminho_service_account (str): caminho local da service account que vai ser utilizada para autenticação na api do google drive
        id_pasta (str): id da pasta do google drive na qual o arquivo vai ser adicionado
        email_usuario (str): email do usuário em nome do qual vai ser feito o upload do arquivo
    """
    try:
        # Transformar caminho do formato str para Path
        caminho_arquivo_path = Path(caminho_arquivo_a_ser_inserido)

        # Gerar chave md5 antes de inserir o arquivo
        chave_md5 = gerar_chave_md5(caminho_arquivo_path)

        # Recuperar as credenciais de serviço autenticadas usando o arquivo JSON fornecido
        credenciais = service_account.Credentials.from_service_account_file(
            caminho_service_account, scopes=ESCOPO_DRIVE
        )

        # Personaliza o email que vai ser responsável pela inclusão do email
        delegated_credentials = credenciais.with_subject(email_usuario)

        # Cria instancia do serviço Google Drive  com as credenciais fornecidas utilizando a 3 versão da api do google drive
        service = build("drive", "v3", credentials=delegated_credentials)

        # Verifica se a pasta do drive está disponível
        service.files().get(fileId=id_pasta, fields="id, name").execute()
        instancia_log.info("Pasta para adicionar arquivo encontrada")

        # Configura os metadados do arquivo a ser inserido
        file_metadata = {
            "name": Path(caminho_arquivo_a_ser_inserido).name,
            "parents": [id_pasta],
        }

        media = MediaFileUpload(caminho_arquivo_a_ser_inserido)

        # Cria um objeto de serviço do drive com os metadados indicados para enviar o arquivo especificado para o drive
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, supportsAllDrives=True)
            .execute()
        )

        file_id = file["id"]
        link_arquivo_inserido = "https://drive.google.com/file/d/" + file_id

        return f"Arquivo output:{link_arquivo_inserido} | Chave para validação: {chave_md5}"

    except HttpError as e:
        if e.resp.status == 404:
            instancia_log.error(f"Pasta do drive com id {id_pasta} não foi encontrada")
            raise Exception(
                f"Erro não previsto: pasta do drive com id {id_pasta} não foi encontrada"
            )
        else:
            instancia_log.error(
                f"Erro não previsto do tipo Http ao utilizar a api do drive"
            )
            raise Exception(
                f"Erro não previsto do tipo Http ao utilizar a api do drive"
            )
    except Exception as e:
        instancia_log.error(f"Erro não previsto ao fazer o upload no drive: {str(e)}")
        raise Exception(f"Erro não previsto ao fazer o upload no drive: {str(e)}")


def escrever_no_excel(
    dataframe_para_ser_escrito: pd.DataFrame,
    colunas_para_excluir: list,
    nome_arquivo_excel: str,
    pasta_armazenamento: Path,
) -> Path:
    """
    Faz algumas manipulações (filtro de colunas) no dataframe e escreve dataframe no arquivo excel

    Args:
        dataframe_para_ser_escrito (pd.DataFrame): dataframe que contém os dados a serem escritos no excel
        colunas_para_excluir (list): lista de colunas que não precisam ser escritas no excel e precisam ser deletadas
        nome_arquivo_excel (str): nome do arquivo excel que vai ser criado
        pasta_armazenamento (Path): pasta onde o arquivo excel criado vai ser adicionado
    """
    try:
        if dataframe_para_ser_escrito.empty:
            instancia_log.error("Dataframe para ser escrito está vazio")
            raise ValueError("DataFrame está vazio")

        # Exclui colunas que não são necessárias
        dataframe_para_ser_escrito = dataframe_para_ser_escrito.drop(
            colunas_para_excluir, axis=1
        )

        # Define nome e local onde vai ser armazenado o excel
        nome_planilha = f"{nome_arquivo_excel}_{datetime.datetime.now().strftime('%d%b%Y-%H.%M')}.xlsx"
        caminho_local_planilha = pasta_armazenamento / nome_planilha

        # Cria o arquivo excel que vai ser preenchido
        wb = Workbook()
        wb.save(caminho_local_planilha)

        # Verifica se o caminho da planilha é um diretório válido e pode ser escrito
        if (
            not caminho_local_planilha.parent.is_dir()
            or not caminho_local_planilha.is_file()
        ):
            instancia_log.error(
                f"O diretório {caminho_local_planilha.parent} não é um diretório válido ou não pode ser escrito."
            )
            raise IOError(
                f"O diretório {caminho_local_planilha.parent} não é um diretório válido ou não pode ser escrito."
            )

        # Escreve relatório no excel
        dataframe_para_ser_escrito.to_excel(caminho_local_planilha, index=False)

        return caminho_local_planilha

    except ValueError as e:
        raise Exception(f"Erro ao excrever relatório do excel: {e}")
    except IOError as e:
        raise Exception(
            f"O diretório {caminho_local_planilha.parent} não é um diretório válido ou não pode ser escrito: {e}"
        )
    except Exception as e:
        msg = f"Erro ao escrever relatório do excel: {e}"
        raise Exception(msg)


def incluir_info_certificado(
    dados_para_processar: pd.DataFrame, dados_certificado: pd.DataFrame
) -> pd.DataFrame:
    """
    Adiciona dados dos certificados no dataframe de dados para processar

    Args:
        dados_para_processar (pd.DataFrame): dataframe que contém os dados de input da área
        dados_certificado (pd.DataFrame): dataframe que contém os dados relacionados aos certificados
    """

    try:
        # Checa se a coluna "Empresa" existe em ambos os dataframes  antes de fazer o merge
        if "EMPRESA" not in dados_para_processar.columns:
            instancia_log.error("Coluna empresa não está presente no input da área")
            raise ValueError("Column 'EMPRESA' not found in 'dados_para_processar'")
        if "EMPRESA" not in dados_certificado.columns:
            instancia_log.error(
                "Coluna empresa não está presente nas informações do certificado"
            )
            raise ValueError("Column 'EMPRESA' not found in 'dados_certificado'")

        # Faz a combinação dos dados dos 2 dataframes (input e com informações de certificado)
        dados_combinados = pd.merge(
            dados_para_processar, dados_certificado, on="EMPRESA", how="left"
        )

        # Remove colunas que não vão ser necessárias
        dados_combinados = dados_combinados.drop(
            ["CAMINHO DO CERTIFICADO", "NOME DO CERTIFICADO"], axis=1
        )

        # Ordena os certificados para manter as mesmas empresas juntas
        dados_combinados = dados_combinados.sort_values(
            by="POSICAO DO CERTIFICADO", ascending=True
        )

        return dados_combinados

    except ValueError as e:
        raise Exception(
            f"Erro ao realizar o merge dos dataframes, verificar se a coluna chave Empresa está presente em ambos: {e}"
        )
    except Exception as e:
        raise Exception(
            f"Erro ao fazer ao combinar dados de input da área com dados dos certificados: {e}"
        )

