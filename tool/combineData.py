import os
import tempfile
from pathlib import Path
import time


import axipy
from PySide2 import QtCore
from axipy import provider_manager, CoordSystem, Table, Point, Polygon, Rect
from numpy.random import randint
from osgeo import ogr, osr
from osgeo.ogr import OFTInteger, OFTReal, OFTString, FieldDefn, Feature
''' Форматирование координат '''
def coordToString(value,typeCsLatLon=True):
    if typeCsLatLon:
        return f'{value:0.6f}'
    else:
        return f'{value:0.2f}'
class DoubleRect:
    __xmin=None
    __ymin=None
    __xmax=None
    __ymax=None
    def __init__(self,cs:CoordSystem,xmin=None,ymin=None,xmax=None,ymaх=None):
        self.__cs=cs
        self.__xmin=xmin
        self.__ymin=ymin
        self.__xmax=xmax
        self.__ymax=ymaх
    @property
    def xmin(self):
        return self.__xmin
    @property
    def ymin(self):
        return self.__ymin
    @property
    def xmax(self):
        return self.__xmax
    @property
    def ymax(self):
        return self.__ymax
    def merge(self,rect:Rect ):
        if rect.xmin<self.__xmin:
            self.__xmin=rect.xmin
        if rect.xmax>self.__xmax:
            self.__xmax=rect.xmax
        if rect.ymin<self.__ymin:
            self.__ymin=rect.ymin
        if rect.ymax>self.__ymax:
            self.__ymax=rect.ymax
    @property
    def coordsystem(self):
        return self.__cs
    def merge(self,rect):
        self.__merge_point(rect.xmin,rect.ymin)
        self.__merge_point(rect.xmin,rect.ymax)
        self.__merge_point(rect.xmax,rect.ymax)
        self.__merge_point(rect.xmax,rect.ymin)
    def mergePoint(self,point:Point):
        if self.__xmin is None or self.__xmax is None or self.__ymin is None or self.__ymax is None:
            self.__xmin=point.x
            self.__ymin=point.y
            self.__xmax=point.x
            self.__ymax=point.y
            return
        if point.x<self.__xmin:
            self.__xmin=point.x
        if point.x>self.__xmax:
            self.__xmax=point.x
        if point.y<self.__ymin:
            self.__ymin=point.y
        if point.y>self.__ymax:
            self.__ymax=point.y
        return
    def __merge_point(self,x,y):
        if self.__xmin is None or x<self.__xmin:
            self.__xmin=x
        if self.__xmax is None or x>self.__xmax:
            self.__xmax=x
        if self.__ymin is None or y<self.__ymin:
            self.__ymin=y
        if self.__ymax is None or y>self.__ymax:
            self.__ymax=y
        return
    def extendOnProcent(self,value_proc_ext):
        self.__xmin,self.__xmax=self.__calcExtend(value_proc_ext,self.__xmin,self.__xmax)
        self.__ymin,self.__ymax=self.__calcExtend(value_proc_ext,self.__ymin,self.__ymax)
    def __calcExtend(self,value_proc_ext,val_min,val_max):
        dx=val_max-val_min
        val_dx_proc=dx/100
        d_proc=val_dx_proc*value_proc_ext
        return val_min-d_proc,val_max+d_proc
    def reproject(self,new_cs):
        poly=Polygon.from_rect(Rect(self.__xmin,self.__ymin,self.__xmax,self.__ymax),self.__cs)
        poly_rep=poly.reproject(new_cs)
        bound=poly_rep.bounds
        return DoubleRect(new_cs,bound.xmin,bound.ymin,bound.xmax,bound.ymax)
    @property
    def clone(self):
        return DoubleRect(self.__cs,self.__xmin,self.__ymin,self.__xmax,self.__ymax)
    @property
    def boundsStr(self):
        str_bounds="Bounds ("+coordToString(self.__xmin,self.__cs.lat_lon)
        str_bounds=str_bounds+","+coordToString(self.__ymin,self.__cs.lat_lon)+") "
        str_bounds=str_bounds+"("+coordToString(self.__xmax,self.__cs.lat_lon)+","

        str_bounds=str_bounds+coordToString(self.__ymax,self.__cs.lat_lon)+")"
        return str_bounds

