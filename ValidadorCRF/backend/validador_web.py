import asyncio
from playwright.async_api import async_playwright

URL_CRF = "https://crfgo-emcasa.cisantec.com.br/crf-em-casa/consulta/certidao/inicial.jsf"

async def consultar_certidao_no_conselho(codigo_autenticacao: str) -> dict:
    """
    Acessa o portal do CRF-GO, insere o código de autenticação e valida
    se a certidão é legítima e ativa no conselho.
    """
    async with async_playwright() as p:
        # Abre o navegador em segundo plano (headless=True)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # 1. Acessa a página de consulta
            await page.goto(URL_CRF, timeout=30000)
            
            # 2. Localiza o campo de input para o código de autenticação
            input_selector = "input[type='text']" 
            await page.wait_for_selector(input_selector)
            
            # Preenche o código extraído da certidão
            await page.fill(input_selector, codigo_autenticacao)
            
            # 3. Clica no botão de Consultar / Validar
            botao_consultar = page.locator("button:has-text('Consultar'), input[type='submit'], button[id*='btn']")
            await botao_consultar.first.click()
            
            # Aguarda a resposta do site
            await page.wait_for_load_state("networkidle")
            
            # Obtém o conteúdo da página e passa para minúsculo para facilitar a busca
            conteudo_pagina = await page.content()
            conteudo_baixo = conteudo_pagina.lower()

            # Lista de termos que indicam que a certidão é inválida ou não existe
            se_invalida = ["inexistente", "não encontrada", "inválido", "não conferem", "incorreto"]
            for termo in se_invalida:
                if termo in conteudo_baixo:
                    return {
                        "autentica": False,
                        "mensagem": "A certidão não foi encontrada ou o código de autenticação é inválido perante o conselho."
                    }
            
            # --- NOVA VERIFICAÇÃO: DETECTA O ALERTA DE CERTIDÃO MAIS ATUALIZADA ---
            texto_alerta = "possui outra certidão de regularidade mais atualizada"
            if texto_alerta in conteudo_baixo:
                return {
                    "autentica": True,  # Ela ainda é autêntica!
                    "mensagem": "Certidão válida, porém ATENÇÃO: Este estabelecimento possui outra Certidão de Regularidade mais atualizada no CRF-GO! Solicite o documento mais recente."
                }

            # ... (todo o resto do seu código igualzinho para cima)

            # Caso encontre dados normais do estabelecimento ou mensagem padrão de regularidade:
            if "regular" in conteudo_baixo or codigo_autenticacao.lower() in conteudo_baixo:
                return {
                    "autentica": True,
                    "mensagem": "Certidão validada com SUCESSO no portal do CRF-GO! Documento autêntico e atualizado."
                }
                
            return {
                "autentica": False,
                "mensagem": "Não foi possível confirmar a autenticidade. Verifique o código manualmente."
            }
            
        except Exception as e:
            return {
                "autentica": False,
                "mensagem": f"Erro de conexão com o portal do CRF: {str(e)}"
            }
        finally:
            await browser.close()

# =====================================================================
# 🚀 ESPAÇO ADICIONADO: COLE A NOVA FUNÇÃO EXATAMENTE AQUI EMBAIXO!
# =====================================================================

async def consultar_conselho_com_captcha(url_site: str, input_selector: str, seletor_resultado: str, dado_busca: str) -> dict:
    """
    Nova função para conselhos com CAPTCHA (CRM, CRO, CRBM).
    Abre o navegador visível (headless=False) e espera a intervenção humana.
    """
    async with async_playwright() as p:
        # A janela VAI ABRIR na tela (headless=False) para você resolver o Captcha
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # 1. Acessa o site do conselho específico
            await page.goto(url_site, timeout=45000)
            
            # 2. Aguarda o campo de texto aparecer e preenche o registro
            await page.wait_for_selector(input_selector)
            await page.fill(input_selector, dado_busca)
            
            # [PAUSA DO CAPTCHA]
            # O robô vai parar aqui por até 60 segundos esperando você resolver 
            # o Captcha na tela e clicar em buscar. Quando a tela de resultado carregar, ele continua.
            await page.wait_for_selector(seletor_resultado, timeout=60000)
            
            # 3. O robô raspa o conteúdo final sozinho
            conteudo_pagina = await page.content()
            conteudo_baixo = conteudo_pagina.lower()
            
            if dado_busca.lower() in conteudo_baixo or "ativo" in conteudo_baixo or "regular" in conteudo_baixo:
                return {"autentica": True, "mensagem": "Documento validado com sucesso após verificação de segurança!"}
                
            return {"autentica": False, "mensagem": "Profissional ou certidão não encontrados no portal externo."}
            
        except Exception as e:
            return {"autentica": False, "mensagem": f"Validação interrompida ou erro: {str(e)}"}
        finally:
            await browser.close()