from gdeltdoc import GdeltDoc, Filters
import requests
from bs4 import BeautifulSoup
import re
import json

def get_news(domain: str, country: str, start_date: str, end_date: str):
    """
    Retrieves news articles from a specified domain within a given date range and containing specific keywords.

    Parameters:
    -----------
    domain : str
        The exact domain from which to retrieve articles. For example, 'eltiempo.com'.
    country : str
        The country code representing the country from which to retrieve articles. For example, 'US' for the United States.
    start_date : str
        The start date for the date range to filter articles, in the format 'YYYYMMDD'.
    end_date : str
        The end date for the date range to filter articles, in the format 'YYYYMMDD'.
    keywords : list of str
        A list of keywords to filter articles. Articles containing any of these keywords will be retrieved.

    Returns:
    --------
    pandas.DataFrame
        A DataFrame containing the titles, URLs, publication dates, and domains of the retrieved articles.

    Example:
    --------
    >>> get_news(
    ...     domain="eltiempo.com",
    ...     country="CO",
    ...     start_date="20220101",
    ...     end_date="20220131",
    ...     keywords=["economy", "technology"]
    ... )
        title                     url                        seendate    domain
    0   Example Article Title     https://example.com/article 2022-01-15  eltiempo.com
    1   Another Example Title     https://example.com/article 2022-01-20  eltiempo.com
    ...
    """
    
    f = Filters(
        keyword= 'Venezuela',
        start_date=start_date,
        end_date=end_date,
        country=country,
        domain_exact=domain
    )

    gd = GdeltDoc()

    # Search for articles matching the filters
    articles = gd.article_search(f)
    articles = articles[['url', 'title', 'seendate', 'domain']]
    return articles

def get_information(url:str, domain:str):
    content, coments, tags = None, None, None

    if domain == 'eltiempo.com':
        content, coments, tags = get_information_eltiempo(url)
    elif domain == 'elespectador.com':
        content, coments, tags = get_information_elespectador(url)
    elif domain == 'vanguardia.com':
        content, coments, tags = get_information_vanguardia(url)

    return content, coments, tags

def contiene_palabra_clave(texto):
    """
    Evalúa si al menos una de las palabras clave aparece en la cadena de texto,
    independientemente de mayúsculas o minúsculas.

    :param texto: Cadena de caracteres en la que se busca.
    :param palabras_clave: Lista de palabras clave a buscar.
    :return: True si alguna palabra clave está en el texto, False en caso contrario.
    """

    # Lista de palabras clave
    palabras = ['Migrantes venezolanos']
#     palabras = [
#         "venecos", "Venezolanos", 'colombo-venezolana', 'venezolana', 'Inmigrante venezolano',
#         "Venezolanos en Colombia",
#         "Crisis migratoria",
#         "Refugiados venezolanos",
#         "Diáspora venezolana",
#         "Migrantes venezolanos",
#         "Exiliados venezolanos",
#         "Venezolanos desplazados"
# ]
    texto_lower = texto.lower()  # Convertir el texto a minúsculas para comparación insensible
    for palabra in palabras:
        palabra_lower = palabra.lower()  # Convertir cada palabra clave a minúsculas
        if palabra_lower in texto_lower:
            return True
    return False




###################### EL TIEMPO ##############################################################
def get_information_eltiempo(url:str, timeout=10):
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
            r'\(Además:[^\)]*\)',  # Frases que empiezan con (Además: y terminan con ),
            r'\(Puede leer:[^\)]*\)',
            r'\(Lea también:[^\)]*\)',
            r'\(Le puede interesar:[^\)]*\)'
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

        # # Validar contenido
        # if content is not None:
        #     validate = contiene_palabra_clave(content)
        #     if not validate:
        #         content = None
        #         coments = None
        #         tags = None
        #     else:
        article_number = obtener_numero_articulo_eltiempo(soup)
        coments = obtener_comentarios_eltiempo(article_number)
        tags =  obtener_tags_from_js_eltiempo(soup)
        return content, coments, tags
    except requests.RequestException as e:
        # Manejar errores de solicitud (e.g., tiempo de espera agotado, conexión fallida)
        print(f"Error al realizar la solicitud: {e}")
        return None, None, None

