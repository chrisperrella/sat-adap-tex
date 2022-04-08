import os, weakref, sys
from functools import partial
from pathlib import Path
from PySide2 import QtCore, QtGui, QtWidgets, QtSvg

import sd
from sd.api.apiexception import APIException
from sd.api.sdvaluestring import SDValueString

def icon_svg(name, size):
    currentDir = os.path.dirname(__file__)
    icon_path = os.path.abspath(os.path.join(currentDir, name + '.svg'))
    icon_path_hover = os.path.abspath(os.path.join(currentDir, name + '_hover.svg'))
    
    if not Path(icon_path_hover).is_file():
        icon_path_hover = icon_path    

    svgRenderer = QtSvg.QSvgRenderer(icon_path)
    svgRenderer_hover = QtSvg.QSvgRenderer(icon_path_hover)
    if svgRenderer.isValid():
        pixmap = QtGui.QPixmap(QtCore.QSize(size, size))
        pixmap_hover = QtGui.QPixmap(QtCore.QSize(size, size))

        if not pixmap.isNull():
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            svgRenderer.render(painter)
            painter.end()

            pixmap_hover.fill(QtCore.Qt.transparent)
            painter_hover = QtGui.QPainter(pixmap_hover)
            svgRenderer_hover.render(painter_hover)
            painter_hover.end()            

        icon = QtGui.QIcon()
        icon.addPixmap(pixmap)
        icon.addPixmap(pixmap_hover, QtGui.QIcon.Active)
        return icon

    return None

class AdaptiveTexturingShelf(QtWidgets.QToolBar):
    __toolbarList = {}

    def __init__(self, graphViewID, ui_mrg):
        super(AdaptiveTexturingShelf, self).__init__(parent=ui_mrg.getMainWindow())

        sys.path.append(Path(Path(__file__).parent.absolute(), 'satadap').as_posix())

        self.__graphViewID = graphViewID
        self.__uiMgr = ui_mrg

        act = self.addAction(icon_svg("generate_hex", 64), "Generate Hex")
        act.setToolTip(self.tr("Generate Hex"))
        act.triggered.connect(self.__onGenerateHex)

        self.__toolbarList[graphViewID] = weakref.ref(self)
        self.destroyed.connect(partial(AdaptiveTexturingShelf.__onToolbarDeleted, graphViewID=graphViewID))

    def tooltip(self):
        return self.tr("Adaptive Texturing")
            
    def __onGenerateHex(self):
        graph = self.__uiMgr.getCurrentGraph()
        metadata = graph.getMetadataDict()
        try:
            material_id_value = metadata.getPropertyFromId("material_id").getDefaultValue().get()
        except APIException:
            from satadap import util
            material_id_value = SDValueString.sNew(util.random_hex_color())
            metadata.setPropertyValueFromId("material_id", material_id_value)       

    @classmethod
    def __onToolbarDeleted(cls, graphViewID):
        del cls.__toolbarList[graphViewID]

    @classmethod
    def removeAllToolbars(cls):
        for toolbar in cls.__toolbarList.values():
            if toolbar():
                toolbar().deleteLater()


def onNewGraphViewCreated(graphViewID, ui_mrg):
    toolbar = AdaptiveTexturingShelf(graphViewID, ui_mrg)
    ui_mrg.addToolbarToGraphView(
        graphViewID,
        toolbar,
        icon = icon_svg("adaptive_texturing", 64),
        tooltip = toolbar.tooltip())

graphViewCreatedCallbackID = 0

def initializeSDPlugin():
    ctx = sd.getContext()
    app = ctx.getSDApplication()
    ui_mrg = app.getQtForPythonUIMgr()

    if ui_mrg:
        global graphViewCreatedCallbackID
        graphViewCreatedCallbackID = ui_mrg.registerGraphViewCreatedCallback(
            partial(onNewGraphViewCreated, ui_mrg=ui_mrg))


def uninitializeSDPlugin():
    ctx = sd.getContext()
    app = ctx.getSDApplication()
    ui_mrg = app.getQtForPythonUIMgr()

    if ui_mrg:
        global graphViewCreatedCallbackID
        ui_mrg.unregisterCallback(graphViewCreatedCallbackID)
        AdaptiveTexturingShelf.removeAllToolbars()