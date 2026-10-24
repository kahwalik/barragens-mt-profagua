# ==============================================================================
# PRODUTO TECNOLÓGICO PROFÁGUA / UNEMAT
# Dashboard Interativo para Triagem e Diagnóstico de Barragens (SIMCAR - MT)
# Autores: Kahwalik P. Medrado & Tadeu M. de Queiroz
# ==============================================================================

import os
import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Diagnóstico de Barragens SIMCAR-MT | PROFÁGUA UNEMAT",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Caminhos dos arquivos
DIRETORIO = os.path.dirname(os.path.abspath(__file__))
CSV_DIAG = os.path.join(DIRETORIO, "SIMCAR_BARRAGENS_DIAGNOSTICO_COMPLETO.csv")
CSV_DIAG_GZ = os.path.join(DIRETORIO, "SIMCAR_BARRAGENS_DIAGNOSTICO_COMPLETO.csv.gz")
if os.path.exists(CSV_DIAG_GZ) and (not os.path.exists(CSV_DIAG) or os.path.getsize(CSV_DIAG_GZ) > 0):
    CSV_DIAG = CSV_DIAG_GZ
JSON_MUN = os.path.join(DIRETORIO, "municipios_mt.json")
MAPA_HTML = os.path.join(DIRETORIO, "MAPA_INTERATIVO_BARRAGENS_MT.html")

@st.cache_data
def carregar_dados():
    # Carregar dicionário oficial de municípios do IBGE
    mapa_mun = {}
    if os.path.exists(JSON_MUN):
        with open(JSON_MUN, 'r', encoding='utf-8') as f:
            mapa_mun = json.load(f)

    cols = ['ID', 'COD_IBGE', 'ZONA', 'BARRAMENTO', 'LARGURA_APP', 
            'AREA_HA', 'VOLUME_M3', 'ALTURA_M', 'ENQUADRAMENTO', 
            'CRI_TRIAGEM', 'DPA_TRIAGEM', 'EXIGE_PSB_PAE', 'EH_BARRAMENTO']
    df = pd.read_csv(CSV_DIAG, usecols=cols, low_memory=False)
    
    # Filtrar apenas barramentos efetivos
    df_barr = df[df['EH_BARRAMENTO'] == True].copy()
    
    # Mapear código IBGE para o Nome do Município
    # Tratamento caso o código venha com .0 ou como float
    def obter_nome_mun(cod):
        if pd.isna(cod):
            return "Não Identificado"
        cod_limpo = str(cod).split('.')[0].strip()
        return mapa_mun.get(cod_limpo, f"Município {cod_limpo}")

    df_barr['MUNICIPIO'] = df_barr['COD_IBGE'].apply(obter_nome_mun)
    return df_barr

# Cabeçalho Principal
st.markdown("""
<div style="background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 10px; color: white; margin-bottom: 25px;">
    <h1 style="margin: 0; font-size: 28px;">🌊 Sistema de Triagem Normativa e Diagnóstico de Barragens</h1>
    <h3 style="margin: 5px 0 0 0; font-size: 16px; font-weight: normal; opacity: 0.9;">
        Produto Tecnológico - Mestrado Profissional em Rede Nacional em Gestão e Regulação de Recursos Hídricos (PROFÁGUA / UNEMAT)
    </h3>
    <p style="margin: 8px 0 0 0; font-size: 13px; opacity: 0.8;">
        <b>Autores:</b> Kahwalik P. Medrado & Tadeu M. de Queiroz | Base Normativa: <b>Lei Federal 12.334/2010</b> & <b>IN SEMA/MT 02/2021</b>
    </p>
</div>
""", unsafe_allow_html=True)

try:
    df_total = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar base de dados processada: {e}")
    st.stop()

# --- BARRA LATERAL COM FILTROS ---
st.sidebar.header("🔍 Filtros de Consulta")

# Filtro de Enquadramento
opcoes_enquadramento = ["Todos"] + sorted(list(df_total['ENQUADRAMENTO'].unique()))
sel_enquadramento = st.sidebar.selectbox("Enquadramento Normativo:", opcoes_enquadramento)

# Filtro de Município pelo NOME
opcoes_mun = ["Todos"] + sorted([m for m in df_total['MUNICIPIO'].unique() if m != "Não Identificado"])
sel_mun = st.sidebar.selectbox("Município de Mato Grosso:", opcoes_mun)

