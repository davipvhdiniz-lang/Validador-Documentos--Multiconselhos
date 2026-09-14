import fitz  # PyMuPDF

def extrair_texto(caminho_ou_bytes):
    texto = ""

    # 1. Abre o PDF (seja por bytes enviados pelo Streamlit/FastAPI ou caminho do arquivo)
    if isinstance(caminho_ou_bytes, bytes):
        doc = fitz.open(stream=caminho_ou_bytes, filetype="pdf")
    else:
        doc = fitz.open(caminho_ou_bytes)

    # 2. Percorre as páginas e extrai o texto da camada nato-digital
    with doc as pdf:
        for pagina in pdf:
            texto += pagina.get_text()

    # 3. VERIFICAÇÃO DE PDF NATO-DIGITAL:
    # Se o texto for menor que 10 caracteres, significa que é um PDF contendo imagem/escaneado
    if len(texto.strip()) < 10:
        raise ValueError(
            "O documento analisado não está no formato de PDF de origem (Nato-Digital). "
            "Documentos no formato PDF que tiveram origem em documentos digitalizados, como imagem, não serão processados pelo sistema."
        )

    return texto