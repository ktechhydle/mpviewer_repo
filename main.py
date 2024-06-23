from src.scripts.imports import *
from src.scripts.styles import *
from src.framework.graphics_framework import *

class MPVIEWER(QMainWindow):
    def __init__(self):
        super(MPVIEWER, self).__init__()
        # Creating the main window
        self.setWindowIcon(QIcon('ui/Main Logos/MPRUN_logoV3.png'))
        self.setGeometry(0, 0, 1500, 800)
        self.setAcceptDrops(True)

        self.createGUI()
        self.createMenu()

        self.show()

    def createGUI(self):
        self.grScene = CustomGraphicsScene()
        self.grScene.setParentWindow(self)
        self.grView = CustomGraphicsView(QSpinBox(self))
        self.grView.setScene(self.grScene)

        self.setCentralWidget(self.grView)

    def createMenu(self):
        self.menu = QMenuBar()
        self.setMenuBar(self.menu)
        file_menu = self.menu.addMenu('&File')

        # Create actions
        open_action = QAction('Open', self)
        open_action.triggered.connect(self.grScene.manager.load)

        # Add actions
        file_menu.addAction(open_action)



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