def createOgrSpatialReference(cs_des):
    name_format=cs_des['format']
    cs_str=cs_des['cs']
    src = osr.SpatialReference()
    if name_format=="mi":
        src.ImportFromMICoordSys(cs_str)
    if name_format=='wkt':
        src.ImportFromWkt(cs_str)
    if name_format=='proj4':
        src.ImportFromProj4(cs_str)
    if name_format=='epsg':
        src.ImportFromEPSG(int(cs_str))
    return src

def getFilesInfFolder(path_folder,extFile,isSubFolder=True)->list:
    out_files=[]
    for path, currentDirectory, files in os.walk(path_folder):
        for file in files:
            full_path_files=os.path.join(path, file)
            #print(os.path.join(path, file))
            extFileCurent=Path(file).suffix
            if extFileCurent.lower()=="."+extFile:
                out_files.append(full_path_files)
        if not isSubFolder:
            break
    return out_files
class AxiPyTable:
    def __init__(self):
        self.__path_temp_tab=None
        self.__axi_table=None
        pass
    def open(self,path_source):
        ext_file=Path(path_source).suffix

        if ext_file.lower()==".mif":
            '''
            temp_folder=tempfile.gettempdir()
            name_file=Path(path_source).name
            self.__path_temp_tab=os.path.join(temp_folder)
            self.__axi_table=provider_manager.MifMidDataProvider.convert_to_tab(path_source,self.__path_temp_tab)
            '''
            return False
        if ext_file.lower()=='.tab':
            self.__axi_table=provider_manager.openfile(path_source)
            if self.__axi_table is None:
                return False
            return True
    @property
    def schema(self):
        if self.__axi_table is not None:
            return self.__axi_table.schema
        return self.__axi_table.schema
    def copyTo(self,table_dest:Table):
        schema_source=table_dest.schema
        features=self.__axi_table.items()
        buffer_ft_out=[]
        bound=DoubleRect(self.__axi_table.coordsystem)
        for ft in features:
            data_feature={}
            for att_name in schema_source.attribute_names:
                data_feature[att_name]=ft[att_name]
            if ft.has_geometry():
                geo_out=ft.geometry
                bound.merge(geo_out.bounds)
            if ft.has_style():
                style_out=ft.style
            ft_out= axipy.da.Feature(data_feature,geometry=geo_out,style=style_out)
            buffer_ft_out.append(ft_out)
        table_dest.insert(buffer_ft_out)
        #table_dest.commit()
        count= len(buffer_ft_out)
        buffer_ft_out=None
        return count,bound
    def close(self):
        if self.__axi_table is not None:
            self.__axi_table.close()
            self.__axi_table=None

class ColumnsDesciptor:
    def __init__(self,name:str,type:str):
        self.__name=name
        self.__type=type
    @property
    def name(self):
        return self.__name
    @property
    def type(self):
        return self.__type
def createOgrField(column_desc:ColumnsDesciptor):
    def_width_string=240
    type_ogr=OFTInteger
    if column_desc.type=='float':
        type_ogr=OFTReal
    if column_desc.type=='Integer':
        type_ogr=OFTInteger
    if column_desc.type == "text" or column_desc.type == "String":
        type_ogr=OFTString
    def_field=FieldDefn(column_desc.name,type_ogr)
    if column_desc.type == "text" or column_desc.type == "String":
        def_field.SetWidth(def_width_string)
    return def_field
def copyFeature(ft_source,out_defLayer):
    ft_out=Feature(out_defLayer)
    count_field=ft_out.GetFieldCount()

    for i in range(count_field):
        name_field=out_defLayer.GetFieldDefn(i).GetName()

        value_field=ft_source.GetField(i)
        ft_out.SetField(name_field,value_field)
    ft_out.SetGeometry(ft_source.GetGeometryRef())
    return ft_out
