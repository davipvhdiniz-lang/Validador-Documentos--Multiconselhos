import streamlit as st
import re
import asyncio
import sys
import pandas as pd
from datetime import datetime
from leitor_pdf import extrair_texto
from comparador import comparar
from validador_web import consultar_certidao_no_conselho

# Configuração da página do Streamlit
st.set_page_config(page_title="Sistema de Validação de Documentos", page_icon="📄", layout="wide")

# 1. Inicializa o contador de reset se ele não existir na memória
if "reset_contador" not in st.session_state:
    st.session_state["reset_contador"] = 0

# 2. Inicializa o sequencial do protocolo (começa em 1 se não existir)
if "sequencial_protocolo" not in st.session_state:
    st.session_state["sequencial_protocolo"] = 1

# Cria o sufixo dinâmico para limpar os arquivos no 'Voltar'
sufixo = st.session_state["reset_contador"]

# --- CABEÇALHO COM BOTÃO RETORNAR LADO A LADO ---
col_titulo, col_botao = st.columns([0.85, 0.15])

with col_titulo:
    st.title("📄 Sistema de Validação de Documentos")

with col_botao:
    st.write("##") 
    if st.button("🔙 Voltar", use_container_width=True):
        st.session_state["reset_contador"] += 1
        st.rerun()

st.markdown("Faça o upload dos documentos para validar os dados e autenticar a certidão no conselho.")

# --- SEÇÃO SUPERIOR: PROTOCOLO E TIPO (LADO A LADO) ---
col_prot, col_proc = st.columns(2)

with col_prot:
    st.subheader("🆔 Protocolo do Solicitante")
    ano_atual = datetime.now().year
    numero_formatado = f"{st.session_state['sequencial_protocolo']:05d}"
    sugestao_protocolo = f"GO{ano_atual}{numero_formatado}"
    
    protocolo_final = st.text_input(
        "Protocolo da validação:",
        value=sugestao_protocolo,
        disabled=False,
        label_visibility="collapsed",
        key=f"p_input_{sufixo}"
    )

with col_proc:
    st.subheader("⚙️ Tipo de Processo")
    opcao_processo = st.pills(
        "Selecione uma opção:",
        ["Alto Risco", "Renovação de Alto Risco"],
        default="Alto Risco",
        key=f"pills_tipo_processo_{sufixo}",  
        label_visibility="collapsed"
    )

st.divider()

# --- CAMPOS DE UPLOAD ---
col_upload1, col_upload2 = st.columns(2)

with col_upload1:
    st.subheader("📋 Pedido")
    pedido_file = st.file_uploader("Selecione o PDF do pedido", type=["pdf"], key=f"pedido_{sufixo}")

with col_upload2:
    st.subheader("🛡️ Certidão CRF")
    certidao_file = st.file_uploader("Selecione o PDF da certidão", type=["pdf"], key=f"certidao_{sufixo}")

st.divider()

