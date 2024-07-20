import pandas as pd
import panel as pn
from datetime import datetime

# Datos de ejemplo
data = {
    'date': pd.date_range(start='2023-01-01', periods=10, freq='D'),
    'value': range(10)
}
df = pd.DataFrame(data)

# Convertir la columna 'date' a tipo datetime
df['date'] = pd.to_datetime(df['date'])

# Crear widgets para seleccionar el rango de fechas
start_date = pn.widgets.DatePicker(name='Start Date', value=datetime(2023, 1, 1))
end_date = pn.widgets.DatePicker(name='End Date', value=datetime(2023, 1, 10))

# Función para filtrar los datos basados en el rango de fechas seleccionado
@pn.depends(start_date.param.value, end_date.param.value)
def filter_data(start, end):
    if start is not None and end is not None:
        filtered_df = df[(df['date'] >= start) & (df['date'] <= end)]
        return filtered_df
    return df

# Mostrar la tabla filtrada y los widgets
app = pn.Column(
    pn.Row(start_date, end_date),
    pn.bind(filter_data, start_date, end_date)
)

# Servir la aplicación
pn.serve(app)
