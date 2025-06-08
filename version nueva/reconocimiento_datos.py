import pytesseract
import numpy as np
import re
from PIL import Image
import cv2
import os

class ReconocimientoDatos:
    def __init__(self):
        self.texto = None
        self.patente = None
        self.orden = None
        self.siniestro = None
        self.poliza = None

    def convertir_a_escala_grises(self, imagen):
        """Convierte una imagen a escala de grises."""
        return imagen.convert('L')

    def extraer_texto(self, imagen):
        """Utiliza Tesseract para realizar OCR en la imagen en español."""
        self.texto = pytesseract.image_to_string(imagen, lang='spa')
        self.texto = self.limpiar_texto(self.texto)
        print(self.texto)

    def limpiar_texto(self, texto):
        """Elimina múltiples espacios y saltos de línea consecutivos."""
        return re.sub(r'(\s*\n\s*)+', '\n', texto)

    def extraer_datos(self):
        """Extrae los datos de la imagen."""
        datos = {
            "Orden": self.extraer_orden(),
            "Patente": self.extraer_patente(archivo_pdf),
            "Siniestro": None,
            "Poliza": None
        }
        
        # Si se encuentra el número de orden, se prioriza la devolución de ese dato.
        if datos["Orden"]:
            return datos

        # Si no se encontró el número de orden, buscar otros datos.
        datos.update({
            "Siniestro": self.extraer_siniestro(),
            "Poliza": self.extraer_poliza()
        })

        return datos

    def extraer_orden(self):
        """Extrae el número de orden utilizando un patrón regex."""
        patron = r"(?i)Orden(?:\s*de\s*servicio)?\s*.{0,5}(\d{7})"
        resultado = re.search(patron, self.texto)
        return resultado.group(1) if resultado else None

    def extraer_patente(self, archivo_pdf):
        """Extrae la patente utilizando el patrón estándar."""
        patron_estandar = r"\b([A-Za-z]{2}\d{3}[A-Za-z]{2}|[A-Za-z]{3}\d{3})\b"
        resultado_patente = re.search(patron_estandar, self.texto, flags=re.IGNORECASE)

        if resultado_patente:
            patente = resultado_patente.group(1)
            return self.validar_y_corregir_patente(patente)

        # Si no se encuentra una patente válida, se considera "ILEGIBLE"
        self.generar_excel_ilegible(archivo_pdf)
        return "ILEGIBLE"

    def generar_excel_ilegible(self, archivo_pdf):
        """Genera un archivo Excel con todas las palabras de 6, 7 y 8 caracteres si la patente es ilegible."""
        palabras = re.findall(r'\b[A-Za-z0-9]{6,8}\b', self.texto)
        
        # Crear un DataFrame con las palabras encontradas
        df = pd.DataFrame(palabras, columns=["Palabras"])
        
        # Generar el nombre del archivo Excel basado en el nombre del archivo PDF original
        nombre_excel = os.path.splitext(os.path.basename(archivo_pdf))[0] + "_ilegible.xlsx"
        ruta_excel = os.path.join(os.getcwd(), nombre_excel)
        
        # Guardar el DataFrame en un archivo Excel
        df.to_excel(ruta_excel, index=False)
        print(f"Archivo Excel guardado en: {ruta_excel}")

    def validar_y_corregir_patente(self, patente):
        """Valida y corrige la patente si es necesario."""
        # Primero, validamos con el formato original
        if self.validar_patente(patente):
            return patente
        
        # Si contiene '0' o 'O', aplicamos la corrección
        if '0' in patente or 'O' in patente:
            patente_corregida = self.corregir_patente(patente)
            if self.validar_patente(patente_corregida):
                return patente_corregida

        return "ILEGIBLE"

    def corregir_patente(self, patente):
        """Aplica correcciones comunes para confusiones entre 'O' y '0'."""
        # Reemplazar posibles confusiones
        patente = patente.replace('0', 'O').replace('O0', 'O').replace('0O', 'O')
        patente = patente.replace('OO', 'O').replace('5', 'S')

        return patente.upper()

    def validar_patente(self, patente):
        """Valida si la patente tiene un formato válido."""
        # Patente de 6 caracteres: 3 letras seguidas de 3 números
        if re.fullmatch(r'[A-Z]{3}\d{3}', patente):
            return True
        # Patente de 7 caracteres: 2 letras seguidas de 3 números y 2 letras
        if re.fullmatch(r'[A-Z]{2}\d{3}[A-Z]{2}', patente):
            return True

        return False

    def analizar_resultado_patente(self, resultado_patente):
        if resultado_patente:
            patente = resultado_patente.group(1).replace('-', '')
            if len(patente) == 6:
                return self.corregir_patente_seis_caracteres(patente)
            elif len(patente) == 7:
                return self.corregir_patente_siete_caracteres(patente)
        return "ILEGIBLE"

    
    def corregir_patente_seis_caracteres(self, patente):
        """Corrige errores comunes en patentes de seis caracteres donde hay confusión entre 'O' y '0'."""
        letras, numeros = patente[:3], patente[3:]
        
        # Reemplazar posibles confusiones
        letras = letras.replace('0', 'O').replace('1', 'I').replace('5', 'S')
        numeros = numeros.replace('O', '0').replace('I', '1').replace('S', '5')
        
        # Eliminar combinaciones no deseadas como 'OO' o '00'
        letras = re.sub(r'[0O]{2}', '', letras)
        
        # Reconstruir la patente corregida
        patente_corregida = (letras + numeros).upper()
        
        return patente_corregida if len(patente_corregida) == 6 else "ILEGIBLE"

    def corregir_patente_siete_caracteres(self, patente):
        """Corrige errores comunes en patentes de siete caracteres."""
        letras1, numeros, letras2 = patente[:2], patente[2:5], patente[5:]
        letras1 = letras1.replace('0', 'O').replace('1', 'I').replace('5', 'S')
        numeros = numeros.replace('O', '0').replace('I', '1').replace('S', '5')
        letras2 = letras2.replace('0', 'O').replace('1', 'I').replace('5', 'S')
        return (letras1 + numeros + letras2).upper()

    def extraer_siniestro(self):
        """Extrae el número de siniestro utilizando un patrón regex."""
        patron = r"(?i)S?tro\s*:\s*([\d\s\/\*\.,-]+)"
        resultado = re.search(patron, self.texto)
        if resultado:
            return re.sub(r'[\\/:\*\?"<>\|]', '_', resultado.group(1))
        return None

    def extraer_poliza(self):
        """Extrae el número de póliza utilizando un patrón regex."""
        patron = r"(?i)P[óo]liza\s*[:=/]?\s*(\d+(?:[\s\/-]\d+)*)"
        resultado = re.search(patron, self.texto)
        if resultado:
            poliza = re.sub(r'[\\:\*\?"<>\|]', '_', resultado.group(1))
            return poliza.replace("/", "-")
        return None

    def ajustar_brillo_contraste(self, imagen):
        """Ajusta el brillo y contraste de la imagen."""
        imagen = np.array(imagen)
        alpha, beta = 1.05, 10
        imagen_ajustada = cv2.convertScaleAbs(imagen, alpha=alpha, beta=beta)

        if imagen_ajustada is not None:
            gamma = 1.2
            imagen_ajustada = np.uint8(np.power(imagen_ajustada / 255.0, gamma) * 255.0)
            return Image.fromarray(imagen_ajustada)
        else:
            print("No se pudo ajustar la imagen. La imagen es None.")
            return imagen

    def set_dato(self, dato, valor):
        """Actualiza el valor del atributo correspondiente."""
        if valor is not None:
            setattr(self, dato.lower(), valor)

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
        """Limpia el nombre del archivo eliminando saltos de línea y espacios duplicados."""
        return ' '.join(nombre.replace('\n', '').replace('\r', '').split())

    def datos_None_a_str(self):
        """Convierte atributos None a una cadena vacía para evitar errores."""
        for attr in ["orden", "patente", "siniestro", "poliza"]:
            valor = getattr(self, attr)
            setattr(self, attr, valor or "")
