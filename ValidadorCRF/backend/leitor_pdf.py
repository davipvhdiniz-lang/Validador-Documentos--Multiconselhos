import fitz  # PyMuPDF

def extrair_texto(caminho_ou_bytes):
    texto = ""

    if isinstance(caminho_ou_bytes, bytes):
        doc = fitz.open(stream=caminho_ou_bytes, filetype="pdf")
    else:
        doc = fitz.open(caminho_ou_bytes)

    with doc as pdf:
        for pagina in pdf:
            texto += pagina.get_text()

    # Validação de PDF Nato-Digital
    if len(texto.strip()) < 10:
        raise ValueError(
            "O documento analisado não está no formato de PDF de origem (Nato-Digital). "
            "Documentos no formato PDF que tiveram origem em documentos digitalizados, como imagem, não serão processados pelo sistema."
        )

    return texto