def obtener_numero_articulo_eltiempo(soup):

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
    
def obtener_tags_from_js_eltiempo(soup):
    """
    Extrae etiquetas desde un bloque de JavaScript en una página web.

    Args:
        soup (BeautifulSoup): Objeto BeautifulSoup que representa el contenido HTML de la página.

    Returns:
        list: Lista de etiquetas extraídas y formateadas, o None si ocurre un error.
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


    except ValueError as e:
        print(f"Error al obtener las etiquetas: {e}")
        return None

def obtener_comentarios_eltiempo(id_, timeout=10):
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

####################### EL ESPECTADOR #########################################################
def extract_comments_elespectador(id_, timeout = 10):
        """
        Extrae los comentarios de un artículo de El Espectador dado su ID.

        Parameters:
        article_id (str): El ID del artículo para el cual se desean obtener los comentarios.
        timeout (int): El tiempo de espera para la solicitud HTTP (por defecto 10).

        Returns:
        list: Una lista de comentarios si se encuentran, de lo contrario None.
        """
        
        if id_ is not None:
            url = f'https://www.elespectador.com/pf/api/v3/content/fetch/comments?query=%7B"articleId"%3A"{id_}"%7D&d=937&_website=el-espectador'
            
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()

                data = response.json()
                comentarios = [comment['content'] for comment in data.get('body', [])]

            except requests.exceptions.RequestException as e:
                print(f"Error en la solicitud: {e}")
                comentarios = None

            except ValueError as e:
                print(f"Error al procesar la respuesta JSON: {e}")
                comentarios = None

            return comentarios
        else:
            return None

def get_information_elespectador(url:str, timeout=10):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        #Parsear el contenido HTML del artículo
        soup = BeautifulSoup(response.content, 'html.parser')

        #---
        content = extract_content_elespectador(soup)

        # Validar contenido
        if content is not None:
            validate = contiene_palabra_clave(content)
            if not validate:
                content = None
                coments = None
                tags = None
            else:
                article_number = extract_article_number_elespectador(soup)
                coments = extract_comments_elespectador(article_number)
                tags =  None
        return content, coments, tags

    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        return None, None, None
    
def extract_content_elespectador(soup):
    # Encontrar todos los scripts JSON-LD
    script_tags = soup.find_all('script', type='application/ld+json')

    # Iterar sobre cada script para encontrar el correcto
    article_body = None
    for script_tag in script_tags:
        try:
            json_data = json.loads(script_tag.string)
            if json_data.get('@type') == 'NewsArticle':
                article_body = json_data.get('articleBody', 'No se encontró articleBody')
                break
        except json.JSONDecodeError:
            continue
    return article_body

def extract_article_number_elespectador(soup):
    pattern = r'"_id":"([A-Z0-9]+)"'
    match = re.search(pattern, str(soup))

    if match: 
        number = match.group(1)
        return number
    else:
        print('no se encontró el número')
        return None

###################### VANGUARDIA LIBERAL #####################################################
def get_information_vanguardia(url:str, timeout=10):
    response = requests.get(url,  timeout=timeout)
    soup = BeautifulSoup(response.content, 'html.parser')
    content = extract_content_vanguardia(soup)
    # Validar contenido
    if content is not None:
        validate = contiene_palabra_clave(content)
        if not validate:
            content = None

    coments = None
    tags = None
    return content, coments, tags

def extract_content_vanguardia(soup):
    content = None
    try:
        # Extraer el contenido de la noticia
        article_body = soup.find('script', type='application/ld+json').string
            
        article_json = json.loads(article_body)
        content = article_json.get('articleBody')
    except ValueError:
        pass

    return content