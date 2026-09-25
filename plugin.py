from qgis.PyQt.QtWidgets import QAction, QInputDialog
from qgis.core import QgsProject, QgsFeature, QgsGeometry
from qgis.gui import QgsMapToolEmitPoint

class AddTerminalTool(QgsMapToolEmitPoint):
    def __init__(self, iface, plugin):
        super().__init__(iface.mapCanvas())
        self.iface = iface
        self.plugin = plugin

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        term_layer = self.plugin.term_layer
        wire_layer = self.plugin.wire_layer

        terminal_size = 1
        for wire in wire_layer.getFeatures():
            try:
                if wire.geometry().contains(QgsGeometry.fromPointXY(point)):
                    terminal_size = int(float(str(wire["Size"])))
                    break
            except:
                pass

        terminal_name = f"T{self.plugin.next_terminal_no}"
        start_count = self.plugin.current_count
        end_count = start_count + terminal_size - 1

        feat = QgsFeature(term_layer.fields())
        feat.setGeometry(QgsGeometry.fromPointXY(point))
        feat['TRM_NAME'] = terminal_name
        feat['TRM_SIZE'] = terminal_size
        feat['START_COUN'] = start_count
        feat['TRM_COUNTS'] = f'{start_count}-{end_count}'

        term_layer.startEditing()
        term_layer.addFeature(feat)
        term_layer.commitChanges()

        structure_layers = QgsProject.instance().mapLayersByName('STRUCTURE')
        if structure_layers:
            structure_layer = structure_layers[0]
            fp = QgsFeature(structure_layer.fields())
            fp.setGeometry(QgsGeometry.fromPointXY(point))
            try:
                fp['Type'] = 'FP'
            except:
                pass
            try:
                fp['Size'] = '11"X11"X16"'
            except:
                pass
            structure_layer.startEditing()
            structure_layer.addFeature(fp)
            structure_layer.commitChanges()

        self.plugin.current_count = end_count + 1
        self.plugin.next_terminal_no += 1

class TerminalAutoPlugin:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.action = QAction('Auto Terminal Placement', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        self.term_layer = QgsProject.instance().mapLayersByName('TERMINAL')[0]
        self.wire_layer = QgsProject.instance().mapLayersByName('Wirelimit')[0]
        self.current_count, ok = QInputDialog.getInt(None, 'Starting Count', 'Enter starting count', 1)
        if not ok:
            return
        self.next_terminal_no = self.term_layer.featureCount() + 1
        self.tool = AddTerminalTool(self.iface, self)
        self.iface.mapCanvas().setMapTool(self.tool)
