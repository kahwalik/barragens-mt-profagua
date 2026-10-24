# ==============================================================================
# PRODUTO TECNOLÓGICO PROFÁGUA / UNEMAT
# Diagnóstico e Triagem Normativa de Barragens (SIMCAR - MT)
# Autores: Kahwalik P. Medrado & Tadeu M. de Queiroz
# ==============================================================================

import os
import time
import pandas as pd
import numpy as np

def executar_diagnostico():
    inicio = time.time()
    
    diretorio = os.path.dirname(os.path.abspath(__file__))
    arquivo_csv = os.path.join(diretorio, "SIMCAR_D_RESERVATORIO_ARTIFICIAL.csv")
    arquivo_saida_csv = os.path.join(diretorio, "SIMCAR_BARRAGENS_DIAGNOSTICO_COMPLETO.csv")
    arquivo_resumo_excel = os.path.join(diretorio, "SIMCAR_RESUMO_EXECUTIVO_DIAGNOSTICO.xlsx")

    print(f"📂 Lendo base de dados do SIMCAR-MT ({arquivo_csv})...")
    
    # Carregar dados (usamos apenas as colunas necessárias para economizar memória e acelerar)
    cols = ['FID', 'ID', 'BASECORTE_ID', 'ZONA', 'BARRAMENTO', 'OBJETIVO', 
            'SITUACAO_ENTORNO', 'LARGURA_APP', 'NOME', 'AREA_HA', 'COD_IBGE']
    
    df = pd.read_csv(arquivo_csv, usecols=cols, low_memory=False)
    total_registros = len(df)
    print(f" Total de registros encontrados: {total_registros:,}")

    # Limpeza e conversão de tipos
    df['AREA_HA'] = pd.to_numeric(df['AREA_HA'], errors='coerce').fillna(0.0)
    df['LARGURA_APP'] = pd.to_numeric(df['LARGURA_APP'], errors='coerce').fillna(15.0)
    df['BARRAMENTO'] = df['BARRAMENTO'].fillna('N').astype(str).str.strip().str.upper()

    # 1. Filtro: Distinção entre Barramentos Efetivos e Outros Reservatórios Artificiais
    df['EH_BARRAMENTO'] = df['BARRAMENTO'] == 'S'
    total_barramentos = df['EH_BARRAMENTO'].sum()
    print(f"📊 Reservatórios identificados como Barramento (BARRAMENTO == 'S'): {total_barramentos:,} ({total_barramentos/total_registros*100:.1f}%)")

    # 2. Métricas Hidráulicas / Geométricas (Liebe et al., 2005)
    # Área da lâmina em m²
    df['AREA_M2'] = df['AREA_HA'] * 10000.0

    # Volume estimado em m³: V = 0.215 * A^1.18
    df['VOLUME_M3'] = np.where(df['AREA_M2'] > 0, 0.215 * (df['AREA_M2'] ** 1.18), 0.0)

    # Altura estimada em metros: H = (3 * V) / A
    df['ALTURA_M'] = np.where(df['AREA_M2'] > 0, (3.0 * df['VOLUME_M3']) / df['AREA_M2'], 0.0)

    # 3. Triagem Normativa (Lei Federal 12.334/2010 & IN SEMA/MT 02/2021)
    # Enquadramento PNSB: Altura >= 15m OU Volume >= 3.000.000 m³
    cond_enquadrada = (df['ALTURA_M'] >= 15.0) | (df['VOLUME_M3'] >= 3000000.0)
    cond_outorga = (~cond_enquadrada) & ((df['VOLUME_M3'] >= 1000000.0) | (df['AREA_HA'] >= 1.0))

    df['ENQUADRAMENTO'] = np.select(
        [cond_enquadrada, cond_outorga],
        ['Enquadrada na PNSB', 'Sujeita a Outorga/Cadastro SEMA'],
        default='Cadastro Simplificado / Dispensa SEMA'
    )

    df['CRI_TRIAGEM'] = np.select([cond_enquadrada, cond_outorga], ['ALTO', 'MÉDIO'], default='BAIXO')
    df['DPA_TRIAGEM'] = np.select([cond_enquadrada, cond_outorga], ['ALTO', 'MÉDIO'], default='BAIXO')
    df['EXIGE_PSB_PAE'] = np.select(
        [cond_enquadrada, cond_outorga],
        ['SIM (Exige PSB e PAE)', 'RECOMENDADO'],
        default='NÃO'
    )

    # 4. Exportação dos Dados Completos Processados em CSV
    print(f"💾 Salvando base completa processada ({arquivo_saida_csv})...")
    df.to_csv(arquivo_saida_csv, index=False)

    # 5. Criação do Resumo Executivo e Tabelas para a Dissertação / Produto Técnico
    print(f"📊 Gerando Resumo Executivo em Excel ({arquivo_resumo_excel})...")
    with pd.ExcelWriter(arquivo_resumo_excel, engine='openpyxl') as writer:
        # A. Resumo Geral por Enquadramento (Apenas Barramentos)
        df_barr = df[df['EH_BARRAMENTO']].copy()
        
        resumo_geral = df_barr.groupby('ENQUADRAMENTO').agg(
            QTD_BARRAGENS=('ID', 'count'),
            AREA_TOTAL_HA=('AREA_HA', 'sum'),
            AREA_MEDIA_HA=('AREA_HA', 'mean'),
            VOLUME_TOTAL_M3=('VOLUME_M3', 'sum'),
            ALTURA_MAX_M=('ALTURA_M', 'max'),
            ALTURA_MEDIA_M=('ALTURA_M', 'mean')
        ).reset_index()
        resumo_geral['%_DO_TOTAL'] = (resumo_geral['QTD_BARRAGENS'] / len(df_barr)) * 100
        resumo_geral.to_excel(writer, sheet_name="Resumo_Enquadramento", index=False)

        # B. Resumo por Município (COD_IBGE)
        resumo_mun = df_barr.groupby(['COD_IBGE', 'ENQUADRAMENTO']).size().unstack(fill_value=0)
        resumo_mun['TOTAL_BARRAGENS'] = resumo_mun.sum(axis=1)
        resumo_mun = resumo_mun.sort_values(by='TOTAL_BARRAGENS', ascending=False).reset_index()
        resumo_mun.to_excel(writer, sheet_name="Barragens_por_Municipio", index=False)

        # C. Top 50 Maiores Reservatórios de MT
        top50 = df_barr.sort_values(by='VOLUME_M3', ascending=False).head(50)[[
            'ID', 'COD_IBGE', 'ZONA', 'AREA_HA', 'VOLUME_M3', 'ALTURA_M', 
            'ENQUADRAMENTO', 'CRI_TRIAGEM', 'DPA_TRIAGEM', 'EXIGE_PSB_PAE'
        ]]
        top50.to_excel(writer, sheet_name="Top_50_Maiores_Barragens", index=False)

        # D. Estatísticas Descritivas
        stats = df_barr[['AREA_HA', 'VOLUME_M3', 'ALTURA_M']].describe().reset_index()
        stats.to_excel(writer, sheet_name="Estatisticas_Descritivas", index=False)

    tempo_total = round(time.time() - inicio, 2)
    print(f"\n✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO EM {tempo_total} SEGUNDOS!")
    print(f"📄 Arquivo CSV detalhado: {arquivo_saida_csv}")
    print(f"📊 Arquivo Excel executivo: {arquivo_resumo_excel}")

    print("\n--- SÍNTESE DO DIAGNÓSTICO ESTADUAL (SIMCAR-MT) ---")
    print(resumo_geral.to_string(index=False))

if __name__ == "__main__":
    executar_diagnostico()
