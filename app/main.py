import flet as ft
import httpx
import json
from cachetools import TTLCache
import pybreaker
import logging
from logging.handlers import TimedRotatingFileHandler
import datetime

class BRTFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
        return (dt - datetime.timedelta(hours=3)).timetuple()

import xml.etree.ElementTree as ET

I18N = {
    "pt": {
        "title_br": "Busca CEP", "title_intl": "Busca Postal Code",
        "br": "Brasil", "intl": "Internacional",
        "cep_label": "Digite o CEP (somente números)",
        "country_label": "Selecione o País",
        "postal_label": "Digite o Postal Code",
        "btn_search": "Buscar Endereço",
        "address": "Endereço", "details": "Detalhes",
        "raw_data": "Dados brutos:",
    },
    "en": {
        "title_br": "Zip Code Search", "title_intl": "Search Postal Code",
        "br": "Brazil", "intl": "International",
        "cep_label": "Enter Zip Code (numbers only)",
        "country_label": "Select Country",
        "postal_label": "Enter Postal Code",
        "btn_search": "Search Address",
        "address": "Address", "details": "Details",
        "raw_data": "Raw data:",
    },
    "es": {
        "title_br": "Búsqueda Postal", "title_intl": "Búsqueda Código Postal",
        "br": "Brasil", "intl": "Internacional",
        "cep_label": "Ingrese el CEP (solo números)",
        "country_label": "Seleccionar País",
        "postal_label": "Ingrese el Código Postal",
        "btn_search": "Buscar Dirección",
        "address": "Dirección", "details": "Detalles",
        "raw_data": "Datos sin procesar:",
    }
}

logger = logging.getLogger("cep_app")
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler("cep_app.log", when="midnight", interval=1, backupCount=30, encoding="utf-8")
handler.setFormatter(BRTFormatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

cache = TTLCache(maxsize=1000, ttl=2592000)
app_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)

@app_breaker
async def _perform_request(url, is_br, val, fmt):
    headers = {"X-API-KEY": "CEP_PRO_2026_KEY"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=5.0)
            if response.status_code == 404:
                raise ValueError("Não encontrado.")
            return response.json() if fmt == "json" else response.text
        except ValueError:
            raise
        except Exception:
            if is_br:
                res = await client.get(f"https://viacep.com.br/ws/{val}/json/", timeout=5.0)
                if res.status_code != 200 or res.json().get("erro"):
                    raise ValueError("CEP não encontrado.")
                return res.json()
            else: 
                raise ValueError("API offline e fallback não suportado para internacional.")

# --- Configurações de Design (Alinhadas com o Web Pro) ---
PRIMARY_COLOR = "#6366f1"
BG_COLOR = "#0f172a"
SURFACE_COLOR = "#1e293b"
SURFACE_BORDER = "#334155"
TEXT_MAIN = "#f8fafc"
TEXT_MUTED = "#94a3b8"