class OgrDataSource:
    __indexCurentLayer=0
    __layer=None
    def open(self,path_source):
        self.__ds=ogr.Open(path_source)
        if self.__ds is None:
            return False
        return True
    def setCurentIndexLayer(self,id_layer):
        self.__indexCurentLayer=id_layer

    @property
    def LayerColumnsDef(self):
        self.__layer=self.__ds.GetLayerByIndex(self.__indexCurentLayer)
        fts_def = self.__layer.GetLayerDefn()
        list_field_def=[]
        for i in range(fts_def.GetFieldCount()):
            def_field = fts_def.GetFieldDefn(i)
            name=def_field.GetName()
            type_name=def_field.GetTypeName()
            list_field_def.append(ColumnsDesciptor(name,type_name))
        fts_def=None
        #layer_cur=None
        return list_field_def
    def createOutDs(self,path_out,type_drv):
        self.__out_drv=ogr.GetDriverByName(type_drv)
        if self.__out_drv is None:
            self.__error_message="Not find Out Drver "+type_drv
            return False
        self.__ds=self.__out_drv.CreateDataSource(path_out)
        if self.__ds is None:

            return False
        return True
    @property
    def SpatialRef(self):
        if self.__ds is None:
            return None
        self.LayerColumnsDef
        src=self.__layer.GetSpatialRef()
        return src
    def createLayer(self,name:str,fields_def:list,cs_des,options):
        src_out=createOgrSpatialReference(cs_des)
        #options=['OVERWRITE=YES']
        self.__layer = self.__ds.CreateLayer(name, src_out, ogr.wkbUnknown, options)
        size_str = 240
        for field_des in fields_def:
            ogr_def_field=createOgrField(field_des)
            self.__layer.CreateField(ogr_def_field,1)
        return True
    def copyTo(self,layer):
        out_layer_def=layer.GetLayerDefn()
        #layer.StartTransaction()
        count_feature=self.__layer.GetFeatureCount(1)
        for i in range(count_feature):
            ft=self.__layer.GetFeature(i+1)
            cur_ft=copyFeature(ft,out_layer_def)

            layer.CreateFeature(cur_ft)
            ft=None
            cur_ft=None
        #layer.CommitTransaction()
    @property
    def curentLayer(self):
        return self.__layer
    def close(self):
        if self.__layer is not None:
            self.__layer=None
        if self.__ds is not None:
            self.__ds=None
        return
def prjFile(path_file):
    ''' Получить SpatialReference файла '''
    ogr_source=OgrDataSource()
    isOk=ogr_source.open(path_file)
    if not isOk:
        return None
    sp_ref=ogr_source.SpatialRef
    ogr_source.close()
    return sp_ref
def csMiFromGdal(path_source):
    sp_ref=prjFile(path_source)
    if sp_ref is None:
        return None
    cs_wkt=sp_ref.ExportToWkt()
    cs_mi=CoordSystem.from_wkt(cs_wkt)
    return cs_mi
def csMi(path_source):
    tab=provider_manager.openfile(path_source)
    if tab is None:
        return None
    cs=tab.coordsystem
    tab.close()
    return cs

def runCombine(path_source_folder,ext_source:str,out_cs,name_out_layer,result_file,isSubFolder=True,progressbar=None):
    ''' Функция объедиения простраственных данных в один файл
    path_source_folder - исходная директория из которой берутся файлы для объединения
    ext_source - расширение исходных файлов
    out_cs - выходная проекция
    result_file - результирующий файл
    '''
    list_files=getFilesInfFolder(path_source_folder,ext_source.lower(),isSubFolder)
    source=OgrDataSource()
    ext_out_file=Path(result_file).suffix
    name_driver_out="GPKG"
    options= ['OVERWRITE=YES','ENCODING=UTF-8']
    if ext_out_file.lower()==".tab":
        options= ['ENCODING=CP1251']
        name_driver_out='MapInfo File'
    for i,source_file in enumerate(list_files):
        idOkOpen=source.open(source_file)
        if i==0:
            ''' output file '''
            out_ogr=OgrDataSource()

            out_ogr.createOutDs(result_file,name_driver_out)
            def_layer_field=source.LayerColumnsDef
            out_ogr.createLayer(name_out_layer,def_layer_field,out_cs,options)
        out_layer=out_ogr.curentLayer
        try:
            source.copyTo(out_layer)
        except:
            pass
        finally:
            source.close()
    out_ogr.close()

