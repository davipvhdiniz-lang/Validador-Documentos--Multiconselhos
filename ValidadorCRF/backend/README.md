# 🩺 Validador de Certidões Multiconselhos (RPA & Data Science)

Este projeto foi desenvolvido como parte de um estudo prático de **Ciência de Dados** e **Automação de Processos Robóticos (RPA)**. O sistema automatiza a validação de conformidade regulatória cruzando dados de solicitações internas com Certidões de Regularidade Profissional de múltiplos conselhos (CRF-GO, CRM, CRO e CRBM), realizando validações dinâmicas e raspagem de dados web em tempo real.

---

## 🚀 Funcionalidades Principais

* 📄 **Extração Inteligente de PDFs:** Processamento e extração de texto bruto de documentos (pedidos e certidões) utilizando engenharia de dados com a biblioteca `PyMuPDF` (`fitz`).
* 📊 **Cruzamento e Análise Algorítmica:** Módulo lógico embarcado que compara chaves estruturais (CNPJ, CNAE, Responsável Técnico e datas de vigência) para identificar divergências ou fraudes em tempo real.
* 🤖 **Roteamento Dinâmico de RPA:** Motor web baseado em `Playwright` que identifica automaticamente o conselho emissor a partir do texto do PDF e adota a estratégia de validação ideal:
  * **Modo Silencioso (Headless):** Execução em segundo plano para consultas estruturadas sem desafios visuais (ex: CRF-GO via código hash de 32 caracteres).
  * **Modo Interativo (Headful com Bypass Humano):** Abertura automatizada da interface do navegador na tela quando o portal externo exige resolução de **CAPTCHA** ou validação de segurança manual (CRM, CRO, CRBM).
* 🎨 **Dashboard Analítico:** Interface web reativa construída em `Streamlit` contendo tabelas comparativas de dados, alertas visuais de risco e controle sequencial de protocolos processados.

---

## 🔧 Instalação e Configuração

### 1. Preparação do Ambiente
Abra o terminal do seu sistema operacional e navegue até a pasta raiz do projeto:
```bash
cd C:\Projetos\ValidadorCRF\backend
```

### 2. Criação e Ativação do Ambiente Virtual (venv)
Isole as dependências do ecossistema executando:
```bash
python -m venv venv

# Para ativar no Windows (Prompt de Comando / CMD):
.\venv\Scripts\activate.bat

# Para ativar no Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

### 3. Instalação do Ecossistema de Bibliotecas
Com a `venv` ativa (indicada pelo prefixo `(venv)` no terminal), instale as ferramentas necessárias:
```bash
pip install streamlit pandas pymupdf playwright
```

### 4. Provisionamento dos Binários do Navegador
Instale os binários isolados do Chromium controlados pelo robô:
```bash
playwright install chromium
```

---

## ▶️ Como Executar o Sistema

### Via Terminal (Manual)
Certifique-se de que a `venv` está ativa e execute o comando abaixo na pasta `backend`:
```bash
streamlit run app.py
```

### Via Atalho (Produção)
O projeto conta com um script automatizado de um clique (`.bat`) localizado na Área de Trabalho, encarregado de ativar o ambiente virtual e subir a aplicação no seu navegador padrão de forma transparente.

---

## 📂 Estrutura Arquitetural do Projeto

```plaintext
ValidadorCRF/
└── backend/
    ├── venv/                 # Ambiente virtual isolado do Python
    ├── app.py                # Core da aplicação: Interface Streamlit e Roteamento de Fluxo
    ├── leitor_pdf.py         # Módulo de Engenharia de Dados: Extração de Texto via PyMuPDF
    ├── comparador.py         # Módulo de Inteligência de Negócio: Regras de Cruzamento de Dados
    ├── validador_web.py      # Módulo de Automação RPA: Motores Playwright (Headless e Headful)
    └── requirements.txt      # Manifesto de dependências do ecossistema Python
```

---

## 🛠️ Stack Tecnológica Utilizada

* **Streamlit:** Construção de dashboards reativos e interface do usuário orientada a dados.
* **Playwright:** Automação de navegadores (RPA) de alta performance com suporte a fluxos assíncronos.
* **PyMuPDF (Fitz):** Parser de alta velocidade para processamento de estruturas binárias de arquivos PDF.
* **Pandas:** Modelagem, estruturação e alinhamento das matrizes de dados para comparação na interface gráfica.