#!/usr/bin/env python3.12

# procesador_pdf.py
from pdf2image import convert_from_path
import os
from PIL import Image
from reconocimiento_datos import ReconocimientoDatos
import pandas as pd
from lector_de_nombre import Lector
import tkinter as tk
from tkinter import filedialog
import sys
import io
from datetime import datetime


class ProcesadorPDF:
    def __init__(self, pdf_directory):
        self.pdf_directory = pdf_directory
        self.ruta_imagen_base = "pagina_1_base.png"
        self.intentos = 7
        self.ordenes_procesadas = []
        self._stdout_original = sys.stdout
        self._consola_buffer = io.StringIO()
        sys.stdout = self._consola_buffer



    def procesar_archivos_pdf_en_directorio(self):
        for filename in os.listdir(self.pdf_directory):
            if filename.lower().endswith(".pdf"):
                archivo_pdf = os.path.join(self.pdf_directory, filename)
                # self.generar_imagen_base(archivo_pdf)  # Necesario para crear la imagen base
                self.procesar_archivo_pdf(archivo_pdf)

        # Guardar las órdenes procesadas en un archivo Excel
        self.guardar_ordenes_en_excel()
        # Restaurar consola original
        sys.stdout = self._stdout_original

        # Guardar log a archivo
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_log = f"log_OCR_{timestamp}.txt"
        with open(nombre_log, "w", encoding="utf-8") as f:
            f.write(self._consola_buffer.getvalue())

        print(f"\n📝 Log guardado en: {nombre_log}")


    def procesar_archivo_pdf(self, pdf_path):
        reconocimiento = ReconocimientoDatos()

        # Nombre base del PDF (sin extensión)
        nombre_base = os.path.splitext(os.path.basename(pdf_path))[0]
        ruta_imagen_base = f"pagina_1_base_{nombre_base}.png"

        # Si no existe la imagen, crearla desde la primera página del PDF
        if not os.path.exists(ruta_imagen_base):
            imagenes = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300)
            imagen_base = imagenes[0]
            reconocimiento.convertir_a_escala_grises_y_guardar(imagen_base, ruta_imagen_base)
        else:
            imagen_base = Image.open(ruta_imagen_base)

        imagen_original = imagen_base.copy()
        datos_acumulados = {"Orden": None, "Patente": None, "Siniestro": None, "Poliza": None, "Compania": None}

        for intento in range(self.intentos):
            imagen = imagen_base.copy()
            if intento != 0:
                reconocimiento.ajustar_brillo_contraste_y_guardar(ruta_imagen_base)

            reconocimiento.extraer_texto(ruta_imagen_base)
            datos_iteracion = reconocimiento.extraer_datos()

            for dato, valor in datos_iteracion.items():
                if datos_acumulados[dato] is None and valor is not None:
                    datos_acumulados[dato] = valor
                    reconocimiento.set_dato(dato, valor)

            if datos_acumulados["Orden"] and reconocimiento.identificar_compania() == 'FEDPAT':
                datos_acumulados["Poliza"] = None
                datos_acumulados["Siniestro"] = None
                break

            if all(valor is not None for clave, valor in datos_acumulados.items() if clave != "Patente"):
                break

        # Reintento con imagen original + realce si faltan datos clave
        datos_faltantes = any(
            datos_acumulados[clave] is None
            for clave in ["Siniestro", "Poliza", "Patente"]
        )

        if datos_faltantes:
            print("Reintento OCR sobre imagen original con realce por fondo gris...")

            imagen_corr = self.realzar_texto_sobre_fondo_gris(imagen_original)
            imagen_corr.save(ruta_imagen_base)

            reconocimiento.extraer_texto(ruta_imagen_base)
            datos_extra = reconocimiento.extraer_datos()

            for clave, valor in datos_extra.items():
                if datos_acumulados[clave] is None and valor is not None:
                    datos_acumulados[clave] = valor
                    reconocimiento.set_dato(clave, valor)

        # Actualizar datos en el objeto
        for dato, valor in datos_acumulados.items():
            reconocimiento.set_dato(dato, valor)

        # Mostrar resumen de datos extraídos
        print(f"\n🧾  RESUMEN DE EXTRACCIÓN OCR PARA: {nombre_base}")
        for clave in ["Orden", "Patente", "Siniestro", "Poliza"]:
            valor = datos_acumulados[clave]
            estado = "✔" if valor else "✘"
            color = "\033[92m" if valor else "\033[91m"
            print(f"{color}{estado} {clave}: {valor if valor else 'NO DETECTADO'}\033[0m")

        # Registrar número de orden
        orden_procesada = datos_acumulados["Orden"]
        if orden_procesada is not None:
            self.ordenes_procesadas.append(orden_procesada)

        # Si no se obtuvo patente o es ilegible, ofrecer ingreso manual
        if datos_acumulados["Patente"] in [None, "ILEGIBLE"]:
            print("🟡 No se detectó una patente válida. Mostrando ventana de ingreso manual...")
            patente_manual = reconocimiento.mostrar_ventana_seleccion()
            if patente_manual:
                datos_acumulados["Patente"] = patente_manual
                reconocimiento.set_dato("Patente", patente_manual)


        # Renombrar el archivo original según los datos extraídos
        reconocimiento.renombrar_archivo_pdf(pdf_path)

        # (Opcional) Eliminar imagen base generada
        if os.path.exists(ruta_imagen_base):
            try:
                os.remove(ruta_imagen_base)
            except Exception as e:
                print(f"⚠️ No se pudo eliminar {ruta_imagen_base}: {e}")


    def realzar_texto_sobre_fondo_gris(self, imagen):
        """Intenta eliminar fondos grises sin afectar texto oscuro."""
        imagen = imagen.convert("L")  # Escala de grises

        # Eliminar tonos intermedios (gris claro)
        imagen = imagen.point(lambda x: 0 if 130 < x < 190 else 255, mode='1')

        return imagen.convert("L")  # Devuelve imagen lista para OCR


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


def seleccionar_carpeta():
    # Crear una ventana de tkinter (no visible)
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal

    # Mostrar el diálogo para seleccionar una carpeta
    carpeta_seleccionada = filedialog.askdirectory(
                                                    title="Seleccione la carpeta de trabajo",
                                                    initialdir=os.path.join(os.path.dirname(__file__), 'archivos')  # Carpeta predeterminada
                                                )
    root.destroy()  # Destruir la ventana después de seleccionar
    return carpeta_seleccionada


def leer_nombres(ruta_carpeta = os.path.join(os.path.dirname(__file__), 'archivos') ):
    ruta_excel = os.path.join(os.path.dirname(__file__), 'archivo.xlsx')
    new_names = Lector(ruta_carpeta, ruta_excel)
    new_names.registrar()


if __name__ == "__main__":
    # Seleccionar la carpeta de trabajo
    carpeta_trabajo = seleccionar_carpeta()

    if carpeta_trabajo:  # Si el usuario seleccionó una carpeta
        print(f"Carpeta seleccionada: {carpeta_trabajo}")
        procesador = ProcesadorPDF(carpeta_trabajo)
        procesador.procesar_archivos_pdf_en_directorio()

        leer_nombres(carpeta_trabajo)
    else:
        print("No se seleccionó ninguna carpeta. El programa ha finalizado.")