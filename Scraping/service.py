import requests
from bs4 import BeautifulSoup
import re
import json

def extract_article_content(url, timeout=10):
    """
    Extrae y filtra el contenido de un artículo web a partir de su URL.

    Parameters:
    url (str): La URL del artículo del que se desea extraer el contenido.
    timeout (int): El tiempo máximo de espera para la solicitud HTTP en segundos. (Default es 10 segundos)

    Returns:
    str: El contenido del artículo, filtrado para excluir frases específicas entre paréntesis.
    """
    try:
        # Realizar la solicitud a la URL del artículo con timeout
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # Lanza un error para códigos de estado HTTP 4xx/5xx

        # Parsear el contenido HTML del artículo
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraer el contenido dentro de las etiquetas <div> con clase "paragraph"
        paragraph_divs = soup.find_all('div', class_='paragraph')

        # Definir patrones para excluir frases entre paréntesis
        exclude_patterns = [
            r'\(Lea además:[^\)]*\)',  # Frases que empiezan con (Lea además: y terminan con )
            r'\(Siga leyendo:[^\)]*\)',  # Frases que empiezan con (Siga leyendo: y terminan con )
            r'\(Le recomendamos:[^\)]*\)',  # Frases que empiezan con (Le recomendamos: y terminan con )
            r'\(Además:[^\)]*\)'  # Frases que empiezan con (Además: y terminan con )
        ]

        # Filtrar y limpiar el texto para eliminar las secciones no deseadas
        paragraphs = []
        for div in paragraph_divs:
            text = div.get_text().strip()
            # Filtrar el texto que contiene cualquier patrón de exclusión
            if not any(re.search(pattern, text) for pattern in exclude_patterns):
                paragraphs.append(text)

        # Unir todos los párrafos en una sola cadena
        content = "\n".join(paragraphs[:-3])
        
        article_number = obtener_numero_articulo(soup)
        coments = obtener_comentarios(article_number)
        tags =  obtener_tags_from_js(soup)
        return content, coments, tags
    
    except requests.RequestException as e:
        # Manejar errores de solicitud (e.g., tiempo de espera agotado, conexión fallida)
        print(f"Error al realizar la solicitud: {e}")
        return None

def obtener_numero_articulo(soup):

   # Encontrar el script que contiene el JSON
    script_tag = soup.find('script', type='application/ld+json')

    if script_tag:
        # Extraer el contenido del script
        script_content = script_tag.string.strip()

        # Convertir el contenido JSON en un diccionario de Python
        data = json.loads(script_content)

        # Buscar el número en el campo @id
        match = re.search(r'article-(\d+)', data.get('@id', ''))
        if match:
            number = match.group(1)
            return number
        else:
            return "No se encontró el número en el campo @id."
    else:
        return "No se encontró el script con el JSON."
    
def obtener_tags_from_js(soup):
    """
    Extrae etiquetas desde un bloque de JavaScript en una página web.

    Parámetros:
    url (str): URL del artículo desde el cual extraer las etiquetas.

    Retorna:
    list: Lista de etiquetas formateadas.
    """
    try:
        # Encontrar el bloque <script> que contiene el JavaScript con tagsArticle
        script_tag = soup.find('script', type='text/javascript', text=re.compile(r'let tagsArticle'))
     
        script_content = str(script_tag.string)
        # Extraer el valor de tagsArticle usando una expresión regular
        match =  re.search(r"let tagsArticle\s*=\s*'([^']*)'", script_content)
        if not match:
            raise ValueError("No se encontraron las etiquetas en el contenido del script.")
        
        # Extraer el contenido de tagsArticle
        tags_string = match.group(1)
        tags = tags_string.split(',')
        return tags


    except Exception as e:
        print(f"Error al obtener las etiquetas: {e}")
        return None


def obtener_comentarios(id_, timeout=10):
    # URL de la API
    url = f'https://livecomments.viafoura.co/v4/livecomments/00000000-0000-4000-8000-9c5d48314ca1?limit=100&container_id={id_}&reply_limit=4&sorted_by=newest'
    
    try:
        # Realizar la petición GET
        response = requests.get(url, timeout=timeout)
        
        # Comprobar si la respuesta es exitosa
        response.raise_for_status()
        
        # Convertir la respuesta en un diccionario de Python
        data = response.json()
        
        # Extraer todos los comentarios
        comentarios = [comment['content'] for comment in data.get('contents', [])]
    
    except requests.exceptions.RequestException as e:
        # Manejo de errores relacionados con la petición
        print(f"Error en la solicitud: {e}")
        comentarios = []
    
    except ValueError as e:
        # Manejo de errores relacionados con la conversión de JSON
        print(f"Error al procesar la respuesta JSON: {e}")
        comentarios = None
    
    return comentarios