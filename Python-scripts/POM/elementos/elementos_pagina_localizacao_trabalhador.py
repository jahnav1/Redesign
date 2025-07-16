from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from POM.page_objects.page_objects import PageElement
from datetime import datetime
from registrador_logs import instancia_log


class LocalizacaoTrabalhadorNome(PageElement):
    """
    Classe que representa a o formulário para localização do trabalhador
    """
    lista_base_conta = (By.NAME, "sltRegiao")  
    campo_preenchimento_nome = (By.NAME, "txtNomeTrab") 
    botao_continuar = (        
        By.XPATH,
        "/html/body/form/table[2]/tbody/tr[3]/td[3]/p/table/tbody/tr[23]/td/a[1]/img",
    )

    seletor_trabalhador = (By.NAME, "rdoTrabalhador")

    data_admissao_log = (  # Datas de admissao mostrada ao procurar pelo trabalhador
        By.XPATH,
        "/html/body/form/table[2]/tbody/tr[3]/td[3]/table[3]/tbody/tr[4]/td[4]"
    )                                                                                                  

    indicador_trabalhador_localizado_saldo = (
        By.XPATH,
        "/html/body/form/table[2]/tbody/tr[2]/td[3]/table[3]/tbody/tr[2]/td/table[1]/tbody/tr[19]/td[2]",
    )

    indicador_trabalhador_localizado_chave = (By.NAME, "txtDtMovimentacao") 

    msg_erro_nome_nao_localizado = (
        By.XPATH,
        "/html/body/form/table[2]/tbody/tr[2]/td[3]/table[3]/tbody/tr[2]/td/b",
    )
    msg_inconsistencia_dados_caixa = (
        By.XPATH,
        "/html[1]/body[1]/form[1]/table[2]/tbody[1]/tr[2]/td[3]/table[3]/tbody[1]/tr[2]/td[1]/b[1]",
    )



    def preencher_dados_trabalhador(self, nome_colaborador: str, timeout: int) -> None:
        """
        Preenche informações do trabalhador na página de localização, que é comum para todos os serviços

        Ags:
            nome_colaborador (str): nome do trabalhador que vai ser utilizado para preencher o formulário de localização do trabalhador
            timeout (int): tempo de timout utilizado na interação com elementos da tela
        """
        # Selecionar a conta base (sempre SP)
        opcao_base_conta = "SP-SAO PAULO"
        self.seleciona_opcao_dropdown(self.lista_base_conta, opcao_base_conta, timeout)

        # Preencher o NOME
        self.preencher_campo(self.campo_preenchimento_nome, nome_colaborador, timeout)

        # Confirmar solicitação de localização do trabalhador
        self.clicar_botao(self.botao_continuar, timeout)
        instancia_log.info("Dados do trabalhador preenchidos")


    def contar_ocorrencias_trabalhador(self) -> int:
        """
        Verifica o número de ocorrências do trabalhador na página
        """
        try:
            elementos_trabalhador = self.procura_elementos(*self.seletor_trabalhador)
            numero_ocorrencias = len(elementos_trabalhador)
            return numero_ocorrencias
        except NoSuchElementException:
            return 0
        
    def verificar_try_except(self, elemento_indicador_trabalhador_localizado, timeout: int):
        """
        Verifica se o trabalhador foi localizado
        Ags :
            elemento_indicador_trabalhador_localizado (By): elemento que indica que o trabalhador foi localizado
            timeout (int): tempo de timout utilizado na interação com elementos da tela 
        """
        try:
            self.aguarda_elemento_aparecer(elemento_indicador_trabalhador_localizado, timeout)
            trabalhador_localizado = True
            return "Trabalhador localizado"
        except TimeoutException:
            trabalhador_localizado = False

        if not trabalhador_localizado:
            msg_retorno = "Não localizado"
            try:
                # Verifica mensagem de erro de nome não localizado
                if self.aguarda_elemento_aparecer(
                    self.msg_erro_nome_nao_localizado, timeout
                ):
                    msg_retorno = "Erro previsto na etapa de localização do trabalhador: nome não localizado"

                # Verifica mensagem de erro de inconsistência nos dados da caixa
                elif self.aguarda_elemento_aparecer(
                    self.msg_inconsistencia_dados_caixa, timeout
                ):
                    msg_retorno = "Erro previsto na etapa de localização do trabalhador: inconsistência nos dados da caixa"

                return msg_retorno
            except TimeoutException:
                return "Erro não previsto na etapa de localização do trabalhador"
            

    def converter_data(self, data):
        try:
            # Tenta converter usando o formato 'YYYY-MM-DD HH:MM:SS'
            data_objeto = datetime.strptime(data, r'%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # Se falhar, tenta converter usando o formato 'DD/MM/ANO'
                data_objeto = datetime.strptime(data, r'%d/%m/%Y')
            except ValueError:
                # Se ambos os formatos falharem, lança um erro
                raise ValueError("Formato de data inválido")
        
        return data_objeto
    

    def verificar_trabalhador_localizado(self, data_admissao: str, servico: str, timeout: int) -> tuple: 
        """
        Verifica o número de ocorrências do trabalhador e se foi localizado
        """
        # Converte a data de admissao para o formato da página
        data_objeto = self.converter_data(data_admissao)
        data_admissao = data_objeto.strftime(r'%d/%m/%Y')

        # Verificar o número de ocorrências do trabalhador para a data de admissão
        numero_ocorrencias = self.contar_ocorrencias_trabalhador()
        indices_datas_admissao = []  # Lista para armazenar os indices dos seletores das datas de admissão corretas
        # Caso não tenha ocorrencia do seletor, significa que o passo a passo deve ser o mesmo de antes
        if numero_ocorrencias == 0: 
            if servico == "CHAVE":
                elemento_indicador_trabalhador_localizado = (
                    self.indicador_trabalhador_localizado_chave
                )
            else:
                elemento_indicador_trabalhador_localizado = (
                    self.indicador_trabalhador_localizado_saldo
                )
                instancia_log.info(f"Elemento indicador trabalhador: {elemento_indicador_trabalhador_localizado}")

            ret = self.verificar_try_except(elemento_indicador_trabalhador_localizado, timeout)  # Verifica se o trabalhador foi localizado
            return ret, indices_datas_admissao


        elif numero_ocorrencias > 1:
            # Se o serviço não for do tipo chave e houver mais de uma ocorrência, seleciona cada uma e executa a sequência específica
            for i in range(numero_ocorrencias):  # Para cada ocorrência:
                self.aguarda_elemento_aparecer(self.data_admissao_log, timeout)    # Aguarda a data de admissão aparecer
                # Formata o XPath da data de admissao dinamicamente
                xpath_formatado = "/html/body/form/table[2]/tbody/tr[3]/td[3]/table[3]/tbody/tr[{indice}]/td[4]".format(indice=4 + i * 3)
                data_admissao_log = (By.XPATH, xpath_formatado)
                
                # Verifica se a data de admissão é a correta
                data_admissao_texto = self.recuperar_texto_do_elemento(data_admissao_log).strip()   # Pega a data de admissão
                if data_admissao_texto == data_admissao:   # Se a data de admissão for a correta
                    indices_datas_admissao.append(i)  # Adiciona o índice da data de admissão correta
                    # Caso a data de admissao seja a correta, o trabalhador foi localizado
                    elemento_indicador_trabalhador_localizado = (
                        data_admissao_log
                    )
                    self.verificar_try_except(elemento_indicador_trabalhador_localizado, timeout) # Verifica se o trabalhador foi localizado
                else:
                    return "Nenhuma ocorrência do trabalhador com a data de admissão correta na iteração", indices_datas_admissao
            return "Ocorrencias do trabalhador nos indices: ", indices_datas_admissao
        