# Lista de Países (Extraída do index.html)
COUNTRIES = [
    {"code": "af", "name": "Afeganistão"}, {"code": "za", "name": "África do Sul"},
    {"code": "al", "name": "Albânia"}, {"code": "de", "name": "Alemanha"},
    {"code": "ad", "name": "Andorra"}, {"code": "ao", "name": "Angola"},
    {"code": "ag", "name": "Antígua e Barbuda"}, {"code": "sa", "name": "Arábia Saudita"},
    {"code": "dz", "name": "Argélia"}, {"code": "ar", "name": "Argentina"},
    {"code": "am", "name": "Armênia"}, {"code": "au", "name": "Austrália"},
    {"code": "at", "name": "Áustria"}, {"code": "az", "name": "Azerbaijão"},
    {"code": "bs", "name": "Bahamas"}, {"code": "bh", "name": "Bahrein"},
    {"code": "bd", "name": "Bangladesh"}, {"code": "bb", "name": "Barbados"},
    {"code": "be", "name": "Bélgica"}, {"code": "bz", "name": "Belize"},
    {"code": "bj", "name": "Benim"}, {"code": "by", "name": "Bielorrússia"},
    {"code": "bo", "name": "Bolívia"}, {"code": "ba", "name": "Bósnia e Herzegovina"},
    {"code": "bw", "name": "Botsuana"}, {"code": "br", "name": "Brasil"},
    {"code": "bn", "name": "Brunei"}, {"code": "bg", "name": "Bulgária"},
    {"code": "bf", "name": "Burquina Faso"}, {"code": "bi", "name": "Burundi"},
    {"code": "bt", "name": "Butão"}, {"code": "cv", "name": "Cabo Verde"},
    {"code": "cm", "name": "Camarões"}, {"code": "kh", "name": "Camboja"},
    {"code": "ca", "name": "Canadá"}, {"code": "qa", "name": "Catar"},
    {"code": "kz", "name": "Cazaquistão"}, {"code": "td", "name": "Chade"},
    {"code": "cl", "name": "Chile"}, {"code": "cn", "name": "China"},
    {"code": "cy", "name": "Chipre"}, {"code": "co", "name": "Colômbia"},
    {"code": "km", "name": "Comores"}, {"code": "cg", "name": "Congo"},
    {"code": "cd", "name": "Congo (DR)"}, {"code": "kp", "name": "Coreia do Norte"},
    {"code": "kr", "name": "Coreia do Sul"}, {"code": "ci", "name": "Costa do Marfim"},
    {"code": "cr", "name": "Costa Rica"}, {"code": "hr", "name": "Croácia"},
    {"code": "cu", "name": "Cuba"}, {"code": "dk", "name": "Dinamarca"},
    {"code": "dj", "name": "Djibuti"}, {"code": "dm", "name": "Dominica"},
    {"code": "eg", "name": "Egito"}, {"code": "sv", "name": "El Salvador"},
    {"code": "ae", "name": "E. Árabes Unidos"}, {"code": "ec", "name": "Equador"},
    {"code": "er", "name": "Eritreia"}, {"code": "sk", "name": "Eslováquia"},
    {"code": "si", "name": "Eslovênia"}, {"code": "es", "name": "Espanha"},
    {"code": "us", "name": "Estados Unidos"}, {"code": "ee", "name": "Estônia"},
    {"code": "sz", "name": "Eswatini"}, {"code": "et", "name": "Etiópia"},
    {"code": "fj", "name": "Fiji"}, {"code": "ph", "name": "Filipinas"},
    {"code": "fi", "name": "Finlândia"}, {"code": "fr", "name": "França"},
    {"code": "ga", "name": "Gabão"}, {"code": "gm", "name": "Gâmbia"},
    {"code": "gh", "name": "Gana"}, {"code": "ge", "name": "Geórgia"},
    {"code": "gd", "name": "Granada"}, {"code": "gr", "name": "Grécia"},
    {"code": "gt", "name": "Guatemala"}, {"code": "gy", "name": "Guiana"},
    {"code": "gn", "name": "Guiné"}, {"code": "gq", "name": "Guiné Equatorial"},
    {"code": "gw", "name": "Guiné-Bissau"}, {"code": "ht", "name": "Haiti"},
    {"code": "hn", "name": "Honduras"}, {"code": "hk", "name": "Hong Kong"},
    {"code": "hu", "name": "Hungria"}, {"code": "ye", "name": "Iêmen"},
    {"code": "mh", "name": "Ilhas Marshall"}, {"code": "sb", "name": "Ilhas Salomão"},
    {"code": "in", "name": "Índia"}, {"code": "id", "name": "Indonésia"},
    {"code": "ir", "name": "Irã"}, {"code": "iq", "name": "Iraque"},
    {"code": "ie", "name": "Irlanda"}, {"code": "is", "name": "Islândia"},
    {"code": "il", "name": "Israel"}, {"code": "it", "name": "Itália"},
    {"code": "jm", "name": "Jamaica"}, {"code": "jp", "name": "Japão"},
    {"code": "jo", "name": "Jordânia"}, {"code": "ki", "name": "Kiribati"},
    {"code": "kw", "name": "Kuwait"}, {"code": "ls", "name": "Lesoto"},
    {"code": "lv", "name": "Letônia"}, {"code": "lb", "name": "Líbano"},
    {"code": "lr", "name": "Libéria"}, {"code": "ly", "name": "Líbia"},
    {"code": "li", "name": "Liechtenstein"}, {"code": "lt", "name": "Lituânia"},
    {"code": "lu", "name": "Luxemburgo"}, {"code": "mk", "name": "Macedônia"},
    {"code": "mg", "name": "Madagascar"}, {"code": "my", "name": "Malásia"},
    {"code": "mw", "name": "Malaui"}, {"code": "mv", "name": "Maldivas"},
    {"code": "ml", "name": "Mali"}, {"code": "mt", "name": "Malta"},
    {"code": "ma", "name": "Marrocos"}, {"code": "mu", "name": "Maurício"},
    {"code": "mr", "name": "Mauritânia"}, {"code": "mx", "name": "México"},
    {"code": "mm", "name": "Mianmar"}, {"code": "fm", "name": "Micronésia"},
    {"code": "mz", "name": "Moçambique"}, {"code": "md", "name": "Moldávia"},
    {"code": "mc", "name": "Mônaco"}, {"code": "mn", "name": "Mongólia"},
    {"code": "me", "name": "Montenegro"}, {"code": "na", "name": "Namíbia"},
    {"code": "nr", "name": "Nauru"}, {"code": "np", "name": "Nepal"},
    {"code": "ni", "name": "Nicarágua"}, {"code": "ne", "name": "Níger"},
    {"code": "ng", "name": "Nigéria"}, {"code": "no", "name": "Noruega"},
    {"code": "nz", "name": "N. Zelândia"}, {"code": "om", "name": "Omã"},
    {"code": "nl", "name": "P. Baixos"}, {"code": "pw", "name": "Palau"},
    {"code": "pa", "name": "Panamá"}, {"code": "pg", "name": "P. Nova Guiné"},
    {"code": "pk", "name": "Paquistão"}, {"code": "py", "name": "Paraguai"},
    {"code": "pe", "name": "Peru"}, {"code": "pl", "name": "Polônia"},
    {"code": "pt", "name": "Portugal"}, {"code": "ke", "name": "Quênia"},
    {"code": "kg", "name": "Quirguistão"}, {"code": "gb", "name": "Reino Unido"},
    {"code": "cf", "name": "Rep. Centro-Africana"}, {"code": "do", "name": "Rep. Dominicana"},
    {"code": "cz", "name": "Rep. Tcheca"}, {"code": "ro", "name": "Romênia"},
    {"code": "rw", "name": "Ruanda"}, {"code": "ru", "name": "Rússia"},
    {"code": "ws", "name": "Samoa"}, {"code": "sm", "name": "San Marino"},
    {"code": "lc", "name": "Santa Lúcia"}, {"code": "kn", "name": "S. Cristóvão e Névis"},
    {"code": "st", "name": "S. Tomé e Príncipe"}, {"code": "vc", "name": "S. Vicente"},
    {"code": "sn", "name": "Senegal"}, {"code": "sl", "name": "Serra Leoa"},
    {"code": "rs", "name": "Sérvia"}, {"code": "sc", "name": "Seychelles"},
    {"code": "sg", "name": "Singapura"}, {"code": "sy", "name": "Síria"},
    {"code": "so", "name": "Somália"}, {"code": "lk", "name": "Sri Lanka"},
    {"code": "sd", "name": "Sudão"}, {"code": "ss", "name": "Sudão do Sul"},
    {"code": "se", "name": "Suécia"}, {"code": "ch", "name": "Suíça"},
    {"code": "sr", "name": "Suriname"}, {"code": "th", "name": "Tailândia"},
    {"code": "tw", "name": "Taiwan"}, {"code": "tj", "name": "Tajiquistão"},
    {"code": "tz", "name": "Tanzânia"}, {"code": "tg", "name": "Togo"},
    {"code": "to", "name": "Tonga"}, {"code": "tt", "name": "Trinidad e Tobago"},
    {"code": "tn", "name": "Tunísia"}, {"code": "tm", "name": "Turcomenistão"},
    {"code": "tr", "name": "Turquia"}, {"code": "tv", "name": "Tuvalu"},
    {"code": "ua", "name": "Ucrânia"}, {"code": "ug", "name": "Uganda"},
    {"code": "uy", "name": "Uruguai"}, {"code": "uz", "name": "Uzbequistão"},
    {"code": "vu", "name": "Vanuatu"}, {"code": "va", "name": "Vaticano"},
    {"code": "ve", "name": "Venezuela"}, {"code": "vn", "name": "Vietnã"},
    {"code": "zm", "name": "Zâmbia"}, {"code": "zw", "name": "Zimbábue"}
]
COUNTRIES.sort(key=lambda x: x["name"])

class CEPApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_tab = "br"
        self.selected_country = {"code": "us", "name": "Estados Unidos"}
        self.setup_page()
        self.init_ui()

    def setup_page(self):
        self.page.title = "CEP API Pro"
        self.page.theme_mode = "dark"
        self.page.bgcolor = BG_COLOR
        self.page.padding = 0
        self.page.window_width = 450
        self.page.window_height = 850
        self.page.fonts = {
            "Inter": "https://github.com/google/fonts/raw/main/ofl/inter/Inter-VariableFont_slnt%2Cwght.ttf"
        }
        self.page.theme = ft.Theme(font_family="Inter")
        
        self.lang = "pt"
        self.lang_btn = ft.PopupMenuButton(
            content=ft.Row([
                ft.Image(src="https://flagcdn.com/w20/br.png", width=20, height=15, border_radius=2),
                ft.Text("PT", color=TEXT_MAIN, size=14, weight="bold")
            ], spacing=5, alignment="center"),
            items=[
                ft.PopupMenuItem(content=ft.Row([ft.Image(src="https://flagcdn.com/w20/br.png", width=20, height=15), ft.Text("PT")]), on_click=lambda _: self.change_lang("pt")),
                ft.PopupMenuItem(content=ft.Row([ft.Image(src="https://flagcdn.com/w20/gb.png", width=20, height=15), ft.Text("EN")]), on_click=lambda _: self.change_lang("en")),
                ft.PopupMenuItem(content=ft.Row([ft.Image(src="https://flagcdn.com/w20/es.png", width=20, height=15), ft.Text("ES")]), on_click=lambda _: self.change_lang("es"))
            ]
        )
        self.page.appbar = ft.AppBar(
            title=ft.Text("CEP API Pro", color=TEXT_MAIN, size=16),
            bgcolor=BG_COLOR,
            actions=[ft.Container(content=self.lang_btn, padding=ft.Padding(0, 0, 10, 0))]
        )

    def init_ui(self):
        # Logo e Título
        self.logo = ft.Image(src="icon.png", width=120, height=120, fit="contain")
        self.title_text = ft.Text("Busca CEP", size=28, weight="bold", text_align="center", color=TEXT_MAIN)

        # Tabs Customizadas
        self.btn_br = ft.Container(
            content=ft.Text("Brasil", weight="bold", color="white"),
            padding=ft.Padding.symmetric(vertical=12, horizontal=20),
            border_radius=10, bgcolor=PRIMARY_COLOR, expand=True, alignment=ft.Alignment.CENTER,
            on_click=lambda _: self.change_tab("br")
        )
        self.btn_intl = ft.Container(
            content=ft.Text("Internacional", weight="bold", color=TEXT_MUTED),
            padding=ft.Padding.symmetric(vertical=12, horizontal=20),
            border_radius=10, bgcolor="transparent", expand=True, alignment=ft.Alignment.CENTER,
            on_click=lambda _: self.change_tab("intl")
        )
        self.tabs_row = ft.Container(
            content=ft.Row([self.btn_br, self.btn_intl], spacing=5),
            bgcolor="rgba(15, 23, 42, 0.4)", padding=5, border_radius=12, border=ft.Border.all(1, SURFACE_BORDER),
        )

        # Campos de Input
        self.cep_input = ft.TextField(
            label="Digite o CEP (somente números)", hint_text="Ex: 01001-000",
            bgcolor="rgba(15, 23, 42, 0.6)", border_color=SURFACE_BORDER,
            focused_border_color=PRIMARY_COLOR, border_radius=12, on_submit=self.handle_search
        )

        # Seletor de País Customizado (com bandeira Real)
        self.country_selector = ft.Container(
            content=ft.Row([
                ft.Image(src=f"https://flagcdn.com/w40/{self.selected_country['code']}.png", width=24, height=18, border_radius=2),
                ft.Text(self.selected_country["name"], color=TEXT_MAIN, expand=True),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=TEXT_MUTED)
            ]),
            padding=15,
            border=ft.Border.all(1, SURFACE_BORDER),
            border_radius=12,
            bgcolor="rgba(15, 23, 42, 0.6)",
            on_click=self.open_country_picker,
            visible=False
        )

        self.postal_input = ft.TextField(
            label="Digite o Postal Code", hint_text="Ex: 90210",
            bgcolor="rgba(15, 23, 42, 0.6)", border_color=SURFACE_BORDER,
            focused_border_color=PRIMARY_COLOR, border_radius=12, visible=False, on_submit=self.handle_search
        )

        # Seletor de Formato
        self.format_radio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="json", label="JSON"),
                ft.Radio(value="xml", label="XML"),
            ], alignment="center", spacing=20),
            value="json"
        )

        # Botão de Busca
        self.search_btn = ft.ElevatedButton(
            content=ft.Text("Buscar Endereço", color="white", weight="bold"),
            bgcolor=PRIMARY_COLOR, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            height=50, width=float("inf"), on_click=self.handle_search
        )

        self.loader = ft.Container(
            content=ft.ProgressRing(color=TEXT_MAIN, width=24, height=24),
            visible=False, alignment=ft.Alignment.CENTER,
        )

        # Resultados
        self.result_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("📍", size=40),
                    ft.Column([
                        ft.Text("Endereço", weight="bold", size=20, color=TEXT_MAIN, key="title"),
                        ft.Text("Detalhes", size=14, color=TEXT_MUTED, key="subtitle")
                    ], spacing=2, expand=True)
                ])
            ], spacing=10),
            bgcolor="rgba(99, 102, 241, 0.15)", border=ft.Border.all(1, "rgba(139, 92, 246, 0.3)"),
            padding=20, border_radius=15, visible=False,
        )

        self.raw_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Dados brutos:", weight="bold", color=TEXT_MAIN),
                    ft.IconButton(ft.Icons.COPY, on_click=self.copy_to_clipboard, icon_color=TEXT_MUTED)
                ], alignment="spaceBetween"),
                ft.Container(
                    content=ft.Text("", font_family="monospace", size=12, color="#e2e8f0", key="text"),
                    padding=15, bgcolor="rgba(15, 23, 42, 0.8)", border_radius=10, border=ft.Border.all(1, SURFACE_BORDER),
                )
            ]),
            visible=False,
        )

        # Footer
        self.footer = ft.Column([
            ft.Text("Desenvolvido por Caique Novaes | © 2026 | v2.0.0", size=12, color=TEXT_MAIN, weight="bold"),
            ft.Text('"Simplificando a geolocalização global, um código postal de cada vez."', size=11, color=TEXT_MUTED, italic=True, text_align="center"),
            ft.Row([
                ft.TextButton("GitHub", on_click=self.open_github),
                ft.Text("|", color=TEXT_MUTED),
                ft.TextButton("E-mail", on_click=self.open_email),
            ], alignment="center", spacing=5)
        ], horizontal_alignment="center", spacing=10)

        # Layout
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(height=20),
                    ft.Container(self.logo, alignment=ft.Alignment.CENTER),
                    ft.Container(self.title_text, alignment=ft.Alignment.CENTER, margin=ft.Margin.only(bottom=20)),
                    self.tabs_row,
                    ft.Container(height=20),
                    self.cep_input,
                    self.country_selector,
                    self.postal_input,
                    ft.Container(height=10),
                    ft.Text("Formato de saída:", size=12, color=TEXT_MUTED, text_align="center"),
                    self.format_radio,
                    ft.Container(height=10),
                    self.search_btn,
                    self.loader,
                    ft.Container(height=20),
                    self.result_card,
                    ft.Container(height=15),
                    self.raw_container,
                    ft.Container(expand=True),
                    self.footer,
                    ft.Container(height=30),
                ], scroll="adaptive", horizontal_alignment="center"),
                expand=True, padding=25,
                gradient=ft.RadialGradient(center=ft.Alignment(1, -1), radius=1.5, colors=["#1e1b4b", BG_COLOR])
            )
        )

    def change_lang(self, lang_code):
        self.lang = lang_code
        flags = {"pt": "br", "en": "gb", "es": "es"}
        self.lang_btn.content.controls[0].src = f"https://flagcdn.com/w20/{flags[self.lang]}.png"
        self.lang_btn.content.controls[1].value = self.lang.upper()
        
        t = I18N[self.lang]
        is_br = self.current_tab == "br"
        self.title_text.value = t["title_br"] if is_br else t["title_intl"]
        self.btn_br.content.value = t["br"]
        self.btn_intl.content.value = t["intl"]
        self.cep_input.label = t["cep_label"]
        self.postal_input.label = t["postal_label"]
        self.search_btn.content.value = t["btn_search"]
        self.raw_container.content.controls[0].controls[0].value = t["raw_data"]
        self.page.update()

    def change_tab(self, tab):
        self.current_tab = tab
        t = I18N[self.lang]
        is_br = tab == "br"
        self.btn_br.bgcolor = PRIMARY_COLOR if is_br else "transparent"
        self.btn_br.content.color = "white" if is_br else TEXT_MUTED
        self.btn_intl.bgcolor = PRIMARY_COLOR if not is_br else "transparent"
        self.btn_intl.content.color = "white" if not is_br else TEXT_MUTED
        self.cep_input.visible = is_br
        self.country_selector.visible = not is_br
        self.postal_input.visible = not is_br
        self.title_text.value = t["title_br"] if is_br else t["title_intl"]
        self.page.update()

    def open_country_picker(self, e):
        search_field = ft.TextField(label="Pesquisar país...", prefix_icon=ft.Icons.SEARCH, border_radius=10, on_change=self.filter_countries)
        self.country_list = ft.Column(scroll="adaptive", expand=True)
        self.render_country_list()
        
        self.bottom_sheet = ft.BottomSheet(
            ft.Container(
                content=ft.Column([
                    ft.Text("Selecione o País", size=20, weight="bold"),
                    search_field,
                    ft.Container(content=self.country_list, height=400),
                ], spacing=15, tight=True),
                padding=20, bgcolor=SURFACE_COLOR, border_radius=ft.BorderRadius(20, 20, 0, 0)
            )
        )
        self.page.overlay.append(self.bottom_sheet)
        self.bottom_sheet.open = True
        self.page.update()

    def render_country_list(self, filter_text=""):
        self.country_list.controls.clear()
        for c in COUNTRIES:
            if filter_text.lower() in c["name"].lower():
                self.country_list.controls.append(
                    ft.ListTile(
                        leading=ft.Image(src=f"https://flagcdn.com/w40/{c['code']}.png", width=30, height=20, border_radius=2),
                        title=ft.Text(c["name"]),
                        on_click=lambda _, country=c: self.select_country(country)
                    )
                )
        self.page.update()

    def filter_countries(self, e):
        self.render_country_list(e.control.value)

    def select_country(self, country):
        self.selected_country = country
        self.country_selector.content.controls[0].src = f"https://flagcdn.com/w40/{country['code']}.png"
        self.country_selector.content.controls[1].value = country["name"]
        self.bottom_sheet.open = False
        self.page.update()

    async def open_github(self, e): await self.page.launch_url("https://github.com/caiquenovaes1994/")
    async def open_email(self, e): await self.page.launch_url("mailto:caiquenovaes1994@gmail.com")

    async def handle_search(self, e):
        fmt = self.format_radio.value
        is_br = self.current_tab == "br"
        if is_br:
            val = self.cep_input.value.strip().replace("-", "")
            if len(val) != 8: self.show_error("CEP inválido."); return
            url = f"http://localhost:8000/api/cep/{val}?formato={fmt}"
            cache_key = f"cep:{val}:{fmt}"
        else:
            postal = self.postal_input.value.strip()
            if not postal: self.show_error("Digite o Postal Code."); return
            url = f"http://localhost:8000/api/postal/{self.selected_country['code']}/{postal}?formato={fmt}"
            cache_key = f"postal:{self.selected_country['code']}:{postal}:{fmt}"

        if cache_key in cache:
            logger.info(f"Cache HIT (App): {cache_key}")
            self.display_results(cache[cache_key], fmt, is_br)
            return

        self.set_loading(True)
        try:
            data = await _perform_request(url, is_br, val, fmt)
            cache[cache_key] = data
            self.display_results(data, fmt, is_br)
        except pybreaker.CircuitBreakerError:
            logger.error("Circuit Breaker ABERTO (App)")
            self.show_error("Serviços temporariamente indisponíveis. Tente novamente mais tarde.")
        except Exception as ex: 
            logger.warning(f"Erro na busca (App) ({cache_key}): {str(ex)}")
            self.show_error(str(ex))
        finally: 
            self.set_loading(False)

    def set_loading(self, loading: bool):
        self.loader.visible = loading
        self.search_btn.visible = not loading
        self.page.update()

    def display_results(self, data, fmt, is_br):
        self.result_card.visible = True
        self.raw_container.visible = True
        t = I18N[self.lang]
        
        addr_title = t["address"]
        addr_subtitle = t["details"]

        if fmt == "json":
            if is_br:
                addr_title = data.get("logradouro", t["address"]) if data.get("logradouro") else data.get("localidade", t["address"])
                addr_subtitle = f"{data.get('localidade', '')} - {data.get('uf', '')} | CEP: {data.get('cep', '')}"
            else:
                place = data.get("places", [{}])[0] if data.get("places") else {}
                addr_title = place.get("place name", t["address"])
                addr_subtitle = f"{place.get('state', '')}, {data.get('country', '')}"
            raw = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            try:
                root = ET.fromstring(data)
                if is_br:
                    logradouro = root.findtext('logradouro', '')
                    localidade = root.findtext('localidade', '')
                    uf = root.findtext('uf', '')
                    cep = root.findtext('cep', '')
                    addr_title = logradouro if logradouro else (localidade if localidade else t["address"])
                    addr_subtitle = f"{localidade} - {uf} | CEP: {cep}"
                else:
                    place_name = root.findtext('.//place_name', '')
                    state = root.findtext('.//state', '')
                    country = root.findtext('.//country', '')
                    addr_title = place_name if place_name else t["address"]
                    addr_subtitle = f"{state}, {country}"
            except Exception:
                addr_title = "XML"
            raw = data

        self.result_card.content.controls[0].controls[1].controls[0].value = addr_title
        self.result_card.content.controls[0].controls[1].controls[1].value = addr_subtitle
        self.raw_container.content.controls[1].content.value = raw
        self.page.update()

    def copy_to_clipboard(self, e):
        self.page.set_clipboard(self.raw_container.content.controls[1].content.value)
        self.page.snack_bar = ft.SnackBar(ft.Text("Copiado!"), bgcolor=PRIMARY_COLOR)
        self.page.snack_bar.open = True
        self.page.update()

    def show_error(self, message):
        self.page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=ft.Colors.RED_700)
        self.page.snack_bar.open = True
        self.page.update()

def main(page: ft.Page): CEPApp(page)
if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets", view=ft.AppView.WEB_BROWSER, port=8080)
