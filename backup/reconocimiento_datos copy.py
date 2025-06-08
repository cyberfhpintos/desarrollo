# reconocimiento_datos.py
import pytesseract
import numpy as np
import re
from PIL import Image
import cv2
import os

class ReconocimientoDatos:
    def __init__(self):
        self.ruta_imagen_base = "pagina_1_base.png"
        self.texto = None
        self.patente = None
        self.orden = None
        self.siniestro = None
        self.poliza = None

    def convertir_a_escala_grises_y_guardar(self, imagen, ruta_guardado):
        """Convierte una imagen a escala de grises y la guarda en la ruta especificada."""
        imagen_gris = imagen.convert('L')
        imagen_gris.save(ruta_guardado)

    def extraer_texto(self, ruta_imagen):
        """Utiliza Tesseract para realizar OCR en la imagen en español.
        Busca el número de orden y el código de patente en el texto extraído.
        Retorna el texto extraído, el número de orden y el código de patente."""
        self.texto = pytesseract.image_to_string(Image.open(ruta_imagen), lang='spa')
        print(self.texto)

    def extraer_datos(self):
        orden = self.extraer_orden()
        
        if orden:
            # Si se encuentra el número de orden, devolver solo el número de orden y establecer poliza y siniestro como None
            return {"Orden": orden, "Patente": self.extraer_patente(), "Siniestro": None, "Poliza": None}

        # Si no se encuentra el número de orden, continuar con la extracción normal de datos
        return {
            "Patente": self.extraer_patente(),
            "Orden": orden,
            "Siniestro": self.extraer_siniestro(),
            "Poliza": self.extraer_poliza()
        }

    def extraer_orden(self):
        patron_orden = r"(?i)Orden\s*.{0,5}(\d{7})"
        resultado_orden = re.search(patron_orden, self.texto)
        return(resultado_orden.group(1) if resultado_orden else None)

    def extraer_patente(self):
        # Patrón para buscar la patente en cualquier posición del texto
        patron_patente = r"\b\s*([A-Za-z]{2}\d{3}[A-Za-z]{2}|[A-Za-z]{3}\d{3}|[A-Z]{3}[Oo0]{2}\d{3})\s*\b"

        # Buscar la patente en el texto
        resultado_patente = re.search(patron_patente, self.texto, flags=re.IGNORECASE)

        if resultado_patente:
            patente = resultado_patente.group(1)
            if len(patente) == 8 and patente[:3].isalpha() and patente[-3:].isdigit():
                # Si la longitud es 8 y los primeros 3 son letras y los últimos 3 son dígitos, entonces es del formato [A-Z]{3}00\d{3}

                return(patente[:3].upper() + patente[-3:])
            else:
                return(patente.upper())

        # Intentar con el patrón alternativo si el primero falla
        patente_alternativa = self.extraer_patente_alternativa()
        return patente_alternativa

    def extraer_patente_alternativa(self):
        # Patrón alternativo para buscar la patente en cualquier posición del texto
        patron_patente_alternativo = r"\b\s*([A-Za-z]{2}[1IiLlOo0]{3}[A-Za-z]{2}|[A-Z]{3}[Oo0]{2}[1IiLlOo0]{3}[A-Za-z]{2})\s*\b"

        # Buscar la patente con el patrón alternativo en el texto
        resultado_patente_alternativa = re.search(patron_patente_alternativo, self.texto, flags=re.IGNORECASE)

        if resultado_patente_alternativa:
            patente_alternativa = resultado_patente_alternativa.group(1)
            # Reemplazar 'O' por '0' y '1' por 'I' en la patente alternativa
            patente_alternativa = patente_alternativa.replace('O', '0').replace('1', 'I').replace('l', 'I')
            if len(patente_alternativa) == 8 and patente_alternativa[:3].isalpha() and patente_alternativa[-3:].isdigit():
                # Si la longitud es 8 y los primeros 3 son letras y los últimos 3 son dígitos, entonces es del formato [A-Z]{3}00\d{3}
                return patente_alternativa[:3].upper() + patente_alternativa[-3:]
            else:
                return patente_alternativa.upper()
        return None

    def extraer_siniestro(self):
        # Patrón para buscar un número con guiones o espacios separadores
        patron_siniestro = r"(?i)Siniestro\s*:\s*([\d\s\/\*\.,-]+)"

        # Buscar el número de siniestro en el texto
        resultado_siniestro = re.search(patron_siniestro, self.texto)

        if resultado_siniestro:
            siniestro = resultado_siniestro.group(1)
            # Remover caracteres no permitidos en nombres de archivos
            siniestro = re.sub(r'[\\/:\*\?"<>\|]', '_', siniestro)
            return siniestro
        return None

    def extraer_poliza(self):
        # Patrón para buscar un número de póliza con guiones o espacios separadores
        patron_poliza = r"(?i)P[óo]liza\s*[:=]?\s*(\d+(?:[\s-]\d+)*)"
        
        # Buscar el número de póliza en el texto
        resultado_poliza = re.search(patron_poliza, self.texto)

        if resultado_poliza:
            poliza = resultado_poliza.group(1)
            # Remover caracteres no permitidos en nombres de archivos
            poliza = re.sub(r'[\\/:\*\?"<>\|]', '_', poliza)
            return poliza
        return None

    def get_dato(self, dato):
        if dato == "Patente":
            return(self.patente)
        elif dato == "Orden":
            return(self.orden)
        elif dato == "Siniestro":
            return(self.siniestro)
        elif dato == "Poliza":
            return(self.poliza)
        else:
            print(f"\n\n ERROR EN GET DE PARAMETRO -{dato}- VERIFICAR DATO A ACCEDER 'n\n")

    def set_dato(self, dato, valor):
        if valor is not None:
            setattr(self, dato.lower(), valor)
            print(f"el nuevo dato {dato} es {valor}")
        else:
            print(f"\n\n ERROR EN SET DE PARAMETRO -{dato}- VERIFICAR DATO A ACCEDER 'n\n")


    def ajustar_brillo_contraste_y_guardar(self, ruta_imagen):
        """Ajusta el brillo y contraste de la imagen y la guarda."""
        imagen = cv2.imread(ruta_imagen)
        # Realiza ajuste de brillo y contraste según tus necesidades
        # Por ejemplo, aquí se aumenta el brillo y el contraste
        alpha = 1.05  # factor de contraste
        beta = 10   # factor de brillo
        imagen_ajustada = cv2.convertScaleAbs(imagen, alpha=alpha, beta=beta)
        # Aplica la corrección gamma
        gamma = 1.2
        imagen_ajustada = np.power(imagen_ajustada / 255.0, gamma) * 255.0

        # Convierte la imagen a tipo uint8
        imagen_ajustada = np.uint8(imagen_ajustada)
        # Guarda la imagen ajustada
        cv2.imwrite(ruta_imagen, imagen_ajustada)


    def renombrar_archivo_pdf(self, original):
        print(self.orden, self.patente, self.poliza, self.siniestro)
        """Renombra el archivo PDF original con el formato deseado."""
        self.datos_None_a_str()

        variables = ["patente", "orden", "poliza", "siniestro"]

        for variable in variables:
            valor = getattr(self, variable)
            setattr(self, variable, f" -{variable[:3]} {valor}" if (valor is not None) and (valor != "") else "")

        nuevo_nombre = f"{original.split('.')[0]}{self.patente}{self.orden}{self.poliza}{self.siniestro}.pdf"
        nuevo_nombre = self.limpiar_nombre_archivo(nuevo_nombre)
        

        if any([getattr(self, variable) for variable in variables]):
            os.rename(original, nuevo_nombre)
            print(f"Archivo renombrado a: {nuevo_nombre}")
        else:
            print("No se pudo renombrar el archivo por falta de datos")
            
    def limpiar_nombre_archivo(self, nombre):
        # Eliminar saltos de línea
        nombre_limpio = nombre.replace('\n', '').replace('\r', '')

        # Eliminar espacios duplicados
        nombre_limpio = ' '.join(nombre_limpio.split())

        return nombre_limpio

    def datos_None_a_str(self):
        atributos = ["orden", "patente", "siniestro", "poliza"]

        for atributo in atributos:
            valor = getattr(self, atributo)
            setattr(self, atributo, f" {valor}" if valor is not None else "")

