from gdeltdoc import GdeltDoc, Filters

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
