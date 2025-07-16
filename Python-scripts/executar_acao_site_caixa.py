import sys
import pandas as pd
from pathlib import Path

from POM.pages.pagina_chave import PaginaChave
from POM.pages.pagina_extrato_fgts import PaginaExtratoFgts
from POM.pages.pagina_inicial import PaginaInicial
from POM.pages.pagina_localizacao_trabalhador import PaginaLocalizacaoTrabalhador
from POM.pages.pagina_selecao_servicos import PaginaSelecaoServicos
from registrador_logs import ConfiguradorLog
from registrador_logs import instancia_log
from auxiliar import (
    instanciar_drive,
    upload_arquivo_drive,
    escrever_no_excel,
    incluir_info_certificado
)

# Recupera a pasta em que o script está sendo executado
SCRIPT_DIRECTORY = Path(__file__).resolve().parent


def executar_acao(parametros: dict) -> None:
    """
    Executa a ação necessária no site da caixa, que pode ser SALDO, EXTRATO, CHAVE

    Ags:
        parametros (dict): dicionário de parâmetros que vão ser utilizado na execução em subprocess
    """
    # Instanciar a classe que vai configurar toda a parte de logs
    arquivo_log = ConfiguradorLog(SCRIPT_DIRECTORY)

    # Configurar arquivo de log
    ConfiguradorLog.configurar_arquivo_log(arquivo_log)

    # Incluir informações iniciais da execução no arquivo de log
    ConfiguradorLog.incluir_info_execucao(arquivo_log)

    # Recupera parâmetros
    url_site_caixa = parametros["url_site_caixa"]
    servico = parametros["servico"]
    caminho_arquivo_input = parametros["caminho_arquivo_input"]
    ambiente_execucao = parametros["ambiente_execucao"]
    caminho_service_account = parametros["caminho_service_account"]
    email_usuario = parametros["email_usuario"]
    caminho_arquivo_dados_certificados = parametros[
        "caminho_arquivo_dados_certificados"
    ]
    max_qtd_retry = parametros["max_qtd_retry"]
    max_qtd_falhas_consecutivas = parametros["max_qtd_falhas_consecutivas"]
    caminho_relativo_output_scripts = parametros["caminho_relativo_output_scripts"]
    caminho_relativo_relatorio_execucao = parametros[
        "caminho_relativo_relatorio_execucao"
    ]

    # Pasta para armazenamento de outputs
    pasta_projeto = Path(SCRIPT_DIRECTORY).parent
    pasta_armazenamento_output = pasta_projeto / Path(
        *caminho_relativo_output_scripts.split("/")
    )
    pasta_armazenamento_relatorio_execucao = pasta_projeto / Path(
        *caminho_relativo_relatorio_execucao.split("/")
    )

    # Ler dados de input
    dados_para_processar = pd.read_excel(
        caminho_arquivo_input, dtype={"CPF": str, "PIS": str, "DATA DE ADMISSAO": str}
    )


    qtd_linhas_recebidas_para_processar = len(dados_para_processar)
    instancia_log.info("Dados de input lidos")
    instancia_log.info(
        f"{qtd_linhas_recebidas_para_processar} linhas recebidas para processar"
    )

    # Ler dados de certificado
    dados_certificados = pd.read_excel(caminho_arquivo_dados_certificados)
    instancia_log.info("Dados de certificado digital lidos")

    # Adiciona dados de certificado nos dados para processar
    dados_para_processar = incluir_info_certificado(
        dados_para_processar, dados_certificados
    )
    instancia_log.info("Dados de certificado adicicionados aos dados de input")

    # Inicialização do dataframe para armazenar output, caso o serviço desejado seja SALDO
    if servico == "SALDO":
        df_output_saldo = dados_para_processar.copy()
        df_output_saldo["SALDO"] = None

    # Adiciona colunas de status e observação (sem nada preenchido) para armazenar o resultado do processamento
    dados_para_processar["STATUS"] = None
    dados_para_processar["OBSERVAÇÃO"] = None

    # Filtrar linhas que tenham certificado invalido e atualizar a coluna de status com erro previsto e a coluna de observação com a mensagem de certificado vencido
    condicao_certificado_invalido = (
        dados_para_processar["STATUS CERTIFICADO"] == "INVALIDO"
    )
    dados_para_processar.loc[condicao_certificado_invalido, "STATUS"] = "ERRO PREVISTO"
    dados_para_processar.loc[condicao_certificado_invalido, "OBSERVAÇÃO"] = (
        "Certificado digital para acesssar site da caixa invalido"
    )

    # Cria instancia para o driver
    driver = instanciar_drive()
    instancia_log.info("Driver instanciado")

    # Cria instancia para páginas
    pagina_inicial = PaginaInicial(driver, url_site_caixa)
    pagina_selecao_servicos = PaginaSelecaoServicos(driver, url_site_caixa)
    pagina_localizacao_trabalhador = PaginaLocalizacaoTrabalhador(
        driver, url_site_caixa
    )
    pagina_extrato_fgts = PaginaExtratoFgts(driver, url_site_caixa)
    pagina_chave = PaginaChave(driver, url_site_caixa)

    instancia_log.info("Paginas instanciadas")

    reiniciar_navegador = False
    condicao_linhas_certificado_valido = (
        dados_para_processar["STATUS CERTIFICADO"] == "VALIDO"
    )
    qtd_linhas_validas = len(dados_para_processar[condicao_linhas_certificado_valido])
    instancia_log.info(
        f"{qtd_linhas_validas} linha(s) com certificado valido para processar"
    )
    index_linha_valida = 0
    empresa_anterior = ""
    contador_falhas_consecutivas = 0
    condicao_para_executar = True
    status_processamento = ""

    try:
        # Percorrer cada linha que possua certificado valido e realizar as ações necessárias
        for index, row in dados_para_processar[
            condicao_linhas_certificado_valido
        ].iterrows():
            condicao_para_executar = True 
            contador_retry = 0

            while condicao_para_executar and (
                contador_falhas_consecutivas < max_qtd_falhas_consecutivas
            ):
                try:
                    # Identificando linha
                    instancia_log.info("========================================")
                    instancia_log.info(f"index linha válida: {index_linha_valida}")
                    ultima_linha = (index_linha_valida + 1) == qtd_linhas_validas
                    instancia_log.info(
                        f"Processando linha {index + 1} /Última linha: {ultima_linha}"
                    )
                    instancia_log.info("========================================")

                    # Recupera dados da linha que vão ser utilizados no processamento para acessar o site e localizar o colaborador
                    nome_colaborador_original = str(row["NOME"]).strip() # Nome original do colaborador sem a remoção de preposições
                    nome_colaborador = str(row["NOME"]).strip().replace(" DA ", " ").replace(" DE ", " ").replace(" DO ", " ").replace(" DOS ", " ").replace(" DAS ", " ").replace(" E ", " ")
                    data_admissao = str(row["DATA DE ADMISSAO"]).strip()
                    posicao_certificado = row["POSICAO DO CERTIFICADO"]
                    empresa = str(row["EMPRESA"]).strip()
                    id_pasta = str(row[f"ID PASTA DRIVE {servico}"])
                    empresa_atual = empresa
                    instancia_log.info(
                        f"Dados da linha a serem utilizados no processamento recuperados/Posição do certificado: {posicao_certificado}"
                    )

                    reiniciar_navegador = (not empresa_atual == empresa_anterior) or (
                        status_processamento == "ERRO PREVISTO"
                        or status_processamento == "ERRO NÃO PREVISTO"
                    )

                    instancia_log.info(
                        f"Empresa anterior: {empresa_anterior}/Empresa atual: {empresa_atual}/Reiniciar navegador: {reiniciar_navegador}"
                    )

                    # Se necessário abre browser e vai até a página inicial. Caso não precise abrir o navegador novamente apenas volta para a página de seleção do serviço
                    if index_linha_valida == 0 and contador_retry == 0:
                        instancia_log.info("É a primeira linha > acessar o site")
                        pagina_inicial.acessar_site(posicao_certificado)
                    elif reiniciar_navegador:
                        instancia_log.info(
                            "É preciso reiniciar o browser antes de acessar o site"
                        )
                        pagina_inicial.fecha_browser()
                        driver = instanciar_drive()
                        # Cria instancia das páginas diferentes
                        pagina_inicial = PaginaInicial(driver, url_site_caixa)
                        pagina_selecao_servicos = PaginaSelecaoServicos(
                            driver, url_site_caixa
                        )
                        pagina_localizacao_trabalhador = PaginaLocalizacaoTrabalhador(
                            driver, url_site_caixa
                        )
                        pagina_extrato_fgts = PaginaExtratoFgts(driver, url_site_caixa)
                        pagina_chave = PaginaChave(driver, url_site_caixa)
                        pagina_inicial.acessar_site(posicao_certificado)
                    else:
                        # Seleciona um serviço qualquer para indicar que saiu do serviço anterior e posteriormente o serviço correto será selecionado
                        instancia_log.info(
                            "Não é preciso reiniciar o browser, apenas retomar para a tela inicial do serviço para que o colaborador possa ser localizado"
                        )
                        pagina_selecao_servicos.retornar_menu_selecao_servico()
                        instancia_log.info("Retorna ao menu dos serviços")

                        # pagina_selecao_servicos.selecionar_servivo(servico)

                    # Selecionar o serviço desejado
                    pagina_selecao_servicos.selecionar_servico(servico)
                    instancia_log.info(f"Serviço de {servico} selecionado")

                    # Localizar o colaborador utilizando o nome
                    pagina_localizacao_trabalhador.localizar_trabalhador(
                        nome_colaborador, data_admissao, servico
                    )
                    
                    
                    # Utilizar o retorno da função verificar_trabalhador_localizado ( que é uma tupla com uma mensagem e uma lista de elementos) para verificar se o trabalhador foi localizado
                    retorno, lista_indice_data = pagina_localizacao_trabalhador.localizacao_trabalhador.verificar_trabalhador_localizado(
                        data_admissao, servico, timeout=5
                    )
                    instancia_log.info(f"Retorno da localização do trabalhador: {retorno}")
                    instancia_log.info(f"Lista de indices de datas de admissão: {lista_indice_data}")

                    # Executa a ação de acordo o serviço desejado
                    if servico == "SALDO":
                        df_output_saldo = pagina_extrato_fgts.extrair_saldo(
                            df_output_saldo, index, lista_indice_data, retorno
                        )
                        # O output do processamento do saldo só é enviado no final
                        instancia_log.info("Saldo extraido")
                        obs_processamento = ""
                    elif servico == "EXTRATO":
                        caminho_local_pdf_gerado = (
                            pagina_extrato_fgts.gerar_extrato_fgts(
                                pasta_armazenamento_output, nome_colaborador, nome_colaborador_original, lista_indice_data
                            )
                        )
                        if lista_indice_data:
                            for i in range(len(lista_indice_data)):
                                instancia_log.info(f"Caminhos: {caminho_local_pdf_gerado[i]}")
                                obs_processamento = upload_arquivo_drive(
                                    caminho_local_pdf_gerado[i],
                                    caminho_service_account,
                                    id_pasta,
                                    email_usuario,
                                )
                        else:
                            instancia_log.info(f"Caminho: {caminho_local_pdf_gerado[0]}")
                            obs_processamento = upload_arquivo_drive(
                                caminho_local_pdf_gerado[0],
                                caminho_service_account,
                                id_pasta,
                                email_usuario,
                            )
                        instancia_log.info("Extrato gerado")
                        
                    elif servico == "CHAVE":
                        # O código de movimento e de saque são recebidos na coluna CODIGO EXECUCAO nos seguintes formatos 'I1 - 01' ou 'I3 - 04'
                        data_movimentacao = pd.to_datetime(row["DATA DE RECISÃO"]).strftime(r'%d/%m/%Y')
                        codigo_movimentacao = (
                            str(row["CODIGO EXECUCAO"]).strip().split(" - ")[0]
                        )
                        codigo_saque = (
                            str(row["CODIGO EXECUCAO"]).strip().split(" - ")[1]
                        )

                        # Lista com os registros anteriores existentes ou não
                        registro_anterior_existente = (
                            pagina_chave.verificar_existencia_registro_anterior(nome_colaborador, data_admissao, lista_indice_data, retorno, driver, url_site_caixa)
                        )
                        instancia_log.info(
                            f"Registro anterior existente: {registro_anterior_existente}"
                        )

                        caminho_local_pdf_gerado = pagina_chave.gerar_chave(
                            pasta_armazenamento_output,
                            nome_colaborador,
                            nome_colaborador_original,
                            data_movimentacao,
                            codigo_movimentacao,
                            codigo_saque,
                            ambiente_execucao,
                            registro_anterior_existente,
                            lista_indice_data,
                            retorno,
                        )
                        instancia_log.info(f"Caminho: {caminho_local_pdf_gerado}")
                        if caminho_local_pdf_gerado:
                            for caminho in caminho_local_pdf_gerado:
                                output_arquivo_chave = upload_arquivo_drive(
                                    caminho,
                                    caminho_service_account,
                                    id_pasta,
                                    email_usuario,
                                )
                                obs_processamento = f"Registo anterior existente:{registro_anterior_existente}|{output_arquivo_chave}"
                        else:
                            obs_processamento = ""
                        instancia_log.info("Extrato gerado")
                        
                    if retorno == "Não localizado":
                        status_processamento = "ERRO PREVISTO"
                    else:
                        status_processamento = "SUCESSO"
                    contador_falhas_consecutivas = 0
                    instancia_log.info(
                        f"Status do processamento: {status_processamento}"
                    )

                except Exception as e:
                    excecao_linha = str(e)
                    # Verifica se foi erro previsto ou não previsto e atribui o status do processamento (por meio da nomenclatura)
                    if "Erro previsto" in excecao_linha:
                        status_processamento = "ERRO PREVISTO"
                    elif "Erro não previsto" in excecao_linha:
                        status_processamento = "ERRO NÃO PREVISTO"
                    else:
                        status_processamento = "ERRO NÃO PREVISTO"

                    instancia_log.info(
                        f"Status do processamento: {status_processamento}"
                    )
                    instancia_log.info(f"Status do processamento: {excecao_linha}")

                    obs_processamento = excecao_linha

                    if status_processamento == "ERRO NÃO PREVISTO":
                        contador_retry = contador_retry + 1
                        instancia_log.info(f"Contador do retry: {contador_retry}")

                        contador_falhas_consecutivas = contador_falhas_consecutivas + 1
                        instancia_log.info(
                            f"Contador de falhas consecutivas: {contador_falhas_consecutivas}"
                        )

                    if contador_falhas_consecutivas >= max_qtd_falhas_consecutivas:
                        instancia_log.info(
                            f"Excedido o número máximo de {max_qtd_falhas_consecutivas} falhas consecutivas."
                        )

                    continue

                finally:
                    # Atualiza o status da linha que esta sendo processada
                    dados_para_processar.at[index, "STATUS"] = status_processamento
                    dados_para_processar.at[index, "OBSERVAÇÃO"] = obs_processamento

                    # No caso de o máximo de falhas consecutivas ter sido atingida informar a área que esse foi o motivo da linha não ter sido processad
                    if contador_falhas_consecutivas >= max_qtd_falhas_consecutivas:
                        condicao_linhas_nao_processadas_max_exc = (
                            (dados_para_processar["STATUS"] != "ERRO PREVISTO")
                            & (dados_para_processar["STATUS"] != "ERRO NÃO PREVISTO")
                            & (dados_para_processar["STATUS"] != "SUCESSO")
                        )
                        instancia_log.info(
                            f"Quantidade de linhas não processadas: {condicao_linhas_nao_processadas_max_exc.sum()}"
                        )
                        dados_para_processar.loc[
                            condicao_linhas_nao_processadas_max_exc, "STATUS"
                        ] = "LINHA NÃO PROCESSADA"
                        dados_para_processar.loc[
                            condicao_linhas_nao_processadas_max_exc, "OBSERVAÇÃO"
                        ] = "Linha não foi processada, pois foi atingido um número máximo de exceções consecutivas, fazer uma nova solicitação"

                    # Verifica se a linha vai ser reprocessada ou não
                    condicao_para_retry = (
                        contador_retry < max_qtd_retry
                        and status_processamento == "ERRO NÃO PREVISTO"
                        and (contador_falhas_consecutivas < max_qtd_falhas_consecutivas)
                    )

                    instancia_log.info(
                        f"Condição para retry: Contador de retry < Qtd max de retries: {contador_retry < max_qtd_retry}/ Status do processamento é erro não previsto: {status_processamento == 'ERRO NÃO PREVISTO'}/ Qtd de falhas consecutivas não foi atingida: {contador_falhas_consecutivas < max_qtd_falhas_consecutivas}"
                    )

                    # Garante que o arquivo de output do saldo será enviado ao final da execução caso seja a última linha, idenpendente de erro ou não. Além disso faz o incremento do index da linha válida
                    if (
                        (ultima_linha and not condicao_para_retry)
                        or (contador_falhas_consecutivas >= max_qtd_falhas_consecutivas)
                    ) and servico == "SALDO":
                        # Escreve output no excel
                        colunas_para_remover = [
                            "STATUS CERTIFICADO",
                            "ALERTA CERTIFICADO",
                            "POSICAO DO CERTIFICADO",
                            "ID PASTA DRIVE SALDO",
                            "ID PASTA DRIVE EXTRATO",
                            "ID PASTA DRIVE CHAVE",
                        ]
                        nome_arquivo_excel = "extrato_fgts_saldo"
                        caminho_local_planilha_com_saldo = escrever_no_excel(
                            df_output_saldo,
                            colunas_para_remover,
                            nome_arquivo_excel,
                            pasta_armazenamento_output,
                        )

                        # Insere arquivo no drive
                        obs_processamento = upload_arquivo_drive(
                            caminho_local_planilha_com_saldo,
                            caminho_service_account,
                            id_pasta,
                            email_usuario,
                        )

                        # Preenche informações do output do processamento nas colunas com status de sucesso
                        condicao_linhas_saldo_sucesso = (
                            dados_para_processar["STATUS"] == "SUCESSO"
                        )
                        dados_para_processar.loc[
                            condicao_linhas_saldo_sucesso, "OBSERVAÇÃO"
                        ] = obs_processamento

                        instancia_log.info(
                            "Última linha e serviço de saldo > upload do output de saldo no drive"
                        )

                    if (ultima_linha and not condicao_para_retry) or (
                        contador_falhas_consecutivas >= max_qtd_falhas_consecutivas
                    ):
                        # Escreve output no excel
                        colunas_para_remover = [
                            "STATUS CERTIFICADO",
                            "POSICAO DO CERTIFICADO",
                            "ID PASTA DRIVE SALDO",
                            "ID PASTA DRIVE EXTRATO",
                            "ID PASTA DRIVE CHAVE",
                        ]
                        nome_arquivo_excel = "relatorio_execucao"
                        escrever_no_excel(
                            dados_para_processar,
                            colunas_para_remover,
                            nome_arquivo_excel,
                            pasta_armazenamento_relatorio_execucao,
                        )

                        qtd_linhas_sucesso = (
                            dados_para_processar["STATUS"] == "SUCESSO"
                        ).sum()
                        qtd_linhas_erro_previsto = (
                            dados_para_processar["STATUS"] == "ERRO PREVISTO"
                        ).sum()
                        qtd_linhas_erro_nao_previsto = (
                            dados_para_processar["STATUS"] == "ERRO NÃO PREVISTO"
                        ).sum()

                        # A quantidade de linhas processadas é a quantidade de linhas que possui algum status
                        qtd_linhas_processadas = (
                            qtd_linhas_sucesso
                            + qtd_linhas_erro_previsto
                            + qtd_linhas_erro_nao_previsto
                        )

                        # Escreve no arquivo de retorno
                        print(
                            f"Quantidade de linhas recebidas:{qtd_linhas_recebidas_para_processar},Quantidade de linhas processadas:{qtd_linhas_processadas},Sucesso:{qtd_linhas_sucesso},Erro previsto:{qtd_linhas_erro_previsto},Erro não previsto:{qtd_linhas_erro_nao_previsto}"
                        )
                        instancia_log.info(
                            "Última linha processada > Relatório da execução escrito"
                        )
                        instancia_log.info(
                            f"Quantidade de linhas recebidas:{qtd_linhas_recebidas_para_processar}/Quantidade de linhas processadas:{qtd_linhas_processadas}/Sucesso:{qtd_linhas_sucesso}/Erro previsto:{qtd_linhas_erro_previsto}/Erro não previsto:{qtd_linhas_erro_nao_previsto}"
                        )

                        # Fecha instancia do driver:
                        pagina_inicial.quit_driver()
                    else:
                        empresa_anterior = empresa

                    if not condicao_para_retry and (
                        contador_falhas_consecutivas >= max_qtd_falhas_consecutivas
                    ):
                        instancia_log.info(
                            f"A execução será interrompida porque a quantidade máxima de falhas consecutivas foi atingida, Quantidade de linhas não processadas: {condicao_linhas_nao_processadas_max_exc.sum()}"
                        )
                    elif not condicao_para_retry:
                        index_linha_valida = index_linha_valida + 1
                        instancia_log.info(
                            f"Se ainda existem linhas para processar > Ir para a próxima linha > index da próxima linha a ser processada: {index_linha_valida} "
                        )
                    else:
                        instancia_log.info("A linha será reprocessada")

                    condicao_para_executar = condicao_para_retry

    except Exception as e:
        instancia_log.error(str(e))
        sys.exit(1)
