import os
from pathlib import Path

import axipy
from PySide2 import QtWidgets
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QWidget, QFileDialog, QDialog
from axipy import CoordSystem

from ..tool.combineData import getFilesInfFolder, workerCopy, csMi, csMiFromGdal


class dlgFromCombine(QWidget):
    __dlgSelectSourceFolder=None
    __dlgOutCombineFile=None
    __list_source_file=None
    def __init__(self,parent=None):
        super().__init__()
        self.__parent=parent
        self.__dlg_cs=None
        self.__out_cs=CoordSystem.from_prj('NonEarth 0, \'m\'')
        self.load_ui('dlgFormMergedData.ui')
        self.__ui.pb_run.clicked.connect(self.__run)

        self.__ui.pb_cancel.clicked.connect(self.__process_cancel)
        #self.__ui.pb_test.clicked.connect(self.__cancel)
        self.__ui.pb_select_folder.clicked.connect(self.__select_source_folder)
        self.__ui.pb_select_out_file.clicked.connect(self.__select_out_file)
        self.__ui.pn_select_out_prj.clicked.connect(self.__change_coord_sys)
        self.__ui.pr_bar.setValue(0)
        self.__ui.label_out_prj.setText(self.__out_cs.name)
        self.__ui.ch_prj_first.stateChanged.connect(self.__change_stata_use_cs_file)
        self.__workerCopy=workerCopy()
        self.__workerCopy.progressMade.connect(self.update_progress)
        self.__workerCopy.finished.connect(self.on_finished)

        #self.__ui.pb_cancel.setEnabled(True)
    def load_ui(self,name_resource):
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__),name_resource)
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.__ui  = loader.load(ui_file,self.__parent)
        ui_file.close()
    def update_progress(self, n_done):
        self.__ui.pr_bar.setValue(n_done)
    def __process_cancel(self):
        #print("Test")
        self.__workerCopy.terminate()
    def __cancel(self):
        #self.worker.cancel(True)
        print("Cancel")
        self.__workerCopy.terminate()

    def on_finished(self, done):
        self.__ui.pb_run.setEnabled(True)
        self.__ui.pb_cancel.setEnabled(False)
        self.__ui.pr_bar.setValue(0)
        '''
        QtWidgets.QMessageBox.information(
            self, "Picasso: ToRaw", "Conversion complete."
        )
        '''
    def __select_source_folder(self):
        if self.__dlgSelectSourceFolder is None:
            self.__dlgSelectSourceFolder=QFileDialog()
            base_path=str(Path.home())
        else:
            base_path=self.__ui.ln_source_folder.text()
        sel_folder=self.__dlgSelectSourceFolder.getExistingDirectory(self.__ui, "Выбор директории c исходными данными", base_path)
        if not (sel_folder==''):
            self.__ui.ln_source_folder.setText(sel_folder)
            form_filter=self.__ui.cmb_format_source.currentText()
            self.__list_source_file=getFilesInfFolder(sel_folder,form_filter.lower(),True)

        else:
            pass
        self.__setRun()
    def __change_coord_sys(self):
        if self.__dlg_cs is None:
            self.__dlg_cs=axipy.gui.ChooseCoordSystemDialog(self.__out_cs)
        if self.__dlg_cs.exec() == QDialog.Accepted:
            self.__out_cs=self.__dlg_cs.chosenCoordSystem()
            self.__ui.label_out_prj.setText(self.__out_cs.name)
    def __change_stata_use_cs_file(self):
        self.__is_cs_from_file=self.__ui.ch_prj_first.isChecked()
        if self.__is_cs_from_file:
            if len(self.__list_source_file)>0:
                self.__out_cs=csMiFromGdal(self.__list_source_file[0])
                self.__ui.label_out_prj.setText(self.__out_cs.name)

    def __select_out_file(self):
        str_filter='GeoPackeg (*.gpkg);;MapInfo (*.tab)'
        if self.__ui.cmb_format_source.currentIndex()==0:
            str_filter='GeoPackeg (*.gpkg)'

        if self.__dlgOutCombineFile is None:
            self.__dlgOutCombineFile=QFileDialog()
            name_save_file=self.__dlgOutCombineFile.getSaveFileName(self.__ui,"Сохранить в ",str(Path.home()),str_filter)
        else:
            name_save_file=self.__dlgOutCombineFile.getSaveFileName(self.__ui,caption="Сохранить в ",filter=str_filter)
        if name_save_file != ('', ''):
            self.__ui.ln_out_file.setText(name_save_file[0])
        self.__setRun()
    def __setRun(self):
        ''' Проверяем достаточность условий для выполнения'''
        isSourceFolderValid=False
        if len(self.__ui.ln_source_folder.text())>0 and  os.path.isdir(self.__ui.ln_source_folder.text()):
            isSourceFolderValid=True
        isOutFileValid=False
        file_out=self.__ui.ln_out_file.text()

        path_out=str(Path(self.__ui.ln_out_file.text()).parent)
        if len(file_out)>0 and os.path.isdir(path_out):
            isOutFileValid=True
        isStatusRun=isOutFileValid and isSourceFolderValid
        if self.__list_source_file is None or len(self.__list_source_file)==0:
            isStatusRun=False
        self.__ui.pb_run.setEnabled(isStatusRun)
        self.__ui.ch_prj_first.setEnabled(isStatusRun)
    @property
    def widget(self):
        return self.__ui
    def __run(self):
        isNonEarth=self.__out_cs.non_earth
        path_source_folder=self.__ui.ln_source_folder.text()
        ext_file=Path()
        form_filter=self.__ui.cmb_format_source.currentText()
        list_files=getFilesInfFolder(path_source_folder,form_filter.lower(),True)
        if len(list_files)>0:
            cs_out={}
            cs_out['format']='wkt'
            cs_out['cs']="LOCAL_CS[\"NonEarth_Meter\",UNIT[\"METER\",1]]"
            self.__ui.pr_bar.setRange(0,len(list_files))
            self.__workerCopy.setParams(list_files,cs_out,"demo",self.__ui.ln_out_file.text())
            self.__ui.pb_run.setEnabled(False)
            self.__ui.pb_cancel.setEnabled(True)
            self.__workerCopy.start()
            #self.__ui.pb_run.setEnabled(True)
            #self.__ui.pb_cancel.setEnabled(False)
        jkl=0
    def __cancel(self):
        pass