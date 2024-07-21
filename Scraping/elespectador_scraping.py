####################### EL ESPECTADOR #########################################################
from .controller import contiene_palabra_clave
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import json


class ElEspectadorScraper ():
    """
    Clase para acceder a la API del periódico digital El Espectador.

    Esta clase permite obtener información de noticias que contienen palabras de interés,
    así como el contenido de las noticias y los comentarios asociados.
    """

    def __init__(self) -> None:
        pass
    
    def extract_content_elespectador(self, soup):
        """
        Extrae el contenido del cuerpo del artículo de El Espectador desde el HTML parseado.

        Parameters:
        soup (BeautifulSoup): El objeto BeautifulSoup con el contenido HTML parseado.

        Returns:
        str: El contenido del cuerpo del artículo, o un mensaje de error si no se encuentra.
        """
        # Encontrar todos los scripts JSON-LD
        script_tags = soup.find_all('script', type='application/ld+json')

        # Inicializar la variable para el cuerpo del artículo
        article_body = None

        # Iterar sobre cada script para encontrar el correcto
        for script_tag in script_tags:
            try:
                # Cargar el contenido JSON del script
                json_data = json.loads(script_tag.string)
                # Verificar si es un artículo de noticias
                if json_data.get('@type') == 'NewsArticle':
                    # Extraer el cuerpo del artículo
                    article_body = json_data.get('articleBody', 'No se encontró articleBody')
                    break
            except json.JSONDecodeError:
                # Continuar si hay un error al decodificar el JSON
                continue

        return article_body

    def extract_article_number_elespectador(self, soup):
        """
        Extrae el número del artículo de El Espectador desde el HTML parseado.

        Parameters:
        soup (BeautifulSoup): El objeto BeautifulSoup con el contenido HTML parseado.

        Returns:
        str: El número del artículo si se encuentra, de lo contrario None.
        """

        pattern = r'"_id":"([A-Z0-9]+)"'
        match = re.search(pattern, str(soup))

        if match: 
            number = match.group(1)
            return number
        else:
            print('no se encontró el número')
            return None

    def extract_comments_elespectador(self, id_, timeout = 10):
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

    def get_information_elespectador(self, url: str, timeout = 10):
        """
        Obtiene información de un artículo de El Espectador.

        Parameters:
        url (str): La URL del artículo.
        timeout (int): El tiempo de espera para la solicitud HTTP (por defecto 10).

        Returns:
        tuple: Contenido del artículo, comentarios y etiquetas. 
            Si no se encuentra contenido o no se valida, retorna (None, None, None).
        """
        
        try:
            # Realizar la solicitud a la URL del artículo con timeout
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            #Parsear el contenido HTML del artículo
            soup = BeautifulSoup(response.content, 'html.parser')

            #---
            content = self.extract_content_elespectador(soup)

            # Validar contenido
            if content is not None:
                validate = contiene_palabra_clave(content)
                if not validate:
                    content = None
                    coments = None
                    tags = None
                else:
                    article_number = self.extract_article_number_elespectador(soup)
                    coments = self.extract_comments_elespectador(article_number)
                    tags =  None
            return content, coments, tags

        except requests.exceptions.RequestException as e:
            print(f"Error al realizar la solicitud: {e}")
            return None, None, None
    
    def obtener_articulos(self,text, paginas=100):
        """
        Extrae los nombres de los artículos, URLs y fechas de publicación de las páginas especificadas
        de la búsqueda en El Tiempo sobre migrantes venezolanos en Colombia.

        Parameters:
        text(str): Texto de busqueda del articulo
        paginas(int): Número de páginas a procesar.
        :return: DataFrame con las columnas 'Título', 'Fecha de Publicación' y 'URL'.
        """
        # Lista para almacenar los datos
        datos = []
        # text = 'migrante-venezolano'
        try:
            for page in range(paginas):
                if (page): 
                    page = str(page) + '0'
                
                url_api = f'https://www.elespectador.com/pf/api/v3/content/fetch/searcherTag?query=%7B%22author%22%3Anull%2C%22date%22%3Anull%2C%22from%22%3A{page}%2C%22keyword%22%3A%22{text}%22%2C%22section%22%3A%5B%22%2Fcolombia%22%5D%2C%22subtype%22%3A%5B%22Art%C3%ADculos%22%5D%7D&d=937&_website=el-espectador'
                response = requests.get(url_api,timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')
                html_content = soup.string.strip()

                data = json.loads(html_content)

                for element in data.get('content_elements', []):
                    title = element.get('headlines', {}).get('basic', {})
                    date = element.get('display_date', 'No Date')
                    url = element.get('canonical_url', 'not found')
                    url = 'https://www.elespectador.com' + url
                    
                    datos.append({
                        'title': title,
                        'date': date,
                        'url': url
                    })

        except requests.exceptions.RequestException as e:
            print(f'Error al realizar la solicitud: {e}')
        finally:
            df = pd.DataFrame(datos)
            return df
