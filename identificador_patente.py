from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLineEdit, QLabel, QFileDialog, QMessageBox, QGraphicsView, QGraphicsScene
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QTransform
from PyQt5.QtCore import Qt, QRectF
from pdf2image import convert_from_path
from PyQt5.QtGui import QImage
import sys
from PIL import Image
import fitz

class PatenteSelector(QWidget):
    def __init__(self, pdf_path, candidatas):
        super().__init__()
        self.setWindowTitle("Seleccionar Patente")
        self.setGeometry(100, 100, 1000, 700)
        self.resultado = None

        self.initUI(pdf_path, candidatas)

    def render_pdf_pagina(self, pagina_pdf):
        doc = fitz.open(pagina_pdf)
        page = doc.load_page(0)  # primera página
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom, mejora calidad
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img

    def pil2qimage(self, pil_image):
        pil_image = pil_image.convert("RGB")
        data = pil_image.tobytes("raw", "RGB")
        return QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)

    def initUI(self, pdf_path, candidatas):
        layout = QHBoxLayout(self)

        # LADO IZQUIERDO: opciones
        lado_izq = QVBoxLayout()

        self.lista = QListWidget()
        self.lista.addItems(candidatas)
        lado_izq.addWidget(QLabel("Patentes candidatas:"))
        lado_izq.addWidget(self.lista)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Ingrese una patente manualmente...")
        lado_izq.addWidget(self.entry)

        botones = QHBoxLayout()
        btn_aceptar = QPushButton("Aceptar")
        btn_ilegible = QPushButton("Marcar como ILEGIBLE")
        btn_aceptar.clicked.connect(self.seleccionar)
        btn_ilegible.clicked.connect(self.marcar_ilegible)
        botones.addWidget(btn_aceptar)
        botones.addWidget(btn_ilegible)

        lado_izq.addLayout(botones)
        layout.addLayout(lado_izq, 1)

        # LADO DERECHO: imagen
        lado_der = QVBoxLayout()
        self.viewer = QGraphicsView()
        self.viewer.setDragMode(QGraphicsView.ScrollHandDrag)
        lado_der.addWidget(QLabel("Vista previa del PDF"))
        lado_der.addWidget(self.viewer, 1)
        layout.addLayout(lado_der, 2)

        self.load_pdf_image(pdf_path)

    def load_pdf_image(self, pdf_path):
        try:
            imagen = self.render_pdf_pagina(pdf_path)
            qt_image = self.pil2qimage(imagen)

            pixmap = QPixmap.fromImage(qt_image)
            scene = QGraphicsScene(self.viewer)
            scene.clear()
            scene.setSceneRect(QRectF(pixmap.rect()))

            scene.addPixmap(pixmap)
            self.viewer.setScene(scene)

            self.viewer.resetTransform()  # Reinicia cualquier zoom anterior
            self.viewer.setRenderHint(QPainter.SmoothPixmapTransform)
            self.viewer.fitInView(QRectF(pixmap.rect()), Qt.KeepAspectRatio) #Usamos pixmap.rect() directamente!

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el PDF:\n{e}")


    def seleccionar(self):
        seleccion = self.lista.currentItem()
        if seleccion:
            self.resultado = seleccion.text()
        else:
            texto = self.entry.text().strip()
            if texto:
                self.resultado = texto
            else:
                QMessageBox.warning(self, "Advertencia", "Seleccione una patente o escriba una.")
                return
        self.close()

    def marcar_ilegible(self):
        self.resultado = "ILEGIBLE"
        self.close()

    def obtener_resultado(self):
        return self.resultado

# USO
if __name__ == "__main__":
    app = QApplication(sys.argv)
    archivo_pdf, _ = QFileDialog.getOpenFileName(None, "Seleccionar PDF", "", "Archivos PDF (*.pdf)")
    if archivo_pdf:
        selector = PatenteSelector(archivo_pdf, ["ABC123", "DEF456", "GHI789"])
        selector.show()
        app.exec_()
        print("Resultado seleccionado:", selector.obtener_resultado())



from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PIL import ImageQt
import sys

def mostrar_ventana_seleccion(imagen_pil):
    class VentanaIngreso(QWidget):
        def __init__(self, imagen):
            super().__init__()
            self.setWindowTitle("Ingreso de patente manual")
            self.resultado = None

            layout = QVBoxLayout()
            self.imagen_label = QLabel()
            qt_image = ImageQt.ImageQt(imagen)
            pixmap = QPixmap.fromImage(QImage(qt_image))
            self.imagen_label.setPixmap(pixmap.scaled(600, 400, Qt.KeepAspectRatio))
            layout.addWidget(self.imagen_label)

            self.entrada = QLineEdit()
            self.entrada.setPlaceholderText("Ingresar patente detectada manualmente...")
            layout.addWidget(self.entrada)

            self.boton = QPushButton("Confirmar")
            self.boton.clicked.connect(self.confirmar)
            layout.addWidget(self.boton)

            self.setLayout(layout)

        def confirmar(self):
            self.resultado = self.entrada.text().strip()
            self.close()

    app = QApplication.instance()
    creada = False
    if not app:
        app = QApplication(sys.argv)
        creada = True
    ventana = VentanaIngreso(imagen_pil)
    ventana.exec_() if hasattr(ventana, 'exec_') else ventana.show()
    app.exec_() if creada else None
    return ventana.resultado if ventana.resultado else "ILEGIBLE"
