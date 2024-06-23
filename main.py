from src.scripts.imports import *
from src.scripts.styles import *
from src.framework.graphics_framework import *

class MPVIEWER(QMainWindow):
    def __init__(self):
        super(MPVIEWER, self).__init__()
        # Creating the main window
        self.setWindowIcon(QIcon('ui/Main Logos/MPVIEWER_logo.png'))
        self.setWindowTitle('MPVIEWER')
        self.setGeometry(0, 0, 1500, 800)
        self.setAcceptDrops(True)

        self.createGUI()
        self.createMenu()

        self.show()

    def createGUI(self):
        self.grScene = CustomGraphicsScene()
        self.grScene.setParentWindow(self)
        self.grView = CustomGraphicsView()
        self.grView.setScene(self.grScene)

        self.setCentralWidget(self.grView)

    def createMenu(self):
        self.menu = QMenuBar()
        self.setMenuBar(self.menu)
        file_menu = self.menu.addMenu('&File')
        view_menu = self.menu.addMenu('&View')

        # Create file actions
        open_action = QAction('Open', self)
        open_action.triggered.connect(self.grScene.manager.load)

        # Create view actions
        center_on_content_action = QAction('Center On Content', self)
        center_on_content_action.triggered.connect(lambda: self.grView.fitInView(self.grScene.itemsBoundingRect(), Qt.KeepAspectRatio))

        # Add actions
        file_menu.addAction(open_action)

        view_menu.addAction(center_on_content_action)


if __name__ == '__main__':
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    if sys.platform == 'darwin':
        app.setStyleSheet(windows_style)

    else:
        app.setStyleSheet(windows_style)

    window = MPVIEWER()

    sys.exit(app.exec_())
