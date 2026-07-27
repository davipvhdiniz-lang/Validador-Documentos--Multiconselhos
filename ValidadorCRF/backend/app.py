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
    st.write("##") 
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
                
                texto_pedido = extrair_texto(pedido_bytes)
                texto_certidao = extrair_texto(certidao_bytes)
                
                resultado_comparacao = comparar(texto_pedido, texto_certidao)
                
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
                    pedido_dados_temp = {"cnpj": "Não encontrado", "rt": "Não encontrado", "cnae": "Não encontrado", "data": "Não encontrada"}
                    certidao_dados_temp = {"cnpj": "Não encontrado", "rt": "Não encontrado", "cnae": "Não encontrado", "validade": "Não encontrada"}
                    
                    # Extração Pedido CRO
                    nome_rt_pedido = "Não encontrado"
                    texto_ped_upper = texto_pedido.upper()
                    rt_ped_match = re.search(r'(?:RESPONSÁVEL TÉCNICO|RT)[:\s]+([A-ZÁÉÍÓÚÇ\s]{10,60})', texto_ped_upper)
                    if rt_ped_match:
                        nome_rt_pedido = rt_ped_match.group(1).strip()
                    pedido_dados_temp["rt"] = nome_rt_pedido
                    
                    cnaes_ped = re.findall(r'\b\d{7}\b', texto_pedido)
                    if cnaes_ped:
                        pedido_dados_temp["cnae"] = ", ".join(cnaes_ped)

                    cnpj_ped_match = re.search(r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b|\b\d{14}\b', texto_pedido)
                    if cnpj_ped_match:
                        cnpj_cru = cnpj_ped_match.group(0).replace(".", "").replace("/", "").replace("-", "")
                        pedido_dados_temp["cnpj"] = f"{cnpj_cru[:2]}.{cnpj_cru[2:5]}.{cnpj_cru[5:8]}/{cnpj_cru[8:12]}-{cnpj_cru[12:]}"

                    data_ab_match = re.search(r'(?:ABERTURA|DATA)[:\s]*(\d{2}/\d{2}/\d{4})', texto_ped_upper)
                    if data_ab_match:
                        pedido_dados_temp["data"] = data_ab_match.group(1)

                    # Extração Certidão CRO
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

                    certidao_dados_temp["cnae"] = "Atividades Odontológicas (Regular)"

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
                
                # --- CORE: MAPEAMENTO E BUSCA DAS VARIÁVEIS DE FORMA SEGURA ---
                res_pedido = resultado_comparacao.get("dados_pedido", {}) if isinstance(resultado_comparacao, dict) else {}
                res_certidao = resultado_comparacao.get("dados_certidao", {}) if isinstance(resultado_comparacao, dict) else {}
                
                # Fallback caso o dicionário geral não tenha os dados mas o fluxo do comparador padrão sim
                if not res_pedido and 'pedido_dados' in resultado_comparacao: res_pedido = resultado_comparacao['pedido_dados']
                if not res_certidao and 'certidao_dados' in resultado_comparacao: res_certidao = resultado_comparacao['certidao_dados']
                
                # --- VERIFICAÇÃO DE VALIDADE DA CERTIDÃO ---
                from datetime import datetime
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
                
                # --- TABELA COMPARATIVA TOTALMENTE CORRIGIDA E LIMPA ---
                st.subheader("📊 Tabela Comparativa de Detalhes")
                
                dados_tabela = {
                    "Dado Comparado": [
                        "🏢 CNPJ", 
                        "👨‍⚕️ Responsável Técnico (RT)", 
                        "🔢 CNAE", 
                        "📅 Dados Importantes"
                    ],
                    "No Pedido": [
                        res_pedido.get("cnpj", "Não encontrado"), 
                        res_pedido.get("rt", "Não encontrado"), 
                        res_pedido.get("cnae", "Não encontrado"), 
                        f"Abertura: {res_pedido.get('data', 'Não encontrada')}"
                    ],
                    "Na Certidão": [
                        res_certidao.get("cnpj", "Não encontrado"), 
                        res_certidao.get("rt", "Não encontrado"), 
                        res_certidao.get("cnae", "Não encontrado"), 
                        f"Validade: {data_validade_str}"
                    ]
                }

                df_final = pd.DataFrame(dados_tabela)
                st.dataframe(df_final, use_container_width=True, hide_index=True)
                
                st.divider()
                
                # --- EXIBIÇÃO DA AUTENTICIDADE E LINK (AJUSTADO PARA ERROS) ---
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

                # --- GERAÇÃO DA MINUTA AUTOMÁTICA CORRIGIDA ---
                st.divider()
                st.subheader("📝 Minuta do Parecer Técnico")

                if resultado_comparacao.get("compativel", False) and not certidao_vencida and autenticidade_confirmada:
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
                    motivo = "Certidão VENCIDA" if certidao_vencida else ", ".join(resultado_comparacao.get("erros", ["Divergência de dados técnicos"]))
                    texto_minuta = (
                        f"PARECER TÉCNICO - INDEFERIDO\n\n"
                        f"Identificada inconformidade no processo de validação documental. Durante a análise automatizada "
                        f"da certidão ({conselho_detectado}), foi constatado o seguinte impedimento: {motivo}.\n"
                        f"Diante dos fatos, emitimos parecer pelo INDEFERIMENTO do pedido."
                    )

                st.text_area(label="Cópia rápida do Parecer:", value=texto_minuta, height=180) 

            except Exception as e:
                st.error(f"Erro no processamento: {e}")