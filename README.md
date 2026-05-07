# CEP API Pro (v1.0.0)

Uma API rápida, assíncrona e altamente resiliente construída com **FastAPI** para buscar dados de endereços a partir de códigos postais do Brasil e do mundo inteiro.

Esta API atua como um hub inteligente, roteando requisições e normalizando respostas de múltiplos provedores geográficos globais (ViaCEP, Zippopotam.us e OpenStreetMap Nominatim), suportando saídas tanto em **JSON** quanto em **XML**.

## 🚀 Principais Funcionalidades

- **Motor Duplo Internacional (Fallback API)**: Busca primária no `Zippopotam.us` e fallback inteligente para o `OpenStreetMap` em países não suportados (com conversão e tradução automática para o alfabeto Romano via header de idioma).
- **Tratamento Específico por Região**: Lógica embutida de prefixos para Canadá, Reino Unido e Holanda, além de mapeamento customizado para áreas que não usam CEP (Ex: Hong Kong e Macau com o placeholder `999077`).
- **Rigor Fiscal Brasil**: Para buscas nacionais, utilizamos unicamente a base estrita do **ViaCEP** (espelho dos Correios) de forma proposital, garantindo a validade fiscal dos endereços para sistemas de faturamento e emissão de Notas Fiscais (Requisito Accor).
- **Frontend Moderno Incluso**: A API serve uma interface web "Dark Mode" premium na rota `/`, contando com:
  - Sistema de abas (Brasil x Internacional)
  - Dropdown customizado de 195 países com bandeiras (via FlagCDN)
  - Navegação fluida por teclado no seletor de países
  - Área inteligente de extração de endereço visual, convertendo o JSON cru em uma leitura rápida e clara para o usuário.
- **Altíssima Performance**: Construída de ponta a ponta com `httpx` (Assíncrono) para lidar com milhares de requisições simultâneas sem bloqueio da Event Loop do FastAPI.

## 🛠 Tecnologias Utilizadas

- **Python 3.12+**
- **FastAPI** (Web Framework)
- **Uvicorn** (Servidor ASGI)
- **HTTPX** (Requisições assíncronas ultra-rápidas)
- **Vanilla JS, HTML5 e CSS3** (Frontend Zero Dependencies)

## 📦 Instalação

1. Clone o repositório e acesse a pasta.
2. Crie seu ambiente virtual (opcional, mas recomendado):
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Como Executar

Inicie o servidor de alta performance:

```bash
python main.py
```
A API estará rodando em: `http://127.0.0.1:8000`

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
