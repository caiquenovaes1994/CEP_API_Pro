from fastapi import FastAPI, Header, HTTPException, Response, Query, Security, status, Request
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
import xml.etree.ElementTree as ET
from typing import Optional
import logging
import datetime
import pybreaker
import redis.asyncio as redis
import json
import os



class BRTFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
        return (dt - datetime.timedelta(hours=3)).timetuple()

# Configuração de logs diretamente em arquivos datados (sem arquivo base independente)
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Define o nome do arquivo com a data de hoje no formato solicitado: cep_api_AAAA-MM-DD.log
today_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3)).strftime("%Y-%m-%d")
log_filename = os.path.join(LOG_DIR, f"cep_api_{today_date}.log")


# Limpa ABSOLUTAMENTE todos os handlers existentes para evitar arquivos fantasmas e duplicidade
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).handlers = []
logging.getLogger().handlers = []

logger = logging.getLogger("cep_api")
logger.setLevel(logging.INFO)

# Handler direto para o arquivo datado
handler = logging.FileHandler(log_filename, encoding="utf-8")
handler.setFormatter(BRTFormatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

logger.info(f"Sistema de logs iniciado. Gravando diretamente em: {log_filename}")



# Força a remoção de qualquer arquivo genérico residual na pasta logs
legacy_log = os.path.join(LOG_DIR, "cep_api.log")
if os.path.exists(legacy_log):
    try:
        # Se o arquivo estiver vazio ou for o resíduo indesejado, tenta apagar
        os.remove(legacy_log)
    except:
        # Se estiver em uso, o sistema apenas ignora (provável log de acesso do uvicorn)
        pass


# Lógica de retenção: Remove arquivos com mais de 30 dias
try:
    now = datetime.datetime.now()
    for f in os.listdir(LOG_DIR):
        if f.startswith("cep_api_") and f.endswith(".log"):
            f_path = os.path.join(LOG_DIR, f)
            f_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(f_path))
            if (now - f_mtime).days > 30:
                os.remove(f_path)
except Exception as e:

    # Erro na limpeza não deve travar a API
    pass



# Configuração de Circuit Breakers independentes para cada serviço
viacep_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)
brasilapi_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)
zippopotamus_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)
nominatim_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)

# Redis com timeout agressivo para não travar a API se o cache estiver offline
redis_client = redis.Redis(
    host='localhost', 
    port=6379, 
    db=0, 
    decode_responses=True, 
    socket_connect_timeout=0.1, # 100ms
    socket_timeout=0.1          # 100ms
)
redis_available = True

CACHE_TTL = 2592000

async def get_cache(key: str):
    global redis_available
    if not redis_available: return None
    try:
        data = await redis_client.get(key)
        if data: return json.loads(data)
    except Exception as e:
        logger.error(f"Erro Redis ler: {e}. Desativando cache temporariamente.")
        redis_available = False
    return None

async def set_cache(key: str, value: dict):
    global redis_available
    if not redis_available: return
    try:
        await redis_client.setex(key, CACHE_TTL, json.dumps(value))
    except Exception as e:
        logger.error(f"Erro Redis salvar: {e}. Desativando cache temporariamente.")
        redis_available = False

# Mapeamento completo de países para logs e respostas precisas

