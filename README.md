# CEP API Pro (v1.0.0)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white)

Uma API rápida, assíncrona e altamente resiliente construída com **FastAPI** para buscar dados de endereços a partir de códigos postais do Brasil e do mundo inteiro.

Esta API atua como um hub inteligente, roteando requisições e normalizando respostas de múltiplos provedores geográficos globais (ViaCEP, Zippopotam.us e OpenStreetMap Nominatim), suportando saídas tanto em **JSON** quanto em **XML**.

## 🚀 Principais Funcionalidades

- **Motor Duplo Internacional (Fallback API)**: Busca primária no `Zippopotam.us` e fallback inteligente para o `OpenStreetMap` em países não suportados (com conversão e tradução automática para o alfabeto Romano via header de idioma).
- **Tratamento Específico por Região**: Lógica embutida de prefixos para Canadá, Reino Unido, Holanda e Taiwan, além de mapeamento customizado para áreas que não usam CEP (Ex: Hong Kong e Macau com o placeholder `999077`).
- **Rigor Fiscal Brasil**: Para buscas nacionais, utilizamos unicamente a base estrita do **ViaCEP** (espelho dos Correios) de forma proposital, garantindo a validade absoluta dos endereços para sistemas de faturamento e emissão de Notas Fiscais.
- **Frontend Moderno Incluso**: A API serve uma interface web "Dark Mode" premium na rota `/`, contando com:
  - Sistema de abas (Brasil x Internacional)
  - Dropdown customizado de 197 países e territórios com bandeiras (via FlagCDN)
  - Navegação fluida por teclado no seletor de países
  - Área inteligente de extração de endereço visual, convertendo o JSON cru em uma leitura rápida e clara para o usuário.
- **Altíssima Performance**: Construída de ponta a ponta com `httpx` (Assíncrono) para lidar com milhares de requisições simultâneas sem bloqueio da Event Loop do FastAPI.

## 📖 Endpoints Principais

### 1. Busca no Brasil (Estrita)

**GET** `/api/cep/{cep}`

- **cep**: 8 dígitos.
- **Query `?formato=xml`** (Opcional): Força o retorno em XML.

*O backend validará com o provedor oficial. Caso o CEP tenha sido desativado pelos Correios (ex: CEPs terminados em -000 de municípios recém mapeados), retornará erro 404 alertando sobre a necessidade de um código atualizado.*

### 2. Busca Internacional (Resiliente)

**GET** `/api/postal/{country}/{postal}`

- **country**: Sigla ISO Alpha-2 (ex: `us`, `jp`, `gb`).
- **postal**: O código postal do respectivo país.

*Se a região for asiática ou árabe, o sistema converterá a localidade para caracteres ocidentais automaticamente.*

## 👨‍💻 Autor

### Caique

> *Simplificando a geolocalização global, um código postal de cada vez.*

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/caiqu)
[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:contato@exemplo.com)
