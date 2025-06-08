#!/usr/bin/env python
# procesador_pdf.py
from pdf2image import convert_from_path
import os
from PIL import Image
from reconocimiento_datos import ReconocimientoDatos
import pandas as pd
from lector_de_nombre import Lector

class ProcesadorPDF:
    def __init__(self, pdf_directory):
        self.pdf_directory = pdf_directory
        self.ruta_imagen_base = "pagina_1_base.png"
        self.intentos = 7
        self.ordenes_procesadas = []

    def procesar_archivos_pdf_en_directorio(self):
        for filename in os.listdir(self.pdf_directory):
            if filename.lower().endswith(".pdf"):
                archivo_pdf = os.path.join(self.pdf_directory, filename)
                self.procesar_archivo_pdf(archivo_pdf)

        # Guardar las órdenes procesadas en un archivo Excel
        self.guardar_ordenes_en_excel()

    def procesar_archivo_pdf(self, pdf_path):
        reconocimiento = ReconocimientoDatos()

        # Verificar si la imagen base existe
        if not os.path.exists(self.ruta_imagen_base):
            # Descargar la imagen base solo la primera vez
            imagenes = convert_from_path(pdf_path, first_page=1, last_page=1)
            imagen_base = imagenes[0]
            reconocimiento.convertir_a_escala_grises_y_guardar(imagen_base, self.ruta_imagen_base)
        else:
            imagen_base = Image.open(self.ruta_imagen_base)

        # Inicializar datos fuera del bucle
        datos_acumulados = {"Orden": None, "Patente": None, "Siniestro": None, "Poliza": None}

        # Bandera para indicar si se encontró el número de orden
        numero_de_orden_encontrado = False

        for _ in range(self.intentos):
            # Copiar la imagen base para realizar ajustes
            imagen = imagen_base.copy()

            # Aplicar ajustes en la imagen
            if _ != 0:
                reconocimiento.ajustar_brillo_contraste_y_guardar(self.ruta_imagen_base)

            # Extraer texto y datos
            texto_extraido = reconocimiento.extraer_texto(self.ruta_imagen_base)

            # Actualizar datos acumulados
            datos_iteracion = reconocimiento.extraer_datos()
            print(datos_iteracion)

            for dato, valor in datos_iteracion.items():
                print(f"dato reconocido: {dato}'--'{valor} ")
                if valor is not None:
                    reconocimiento.set_dato(dato, valor)
                    print(f"----------------------------------------------Dato encontrado: <{dato}> {reconocimiento.get_dato(dato)}")
                    datos_acumulados[dato] = valor

                    # Si se encuentra el número de orden, establecer la bandera
                    if dato == "Orden":
                        numero_de_orden_encontrado = True

            # Si se encontró el número de orden, no buscar para ese caso ni poliza ni siniestro
            if numero_de_orden_encontrado:
                datos_acumulados["Poliza"] = None
                datos_acumulados["Siniestro"] = None

            # Actualizar el objeto reconocimiento después del bucle
            for dato, valor in datos_acumulados.items():
                reconocimiento.set_dato(dato, valor)

            # Guardar el número de orden procesado
            orden_procesada = datos_acumulados["Orden"]
            if orden_procesada is not None:
                self.ordenes_procesadas.append(orden_procesada)

        # Eliminar la imagen PNG después de procesar el archivo antes de la revision alternativa
        os.remove(self.ruta_imagen_base)

        if datos_acumulados["Patente"]=="ILEGIBLE":
            print("                                          ================= BUSCO PATENTES ALTERNATIVAS ===================")
            # Descargar la imagen base nuevamente
            imagenes = convert_from_path(pdf_path, first_page=1, last_page=1)
            imagen_base = imagenes[0]
            reconocimiento.convertir_a_escala_grises_y_guardar(imagen_base, self.ruta_imagen_base)

            for _ in range(self.intentos):
                # Copiar la imagen base para realizar ajustes
                imagen = imagen_base.copy()

                # Aplicar ajustes en la imagen
                if _ != 0:
                    reconocimiento.ajustar_brillo_contraste_y_guardar(self.ruta_imagen_base)

                # Extraer texto y datos
                texto_extraido = reconocimiento.extraer_texto(self.ruta_imagen_base)

                # Actualizar datos acumulados
                patente_alternativa = reconocimiento.extraer_patente_alternativa()
                print("PATENTE ALTERNATIVA ENCONTRADA: --> ",patente_alternativa)

                if patente_alternativa is not None and patente_alternativa != "ILEGIBLE":
                    datos_acumulados["Patente"] = patente_alternativa
                    reconocimiento.set_dato("Patente", patente_alternativa)
                    break

            # Eliminar la imagen PNG después de procesar el archivo
            os.remove(self.ruta_imagen_base)






        print("Datos Acumulados: ---------------------------------------------------------------------")
        print(datos_acumulados)
        print("---------------------------------------------------------------------")
        reconocimiento.renombrar_archivo_pdf(pdf_path)



    def guardar_ordenes_en_excel(self):
        if self.ordenes_procesadas:
            # Crear un DataFrame de pandas
            df_ordenes = pd.DataFrame({"ORDEN": self.ordenes_procesadas})

            # Guardar en un archivo de Excel sin índice
            df_ordenes.to_excel("ordenes_procesadas.xlsx", index=False)


def obtener_ruta_subcarpeta(nombre_subcarpeta):
    # Obtener el directorio de trabajo actual
    directorio_actual = os.getcwd()

    # Obtener la ruta completa de la subcarpeta
    ruta_subcarpeta = os.path.join(directorio_actual, nombre_subcarpeta)
    
    return ruta_subcarpeta

def leer_nombres():
    ruta_carpeta    = os.path.join(os.path.dirname(__file__), 'archivos')
    ruta_excel = os.path.join(os.path.dirname(__file__), 'archivo.xlsx')
    new_names = Lector(ruta_carpeta, ruta_excel)
    new_names.registrar()

if __name__ == "__main__":
    nombre_subcarpeta = 'archivos'
    directorio_pdf = obtener_ruta_subcarpeta(nombre_subcarpeta)
    procesador = ProcesadorPDF(directorio_pdf)
    procesador.procesar_archivos_pdf_en_directorio()

    leer_nombres()