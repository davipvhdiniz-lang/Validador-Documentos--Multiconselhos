# Validador de Certidão Profissional (ValidadorCRF-GO) 

Projeto desenvolvido para o curso de ciências de dados onde foi criado um validador de documentos
Sistema automatizado para validação de dados de solicitações e autenticação de certidões junto ao Conselho Regional de Farmácia (CRF-GO). O sistema cruza os dados extraídos de documentos em PDF e realiza a checagem automatizada via web para garantir a conformidade dos processos.

## 🚀 Funcionalidades

*   **Extração de Texto de PDFs:** Leitura automatizada dos documentos de pedido e certidões utilizando a biblioteca `PyMuPDF` (`fitz`).
*   **Cruzamento Inteligente de Dados:** Módulo interno que compara as informações extraídas para identificar divergências automaticamente.
*   **Autenticação Web Automatizada:** Consulta automatizada ao portal do conselho profissional via `Playwright` para validação da autenticidade da certidão.
*   **Interface Intuitiva:** Painel web moderno construído em `Streamlit` para acompanhamento do status, upload de arquivos e visualização de alertas de risco do processo.
## 🔧 Instalação e Configuração

1. **Acesse a pasta do projeto:**
   ```bash
   cd C:\Projetos\ValidadorCRF\backend
Crie e ative o ambiente virtual (venv):

Bash
python -m venv venv
# Para ativar no Windows (Prompt de Comando):
.\venv\Scripts\activate.bat
Instale as dependências do projeto:

Bash
pip install streamlit pandas pymupdf playwright
Instale o navegador do robô (Playwright):

Bash
playwright install chromium
▶️ Como Executar
Para iniciar o sistema manualmente via terminal, certifique-se de que a venv está ativa e execute:

Bash
streamlit run app.py
Nota: O projeto também conta com um script de inicialização automatizada (.bat) na Área de Trabalho para execução em um clique.

📂 Estrutura do Projeto
Plaintext
ValidadorCRF/
└── backend/
    ├── venv/                 # Ambiente virtual do Python
    ├── app.py                # Interface gráfica do Streamlit
    ├── leitor_pdf.py         # Módulo de extração de texto (PyMuPDF)
    ├── comparador.py         # Módulo de inteligência e cruzamento de dados
    ├── validador_web.py      # Módulo de automação web (Playwright)
    └── requirements.txt      # Listagem de dependências do ecossistema
🛠️ Tecnologias Utilizadas
Streamlit - Framework de interface web.

Playwright - Automação de processos robóticos (RPA) na web.

PyMuPDF (Fitz) - Engenharia de extração de dados de documentos.

Pandas - Estruturação e manipulação de matrizes de dados.


---

### 🎨 Como vai ficar?
Como o arquivo termina em `.md` (Markdown), o próprio VS Code (ou plataformas como o GitHub) vai renderizar isso de forma linda: os códigos vão ficar em blocos cinzas, os títulos destacados e as tabelas com linhas separadoras perfeitas. 

É só colar, salvar com `Ctrl + S` e o seu projeto ganhou uma documentação de nível sênior!