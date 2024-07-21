import panel as pn
import pandas as pd
from datetime import datetime
import holoviews as hv
from bokeh.models import HoverTool
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import ast

# Configurar Panel y Holoviews
pn.extension('tabulator', 'bokeh')
hv.extension('bokeh')

# Cargar el archivo XLS en un DataFrame con manejo de errores
file_path_tiempo = 'articulos_eltiempo.xlsx'
file_path_elespectador = 'articulos_elespectador.xlsx'
try:
    df_tiempo = pd.read_excel(file_path_tiempo)
    df_elespectador = pd.read_excel(file_path_elespectador)
except FileNotFoundError:
    df_tiempo = pd.DataFrame(columns=['title', 'date', 'url', 'content', '#coments', 'coments', 'tags'])
    df_elespectador = pd.DataFrame(columns=['title', 'date', 'url', 'text', '#coments', 'coments', 'tags'])
    print("Uno de los archivos no fue encontrado. Por favor, verifica la ruta de los archivos.")

# Asegurarse de que las columnas tienen los nombres correctos
df_tiempo.columns = ['title', 'date', 'url', 'content', '#coments', 'coments', 'tags']
df_elespectador.columns = ['title', 'date', 'url', 'text', '#coments', 'coments', 'tags']

# Diccionario de meses en español a números para El Tiempo
months = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06',
    'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
}

# Función para convertir la fecha de texto a datetime para El Tiempo
def convert_date_tiempo(date_str):
    try:
        parts = date_str.split()
        day = parts[0]
        month = months[parts[1].lower()]
        year = parts[3]
        return datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y")
    except (ValueError, IndexError, KeyError):
        return None

# Función para convertir la fecha de texto a datetime para El Espectador
def convert_date_elespectador(date_str):
    try:
        return datetime.strptime(date_str.split('T')[0], "%Y-%m-%d")
    except (ValueError, IndexError):
        return None

# Aplicar la conversión a la columna 'date'
df_tiempo['date'] = df_tiempo['date'].apply(convert_date_tiempo)
df_elespectador['date'] = df_elespectador['date'].apply(convert_date_elespectador)

# Combinar los DataFrames
df_combined = pd.concat([df_tiempo, df_elespectador], ignore_index=True)

# Función para crear los widgets de filtro
def create_filter_widgets():
    date_range_slider = pn.widgets.DateRangeSlider(
        name='Rango:', 
        start=df_combined['date'].min().date(), 
        end=df_combined['date'].max().date(), 
        value=(df_combined['date'].min().date(), df_combined['date'].max().date()), 
        width=200
    )
    keyword_input = pn.widgets.TextInput(name='Palabra Clave', width=200)
    reset_button = pn.widgets.Button(name='Restablecer Filtros', width=200)
    return date_range_slider, keyword_input, reset_button

# Función para filtrar los datos basado en los widgets
def filter_news(date_range_slider, keyword_input):
    @pn.depends(date_range_slider.param.value, keyword_input.param.value)
    def filter_func(date_range, keyword):
        filtered_df = df_combined.copy()
        start_date, end_date = date_range
        if (start_date and end_date) and not pd.isnull(start_date) and not pd.isnull(end_date):
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            filtered_df = filtered_df[(filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)]
        if keyword:
            filtered_df = filtered_df[filtered_df['title'].str.contains(keyword, case=False)]
        return filtered_df[['date', 'title', 'url']]
    
    return filter_func

# Crear layout para los filtros y el DataFrame
def create_dashboard_tab():
    date_range_slider, keyword_input, reset_button = create_filter_widgets()
    
    @pn.depends(reset_button.param.clicks, watch=True)
    def reset_filters(clicks):
        date_range_slider.value = (df_combined['date'].min().date(), df_combined['date'].max().date())
        keyword_input.value = ''
    
    filtered_news = pn.widgets.Tabulator(filter_news(date_range_slider, keyword_input), height=580, sizing_mode='stretch_width')
    
    return pn.Column(
        pn.Row(date_range_slider, keyword_input, reset_button),
        filtered_news
    )

