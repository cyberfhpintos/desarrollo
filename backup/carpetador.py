#!/usr/bin/env python3.12

import os
import pandas as pd

def crear_carpetas_desde_excel(excel_path, columna_nombre, carpeta_principal = "carpetas"):
    # Leer el archivo Excel
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        return

    # Obtener la lista de nombres desde la columna especificada
    nombres = df[columna_nombre].tolist()
    
    if not os.path.exists(carpeta_principal):
        os.makedirs(carpeta_principal)

    # Crear carpetas para cada nombre
    for nombre in nombres:
        if str(nombre)[0] == "7":
            # Eliminar caracteres no permitidos en nombres de carpetas
            if type(nombre) == str:
                nombre = "".join(c for c in nombre if c.isalnum() or c.isspace())
            else:
                nombre = str(nombre)
            carpeta_path = os.path.join(carpeta_principal, nombre)

            # Verificar si la carpeta ya existe antes de crearla
            if not os.path.exists(carpeta_path):
                os.makedirs(carpeta_path)
                print(f"Carpeta creada: {carpeta_path}")
            else:
                print(f"La carpeta {carpeta_path} ya existe.")

if __name__ == "__main__":
    # Especifica la ruta del archivo Excel y la columna de nombres
    archivo_excel = "archivo.xlsx"
    columna_nombres = "Columna_1"

    # Llama a la función para crear carpetas
    crear_carpetas_desde_excel(archivo_excel, columna_nombres)
