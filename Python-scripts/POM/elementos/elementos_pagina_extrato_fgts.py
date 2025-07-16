from selenium.webdriver.common.by import By
from POM.page_objects.page_objects import PageElement
from selenium.common.exceptions import  NoSuchElementException # Adicionando a importação do NoSuchElementException
from pathlib import Path
from auxiliar import gerar_pdf
from registrador_logs import instancia_log


class ExtratoFgts(PageElement):
    """
    Classe que representa o extrato fgts
    """

    informacao_saldo_fgts = (
        By.XPATH,
        "/html/body/form/table[2]/tbody/tr[2]/td[3]/table[3]/tbody/tr[2]/td/table[1]/tbody/tr[19]/td[2]"
    )

    nao_localizado = (
        By.XPATH,
        "/html/body/form/table[2]/tbody/tr[2]/td[3]/table[3]/tbody/tr[2]/td/b"
    )

    botao_continuar = (
        By.XPATH,
        "/html/body/form/table[2]/tbody/tr[3]/td[3]/table[3]/tbody/tr[8]/td/a[1]/img",   
    )

    botao_retornar = (
        By.CSS_SELECTOR,
        "a[href='javascript:retr_solicitar_extrato_fgts();']",
    )

    def recuperar_informacao_saldo(self, lista_indice_data: list, timeout: int) -> list:
        """
        Recupera o saldo fgts do extrato (campo valor base) para todos os índices fornecidos.

        Args:
            lista_indice_data (list): Lista de índices de data.
            timeout (int): Tempo de timeout utilizado na interação com elementos da tela.

        Returns:
            list: Lista contendo os saldos FGTS correspondentes aos índices fornecidos.
        """
        instancia_log.info(f"Lista de índices de data: {lista_indice_data}")
        saldos_fgts = []  # Lista para armazenar os saldos FGTS
        if lista_indice_data:
            instancia_log.info("Lista de índices de data não está vazia")
            elementos_trabalhador = self.encontrar_ocorrencias_por_nome("rdoTrabalhador")
            instancia_log.info(f"Elementos trabalhador: {elementos_trabalhador}")
            for i in lista_indice_data:  # Para cada índice na lista de índices de data
                try:
                    seletor_trabalhador = (
                        By.XPATH,
                        f"{elementos_trabalhador[i]}"
                    )
                    instancia_log.info("XPATH do trabalhador: %s", seletor_trabalhador)
                    # Selecionar o seletor do trabalhador na posição i
                    instancia_log.info(f"Selecionando trabalhador na posição {i}")
                    self.clicar_botao(seletor_trabalhador, timeout)
                    # CLICAR EM CONTINUAR E FAZER O RESTO
                    self.clicar_botao(self.botao_continuar, timeout)
                    info_saldo = self.recuperar_texto_do_elemento(self.informacao_saldo_fgts, timeout)
                    saldos_fgts.append(info_saldo)  # Adicionar o saldo à lista
                    self.clicar_botao(self.botao_retornar, timeout)
                except IndexError:
                    # Se o índice estiver fora do alcance, imprima uma mensagem de erro e continue para o próximo índice
                    instancia_log.error(f"Índice {i} está fora do alcance")
                    continue
                except NoSuchElementException:
                    # Se não for possível clicar no elemento, imprima uma mensagem de erro e continue para o próximo índice
                    instancia_log.error(f"Elemento não encontrado para o índice {i}")
                    continue
        else:
            info_saldo = self.recuperar_texto_do_elemento(self.informacao_saldo_fgts, timeout)
            instancia_log.info(f"Info saldo: {info_saldo}")
            saldos_fgts.append(info_saldo)  # Adicionar o saldo à lista
        return saldos_fgts  # Retornar a lista de saldos FGTS



    def gerar_imagem_extrato_fgts(self, screenshot_path: Path, lista_indice_data: list, pasta_armazenamento: Path, nome_colaborador: str, nome_colaborador_original: str, timeout: int) -> None:
        """
        Tira o print da tela e salva no formato de imagem

        Ags:
            screenshot_path (Path): caminho onde vai ser armazenado o print tirado da tela
            lista_indice_data (list): Lista de índices de data.
        """
        instancia_log.info(f"Lista de índices de data: {lista_indice_data}")
        lista_caminhos_arquivos_pdf = []  # Lista para armazenar os caminhos dos arquivos PDF gerados
        if lista_indice_data:
            elementos_trabalhador = self.encontrar_ocorrencias_por_nome("rdoTrabalhador")
            for i in lista_indice_data:
                try:
                    seletor_trabalhador = (
                        By.XPATH,
                        f"{elementos_trabalhador[i]}"
                    )
                    instancia_log.info("XPATH do trabalhador: %s", seletor_trabalhador)
                    # Selecionar o seletor do trabalhador na posição i
                    instancia_log.info(f"Selecionando trabalhador na posição {i}")
                    self.clicar_botao(seletor_trabalhador, timeout)
                    instancia_log.info("Vai clicar em continuar")

                    # Clicar em continuar e fazer o resto
                    self.clicar_botao(self.botao_continuar, timeout)
                    screenshot_name = f"03 - EXTRATO FGTS - {nome_colaborador_original.upper()} {i+1}.png"
                    screenshot_path = pasta_armazenamento / screenshot_name
                    instancia_log.info(f"Caminho do arquivo de imagem: {screenshot_path}")
                    self.tirar_print_tela(screenshot_path)  # Tirar o print da tela
                    self.clicar_botao(self.botao_retornar, timeout)
                    caminho_arquivo_pdf_gerado = gerar_pdf(screenshot_path)
                    lista_caminhos_arquivos_pdf.append(caminho_arquivo_pdf_gerado)

                except IndexError:
                    # Se o índice estiver fora do alcance, imprima uma mensagem de erro e continue para o próximo índice
                    instancia_log.error(f"Índice {i} está fora do alcance")
                    continue
                except NoSuchElementException:
                    # Se não for possível clicar no elemento, imprima uma mensagem de erro e continue para o próximo índice
                    instancia_log.error(f"Elemento não encontrado para o índice {i}")
                    continue
        else:
            screenshot_name = f"03 - EXTRATO FGTS - {nome_colaborador_original.upper()}.png"
            screenshot_path = pasta_armazenamento / screenshot_name
            instancia_log.info(f"Caminho do arquivo de imagem: {screenshot_path}")
            self.tirar_print_tela(screenshot_path)
            caminho_arquivo_pdf_gerado = gerar_pdf(screenshot_path)
            lista_caminhos_arquivos_pdf.append(caminho_arquivo_pdf_gerado)
            
        instancia_log.info(lista_caminhos_arquivos_pdf)       
        return lista_caminhos_arquivos_pdf



