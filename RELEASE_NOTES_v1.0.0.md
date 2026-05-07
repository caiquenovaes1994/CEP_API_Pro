# Release Notes - CEP API Pro v1.0.0

🎉 **Estamos orgulhosos em anunciar o lançamento oficial da CEP API Pro v1.0.0!** 🎉

Esta versão marca a transformação de um simples buscador de CEPs brasileiros para uma solução global, escalável e robusta, desenhada com foco em Enterprise e User Experience.

## ✨ Novas Funcionalidades (Features)

- **Suporte Global com 197 Países:** Adicionada a aba "Internacional", permitindo consultas de Códigos Postais do mundo inteiro através de integração primária com o provedor *Zippopotam.us*.
- **Motor Duplo de Fallback (OpenStreetMap):** Implementada estratégia de resiliência. Caso o provedor primário não possua dados do país (ex: Costa Rica), o backend aciona instantaneamente a API do *Nominatim*, converte o resultado dinamicamente e entrega o JSON/XML perfeitamente formatado.
- **Frontend Premium com "Dark Mode":** A página principal foi recriada do zero utilizando as melhores práticas de UI/UX, incluindo um seletor de países customizado renderizado via JS com busca nativa pelo teclado e inclusão de imagens de alta definição via FlagCDN.
- **Tradução Automática de Caracteres Especiais:** Países que retornam resultados em alfabetos não ocidentais (ex: Japonês, Chinês) agora são automaticamente convertidos para caracteres romanos através do cabeçalho de tradução inteligente.
- **Extrator de Endereço Visual:** A UI agora possui um "Parser" inteligente que lê os dados brutos de qualquer XML ou JSON retornado e exibe um "Cartão de Endereço" de leitura fácil acima da caixa de códigos.

## 🛠 Melhorias de Backend e Escalabilidade

- **Refatoração Completa para Async/Await:** A biblioteca síncrona `requests` foi substituída inteiramente pelo `httpx`. Todas as rotas do FastAPI agora operam de forma 100% não bloqueante.
- **Validação Fiscal Rigorosa:** A busca no Brasil foi intencionalmente mantida estrita à base do *ViaCEP*. CEPs obsoletos rejeitados agora geram mensagens de erro claras, garantindo que usuários (ex: setor de faturamento de hotéis) utilizem apenas Códigos Postais autorizados para emissão de Notas Fiscais.
- **Interceptador Especial (Mocks):** Regiões sem código postal oficial (como Hong Kong e Macau) possuem interceptadores no Python que simulam o retorno do famoso placeholder fictício de envios logísticos (`999077`).
- **Sanitização Regional de Inputs:** O Javascript foi treinado para higienizar os códigos antes da busca, isolando prefixos corretos para países que possuem CEPs complexos (ex: UK, Holanda, Canadá, Taiwan).

## 🐛 Correções de Bugs (Bug Fixes)

- Correção no gerador recursivo de XML (função `dict_to_xml`) para suportar listas e dicionários aninhados provenientes das consultas globais.
- Correção de erro de referência no parser do Frontend durante a mudança de estrutura do Select para divs customizadas.

---
*Lançado em Maio de 2026. Desenvolvido com carinho e precisão para máxima escalabilidade.*
