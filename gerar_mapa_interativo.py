# ==============================================================================
# PRODUTO TECNOLÓGICO PROFÁGUA / UNEMAT
# Geração do Mapa Interativo HTML de Barragens do SIMCAR-MT
# Autores: Kahwalik P. Medrado & Tadeu M. de Queiroz
# ==============================================================================

import os
import sys
import csv
import json
import folium
from folium.plugins import MarkerCluster, Fullscreen

# Aumentar o limite de tamanho de campo do CSV para suportar geometrias grandes
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2147483647)

def extrair_coordenada_aprox(geom_wkt):
    """Extrai uma coordenada (lat, lon) representativa do texto WKT do polígono."""
    if not geom_wkt or 'POLYGON' not in geom_wkt:
        return None, None
    try:
        # Formato: POLYGON ((-55.351062 -12.052562, ...))
        coords_part = geom_wkt.split('((')[1].split(')')[0]
        first_pair = coords_part.split(',')[0].strip().split()
        lon = float(first_pair[0])
        lat = float(first_pair[1])
        # Validação de limites geográficos para o Estado de Mato Grosso
        if -63.5 <= lon <= -49.0 and -19.5 <= lat <= -6.0:
            return lat, lon
    except Exception:
        pass
    return None, None

def carregar_malhas_e_estatisticas(diretorio, mapa_mun, csv_diag):
    """Carrega as malhas de municípios e do estado de MT com estatísticas calculadas."""
    path_mun = os.path.join(diretorio, 'malha_municipios_mt.geojson')
    path_uf = os.path.join(diretorio, 'limite_estado_mt.geojson')

    # Calcular contagens por município a partir do CSV de diagnóstico
    stats = {}
    if os.path.exists(csv_diag):
        with open(csv_diag, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('EH_BARRAMENTO') != 'True':
                    continue
                cod = str(row.get('COD_IBGE', '')).split('.')[0].strip()
                if cod not in stats:
                    stats[cod] = {'total': 0, 'pnsb': 0, 'outorga': 0, 'dispensa': 0}
                stats[cod]['total'] += 1
                enq = row.get('ENQUADRAMENTO', '')
                if enq == 'Enquadrada na PNSB':
                    stats[cod]['pnsb'] += 1
                elif enq == 'Sujeita a Outorga/Cadastro SEMA':
                    stats[cod]['outorga'] += 1
                else:
                    stats[cod]['dispensa'] += 1

    geo_mun = None
    if os.path.exists(path_mun):
        with open(path_mun, 'r', encoding='utf-8') as f:
            geo_mun = json.load(f)
        for feat in geo_mun.get('features', []):
            cod = str(feat.get('properties', {}).get('codarea', '')).strip()
            nome = mapa_mun.get(cod, feat.get('properties', {}).get('name', f"Município {cod}"))
            s = stats.get(cod, {'total': 0, 'pnsb': 0, 'outorga': 0, 'dispensa': 0})
            feat['properties']['name'] = nome
            feat['properties']['municipio'] = nome
            feat['properties']['cod_ibge'] = cod
            feat['properties']['total_barragens'] = s['total']
            feat['properties']['pnsb_barragens'] = s['pnsb']
            feat['properties']['outorga_barragens'] = s['outorga']
            feat['properties']['dispensa_barragens'] = s['dispensa']

    geo_uf = None
    if os.path.exists(path_uf):
        with open(path_uf, 'r', encoding='utf-8') as f:
            geo_uf = json.load(f)

    return geo_mun, geo_uf

def gerar_mapa():
    diretorio = os.path.dirname(os.path.abspath(__file__))
    csv_original = os.path.join(diretorio, "SIMCAR_D_RESERVATORIO_ARTIFICIAL.csv")
    csv_diag = os.path.join(diretorio, "SIMCAR_BARRAGENS_DIAGNOSTICO_COMPLETO.csv")
    json_mun = os.path.join(diretorio, "municipios_mt.json")
    mapa_saida = os.path.join(diretorio, "MAPA_INTERATIVO_BARRAGENS_MT.html")

    print("📖 Carregando dicionário oficial de municípios...")
    mapa_mun = {}
    if os.path.exists(json_mun):
        with open(json_mun, 'r', encoding='utf-8') as f:
            mapa_mun = json.load(f)

    print("🏛️ Carregando malhas territoriais de Mato Grosso e limites municipais...")
    geo_mun, geo_uf = carregar_malhas_e_estatisticas(diretorio, mapa_mun, csv_diag)

    print("🔍 Lendo coordenadas do arquivo SIMCAR original...")
    coords = {}
    with open(csv_original, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fid = row.get('FID')
            geom = row.get('GEOMETRY')
            lat, lon = extrair_coordenada_aprox(geom)
            if lat and lon:
                coords[fid] = (lat, lon)

    print(f"  Coordenadas extraídas com sucesso para {len(coords):,} reservatórios.")

    print("🗺️ Inicializando mapa centrado no Estado de Mato Grosso...")
    # Cria o mapa centrado em Mato Grosso
    m = folium.Map(
        location=[-12.95, -55.90],
        zoom_start=6,
        tiles=None,
        control_scale=True
    )

    # -------------------------------------------------------------------------
    # 1. CAMADAS DE MAPAS DE FUNDO (BASEMAPS)
    # -------------------------------------------------------------------------
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='🌐 OpenStreetMap (Padrão)',
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Topo Map',
        name='🏔️ Relevo Topográfico & Hidrografia (Esri Topo)',
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='🛰️ Imagem de Satélite de Alta Resolução (Esri)',
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Street Map',
        name='🗺️ Mapa Rodoviário & Urbano (Esri Street)',
        control=True
    ).add_to(m)

    Fullscreen(
        position='topleft',
        title='Expandir em Tela Cheia',
        title_cancel='Sair da Tela Cheia',
        force_separate_button=True
    ).add_to(m)

    # -------------------------------------------------------------------------
    # 2. CAMADA DO CONTORNO ESTADUAL DE MATO GROSSO
    # -------------------------------------------------------------------------
    if geo_uf:
        camada_estado = folium.FeatureGroup(name="🗺️ Contorno Estadual de Mato Grosso", show=True)
        folium.GeoJson(
            geo_uf,
            style_function=lambda feature: {
                'fillColor': 'transparent',
                'color': '#0f172a',
                'weight': 3.5,
                'opacity': 0.95
            },
            name="Limite MT"
        ).add_to(camada_estado)
        camada_estado.add_to(m)

    # -------------------------------------------------------------------------
    # 3. CAMADA DOS LIMITES DOS MUNICÍPIOS DE MATO GROSSO
    # -------------------------------------------------------------------------
    if geo_mun:
        camada_municipios = folium.FeatureGroup(name="🏛️ Limites dos Municípios de MT (141 Municípios - IBGE)", show=True)

        def style_municipio(feat):
            return {
                'fillColor': '#3b82f6',
                'fillOpacity': 0.04,
                'color': '#1d4ed8',
                'weight': 1.2,
                'dashArray': '2, 3'
            }

        def highlight_municipio(feat):
            return {
                'fillColor': '#f59e0b',
                'fillOpacity': 0.35,
                'color': '#b45309',
                'weight': 2.8,
                'dashArray': ''
            }

        tooltip_mun = folium.GeoJsonTooltip(
            fields=['municipio', 'cod_ibge', 'total_barragens', 'pnsb_barragens', 'outorga_barragens'],
            aliases=['Município:', 'Código IBGE:', 'Total de Barragens:', '🚨 Barragens PNSB (Alto Porte):', '🟡 Sujeitas a Outorga:'],
            localize=True,
            sticky=True,
            labels=True,
            style="""
                background-color: #ffffff;
                color: #1f2937;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
                padding: 10px 14px;
                border: 2px solid #2563eb;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            """
        )

        popup_mun = folium.GeoJsonPopup(
            fields=['municipio', 'cod_ibge', 'total_barragens', 'pnsb_barragens', 'outorga_barragens', 'dispensa_barragens'],
            aliases=['Município:', 'Cód. IBGE:', 'Total Barramentos:', '🚨 Barragens PNSB:', '🟡 Sujeitas a Outorga:', '🟢 Dispensa/Simplificado:'],
            localize=True,
            labels=True,
            style="font-family: sans-serif; font-size: 13px; width: 250px;"
        )

        folium.GeoJson(
            geo_mun,
            style_function=style_municipio,
            highlight_function=highlight_municipio,
            tooltip=tooltip_mun,
            popup=popup_mun,
            name="Limites Municipais MT"
        ).add_to(camada_municipios)
        camada_municipios.add_to(m)

    # -------------------------------------------------------------------------
    # 4. CAMADAS DAS BARRAGENS
    # -------------------------------------------------------------------------
    print("📊 Lendo base de diagnóstico e distribuindo feições de barragens...")
    camada_pnsb = folium.FeatureGroup(name="🚨 Barragens Enquadradas na PNSB (ALTO RISCO - PSB/PAE)", show=True)
    cluster_outorga = MarkerCluster(name="🟡 Barragens Sujeitas a Outorga/Cadastro SEMA (MÉDIO PORTE)", show=True)

    qtd_pnsb = 0
    qtd_outorga = 0

    with open(csv_diag, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('EH_BARRAMENTO') != 'True':
                continue
            
            fid = row.get('FID')
            enquadramento = row.get('ENQUADRAMENTO')
            if fid not in coords:
                continue

            lat, lon = coords[fid]
            area = float(row.get('AREA_HA', 0))
            vol = float(row.get('VOLUME_M3', 0))
            alt = float(row.get('ALTURA_M', 0))
            municipio_cod = str(row.get('COD_IBGE', '')).split('.')[0].strip()
            nome_cidade = mapa_mun.get(municipio_cod, f"IBGE {municipio_cod}")
            id_barr = row.get('ID', '')

            # 4.1 BARRAGENS PNSB (ALTO RISCO - EXIGÊNCIA DE PSB/PAE)
            if enquadramento == 'Enquadrada na PNSB':
                qtd_pnsb += 1
                popup_html = f"""
                <div style="font-family: Arial, sans-serif; width: 280px; font-size: 13px;">
                    <div style="background-color: #dc2626; color: white; padding: 8px 10px; border-radius: 6px 6px 0 0;">
                        <h4 style="margin: 0; font-size: 14px;">🚨 Barragem PNSB (Alto Porte)</h4>
                        <small style="opacity: 0.9;">Lei Federal nº 12.334/2010</small>
                    </div>
                    <div style="padding: 10px; border: 1px solid #dc2626; border-top: none; border-radius: 0 0 6px 6px; background-color: #fffafa;">
                        <b>ID SIMCAR:</b> {id_barr}<br>
                        <b>Município:</b> {nome_cidade}<br>
                        <b>Área da Lâmina:</b> {area:,.2f} ha<br>
                        <b>Volume Estimado:</b> {vol:,.0f} m³<br>
                        <b>Altura Estimada:</b> {alt:.2f} m<br>
                        <hr style="margin: 6px 0; border: none; border-top: 1px solid #fca5a5;">
                        <b>CRI / DPA (Triagem):</b> <span style="color:#b91c1c; font-weight:bold;">ALTO / ALTO</span><br>
                        <b>Obrigatoriedade:</b> <span style="color:#dc2626; font-weight:bold;">PSB e PAE Obrigatórios</span>
                    </div>
                </div>
                """
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=9,
                    color="#991b1b",
                    weight=2,
                    fill=True,
                    fill_color="#ef4444",
                    fill_opacity=0.9,
                    popup=folium.Popup(popup_html, max_width=320),
                    tooltip=f"🚨 PNSB | {nome_cidade} - ID {id_barr} ({vol/1e6:,.2f}M m³ | {alt:.1f}m)"
                ).add_to(camada_pnsb)

            # 4.2 BARRAGENS SUJEITAS A OUTORGA (SEMA)
            elif enquadramento == 'Sujeita a Outorga/Cadastro SEMA':
                qtd_outorga += 1
                popup_html = f"""
                <div style="font-family: Arial, sans-serif; width: 220px; font-size: 12px;">
                    <div style="background-color: #d97706; color: white; padding: 5px 8px; border-radius: 4px 4px 0 0; font-weight: bold;">
                        ⚠️ Outorga / Cadastro SEMA
                    </div>
                    <div style="padding: 8px; border: 1px solid #d97706; border-top: none; border-radius: 0 0 4px 4px; background: #fffbeb;">
                        <b>ID SIMCAR:</b> {id_barr}<br>
                        <b>Município:</b> {nome_cidade}<br>
                        <b>Área:</b> {area:,.2f} ha<br>
                        <b>Volume:</b> {vol:,.0f} m³<br>
                        <b>Altura:</b> {alt:.2f} m
                    </div>
                </div>
                """
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=5,
                    color="#b45309",
                    weight=1,
                    fill=True,
                    fill_color="#f59e0b",
                    fill_opacity=0.75,
                    popup=folium.Popup(popup_html, max_width=260),
                    tooltip=f"{nome_cidade} | ID {id_barr} ({area:.1f} ha | {vol:,.0f} m³)"
                ).add_to(cluster_outorga)

    camada_pnsb.add_to(m)
    cluster_outorga.add_to(m)

    # -------------------------------------------------------------------------
    # 5. CONTROLE DE CAMADAS
    # -------------------------------------------------------------------------
    folium.LayerControl(collapsed=False, position='topright').add_to(m)

    # -------------------------------------------------------------------------
    # 6. LEGENDA & PAINEL FLUTUANTE
    # -------------------------------------------------------------------------
    titulo_html = f'''
    <div style="position: fixed; 
                bottom: 24px; left: 24px; width: 380px; z-index:9999;
                background-color: rgba(255, 255, 255, 0.96); backdrop-filter: blur(4px);
                border: 2px solid #1e3a8a; border-radius: 12px;
                padding: 14px 18px; box-shadow: 0 8px 24px rgba(0,0,0,0.25);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="font-size: 24px; margin-right: 10px;">🌊</div>
            <div>
                <h4 style="margin: 0; color: #1e3a8a; font-size: 15px; font-weight: 700;">PROFÁGUA / UNEMAT</h4>
                <div style="font-size: 11px; color: #475569; font-weight: 500;">Triagem Normativa de Barragens (SIMCAR - MT)</div>
            </div>
        </div>
        <hr style="margin: 6px 0 10px 0; border: none; border-top: 1px solid #cbd5e1;">
        
        <div style="font-size: 12px; color: #1e293b; line-height: 1.6;">
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="display: inline-block; width: 14px; height: 14px; background: #ef4444; border: 2px solid #991b1b; border-radius: 50%; margin-right: 8px;"></span>
                <b>{qtd_pnsb} Barragens PNSB</b> &nbsp;<span style="color:#dc2626; font-size:11px;">(Alto Risco / PSB e PAE)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="display: inline-block; width: 14px; height: 14px; background: #f59e0b; border: 2px solid #b45309; border-radius: 50%; margin-right: 8px;"></span>
                <b>{qtd_outorga:,} Barragens Outorga SEMA</b> &nbsp;<span style="color:#d97706; font-size:11px;">(Agrupadas)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="display: inline-block; width: 18px; height: 4px; background: #2563eb; border: 1px dashed #1e40af; margin-right: 8px;"></span>
                <b>Limites Municipais de MT</b> &nbsp;<span style="color:#64748b; font-size:11px;">(141 Municípios)</span>
            </div>
            <div style="display: flex; align-items: center;">
                <span style="display: inline-block; width: 18px; height: 4px; background: #0f172a; margin-right: 8px;"></span>
                <b>Limite Estadual de MT</b>
            </div>
        </div>
        
        <div style="margin-top: 10px; padding-top: 6px; border-top: 1px dashed #cbd5e1; font-size: 10.5px; color: #64748b; display: flex; justify-content: space-between;">
            <span>Autores: <b>K. P. Medrado & T. M. Queiroz</b></span>
            <span>Mato Grosso</span>
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(titulo_html))

    print(f"💾 Salvando mapa interativo enriquecido em: {mapa_saida}...")
    m.save(mapa_saida)
    tamanho_mb = os.path.getsize(mapa_saida) / (1024 * 1024)
    print(f"✅ MAPA INTERATIVO GERADO COM SUCESSO! ({tamanho_mb:.2f} MB)")

if __name__ == "__main__":
    gerar_mapa()
