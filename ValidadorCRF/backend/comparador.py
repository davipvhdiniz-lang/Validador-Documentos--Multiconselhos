import re
import unicodedata
from datetime import datetime


# ==========================================
# FUNÇÕES DE NORMALIZAÇÃO E TRATAMENTO DE TEXTO
# ==========================================

def normalizar_texto(texto: str, remover_espacos: bool = False) -> str:
    """
    Normaliza um texto removendo acentos, convertendo para maiúsculas e limpando pontuações.
    Se remover_espacos=True, remove TODOS os espaços para ignorar colagens/erros de OCR.
    """
    if not texto:
        return ""
    
    # 1. Converte para maiúsculas
    texto = texto.upper()
    
    # 2. Remove acentos (ex: Á -> A, Ç -> C)
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    
    # 3. Mantém apenas letras e números
    texto = re.sub(r'[^A-Z0-9\s]', '', texto)
    
    if remover_espacos:
        # Remove TODOS os espaços (ex: "MARIA DA SILVA" -> "MARIADASILVA")
        return re.sub(r'\s+', '', texto)
    else:
        # Apenas remove espaços duplos e limpa as bordas
        return re.sub(r'\s+', ' ', texto).strip()


def nomes_sao_iguais(nome1: str, nome2: str) -> bool:
    """
    Compara dois nomes em duas etapas:
    1. Comparação Normal: Limpa acentos e espaços duplos.
    2. Comparação sem Espaços (Fallback): Remove TODOS os espaços para tolerar
       erros de digitação ou textos colados pelo OCR (ex: "MARIA DA SILVA" vs "MARIADASILVA").
    """
    if not nome1 or not nome2 or nome1 == "Não encontrado" or nome2 == "Não encontrado":
        return False
        
    # Etapa 1: Comparação Normal
    n1_padrao = normalizar_texto(nome1, remover_espacos=False)
    n2_padrao = normalizar_texto(nome2, remover_espacos=False)
    
    if n1_padrao == n2_padrao:
        return True
        
    # Etapa 2: Comparação Sem Espaços (Fallback/Resgate)
    n1_sem_espaco = normalizar_texto(nome1, remover_espacos=True)
    n2_sem_espaco = normalizar_texto(nome2, remover_espacos=True)
    
    return n1_sem_espaco == n2_sem_espaco


# ==========================================
# FUNÇÕES DE EXTRAÇÃO DE DADOS
# ==========================================

def extrair_dados_pedido(texto):
    dados = {}

    # Data do pedido
    data = re.search(r"Data de Abertura\s*:\s*(\d{2}/\d{2}/\d{4})", texto)
    if data:
        dados["data"] = data.group(1)

    # CNPJ (Aceita com pontos/barra ou apenas números limpos)
    cnpj = re.search(r"CPF/CNPJ:\s*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})", texto)
    if cnpj:
        dados["cnpj"] = cnpj.group(1)

    # Responsável Técnico
    rt = re.search(r"Responsável\s*Técnico\s*:\s*(.+)", texto, re.IGNORECASE)
    if rt:
        dados["rt"] = rt.group(1).strip()

    return dados


def extrair_dados_certidao(texto):
    dados = {}

    # Validade da certidão
    validade = re.search(r"VALIDADE\s*(\d{2}/\d{2}/\d{4})", texto, re.IGNORECASE)
    if validade:
        dados["validade"] = validade.group(1)

    # CNPJ
    cnpj = re.search(r"(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})", texto)
    if cnpj:
        dados["cnpj"] = cnpj.group(1)

    # EXTRAÇÃO DE MÚLTIPLOS RESPONSÁVEIS TÉCNICOS (RTs)
    # Captura todas as ocorrências de nomes listados no bloco de RTs
    rts_encontrados = []
    
    # Busca o bloco completo de RTs na certidão
    bloco_rt = re.search(r"RESPONSÁVEIS TÉCNICOS.*?(?=TIPO DE ESTABELECIMENTO|VALOR|OBSERVAÇÕES|$)", texto, re.S | re.I)
    
    if bloco_rt:
        texto_bloco = bloco_rt.group(0)
        # Extrai os nomes associados ao padrão do CRF (entre o código/função e diretoria/cargo)
        linhas_rt = re.findall(r"(?:F\s+\d+|CRF\s*\d+|RT[:\s]+)(.*?)(?=\s+DIRETOR|\s+ASSISTENTE|\s+SUBSTITUTO|\n|$)", texto_bloco, re.I)
        
        for nome in linhas_rt:
            nome_limpo = nome.strip()
            if len(nome_limpo) > 3 and nome_limpo not in rts_encontrados:
                rts_encontrados.append(nome_limpo)

    # Se a expressão regular acima não encontrar, faz um fallback genérico
    if not rts_encontrados:
        rt_unico = re.search(r"RESPONSÁVEIS TÉCNICOS.*?F\s+\d+\s+(.*?)\s+DIRETOR", texto, re.S | re.I)
        if rt_unico:
            rts_encontrados.append(rt_unico.group(1).strip())

    dados["rts"] = rts_encontrados  # Salva a lista de RTs
    return dados


def comparar(texto_pedido, texto_certidao):
    pedido = extrair_dados_pedido(texto_pedido)
    certidao = extrair_dados_certidao(texto_certidao)

    erros = []
    compativel = True

    # 1. Validação de CNPJ
    if "cnpj" in pedido and "cnpj" in certidao:
        cnpj_ped_limpo = "".join(filter(str.isdigit, pedido["cnpj"]))
        cnpj_cert_limpo = "".join(filter(str.isdigit, certidao["cnpj"]))
        if cnpj_ped_limpo != cnpj_cert_limpo:
            erros.append(f"CNPJ divergente: Pedido ({pedido['cnpj']}) vs Certidão ({certidao['cnpj']})")
            compativel = False
    else:
        erros.append("CNPJ não encontrado em um dos documentos.")
        compativel = False

    # 2. Validação de Responsável Técnico (Múltiplos RTs)
    rt_pedido = pedido.get("rt")
    rts_certidao = certidao.get("rts", [])

    if rt_pedido and rts_certidao:
        # Verifica se o RT do pedido é igual a PELO MENOS UM dos RTs da certidão
        rt_encontrado = any(nomes_sao_iguais(rt_pedido, rt_c) for rt_c in rts_certidao)
        
        if not rt_encontrado:
            erros.append(
                f"O Responsável Técnico do pedido ({rt_pedido}) não foi localizado na certidão do conselho."
            )
            compativel = False
    else:
        erros.append("Responsável Técnico não localizado no pedido ou na certidão.")
        compativel = False

    # 3. Validação de Validade da Certidão
    if "data" in pedido and "validade" in certidao:
        try:
            data_pedido = datetime.strptime(pedido["data"], "%d/%m/%Y")
            validade = datetime.strptime(certidao["validade"], "%d/%m/%Y")
            if validade < data_pedido:
                erros.append(f"A certidão expirou! Vencimento: {certidao['validade']} | Data do Pedido: {pedido['data']}")
                compativel = False
        except Exception:
            erros.append("Erro ao formatar datas para comparação.")
            compativel = False
    else:
        erros.append("Data de abertura do pedido ou validade da certidão não encontrada.")
        compativel = False

    return {
        "compativel": compativel,
        "erros": erros,
        "dados_pedido": pedido,
        "dados_certidao": certidao
    }