# Filtro por Faixa de Área
min_ha, max_ha = float(df_total['AREA_HA'].min()), float(df_total['AREA_HA'].max())
faixa_area = st.sidebar.slider("Área da Lâmina (Hectares):", min_value=0.0, max_value=min(100.0, max_ha), value=(0.0, 100.0), step=0.5)

# Aplicação dos Filtros
df_filtrado = df_total.copy()
if sel_enquadramento != "Todos":
    df_filtrado = df_filtrado[df_filtrado['ENQUADRAMENTO'] == sel_enquadramento]

if sel_mun != "Todos":
    df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'] == sel_mun]

df_filtrado = df_filtrado[(df_filtrado['AREA_HA'] >= faixa_area[0]) & (df_filtrado['AREA_HA'] <= faixa_area[1])]

# --- SEÇÃO DE ACESSO PELO CELULAR (SIDEBAR) ---
st.sidebar.markdown("---")
st.sidebar.subheader("📱 Acesso pelo Celular")
qr_path = os.path.join(DIRETORIO, "qr_code_celular.png")
if os.path.exists(qr_path):
    st.sidebar.image(qr_path, caption="Aponte a câmera do celular", use_container_width=True)
st.sidebar.markdown("""
<div style="font-size: 11.5px; color: #334155; background: #f1f5f9; padding: 8px 10px; border-radius: 6px; border: 1px solid #cbd5e1;">
<b>Endereço no Celular:</b><br>
<code style="font-size: 12px; color: #0284c7;">http://172.16.114.66:8501</code><br>
<span style="font-size: 10.5px; color: #64748b;">(O celular deve estar conectado na mesma rede Wi-Fi)</span>
</div>
""", unsafe_allow_html=True)

# --- CARDS DE MÉTRICAS (KPIs) ---
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_barr = len(df_filtrado)
vol_total = df_filtrado['VOLUME_M3'].sum()
area_total = df_filtrado['AREA_HA'].sum()
qtd_pnsb = (df_filtrado['ENQUADRAMENTO'] == 'Enquadrada na PNSB').sum()

kpi1.metric("Total de Barragens", f"{total_barr:,}")
kpi2.metric("Volume Acumulado Estimado", f"{vol_total/1e6:,.1f} M m³")
kpi3.metric("Área Total Inundada", f"{area_total:,.1f} ha")
kpi4.metric("Barragens na PNSB (Alto Porte)", f"{qtd_pnsb:,}", delta="Exigem PSB/PAE" if qtd_pnsb > 0 else None)

st.markdown("---")

# --- ABAS DE ANÁLISE ---
aba_graficos, aba_mapa, aba_tabela, aba_metodologia = st.tabs([
    "📊 Gráficos & Estatísticas", 
    "🗺️ Mapa Interativo Geoespacial", 
    "📋 Tabela Completa & Download", 
    "📖 Metodologia & Normas"
])

