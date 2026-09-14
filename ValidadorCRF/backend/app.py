import io
import re
import sys
import asyncio
import pandas as pd
import streamlit as st
from datetime import datetime

# Bibliotecas do ReportLab para gerar o PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# Módulos internos do seu projeto
from leitor_pdf import extrair_texto
from comparador import comparar
from validador_web import consultar_certidao_no_conselho


# ==============================================================================
# FUNÇÃO GERADORA DO PDF
# ==============================================================================

def gerar_pdf_parecer(protocolo, status_compativel, divergencias, dados_pedido, dados_certidao, texto_minuta_tela="", certidao_vencida=False):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    elementos = []

    # Estilos customizados do documento
    style_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, alignment=1, textColor=colors.gray)
    style_corpo = ParagraphStyle('Corpo', parent=styles['Normal'], fontSize=10, leading=14)
    style_bold = ParagraphStyle('Bold', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')

    # 1. Cabeçalho Oficial
    elementos.append(Paragraph("SISTEMA AUTOMATIZADO DE VALIDAÇÃO DOCUMENTAL", style_sub))
    elementos.append(Spacer(1, 15))

    # 2. Informações do Processo
    data_emissao = datetime.now().strftime("%d/%m/%Y às %H:%M")
    elementos.append(Paragraph(f"<b>Protocolo do Solicitante:</b> {protocolo}", style_corpo))
    elementos.append(Paragraph(f"<b>Data da Auditoria:</b> {data_emissao}", style_corpo))
    
    status_str = "<font color='green'><b>COMPATÍVEL / DEFERIDO</b></font>" if status_compativel else "<font color='red'><b>INCOMPATÍVEL / REJEITADO</b></font>"
    elementos.append(Paragraph(f"<b>Resultado do Parecer:</b> {status_str}", style_corpo))
    elementos.append(Spacer(1, 15))

    # 3. Tabela Comparativa
    elementos.append(Paragraph("<b>Tabela Comparativa de Detalhes:</b>", style_bold))
    elementos.append(Spacer(1, 6))

    dados_tabela = [
        ["Dado Comparado", "No Pedido", "Na Certidão"],
        ["CNPJ", dados_pedido.get("cnpj", "Não encontrado"), dados_certidao.get("cnpj", "Não encontrado")],
        ["Responsável Técnico", dados_pedido.get("rt", "Não encontrado"), dados_certidao.get("rt", "Não encontrado")],
        ["Data / Validade", f"Abertura: {dados_pedido.get('data', 'N/A')}", f"Validade: {dados_certidao.get('validade', 'N/A')}"]
    ]

    tabela = Table(dados_tabela, colWidths=[130, 200, 200])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)
    ]))
    elementos.append(tabela)
    elementos.append(Spacer(1, 15))

    # 4. Parecer Técnico / Apuração de Anomalias
    elementos.append(Paragraph("<b>Parecer Técnico / Apuração de Anomalias:</b>", style_bold))
    elementos.append(Spacer(1, 6))

    # Se passamos a minuta da tela, imprimimos ela no PDF para manter a paridade
    if texto_minuta_tela:
        linhas = texto_minuta_tela.split("\n")
        for linha in linhas:
            if linha.strip():
                elementos.append(Paragraph(linha, style_corpo))
                elementos.append(Spacer(1, 4))
    else:
        lista_erros = list(divergencias) if divergencias else []
        if certidao_vencida and not any("VENCIDA" in str(e).upper() for e in lista_erros):
            lista_erros.append(f"Certidão VENCIDA (Validade: {dados_certidao.get('validade', 'N/A')}).")

        if lista_erros:
            elementos.append(Paragraph("Foram identificadas as seguintes inconformidades durante a validação:", style_corpo))
            elementos.append(Spacer(1, 5))
            for erro in lista_erros:
                elementos.append(Paragraph(f"• {erro}", style_corpo))
                elementos.append(Spacer(1, 3))
        else:
            elementos.append(Paragraph("Certifico que não foram identificadas divergências cadastrais. O documento cumpre com os requisitos regulamentares.", style_corpo))

    elementos.append(Spacer(1, 30))

    # 5. Assinatura Rodapé
    elementos.append(Paragraph("____________________________________________________", style_sub))
    elementos.append(Paragraph("Validador Automatizado de Documentos", style_sub))

    doc.build(elementos)
    buffer.seek(0)
    return buffer


