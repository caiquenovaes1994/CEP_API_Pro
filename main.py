from fastapi import FastAPI, Header, HTTPException, Response, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
import xml.etree.ElementTree as ET
import xml.dom.minidom
from typing import Optional

app = FastAPI(
    title="API de Busca de CEP", 
    description="API para buscar informações de endereços usando o CEP, suportando respostas em JSON e XML."
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

async def fetch_cep(cep: str) -> dict:
    # Remove caracteres não numéricos
    cep_limpo = "".join(filter(str.isdigit, cep))
    
    if len(cep_limpo) != 8:
        raise ValueError("O CEP deve conter 8 dígitos numéricos.")
        
    async with httpx.AsyncClient() as client:
        # Mantendo APENAS o ViaCEP por ser espelho estrito da base oficial dos Correios.
        # Fundamental para garantir a validade em sistemas de faturamento e emissão de NFs.
        res = await client.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5.0)
        
    if res.status_code != 200:
        raise ValueError("Erro de comunicação com o provedor de CEP.")
        
    data = res.json()
    if data.get("erro"):
        raise ValueError("CEP desativado ou não encontrado. Por favor, insira o CEP atualizado da rua.")
        
    return data

def dict_to_xml(data: dict, root_tag: str = "endereco") -> str:
    """Converte um dicionário para uma string XML, suportando aninhamento."""
    def build_xml(parent, data_dict):
        for key, value in data_dict.items():
            tag_name = key.replace(" ", "_")
            if isinstance(value, dict):
                child = ET.SubElement(parent, tag_name)
                build_xml(child, value)
            elif isinstance(value, list):
                for item in value:
                    child = ET.SubElement(parent, tag_name)
                    if isinstance(item, dict):
                        build_xml(child, item)
                    else:
                        child.text = str(item)
            else:
                child = ET.SubElement(parent, tag_name)
                child.text = str(value) if value is not None else ""

    root = ET.Element(root_tag)
    build_xml(root, data)
    
    ET.indent(root, space="  ", level=0)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

@app.get("/api/cep/{cep}")
async def buscar_cep(
    cep: str, 
    formato: Optional[str] = Query(None, description="Formato de saída: 'json' ou 'xml'"),
    accept: Optional[str] = Header(None)
):
    # Lógica para determinar se o usuário quer XML
    wants_xml = False
    if formato:
        wants_xml = formato.lower() == "xml"
    elif accept and "application/xml" in accept.lower() and "text/html" not in accept.lower():
        # Ignora application/xml se for um navegador padrão pedindo text/html
        wants_xml = True

    try:
        data = await fetch_cep(cep)
    except ValueError as e:
        if wants_xml:
            error_xml = dict_to_xml({"erro": str(e)}, "resultado")
            return Response(content=error_xml, media_type="application/xml", status_code=404)
        raise HTTPException(status_code=404, detail=str(e))
        
    if wants_xml:
        xml_content = dict_to_xml(data)
        return Response(content=xml_content, media_type="application/xml")
        
    return data

async def fetch_postal_internacional(country: str, postal: str) -> dict:
    country = country.lower().strip()
    postal = postal.strip()
    
    # Caso Especial: Hong Kong e Macau não possuem sistema de código postal. 
    # O código "999077" é um código fictício (placeholder) amplamente usado por transportadoras (como China Post/DHL) 
    # para forçar o preenchimento de formulários estrangeiros. Como não é real, ele não consta em bancos de dados geográficos.
    if postal == "999077" and country in ["hk", "cn"]:
        return {
            "post code": postal,
            "country": "Hong Kong" if country == "hk" else "China",
            "country abbreviation": country.upper(),
            "places": [
                {
                    "place name": "Hong Kong (Special Administrative Region)",
                    "state": "Kowloon / HK Island",
                    "state abbreviation": "HK",
                    "latitude": "22.3193",
                    "longitude": "114.1694"
                }
            ]
        }

    # 1. Tentativa Primária: Zippopotam.us
    async with httpx.AsyncClient() as client:
        res = await client.get(f"http://api.zippopotam.us/{country}/{postal}")
        if res.status_code == 200:
            return res.json()
            
    # 2. Estratégia de Fallback: Nominatim (OpenStreetMap)
    # Útil para países não suportados (ex: Costa Rica) ou postais não encontrados.
    headers = {
        "User-Agent": "CEP_API_Pro_App/1.0",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
    }
    nominatim_url = f"https://nominatim.openstreetmap.org/search?postalcode={postal}&country={country}&format=json"
    
    async with httpx.AsyncClient() as client:
        try:
            res_nom = await client.get(nominatim_url, headers=headers, timeout=10.0)
            if res_nom.status_code == 200:
                data = res_nom.json()
                if data and len(data) > 0:
                    place = data[0]
                    display_name = place.get("display_name", "")
                    
                    # O "display_name" do OpenStreetMap costuma ser uma string separada por vírgulas. Ex: "10101, Carmen, San José, Costa Rica"
                    parts = [p.strip() for p in display_name.split(",")]
                    
                    # Vamos tentar extrair local e estado sem quebrar
                    place_name = parts[1] if len(parts) > 1 else (parts[0] if len(parts) > 0 else "Região Encontrada")
                    state = parts[2] if len(parts) > 2 else ""
                    
                    # Simulamos a mesma estrutura JSON do Zippopotam.us para garantir a compatibilidade total com nosso Frontend!
                    return {
                        "post code": postal,
                        "country": parts[-1] if len(parts) > 0 else country.upper(),
                        "country abbreviation": country.upper(),
                        "places": [
                            {
                                "place name": place_name,
                                "state": state,
                                "state abbreviation": "",
                                "latitude": place.get("lat", ""),
                                "longitude": place.get("lon", "")
                            }
                        ]
                    }
        except Exception:
            pass # Se o Nominatim falhar (ex: timeout da rede), deixamos prosseguir para o erro genérico.
            
    raise ValueError("Código postal não encontrado ou país não suportado em nenhum dos provedores.")

@app.get("/api/postal/{country}/{postal}")
async def buscar_postal(
    country: str,
    postal: str,
    formato: Optional[str] = Query(None, description="Formato de saída: 'json' ou 'xml'"),
    accept: Optional[str] = Header(None)
):
    wants_xml = False
    if formato:
        wants_xml = formato.lower() == "xml"
    elif accept and "application/xml" in accept.lower() and "text/html" not in accept.lower():
        wants_xml = True

    try:
        data = await fetch_postal_internacional(country, postal)
    except ValueError as e:
        if wants_xml:
            error_xml = dict_to_xml({"erro": str(e)}, "resultado")
            return Response(content=error_xml, media_type="application/xml", status_code=404)
        raise HTTPException(status_code=404, detail=str(e))
        
    if wants_xml:
        xml_content = dict_to_xml(data, root_tag="resultado")
        return Response(content=xml_content, media_type="application/xml")
        
    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
