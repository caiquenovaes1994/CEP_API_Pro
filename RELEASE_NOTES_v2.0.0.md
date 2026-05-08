# 🚀 Release Notes - CEP API Pro v2.0.0

**Data de Lançamento:** 08 de Maio de 2026

É com grande satisfação que anunciamos a chegada da versão **2.0.0** da **CEP API Pro**. Esta atualização representa a maior evolução arquitetural do projeto até o momento, transformando uma ferramenta focada em pesquisa em um ecossistema completo de geolocalização resiliente, seguro e multiplataforma.

Nesta versão, encerramos oficialmente a *Fase 2 (Melhorias de Produto e Negócio)* e *Fase 3 (Frontend e Interface)* do nosso Roadmap corporativo.

---

## 🌟 Novas Funcionalidades e Melhorias

### 🛡️ 1. Infraestrutura e Resiliência (Backend)

Para garantir alta disponibilidade em ambientes de produção e lidar com instabilidades de provedores externos, implementamos novas camadas de proteção no backend (FastAPI):

- **Circuit Breaker Pattern (`pybreaker`)**: A API agora detecta ativamente falhas sucessivas nos provedores primários (ViaCEP e Zippopotam.us). Se um serviço sair do ar, o disjuntor "abre", poupando recursos e retornando instantaneamente um erro amigável aos usuários ou roteando para provedores secundários.
- **Camada de Cache Distribuído (Redis)**: Integrado o `redis.asyncio` para armazenamento em memória de resultados de buscas recentes, reduzindo as requisições externas e garantindo latência na casa de ~5ms para CEPs buscados frequentemente.
- **Log Rotativo Inteligente**: Todo acesso e exceção são registrados no arquivo `cep_api.log`, programado para fazer rotação diariamente (TimedRotatingFileHandler), mantendo retenção limpa de 30 dias com base no fuso horário local (BRT).

### 🔒 2. Segurança Corporativa

- **Middleware `X-API-KEY`**: Todos os endpoints de busca (nacionais e internacionais) agora exigem autenticação obrigatória via cabeçalho.
- Proteção automática com rejeição imediata (`401 Unauthorized`) de acessos anônimos para evitar abuso da API.

### 🗺️ 3. Mapas Interativos e UX Global

- **Integração Web com Leaflet.js**: Quando um Postal Code internacional válido é encontrado, o cliente Web agora processa as coordenadas (Latitude/Longitude) e renderiza um mapa dinâmico de alta resolução logo abaixo do resultado, sem bloquear a UI principal.
- **Internacionalização (i18n)**: Suporte dinâmico e integrado para **Português (PT)**, **Inglês (EN)** e **Espanhol (ES)**. Um novo seletor reativo (livre de conflitos de emoji no Windows Chrome) adapta as tags, botões e placeholders para clientes no mundo todo, ideal para o setor hoteleiro global.

### 📱 4. Aplicativo Nativo Cross-Platform (Flet)

Levamos o frontend PWA a um novo patamar lançando um aplicativo compilável para Android e iOS através do SDK Flet (Flutter via Python) na pasta `/app`.

- **Interface Multiplataforma**: Paridade total de design Premium e Dark Mode com o Web App.
- **Resiliência Espelhada**: O App possui o próprio mecanismo de **Circuit Breaker** local e um sistema de **Cache (TTLCache)** em memória. Mesmo que a rede oscile, buscas repetidas são processadas instantaneamente offline.
- **Deep Links Geográficos**: Em vez de engessar o app com mapas WebView pesados, o botão "Ver no Mapa" aciona a intent nativa do aparelho, abrindo a coordenada perfeitamente.
- **i18n Nativo**: Seletor `PopupMenuButton` integrado diretamente na AppBar, re-renderizando a árvore de componentes sem necessidade de reinicialização.

---

## 🔧 Aspectos Técnicos

- **FastAPI**: Mantido o assincronismo em 100% das chamadas HTTP.
- **Novas Dependências Web**: `redis`, `pybreaker`
- **Novas Dependências App**: `flet`, `cachetools`, `pybreaker`
- **Integração FlagCDN**: A renderização das bandeiras foi uniformizada usando arquivos SVG estáticos otimizados do `flagcdn.com`, solucionando o bug histórico de renderização de *Emojis de Bandeira* em sistemas Windows (Chromium/Edge).

---

Agradecemos o apoio contínuo. Este ecossistema está oficialmente selado e preparado para escala na nuvem.

**[Caique Novaes](https://github.com/caiquenovaes1994/)**  
*Criador & Desenvolvedor Líder*
