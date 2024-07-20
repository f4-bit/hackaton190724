import panel as pn
import pandas as pd

# Configurar Panel
pn.extension()

# Cargar el archivo XLS en un DataFrame
file_path = 'test_data.xlsx'
df = pd.read_excel(file_path)

# Asegurarse de que las columnas tienen los nombres correctos
df.columns = ['url','title', 'seendate', 'domain','content']

# Extraer y convertir la fecha en la misma columna
df['seendate'] = pd.to_datetime(df['seendate'].str[:8], format='%Y%m%d')

# Renombrar la columna para claridad
df.rename(columns={'seendate': 'fecha'}, inplace=True)

# Widgets para filtros
date_picker = pn.widgets.DatePicker(name='Fecha')
portal_selector = pn.widgets.Select(name='Portal de Noticias', options=['Todos'] + list(df['domain'].unique()))
keyword_input = pn.widgets.TextInput(name='Palabra Clave')

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

    return filtered_df

# Layout de la aplicación
layout = pn.Column(
    pn.Row(date_picker, portal_selector, keyword_input),
    pn.panel(filter_news)
)

# Servir la aplicación
layout.servable()