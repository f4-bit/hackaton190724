import panel as pn
import pandas as pd

# Configurar Panel
pn.extension('tabulator')

# Cargar el archivo XLS en un DataFrame con manejo de errores
file_path = 'test_data.xlsx'
try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    df = pd.DataFrame(columns=['url', 'title', 'seendate', 'domain', 'content'])
    print("El archivo no fue encontrado. Por favor, verifica la ruta del archivo.")

# Asegurarse de que las columnas tienen los nombres correctos
df.columns = ['url', 'title', 'seendate', 'domain', 'content']

# Extraer y convertir la fecha en la misma columna
df['seendate'] = pd.to_datetime(df['seendate'].str[:8], format='%Y%m%d')

# Renombrar la columna para claridad
df.rename(columns={'seendate': 'fecha'}, inplace=True)

# Widgets para filtros
def create_filter_widgets():
    date_range_slider = pn.widgets.DateRangeSlider(
        name='Rango:', 
        start=df['fecha'].min().date(), 
        end=df['fecha'].max().date(), 
        value=(df['fecha'].min().date(), df['fecha'].max().date()), 
        width=200
    )
    portal_selector = pn.widgets.Select(name='Portal de Noticias', options=['Todos'] + list(df['domain'].unique()), width=200)
    keyword_input = pn.widgets.TextInput(name='Palabra Clave', width=200)
    reset_button = pn.widgets.Button(name='Restablecer Filtros', width=200)
    return date_range_slider, portal_selector, keyword_input, reset_button

# Filtro de datos basado en los widgets
def filter_news(date_range_slider, portal_selector, keyword_input):
    @pn.depends(date_range_slider.param.value, portal_selector, keyword_input)
    def filter_func(date_range, portal, keyword):
        filtered_df = df.copy()
        start_date, end_date = date_range
        if start_date and end_date:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            filtered_df = filtered_df[(filtered_df['fecha'] >= start_date) & (filtered_df['fecha'] <= end_date)]
        if portal != 'Todos':
            filtered_df = filtered_df[filtered_df['domain'] == portal]
        if keyword:
            filtered_df = filtered_df[filtered_df['title'].str.contains(keyword, case=False)]
        return filtered_df[['fecha', 'title', 'domain', 'url']]
    
    return filter_func

# Crear layout para los filtros y el DataFrame
def create_dashboard_tab():
    date_range_slider, portal_selector, keyword_input, reset_button = create_filter_widgets()
    
    @pn.depends(reset_button.param.clicks, watch=True)
    def reset_filters(clicks):
        date_range_slider.value = (df['fecha'].min().date(), df['fecha'].max().date())
        portal_selector.value = 'Todos'
        keyword_input.value = ''
    
    filtered_news = pn.widgets.Tabulator(filter_news(date_range_slider, portal_selector, keyword_input), height=580, sizing_mode='stretch_width')
    
    return pn.Column(
        pn.Row(date_range_slider, portal_selector, keyword_input, reset_button),
        filtered_news
    )

# Crear el contenido principal
dashboard_tab = create_dashboard_tab()
metricas_1 = pn.pane.Markdown("# Aquí puedes añadir la visualización de las primeras métricas")
metricas_2 = pn.pane.Markdown("# Aquí puedes añadir la visualización de otras métricas")

# Crear las pestañas para métricas adicionales
tabs = pn.Tabs(
    ("Dashboard", dashboard_tab),
    ("Métricas 1", metricas_1),
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