# Crear layout para la comparación de métricas
def create_comparison_tab():
    start_date_range_1 = pn.widgets.DateRangeSlider(name='Rango de Fecha 1:', start=df_combined['date'].min().date(), end=df_combined['date'].max().date(), value=(df_combined['date'].min().date(), df_combined['date'].max().date()), width=300)
    start_date_range_2 = pn.widgets.DateRangeSlider(name='Rango de Fecha 2:', start=df_combined['date'].min().date(), end=df_combined['date'].max().date(), value=(df_combined['date'].min().date(), df_combined['date'].max().date()), width=300)

        # Función para convertir una cadena de texto en una lista de etiquetas
    def safe_eval(tags_str):
        try:
            return ast.literal_eval(tags_str)
        except (ValueError, SyntaxError):
            return []

    # En la función compare_ranges, usa safe_eval en lugar de eval
    @pn.depends(start_date_range_1.param.value, start_date_range_2.param.value)
    def compare_ranges(date_range_1, date_range_2):
        start_date_1, end_date_1 = date_range_1
        start_date_2, end_date_2 = date_range_2

        range_1_df = df_combined[(df_combined['date'] >= pd.to_datetime(start_date_1)) & (df_combined['date'] <= pd.to_datetime(end_date_1))]
        range_2_df = df_combined[(df_combined['date'] >= pd.to_datetime(start_date_2)) & (df_combined['date'] <= pd.to_datetime(end_date_2))]

        range_1_tags = pd.Series([tag for tags in range_1_df['tags'] for tag in safe_eval(tags)]).value_counts().nlargest(20)
        range_2_tags = pd.Series([tag for tags in range_2_df['tags'] for tag in safe_eval(tags)]).value_counts().nlargest(20)

        comparison_df = pd.DataFrame({
            'Tags': list(set(range_1_tags.index).union(set(range_2_tags.index))),
            'Rango 1': [range_1_tags.get(tag, 0) for tag in set(range_1_tags.index).union(set(range_2_tags.index))],
            'Rango 2': [range_2_tags.get(tag, 0) for tag in set(range_1_tags.index).union(set(range_2_tags.index))]
        }).set_index('Tags')

        bars = hv.Bars(comparison_df.reset_index(), kdims='Tags', vdims=['Rango 1', 'Rango 2']).opts(
            width=1200, height=600, tools=['hover'], xrotation=45, show_legend=True)

        news_counts = {
            'Rango 1': len(range_1_df),
            'Rango 2': len(range_2_df)
        }

        news_count_pane = pn.pane.Markdown(f"**Cantidad de Noticias:**\n\n- Rango 1: {news_counts['Rango 1']}\n- Rango 2: {news_counts['Rango 2']}")

        return pn.Column(bars, news_count_pane)
    
    return pn.Column(
        pn.Row(start_date_range_1, start_date_range_2),
        compare_ranges
    )

# Función para generar la nube de palabras
def create_wordcloud(file_path):
    # Cargar los datos del archivo XLSX
    words_df = pd.read_excel(file_path)
    
    # Convertir a cadenas y eliminar filas con NaN en 'token'
    words_df['token'] = words_df['token'].astype(str)
    words_df = words_df.dropna(subset=['token'])
    text = ' '.join(words_df['token'])
    
    # Generar la nube de palabras
    wordcloud = WordCloud(width=1200, height=1000, background_color='white').generate(text)
    
    # Mostrar la nube de palabras usando matplotlib
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    
    # Convertir la figura de matplotlib en un objeto Panel
    return pn.pane.Matplotlib(plt.gcf())

# Función para crear la pestaña de sentimientos
def create_sentiments_table():
    # Cargar los datos de los archivos XLSX
    sentiments_df = pd.read_excel('sentiment_word_counts_text.xlsx')
    
    # Crear una tabla interactiva para mostrar los datos
    sentiments_table = pn.widgets.Tabulator(sentiments_df, pagination='remote', page_size=10)
    
    return pn.Column(
        "# Tabla de Sentimientos",
        sentiments_table
    )

