from src.scripts.imports import *

class HorizontalSeparator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = '#4b4b4b'
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setStyleSheet(f'background-color: {self.color}; color: {self.color}')
        self.setFixedHeight(2)  # Set the height to 1 pixel

    def sizeHint(self):
        return QSize(2, 2)

    def minimumSizeHint(self):
        return QSize(2, 2)

class InspectorWindow(QWidget):
    def __init__(self, item: QGraphicsItem, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Inspector')
        self.setWindowIcon(QIcon('ui/Main Logos/MPVIEWER_logo.png'))
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setFixedWidth(300)

        self.item = item
        self.setLayout(QVBoxLayout())

        self.createUI()
        self.show()

    def createUI(self):
        self.label1 = QLabel(f'Type: {self.item.toolTip()}')
        self.label1.setStyleSheet('font-size: 30px;')

        self.label2 = QLabel(f'''Position: {int(self.item.sceneBoundingRect().x())}, {int(self.item.sceneBoundingRect().y())}
Width: {int(self.item.boundingRect().width())}
Height: {int(self.item.boundingRect().height())}
Scale: {int(self.item.scale() * 100)}%
Rotation: {int(self.item.rotation())}°
''')
        self.label2.setStyleSheet('font-size: 16px;')

        copy_btn = QPushButton('Copy Item Attributes')
        copy_btn.clicked.connect(self.copyAttr)

        self.layout().addWidget(self.label1)
        self.layout().addWidget(HorizontalSeparator())
        self.layout().addWidget(self.label2)
        self.layout().addWidget(HorizontalSeparator())
        self.layout().addWidget(copy_btn)

    def copyAttr(self):
        clipboard = QApplication.clipboard()
        label1_text = self.label1.text()
        label2_text = self.label2.text()
        combined_text = f"{label1_text}\n{label2_text}"
        clipboard.setText(combined_text)

    def closeEvent(self, event):
        self.item.scene().views()[0].setDragMode(QGraphicsView.ScrollHandDrag)
        self.item.scene().views()[0].setCurrentAction('')

        event.accept()

class InspectorTool:
    def __init__(self, scene, view):
        self.scene = scene
        self.view = view

        self.window = None

    def on_press(self, event):
        item = self.scene.itemAt(self.view.mapToScene(event.pos()), self.view.transform())

        if item:
            self.window = InspectorWindow(item)
            # self.window.move(self.scene.parentWindow().pos())
            self.view.setDragMode(QGraphicsView.NoDrag)


    def on_release(self, event):
        pass
