import os
import pandas as pd

class Lector:
    def __init__(self, ruta_carpeta, ruta_excel):
        self.ruta_carpeta = ruta_carpeta
        self.ruta_excel = ruta_excel

    def obtener_nombres_archivos(self):
        nombres_archivos = []
        for archivo in os.listdir(self.ruta_carpeta):
            if os.path.isfile(os.path.join(self.ruta_carpeta, archivo)):
                nombres_archivos.append(archivo)
        return nombres_archivos

    def quitar_extension(self, nombre_archivo):
        # Obtener el nombre del archivo sin la extensión
        return os.path.splitext(nombre_archivo)[0]

    def volcar_a_excel(self, nombres_archivos):
        # Obtener el máximo número de palabras en cualquier nombre de archivo
        max_palabras = max(len(self.quitar_extension(nombre).split()) for nombre in nombres_archivos)

        # Dividir los nombres de archivo en diferentes columnas
        datos = [self.quitar_extension(nombre).split() + [''] * (max_palabras - len(self.quitar_extension(nombre).split())) for nombre in nombres_archivos]

        # Crear un DataFrame de pandas
        df = pd.DataFrame(datos, columns=[f"Columna_{i + 1}" for i in range(max_palabras)])

        # Guardar en un archivo de Excel
        df.to_excel(self.ruta_excel, index=False)

    def registrar(self):
        # Obtener nombres de archivos
        nombres_archivos = self.obtener_nombres_archivos()

        # Volcar a Excel
        self.volcar_a_excel(nombres_archivos)
        
'''
if __name__ == "__main__":
    # Ruta de la carpeta que contiene los archivos (dentro de la subcarpeta 'archivos')
    ruta_carpeta = os.path.join(os.path.dirname(__file__), 'archivos')

    # Ruta del archivo de Excel de salida (en el mismo directorio que el script de Python)
    ruta_excel = os.path.join(os.path.dirname(__file__), 'archivo.xlsx')

    # Crear una instancia de la clase y ejecutar el método renombrar
    new_names = Lector(ruta_carpeta, ruta_excel)
    new_names.registrar()
'''