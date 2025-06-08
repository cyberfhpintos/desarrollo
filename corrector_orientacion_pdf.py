#!/usr/bin/env python3.12
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# Configurar pytesseract en Windows (en Linux, suele estar en /usr/bin/tesseract)
if os.name == 'nt':
    pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def select_folder():
    """Selecciona la carpeta y pregunta si incluir subdirectorios."""
    root = tk.Tk()
    root.withdraw()  # Ocultamos la ventana principal
    
    # Selección de la carpeta
    folder_selected = filedialog.askdirectory(title="Seleccione la carpeta con los PDFs")
    
    if not folder_selected:
        return None, None

    # Preguntar si incluir subdirectorios
    include_subdirs = messagebox.askyesno("Incluir subdirectorios", "¿Desea incluir subdirectorios en la búsqueda de PDFs?")

    return folder_selected, include_subdirs


def detect_orientation(image):
    """Detecta la orientación del texto en una imagen."""
    try:
        osd = pytesseract.image_to_osd(image)
        rotate_angle = int(osd.split('Rotate: ')[1].split('\n')[0])
        return rotate_angle
    except pytesseract.TesseractError as e:
        print(f"Error detectando orientación: {e}")
        return 0
    except Exception as e:
        print(f"Otro error en OCR: {e}")
        return 0


def correct_pdf_orientation(pdf_path):
    """Corrige la orientación de un PDF si es necesario y sobrescribe el archivo original."""
    doc = fitz.open(pdf_path)
    corrected = False
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))  # Aumentamos la resolución para OCR
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        if img.width < 50 or img.height < 50:
            print(f"Página {page_num + 1} ignorada: imagen demasiado pequeña para OCR.")
            continue
        
        rotation = detect_orientation(img)
        
        if rotation in [90, 180, 270]:
            corrected_rotation = (page.rotation + rotation) % 360
            page.set_rotation(corrected_rotation)
            corrected = True
    
    if corrected:
        temp_path = pdf_path + ".tmp"
        doc.save(temp_path)
        doc.close()
        os.replace(temp_path, pdf_path)
        print(f"Orientación corregida: {pdf_path}")
    else:
        doc.close()


def process_pdfs_in_folder(folder, include_subdirs):
    """Procesa todos los PDFs en la carpeta seleccionada."""
    if not folder:
        print("No se seleccionó ninguna carpeta.")
        return
    
    # Si se debe incluir subdirectorios, usamos os.walk
    if include_subdirs:
        for root_dir, _, files in os.walk(folder):
            for filename in files:
                if filename.lower().endswith(".pdf"):
                    pdf_path = os.path.join(root_dir, filename)
                    correct_pdf_orientation(pdf_path)
    else:
        for filename in os.listdir(folder):
            if filename.lower().endswith(".pdf"):
                pdf_path = os.path.join(folder, filename)
                correct_pdf_orientation(pdf_path)


if __name__ == "__main__":
    folder, include_subdirs = select_folder()
    
    if folder is None:
        print("No se seleccionó ninguna carpeta.")
    else:
        process_pdfs_in_folder(folder, include_subdirs)
        print("Proceso completado.")
