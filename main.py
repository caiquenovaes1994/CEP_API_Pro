from fastapi import FastAPI, Header, HTTPException, Response, Query, Security, status
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
import xml.etree.ElementTree as ET
import xml.dom.minidom
from typing import Optional
import logging
from logging.handlers import TimedRotatingFileHandler
import datetime
import pybreaker
import redis.asyncio as redis
import json

class BRTFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
        return (dt - datetime.timedelta(hours=3)).timetuple()

logger = logging.getLogger("cep_api")
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler("cep_api.log", when="midnight", interval=1, backupCount=30, encoding="utf-8")
handler.setFormatter(BRTFormatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

api_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, socket_connect_timeout=1, socket_timeout=1)
CACHE_TTL = 2592000

async def get_cache(key: str):
    try:
        data = await redis_client.get(key)
        if data: return json.loads(data)
    except Exception as e:
        logger.error(f"Erro Redis ler: {e}")
    return None

async def set_cache(key: str, value: dict):
    try:
        await redis_client.setex(key, CACHE_TTL, json.dumps(value))
    except Exception as e:
        logger.error(f"Erro Redis salvar: {e}")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != "CEP_PRO_2026_KEY":
        logger.warning(f"Acesso negado: Chave de API inválida ({api_key})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acesso não autorizado. Chave de API (X-API-KEY) inválida ou ausente.",
        )
    return api_key

app = FastAPI(
    title="API de Busca de CEP", 
    description="API para buscar informações de endereços usando o CEP, suportando respostas em JSON e XML."
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@api_breaker
async def _viacep_request(cep_limpo: str) -> dict:
    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5.0)
    if res.status_code != 200:
        raise ValueError("Erro de comunicação com o provedor de CEP.")
    return res.json()

async def fetch_cep(cep: str) -> dict:
    cep_limpo = "".join(filter(str.isdigit, cep))
    if len(cep_limpo) != 8:
        raise ValueError("O CEP deve conter 8 dígitos numéricos.")
        
    cache_key = f"cep:{cep_limpo}"
    cached_data = await get_cache(cache_key)
    if cached_data:
        return cached_data

    try:
        data = await _viacep_request(cep_limpo)
    except pybreaker.CircuitBreakerError:
        logger.error("Circuit Breaker ABERTO para ViaCEP")
        raise ValueError("Serviço temporariamente indisponível. Tente novamente mais tarde.")
        
    if data.get("erro"):
        logger.warning(f"CEP não encontrado/404: {cep_limpo}")
        raise ValueError("CEP desativado ou não encontrado. Por favor, insira o CEP atualizado da rua.")
        
    await set_cache(cache_key, data)
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
    accept: Optional[str] = Header(None),
    api_key: str = Security(verify_api_key)
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

@api_breaker
async def _zippopotamus_request(country: str, postal: str) -> dict:
    async with httpx.AsyncClient() as client:
        res = await client.get(f"http://api.zippopotam.us/{country}/{postal}", timeout=5.0)
        if res.status_code == 200:
            return res.json()
    return None

@api_breaker
async def _nominatim_request(country: str, postal: str) -> dict:
    headers = {
        "User-Agent": "CEP_API_Pro_App/1.0",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
    }
    nominatim_url = f"https://nominatim.openstreetmap.org/search?postalcode={postal}&country={country}&format=json"
    async with httpx.AsyncClient() as client:
        res_nom = await client.get(nominatim_url, headers=headers, timeout=10.0)
        if res_nom.status_code == 200:
            return res_nom.json()
    return None

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

    cache_key = f"postal:{country}:{postal}"
    cached_data = await get_cache(cache_key)
    if cached_data:
        return cached_data

    # 1. Tentativa Primária: Zippopotam.us
    try:
        data = await _zippopotamus_request(country, postal)
        if data:
            await set_cache(cache_key, data)
            return data
    except pybreaker.CircuitBreakerError:
        logger.warning("Circuit Breaker ABERTO para Zippopotam.us")
    except Exception:
        pass
            
    # 2. Estratégia de Fallback: Nominatim (OpenStreetMap)
    try:
        data_nom = await _nominatim_request(country, postal)
        if data_nom and len(data_nom) > 0:
            place = data_nom[0]
            display_name = place.get("display_name", "")
            parts = [p.strip() for p in display_name.split(",")]
            place_name = parts[1] if len(parts) > 1 else (parts[0] if len(parts) > 0 else "Região Encontrada")
            state = parts[2] if len(parts) > 2 else ""
            
            result = {
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
            await set_cache(cache_key, result)
            return result
    except pybreaker.CircuitBreakerError:
        logger.warning("Circuit Breaker ABERTO para Nominatim")
    except Exception:
        pass
            
    logger.warning(f"Postal não encontrado/404: {country}-{postal}")
    raise ValueError("Código postal não encontrado ou país não suportado em nenhum dos provedores.")

@app.get("/api/postal/{country}/{postal}")
async def buscar_postal(
    country: str,
    postal: str,
    formato: Optional[str] = Query(None, description="Formato de saída: 'json' ou 'xml'"),
    accept: Optional[str] = Header(None),
    api_key: str = Security(verify_api_key)
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
