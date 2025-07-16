from selenium.webdriver.common.by import By
import time
import pyautogui
from selenium.common.exceptions import TimeoutException

from POM.page_objects.page_objects import PageElement


class Empregador(PageElement):
    """
    Classe que representa o elemento de seleção do empregador na página inicial
    """

    botao_empregador = (By.CSS_SELECTOR, "#btnEmpregador")

    def selecionar_empregador(self, timeout: int) -> None:
        """
        Clica no botão empregador disponível na tela inicial

        Ags:
            timeout (int): tempo de timout utilizado na interação com elementos da tela
        """
        self.clicar_botao(self.botao_empregador, timeout)


class CertificadoDigital(PageElement):
    """
    Classe que representa o elemento para seleção do certificado digital
    """

    texto_indicador_portal_acessado = (By.NAME, "sltOpcao")
    erro_certificado_diferente_conexao = (
        By.XPATH,
        "/html[1]/body[1]/form[1]/table[2]/tbody[1]/tr[3]/td[3]/table[2]/tbody[1]/tr[2]/td[1]/b[1]",
    )

    def selecionar_certificado(self, posicao_certificado: int) -> None:
        """
        Procura o certificado da empresa e seleciona

        Ags:
            posicao_certificado (int): posicao do certificado que vai ser selecionado
        """

        # Para o site da caixa é preciso selecionar 2 vezes o certificado
        qtd_selecoes_certificado = 2
        contador_interacoes_certificado = 1

        while contador_interacoes_certificado <= qtd_selecoes_certificado:
            time.sleep(1)
            pyautogui.press("down", presses=posicao_certificado - 1)
            time.sleep(1)

            pyautogui.press("tab")
            time.sleep(1)

            pyautogui.press("left", presses=2)
            time.sleep(1)

            pyautogui.press("enter")
            time.sleep(1)

            contador_interacoes_certificado += 1
            time.sleep(2)

    def verificacao_selecao_certificado(self, timeout: int) -> str:
        """
        verifica se a página inicial logada apareceu.Caso não tenha aparecido identifica se erro foi mapeado anteriormente
        """
        # verifica se a tela de página logada inicial apareceu
        try:
            self.aguarda_elemento_aparecer(
                self.texto_indicador_portal_acessado, timeout
            )
            certificado_selecionado = True
            return "Certificado selecionado"
        except TimeoutException:
            certificado_selecionado = False

        # pagina logada inicial não apareceu > identificar se tela de erro foi mapeada
        if not certificado_selecionado:
            try:
                self.aguarda_elemento_aparecer(
                    self.erro_certificado_diferente_conexao, timeout
                )
                return "Erro previsto na etapa de seleção do certificado: certificado diferente da conexão "
            except TimeoutException:
                return "Erro não previsto na etapa de seleção do certificado"
