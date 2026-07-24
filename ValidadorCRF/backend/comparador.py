import re
from datetime import datetime


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

    # --- EXTRAÇÃO DE CNAE ---
    cnaes_encontrados = re.findall(r"\b\d{7}\b", texto)
    if cnaes_encontrados:
        cnaes_unicos = list(dict.fromkeys(cnaes_encontrados))
        dados["cnae"] = ", ".join(cnaes_unicos)
    else:
        dados["cnae"] = "Não encontrado"

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

    # Responsável Técnico
    rt = re.search(r"RESPONSÁVEIS TÉCNICOS.*?F\s+\d+\s+(.*?)\s+DIRETOR", texto, re.S | re.I)
    if rt:
        dados["rt"] = rt.group(1).strip()

    # --- EXTRAÇÃO DE TIPO DE ESTABELECIMENTO (CERTIDÃO) ---
    tipo_est = re.search(r"TIPO DE ESTABELECIMENTO\s*\n*(.+)", texto, re.IGNORECASE)
    if tipo_est:
        resultado = tipo_est.group(1).split("Consulte")[0].strip()
        dados["cnae"] = resultado.upper()
    else:
        if "FARMÁCIA SEM MANIPULAÇÃO" in texto.upper():
            dados["cnae"] = "FARMÁCIA SEM MANIPULAÇÃO"
        else:
            dados["cnae"] = "Não encontrado"

    return dados


def comparar(texto_pedido, texto_certidao):
    # Primeiro, extrai os dicionários de dados a partir dos textos brutos
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

    # 2. Validação de Responsável Técnico (RT)
    if "rt" in pedido and "rt" in certidao:
        if pedido["rt"].upper() != certidao["rt"].upper():
            erros.append(f"Responsável Técnico divergente: Pedido ({pedido['rt']}) vs Certidão ({certidao['rt']})")
            compativel = False
    else:
        erros.append("Responsável Técnico não encontrado em um dos documentos.")
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

    # 4. Validação de CNAE (Checagem de consistência simples)
    cnae_pedido = pedido.get("cnae", "")
    cnae_certidao = certidao.get("cnae", "")
    
    if "4771701" in cnae_pedido or "4772500" in cnae_pedido:
        if not any(termo in cnae_certidao.upper() for termo in ["FARMÁCIA", "DROGARIA", "FARMACIA"]):
            erros.append(f"CNAE do pedido indica Farmácia/Drogaria, mas a Certidão indica: {cnae_certidao}")
            compativel = False

    # RETORNA OS DADOS ESTRUTURADOS PARA O STREAMLIT
    return {
        "compativel": compativel,
        "erros": erros,
        "dados_pedido": pedido,
        "dados_certidao": certidao
    }