# --- BOTÃO DE VALIDAR E PROCESSAMENTO ---
if st.button("🚀 Validar Documentos", use_container_width=True):
    if not pedido_file or not certidao_file:
        st.warning("⚠️ Por favor, envie ambos os arquivos PDF para continuar.")
    else:
        with st.spinner("Analisando arquivos... Por favor, aguarde."):
            try:
                pedido_bytes = pedido_file.read()
                certidao_bytes = certidao_file.read()
                
                texto_pedido = extrair_texto(pedido_bytes)
                texto_certidao = extrair_texto(certidao_bytes)
                
                resultado_comparacao = comparar(texto_pedido, texto_certidao)
                
                # -------------------------------------------------------------
                # 🧠 SISTEMA DE ROTEAMENTO MULTICONSELIHOS (CRM / CRO / CRBM / CRF)
                # -------------------------------------------------------------
                texto_certidao_alta = texto_certidao.upper()
                if "CRM" in texto_certidao_alta or "MEDICINA" in texto_certidao_alta:
                    conselho_detectado = "CRM"
                elif "CRO" in texto_certidao_alta or "ODONTOLOGIA" in texto_certidao_alta:
                    conselho_detectado = "CRO"
                elif "CRBM" in texto_certidao_alta or "BIOMEDICINA" in texto_certidao_alta:
                    conselho_detectado = "CRBM"
                else:
                    conselho_detectado = "CRF"

                status_conselho = {"autentica": False, "mensagem": "Não foi possível realizar a validação externa."}
                
                # 🟢 CASO 1: SEU FLUXO ORIGINAL DO CRF-GO (100% INTACTO)
                if conselho_detectado == "CRF":
                    codigo_match = re.search(r'[A-F0-9]{32}', texto_certidao)
                    codigo_autenticacao = codigo_match.group(0) if codigo_match else None
                    
                    if codigo_autenticacao:
                        status_conselho = asyncio.run(consultar_certidao_no_conselho(codigo_autenticacao))
                    else:
                        status_conselho = {"autentica": False, "mensagem": "Código de autenticação não encontrado na certidão."}
                        
                # 🔵 CASO 2: MEDICINA (CRM)
                elif conselho_detectado == "CRM":
                    st.warning("⚠️ O portal do CRM exige verificação de segurança. Uma janela do navegador foi aberta. Preencha o CAPTCHA nela para continuar.")
                    registro = re.search(r'\d+', texto_certidao).group(0) if re.search(r'\d+', texto_certidao) else "Teste"
                    from validador_web import consultar_conselho_com_captcha
                    status_conselho = asyncio.run(consultar_conselho_com_captcha(
                        url_site="COLE_AQUI_O_LINK_DO_PORTAL_DE_BUSCA_DO_CRM", 
                        input_selector="input[id*='crm']",       
                        seletor_resultado="#resultado-medico",   
                        dado_busca=registro
                    ))
                    
                # 🟡 CASO 3: ODONTOLOGIA (CRO)
                elif conselho_detectado == "CRO":
                    st.warning("⚠️ O portal do CRO exige verificação de segurança. Uma janela do navegador foi aberta. Preencha o CAPTCHA nela para continuar.")
                    registro = re.search(r'\d+', texto_certidao).group(0) if re.search(r'\d+', texto_certidao) else "Teste"
                    from validador_web import consultar_conselho_com_captcha
                    status_conselho = asyncio.run(consultar_conselho_com_captcha(
                        url_site="COLE_AQUI_O_LINK_DO_PORTAL_DE_BUSCA_DO_CRO", 
                        input_selector="input[type='text']",
                        seletor_resultado="#resultado-odonto",
                        dado_busca=registro
                    ))
                    
                # 🟠 CASO 4: BIOMEDICINA (CRBM)
                elif conselho_detectado == "CRBM":
                    st.warning("⚠️ O portal da Biomedicina exige verificação de segurança. Uma janela do navegador foi aberta. Preencha o CAPTCHA nela para continuar.")
                    registro = re.search(r'\d+', texto_certidao).group(0) if re.search(r'\d+', texto_certidao) else "Teste"
                    from validador_web import consultar_conselho_com_captcha
                    status_conselho = asyncio.run(consultar_conselho_com_captcha(
                        url_site="COLE_AQUI_O_LINK_DO_PORTAL_DE_BUSCA_DO_CRBM", 
                        input_selector="input[type='text']",
                        seletor_resultado="#resultado-biomedicina",
                        dado_busca=registro
                    ))
                # -------------------------------------------------------------

                st.success("🎉 Processamento concluído!")
                st.session_state["sequencial_protocolo"] += 1
                
                # =========================================================
                # 🔄 EXIBIÇÃO DOS RESULTADOS (IGUALZINHO AO SEU ORIGINAL)
                # =========================================================
                
                # 1. Status do Cruzamento de Dados
                st.subheader("🔍 Status do Cruzamento de Dados")
                if resultado_comparacao.get("compativel", False):
                    st.success("✅ Os dados dos documentos são compatíveis!")
                else:
                    st.error("❌ Divergência encontrada!")
                    for erro in resultado_comparacao.get("erros", []):
                        st.write(f"- {erro}")
                
                st.divider()
                
                # 2. Tabela Comparativa de Detalhes
                st.subheader("📊 Tabela Comparativa de Detalhes")
                pedido_dados = resultado_comparacao.get("dados_pedido", {})
                certidao_dados = resultado_comparacao.get("dados_certidao", {})
                
                tabela_dados = {
                    "Dado Comparado": [
                        "🏢 CNPJ", 
                        "👨‍⚕️ Responsável Técnico (RT)", 
                        "🔢 CNAE", 
                        "📅 Data Importante"
                    ],
                    "No Pedido": [
                        pedido_dados.get("cnpj", "Não encontrado"),
                        pedido_dados.get("rt", "Não encontrado"),
                        pedido_dados.get("cnae", "Não encontrado"), 
                        f"Abertura: {pedido_dados.get('data', 'Não encontrada')}"
                    ],
                    "Na Certidão": [
                        certidao_dados.get("cnpj", "Não encontrado"),
                        certidao_dados.get("rt", "Não encontrado"),
                        certidao_dados.get("cnae", "Não encontrado"), 
                        f"Validade: {certidao_dados.get('validade', 'Não encontrada')}"
                    ]
                }
                
                df = pd.DataFrame(tabela_dados)
                st.table(df)
                
                st.divider()
                
                # 3. Exibição Dinâmica da Autenticidade (Adapta o título conforme o conselho)
                st.subheader(f"🌐 Autenticidade no {conselho_detectado}-GO" if conselho_detectado == "CRF" else f"🌐 Autenticidade no {conselho_detectado}")
                mensagem_conselho = status_conselho.get('mensagem', '')
                if status_conselho.get("autentica", False):
                    if "ATENÇÃO" in mensagem_conselho:
                        st.warning(f"⚠️ {mensagem_conselho}")
                    else:
                        st.success(f"✅ {mensagem_conselho}")
                else:
                    st.error(f"❌ {mensagem_conselho}")
                    
            except Exception as e:
                st.error(f"Ocorreu um erro inesperado ao processar: {e}")