class workerCopy(QtCore.QThread):
    progressMade = QtCore.Signal(int)
    finished = QtCore.Signal(int)
    interrupted = QtCore.Signal()
    __isCancel=False
    def __init__(self):
        super().__init__()
        #self.count_proc = count
    def setParams(self,list_source_files,out_cs,name_out_layer,result_file,optimiz_bound=None,progressbar=None):
        self.__list_source_files=list_source_files
        self.__out_cs=out_cs
        self.__name_out_layer=name_out_layer
        self.__result_file=result_file
        self.__cls_progresBar=progressbar
        self.__optimiz_bound=optimiz_bound
    def cancel(self,isCancel):
        self.__isCancel=isCancel
    def terminate(self):
        self.__isCancel=True
    def run(self):
        source=OgrDataSource()
        ext_out_file=Path(self.__result_file).suffix
        name_driver_out="GPKG"
        options= ['OVERWRITE=YES','ENCODING=UTF-8']
        if ext_out_file.lower()==".tab":
            options= ['ENCODING=CP1251']
            name_driver_out='MapInfo File'
            self.__optimiz_bound=0.1
            self.combineToTab()
        for i,source_file in enumerate(self.__list_source_files):
            time.sleep(0.001)
            self.progressMade.emit(i + 1)
            if self.__isCancel:
                break
            idOkOpen=source.open(source_file)
            if i==0:
                ''' output file '''
                out_ogr=OgrDataSource()

                out_ogr.createOutDs(self.__result_file,name_driver_out)
                def_layer_field=source.LayerColumnsDef
                out_ogr.createLayer(self.__name_out_layer,def_layer_field,self.__out_cs,options)
            out_layer=out_ogr.curentLayer
            try:
                source.copyTo(out_layer)
            except:
                pass
            finally:
                source.close()
        out_ogr.close()
        self.__isCancel=False
        self.finished.emit(i)
    def combineToTab(self):
        tab_mem=None
        base_schema=None
        all_bound=None
        for i,source_file in enumerate(self.__list_source_files):

            time.sleep(0.001)
            self.progressMade.emit(i + 1)
            if self.__isCancel:
                break

            curent_tab=AxiPyTable()
            curent_tab.open(source_file)
            #curent_tab=provider_manager.openfile(source_file)
            if tab_mem is None:
                ''' Первый tab'''
                name_temp_file="temp_merge_"+str(randint(0,10000))
                base_schema=curent_tab.schema

                definition = {
                    'src': '',
                    'dataobject': name_temp_file,
                    'schema':base_schema}
                tab_mem = axipy.io.create(definition)

                #tab_mem=open_temporary(base_schema)

            count,bound=curent_tab.copyTo(tab_mem)
            if all_bound is None:
                all_bound=bound.clone
            else:
                all_bound.merge(bound)
            curent_tab.close()
        str_cs_bound=None
        if self.__optimiz_bound is not None:
            all_bound.extendOnProcent(self.__optimiz_bound)
            str_cs_bound=all_bound.boundsStr
            str_coordsys=base_schema.coordsystem.prj
            new_cs=CoordSystem.from_prj(str_coordsys+" "+str_cs_bound)
            base_schema.coordsystem=new_cs
        definition = {
            'src': self.__result_file,
            'schema': base_schema
        }
        table_out = provider_manager.create(definition)
        table_out.insert(tab_mem.items())
        try:
            tab_mem.restore()
            tab_mem.close()
        except:
            pass
        table_out.commit()
        table_out.close()
        self.__isCancel=False
        self.finished.emit(i)






















