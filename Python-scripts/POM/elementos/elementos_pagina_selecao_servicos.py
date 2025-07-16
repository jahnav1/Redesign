from selenium.webdriver.common.by import By
from POM.page_objects.page_objects import PageElement


class SeletorServico(PageElement):
    """
    Classe que representa a lista de seleção dos serviços disponiveis
    """

    lista_serviços = (By.NAME, "sltOpcao")

    def selecionar_servico_desejado(self, servico_desejado: str, timeout: int) -> None:
        """
        Aguarda a lista de serviços aparecer, procura o serviço desejado na lista e seleciona

        Ags:
            servico_desejado (str): serviço que vai ser executado pelo robô dentro do site da caixa
            timeout (int): tempo de timout utilizado na interação com elementos da tela
        """
        # Mapeando as opções de serviço
        opcoes_servico = {
            "SALDO": "Solicitar Extrato do Trabalhador",
            "EXTRATO": "Solicitar Extrato do Trabalhador",
            "CHAVE": "Comunicar Movimentação do Trabalhador",
        }

        # Obtendo a opção correspondente ao serviço desejado
        opcao_servico_desejado = opcoes_servico.get(servico_desejado)

        # Selecionando a opção do serviço desejado
        self.seleciona_opcao_dropdown(
            self.lista_serviços, opcao_servico_desejado, timeout
        )

    def retornar_menu_selecao_servico(self, timeout: int) -> None:
        """
        Aguarda a lista de serviços aparecer e seleciona uma opção aleatório

        Ags:
            timeout (int): tempo de timout utilizado na interação com elementos da tela
        """
        # Mapeando as opções de serviço
        servico_desejado = "Solicitar Extrato Analítico do Trabalhador"

        # Selecionando a opção do serviço desejado
        self.seleciona_opcao_dropdown(self.lista_serviços, servico_desejado, timeout)
