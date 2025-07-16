import pandas as pd
from pathlib import Path

from POM.page_objects.page_objects import Page
from POM.elementos.elementos_pagina_extrato_fgts import ExtratoFgts
from auxiliar import gerar_pdf
from registrador_logs import instancia_log

class PaginaExtratoFgts(Page):
    """
    Classe que representa a página onde o extrato fgts é gerado
    """

    extrato_fgts = ExtratoFgts()

    def extrair_saldo(
        self, df_output_saldo: pd.DataFrame, index_linha: int, lista_indice_data: list, retorno: str
    ) -> pd.DataFrame:
        """
        Extrai saldo fgts e atualiza numa planilha de output do saldo

        Ags:
            df_output_saldo (pd.DataFrame): dataframe no qual vai ser adicionado a informação de saldo extraida da tela
            index_linha (int): index da linha do dataframe na qual vai ser adicionada a informação de saldo extraida da tela
        """
        try:
            # Recupera saldo
            coluna_saldo_base = "SALDO"
            if retorno == "Não localizado":
                saldo = ["Não localizado"]
            else:
                saldo = self.extrato_fgts.recuperar_informacao_saldo(lista_indice_data, timeout=5)
                instancia_log.info(f"Saldo recuperado: {saldo}")

            # Adiciona os saldos às colunas correspondentes
            for i, saldo_individual in enumerate(saldo):
                coluna_atual = coluna_saldo_base if i == 0 else f"{coluna_saldo_base} {i + 1}"
                df_output_saldo.at[index_linha, coluna_atual] = saldo_individual if saldo_individual != "Não localizado" else saldo_individual

            return df_output_saldo
        except Exception as e:
            instancia_log.error(e)
            etapa = "extração do saldo"
            msg_erro = f"Erro não previsto na etapa de: {etapa}"
            raise Exception(msg_erro)

    def gerar_extrato_fgts(
        self, pasta_armazenamento: Path, nome_colaborador: str, nome_colaborador_original: str, lista_indice_data: list
    ) -> list:
        """
        Tira print da tela do extrato e salva o pdf

        Ags:
            pasta_armazenamento (Path): pasta onde vai ser armazenado o arquivo png com o print da dela e também o arquivo pdf que vai ser gerado a partir da imagem
            nome_colaborador (str): nome do colocaborados para o qual o extrato está sendo gerado
        """
        try:
           return self.extrato_fgts.gerar_imagem_extrato_fgts(
               screenshot_path=pasta_armazenamento,
               lista_indice_data=lista_indice_data,
               pasta_armazenamento=pasta_armazenamento,
               nome_colaborador=nome_colaborador,
               nome_colaborador_original=nome_colaborador_original,
               timeout=10,
           )
        except Exception as e:
            instancia_log.error(e)
            etapa = "geração do extrato fgts"
            msg_erro = f"Erro não previsto na etapa de: {etapa}"
            raise Exception(msg_erro)
