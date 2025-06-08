#!/usr/bin/env python3.12

from pdf2image import convert_from_path
import os
from PIL import Image
from reconocimiento_datos import ReconocimientoDatos
import pandas as pd
from lector_de_nombre import Lector

class ProcesadorPDF:
    def __init__(self, pdf_directory):
        self.pdf_directory = pdf_directory
        self.intentos = 7
        self.ordenes_procesadas = []

    def procesar_archivos_pdf_en_directorio(self):
        for filename in os.listdir(self.pdf_directory):
            if filename.lower().endswith(".pdf"):
                archivo_pdf = os.path.join(self.pdf_directory, filename)
                self.procesar_archivo_pdf(archivo_pdf)

        self.guardar_ordenes_en_excel()

    def procesar_archivo_pdf(self, pdf_path):
        reconocimiento = ReconocimientoDatos()
        imagenes = convert_from_path(pdf_path, first_page=1, last_page=1)
        imagen_base = reconocimiento.convertir_a_escala_grises(imagenes[0])

        datos_acumulados = {"Orden": None, "Patente": None, "Siniestro": None, "Poliza": None}
        numero_de_orden_encontrado = False

        for _ in range(self.intentos):
            if _ != 0:
                imagen_base = reconocimiento.ajustar_brillo_contraste(imagen_base)

            reconocimiento.extraer_texto(imagen_base)
            datos_iteracion = reconocimiento.extraer_datos()

            for dato, valor in datos_iteracion.items():
                if valor:
                    reconocimiento.set_dato(dato, valor)
                    datos_acumulados[dato] = valor

                    if dato == "Orden":
                        numero_de_orden_encontrado = True

            if numero_de_orden_encontrado:
                datos_acumulados["Poliza"] = None
                datos_acumulados["Siniestro"] = None
                break

        if datos_acumulados["Patente"] == "ILEGIBLE":
            print("=== BUSCO PATENTES ALTERNATIVAS ===")
            imagen_base = reconocimiento.convertir_a_escala_grises(imagenes[0])

            for _ in range(self.intentos):
                if _ != 0:
                    imagen_base = reconocimiento.ajustar_brillo_contraste(imagen_base)

                reconocimiento.extraer_texto(imagen_base)
                patente_alternativa = reconocimiento.extraer_patente(archivo_pdf)

                if patente_alternativa and patente_alternativa != "ILEGIBLE":
                    datos_acumulados["Patente"] = patente_alternativa
                    reconocimiento.set_dato("Patente", patente_alternativa)
                    break

        print("Datos Acumulados:", datos_acumulados)
        reconocimiento.renombrar_archivo_pdf(pdf_path)

    def guardar_ordenes_en_excel(self):
        if self.ordenes_procesadas:
            df_ordenes = pd.DataFrame({"ORDEN": self.ordenes_procesadas})
            df_ordenes.to_excel("ordenes_procesadas.xlsx", index=False)

def obtener_ruta_subcarpeta(nombre_subcarpeta):
    directorio_actual = os.getcwd()
    return os.path.join(directorio_actual, nombre_subcarpeta)

def leer_nombres():
    ruta_carpeta = os.path.join(os.path.dirname(__file__), 'archivos')
    ruta_excel = os.path.join(os.path.dirname(__file__), 'archivo.xlsx')
    new_names = Lector(ruta_carpeta, ruta_excel)
    new_names.registrar()

if __name__ == "__main__":
    nombre_subcarpeta = 'archivos'
    directorio_pdf = obtener_ruta_subcarpeta(nombre_subcarpeta)
    procesador = ProcesadorPDF(directorio_pdf)
    procesador.procesar_archivos_pdf_en_directorio()

    leer_nombres()
