from selenium.common.exceptions import UnexpectedAlertPresentException

from POM.page_objects.page_objects import Page
from POM.elementos.elementos_pagina_localizacao_trabalhador import (
    LocalizacaoTrabalhadorNome,
)
from registrador_logs import instancia_log

class PaginaLocalizacaoTrabalhador(Page):
    """
    Página em que acontece a localização do trabalhador
    """
    localizacao_trabalhador = LocalizacaoTrabalhadorNome()

    def localizar_trabalhador(self, nome_colaborador: str, data_admissao: str, servico: str) -> None:
        """
        Localiza o trabalhador com base no NOME

        Ags:
            nome_colaborador (str): nome do trabalhador que vai ser utilizado para preencher o formulário de localização
            data_admissao (str): data de admissão para verificação em caso de mais de uma ocorrência
        """
        try:
            self.localizacao_trabalhador.preencher_dados_trabalhador(nome_colaborador, timeout=5)
            alerta = self.aguarda_alerta_aparecer(timeout=5)

            if alerta:
                msg_alerta = alerta.text
                raise UnexpectedAlertPresentException(
                    f"Erro previsto na etapa de localização do trabalhador: {alerta.text}"
                )

            retorno_trabalhador_localizado = (
                self.localizacao_trabalhador.verificar_trabalhador_localizado(
                    data_admissao, servico, timeout=5
                )
            )
            instancia_log.info("Retorno trabalhador localizado: %s", retorno_trabalhador_localizado)
            if "Erro" in retorno_trabalhador_localizado:
                raise Exception(retorno_trabalhador_localizado)

        except UnexpectedAlertPresentException:
            self.localizacao_trabalhador.aceitar_alerta()
            raise Exception(
                f"Erro previsto na etapa de localização do trabalhador:{msg_alerta}"
            )
    
    def localizar_sem_verificar(self, nome_colaborador: str) -> None:
        """
        Localiza o trabalhador com base no NOME

        Ags:
            nome_colaborador (str): nome do trabalhador que vai ser utilizado para preencher o formulário de localização
        """
        try:
            self.localizacao_trabalhador.preencher_dados_trabalhador(nome_colaborador, timeout=5)
            alerta = self.aguarda_alerta_aparecer(timeout=5)

            if alerta:
                msg_alerta = alerta.text
                raise UnexpectedAlertPresentException(
                    f"Erro previsto na etapa de localização do trabalhador: {alerta.text}"
                )
            
        except UnexpectedAlertPresentException:
            self.localizacao_trabalhador.aceitar_alerta()
            raise Exception(
                f"Erro previsto na etapa de localização do trabalhador:{msg_alerta}"
            )