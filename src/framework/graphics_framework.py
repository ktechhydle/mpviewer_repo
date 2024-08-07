from src.scripts.imports import *
from src.framework.custom_classes import *
from src.framework.tools import *

class CustomViewport(QOpenGLWidget):
    def __init__(self):
        super().__init__()

        format = QSurfaceFormat()
        format.setSamples(4)
        format.setRenderableType(QSurfaceFormat.OpenGL)
        self.setFormat(format)

class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__()
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # tools
        self.inspectorTool = InspectorTool(scene, self)

        # actions
        self.current_action = None

        # Add methods for zooming
        self.zoomInFactor = 1.25
        self.zoomClamp = True
        self.zoom = 20
        self.zoomStep = 1
        self.zoomRange = [0, 100]

    def wheelEvent(self, event):
        try:
            self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

            # Calculate zoom Factor
            zoomOutFactor = 1 / self.zoomInFactor

            # Calculate zoom
            if event.angleDelta().y() > 0:
                zoomFactor = self.zoomInFactor
                self.zoom += self.zoomStep
            else:
                zoomFactor = zoomOutFactor
                self.zoom -= self.zoomStep

            # Deal with clamping!
            clamped = False
            if self.zoom < self.zoomRange[0]: self.zoom, clamped = self.zoomRange[0], True
            if self.zoom > self.zoomRange[1]: self.zoom, clamped = self.zoomRange[1], True

            if not clamped or self.zoomClamp is False:
                self.scale(zoomFactor, zoomFactor)

        except Exception:
            pass

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if self.currentAction() == 'inspector':
            self.inspectorTool.on_press(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        self.showToolTip(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

        if self.currentAction() == 'inspector':
            self.inspectorTool.on_release(event)

    def mouseDoubleClickEvent(self, event):
        pass

    def showToolTip(self, event):
        p = self.mapToGlobal(event.pos())
        p.setY(p.y())
        p.setX(p.x() + 10)

        QToolTip.showText(p, f'''x: {int(self.mapToScene(event.pos()).x())}
y: {int(self.mapToScene(event.pos()).y())}''')

    def currentAction(self):
        return self.current_action

    def setCurrentAction(self, action):
        self.current_action = action

class CustomGraphicsScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.file_name = None
        self.pWindow = None

        width = 64000
        height = 64000
        self.setSceneRect(-width // 2, -height // 2, width, height)
        self.setBackgroundBrush(QBrush(QColor('#606060')))

        # File
        self.manager = SceneManager(self)
    def setParentWindow(self, parent: QMainWindow):
        self.pWindow = parent

    def parentWindow(self):
        return self.pWindow

class SceneManager:
    def __init__(self, scene):
        self.scene = scene
        self.filename = 'Untitled'
        self.parent = None
        self.repair_needed = False

    def load(self):
        try:
            filename, _ = QFileDialog.getOpenFileName(self.scene.parentWindow(), 'Open File', '',
                                                      'MPRUN files (*.mp)')

            if filename:
                self.scene.clear()

                with open(filename, 'rb') as f:
                    items_data = pickle.load(f)
                    self.deserialize_items(items_data)

                    self.filename = filename
                    self.scene.parentWindow().setWindowTitle(f'{os.path.basename(self.filename)} - MPVIEWER')

                    if self.repair_needed:
                        # Display a confirmation dialog
                        confirmation_dialog = QMessageBox(self.scene.parentWindow())
                        confirmation_dialog.setWindowTitle('Open Document Error')
                        confirmation_dialog.setIcon(QMessageBox.Warning)
                        confirmation_dialog.setText(
                            f"The document has file directories that could not be found. Do you want to do a file repair?")
                        confirmation_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                        confirmation_dialog.setDefaultButton(QMessageBox.Yes)

                        # Get the result of the confirmation dialog
                        result = confirmation_dialog.exec_()

                        if result == QMessageBox.Yes:
                            self.repair_file()

        except Exception as e:
            QMessageBox.critical(self.scene.parentWindow,
                                 'Open File Error',
                                 'The document you are attempting to open has been corrupted. '
                                 'Please open a different document, or repair any changes.')

            print(e)

    def deserialize_items(self, items_data):
        # Handle metadata
        metadata = items_data.pop(0)

        for item_data in items_data:
            item = None
            if item_data['type'] == 'CanvasItem':
                item = self.deserialize_canvas(item_data)
            elif item_data['type'] == 'CustomTextItem':
                item = self.deserialize_custom_text_item(item_data)
            elif item_data['type'] == 'CustomPathItem':
                item = self.deserialize_custom_path_item(item_data)
            elif item_data['type'] == 'CustomGraphicsItemGroup':
                item = self.deserialize_custom_group_item(item_data)
            elif item_data['type'] == 'LeaderLineItem':
                item = self.deserialize_leader_line_item(item_data)
            elif item_data['type'] == 'CustomSvgItem':
                item = self.deserialize_custom_svg_item(item_data)
            elif item_data['type'] == 'CustomPixmapItem':
                item = self.deserialize_custom_pixmap_item(item_data)

            if item is not None:
                self.scene.addItem(item)

    def deserialize_color(self, color):
        return QColor(color['red'], color['green'], color['blue'], color['alpha'])

    def deserialize_pen(self, data):
        pen = QPen()
        pen.setWidth(data['width'])
        pen.setColor(self.deserialize_color(data['color']))
        pen.setStyle(data['style'])
        pen.setCapStyle(data['capstyle'])
        pen.setJoinStyle(data['joinstyle'])
        return pen

    def deserialize_brush(self, data):
        brush = QBrush()
        brush.setColor(self.deserialize_color(data['color']))
        brush.setStyle(data['style'])
        return brush

    def deserialize_font(self, data):
        font = QFont()
        font.setFamily(data['family'])
        font.setPixelSize(data['pointsize'])
        font.setLetterSpacing(QFont.AbsoluteSpacing, data['letterspacing'])
        font.setBold(data['bold'])
        font.setItalic(data['italic'])
        font.setUnderline(data['underline'])
        return font

    def deserialize_transform(self, data):
        transform = QTransform(
            data['m11'], data['m12'], data['m13'],
            data['m21'], data['m22'], data['m23'],
            data['m31'], data['m32'], data['m33']
        )
        return transform

    def deserialize_point(self, data):
        return QPointF(data['x'], data['y'])

    def deserialize_canvas(self, data):
        rect = QRectF(*data['rect'])
        canvas = CanvasItem(rect, data['name'])
        canvas.setPos(data['x'], data['y'])
        return canvas

    def deserialize_custom_text_item(self, data):
        text_item = CustomTextItem(data['text'])
        text_item.setFont(self.deserialize_font(data['font']))
        text_item.setDefaultTextColor(self.deserialize_color(data['color']))
        text_item.locked = data['locked']

        for attr in data['attr']:
            text_item.setTransformOriginPoint(self.deserialize_point(attr['transformorigin']))
            text_item.setRotation(attr['rotation'])
            text_item.setTransform(self.deserialize_transform(attr['transform']))
            text_item.setScale(attr['scale'])
            text_item.setPos(attr['x'], attr['y'])
            text_item.setToolTip(attr['name'])
            text_item.setZValue(attr['zval'])
            text_item.setVisible(attr['visible'])

        if data.get('markdown', True):
            text_item.toMarkdown()

        return text_item

    def deserialize_custom_path_item(self, data):
        sub_path = QPainterPath()
        for element in data['elements']:
            if element['type'] == 'moveTo':
                sub_path.moveTo(element['x'], element['y'])
            elif element['type'] == 'lineTo':
                sub_path.lineTo(element['x'], element['y'])
            elif element['type'] == 'curveTo':
                sub_path.cubicTo(element['x'],
                                 element['y'],
                                 element['x'],
                                 element['y'],
                                 element['x'],
                                 element['y'])

        path_item = CustomPathItem(sub_path)
        path_item.setPen(self.deserialize_pen(data['pen']))
        path_item.setBrush(self.deserialize_brush(data['brush']))

        for attr in data['attr']:
            path_item.setTransformOriginPoint(self.deserialize_point(attr['transformorigin']))
            path_item.setRotation(attr['rotation'])
            path_item.setTransform(self.deserialize_transform(attr['transform']))
            path_item.setScale(attr['scale'])
            path_item.setPos(attr['x'], attr['y'])
            path_item.setToolTip(attr['name'])
            path_item.setZValue(attr['zval'])
            path_item.setVisible(attr['visible'])

        if data.get('smooth', True):
            path_item.smooth = True

        else:
            path_item.smooth = False

        if data.get('addtext', True):
            path_item.add_text = True
            path_item.setTextAlongPath(data['textalongpath'])
            path_item.setTextAlongPathColor(self.deserialize_color(data['textcolor']))
            path_item.setTextAlongPathFont(self.deserialize_font(data['textfont']))
            path_item.setTextAlongPathSpacingFromPath(data['textspacing'])
            path_item.setTextAlongPathFromBeginning(data['starttextfrombeginning'])

        else:
            path_item.add_text = False

        return path_item

    def deserialize_custom_group_item(self, data):
        group_item = CustomGraphicsItemGroup()

        for attr in data['attr']:
            group_item.setTransformOriginPoint(self.deserialize_point(attr['transformorigin']))
            group_item.setRotation(attr['rotation'])
            group_item.setTransform(self.deserialize_transform(attr['transform']))
            group_item.setScale(attr['scale'])
            group_item.setPos(attr['x'], attr['y'])
            group_item.setToolTip(attr['name'])
            group_item.setZValue(attr['zval'])
            group_item.setVisible(attr['visible'])

        for child_data in data['children']:
            if child_data['type'] == 'CustomTextItem':
                child = self.deserialize_custom_text_item(child_data)
            elif child_data['type'] == 'CustomPathItem':
                child = self.deserialize_custom_path_item(child_data)
            elif child_data['type'] == 'CustomPixmapItem':
                child = self.deserialize_custom_pixmap_item(child_data)
            elif child_data['type'] == 'CustomSvgItem':
                child = self.deserialize_custom_svg_item(child_data)

            group_item.addToGroup(child)

        return group_item

    def deserialize_leader_line_item(self, data):
        sub_path = QPainterPath()
        for element in data['elements']:
            if element['type'] == 'moveTo':
                sub_path.moveTo(element['x'], element['y'])
            elif element['type'] == 'lineTo':
                sub_path.lineTo(element['x'], element['y'])
            elif element['type'] == 'curveTo':
                sub_path.cubicTo(element['x'],
                                 element['y'],
                                 element['x'],
                                 element['y'],
                                 element['x'],
                                 element['y'])

        path_item = LeaderLineItem(sub_path, data['text'])
        path_item.setPen(self.deserialize_pen(data['pen']))
        path_item.setBrush(self.deserialize_brush(data['brush']))
        path_item.text_element.setZValue(data['textzval'])
        path_item.text_element.setDefaultTextColor(self.deserialize_color(data['textcolor']))
        path_item.text_element.setFont(self.deserialize_font(data['textfont']))
        path_item.text_element.setTransformOriginPoint(self.deserialize_point(data['texttransformorigin']))
        path_item.text_element.setTransform(self.deserialize_transform(data['texttransform']))
        path_item.text_element.setScale(data['textscale'])
        path_item.text_element.setPos(data['textposx'], data['textposy'])
        path_item.text_element.setRotation(data['textrotation'])
        path_item.text_element.setVisible(data['textvisible'])

        for attr in data['attr']:
            path_item.setTransformOriginPoint(self.deserialize_point(attr['transformorigin']))
            path_item.setRotation(attr['rotation'])
            path_item.setTransform(self.deserialize_transform(attr['transform']))
            path_item.setScale(attr['scale'])
            path_item.setPos(attr['x'], attr['y'])
            path_item.setToolTip(attr['name'])
            path_item.setZValue(attr['zval'])
            path_item.setVisible(attr['visible'])

        path_item.updatePathEndPoint()

        return path_item

    def deserialize_custom_svg_item(self, data):
        try:
            svg_item = CustomSvgItem()
            svg_item.store_filename(data['filename'])
            svg_item.loadFromData(data['raw_svg_data'])

            for attr in data['attr']:
                svg_item.setTransformOriginPoint(self.deserialize_point(attr['transformorigin']))
                svg_item.setRotation(attr['rotation'])
                svg_item.setTransform(self.deserialize_transform(attr['transform']))
                svg_item.setScale(attr['scale'])
                svg_item.setPos(attr['x'], attr['y'])
                svg_item.setToolTip(attr['name'])
                svg_item.setZValue(attr['zval'])
                svg_item.setVisible(attr['visible'])

            return svg_item

        except Exception as e:
            print(e)

    def deserialize_custom_pixmap_item(self, data):
        pixmap = QPixmap(data['filename'])
        pixmap_item = CustomPixmapItem(pixmap)
        pixmap_item.store_filename(data['filename'])
        pixmap_item.loadFromData(data['data'])

        for attr in data['attr']:
            pixmap_item.setTransformOriginPoint(self.deserialize_point(attr['transformorigin']))
            pixmap_item.setRotation(attr['rotation'])
            pixmap_item.setTransform(self.deserialize_transform(attr['transform']))
            pixmap_item.setScale(attr['scale'])
            pixmap_item.setPos(attr['x'], attr['y'])
            pixmap_item.setToolTip(attr['name'])
            pixmap_item.setZValue(attr['zval'])
            pixmap_item.setVisible(attr['visible'])

        pixmap = pixmap_item.pixmap()
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, "PNG")
        pixmap_data = buffer.data().data()
        pixmap_item.loadFromData(pixmap_data)

        return pixmap_item

    def repair_file(self):
        try:
            with open(self.filename, 'rb') as f:
                items_data = pickle.load(f)

            # Handle metadata
            metadata = items_data.pop(0)
            self.scene.mpversion = metadata.get('mpversion', 'unknown')

            repaired_items_data = []
            removed_files = []
            for item_data in items_data:
                if item_data['type'] in ('CustomPixmapItem', 'CustomSvgItem') and not os.path.exists(
                        item_data['filename']):
                    removed_files.append(item_data['filename'])
                else:
                    repaired_items_data.append(item_data)

            with open(self.filename, 'wb') as f:
                pickle.dump(repaired_items_data, f)

                QMessageBox.information(self.scene.parentWindow, 'File Repair', f"""File repair completed: 
Removed missing items with filenames: {', '.join(removed_files)}""")

        except Exception as e:
            print(f"Error repairing file: {e}")
