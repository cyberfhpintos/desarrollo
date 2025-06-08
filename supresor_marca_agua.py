
import cv2
import numpy as np
from PIL import Image

class SupresorMarcaAgua:
    def __init__(self, ruta_marca_agua):
        self.marca = cv2.imread(ruta_marca_agua, cv2.IMREAD_GRAYSCALE)
        if self.marca is None:
            raise ValueError("No se pudo cargar la imagen de la marca de agua.")

    def aplicar(self, ruta_imagen_original, ruta_salida=None, umbral_relativo=2, umbral_template=0.8):
        imagen = cv2.imread(ruta_imagen_original, cv2.IMREAD_GRAYSCALE)
        if imagen is None:
            raise ValueError("No se pudo cargar la imagen original.")

        # Detección de marca de agua por coincidencia de plantilla
        resultado = cv2.matchTemplate(imagen, self.marca, cv2.TM_CCOEFF_NORMED)
        ubicaciones = np.where(resultado >= umbral_template)

        # Crear máscara con zonas detectadas
        mascara = np.zeros_like(imagen, dtype=np.uint8)
        alto_marca, ancho_marca = self.marca.shape
        for pt in zip(*ubicaciones[::-1]):
            cv2.rectangle(mascara, pt, (pt[0] + ancho_marca, pt[1] + alto_marca), 255, -1)

        # Aislar las zonas con marca
        zona_afectada = np.where(mascara == 255, imagen, 255)

        # Calcular niveles de gris presentes solo en zona afectada
        niveles = zona_afectada[zona_afectada < 255]
        if niveles.size == 0:
            return Image.fromarray(imagen)  # No se detectó marca

        nivel_negro = np.min(niveles)
        umbral = nivel_negro + umbral_relativo

        # Binarización selectiva
        binarizada = np.where((mascara == 255) & (imagen <= umbral), 0, 255).astype(np.uint8)

        # Restaurar zonas no afectadas
        final = np.where(mascara == 255, binarizada, imagen).astype(np.uint8)

        if ruta_salida:
            cv2.imwrite(ruta_salida, final)

        return Image.fromarray(final)
