import panel as pn
import matplotlib.pyplot as plt

# Crear un gráfico de Matplotlib
fig, ax = plt.subplots()
ax.plot([1, 2, 3, 4], [10, 20, 25, 30])
ax.set_title('Gráfico de Matplotlib en Panel')

# Convertir el gráfico de Matplotlib en un objeto Panel
matplotlib_pane = pn.pane.Matplotlib(fig)

# Crear algunos widgets
slider = pn.widgets.FloatSlider(name='Slider', start=0, end=10, step=0.1)
button = pn.widgets.Button(name='Botón')

# Usar una plantilla
template = pn.template.FastListTemplate(
    title='Mi Aplicación con Panel',
    sidebar=[slider, button],
    main=[matplotlib_pane]
)

# Servir la aplicación
template.servable()