COUNTRY_NAMES = {
    "af": "Afeganistão", "za": "África do Sul", "al": "Albânia", "de": "Alemanha", "ad": "Andorra", 
    "ao": "Angola", "ag": "Antígua e Barbuda", "sa": "Arábia Saudita", "dz": "Argélia", "ar": "Argentina", 
    "am": "Armênia", "au": "Austrália", "at": "Áustria", "az": "Azerbaijão", "bs": "Bahamas", 
    "bh": "Bahrein", "bd": "Bangladesh", "bb": "Barbados", "be": "Bélgica", "bz": "Belize", 
    "bj": "Benim", "by": "Bielorrússia", "bo": "Bolívia", "ba": "Bósnia e Herzegovina", "bw": "Botsuana", 
    "br": "Brasil", "bn": "Brunei", "bg": "Bulgária", "bf": "Burquina Faso", "bi": "Burundi", 
    "bt": "Butão", "cv": "Cabo Verde", "cm": "Camarões", "kh": "Camboja", "ca": "Canadá", 
    "qa": "Catar", "kz": "Cazaquistão", "td": "Chade", "cl": "Chile", "cn": "China", 
    "cy": "Chipre", "co": "Colômbia", "km": "Comores", "cg": "Congo", "cd": "Congo (Rep. Dem.)", 
    "kp": "Coreia do Norte", "kr": "Coreia do Sul", "ci": "Costa do Marfim", "cr": "Costa Rica", "hr": "Croácia", 
    "cu": "Cuba", "dk": "Dinamarca", "dj": "Djibuti", "dm": "Dominica", "eg": "Egito", 
    "sv": "El Salvador", "ae": "Emirados Árabes Unidos", "ec": "Equador", "er": "Eritreia", "sk": "Eslováquia", 
    "si": "Eslovênia", "es": "Espanha", "us": "Estados Unidos", "ee": "Estônia", "sz": "Eswatini", 
    "et": "Etiópia", "fj": "Fiji", "ph": "Filipinas", "fi": "Finlândia", "fr": "França", 
    "ga": "Gabão", "gm": "Gâmbia", "gh": "Gana", "ge": "Geórgia", "gd": "Granada", 
    "gr": "Grécia", "gt": "Guatemala", "gy": "Guiana", "gn": "Guiné", "gq": "Guiné Equatorial", 
    "gw": "Guiné-Bissau", "ht": "Haiti", "hn": "Honduras", "hk": "Hong Kong", "hu": "Hungria", 
    "ye": "Iêmen", "mh": "Ilhas Marshall", "sb": "Ilhas Salomão", "in": "Índia", "id": "Indonésia", 
    "ir": "Irã", "iq": "Iraque", "ie": "Irlanda", "is": "Islândia", "il": "Israel", 
    "it": "Itália", "jm": "Jamaica", "jp": "Japão", "jo": "Jordânia", "ki": "Kiribati", 
    "kw": "Kuwait", "ls": "Lesoto", "lv": "Letônia", "lb": "Líbano", "lr": "Libéria", 
    "ly": "Líbia", "li": "Liechtenstein", "lt": "Lituânia", "lu": "Luxemburgo", "mk": "Macedônia do Norte", 
    "mg": "Madagascar", "my": "Malásia", "mw": "Malaui", "mv": "Maldivas", "ml": "Mali", 
    "mt": "Malta", "ma": "Marrocos", "mu": "Maurício", "mr": "Mauritânia", "mx": "México", 
    "mm": "Mianmar", "fm": "Micronésia", "mz": "Moçambique", "md": "Moldávia", "mc": "Mônaco", 
    "mn": "Mongólia", "me": "Montenegro", "na": "Namíbia", "nr": "Nauru", "np": "Nepal", 
    "ni": "Nicarágua", "ne": "Níger", "ng": "Nigéria", "no": "Noruega", "nz": "Nova Zelândia", 
    "om": "Omã", "nl": "Países Baixos", "pw": "Palau", "pa": "Panamá", "pg": "Papua-Nova Guiné", 
    "pk": "Paquistão", "py": "Paraguai", "pe": "Peru", "pl": "Polônia", "pt": "Portugal", 
    "ke": "Quênia", "kg": "Quirguistão", "gb": "Reino Unido", "cf": "República Centro-Africana", "do": "República Dominicana", 
    "cz": "República Tcheca", "ro": "Romênia", "rw": "Ruanda", "ru": "Rússia", "ws": "Samoa", 
    "sm": "San Marino", "lc": "Santa Lúcia", "kn": "São Cristóvão e Névis", "st": "São Tomé e Príncipe", "vc": "São Vicente e Granadinas", 
    "sn": "Senegal", "sl": "Serra Leoa", "rs": "Sérvia", "sc": "Seychelles", "sg": "Singapura", 
    "sy": "Síria", "so": "Somália", "lk": "Sri Lanka", "sd": "Sudão", "ss": "Sudão do Sul", 
    "se": "Suécia", "ch": "Suíça", "sr": "Suriname", "th": "Tailândia", "tw": "Taiwan", 
    "tj": "Tajiquistão", "tz": "Tanzânia", "tg": "Togo", "to": "Tonga", "tt": "Trinidad e Tobago", 
    "tn": "Tunísia", "tm": "Turcomenistão", "tr": "Turquia", "tv": "Tuvalu", "ua": "Ucrânia", 
    "ug": "Uganda", "uy": "Uruguai", "uz": "Uzbequistão", "vu": "Vanuatu", "va": "Vaticano", 
    "ve": "Venezuela", "vn": "Vietnã", "zm": "Zâmbia", "zw": "Zimbábue"
}


def get_country_name(code: str) -> str:
    return COUNTRY_NAMES.get(code.lower(), code.upper())

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def verify_api_key(request: Request, api_key: str = Security(api_key_header)):


    # Bypass de segurança para Same-Origin (requisições vindas do nosso próprio frontend)
    referer = request.headers.get("referer")
    host = request.headers.get("host")
    
    if referer and host and host in referer:
        return api_key

    expected_key = os.getenv("CEP_API_KEY", "CEP_PRO_9A4BF2E17D8C5B6A_2026_SECURE")
    if api_key != expected_key:
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

