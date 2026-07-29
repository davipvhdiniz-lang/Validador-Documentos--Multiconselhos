# 📄 Validador de Certificados Multiconselhos (RPA & Data Science)

Este projeto foi desenvolvido como parte de um estudo prático de Ciência de Dados e Automação de Processos Robóticos (RPA) para o Trabalho de Conclusão de Curso (TCC). O sistema automatiza a validação de conformidade regulatória cruzando dados de interferências internas com Certificados de Regularidade Profissional de múltiplos conselhos (CRF-GO, CRM, CRO e CRBM), realizando validações dinâmicas e raspagem de dados web em tempo real.

---

## 🚀 Funcionalidades Principais

*   **📄 Extração Inteligente de PDFs:** Processamento e remoção de texto bruto de documentos (pedidos e certificados) utilizando engenharia de dados com a biblioteca `PyMuPDF (fitz)`.
*   **📊 Cruzamento e Análise Algorítmica:** Módulo lógico embarcado que compara chaves estruturais (CNPJ, CNAE, Responsável Técnico e dados de vigilância) para identificar divergências ou fraudes em tempo real.
*   **⏱️ Trava de Segurança Temporal (Validade):** Algoritmo integrado que valida a data de vencimento da certidão confrontando-a com a data atual do sistema. Certidões expiradas bloqueiam o processo imediatamente, forçando o parecer de indeferimento.
*   **🤖 Roteamento Dinâmico de RPA:** Motor web baseado em `Playwright` que identifica automaticamente o conselho emissor a partir do texto do PDF e adota a estratégia de validação ideal:
    *   **Modo Silencioso (Headless):** Execução em segundo plano para consultas estruturadas sem desafios visuais (ex: CRF-GO via código hash de 32 caracteres).
    *   **Modo Interativo (Headful / Assistido):** Abertura da interface do navegador ou redirecionamento dinâmico via chaves de acesso estruturadas quando o portal externo exige resolução de CAPTCHA ou validação manual (CRM, CRO, CRBM).
*   **🛡️ Tolerância a Falhas de Rede (Fallback Técnico):** Caso os portais dos conselhos apresentem instabilidade ou gerem quedas de conexão (*Timeouts* / `ERR_CONNECTION_TIMED_OUT`), o sistema intercepta o erro, preserva os dados analisados e altera o parecer para **Análise Pendente**, mitigando o risco de falsos positivos.
*   **🎨 Dashboard Analítico (Streamlit):** Interface web reativa contendo tabelas comparativas limpas, alertas visuais de risco (vermelho, amarelo e verde) e controle sequencial de protocolos processados.

---

## 🔧 Instalação e Configuração para o Grupo

Siga o passo a passo abaixo no seu computador para configurar o ambiente, instalar as bibliotecas de forma automática e rodar o sistema pela primeira vez.

### Passo 1: Abrir o terminal no VS Code
1. Abra a pasta do projeto `ValidadorCRF` no seu VS Code.
2. No seu teclado, aperte as teclas **Ctrl + J** juntas. Isso vai abrir o terminal na parte de baixo da tela.

### Passo 2: Preparação e Ativação do Ambiente Virtual (venv)
1. Primeiro, navegue até a pasta raiz se já não estiver nela:
```bash
cd C:\Projetos\ValidadorCRF
Crie o ambiente virtual (caso ainda não tenha criado no seu PC):

Bash
python -m venv backend\venv
Ative a venv copiando o comando abaixo, colando no terminal e apertando Enter:

Bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process; .\backend\venv\Scripts\Activate.ps1
Note que aparecerá o prefixo (venv) no início da linha do terminal, indicando que o ambiente está ativo.

Passo 3: Entrar na pasta Backend
Digite o comando abaixo para entrar na pasta onde estão os códigos e o arquivo de requisitos e aperte Enter:

Bash
cd backend
Passo 4: Instalação Automática do Ecossistema de Bibliotecas
Para instalar todas as ferramentas necessárias (streamlit, pandas, pymupdf, playwright) de uma vez só, digite o comando abaixo e aperte Enter:

Bash
pip install -r requirements.txt
Provisione os binários isolados do navegador controlados pelo robô digitando o comando abaixo e apertando Enter:

Bash
playwright install chromium
▶️ Como Executar o Sistema
Via Terminal (Manual)
Certifique-se de que a venv está ativa (venv) e que você está dentro da pasta backend. Em seguida, execute o comando abaixo:

Bash
streamlit run app.py
Via Atalho (Produção)
O projeto conta com um script automatizado de um clique (.bat) localizado na Área de Trabalho, encarregado de ativar o ambiente virtual e subir a aplicação no seu navegador padrão de forma transparente.

📂 Estrutura Arquitetural do Projeto
Plaintext
ValidadorCRF/
└── backend/
    ├── venv/                 # Ambiente virtual isolado do Python
    ├── app.py                # Core da aplicação: Interface Streamlit, Regras do CRO e Roteamento
    ├── leitor_pdf.py         # Módulo de Engenharia de Dados: Extração de Texto via PyMuPDF
    ├── comparador.py         # Módulo de Inteligência de Negócio: Regras de Cruzamento de Dados
    ├── validador_web.py      # Módulo de Automação RPA: Motores Playwright (Headless e Headful)
    └── requirements.txt      # Manifesto de dependências do ecossistema Python
🛠️ Stack Tecnológica Utilizada
Streamlit: Construção de dashboards reativos e interface do usuário orientada a dados.

Playwright: Automação de navegadores (RPA) de alta performance com suporte a fluxos assíncronos.

PyMuPDF (Fitz): Analisador de alta velocidade para processamento de estruturas binárias de arquivos PDF.

Pandas: Modelagem, estruturação e alinhamento das matrizes de dados para comparação na interface gráfica.


---

### O que fazer agora:
1. Salve o arquivo (`Ctrl + S`).
2. Garanta que o seu `requirements.txt` tem apenas as 4 linhas com os nomes das bibliotecas.
3. No terminal do VS Code, mande tudo atualizado para o GitHub digitando:
```bash
git add README.md requirements.txt
git commit -m "Docs: Atualiza manual com instruções detalhadas passo a passo para o grupo"
git push origin main