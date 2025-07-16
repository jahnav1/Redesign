from abc import ABC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from pathlib import Path


class UiObject:
    """
    Classe com métodos genéricos para interagir com elementos UI
    """

    def procura_elemento(self, *locator: tuple[str]) -> WebElement:
        """
        Procurar elemento ui com base no localizador do elemento
        """
        return self.webdriver.find_element(*locator)
    
    def procura_elementos(self, *locator: tuple[str]) -> WebElement:
        """
        Procurar todas as ocorrências do elemento ui com base no localizador do elemento
        """
        return self.webdriver.find_elements(*locator)

    def encontrar_ocorrencias_por_nome(self, seletor):
        """
        Encontra todos os elementos com o mesmo nome e retorna uma lista com os seus xpaths
        """
        elementos = self.webdriver.find_elements(By.NAME, seletor)
        xpaths = []
        for elemento in elementos:
            xpath = self.webdriver.execute_script("function absoluteXPath(element) { " +
                                        "var comp, comps = [];" +
                                        "var parent = null;" +
                                        "var xpath = '';" +
                                        "var getPos = function(element) {" +
                                        "var position = 1, curNode;" +
                                        "if (element.nodeType == Node.ATTRIBUTE_NODE) {" +
                                        "return null;" +
                                        "}" +
                                        "for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling) {" +
                                        "if (curNode.nodeName == element.nodeName) {" +
                                        "++position;" +
                                        "}" +
                                        "}" +
                                        "return position;" +
                                        "};" +
                                        "if (element instanceof Document) {" +
                                        "return '/';" +
                                        "}" +
                                        "for (; element && !(element instanceof Document); element = element.nodeType == Node.ATTRIBUTE_NODE ? element.ownerElement : element.parentNode) {" +
                                        "comp = comps[comps.length] = {};" +
                                        "switch (element.nodeType) {" +
                                        "case Node.TEXT_NODE:" +
                                        "comp.name = 'text()';" +
                                        "break;" +
                                        "case Node.ATTRIBUTE_NODE:" +
                                        "comp.name = '@' + element.nodeName;" +
                                        "break;" +
                                        "case Node.PROCESSING_INSTRUCTION_NODE:" +
                                        "comp.name = 'processing-instruction()';" +
                                        "break;" +
                                        "case Node.COMMENT_NODE:" +
                                        "comp.name = 'comment()';" +
                                        "break;" +
                                        "case Node.ELEMENT_NODE:" +
                                        "comp.name = element.nodeName;" +
                                        "break;" +
                                        "}" +
                                        "comp.position = getPos(element);" +
                                        "}" +
                                        "for (var i = comps.length - 1; i >= 0; i--) {" +
                                        "comp = comps[i];" +
                                        "xpath += '/' + comp.name.toLowerCase();" +
                                        "if (comp.position !== null) {" +
                                        "xpath += '[' + comp.position + ']';" +
                                        "}" +
                                        "}" +
                                        "return xpath;" +
                                        "} return absoluteXPath(arguments[0]);", elemento)
            xpaths.append(xpath)
        return xpaths


    def aguarda_elemento_aparecer(self, locator: str, timeout: int = 30) -> None:
        """
        Aguarda o elemento aparecer no DOM
        """
        WebDriverWait(self.webdriver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def aguarda_alerta_aparecer(self, timeout: int = 30) -> Alert:
        """
        Aguarda o elemento aparecer no DOM
        """
        try:
            return WebDriverWait(self.webdriver, timeout).until(EC.alert_is_present())
        except:
            pass

    def aceitar_alerta(self) -> None:
        """
        Muda pro contexto do alerta e faz o aceite
        """
        self.webdriver.switch_to.alert.accept()

    def seleciona_opcao_dropdown(
        self, locator: str, option_text: str, timeout: int = 30
    ) -> None:
        """
        Aguarda o dropdown ficar disponivel e seleciona a opção visivel desejada
        """
        self.aguarda_elemento_aparecer(locator, timeout)
        Select(self.procura_elemento(*locator)).select_by_visible_text(option_text)

    def preencher_campo(
        self, locator: str, dado_para_preencher, timeout: str = 10
    ) -> None:
        """
        Aguarda o campo de preenchimento ficar disponivel e preenche com a informação. O dado a ser preenchido por ser do time inteiro, string ou data.
        """
        self.aguarda_elemento_aparecer(locator, timeout)
        campo_de_preenhcimento = self.procura_elemento(*locator)
        campo_de_preenhcimento.clear()
        campo_de_preenhcimento.send_keys(dado_para_preencher)

    def clicar_botao(self, locator: str, timeout: int = 10) -> None:
        """
        Aguarda o botão ficar disponível e realiza o clique
        """
        self.aguarda_elemento_aparecer(locator, timeout)
        button = self.procura_elemento(*locator)
        button.click()

    def recuperar_texto_do_elemento(self, locator: str, timeout: int = 10) -> str:
        """
        Aguarda o elemento ficar disponível e retorna o texto do elemento
        """
        self.aguarda_elemento_aparecer(locator, timeout)
        element = self.procura_elemento(*locator)
        return element.text

    def tirar_print_tela(self, screenshot_path: Path) -> None:
        """Tira o print da tela e salva localmente a imagem no caminho especificado"""
        self.webdriver.set_window_size(800, 8000)
        self.webdriver.save_screenshot(screenshot_path)
        self.webdriver.maximize_window()

    def extrair_valor_do_elemento(self, locator: str, timeout: int = 10) -> str:
        """
        Aguarda o elemento ficar disponível e retorna o valor do atributo 'value' do elemento
        """
        self.aguarda_elemento_aparecer(locator, timeout)
        element = self.procura_elemento(*locator)
        return element.get_attribute("value")


class Page(ABC, UiObject):
    """
    Classe abstrata que representa uma página da aplicação e contém métodos para interagir com as páginas
    """

    def __init__(self, webdriver: WebDriver, url: str) -> None:
        """
        Inicializa a classe Page
        """
        self.webdriver = webdriver
        self.url = url
        self._atualizar_page_elements_com_webdriver()

    def open(self) -> None:
        """
        Abre o browser numa url especifica e maximiza a tela
        """
        self.webdriver.get(self.url)
        self.webdriver.maximize_window()

    def quit_driver(self) -> None:
        """
        Fecha a instancia do webdriver
        """
        self.webdriver.quit()

    def fecha_browser(self) -> None:
        """
        Fecha a janela do navegador mas mantem a instancia do webdriver aberta
        """
        self.webdriver.close()

    def _atualizar_page_elements_com_webdriver(self) -> None:
        """
        Atualiza os atributos webdriver de todas as instâncias de PageElement na classe com o webdriver da página

        Este método é importante para garantir que todas as instâncias de PageElement tenham acesso ao webdriver da página,
        permitindo interações com os elementos da página

        """
        for atributo in dir(self):
            atributo_real = getattr(self, atributo)
            if isinstance(atributo_real, PageElement):
                atributo_real.webdriver = self.webdriver


class PageElement(ABC, UiObject):
    """
    Classe abstrata que representa um elemento em uma página
    """

    def __init__(self, webdriver: WebDriver = None) -> None:
        """
        Inicializa a classe PageElement
        """
        self.webdriver = webdriver
