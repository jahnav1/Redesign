from POM.page_objects.page_objects import Page
from POM.elementos.elementos_pagina_inicial import Empregador, CertificadoDigital
from registrador_logs import instancia_log

class PaginaInicial(Page):
    """
    Classe que representa a página inicial do site
    """

    empregador = Empregador()
    certificado_digital = CertificadoDigital()

    def acessar_site(self, posicao_certificado: int) -> None:
        """
        Acessa site da caixa e seleciona o certificado digital

        Ags:
            parametros (dict): dicionário de parâmetros que vão ser utilizado na execução em subprocess

        """

        try:
            self.open()
            self.empregador.selecionar_empregador(timeout=10)
            
        except:
            etapa = "abertura do site e seleção do botão empregador"
            msg_erro = f"Erro não previsto na etapa de: {etapa}"
            raise Exception(msg_erro)
        
        try:
            self.certificado_digital.selecionar_certificado(int(posicao_certificado))
        except:
            retorno_verificacao_certificado = (
            self.certificado_digital.verificacao_selecao_certificado(timeout=10)
        )
            if "Erro" in retorno_verificacao_certificado:
                raise Exception(retorno_verificacao_certificado)