@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.png", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.png")

@brasilapi_breaker
async def _brasilapi_request(cep_limpo: str) -> Optional[dict]:
    """Tenta buscar o CEP via BrasilAPI (Geralmente mais rápido)."""
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"https://brasilapi.com.br/api/cep/v1/{cep_limpo}", timeout=3.0)
            if res.status_code == 200:
                data = res.json()
                # Normaliza para o formato esperado pelo frontend (ViaCEP)
                return {
                    "cep": f"{data['cep'][:5]}-{data['cep'][5:]}" if "-" not in data['cep'] else data['cep'],
                    "logradouro": data.get("street") or "",
                    "complemento": "",
                    "bairro": data.get("neighborhood") or "",
                    "localidade": data.get("city") or "",
                    "uf": data.get("state") or "",
                    "ibge": "",
                    "gia": "",
                    "ddd": "",
                    "siafi": "",
                    "fonte": "brasilapi"
                }
        except Exception as e:
            logger.error(f"Erro BrasilAPI: {e}")
    return None

@viacep_breaker
async def _viacep_request(cep_limpo: str) -> dict:
    """Tenta buscar o CEP via ViaCEP."""
    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5.0)
    if res.status_code != 200:
        raise ValueError("Erro de comunicação com o provedor ViaCEP.")
    data = res.json()
    if data.get("erro"):
        return data
    data["fonte"] = "viacep"
    return data


async def fetch_cep(cep: str) -> dict:
    cep_limpo = "".join(filter(str.isdigit, cep))
    if len(cep_limpo) != 8:
        raise ValueError("O CEP deve conter 8 dígitos numéricos.")
        
    cache_key = f"cep:{cep_limpo}"
    cached_data = await get_cache(cache_key)
    if cached_data:
        return cached_data

    # 1. Tentativa Primária: BrasilAPI
    try:
        data = await _brasilapi_request(cep_limpo)
        if data:
            await set_cache(cache_key, data)
            return data
    except pybreaker.CircuitBreakerError:
        logger.warning(f"Circuit Breaker ABERTO para BrasilAPI ao buscar CEP: {cep_limpo}")
    except Exception as e:
        logger.error(f"Falha na tentativa BrasilAPI para CEP {cep_limpo}: {e}")


    # 2. Tentativa Secundária (Fallback): ViaCEP
    try:
        data = await _viacep_request(cep_limpo)
    except pybreaker.CircuitBreakerError:
        logger.error(f"Circuit Breaker ABERTO para ViaCEP ao buscar CEP: {cep_limpo}")
        raise ValueError(f"Serviços de CEP indisponíveis para o CEP {cep_limpo}. Tente novamente mais tarde.")
    except Exception as e:
        logger.error(f"Falha na tentativa ViaCEP para CEP {cep_limpo}: {e}")
        raise ValueError(f"Erro ao obter dados para o CEP {cep_limpo} nos provedores.")


        
    if data.get("erro"):
        logger.warning(f"CEP não encontrado/404: {cep_limpo} (Brasil)")
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
    logger.info(f"Requisição CEP: {cep} | Formato: {formato or 'JSON'}")

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

@zippopotamus_breaker
async def _zippopotamus_request(country: str, postal: str) -> dict:
    async with httpx.AsyncClient() as client:
        res = await client.get(f"http://api.zippopotam.us/{country}/{postal}", timeout=5.0)
        if res.status_code == 200:
            return res.json()
    return None

@nominatim_breaker
async def _nominatim_request(country: str, postal: str) -> dict:
    headers = {
        "User-Agent": "CEP_API_Pro/1.0",
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
        logger.warning(f"Circuit Breaker ABERTO para Zippopotam.us ao buscar Postal: {country}-{postal}")
    except Exception as e:
        logger.error(f"Erro inesperado Zippopotamus para {country}-{postal}: {e}")

            
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
        logger.warning(f"Circuit Breaker ABERTO para Nominatim ao buscar Postal: {country}-{postal}")
    except Exception as e:
        logger.error(f"Erro inesperado Nominatim para {country}-{postal}: {e}")

            
    country_name = get_country_name(country)
    logger.warning(f"Postal não encontrado/404: {postal} ({country_name})")
    raise ValueError(f"Código postal não encontrado ou país ({country_name}) não suportado.")


@app.get("/api/postal/{country}/{postal}")
async def buscar_postal(
    country: str,
    postal: str,
    formato: Optional[str] = Query(None, description="Formato de saída: 'json' ou 'xml'"),
    accept: Optional[str] = Header(None),
    api_key: str = Security(verify_api_key)
):
    logger.info(f"Requisição Postal Internacional: {country}/{postal} | Formato: {formato or 'JSON'}")

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
