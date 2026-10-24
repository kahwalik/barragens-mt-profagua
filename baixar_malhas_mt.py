import os
import sys
import json
import requests

def baixar_malhas():
    diretorio = os.path.dirname(os.path.abspath(__file__))
    mapa_mun_path = os.path.join(diretorio, 'municipios_mt.json')
    
    mapa_mun = {}
    if os.path.exists(mapa_mun_path):
        with open(mapa_mun_path, 'r', encoding='utf-8') as f:
            mapa_mun = json.load(f)

    # 1. Baixar Municipios de MT (IBGE Malhas)
    url_mun = 'https://servicodados.ibge.gov.br/api/v3/malhas/estados/MT?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=intermediaria'
    print("Baixando malha municipal de Mato Grosso do IBGE...")
    resp_mun = requests.get(url_mun, timeout=60)
    resp_mun.raise_for_status()
    data_mun = resp_mun.json()

    # Enriquecer com os nomes dos municípios
    for feat in data_mun.get('features', []):
        cod = str(feat.get('properties', {}).get('codarea', '')).strip()
        nome = mapa_mun.get(cod, f"Município {cod}")
        feat['properties']['name'] = nome
        feat['properties']['municipio'] = nome
        feat['properties']['cod_ibge'] = cod

    path_mun_out = os.path.join(diretorio, 'malha_municipios_mt.geojson')
    with open(path_mun_out, 'w', encoding='utf-8') as f:
        json.dump(data_mun, f, ensure_ascii=False, indent=2)
    print(f"Malha municipal salva: {len(data_mun.get('features', []))} municípios em {path_mun_out}")

    # 2. Baixar Contorno Estadual de MT
    url_uf = 'https://servicodados.ibge.gov.br/api/v3/malhas/estados/MT?formato=application/vnd.geo+json&qualidade=intermediaria'
    print("Baixando limite do estado de Mato Grosso...")
    resp_uf = requests.get(url_uf, timeout=60)
    resp_uf.raise_for_status()
    data_uf = resp_uf.json()
    for feat in data_uf.get('features', []):
        feat['properties']['name'] = "Mato Grosso"

    path_uf_out = os.path.join(diretorio, 'limite_estado_mt.geojson')
    with open(path_uf_out, 'w', encoding='utf-8') as f:
        json.dump(data_uf, f, ensure_ascii=False, indent=2)
    print(f"Limite estadual salvo em {path_uf_out}")

if __name__ == '__main__':
    baixar_malhas()
