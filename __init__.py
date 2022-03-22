import axipy
from PySide2.QtGui import QIcon
from axipy import AxiomaPlugin

from .ui.DlgFormCombine import dlgFromCombine
from .ui.docWidget import DelDocWidget, AxiDocWidget, addDoc, existDocWidget


class Plugin(AxiomaPlugin):
    def load(self):
        self.__form_merge=None
        self.__merge_doc=None
        local_file_icon_correct=self.local_file("ui/icons",'merge.png')
        self.__action = self.create_action('Объединение данных',
                                           icon=local_file_icon_correct, on_click=self.__run_merge)
        position = self.get_position('Дополнительно', 'Инструменты')
        position.add(self.__action,size=2)
    def unload(self):
        self.__action.remove()
        self.__removeWidget()
    def __removeWidget(self):
        if self.__merge_doc is None:
            return
        DelDocWidget(axipy.app.mainwindow.qt_object(),self.__merge_doc)
        self.__form_merge=None
        self.__merge_doc=None
    def __run_merge(self):
        mainwindowAxi=axipy.app.mainwindow.qt_object()
        if self.__form_merge is None:
            self.__form_merge=dlgFromCombine()
        if self.__merge_doc is None:
            self.__merge_doc=AxiDocWidget(self.__form_merge.widget,"MergerData","Объединение данных",QIcon(),mainwindowAxi)
            addDoc(mainwindowAxi,self.__merge_doc)
        else:
            isExist=existDocWidget(axipy.app.mainwindow.qt_object(),self.__merge_doc)
            self.__merge_doc.setVisible(True)
            self.__merge_doc.setFocus()
            self.__merge_doc.raise_()