from POM.page_objects.page_objects import Page
from POM.elementos.elementos_pagina_selecao_servicos import SeletorServico


class PaginaSelecaoServicos(Page):
    """
    Página em que acontece a seleção do serviço desejado
    """

    lista_servicos = SeletorServico()

    def selecionar_servico(self, servico_desejado: str) -> None:
        """
        Seleciona o serviço desejado na lista de serviços disponivel

        Ags:
            servico_desejado (str): serviço que vai ser executado pelo script
        """
        try:
            self.lista_servicos.selecionar_servico_desejado(
                servico_desejado, timeout=10
            )
        except:

            etapa = "seleção do serviço desejado"
            msg_erro = f"Erro não previsto na etapa de: {etapa}"
            raise Exception(msg_erro)

    def retornar_menu_selecao_servico(self) -> None:
        """
        Seleciona uma opção aleatória para retornar ao menu de seleção de serviço
        """
        try:
            self.lista_servicos.retornar_menu_selecao_servico(timeout=10)
        except:
            etapa = "retorno para o menu principal"
            # Caso não encontre erro mapeado retorna erro genérico
            msg_erro = f"Erro não previsto na etapa de: {etapa}"
            raise Exception(msg_erro)
