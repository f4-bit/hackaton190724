import panel as pn
import pandas as pd

# Configurar Panel
pn.extension(sizing_mode="stretch_width")

# Cargar el archivo XLS en un DataFrame
file_path = 'test_data.xlsx'
df = pd.read_excel(file_path)

# Asegurarse de que las columnas tienen los nombres correctos
df.columns = ['url', 'title', 'seendate', 'domain', 'content']

# Extraer y convertir la fecha en la misma columna
df['seendate'] = pd.to_datetime(df['seendate'].str[:8], format='%Y%m%d')

# Renombrar la columna para claridad
df.rename(columns={'seendate': 'fecha'}, inplace=True)

# Widgets para filtros
date_picker = pn.widgets.DatePicker(name='Fecha', width=200)
portal_selector = pn.widgets.Select(name='Portal de Noticias', options=['Todos'] + list(df['domain'].unique()), width=200)
keyword_input = pn.widgets.TextInput(name='Palabra Clave', width=200)

# Filtro de datos basado en los widgets
@pn.depends(date_picker, portal_selector, keyword_input)
def filter_news(date, portal, keyword):
    filtered_df = df.copy()
    
    if date:
        filtered_df = filtered_df[filtered_df['fecha'].dt.date == date]
    if portal != 'Todos':
        filtered_df = filtered_df[filtered_df['domain'] == portal]
    if keyword:
        filtered_df = filtered_df[filtered_df['title'].str.contains(keyword, case=False)]

    return filtered_df[['url', 'title', 'fecha', 'domain']]

# Crear el DataFramePane para mostrar los datos filtrados
filtered_news = pn.widgets.DataFrame(filter_news, autosize_mode='fit_viewport', height=400)

# Crear layout básico
layout = pn.Column(
    pn.Row(date_picker, portal_selector, keyword_input),
    filtered_news
)

# Crear el dashboard con pestañas
dashboard = pn.Tabs(
    ("Dashboard", layout),
    ("Métricas 1", pn.pane.Markdown("# Aquí puedes añadir la visualización de las primeras métricas")),
    ("Métricas 2", pn.pane.Markdown("# Aquí puedes añadir la visualización de otras métricas")),
)

# Servir la aplicación
dashboard.servable()