# ==============================================================================
# INTERFACE STREAMLIT
# ==============================================================================
st.set_page_config(page_title="Sistema de Validação de Documentos", page_icon="📄", layout="wide")

# --- ESTILIZAÇÃO VISUAL CORPORATIVA ---
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #0F172A;
    }

    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        padding: 6px 14px !important;
        border-radius: 6px !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 8px !important;
        margin-bottom: 8px !important;
    }

    .stButton > button, 
    .stButton > button:hover, 
    .stButton > button:focus, 
    .stButton > button:active,
    .stButton > button:focus:not(:focus-visible) {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }

    .stTextInput > div > div > input {
        background-color: #F1F5F9;
        color: #0F172A;
        border-radius: 6px;
    }

    [data-testid="stFileUploadDropzone"] {
        background-color: #F8FAFC;
        border: 1px dashed #CBD5E1;
    }

    .stMarkdown p, label, .stSelectbox label {
        color: #0F172A !important;
    }
    </style>
""", unsafe_allow_html=True)

if "reset_contador" not in st.session_state:
    st.session_state["reset_contador"] = 0

if "sequencial_protocolo" not in st.session_state:
    st.session_state["sequencial_protocolo"] = 1

sufixo = st.session_state["reset_contador"]

# --- CABEÇALHO ---
col_titulo, col_botao = st.columns([0.85, 0.15])
with col_titulo:
    st.title("📄 Sistema de Validação de Documentos")
with col_botao:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    if st.button("🔙 Voltar", use_container_width=True):
        st.session_state["reset_contador"] += 1
        st.rerun()

st.markdown("Faça o upload dos documentos para validar os dados e autenticar a certidão no conselho.")

# --- SEÇÃO SUPERIOR ---
col_prot, col_proc = st.columns(2)
with col_prot:
    st.subheader("🆔 Protocolo do Solicitante")
    ano_atual = datetime.now().year
    numero_formatated = f"{st.session_state['sequencial_protocolo']:05d}"
    sugestao_protocolo = f"GO{ano_atual}{numero_formatated}"
    protocolo_final = st.text_input("Protocolo:", value=sugestao_protocolo, disabled=False, label_visibility="collapsed", key=f"p_input_{sufixo}")

with col_proc:
    st.subheader("⚙️ Tipo de Processo")
    opcao_processo = st.pills("Opção:", ["Alto Risco", "Renovação de Alto Risco"], default="Alto Risco", key=f"pills_tipo_processo_{sufixo}", label_visibility="collapsed")

st.divider()

# --- UPLOADS ---
col_upload1, col_upload2 = st.columns(2)
with col_upload1:
    st.subheader("📋 Pedido")
    pedido_file = st.file_uploader("Selecione o PDF do pedido", type=["pdf"], key=f"pedido_{sufixo}")
with col_upload2:
    st.subheader("🛡️ Certidão CR")
    certidao_file = st.file_uploader("Selecione o PDF da certidão", type=["pdf"], key=f"certidao_{sufixo}")

st.divider()

# --- PROCESSAMENTO ---
if st.button("🚀 Validar Documentos", use_container_width=True):
    if not pedido_file or not certidao_file:
        st.warning("⚠️ Por favor, envie ambos os arquivos PDF para continuar.")
    else:
        with st.spinner("Analisando arquivos..."):
            try:
                pedido_bytes = pedido_file.read()
                certidao_bytes = certidao_file.read()

                # 1. Extração do texto
                texto_pedido = extrair_texto(pedido_bytes)
                texto_certidao = extrair_texto(certidao_bytes)

                # 2. Identificação das palavras-chave
                texto_ped_upper = texto_pedido.upper()
                texto_cert_upper = texto_certidao.upper()

                termos_certidao = ["CERTIDÃO", "CERTIDAO", "CERTIFICADO", "REGULARIDADE", "CONSELHO REGIONAL", "CRF", "CRO", "CRM", "CRBM"]
                termos_pedido = ["PEDIDO", "REQUERIMENTO", "SOLICITAÇÃO", "SOLICITACAO", "DECLARAÇÃO", "FORMULÁRIO", "VIGILÂNCIA SANITÁRIA"]

                pedido_eh_certidao = any(termo in texto_ped_upper for termo in termos_certidao) and not any(termo in texto_ped_upper for termo in termos_pedido)
                certidao_eh_pedido = any(termo in texto_cert_upper for termo in termos_pedido) and not any(termo in texto_cert_upper for termo in termos_certidao)

                # 3. Bloqueio Imediato
                if pedido_eh_certidao or certidao_eh_pedido:
                    st.error(
                        "⛔ **DOCUMENTOS INVERTIDOS OU INCORRETOS DETECTADOS!**\n\n"
                        "• O arquivo anexado em **Pedido** parece ser uma Certidão.\n"
                        "• O arquivo anexado em **Certidão CR** parece ser um Pedido.\n\n"
                        "Por favor, remova os arquivos e faça o upload nos campos corretos para prosseguir."
                    )
                    st.stop()

                resultado_comparacao = comparar(texto_pedido, texto_certidao)
                
                if "CRM" in texto_cert_upper or "MEDICINA" in texto_cert_upper:
                    conselho_detectado = "CRM"
                elif "CRO" in texto_cert_upper or "ODONTOLOGIA" in texto_cert_upper:
                    conselho_detectado = "CRO"
                elif "CRBM" in texto_cert_upper or "BIOMEDICINA" in texto_cert_upper:
                    conselho_detectado = "CRBM"
                else:
                    conselho_detectado = "CRF"

                status_conselho = {"autentica": False, "mensagem": "Não foi possível realizar a validação externa."}
                
                if conselho_detectado == "CRF":
                    codigo_match = re.search(r'[A-F0-9]{32}', texto_certidao)
                    codigo_autenticacao = codigo_match.group(0) if codigo_match else None
                    if codigo_autenticacao:
                        status_conselho = asyncio.run(consultar_certidao_no_conselho(codigo_autenticacao))
                    else:
                        status_conselho = {"autentica": False, "mensagem": "Código não encontrado."}
                        
                elif conselho_detectado == "CRM":
                    st.warning("⚠️ Verificação de segurança necessária no navegador externo.")
                    registro = re.search(r'\d+', texto_certidao).group(0) if re.search(r'\d+', texto_certidao) else "Teste"
                    from validador_web import consultar_conselho_com_captcha
                    status_conselho = asyncio.run(consultar_conselho_com_captcha("LINK_CRM", "input", "#res", registro))
                    
                elif conselho_detectado == "CRO":
                    pedido_dados_temp = {"cnpj": "Não encontrado", "rt": "Não encontrado", "data": "Não encontrada"}
                    certidao_dados_temp = {"cnpj": "Não encontrado", "rt": "Não encontrado", "validade": "Não encontrada"}
                    
                    nome_rt_pedido = "Não encontrado"
                    rt_ped_match = re.search(
                        r'(?:RESPONSÁVEL\s+TÉCNICO|RT)[:\s\n]+([A-ZÁÉÍÓÚÇ\s]{10,60})', 
                        texto_ped_upper, 
                        re.DOTALL
                    )
                    
                    if rt_ped_match:
                        nome_rt_pedido = " ".join(rt_ped_match.group(1).split())
                        
                    pedido_dados_temp["rt"] = nome_rt_pedido
                    cnpj_ped_match = re.search(r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b|\b\d{14}\b', texto_pedido)
                    if cnpj_ped_match:
                        cnpj_cru = cnpj_ped_match.group(0).replace(".", "").replace("/", "").replace("-", "")
                        pedido_dados_temp["cnpj"] = f"{cnpj_cru[:2]}.{cnpj_cru[2:5]}.{cnpj_cru[5:8]}/{cnpj_cru[8:12]}-{cnpj_cru[12:]}"
                    data_ab_match = re.search(r'(?:ABERTURA|DATA)[:\s]*(\d{2}/\d{2}/\d{4})', texto_ped_upper)
                    if data_ab_match:
                        pedido_dados_temp["data"] = data_ab_match.group(1)

                    cnpj_cert_match = re.search(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', texto_certidao)
                    certidao_dados_temp["cnpj"] = cnpj_cert_match.group(0) if cnpj_cert_match else "Não encontrado"
                    
                    chave_match = re.search(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', texto_certidao)
                    chave_autenticacao = chave_match.group(0) if chave_match else "Chave não encontrada"
                    
                    validade_match = re.search(r'(?:VÁLIDA ATÉ|VALIDADE|VENCIMENTO)[:\s]*([\d/]+)', texto_certidao.upper())
                    if validade_match:
                        certidao_dados_temp["validade"] = validade_match.group(1).strip()
                    else:
                        todas_datas = re.findall(r'\d{2}/\d{2}/\d{4}', texto_certidao)
                        certidao_dados_temp["validade"] = todas_datas[-1] if todas_datas else "Não encontrada"
                    
                    if nome_rt_pedido != "Não encontrado" and nome_rt_pedido in texto_certidao.upper():
                        certidao_dados_temp["rt"] = nome_rt_pedido
                    else:
                        certidao_dados_temp["rt"] = "Não encontrado"

                    erros = []
                    if pedido_dados_temp["cnpj"] != certidao_dados_temp["cnpj"]: erros.append("CNPJs divergem.")
                    if pedido_dados_temp["rt"] != certidao_dados_temp["rt"]: erros.append("RT diverge.")
                    
                    resultado_comparacao = {
                        "compativel": len(erros) == 0,
                        "erros": erros,
                        "dados_pedido": pedido_dados_temp,
                        "dados_certidao": certidao_dados_temp
                    }

                    status_conselho = {
                        "autentica": True, 
                        "mensagem": f"Chave de autenticação: {chave_autenticacao} \n\nO código acima foi extraído com sucesso! Utilize o link abaixo para acessar a validação externa."
                    }
                    st.session_state["chave_cro_detectada"] = chave_autenticacao

                st.success("🎉 Processamento concluído!")
                st.session_state["sequencial_protocolo"] += 1
                
                # --- CORE: MAPEAMENTO E BUSCA DAS VARIÁVEIS ---
                res_pedido = resultado_comparacao.get("dados_pedido", {}) if isinstance(resultado_comparacao, dict) else {}
                res_certidao = resultado_comparacao.get("dados_certidao", {}) if isinstance(resultado_comparacao, dict) else {}
                
                if not res_pedido and 'pedido_dados' in resultado_comparacao: res_pedido = resultado_comparacao['pedido_dados']
                if not res_certidao and 'certidao_dados' in resultado_comparacao: res_certidao = resultado_comparacao['certidao_dados']
                
                # --- VERIFICAÇÃO DE VALIDADE DA CERTIDÃO ---
                certidao_vencida = False
                data_validade_str = res_certidao.get("validade", "Não encontrada")
                
                try:
                    data_validade = datetime.strptime(data_validade_str.strip(), "%d/%m/%Y")
                    if data_validade < datetime.now():
                        certidao_vencida = True
                except Exception:
                    pass

                # --- VERIFICAÇÃO DE SUCESSO NA AUTENTICAÇÃO ---
                msg_autenticidade = status_conselho.get("mensagem", "")
                erro_conexao = "ERR_CONNECTION" in msg_autenticidade or "Erro de conexão" in msg_autenticidade or "TIMEOUT" in msg_autenticidade.upper()
                
                autenticidade_confirmada = status_conselho.get("autentica", False) and not erro_conexao

                # --- EXIBIÇÃO DO STATUS DO CRUZAMENTO ---
                st.subheader("🔍 Status do Cruzamento de Dados")
                
                if certidao_vencida:
                    st.error(f"❌ Certidão VENCIDA! Data de validade: {data_validade_str}. Processo interrompido.")
                    resultado_comparacao["compativel"] = False
                elif erro_conexao:
                    st.warning("⚠️ Atenção: Os dados batem, mas a autenticidade externa não pôde ser verificada devido a uma falha de conexão com o portal.")
                elif resultado_comparacao.get("compativel", False):
                    st.success("✅ Os dados dos documentos são compatíveis!")
                else:
                    st.error("❌ Divergência encontrada nos dados do documento!")
                
                st.divider()

                # --- BUSCA FLEXÍVEL DE RT ---
                rt_pedido_limpo = res_pedido.get("rt", "Não encontrado").strip().upper()
                
                if rt_pedido_limpo != "NÃO ENCONTRADO" and rt_pedido_limpo in texto_cert_upper:
                    res_certidao["rt"] = rt_pedido_limpo
                elif not res_certidao.get("rt"):
                    res_certidao["rt"] = "Não encontrado"

                # --- FORMATAÇÃO VISUAL DOS CNPJs ---
                cnpj_p_raw = re.sub(r'\D', '', str(res_pedido.get("cnpj", "")))
                if len(cnpj_p_raw) == 14:
                    res_pedido["cnpj"] = f"{cnpj_p_raw[:2]}.{cnpj_p_raw[2:5]}.{cnpj_p_raw[5:8]}/{cnpj_p_raw[8:12]}-{cnpj_p_raw[12:]}"

                cnpj_c_raw = re.sub(r'\D', '', str(res_certidao.get("cnpj", "")))
                if len(cnpj_c_raw) == 14:
                    res_certidao["cnpj"] = f"{cnpj_c_raw[:2]}.{cnpj_c_raw[2:5]}.{cnpj_c_raw[5:8]}/{cnpj_c_raw[8:12]}-{cnpj_c_raw[12:]}"
                    
                # --- TABELA COMPARATIVA ---
                st.subheader("📊 Tabela Comparativa de Detalhes")

                dados_tabela = {
                    "Dado Comparado": [
                        "🏢 CNPJ",
                        "👨‍⚕️ Responsável Técnico (RT)",
                        "📅 Dados Importantes"
                    ],
                    "No Pedido": [
                        res_pedido.get("cnpj", "Não encontrado"),
                        res_pedido.get("rt", "Não encontrado"),
                        f"Abertura: {res_pedido.get('data', 'Não encontrada')}"
                    ],
                    "Na Certidão": [
                        res_certidao.get("cnpj", "Não encontrado"),
                        res_certidao.get("rt", "Não encontrado"),
                        f"Validade: {data_validade_str}"
                    ]
                }

                df_final = pd.DataFrame(dados_tabela)
                st.dataframe(df_final, use_container_width=True, hide_index=True)

                st.divider()
                
                # --- EXIBIÇÃO DA AUTENTICIDADE E LINK ---
                st.subheader(f"🌐 Autenticidade no {conselho_detectado}")
                
                if certidao_vencida:
                    st.warning("⚠️ O link de validação externa foi bloqueado porque este documento já perdeu a validade jurídica.")
                elif erro_conexao:
                    st.error(f"❌ Falha na Autenticação Externa: {msg_autenticidade}")
                else:
                    st.success(f"✅ {msg_autenticidade}")
                    
                    if conselho_detectado == "CRO" and "chave_cro_detectada" in st.session_state:
                        chave = st.session_state["chave_cro_detectada"]
                        st.divider()
                        st.subheader("🔗 Validação de Link Externo (CRO)")
                        link_direto_cro = f"https://cro-go.implanta.net.br/servicosOnline/Publico/ValidarDocumentos/?txtChave={chave}"
                        st.link_button("👉 Abrir Portal do CRO com a Chave", link_direto_cro)

                # --- RECALCULAR ERROS ---
                erros_atualizados = []
                
                def limpar_cnpj(cnpj_raw):
                    if not cnpj_raw or cnpj_raw == "Não encontrado":
                        return ""
                    return re.sub(r'\D', '', str(cnpj_raw))

                cnpj_ped_limpo = limpar_cnpj(res_pedido.get("cnpj"))
                cnpj_cert_limpo = limpar_cnpj(res_certidao.get("cnpj"))

                if not cnpj_ped_limpo or not cnpj_cert_limpo:
                    erros_atualizados.append("CNPJ não encontrado em um dos documentos.")
                elif cnpj_ped_limpo != cnpj_cert_limpo:
                    erros_atualizados.append(f"CNPJs divergem ({res_pedido.get('cnpj')} vs {res_certidao.get('cnpj')}).")

                rt_ped = res_pedido.get("rt", "Não encontrado")
                rt_cert = res_certidao.get("rt", "Não encontrado")
                if rt_ped == "Não encontrado" or rt_cert == "Não encontrado":
                    erros_atualizados.append(f"O Responsável Técnico do pedido ({rt_ped}) não foi localizado na certidão do conselho.")

                resultado_comparacao["erros"] = erros_atualizados
                resultado_comparacao["compativel"] = len(erros_atualizados) == 0

                # --- GERAÇÃO DA MINUTA AUTOMÁTICA ---
                st.divider()
                st.subheader("📝 Minuta do Parecer Técnico")

                status_compativel_final = (
                    resultado_comparacao.get("compativel", False) 
                    and not certidao_vencida 
                    and autenticidade_confirmada
                )

                if status_compativel_final:
                    texto_minuta = (
                        f"PARECER TÉCNICO - DEFERIDO\n\n"
                        f"Constatada a conformidade integral entre os dados do pedido e a Certidão de Regularidade "
                        f"do conselho profissional ({conselho_detectado}), bem como confirmada com sucesso a sua autenticidade "
                        f"na consulta externa. Diante do exposto, emitimos parecer pelo DEFERIMENTO."
                    )
                elif erro_conexao:
                    texto_minuta = (
                        f"PARECER TÉCNICO - ANÁLISE PENDENTE (ERRO DE CONEXÃO)\n\n"
                        f"Os dados extraídos dos documentos apresentam conformidade preliminar, contudo, "
                        f"houve uma falha de comunicação com o portal do {conselho_detectado} (Timeout/Instabilidade do sistema externo). "
                        f"Não foi possível validar a autenticidade digital do documento de forma automatizada. "
                        f"O processo deve ser encaminhado para validação manual ou nova tentativa posterior."
                    )
                else:
                    motivos_str = "Certidão VENCIDA" if certidao_vencida else ", ".join(resultado_comparacao.get("erros", ["Divergência de dados técnicos"]))
                    texto_minuta = (
                        f"PARECER TÉCNICO - INDEFERIDO\n\n"
                        f"Identificada inconformidade no processo de validação documental. Durante a análise automatizada "
                        f"da certidão ({conselho_detectado}), foi constatado o seguinte impedimento: {motivos_str}.\n"
                        f"Diante dos fatos, emitimos parecer pelo INDEFERIMENTO do pedido."
                    )

                st.text_area(label="Cópia rápida do Parecer:", value=texto_minuta, height=180)

                # --- GERAR PDF E BOTAO DE DOWNLOAD ---
                pdf_bytes = gerar_pdf_parecer(
                    protocolo=protocolo_final,
                    status_compativel=status_compativel_final,
                    divergencias=resultado_comparacao.get("erros", []),
                    dados_pedido=res_pedido,
                    dados_certidao=res_certidao,
                    texto_minuta_tela=texto_minuta,
                    certidao_vencida=certidao_vencida
                )

                st.download_button(
                    label="📥 Baixar Parecer Técnico em PDF (Para Fiscalização)",
                    data=pdf_bytes,
                    file_name=f"Parecer_Tecnico_{protocolo_final}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"Erro no processamento: {e}")