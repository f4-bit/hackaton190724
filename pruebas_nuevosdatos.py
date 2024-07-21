import panel as pn
import pandas as pd
from datetime import datetime
import holoviews as hv
from bokeh.models import HoverTool
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Configurar Panel y Holoviews
pn.extension('tabulator', 'bokeh')
hv.extension('bokeh')

# Cargar el archivo XLS en un DataFrame con manejo de errores
file_path = 'articulos_eltiempo.xlsx'
try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    df = pd.DataFrame(columns=['title', 'date', 'url', 'content', '#coments', 'coments', 'tags'])
    print("El archivo no fue encontrado. Por favor, verifica la ruta del archivo.")

# Asegurarse de que las columnas tienen los nombres correctos
df.columns = ['title', 'date', 'url', 'content', '#coments', 'coments', 'tags']

# Diccionario de meses en español a números
months = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06',
    'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
}

# Función para convertir la fecha de texto a datetime
def convert_date(date_str):
    try:
        parts = date_str.split()
        day = parts[0]
        month = months[parts[1].lower()]
        year = parts[3]
        return datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y")
    except (ValueError, IndexError, KeyError):
        return None

# Aplicar la conversión a la columna 'date'
df['date'] = df['date'].apply(convert_date)

# Función para crear los widgets de filtro
def create_filter_widgets():
    date_range_slider = pn.widgets.DateRangeSlider(
        name='Rango:', 
        start=df['date'].min().date(), 
        end=df['date'].max().date(), 
        value=(df['date'].min().date(), df['date'].max().date()), 
        width=200
    )
    keyword_input = pn.widgets.TextInput(name='Palabra Clave', width=200)
    reset_button = pn.widgets.Button(name='Restablecer Filtros', width=200)
    return date_range_slider, keyword_input, reset_button

# Función para filtrar los datos basado en los widgets
def filter_news(date_range_slider, keyword_input):
    @pn.depends(date_range_slider.param.value, keyword_input.param.value)
    def filter_func(date_range, keyword):
        filtered_df = df.copy()
        start_date, end_date = date_range
        if start_date and end_date:
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
        date_range_slider.value = (df['date'].min().date(), df['date'].max().date())
        keyword_input.value = ''
    
    filtered_news = pn.widgets.Tabulator(filter_news(date_range_slider, keyword_input), height=580, sizing_mode='stretch_width')
    
    return pn.Column(
        pn.Row(date_range_slider, keyword_input, reset_button),
        filtered_news
    )

# Crear layout para la comparación de métricas
def create_comparison_tab():
    start_date_range_1 = pn.widgets.DateRangeSlider(name='Rango de Fecha 1:', start=df['date'].min().date(), end=df['date'].max().date(), value=(df['date'].min().date(), df['date'].max().date()), width=300)
    start_date_range_2 = pn.widgets.DateRangeSlider(name='Rango de Fecha 2:', start=df['date'].min().date(), end=df['date'].max().date(), value=(df['date'].min().date(), df['date'].max().date()), width=300)
    
    @pn.depends(start_date_range_1.param.value, start_date_range_2.param.value)
    def compare_ranges(date_range_1, date_range_2):
        start_date_1, end_date_1 = date_range_1
        start_date_2, end_date_2 = date_range_2
        
        range_1_df = df[(df['date'] >= pd.to_datetime(start_date_1)) & (df['date'] <= pd.to_datetime(end_date_1))]
        range_2_df = df[(df['date'] >= pd.to_datetime(start_date_2)) & (df['date'] <= pd.to_datetime(end_date_2))]
        
        range_1_tags = pd.Series([tag for tags in range_1_df['tags'] for tag in eval(tags)]).value_counts().nlargest(20)
        range_2_tags = pd.Series([tag for tags in range_2_df['tags'] for tag in eval(tags)]).value_counts().nlargest(20)
        
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
def create_wordcloud():
    # Cargar los datos de "mis datos.xlsx"
    words_df = pd.read_excel('misdatos.xlsx')
    
    # Actualiza 'palabras' al nombre correcto de la columna en tu archivo
    words_df['token'] = words_df['token'].astype(str)  # Convertir a cadenas
    words_df = words_df.dropna(subset=['token'])  # Eliminar filas con NaN en 'token'
    text = ' '.join(words_df['token'])
    
    # Generar la nube de palabras
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    
    # Mostrar la nube de palabras usando matplotlib
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    
    # Convertir la figura de matplotlib en un objeto Panel
    return pn.pane.Matplotlib(plt.gcf(), width=800, height=400)

# Crear el contenido principal
dashboard_tab = create_dashboard_tab()
metricas_1 = create_comparison_tab()
metricas_2 = pn.Column("# Nube de Palabras", create_wordcloud())

# Crear las pestañas para métricas adicionales
tabs = pn.Tabs(
    ("Dashboard", dashboard_tab),
    ("Comparación de Métricas", metricas_1),
    ("Métricas 2", metricas_2),
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
