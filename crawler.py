import requests
from bs4 import BeautifulSoup
import urllib3
import re
import json
from datetime import datetime

def links_mais_noticias(opcao: int): # varre as páginas de notícias e retorna uma lista de links para cada notícia.
    urls_noticias = []
    
    if opcao == 1: # para coletar os links a partir dos códigos de cada notícia.
        for i in range(10369, 10745): # notícias de 04/06/2024 a 30/06/2025.
            urls_noticias.append(f"https://ufsj.edu.br/noticias_ler.php?codigo_noticia={i}")
            
        # print(urls_noticias)

        return urls_noticias
    
    else: # para coletar os links varrendo as páginas determinadas (site da UFSJ só vai até a página 12).
        for i in range(1, 13):
            r = requests.get(f'https://ufsj.edu.br/mais_noticias.php?pagina={i}', verify=False)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            conteudo_principal = soup.find(id="ufsj-corpo-paginagenerica-conteudo")
            links = conteudo_principal.find_all('a')
            
            urls_noticias_pagina = [f"https://ufsj.edu.br/{link['href']}" for link in links if "noticias_ler" in link['href']]

            urls_noticias += urls_noticias_pagina # atualiza a lista geral com as novas notícias de cada página.
        
        # print(urls_noticias)
        
        return urls_noticias
    

def extrair_texto_noticia(urls: list[str]): # para cada notícia, extrai seu título, data de publicação e seu conteúdo.
    dataset = []
    
    for url in urls:
        try:
            r = requests.get(url, verify=False)
            soup = BeautifulSoup(r.text, 'html.parser')

            conteudo_principal = soup.find(id="ufsj-corpo-paginagenerica-conteudo")
            titulo_noticia = conteudo_principal.find('h1').text # encontra a primeira tag h1, que deve ser um título
            paragrafos = conteudo_principal.find_all('p')
        
            data_publicacao = paragrafos[0].text.replace("Publicada em ", "").strip()
            texto_completo = []
            texto_completo = re.sub(r"\s+", " ", " ".join(paragrafo.text for paragrafo in paragrafos[1:]))
        
            noticia = dict()
            noticia["url_origem"] = url
            noticia["titulo"] = titulo_noticia
            noticia["data_publicacao"] = datetime.strptime(data_publicacao, "%d/%m/%Y").strftime("%Y/%m/%d") # formata a data para o padrão YYYY/MM/DD
            noticia["texto"] = texto_completo
            dataset.append(noticia)
            
        except Exception as e:
            print(f"Erro na url \"{url}\": {e}")
            continue
        
    with open("noticias.json", "w", encoding="utf8") as file:
        json.dump(dataset, file, ensure_ascii=False, indent=4)

    # print(dataset)
    
def links_boletins(): # retorna uma lista de links para os boletins UFSJ de 03/06/2024 a 30/06/2025.
    urls_boletins = []
    
    for i in range(1255, 1507):
        urls_boletins.append(f"https://ufsj.edu.br/ascom/boletim{i}.php")
        
    # print(urls_boletins)
    
    return urls_boletins

def extrair_texto_boletins(urls: list[str]):
    dataset = []
    
    for url in urls:
        try:
            r = requests.get(url, verify=False)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            conteudo_principal = soup.find(id="ufsj-corpo-paginagenerica-conteudo")
            if not conteudo_principal: # evita páginas defeituosas ou que não carregaram.
                continue

            texto_bruto = conteudo_principal.get_text(separator='\n')
            linhas = [l.strip() for l in texto_bruto.split('\n') if l.strip()]

            data_boletim = ""
            for l in linhas: # encontra a data do boletim (Última atualização: DD/MM/YYYY)
                if "Última atualização:" in l:
                    match = re.search(r"(\d{2}/\d{2}/\d{4})", l)
                    if match:
                        data_boletim = match.group(1)
                        break

            noticia_atual = None
            
            for linha in linhas:
                if "Última atualização:" in linha: 
                    continue
                
                if re.search(r"^\s*\d+\s*[-–—]", linha):
                    if noticia_atual:
                        noticia_atual["texto"] = re.sub(r'\s+', ' ', noticia_atual["texto"]).strip()
                        dataset.append(noticia_atual)
                        
                    titulo_limpo = re.sub(r"^\s*\d+\s*[-–—]\s*", "", linha)
                    noticia_atual = {
                        "url_origem": url, 
                        "titulo": titulo_limpo, 
                        "data_publicacao": datetime.strptime(data_boletim, "%d/%m/%Y").strftime("%Y/%m/%d"), 
                        "texto": ""
                    }
                else:
                    if noticia_atual:
                        noticia_atual["texto"] += linha + " "

            if noticia_atual:
                noticia_atual["texto"] = re.sub(r'\s+', ' ', noticia_atual["texto"]).strip()
                dataset.append(noticia_atual)
        except Exception as e:
            print(f"Erro em {url}: {e}")

    with open("boletins.json", "w", encoding="utf-8") as file:
        json.dump(dataset, file, ensure_ascii=False, indent=4)

def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # links_mais_noticias(0)
    # extrair_texto_noticia(["https://ufsj.edu.br/noticias_ler.php?codigo_noticia=10369"])
    
    extrair_texto_noticia(links_mais_noticias(1))
    
    # extrair_texto_boletins(links_boletins())

if __name__ == "__main__":
    main()