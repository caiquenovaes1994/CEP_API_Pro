# Release Notes - CEP API Pro v1.1.0

A versão **1.1.0** foca primordialmente na elevação da experiência do usuário (UX), identidade de marca (Branding) e instalação mobile, transformando a API não apenas em um backend corporativo robusto, mas em um produto completo, bonito e acessível.

## 🌟 Novas Funcionalidades (Features)

* **PWA (Progressive Web App) Habilitado:**
  * O projeto agora conta com o registro de um `manifest.json` e interceptação via Service Worker (`sw.js`).
  * A aplicação web pode ser oficialmente "instalada" em smartphones e desktops, rodando em ambiente *Standalone* de tela cheia, com ícone de aplicativo nativo na gaveta de apps.
  * O FastAPI foi devidamente configurado com a classe `StaticFiles` para rotear publicamente imagens e assets no path `/static`.

* **Identidade Visual Profissional (Branding):**
  * Criação e adoção de um logotipo oficial: combinação elegante entre o clássico Alfinete de Localização e Nós de Redes Globais.
  * O design utiliza as cores vibrantes Índigo e Verde Esmeralda para compor com o fundo Dark Mode, e é embutido transparentemente na interface através da manipulação `mix-blend-mode: screen;` no CSS.
  * Logo dimensionado dinamicamente para causar grande impacto visual tanto no Desktop (`550px`) quanto no Mobile (`300px`).
  * Adoção de um ícone reduzido sem texto (`app_icon.png`) estritamente focado para a formatação de instalação nativa em Home Screens (PWA).

## 🎨 Ajustes de Layout (UI/UX)

* **Refatoração do Box Model do Documento:**
  * Mudança da estrutura do `body` para o padrão `flex-direction: column`. Isso sanou o problema do rodapé flutuando livremente à direita da tela, ancorando o footer definitivamente abaixo do cartão central sem necessidade de fixes absolutos prejudiciais à rolagem.
  * **Frase de Impacto:** Adicionado o *catchphrase* corporativo "Simplificando a geolocalização global, um código postal de cada vez." diretamente na interface do rodapé.

## 🐛 Correções e Linting

* **Compatibilidade e IDEs:**
  * Substituição de tags Markdown absolutas problemáticas (links estritos de e-mail e imagens) em documentações para URLs canônicas (`https://mail.google.com/...`) para contornar falsos-positivos de validações estáticas e linter bugs de IDEs da família JetBrains.

## 📦 Próximos Passos (Roadmap v2)

O foco agora retorna às melhorias de infraestrutura (Circuit Break, Caching Redis e Log Local Diário), autenticação X-API-KEY e encapsulamento em arquitetura nativa com Capacitor (`/app`). Consulte o [Roadmap oficial na Issue #1 do GitHub](https://github.com/caiquenovaes1994/CEP_API/issues/1) para os detalhes da v2.0.
