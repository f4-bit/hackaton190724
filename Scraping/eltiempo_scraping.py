from .controller import contiene_palabra_clave
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import json

###################### EL TIEMPO ##############################################################

class ElTiempoScraper ():
    """
    Clase para acceder a la API del periódico digital El Tiempo.

    Esta clase permite obtener información de noticias que contienen palabras de interés,
    así como el contenido de las noticias y los comentarios asociados.
    """

    def __init__(self) -> None:
        pass

    def obtener_numero_articulo_eltiempo(self, soup):
        """
        Obtiene el número de artículo de una página de El Tiempo a partir del contenido JSON en un script.

        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup que representa el contenido HTML de la página.

        Returns:
            str: El número del artículo extraído del campo @id en el JSON, o un mensaje de error si no se encuentra.
        """
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
        
    def obtener_tags_from_js_eltiempo(self, soup):
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

    def get_information_eltiempo(self, url:str, timeout=10):
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
            article_number = self.obtener_numero_articulo_eltiempo(soup)
            coments = self.obtener_comentarios_eltiempo(article_number)
            tags =  self.obtener_tags_from_js_eltiempo(soup)
            return content, coments, tags
        except requests.RequestException as e:
            # Manejar errores de solicitud (e.g., tiempo de espera agotado, conexión fallida)
            print(f"Error al realizar la solicitud: {e}")
            return None, None, None

    def obtener_comentarios_eltiempo(self, id_, timeout=10):
        """
        Obtiene comentarios desde la API de El Tiempo.

        Args:
            id_ (str): ID del contenedor para el cual se desean obtener los comentarios.
            timeout (int, opcional): Tiempo máximo de espera para la solicitud en segundos. Por defecto es 10.

        Returns:
            list: Lista de comentarios extraídos o una lista vacía si ocurre un error.
        """

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
    
    def obtener_articulos(self, paginas=100):
        """
        Extrae los nombres de los artículos, URLs y fechas de publicación de las páginas especificadas
        de la búsqueda en El Tiempo sobre migrantes venezolanos en Colombia.

        :param paginas: Número de páginas a procesar.
        :return: DataFrame con las columnas 'Título', 'Fecha de Publicación' y 'URL'.
        """
        # Lista para almacenar los datos
        datos = []
        try: 
            # Iterar sobre las páginas
            for page in range(paginas):
                url = f'https://www.eltiempo.com/buscar/?q=migrantes%20venezolanos%20en%20colombia&sort_field=_score&articleTypes=default,gallery,especial_modular,especial-tipo-d,video_detail,play_video_detail&categories_ids_or=&from=2024-01-20&until=2024-07-20&page={page}'
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # Lanza un error para códigos de estado HTTP 4xx/5xx

                # Parsear el contenido HTML del artículo
                soup = BeautifulSoup(response.content, 'html.parser')
                articulos = soup.find_all('article', class_='c-article')

                # Extraer los nombres, URLs y fechas de publicación de los artículos
                for articulo in articulos:
                    # Encontrar el título del artículo
                    titulo = articulo.find('h3', class_='c-article__title').get_text(strip=True)
                    # Encontrar la URL del artículo
                    url = articulo.find('a', class_='page-link')['href']
                    url = 'https://www.eltiempo.com' + url
                    # Encontrar la fecha de publicación
                    fecha_publicacion = articulo.find('time', class_='c-article__date').get_text(strip=True)
                    
                    # Añadir los datos a la lista
                    datos.append({
                        'title': titulo,
                        'date': fecha_publicacion,
                        'url': url
                    })

        except requests.exceptions.RequestException as e:
            print(f'Error al realizar la solicitud: {e}')
        finally:
            df = pd.DataFrame(datos)
            return df
