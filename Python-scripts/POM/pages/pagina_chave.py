from pathlib import Path

from POM.page_objects.page_objects import Page
from POM.page_objects.page_objects import PageElement
from POM.elementos.elementos_pagina_chave import FormularioChave
from POM.elementos.elementos_pagina_localizacao_trabalhador import LocalizacaoTrabalhadorNome
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from auxiliar import gerar_pdf
from registrador_logs import instancia_log


class PaginaChave(Page, PageElement):
    "Classe que representa a página onde ocorre a geração da chave para saque fgts"

    chave = FormularioChave()
    localizar = LocalizacaoTrabalhadorNome()

    def verificar_existencia_registro_anterior(self, nome_colaborador: str, data_admissao: str, lista_indice_data: list, retorno: str, driver, url_site_caixa) -> list:
        """
        Verifica se já existe um registro anterior de geração de chave para cada ocorrencia do colaborador
        """
        if retorno == "Não localizado":
            registro_anterior_existente = [False]
        else:   
            registro_anterior_existente = self.chave.verificar_registro_anterior(nome_colaborador, data_admissao, lista_indice_data, driver, url_site_caixa ,timeout=5)
        return registro_anterior_existente

    def verificar_validade_registro_existente(
        self,
        data_movimentacao: str,
        codigo_movimentacao: str,
        codigo_saque: str,
        timeout: int,
    ) -> bool:
        """
        Verifica se os dados existentes são válidos com a solicitação realizada

        Args:
        data_movimentação (str): data relacionada a rescisão do colaborador
        codigo_movimentacao (str): código que caracteriza tipo de desligamento
        codigo_saque (str): código que caracteriza o tipo de desligamento
        timeout (int): O tempo máximo de espera para o elemento aparecer
        """

        registro_existente_valido = self.chave.verificar_dados_registro_existente(
            data_movimentacao, codigo_movimentacao, codigo_saque, timeout
        )
        return registro_existente_valido


    def gerar_chave(
            self,
            pasta_armazenamento: Path,
            nome_colaborador: str,
            nome_colaborador_original: str,
            data_movimentacao: str,
            codigo_movimentacao: str,
            codigo_saque: str,
            ambiente_execucao: str,
            registro_anterior_existente: list,
            lista_indice_data: list,
            retorno: str,
        ) -> list:
            """
            Preenche formulário de geração da chave e quando obtem a chave tira print da tela e salva o pdf

            Ags:
                pasta_armazenamento (Path): pasta onde vai ser armazenado o arquivo png com o print da dela e também o arquivo pdf que vai ser gerado a partir da imagem
                nome_colaborador (str): nome do colocaborados para o qual a chave está sendo gerada
                data_movimentação (str): data relacionada a rescisão do colaborador
                codigo_movimentacao (str): código que caracteriza tipo de desligamento
                codigo_saque (str): código que caracteriza o tipo de desligamento
                ambiente_execucao (str): ambiente de execução do script (dev, qa ou prod)
                lista_indice_data (list): lista com os indices de data de cada colaborador
            """
            botao_continuar = (
                By.XPATH,
                "/html/body/form/table[2]/tbody/tr[3]/td[3]/table[3]/tbody/tr[8]/td/a[1]/img",
            )
            botao_retornar = (
                By.CSS_SELECTOR,
                "a[href='javascript:retr_comunicar_movimentacao();']",
            )
            try:
                registro_existente_valido = False
                caminhos_pdf = []
                if retorno == "Não localizado":
                    # Printar a tela de trabalhador não localizado - evita que o script pare de rodar
                    screenshot_name = f"04 - CHAVE FGTS - {nome_colaborador_original.upper()}.png"
                    screenshot_path = pasta_armazenamento / screenshot_name
                    self.chave.gerar_imagem_chave(screenshot_path)
                    caminhos_pdf.append(gerar_pdf(screenshot_path))
                else:    
                    if lista_indice_data:
                        elementos_trabalhador = self.encontrar_ocorrencias_por_nome("rdoTrabalhador")
                        for i in lista_indice_data:
                            try:
                                seletor_trabalhador = (
                                    By.XPATH,
                                    f"{elementos_trabalhador[i]}"
                                )
                                # Selecionar o seletor do trabalhador na posição i
                                instancia_log.info(f"Selecionando trabalhador na posição {i}")
                                self.clicar_botao(seletor_trabalhador)
                                # Clicar em continuar
                                self.clicar_botao(botao_continuar)

                                if registro_anterior_existente[i]:
                                    registro_existente_valido = self.verificar_validade_registro_existente(
                                        data_movimentacao, codigo_movimentacao, codigo_saque, timeout=10
                                    )
                                    instancia_log.info(
                                        f"Registro anterior válido: {registro_existente_valido}"
                                    )
                                if registro_existente_valido or not registro_anterior_existente[i]:
                                    self.chave.preencher_formulario_chave(
                                        data_movimentacao,
                                        codigo_movimentacao,
                                        codigo_saque,
                                        ambiente_execucao,
                                        registro_anterior_existente[i],
                                        timeout=10,
                                    )
                                    screenshot_name = f"04 - CHAVE FGTS - {nome_colaborador_original.upper()} {i+1}.png"
                                    screenshot_path = pasta_armazenamento / screenshot_name
                                    self.chave.gerar_imagem_chave(screenshot_path)
                                    caminhos_pdf.append(gerar_pdf(screenshot_path))
                                

                                self.clicar_botao(botao_retornar, timeout=5) # Clicar no botão de retornar
                                # Preencher formulário de chave novamente
                                self.localizar.preencher_dados_trabalhador(nome_colaborador, timeout=5)
                                
                            

                            except TimeoutException:
                                registro_anterior_existente = False # Caso não exista registro anterior
                                self.clicar_botao(botao_retornar, timeout=5)
                    else:
                        registro_existente_valido = False

                        if registro_anterior_existente[0]:
                            registro_existente_valido = self.verificar_validade_registro_existente(
                                data_movimentacao, codigo_movimentacao, codigo_saque, timeout=10
                            )
                            instancia_log.info(
                                f"Registro anterior válido: {registro_existente_valido}"
                            )

                        if registro_existente_valido or not registro_anterior_existente[0]:
                            self.chave.preencher_formulario_chave(
                                data_movimentacao,
                                codigo_movimentacao,
                                codigo_saque,
                                ambiente_execucao,
                                registro_anterior_existente[0],
                                timeout=10,
                            )

                            screenshot_name = f"04 - CHAVE FGTS - {nome_colaborador_original.upper()}.png"
                            screenshot_path = pasta_armazenamento / screenshot_name
                            instancia_log.info(f"Gerando imagem da chave no caminho: {screenshot_path}")
                            self.chave.gerar_imagem_chave(screenshot_path)
                            caminhos_pdf.append(gerar_pdf(screenshot_path))
                        return caminhos_pdf
                        # else:
                        #     raise Exception
                return caminhos_pdf
            except:
                etapa = "geração da chave"
                msg_erro = f"Erro não previsto na etapa de: {etapa}"
                raise Exception(msg_erro)