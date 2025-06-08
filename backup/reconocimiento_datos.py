# reconocimiento_datos.py
import pytesseract
import numpy as np
import re
from PIL import Image
import cv2
import os
import tkinter as tk
from tkinter import simpledialog, messagebox


class ReconocimientoDatos:
    def __init__(self):
        self.ruta_imagen_base = "pagina_1_base.png"
        self.texto = None
        self.patente = None
        self.orden = None
        self.siniestro = None
        self.poliza = None
        self.candidatas_patente = []  # Nueva lista para almacenar todas las candidatas

    def agregar_candidata(self, patente):
        """Agrega una patente candidata si no está ya en la lista de candidatas."""
        if patente not in self.candidatas_patente:
            self.candidatas_patente.append(patente)

    def limpiar_candidatas(self):
        """Limpia la lista de candidatas. Se ejecuta al iniciar el procesamiento de un nuevo archivo."""
        self.candidatas_patente = []

    def convertir_a_escala_grises_y_guardar(self, imagen, ruta_guardado):
        """Convierte una imagen a escala de grises y la guarda en la ruta especificada."""
        imagen_gris = imagen.convert('L')
        imagen_gris.save(ruta_guardado)

    def extraer_texto(self, ruta_imagen):
        """Utiliza Tesseract para realizar OCR en la imagen en español.
        Busca el número de orden y el código de patente en el texto extraído.
        Retorna el texto extraído, el número de orden y el código de patente."""
        self.texto = pytesseract.image_to_string(Image.open(ruta_imagen), lang='spa')
        self.texto = self.limpiar_texto(self.texto)  # Limpiar el texto
        self.resaltador(self.texto)

    def resaltador(self, texto):
        print("\033[93m")  # Color amarillo
        print("* - " * 50)
        print(texto)
        print("° " * 100)
        print("\033[0m")   # Reset color

    def limpiar_texto(self, texto):
        # Eliminar múltiples espacios y saltos de línea consecutivos
        texto_limpio = re.sub(r'(\s*\n\s*)+', '\n', texto)
        return (texto_limpio)

    def extraer_datos(self):
        orden = self.extraer_orden()
        compania = self.identificar_compania()
        siniestro = self.extraer_siniestro()
        poliza = self.extraer_poliza()
        patente = self.extraer_patente()

        if patente is None:
            patente = self.procesar_patente()

        if compania == 'FEDPAT':
            # Federación Patronal: solo orden, NO póliza ni siniestro.
            siniestro = None
            poliza = None
        else:
            # Cualquier otra compañía: El número de orden es irrelevante.
            orden = None

        return {
            "Patente": patente,
            "Orden": orden,
            "Siniestro": siniestro,
            "Poliza": poliza,
            "Compania": compania
        }


    def extraer_orden(self):
        #patron_orden = r"(?i)Orden\s*.{0,5}(\d{7})"
        #patron_orden = r"(?i)Orden(?:\s* de Servicio)?[^\d]*?(\d{5,15}])"
        patron_orden = r"(?i)Orden(?:\s*de\s*servicio)?\s*.{0,5}(\d{7})"
        resultado_orden = re.search(patron_orden, self.texto)
        return(resultado_orden.group(1) if resultado_orden else None)

    def extraer_patente(self):
        patron_patente = r"\b\s*([A-Za-z]{2}\d{3}[A-Za-z]{2}|[A-Za-z]{3}\d{3}|[A-Z]{3}-?[Oo0]{2}\d{3})\s*\b"
        resultado_patente = re.search(patron_patente, self.texto, flags=re.IGNORECASE)
        return(self.analizar_resultado_patente(resultado_patente))

    def analizar_resultado_patente(self, resultado_patente):
        """Analiza el resultado de la patente y acumula las candidatas si no es válida."""
        if resultado_patente:
            patente = resultado_patente.group(1)
            patente = patente.replace('-', '')  # Limpiamos la patente eliminando guiones
            if len(patente) == 8:
                patente = patente[:3] + patente[-3:]
            if len(patente) == 6:
                patente_corregida = self.corregir_patente_seis_caracteres(patente)
                if self.validar_patente(patente_corregida, 6):
                    return patente_corregida
                else:
                    self.agregar_candidata(patente_corregida)  # Si no es válida, la agregamos como candidata
            elif len(patente) == 7:
                patente_corregida = self.corregir_patente_siete_caracteres(patente)
                if self.validar_patente(patente_corregida, 7):
                    return patente_corregida
                else:
                    self.agregar_candidata(patente_corregida)  # Si no es válida, la agregamos como candidata
        else:
            # Si no hay una patente válida, buscar palabras candidatas en todo el texto
            palabras_candidatas = self.encontrar_candidatas_patente()
            for palabra in palabras_candidatas:
                self.agregar_candidata(palabra)
        
        return None  # No se ha encontrado una patente válida en esta iteración


    def mostrar_ventana_seleccion(self):
        """Muestra una ventana emergente para seleccionar una patente de entre las candidatas."""
        root = tk.Tk()
        root.title("Seleccionar Patente")
        
        # Filtramos las patentes antes de mostrarlas
        candidatas = self.filtrar_patentes_candidatas()

        # Crear un marco para contener el Listbox, el Scrollbar y el Entry
        frame = tk.Frame(root)
        frame.pack(padx=10, pady=10)

        # Crear un Listbox para mostrar las patentes candidatas
        listbox = tk.Listbox(frame, selectmode=tk.SINGLE, width=50)
        listbox.pack(side=tk.LEFT)

        # Agregar las patentes candidatas al Listbox
        for patente in candidatas:
            listbox.insert(tk.END, patente)

        # Crear un Scrollbar y vincularlo al Listbox
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)

        # Crear un Entry para ingresar una patente manualmente
        entry_manual = tk.Entry(root, width=50)
        entry_manual.pack(pady=(10, 0))
        entry_manual.insert(0, "Ingrese una patente manualmente...")  # Texto sugerido
        
        # Variable para almacenar el resultado
        resultado = None

        # Función para seleccionar la patente
        def seleccionar():
            nonlocal resultado  # Declarar la variable como no local
            seleccion = listbox.curselection()  # Obtener el índice seleccionado
            if seleccion:
                # Obtener el valor seleccionado
                resultado = listbox.get(seleccion[0])
            else:
                # Si no hay selección, tomar el texto del Entry
                patente_manual = entry_manual.get().strip()
                if patente_manual and patente_manual != "Ingrese una patente manualmente...":
                    resultado = patente_manual
                else:
                    messagebox.showwarning("Advertencia", "Por favor, selecciona una patente o ingresa una manualmente.")
            root.destroy()  # Cerrar la ventana

        # Botón de aceptar
        button_aceptar = tk.Button(root, text="Aceptar", command=seleccionar)
        button_aceptar.pack(pady=(10, 0))

        root.mainloop()  # Iniciar el bucle de eventos
        return resultado

    def encontrar_candidatas_patente(self):
        """Encuentra todas las palabras que podrían ser posibles patentes basadas en longitud y patrón."""
        posibles_patentes = re.findall(r'\b[A-Za-z0-9]{6,7}\b', self.texto)
        return posibles_patentes

    def filtrar_patentes_candidatas(self):
        """Filtra las patentes para incluir solo aquellas con letras y números."""
        patentes_validas = []
        for patente in self.candidatas_patente:
            # Verificamos que haya al menos una letra y un número
            if re.search(r'[A-Za-z]', patente) and re.search(r'\d', patente):
                patentes_validas.append(patente)
        return patentes_validas

    def procesar_patente(self):
        """Procesa el reconocimiento de la patente en todas las iteraciones."""
        # Inicializamos la lista de candidatas al comenzar un nuevo archivo
        self.limpiar_candidatas()

        patente = None
        for _ in range(7):  # Intentamos 7 iteraciones de mejora de imagen y extracción de patente
            patente = self.extraer_patente()  # Intentamos extraer la patente en cada iteración
            if patente and patente != "ILEGIBLE":
                return patente  # Si encontramos una patente válida, terminamos aquí.

        # Si no se encontró una patente válida después de los 7 intentos, intentamos buscar patentes alternativas
        patente = self.buscar_patente_alternativa()
        if patente and patente != "ILEGIBLE":
            return patente  # Si encontramos una alternativa válida, terminamos aquí.
    
        return patente if patente else "ILEGIBLE"  # Si no hay selección, se marca como "ILEGIBLE"


    def buscar_patente_alternativa(self):
        """Intenta encontrar una patente alternativa si la primera búsqueda falla."""
        for _ in range(3):  # Intentamos otras 3 iteraciones con las patentes alternativas
            patente_alternativa = self.extraer_patente_alternativa()
            if patente_alternativa and patente_alternativa != "ILEGIBLE":
                return patente_alternativa  # Si encontramos una patente válida, la devolvemos
        return "ILEGIBLE"  # Si no encontramos, devolvemos ILEGIBLE    

    def corregir_patente_seis_caracteres(self, patente):
        # Lógica para corregir patentes de 6 caracteres
        letras_grupo = patente[:3]
        numeros_grupo = patente[3:]
        # Reemplazar '0', '1' y '5' por 'O', 'I' y 'S' respectivamente en el grupo de letras
        letras_grupo_corregido = letras_grupo.replace('0', 'O').replace('1', 'I').replace('5', 'S')
        # Reemplazar 'O', 'I' y 'S' por '0', '1' y '5' respectivamente en el grupo de números
        numeros_grupo_corregido = numeros_grupo.replace('O', '0').replace('I', '1').replace('S', '5')
        # Concatenar los grupos corregidos
        patente_corregida = letras_grupo_corregido + numeros_grupo_corregido
        return patente_corregida.upper()

    def corregir_patente_siete_caracteres(self, patente):
        # Lógica para corregir patentes de 7 caracteres
        letras_grupo1 = patente[:2]
        numeros_grupo2 = patente[2:5]
        letras_grupo3 = patente[5:]
        # Reemplazar '0', '1' y '5' por 'O', 'I' y 'S' respectivamente en el grupo de letras
        letras_grupo1_corregido = letras_grupo1.replace('0', 'O').replace('1', 'I').replace('5', 'S')
        # Reemplazar 'O', 'I' y 'S' por '0', '1' y '5' respectivamente en el grupo de números
        numeros_grupo2_corregido = numeros_grupo2.replace('O', '0').replace('I', '1').replace('S', '5')
        # Reemplazar '0', '1' y '5' por 'O', 'I' y 'S' respectivamente en el grupo de letras
        letras_grupo3_corregido = letras_grupo3.replace('0', 'O').replace('1', 'I').replace('5', 'S')
        # Concatenar los grupos corregidos
        patente_corregida = letras_grupo1_corregido + numeros_grupo2_corregido + letras_grupo3_corregido
        return patente_corregida.upper()

    def validar_patente(self, patente, longitud_esperada):
        # Validar la patente corregida con el patrón esperado
        patron_valido = r"\b\s*([A-Za-z]{2}\d{3}[A-Za-z]{2}|[A-Za-z]{3}\d{3}|[A-Z]{3}[Oo0]{2}\d{3})\s*\b"
        return len(patente) == longitud_esperada and re.fullmatch(patron_valido, patente, flags=re.IGNORECASE) is not None


    def extraer_patente_alternativa(self):
        #patron_patente = r"\b\s*([A-Za-z]{2}\d{3}[A-Za-z]{2}|[A-Za-z]{3}\d{3}|[A-Z]{3}[Oo0]{2}\d{3})\s*\b"
        patron_patente = r"(?i)\b(?:patente|dominio)[^\w\d]*([A-Za-z0-9]{3}-?[A-Za-z0-9]{3,4})\b"

        resultado_patente = re.search(patron_patente, self.texto, flags=re.IGNORECASE)
        return self.analizar_resultado_patente(resultado_patente)

    def identificar_compania(self):
        """
        Identifica la compañía aseguradora según palabras clave en el documento.
        Retorna un código único por cada compañía o 'DESCONOCIDA' por defecto.
        """

        texto_min = self.texto.lower()

        # Diccionario escalable con claves únicas por compañía
        companias = {
            'FEDPAT': ['federacion patronal', 'fedpat', 'fedpatronal', '@fedpat.com.ar'],
            # Acá agregás otras compañías en el futuro
            # 'SANCOR': ['sancor seguros', 'sancor', '@sancorseguros.com.ar'],
            # 'LA_CAJA': ['la caja', '@lacaja.com.ar'],
        }

        for codigo, palabras_clave in companias.items():
            if any(clave in texto_min for clave in palabras_clave):
                return codigo

        # Si no coincide con ninguna compañía conocida
        return 'DESCONOCIDA'

    def extraer_siniestro(self):
        # Lista editable con abreviaturas y variaciones
        variantes_siniestro = ["siniestro", "sin", "sini", "stro", "stros"]

        patrones_siniestro = []

        for variante in variantes_siniestro:
            # Variante seguida de "N" con símbolos intermedios (0-4 símbolos) y espacios
            patrones_siniestro.append(
                rf"(?i){variante}\s*N[^a-zA-Z0-9]{{0,4}}\s*(\d{{6,}})"
            )

            # "N" seguido de variante, con símbolos en el medio
            patrones_siniestro.append(
                rf"(?i)N[^a-zA-Z0-9]{{0,4}}\s*{variante}\s*(\d{{6,}})"
            )

            # Variante sola seguida directamente del número
            patrones_siniestro.append(
                rf"(?i){variante}\s*[:\-]?\s*(\d{{6,}})"
            )

        for patron in patrones_siniestro:
            resultado_siniestro = re.search(patron, self.texto)
            if resultado_siniestro:
                siniestro = resultado_siniestro.group(1)
                siniestro = re.sub(r'[\\/:\*\?"<>\|]', '_', siniestro).strip()
                return siniestro

        return None





    def extraer_poliza(self):
        # Patrón para buscar un número de póliza con guiones o espacios separadores
        patron_poliza = r"(?i)P[óo]liza\s*[:=/]?\s*(\d+(?:[\s\/-]\d+)*)"

        # Buscar el número de póliza en el texto
        resultado_poliza = re.search(patron_poliza, self.texto)

        if resultado_poliza:
            poliza = resultado_poliza.group(1)
            # Remover caracteres no permitidos en nombres de archivos
            poliza = re.sub(r'[\\:\*\?"<>\|]', '_', poliza)
            # Eliminar barras
            poliza = poliza.replace("/","-")
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
        print(f"SETEO DE DATOS CON LOS SIGUIENTES PARAMETROS: DATO: {dato} VALOR: {valor}")
        if valor is not None:
            setattr(self, dato.lower(), valor)
            print(f"el nuevo dato {dato} es {valor}")
        else:
            print(f"\n\n EL VALOR DEL -{dato}- ES {valor} y por lo tanto NO SE ALMACENA \n\n")


    def ajustar_brillo_contraste_y_guardar(self, ruta_imagen):
        """Ajusta el brillo y contraste de la imagen y la guarda."""
        imagen = cv2.imread(ruta_imagen)
        # Realiza ajuste de brillo y contraste según tus necesidades
        # Por ejemplo, aquí se aumenta el brillo y el contraste
        alpha = 1.05  # factor de contraste
        beta = 10   # factor de brillo
        imagen_ajustada = cv2.convertScaleAbs(imagen, alpha=alpha, beta=beta)

        if imagen_ajustada is not None:
            # Aplica la corrección gamma
            gamma = 1.2
            imagen_ajustada = np.power(imagen_ajustada / 255.0, gamma) * 255.0

            # Convierte la imagen a tipo uint8
            imagen_ajustada = np.uint8(imagen_ajustada)
            # Guarda la imagen ajustada
            cv2.imwrite(ruta_imagen, imagen_ajustada)
        else:
            print("No se pudo ajustar la imagen. La imagen es None.")

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
