import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.elespectador.com/mundo/mas-paises/bella-hadid-se-suma-a-la-lista-de-celebridades-penalizadas-tras-criticar-a-israel/'
url = 'https://www.elespectador.com/opinion/columnistas/julio-cesar-londono/el-arte-de-conversar/?cx_testId=86&cx_testVariant=cx_1&cx_artPos=3#cxrecs_s'

def extract_article_content(url, timeout = 10):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        #Parsear el contenido HTML del artículo
        soup = BeautifulSoup(response.content, 'html.parser')

        #---
        article_number = extract_article_number(soup)
        coments = extract_comments(article_number)
        tags = 0
        return article_number, coments

    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        return None

def extract_article_number(soup):
    pattern = r'"_id":"([A-Z0-9]+)"'
    match = re.search(pattern, str(soup))

    if match: 
        number = match.group(1)
        return number
    else:
        return 'no se encontró el número'

def extract_comments(id_, timeout = 10):
    url = f'https://www.elespectador.com/pf/api/v3/content/fetch/comments?query=%7B"articleId"%3A"{id_}"%7D&d=937&_website=el-espectador'
    
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        comentarios = [comment['content'] for comment in data.get('body', [])]

    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud: {e}")
        comentarios = []

    except ValueError as e:
        print(f"Error al procesar la respuesta JSON: {e}")
        comentarios = None

    return comentarios


intento = extract_article_content(url)
with open ('./data/info2.txt', 'w', encoding='utf-8') as a:
    for i in intento[1]:
        a.write(i + '\n' + '\n')