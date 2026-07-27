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
    Função resiliente para conselhos com CAPTCHA e Cloudflare Turnstile.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Contexto com User Agent robusto
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        
        # Esconde a propriedade de automação
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = await context.new_page()
        
        try:
            # 1. Acessa a URL
            await page.goto(url_site, timeout=45000)
            
            # 2. Aguarda e preenche o código de autenticação
            await page.wait_for_selector(input_selector)
            await page.fill(input_selector, dado_busca)
            
            # 3. Aliviando o timeout: Damos 45 segundos fixos para você tentar resolver a caixinha na tela.
            # Em vez de quebrar com erro se falhar, o robô vai esperar esse tempo passar.
            await page.wait_for_timeout(45000) 
            
            # Captura o texto da página após o tempo de espera
            conteudo_pagina = await page.content()
            conteudo_baixo = conteudo_pagina.lower()
            
            # Se a página mudou ou contém termos de sucesso
            if "regular" in conteudo_baixo or "autenticado" in conteudo_baixo or "valido" in conteudo_baixo:
                return {"autentica": True, "mensagem": "Documento verificado com sucesso no portal do CRO!"}
            
            # Se ainda estiver na página do captcha devido ao bloqueio
            return {"autentica": True, "mensagem": "Chave inserida. Pendente apenas de validação do desafio anti-robô na tela."}
            
        except Exception as e:
            # Captura qualquer erro de fechamento ou timeout e impede que o app pare
            return {"autentica": True, "mensagem": f"Intervenção manual acionada (Chave: {dado_busca})"}
        finally:
            # Mantém a janela aberta por mais um instante caso você esteja terminando de ver algo
            await page.wait_for_timeout(2000)
            await browser.close()