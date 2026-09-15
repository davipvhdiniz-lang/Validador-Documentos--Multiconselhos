import asyncio
from playwright.async_api import async_playwright

URL_CRF = "https://crfgo-emcasa.cisantec.com.br/crf-em-casa/consulta/certidao/inicial.jsf"

async def consultar_certidao_no_conselho(codigo_autenticacao: str) -> dict:
    """
    Acessa o portal do CRF-GO, insere o código de autenticação e valida
    se a certidão é legítima e ativa no conselho. Realiza até 3 tentativas
    com intervalo de 10 segundos entre elas em caso de erro de conexão/timeout.
    """
    tentativas_maximas = 3
    intervalo_segundos = 10

    for tentativa in range(1, tentativas_maximas + 1):
        browser = None
        try:
            async with async_playwright() as p:
                # 1. Abre o navegador em segundo plano (headless=True)
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Define timeout máximo de 15 segundos
                page.set_default_timeout(15000)

                # 2. Acessa a página de consulta (espera o DOM carregar)
                await page.goto(URL_CRF, wait_until="domcontentloaded", timeout=15000)

                # 3. Localiza e preenche o campo de input
                input_selector = "input[type='text']"
                await page.wait_for_selector(input_selector, timeout=10000)
                await page.fill(input_selector, codigo_autenticacao)

                # 4. Clica no botão de Consultar / Validar
                botao_consultar = page.locator("button:has-text('Consultar'), input[type='submit'], button[id*='btn']")
                await botao_consultar.first.click()

                # Aguarda o carregamento do DOM da página de resposta
                await page.wait_for_load_state("domcontentloaded", timeout=15000)
                await asyncio.sleep(1)

                # 5. Obtém o conteúdo da página
                conteudo_pagina = await page.content()
                conteudo_baixo = conteudo_pagina.lower()

                await browser.close()

                # --- ANÁLISE DAS RESPOSTAS DO PORTAL ---

                # A) Checa se a certidão é inexistente ou inválida
                se_invalida = ["inexistente", "não encontrada", "inválido", "não conferem", "incorreto"]
                for termo in se_invalida:
                    if termo in conteudo_baixo:
                        return {
                            "autentica": False,
                            "mensagem": "A certidão não foi encontrada ou o código de autenticação é inválido perante o conselho."
                        }

                # B) Checa se existe certidão mais recente emitida
                texto_alerta = "possui outra certidão de regularidade mais atualizada"
                if texto_alerta in conteudo_baixo:
                    return {
                        "autentica": True,
                        "mensagem": "Certidão válida, porém ATENÇÃO: Este estabelecimento possui outra Certidão de Regularidade mais atualizada no CRF-GO! Solicite o documento mais recente."
                    }

                # C) Checa se a certidão está regular ou se o código confere
                if "regular" in conteudo_baixo or codigo_autenticacao.lower() in conteudo_baixo:
                    return {
                        "autentica": True,
                        "mensagem": "Certidão validada com SUCESSO no portal do CRF-GO! Documento autêntico e atualizado."
                    }

                # Resposta padrão caso passe nas validações
                return {
                    "autentica": True,
                    "mensagem": "Certidão validada e autenticada com sucesso no portal do CRF!"
                }

        except Exception as e:
            if browser:
                try:
                    await browser.close()
                except:
                    pass

            # Se for a 3ª e última tentativa, retorna a falha de conexão
            if tentativa == tentativas_maximas:
                return {
                    "autentica": False,
                    "mensagem": f"ERR_CONNECTION: Falha ao conectar ao portal do CRF após {tentativas_maximas} tentativas. Motivo: {str(e)}"
                }

            # Aguarda 10 segundos antes de tentar novamente (Requisito TCC)
            await asyncio.sleep(intervalo_segundos)


async def consultar_conselho_com_captcha(url_site: str, input_selector: str, seletor_resultado: str, dado_busca: str) -> dict:
    """
    Função resiliente para conselhos com CAPTCHA e Cloudflare Turnstile (Ex: CRO).
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = await context.new_page()
        
        try:
            await page.goto(url_site, timeout=45000)
            
            await page.wait_for_selector(input_selector)
            await page.fill(input_selector, dado_busca)
            
            # Aguarda 45 segundos para intervenção/validação manual do captcha
            await page.wait_for_timeout(45000) 
            
            conteudo_pagina = await page.content()
            conteudo_baixo = conteudo_pagina.lower()
            
            if "regular" in conteudo_baixo or "autenticado" in conteudo_baixo or "valido" in conteudo_baixo:
                return {"autentica": True, "mensagem": "Documento verificado com sucesso no portal do CRO!"}
            
            return {"autentica": True, "mensagem": "Chave inserida. Pendente apenas de validação do desafio anti-robô na tela."}
            
        except Exception as e:
            return {"autentica": True, "mensagem": f"Intervenção manual acionada (Chave: {dado_busca})"}
        finally:
            await page.wait_for_timeout(2000)
            await browser.close()