from datetime import datetime
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


NOME_JOGO = "Clive Barker's Hellraiser: Revival"
URL_LOJA = "https://store.steampowered.com/"
PASTA_EVIDENCIAS = Path(__file__).resolve().parents[1] / "screenshots"


@pytest.fixture
def navegador(request):
    """Cria um Chrome e salva uma evidência ao final do teste"""
    opcoes = webdriver.ChromeOptions()
    opcoes.add_argument("--start-maximized")
    opcoes.add_argument("--lang=pt-BR")

    driver = webdriver.Chrome(options=opcoes)
    try:
        yield driver
    finally:
        PASTA_EVIDENCIAS.mkdir(parents=True, exist_ok=True)
        nome_arquivo = (
            f"{request.node.name}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        caminho_evidencia = PASTA_EVIDENCIAS / nome_arquivo
        try:
            if not driver.save_screenshot(str(caminho_evidencia)):
                raise RuntimeError(
                    f"Não foi possível salvar a evidência em {caminho_evidencia}"
                )
            print(f"\nEvidência salva em: {caminho_evidencia}")
        finally:
            driver.quit()


def pesquisar_jogo(navegador):
    """Pesquisa Hellraiser na loja e retorna as linhas de resultado exibidas."""
    espera = WebDriverWait(navegador, 30)
    navegador.get(URL_LOJA)

    campo_pesquisa = espera.until(
        EC.visibility_of_element_located((By.NAME, "term"))
    )
    campo_pesquisa.clear()
    campo_pesquisa.send_keys(NOME_JOGO, Keys.ENTER)

    return espera.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "#search_resultsRows a.search_result_row")
        )
    )


def titulo_do_resultado(resultado):
    return resultado.find_element(
        By.CSS_SELECTOR, ".search_name .title"
    ).text.strip()


def test_RF01_pesquisa_e_filtragem(navegador):
    """RF01: pesquisa o jogo e valida o primeiro resultado apresentado."""
    resultados = pesquisar_jogo(navegador)

    assert resultados, "A pesquisa não apresentou resultados."
    assert titulo_do_resultado(resultados[0]) == NOME_JOGO


def test_RF02_exibicao_detalhes_do_produto(navegador):
    """RF02: abre o primeiro resultado e valida os detalhes essenciais."""
    espera = WebDriverWait(navegador, 30)
    resultados = pesquisar_jogo(navegador)

    assert resultados, "A pesquisa não apresentou resultados."
    assert titulo_do_resultado(resultados[0]) == NOME_JOGO
    resultados[0].click()

    titulo = espera.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".apphub_AppName"))
    )
    assert titulo.text.strip() == NOME_JOGO

    descricao = espera.until(
        EC.presence_of_element_located((By.ID, "game_area_description"))
    )
    assert descricao.text.strip(), "A descrição do jogo está vazia."

    galeria = espera.until(
        EC.visibility_of_element_located((By.ID, "game_highlights"))
    )
    midias = espera.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "#game_highlights img, #game_highlights video")
        )
    )
    assert galeria.is_displayed(), "A galeria de mídia não está visível."
    assert midias, "A página não apresenta capturas de tela nem vídeos."

    requisitos = espera.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".game_area_sys_req.sysreq_content.active")
        )
    )
    assert requisitos.text.strip(), "Os requisitos de sistema não foram exibidos."

    # Deixa a galeria no topo para que a evidência final mostre o trailer
    trailer = galeria.find_element(By.CSS_SELECTOR, ".highlight_ctn")
    navegador.execute_script(
        "arguments[0].scrollIntoView({block: 'start', inline: 'nearest'});",
        trailer,
    )
