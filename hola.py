import os

# Establecer la variable R_HOME en el script de Python
os.environ['R_HOME'] = 'C:\Program Files\R\R-4.4.1'  # Cambia esta ruta a la correcta

import rpy2.robjects as ro
print(ro.r['R.version'])