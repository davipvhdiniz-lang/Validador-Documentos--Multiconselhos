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

## 🔧 Instalação e Configuração

### 1. Preparação do Ambiente
Abra o terminal do seu sistema operacional e navegue até a pasta raiz do projeto:
```bash
cd C:\Projetos\ValidadorCRF\backend
2. Criação e Ativação do Ambiente Virtual (venv)
Bash
python -m venv venv

# Para ativar no Windows (Prompt de Comando / CMD):
.\venv\Scripts\activate.bat

# Para ativar no Windows (PowerShell):
.\venv\Scripts\Activate.ps1
3. Instalação do Ecossistema de Bibliotecas
Com a venv ativa (indicada pelo prefixo (venv) no terminal), instale as ferramentas necessárias:

Bash
pip install streamlit pandas pymupdf playwright
4. Provisionamento dos Binários do Navegador
Instale os binários isolados do Chromium controlados pelo robô:

Bash
playwright install chromium
▶️ Como Executar o Sistema
Via Terminal (Manual)
Certifique-se de que a venv está ativa e execute o comando abaixo na pasta backend:

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


### Como salvar e subir para o GitHub:
1. Abra o arquivo `README.md` no seu VS Code.
2. Apague tudo o que está nele, cole o texto acima e salve (`Ctrl + S`).
3. No terminal do VS Code, digite os comandos para subir a atualização:
```bash
git add README.md
git commit -m "Docs: Atualiza o README original com as novas travas de segurança e conexao"
git push origin main