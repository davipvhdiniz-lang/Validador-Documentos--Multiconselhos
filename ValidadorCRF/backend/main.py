from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import asyncio

# Importando a função correta do seu leitor_pdf.py
from leitor_pdf import extrair_texto  
from comparador import comparar
from validador_web import consultar_certidao_no_conselho

app = FastAPI()

# Permite que o seu Frontend converse com o Backend localmente
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Servidor rodando perfeitamente!"}

@app.post("/validar")
async def validar(pedido_file: UploadFile = File(...), certidao_file: UploadFile = File(...)):
    # 1. Lê os arquivos enviados como bytes
    pedido_bytes = await pedido_file.read()
    certidao_bytes = await certidao_file.read()
    
    # 2. Extrai o texto bruto de cada PDF usando sua função ajustada
    texto_pedido = extrair_texto(pedido_bytes)
    texto_certidao = extrair_texto(certidao_bytes)
    
    # 3. Executa a comparação (Etapa 1)
    # Obs: Sua função 'comparar' deve receber o texto bruto extraído para fazer o Regex
    resultado_comparacao = comparar(texto_pedido, texto_certidao)
    
    # 4. Busca o código de autenticação para a Validação Externa (Etapa 2)
    # Usaremos um regex rápido para pegar a chave de autenticação na certidão
    import re
    # Busca um padrão de hash com letras e números de 32 caracteres (padrão da certidão do CRF-GO)
    codigo_match = re.search(r'[A-F0-9]{32}', texto_certidao)
    codigo_autenticacao = codigo_match.group(0) if codigo_match else None
    
    status_conselho = {
        "autentica": False, 
        "mensagem": "Código de autenticação não encontrado na certidão."
    }
    
    if codigo_autenticacao:
        # Executa a busca automatizada no site do CRF-GO usando o Playwright
        status_conselho = await consultar_certidao_no_conselho(codigo_autenticacao)
    
    # 5. Retorna o veredito unificado para o seu Frontend
    return {
        "resultado_comparacao": resultado_comparacao,
        "resultado_conselho": status_conselho,
        "compativel_geral": resultado_comparacao.get("compativel", False) and status_conselho.get("autentica", False)
    }