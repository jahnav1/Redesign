from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from POM.pages.pagina_localizacao_trabalhador import PaginaLocalizacaoTrabalhador
from POM.page_objects.page_objects import PageElement
from registrador_logs import instancia_log
from POM.elementos.elementos_pagina_localizacao_trabalhador import LocalizacaoTrabalhadorNome

class FormularioChave(PageElement):
    """
    Classe que representa um formulário específico para geração de chave
    """
    localizar = LocalizacaoTrabalhadorNome()

    msg_registro_anterior = (
        By.XPATH,
        "/html[1]/body[1]/form[1]/table[2]/tbody[1]/tr[2]/td[3]/table[4]/tbody[1]/tr[1]/td[1]/table[3]/tbody[1]/tr[1]/td[1]",
    )
    campo_preenchimento_data_movimentacao = (By.NAME, "txtDtMovimentacao")
    lista_codigo_movimentacao = (By.NAME, "sltCodMovimentacao")
    lista_codigo_saque = (By.NAME, "sltSaque")
    campo_preenchimento_pensao_alimenticia = (By.NAME, "txtPensao")
    botao_consignado = (
        By.XPATH,
        "/html/body/form/table[2]/tbody/tr[1]/td[3]/table/tbody/tr/td/span[2]",
    )
    botao_continuar = (By.NAME, "subCont")

    botao_continuar1 = (
        By.XPATH,
        "/html/body/form/table[2]/tbody/tr[3]/td[3]/table[3]/tbody/tr[8]/td/a[1]/img",
    )

    opcao_nao_msg_trabalhador_sem_celular = (
        By.XPATH,
        "/html/body/form/table[2]/tbody/tr[2]/td[3]/table[4]/tbody/tr/td/div/a[2]/img",
    )
    checkbox_aviso_trabalhador = (By.NAME, "chkAvisoTrabalhador")

    botao_retornar = (
        By.CSS_SELECTOR,
        "a[href='javascript:retr_comunicar_movimentacao();']",
    )

    def verificar_registro_anterior(self, nome_colaborador: str, lista_indice_data: list, driver, url_site_caixa, timeout: int) -> list:
        """
        Verificar se já existe registro anterior no formulário da chave

        Args:
            timeout (int): O tempo máximo de espera para o elemento aparecer.

        Returns:
            lista: Lista com True se o registro anterior existir, False caso contrário.
        """
        paginalocalizacao = PaginaLocalizacaoTrabalhador(driver, url_site_caixa)
        lista_registro_ja_existente = []
        if lista_indice_data:
            elementos_trabalhador = self.encontrar_ocorrencias_por_nome("rdoTrabalhador")
            instancia_log.info(f"Elementos trabalhador: {elementos_trabalhador}")
            for indice in lista_indice_data:
                try:
                    seletor_trabalhador = (
                        By.XPATH,
                        f"{elementos_trabalhador[indice]}"
                    )
                    # Selecionar o seletor do trabalhador na posição i
                    instancia_log.info(f"Selecionando trabalhador na posição {indice}")
                    self.clicar_botao(seletor_trabalhador, timeout)
                    # Clicar em continuar
                    self.clicar_botao(self.botao_continuar1, timeout)
                    # Verificar se o registro anterior existe
                    self.aguarda_elemento_aparecer(
                        self.msg_registro_anterior, timeout
                    )
                    lista_registro_ja_existente.append(True) # Caso exista registro anterior adiciona True na lista

                    self.clicar_botao(self.botao_retornar, timeout) # Clicar no botão de retornar
                    # Preencher novamente os dados do trabalhador
                    paginalocalizacao.localizar_sem_verificar(nome_colaborador)

                except TimeoutException:
                    lista_registro_ja_existente.append(False)
                    self.clicar_botao(self.botao_retornar, timeout) # Clicar no botão de retornar
        else:
            try:
                self.aguarda_elemento_aparecer(self.msg_registro_anterior, timeout)
                lista_registro_ja_existente.append(True)
            except TimeoutException:
                lista_registro_ja_existente.append(False)

        return lista_registro_ja_existente

    def verificar_dados_registro_existente(
        self,
        data_movimentacao: str,
        codigo_movimentacao: str,
        codigo_saque: str,
        timeout: int,
    ) -> bool:
        """
        Verifica se os dados preenchidos no formulário da chave são iguais aos dados solicitados

        Args:
            timeout (int): O tempo máximo de espera para o elemento aparecer.
            data_movimentacao (dict): data relacionada ao processo recisório
            codigo_movimentacao (str): código relacionado ao tipo de recisão
            codigo_saque (str): codigo relacionado ao tipo de recisão
            timeout (int): O tempo máximo de espera para o elemento aparecer.

        Returns:
            bool: True se o registro anterior existente é válido, False caso contrário.

        """

        valor_preenchido_data_movimentacao_valido = (
            self.extrair_valor_do_elemento(
                self.campo_preenchimento_data_movimentacao, timeout
            )
            == data_movimentacao
        )


        valor_preenchido_codigo_movimentacao_valido = (
            self.extrair_valor_do_elemento(self.lista_codigo_movimentacao, timeout)
            == codigo_movimentacao
        )


        valor_preenchido_codigo_saque_valido = (
            self.extrair_valor_do_elemento(self.lista_codigo_saque) == codigo_saque
        )


        if (
            valor_preenchido_data_movimentacao_valido
            and valor_preenchido_codigo_movimentacao_valido
            and valor_preenchido_codigo_saque_valido
        ):
            registro_existente_valido = True
        else:
            registro_existente_valido = False

        return registro_existente_valido

    def preencher_formulario_chave(
        self,
        data_movimentacao: str,
        codigo_movimentacao: str,
        codigo_saque: str,
        ambiente_execucao: str,
        registro_anterior_existente: bool,
        timeout: int,
    ) -> None:
        """
        Preenche informações do formulário para a geração da chave

        Ags:
            data_movimentacao (dict): data relacionada ao processo recisório
            codigo_movimentacao (str): código relacionado ao tipo de recisão
            codigo_saque (str): codigo relacionado ao tipo de recisão
            ambiente_execucao (str): ambiente em que o script está sendo executado. Pode ser dev, qa ou prod
            timeout (int): tempo de timout utilizado na interação com elementos da tela

        """

        if not registro_anterior_existente:
            # Preencher data de movimentação
            self.preencher_campo(
                self.campo_preenchimento_data_movimentacao, data_movimentacao, timeout
            )

            # Selecionar o código da movimentação
            opcao_codigo_movimentacao = codigo_movimentacao
            self.seleciona_opcao_dropdown(
                self.lista_codigo_movimentacao, opcao_codigo_movimentacao, timeout
            )

            # Selecionar o código de saque
            opcao_codigo_saque = codigo_saque
            self.seleciona_opcao_dropdown(
                self.lista_codigo_saque, opcao_codigo_saque, timeout
            )

        # Prencher sempre NÃO para o campo de pensão alimenticia
        self.preencher_campo(
            self.campo_preenchimento_pensao_alimenticia, "NAO", timeout
        )

        # Tenta executar o click no botão se ele aparece. Caso não apareça segue a execução
        try:
            self.clicar_botao(self.botao_consignado, timeout)
        except:
            pass

        # Clicar no botão de continuar
        self.clicar_botao(self.botao_continuar, timeout)

        # Confirmar no alerta de mensagem que o empregador não possui telefone celular
        self.clicar_botao(self.opcao_nao_msg_trabalhador_sem_celular, timeout)

        # Confirma popup do browser com orientação de aviso ao trabalhador
        self.aceitar_alerta()

        # Dar um check na declaração de que foi efetuada a anotação da data da rescisão na carteira
        self.clicar_botao(self.checkbox_aviso_trabalhador, timeout)

        # Clicar no botão de continuar novamente (SO ACONTECE EM AMBIENTE DE PRODUCAO, JAMAIS CLICAR EM CONTINUAR DURANTE TESTES)
        if ambiente_execucao == "PROD":
            self.clicar_botao(self.botao_continuar, timeout)

    def gerar_imagem_chave(self, screenshot_path: Path) -> None:
        """
        Tira o print da tela e salva no formato de imagem

        Ags:
            screenshot_path (Path): caminho onde vai ser armazenado o print tirado da tela
        """

        self.tirar_print_tela(screenshot_path)
