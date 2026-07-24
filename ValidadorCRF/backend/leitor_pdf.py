import fitz  # PyMuPDF

def extrair_texto(caminho_ou_bytes):
    texto = ""
    
    # Se receber bytes (enviados via FastAPI/UploadFile)
    if isinstance(caminho_ou_bytes, bytes):
        with fitz.open(stream=caminho_ou_bytes, filetype="pdf") as pdf:
            for pagina in pdf:
                texto += pagina.get_text()
    # Se receber o caminho do arquivo direto (string)
    else:
        with fitz.open(caminho_ou_bytes) as pdf:
            for pagina in pdf:
                texto += pagina.get_text()
                
    return texto