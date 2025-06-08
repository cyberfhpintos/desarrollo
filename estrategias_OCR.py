import cv2
import numpy as np
from PIL import Image
import os

def ocr_bordes_y_dilatacion(img_cv2, reconocimiento):
    """
    Aplica Canny + dilatación a la imagen para mejorar trazos OCR.
    """
    try:
        # Escala de grises y bordes
        gris = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2GRAY)
        bordes = cv2.Canny(gris, 100, 200)

        # Dilatar trazos
        kernel = np.ones((2, 2), np.uint8)
        dilatada = cv2.dilate(bordes, kernel, iterations=1)

        # Convertir a 3 canales y guardar temporalmente
        img_dilatada = cv2.cvtColor(dilatada, cv2.COLOR_GRAY2BGR)
        temp_path = "temp_ocr_bordes_dilatacion.png"
        Image.fromarray(cv2.cvtColor(img_dilatada, cv2.COLOR_BGR2RGB)).save(temp_path)

        # Ejecutar OCR y extraer datos
        reconocimiento.extraer_texto(temp_path)
        datos = reconocimiento.extraer_datos()
        os.remove(temp_path)

        return datos.get("Patente")

    except Exception as e:
        print(f"⚠ Error en ocr_bordes_y_dilatacion: {e}")
        return None