with aba_graficos:
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("Distribuição por Enquadramento Regulatório")
        df_enq = df_filtrado['ENQUADRAMENTO'].value_counts().reset_index()
        df_enq.columns = ['Enquadramento', 'Quantidade']
        fig_pie = px.pie(
            df_enq, values='Quantidade', names='Enquadramento',
            color='Enquadramento',
            color_discrete_map={
                'Enquadrada na PNSB': '#d9534f',
                'Sujeita a Outorga/Cadastro SEMA': '#f0ad4e',
                'Cadastro Simplificado / Dispensa SEMA': '#5cb85c'
            },
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        st.subheader("Top 10 Municípios com Mais Barragens")
        df_top_mun = df_filtrado['MUNICIPIO'].value_counts().head(10).reset_index()
        df_top_mun.columns = ['Município', 'Qtd Barragens']
        fig_bar = px.bar(
            df_top_mun, x='Qtd Barragens', y='Município',
            orientation='h', color='Qtd Barragens',
            color_continuous_scale='Blues',
            text='Qtd Barragens'
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        fig_bar.update_traces(textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Relação entre Área da Lâmina (ha) e Altura Estimada do Maciço (m)")
    sample_size = min(3000, len(df_filtrado))
    df_sample = df_filtrado.sample(sample_size, random_state=42) if len(df_filtrado) > sample_size else df_filtrado
    fig_scatter = px.scatter(
        df_sample, x='AREA_HA', y='ALTURA_M',
        color='ENQUADRAMENTO',
        size='VOLUME_M3',
        hover_data=['ID', 'MUNICIPIO', 'VOLUME_M3'],
        color_discrete_map={
            'Enquadrada na PNSB': '#d9534f',
            'Sujeita a Outorga/Cadastro SEMA': '#f0ad4e',
            'Cadastro Simplificado / Dispensa SEMA': '#5cb85c'
        },
        labels={'AREA_HA': 'Área da Lâmina d’Água (ha)', 'ALTURA_M': 'Altura Estimada do Maciço (m)', 'MUNICIPIO': 'Município'}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with aba_mapa:
    st.subheader("🗺️ Mapa Geoespacial Interativo - Barragens de Mato Grosso (SIMCAR)")
    st.markdown("""
    Explore a distribuição geográfica dos barramentos com o **contorno do Estado de Mato Grosso**, os **limites dos 141 municípios (IBGE)** 
    e a localização das barragens auditadas.
    - 🚨 **Vermelho:** Barragens Enquadradas na PNSB (Alto Porte / Alto Risco - Exigem PSB e PAE).
    - 🟡 **Laranja/Âmbar:** Barragens Sujeitas a Outorga/Cadastro SEMA (Médio Porte).
    - 🏛️ **Limites Municipais:** Passe o cursor para inspecionar estatísticas e limites territoriais de cada município.
    """)

    col_m1, col_m2 = st.columns([3, 1])
    with col_m2:
        if os.path.exists(MAPA_HTML):
            with open(MAPA_HTML, 'rb') as f_map:
                st.download_button(
                    label="📥 Baixar Mapa HTML Completo",
                    data=f_map,
                    file_name="MAPA_INTERATIVO_BARRAGENS_MT.html",
                    mime="text/html",
                    use_container_width=True
                )

    if os.path.exists(MAPA_HTML):
        with open(MAPA_HTML, 'r', encoding='utf-8') as f_map:
            html_data = f_map.read()
        components.html(html_data, height=720, scrolling=True)
    else:
        st.info("O mapa interativo ainda não foi gerado. Execute 'python gerar_mapa_interativo.py' para criá-lo.")

with aba_tabela:
    st.subheader("Listagem Individual de Barragens")
    cols_tabela = ['ID', 'MUNICIPIO', 'AREA_HA', 'VOLUME_M3', 'ALTURA_M', 'ENQUADRAMENTO', 'CRI_TRIAGEM', 'DPA_TRIAGEM', 'EXIGE_PSB_PAE']
    st.dataframe(
        df_filtrado[cols_tabela].head(1000),
        use_container_width=True
    )
    
    csv_bytes = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Dados Filtrados em CSV",
        data=csv_bytes,
        file_name="SIMCAR_Barragens_Filtradas.csv",
        mime="text/csv"
    )

with aba_metodologia:
    st.markdown("""
    ### 📚 Fundamentação Metodológica do Produto Tecnológico
    
    1. **Origem dos Dados:**
       * Base de dados geoespaciais declaratórios do **SIMCAR-MT (SEMA/MT)** - Camada `SIMCAR_D_RESERVATORIO_ARTIFICIAL`.
       * Total de feições auditadas: **168.193 reservatórios**, dos quais **68.647 são barramentos efetivos** (`BARRAMENTO == 'S'`).
    
    2. **Relação Hidráulica e Estimativa de Volume:**
       * Aplicação da equação cota-área-volume de **Liebe et al. (2005)**:
         $$V = 0{,}215 \\times A^{1{,}18}$$
         Onde $V$ é o volume ($m^3$) e $A$ é a área do espelho d'água ($m^2$).
       * Altura estimada do barramento com modelo cônico/piramidal:
         $$H = \\frac{3 \\times V}{A}$$
    
    3. **Critérios de Enquadramento Normativo:**
       * **Lei Federal nº 12.334/2010** (alterada pela Lei nº 14.066/2020) e **Instrução Normativa SEMA/MT nº 02/2021**:
         * *Enquadrada na PNSB:* Estruturas com $H \\ge 15\\text{ m}$ **OU** $V \\ge 3.000.000\\text{ m}^3$. Exigência imediata de Plano de Segurança da Barragem (PSB) e Plano de Ação de Emergência (PAE).
         * *Sujeita a Outorga/Cadastro SEMA:* $V \\ge 1.000.000\\text{ m}^3$ ou área $\\ge 1\\text{ ha}$.
         * *Cadastro Simplificado:* Estruturas de menor impacto com processo declaratório simplificado.
    
    ---
    **Desenvolvido como Produto Tecnológico do PROFÁGUA / UNEMAT**  
    *Autores: Kahwalik P. Medrado & Tadeu M. de Queiroz*
    """)