# Función para crear la pestaña de comentarios
def create_comments_tab():
    # Cargar los datos de los archivos XLSX
    comments_df_tiempo = pd.read_excel('negative_words_comments_tiempo.xlsx')
    comments_df = pd.read_excel('negative_words_comments.xlsx')
    
    # Crear un gráfico de barras de la distribución de comentarios negativos para El Tiempo
    comments_counts_tiempo = comments_df_tiempo.groupby(['sentiment', 'lemma'])['count'].sum().reset_index()
    comments_counts_tiempo = comments_counts_tiempo[comments_counts_tiempo['count'] > 1]
    comments_counts_tiempo = comments_counts_tiempo.sort_values(by='count', ascending=False).groupby('sentiment').head(10)
    comments_bars_tiempo = hv.Bars(comments_counts_tiempo, kdims=['sentiment', 'lemma'], vdims='count').opts(
        width=800, height=400, tools=[HoverTool(tooltips=[('Sentiment', '@sentiment'), ('Word', '@lemma'), ('Count', '@count')])],
        xlabel='Sentiment', ylabel='Count', color='sentiment', show_legend=False, toolbar='above', xrotation=45
    )
    
    # Crear un gráfico de barras de la distribución de comentarios negativos para el otro periódico
    comments_counts = comments_df.groupby(['sentiment', 'lemma'])['count'].sum().reset_index()
    comments_counts = comments_counts[comments_counts['count'] > 1]
    comments_counts = comments_counts.sort_values(by='count', ascending=False).groupby('sentiment').head(10)
    comments_bars = hv.Bars(comments_counts, kdims=['sentiment', 'lemma'], vdims='count').opts(
        width=800, height=400, tools=[HoverTool(tooltips=[('Sentiment', '@sentiment'), ('Word', '@lemma'), ('Count', '@count')])],
        xlabel='Sentiment', ylabel='Count', color='sentiment', show_legend=False, toolbar='above', xrotation=45
    )
    
    # Descripción del gráfico de comentarios negativos
    comments_description_1 = pn.pane.Markdown("""
    ## Comentarios Negativos Más Frecuentes - El Tiempo
    El gráfico a continuación muestra las palabras negativas más frecuentes en los comentarios de El Tiempo.
    """)
    
    # Descripción del gráfico de comentarios negativos
    comments_description_2 = pn.pane.Markdown("""
    ## Comentarios Negativos Más Frecuentes - Otro Periódico
    El gráfico a continuación muestra las palabras negativas más frecuentes en los comentarios del otro periódico.
    """)
    
    # Combinar los gráficos en un layout
    layout = pn.Column(
        "# Visualización de Comentarios Negativos",
        comments_description_1,
        comments_bars_tiempo,
        comments_description_2,
        comments_bars
    )
    
    return layout

# Función para crear la pestaña de nube de palabras
def create_wordcloud_tab():
    # Crear una nube de palabras para los comentarios
    wordcloud_comments = create_wordcloud('comentarios.xlsx')
    
    # Crear una nube de palabras para el contenido
    wordcloud_content = create_wordcloud('contenido.xlsx')
    
    # Descripciones para las nubes de palabras
    wordcloud_description_1 = pn.pane.Markdown("""
    ## Nube de Palabras - Comentarios
    La siguiente nube de palabras muestra las palabras más frecuentes encontradas en los comentarios.
    """)
    
    wordcloud_description_2 = pn.pane.Markdown("""
    ## Nube de Palabras - Contenido
    La siguiente nube de palabras muestra las palabras más frecuentes encontradas en el contenido.
    """)
    
    # Combinar las nubes de palabras y descripciones en un layout
    layout = pn.Column(
        "# Nube de Palabras",
        wordcloud_description_1,
        wordcloud_comments,
        wordcloud_description_2,
        wordcloud_content
    )
    
    return layout

# Crear el contenido principal
dashboard_tab = create_dashboard_tab()
metricas_1 = create_comparison_tab()
wordcloud_tab = create_wordcloud_tab()
sentiments_tab = create_sentiments_table()
comments_tab = create_comments_tab()

# Crear las pestañas para métricas adicionales
tabs = pn.Tabs(
    ("Dashboard", dashboard_tab),
    ("Comparación de Métricas", metricas_1),
    ("Nube de Palabras", wordcloud_tab),
    ("Sentimientos", sentiments_tab),
    ("Comentarios", comments_tab),
    tabs_location='left',  # Mover las pestañas a la parte izquierda
    active=0  # Pestaña activa predeterminada
)

# Crear el template sin barra lateral
template = pn.template.MaterialTemplate(
    title='Syntax Error Project',
    main=[tabs],  # Usar las pestañas como el contenido principal
)

# Servir la aplicación
template.servable()
