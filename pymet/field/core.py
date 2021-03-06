# coding:utf-8
import numpy as np
import copy
from datetime import datetime
import pymet.stats as stats

__all__ = ['McGrid', 'McField', 'join']

def testgrid():
    name = 'test_grid'
    lon = np.arange(0,360,2.5)
    lat = np.arange(-90,90.1,2.5)
    lev = [1000,500,200]
    time = [datetime(2009,10,d) for d in range(1, 11)]
    return McGrid(name=name,lon=lon,lat=lat,lev=lev,time=time)

def testfield():
    grid = testgrid()
    data = np.arange(73*144*3*10, dtype=np.float32).reshape(10,3,73,144)
    return McField(data, name='test_field', grid=grid)
    
    
class McGrid:
    u"""
    グリッド情報を扱うためのクラス

    :Parameters:
     **name** : str
      
     **lon**

     **lat**

     **lev**

     **time**

     **ens**    

     **punit** : float, optional
      等圧面の気圧をPaに変換するためのパラメータ。デフォルトは100.でhPa->Paへの変換。


    **Notes**

    **Examples**
     >>> from pymet.field import *
     >>> grid = McGrid(name='test_grid', lon=np.arange(0,360,2.5), lat=np.arange(-90,90.1,2.5)),
                      lev=[1000.,500.,200.], time=[datetime(2009,10,11),datetime(2009,10,12),
                      dims=['time','lev','lat','lon'])

    **Attributes**
    
    ======= ======================
    name
    lon
    lat
    lev
    time
    ens
    dims
    punit
    xdim
    ydim
    zdim
    tdim
    ======= ======================

    **Methods**

    .. currentmodule:: pymet.field.core.McGrid
    
    ..  autosummary::
    
        copy
        latlon
        dimindex
        dimshape    
        gridmask
        getgrid
    
    """
    def __init__(self,name=None,lon=None,lat=None,lev=None,time=None,ens=None,punit=100.,sphere=True):
        # インスタンス作成時にのみ次元の順序をGrADS形式の順序で設定し、
        # その後は、lon,lat,lev,time,ensが変更される度にその長さに応じて変更する
        self.__dict__['dims'] = ['ens','time','lev','lat','lon']
        #
        self.name = name
        self.lon  = lon
        self.lat  = lat
        self.lev  = lev
        self.time = time
        self.ens  = ens
        self.punit = 100.
        self.sphere = sphere

    def _setdimsattr(self, name, which):
        u"""
        dims属性を設定するための内部ルーチン。
        """
        dimsattr = self.__dict__['dims']
        correct_order = ['ens','time','lev','lat','lon']
        if which == 'remove':
            if name in dimsattr: dimsattr.remove(name)
        elif which == 'add':
            if not name in dimsattr:
                dimsattr.append(name)
                dimsattr.sort(key=lambda l: correct_order.index(l))
        else:
            raise ValueError, "internal Error in pymet.field.core.McGrid._setdimsattr"
        
    def __setattr__(self, name, value):
        u"""
        lon, lat, lev, time, ensの属性がセットされたときに、その長さに応じてNumpy Arrayに変換する。
        """
        # dims属性は、lon,lat,lev,time,ensの長さに応じた自動設定に限定
        if name == 'dims':
            raise AttributeError, "Cannot set 'dims' attribute"
        try:
            if name in ['lon', 'lat', 'lev', 'time', 'ens'] :
                if np.size(value)==0:
                    self.__dict__[name] = None
                    self._setdimsattr(name, 'remove')
                elif np.size(value)==1:
                    try:
                        self.__dict__[name] = value[0]
                    except TypeError:
                        self.__dict__[name] = value
                    self._setdimsattr(name, 'remove')                    
                else:
                    self.__dict__[name] = np.asarray(value)
                    self._setdimsattr(name, 'add')                    
            else:
                self.__dict__[name] = value
        except:
            raise 
    def __getattr__(self, name):
        u"""
        xdim, ydim, zdim, tdim, edim を属性で呼び出したときに、dims属性に対応する
        次元が登録されていればその次元を返す。
        """
        try:
            if name == 'xdim':
                dname = 'lon'
                return self.dims.index('lon')
            elif name == 'ydim':
                dname = 'lat'
                return self.dims.index('lat')
            elif name == 'zdim':
                dname = 'lev'
                return self.dims.index('lev')
            elif name == 'tdim':
                dname = 'time'
                return self.dims.index('time')
            elif name == 'edim':
                dname = 'ens'
                return self.dims.index('ens')
            elif name == 'xn':
                dname = 'lon'
                return len(self.lon)
            elif name == 'yn':
                dname = 'lat'                
                return len(self.lat)
            elif name == 'zn':
                dname = 'lev'                
                return len(self.lev)
            elif name == 'tn':                
                dname = 'time'
                return len(self.time)
            elif name == 'en':
                dname = 'ens'                
                return len(self.ens)
        except ValueError:
            raise AttributeError, "McGrid instance has no dimension '{0}'".format(dname)
        raise AttributeError, "McGrid instance has no attribute '{0}'".format(name)

    def copy(self):
        u"""
        McGridオブジェクトの深いコピーを返す。
        """
        grid = McGrid(self.name)
        for a in self.__dict__:
            v = self.__dict__[a]
            if v is not None:
                grid.__dict__[a] = copy.deepcopy(v)
        return grid

    def latlon(self):
        u"""
        2次元プロットのための緯度・経度配列を返す。
        
        :Returns:
         **lat, lon** : 2darray
          緯度,経度配列
        """
        if np.size(self.lon) < 2 or np.size(self.lat) < 2:
            raise ValueError, "McGrid instance does not have enogh length of 'lon' and 'lat' dimension" 

        lon, lat = np.meshgrid(self.lon, self.lat)
        return lat, lon

    def dimindex(self, dimnames, filtered=False):
        u"""
        次元のインデックスを返す。

        :Arguments:
         **dimnames** : str or list
          次元名もしくは、次元名のリスト
         **filtered** : リストを与えた場合に、gridに含まれる次元のみで検索するかどうか。
                        デフォルトはFalse。Falseの場合に含まれない次元名を与えるとValueErrorとなる。
        :Returns:
         **index** : int or list
          引数がリストの場合はリストを返す。
        """
        try:
            if isinstance(dimnames, str):
                return self.dims.index(dimnames)
            else:
                if filtered: dimnames = filter(lambda s: s in self.dims, dimnames)
                return [self.dims.index(dimname) for dimname in dimnames]
        except:
            raise ValueError, "McGrid instance has no dimension '{0}'".format(dimnames)

    def dimshape(self):
        u"""
        """
        shape = ()
        for dim in ['ens','time','lev','lat','lon']:
            dn = getattr(self, dim)
            if dn != None: dn = np.size(dn)
            shape += (dn,)

        return shape

    def dimvalueindex(self, **kwargs):
        u"""
        各次元の値のインデックスを返す。次元が存在しないときはKeyError、
        値が存在しないときはValueErrorを発生する。

        :Arguments:
         **lon, lat, lev, time, ens** : int or datetime object
          次元名とその値。

        **Exmaple**
         >>> grid.lev
         array([1000., 925., 850., 700.], dtype=float32)
         >>> grid.time
         array([2009-10-11 00:00:00, 2009-10-12 00:00:00], dtype=object)
         >>> grid.dimidx(lev=700)
         3
         >>> grid.dimidx(lev=700, time=datetime(2009,10,11,0))
         (3, 0)
        """
        idx_out = ()
        for key, value in kwargs.items():
            dimvalue = getattr(self, key)
            if dimvalue is None:
                return KeyError, "McGrid instance has no dimension '{0}'".format(key)
            idx = list(dimvalue).index(value)
            if idx < 0:
                raise ValueError, "McGrid instance has no value '{0}' in '{1}' dimension".format(value, key)
            else:
                idx_out += (idx,)

        if len(idx_out) <2:
            return idx_out[0]
        else:
            return idx_out

    def gridmask(self, **kwargs):
        u"""
        指定した範囲の値をインデキシングするためのindexing配列を求める。

        :Arguments:
         **lon, lat, lev** : tuple or list of floats, or float, optional
           経度、緯度、鉛直次元の指定する領域。
         **time** : tuple or list or datetime object, optional
           時間次元の範囲。
         **ens** : tuple or list or int
           アンサンブル次元の範囲。

        :Returns:
         **mask** : indexing ndarray

        **Examples**    
         範囲を指定する場合はタプルで指定する。
          >>> grid = pymet.McGrid(name='test_grid', lon=np.arange(0,360,2.5), lat=np.arange(-90,90.1,2.5)),
                                  lev=[1000.,500.,200.,100.], time=[datetime(2009,10,11),datetime(2009,10,12),
                                  dims=['time','lev','lat','lon'])
          >>> mask = grid.gridmask(lon=(0., 180.))
         2つ以上の値で指定する場合はリストで指定する。
          >>> mask = grid.gridmask(lev=[500,100])
        """
        for kwd in kwargs:
            if not kwd in self.dims:
                raise ValueError, "McGrid instance has no dimension {0}".format(kwd)
        mask = []
        for dim in self.dims:
            dimvalue = self.__dict__[dim]
            kwdvalue = kwargs.get(dim, None)
            if kwdvalue == None:
#                mask.append(slice(None,None,None))
                mask.append(dimvalue==dimvalue)                
            elif isinstance(kwdvalue, tuple):
                kwdmin, kwdmax = min(kwdvalue), max(kwdvalue)
                mask.append((dimvalue>=kwdmin) & (dimvalue<=kwdmax))                
            elif isinstance(kwdvalue, list):
                mask.append(map((lambda x: x in dimvalue), kwdvalue))
            else:
                if kwdvalue<dimvalue.min() or kwdvalue>dimvalue.max():
                    raise ValueError, "{0}={1} is out of domain".format(dim, kwdvalue)
                mask.append(np.arange(len(dimvalue))==np.argmin(np.abs(dimvalue-kwdvalue)))

        return np.ix_(*mask)

    def getgrid(self, **kwargs):
        u"""
        指定した範囲の値を含むようなMcGridを返す

        :Arguments:
         **lon, lat, lev** : tuple or list of floats, or float, optional
           経度、緯度、鉛直次元の指定する領域。
         **time** : tuple or list or datetime object, optional
           時間次元の範囲。
         **ens** : tuple or list or int
           アンサンブル次元の範囲。

        :Returns:
         **grid** : McGrid

        **Examples**    
         範囲を指定する場合はタプルで指定する。
          >>> grid = pymet.McGrid(name='test_grid', lon=np.arange(0,360,2.5), lat=np.arange(-90,90.1,2.5)),
                                  lev=[1000.,500.,200.,100.], time=[datetime(2009,10,11),datetime(2009,10,12),
                                  dims=['time','lev','lat','lon'])
          >>> new_grid = grid.getgrid(lon=(0., 180.))
         2つ以上の値で指定する場合はリストで指定する。
          >>> new_grid = grid.getgrid(lev=[500,100])
        """
        for kwd in kwargs:
            if not kwd in self.dims:
                raise ValueError, "McGrid instance has no dimension {0}".format(kwd)
        grid = self.copy()
        for key, value in kwargs.items():
            dimvalue = getattr(self, key)
            if isinstance(value, tuple):
                kwdmin, kwdmax = min(value), max(value)
                mask = (dimvalue>=kwdmin) & (dimvalue<=kwdmax)
            elif isinstance(value, list):
                mask = map((lambda x: x in dimvalue), value)
            else:
                if value<dimvalue.min() or value>dimvalue.max():
                    raise ValueError, "{0}={1} is out of domain".format(dim, value)
                mask = np.argmin(np.abs(dimvalue-value))
            new_dimvalue = dimvalue[mask]
            nd = np.size(new_dimvalue)
            if nd == 0:
                setattr(grid, key, None)
            elif nd == 1:
                try:
                    setattr(grid, key, new_dimvalue[0])
                except TypeError:
                    setattr(grid, key, new_dimvalue)
                except:
                    raise
            else:
                setattr(grid, key, new_dimvalue)
                
            return grid
    
class McField(np.ma.MaskedArray):
    u"""
    格子点データを扱うためのクラス。

    :Arguments:
     **data** : array_like
      格子点データ
     **name**

    **Attribure**
     ======== ======= =====================================
     grid     McGrid  座標に関するデータ
     name     str     変数名
     ======== ======= =====================================
     
     その他属性はnumpy.ma.MaskedArrayと共通。

    **Methods**
     .. currentmodule:: pymet.field

     .. autosummary::
        
        McField.copy
        McField.get

        McField.dmean

        McField.runave
        McField.lowfreq

        McField.mean    
        McField.sum
                
        McField.anom
        McField.conjugate
        McField.cumsum
        McField.cumprod  

        McField.prod    
        McField.std     
        McField.var        
        McField.max 
        McField.min
        McField.ptp
        
     .. autosummary::
        McField.dmean
        
    """
    def __new__(cls, data, **kwargs):
        cls.name = None
        cls.grid = McGrid()
        return super(McField, cls).__new__(cls, data, **kwargs)
    
    def __init__(self, data, name=None, grid=None, **kwargs):
#        super(McField,self).__init__(self, data, **kwargs)
        super(McField,self).__init__(data, **kwargs)
        self.name = name
        if grid == None:
            grid = McGrid(name)
            self.grid = grid
        elif isinstance(grid, McGrid):
            self.grid = grid
        else:
            raise TypeError, "grid must be a McGrid instance"

    def copy(self):
        """
        コピーを返す。
        """
        return McField(self.data.copy(), name=self.name,
                       grid=self.grid.copy(), mask=self.mask.copy())
                                  
    def __getitem__(self, keys):
        ## まずデータ部分について、keysでスライスする
        ## super.__getitem__だとmaskが上手くスライスできない?
        data = np.ma.asarray(self)[keys]
        #        data = super(np.ma.MaskedArray, self).__getitem__(keys)

        ## ゼロ要素は次元を削除
        data = np.ma.squeeze(data)
        
        ## スライスの結果が、arrayにならなければMcFieldにしないで値を返す
        if np.size(data)<2:
            return data

        ## スライスの結果が、arrayになっていればMcFieldにする
        grid = self.grid.copy()
        
        ## ここからかなり変則。検討課題。
        # np.indiceで各軸でのインデックスの配列をつくり、
        # keysでスライスして各次元でのスライスインデックス(1次元)をつくる
        try:
            ind = np.indices(self.shape)
            dimidx = [np.unique(ind[i][keys]) for i in range(self.ndim)]
            # 各次元の値のスライスを求めて、変更する。
            for dimname, idx in zip(self.grid.dims, dimidx):
                setattr(grid, dimname, getattr(grid, dimname)[idx])
                
            return McField(data, name=self.name, grid=grid, mask=data.mask)                
        except:            
            return data

    def get(self, **kwargs):
        u"""
        指定した次元の範囲のスライスを返す。

        :Arguments:
         **lon, lat, lev, time, ens** : optional
          経度、緯度、鉛直、時間、アンサンブル次元の範囲。
          指定の仕方は :py:func:`McGrid.gridmask` に準ずる。
        :Returns:
         **result** : McField object

        **Examples**
         >>> data.grid.dims
         >>> 
        """
        mask = self.grid.gridmask(**kwargs)
        return self[mask]

    #--------------------------------------------------------------
    #-- 領域を指定して計算するメソッド
    #--------------------------------------------------------------
    def dmean(self, **kwargs):
        u"""
        指定した領域に対する平均を求める。

        :Arguments:
         **lon, lat, lev, time, ens** : optional
          経度、緯度、鉛直、時間、アンサンブル次元の範囲。
          指定の仕方は :py:func:`McGrid.gridmask` に準ずる。

        :Returns:
         **result** : McField object

        """
        mask = self.grid.gridmask(**kwargs)
        result = self[mask]
        axes = []
        for dimname in kwargs.keys():
            try:
                axis = result.grid.dims.index(dimname)
            except ValueError:
                raise ValueError, "input field does not have dimension {0}".format(dimname)
            result = result.mean(axis=axis)
        return result

    #--------------------------------------------------------------
    #--- pymetの関数のメソッド化
    #--------------------------------------------------------------
    def runave(self, length, bound='mask'):
        u"""
        移動平均の結果を返す

        .. seealso::
        
           .. autosummary::
              :nosignatures:
     
               pymet.stats.runave

        """
        grid = self.grid.copy()
        data = np.ma.getdata(self)
        mask = np.ma.getmask(self)

        result = stats.runave(data, length, axis=grid.tdim, bound=bound)
        if np.size(result) < 2:
            return result
        if bound == 'valid':
            grid.time = grid.time[length/2:-length/2]
        return McField(result, name='runave', grid=grid, mask=mask)

    def timefilter(self, cut1, cut2=None, mode='lowpass', bound='mask'):
        u"""
        Lanczosフィルターをかけた成分を返す。

        :Arguments:
         **cut1** : int
          カットオフ(イン)周波数。''日数''で指定する。
         **cut2** : int
          bandpassフィルター時のカットイン周波数。''日数''で指定する。
         **bound** : {'mask', 'valid'}, optional
          境界の扱い方。デフォルトはmask。
        :Returns:
         **out** : McField object
        """
        grid = self.grid.copy()
        data = np.ma.getdata(self)
        mask = np.ma.getmask(self)

        # grid.timeからcutoff日に対応するステップ数を求める
        dt = np.diff(grid.time)[0]
        if not np.all(np.diff(grid.time) == dt):
            raise ValueError, "time step must be same"
        
        cut1 = int(cut1*3600.*24 / dt.total_seconds())
        if cut2:
            cut2 = int(cut2*3600.*24 / dt.total_seconds())
            
        length = 2*max(cut1, cut2) + 1
        result = stats.lanczos_filter(data, cut1, cut2=cut2, length=length,
                                      tdim=grid.tdim, bound=bound, mode=mode)
        if np.size(result) < 2:
            return result
        if bound == 'valid':
            grid.time = grid.time[length/2:-length/2]
            mask = tools.mrollaxis(mask, grid.tdim, 0)
            mask = mask[length/2:-length/2,...]
            mask = tools.mrollaxis(mask, 0, grid.tdim+1)

        mask = mask | result.mask
        return McField(result, name=self.name + '_' + mode, grid=grid, mask=mask)

    #-------------------------------------------------------------
    #-- インデックスをgridの値で返す関数
    #-------------------------------------------------------------
    def gridmin(self, **kwargs):
        u"""
        最小値をとる座標を返す。

        :Returns:
         **valuemin** :
          最小値をとる次元の値。ens,time,lev,lat,lonの順で含まれる次元を返す。
        """
        if len(kwargs) != 0:
            field = self.get(**kwargs)
            grid = field.grid.copy()
            data = np.ma.asarray(field)            
        else:            
            grid = self.grid.copy()
            data = np.ma.asarray(self)
            
        idx = np.unravel_index(data.argmin(), data.shape)
        valuemin = []        
        for i, key in enumerate(grid.dims):
            valuemin.append(getattr(grid, key)[idx[i]])

        return valuemin

    def gridmax(self, **kwargs):
        u"""
        最大値をとる座標を返す。

        :Returns:
         **valuemax** :
          最大値をとる次元の値。ens,time,lev,lat,lonの順で含まれる次元を返す。
        """
        if len(kwargs) != 0:
            field = self.get(**kwargs)
            grid = field.grid.copy()
            data = np.ma.asarray(field)            
        else:            
            grid = self.grid.copy()
            data = np.ma.asarray(self)
        idx = np.unravel_index(data.argmax(), data.shape)
        valuemax = []        
        for i, key in enumerate(grid.dims):
            valuemax.append(getattr(grid, key)[idx[i]])

        return valuemax

    def gridargmin(self, **kwargs):
        u"""
        最小値をとる座標のインデックスを返す。

        :Returns:
         **idx** :
          最小値をとる座標のインデックスをタプルで返す。

        .. note::
         これは以下と同じである。

         >>> np.unravel_index(field.argmin(), field.argmin())
        """
        if len(kwargs) != 0:
            gmask = self.grid.gridmask(**kwargs)
            mask = np.zeros(self.shape, dtype=np.bool)
            mask[gmask] = True
            mask = mask | np.ma.getmask(self)
            data = np.ma.array(self, mask=mask)
        else:
            data = np.ma.array(self)            

        idx = np.unravel_index(data.argmin(), data.shape)

        return idx

    def gridargmax(self, **kwargs):
        u"""
        最大値をとる座標のインデックスを返す。

        :Returns:
         **idx** :
          最大値をとる座標のインデックスをタプルで返す。         
        """
        if len(kwargs) != 0:
            gmask = self.grid.gridmask(**kwargs)
            mask = np.zeros(self.shape, dtype=np.bool)
            mask[gmask] = True
            mask = mask | np.ma.getmask(self)
            data = np.ma.array(self, mask=mask)
        else:
            data = np.ma.array(self)            

        idx = np.unravel_index(data.argmax(), data.shape)

        return idx

    #--------------------------------------------------------------
    #-- MaskedArrayのMarithmeticsメソッドに対するラッパー
    #--------------------------------------------------------------
    ## Arithmetics
    #-------------------------------------------------------------
    #-- 領域指定計算対応済みメソッド
    #-------------------------------------------------------------
    def mean(self, axis=None, dtype=None, out=None, **kwargs):
        u"""
        指定した軸、もしくは領域での平均を計算する。

        :Arguments:
         **lon, lat, lev, time, ens** : tuple or list
          平均を計算する領域。指定の仕方は :py:func:`McGrid.gridmask` に準ずる。
         **axis** : int, optional
          平均を計算する軸。指定しない場合は全領域で計算。
          lon,lev,lat,time,ensが指定されている場合は無視される。
          
        :Returns:
         **result** : McField or float

        **Examples**
         >>> field.mean(lon=(0,180), lat=(0,90))
        """
        # gridを持たない場合はMaskedArrayを返す
        if not hasattr(self, 'grid') or out!=None:
            np.ma.asarray(self).mean(axis=axis, dtype=dtype, out=out)
            
        if len(kwargs) != 0:
            field = self.get(**kwargs)
            grid = field.grid.copy()
            axes = grid.dimindex(kwargs.keys(), filtered=True)
            result = np.ma.asarray(field)
            for i, axis in enumerate(axes):            
                result = result.mean(axis=axis-i, dtype=dtype, out=out)            
        else:
            grid = self.grid.copy()
            axes = [axis]
            result = np.ma.asarray(self).mean(axis=axis, dtype=dtype, out=out)
            
        rndim = getattr(result, 'ndim', 0)
        # 返り値が無次元の場合、gridを持たない場合はMcFieldにしない
        if not rndim:
            return result        
        # 縮約される次元の値をNoneにする        
        for i, axis in enumerate(axes):
            setattr(grid, grid.dims[axis-i], None)
        result = McField(result, name=self.name, grid=grid, mask=result.mask)

        return result

    def sum(self, axis=None, dtype=None, out=None, **kwargs):
        u"""
        指定した軸、もしくは領域での合計を計算する。

        :Arguments:
         **lon, lat, lev, time, ens** : tuple or list
          計算する領域。指定の仕方は :py:func:`McGrid.gridmask` に準ずる。
         **axis** : int, optional
          計算する軸。指定しない場合は全領域で計算。
          lon,lev,lat,time,ensが指定されている場合は無視される。
          
        :Returns:
         **result** : McField or float
         
        **Examples**
         >>> field.sum(lon=(0,180), lat=(0,90))
        """
        # gridを持たない場合はMaskedArrayを返す
        if not hasattr(self, 'grid') or out!=None:
            np.ma.asarray(self).sum(axis=axis, dtype=dtype, out=out)
            
        if len(kwargs) != 0:
            field = self.get(**kwargs)
            grid = field.grid.copy()
            axes = grid.dimindex(kwargs.keys(), filtered=True)
            result = np.ma.asarray(field)
            for i, axis in enumerate(axes):            
                result = result.sum(axis=axis-i, dtype=dtype, out=out)            
        else:
            grid = self.grid.copy()
            axes = [axis]
            result = np.ma.asarray(self).sum(axis=axis, dtype=dtype, out=out)
            
        rndim = getattr(result, 'ndim', 0)
        # 返り値が無次元の場合、gridを持たない場合はMcFieldにしない
        if not rndim:
            return result        
        # 縮約される次元の値をNoneにする        
        for i, axis in enumerate(axes):
            setattr(grid, grid.dims[axis-i], None)
        result = McField(result, name=self.name, grid=grid, mask=result.mask)

        return result

    ##----------------------------------------------------------------------------
    #-- 領域指定未対応
    ##----------------------------------------------------------------------------
    def cumsum(self, axis=None, dtype=None, out=None):
        u"""
        """
        marray = np.ma.asarray(self)
        result = marray.cumsum(axis=axis, dtype=dtype, out=out)
        rndim = getattr(result, 'ndim', 0)

        # 返り値が無次元の場合、gridを持たない場合はMcFieldにしない
        if not rndim or not hasattr(self, 'grid') or out!=None:
            return result        
        # 縮約される次元の値をNoneにする            
        grid = self.grid.copy()        
        if axis != None:
            setattr(grid, grid.dims[axis], None)
        result = McField(result, name=self.name, gird=grid, mask=result.mask)

        return result

    def cumprod(self, axis=None, dtype=None, out=None):
        u"""
        """
        marray = np.ma.asarray(self)
        result = marray.cumprod(axis=axis, dtype=dtype, out=out)
        rndim = getattr(result, 'ndim', 0)

        # 返り値が無次元の場合、gridを持たない場合はMcFieldにしない
        if not rndim or not hasattr(self, 'grid') or out!=None:
            return result        
        # 縮約される次元の値をNoneにする            
        grid = self.grid.copy()        
        if axis != None:
            setattr(grid, grid.dims[axis], None)
        result = McField(result, name=self.name, gird=grid, mask=result.mask)
        
        return result


    def prod(self, axis=None, dtype=None, out=None):
        u"""
        """
        marray = np.ma.asarray(self)
        result = marray.prod(axis=axis, dtype=dtype, out=out)
        rndim = getattr(result, 'ndim', 0)

        # 返り値が無次元の場合、gridを持たない場合はMcFieldにしない
        if not rndim or not hasattr(self, 'grid') or out!=None:
            return result        
        # 縮約される次元の値をNoneにする            
        grid = self.grid.copy()        
        if axis != None:
            setattr(grid, grid.dims[axis], None)
        result = McField(result, name=self.name, gird=grid, mask=result.mask)

        return result


    ## axis, dtype, out, ddof 型: outオプションには対応せず互換性のために残しておく
    def std(self, axis=None, dtype=None, out=None, ddof=None):
        u"""
        """
        marray = np.ma.asarray(self)
        result = marray.std(axis=axis, dtype=dtype, out=out, ddof=ddof)
        rndim = getattr(result, 'ndim', 0)

        # 返り値が無次元の場合、gridを持たない場合はMcFieldにしない
        if not rndim or not hasattr(self, 'grid') or out!=None:
            return result        
        # 縮約される次元の値をNoneにする            
        grid = self.grid.copy()        
        if axis != None:
            setattr(grid, grid.dims[axis], None)
        result = McField(result, name=self.name, gird=grid, mask=result.mask)

        return result

    def var(self, axis=None, dtype=None, out=None, ddof=None):
        u"""
        """
        marray = np.ma.asarray(self)
        result = marray.std(axis=axis, dtype=dtype, out=out, ddof=ddof)
        rndim = getattr(result, 'ndim', 0)

        # 返り値が無次元の場合、gridを持たない場合はMcFieldにしない
        if not rndim or not hasattr(self, 'grid') or out!=None:
            return result        
        # 縮約される次元の値をNoneにする            
        grid = self.grid.copy()        
        if axis != None:
            setattr(grid, grid.dims[axis], None)
        result = McField(result, name=self.name, gird=grid, mask=result.mask)

        return result

    ## Minimum/Maximum---------------------------------------------------------------------------
    ## axis, out, fill_value型    
    def max(self, axis=None, out=None, fill_value=None):
        u"""
        """
        marray = np.ma.asarray(self)
        result = marray.max(axis=axis, out=out, fill_value=fill_value)
        rndim = getattr(result, 'ndim', 0)

        # 返り値が無次元の場合、gridを持たない場合はMcFieldにしない
        if not rndim or not hasattr(self, 'grid') or out!=None:
            return result        
        # 縮約される次元の値をNoneにする            
        grid = self.grid.copy()        
        if axis != None:
            setattr(grid, grid.dims[axis], None)
        result = McField(result, name=self.name, gird=grid, mask=result.mask)

        return result

    def min(self, axis=None, out=None, fill_value=None):
        u"""
        """
        marray = np.ma.asarray(self)
        result = marray.min(axis=axis, out=out, fill_value=fill_value)
        rndim = getattr(result, 'ndim', 0)

        # 返り値が無次元の場合、gridを持たない場合はMcFieldにしない
        if not rndim or not hasattr(self, 'grid') or out!=None:
            return result        
        # 縮約される次元の値をNoneにする            
        grid = self.grid.copy()        
        if axis != None:
            setattr(grid, grid.dims[axis], None)
        result = McField(result, name=self.name, gird=grid, mask=result.mask)

        return result

    def ptp(self, axis=None, out=None, fill_value=None):
        u"""
        """
        marray = np.ma.asarray(self)
        result = marray.ptp(axis=axis, out=out, fill_value=fill_value)
        rndim = getattr(result, 'ndim', 0)

        # 返り値が無次元の場合、gridを持たない場合はMcFieldにしない
        if not rndim or not hasattr(self, 'grid') or out!=None:
            return result        
        # 縮約される次元の値をNoneにする            
        grid = self.grid.copy()        
        if axis != None:
            setattr(grid, grid.dims[axis], None)
        result = McField(result, name=self.name, gird=grid, mask=result.mask)
        
        return result

    #---------------------------------------------------------------------------------------
    
    # ラッパーのためのクロージャー
    def _oper_wrapper(oper):
        def wrapper(self, *args, **kwargs):
            marray = np.ma.asarray(self)
            result = oper(marray, *args, **kwargs)
            rndim = getattr(result, 'ndim', 0)            
            if not rndim or not hasattr(self, 'grid'):
                return result
            else:
                result = McField(result, name=self.name, grid=self.grid.copy(), mask=result.mask)
                return result
        return wrapper

    __lt__        = _oper_wrapper(np.ma.MaskedArray.__lt__)
    __le__        = _oper_wrapper(np.ma.MaskedArray.__le__)
    __eq__        = _oper_wrapper(np.ma.MaskedArray.__eq__)
    __ne__        = _oper_wrapper(np.ma.MaskedArray.__ne__)
    __gt__        = _oper_wrapper(np.ma.MaskedArray.__gt__)
    __ge__        = _oper_wrapper(np.ma.MaskedArray.__ge__)
    
    __add__       = _oper_wrapper(np.ma.MaskedArray.__add__)           # +
    __sub__       = _oper_wrapper(np.ma.MaskedArray.__sub__)           # -
    __mul__       = _oper_wrapper(np.ma.MaskedArray.__mul__)           # *
    __floordiv__  = _oper_wrapper(np.ma.MaskedArray.__floordiv__)
    __mod__       = _oper_wrapper(np.ma.MaskedArray.__mod__)           #
    __divmod__    = _oper_wrapper(np.ma.MaskedArray.__divmod__)
    __pow__       = _oper_wrapper(np.ma.MaskedArray.__pow__)
    __lshift__    = _oper_wrapper(np.ma.MaskedArray.__lshift__)
    __rshift__    = _oper_wrapper(np.ma.MaskedArray.__rshift__)
    __and__       = _oper_wrapper(np.ma.MaskedArray.__and__)
    __xor__       = _oper_wrapper(np.ma.MaskedArray.__xor__)

    __div__       = _oper_wrapper(np.ma.MaskedArray.__div__)
    __truediv__   = _oper_wrapper(np.ma.MaskedArray.__truediv__)

    __radd__      = _oper_wrapper(np.ma.MaskedArray.__radd__)
    __rsub__      = _oper_wrapper(np.ma.MaskedArray.__rsub__)
    __rmul__      = _oper_wrapper(np.ma.MaskedArray.__rmul__)
    __rdiv__      = _oper_wrapper(np.ma.MaskedArray.__rdiv__)
    __rtruediv__  = _oper_wrapper(np.ma.MaskedArray.__rtruediv__)
    __rdivmod__   = _oper_wrapper(np.ma.MaskedArray.__rdivmod__)
    __rpow__      = _oper_wrapper(np.ma.MaskedArray.__rpow__)
    __rlshift__   = _oper_wrapper(np.ma.MaskedArray.__rlshift__)
    __rrshift__   = _oper_wrapper(np.ma.MaskedArray.__rrshift__)
    __rand__      = _oper_wrapper(np.ma.MaskedArray.__rand__)
    __rxor__      = _oper_wrapper(np.ma.MaskedArray.__rxor__)
    __ror__       = _oper_wrapper(np.ma.MaskedArray.__ror__)

    __iadd__      = _oper_wrapper(np.ma.MaskedArray.__iadd__)
    __isub__      = _oper_wrapper(np.ma.MaskedArray.__isub__)
    __imul__      = _oper_wrapper(np.ma.MaskedArray.__imul__)
    __idiv__      = _oper_wrapper(np.ma.MaskedArray.__idiv__)
    __itruediv__  = _oper_wrapper(np.ma.MaskedArray.__itruediv__)
    __ifloordiv__ = _oper_wrapper(np.ma.MaskedArray.__ifloordiv__)
    __imod__      = _oper_wrapper(np.ma.MaskedArray.__imod__)
    __ipow__      = _oper_wrapper(np.ma.MaskedArray.__ipow__)
    __ilshift__   = _oper_wrapper(np.ma.MaskedArray.__ilshift__)
    __irshift__   = _oper_wrapper(np.ma.MaskedArray.__irshift__)
    __iand__      = _oper_wrapper(np.ma.MaskedArray.__iand__)
    __ixor__      = _oper_wrapper(np.ma.MaskedArray.__ixor__)
    __ior__       = _oper_wrapper(np.ma.MaskedArray.__ior__)

    __neg__       = _oper_wrapper(np.ma.MaskedArray.__neg__)
    __pos__       = _oper_wrapper(np.ma.MaskedArray.__pos__)
    __abs__       = _oper_wrapper(np.ma.MaskedArray.__abs__)
    __invert__    = _oper_wrapper(np.ma.MaskedArray.__invert__)

    __int__       = _oper_wrapper(np.ma.MaskedArray.__int__)
    __long__      = _oper_wrapper(np.ma.MaskedArray.__long__)
    __float__     = _oper_wrapper(np.ma.MaskedArray.__float__)

    # numpy ufunc
    exp = _oper_wrapper(np.ma.exp)
    abs = absolute = _oper_wrapper(np.ma.abs)
    conjugate = _oper_wrapper(np.ma.conjugate)
    sqrt = _oper_wrapper(np.ma.sqrt)
    sin = _oper_wrapper(np.ma.sin)
    cos = _oper_wrapper(np.ma.cos)
    tan = _oper_wrapper(np.ma.tan)
    
def join(args, axis=0):
    u"""
    McFieldオブジェクトを指定した次元方向に結合する。

    :Arguments:
     **args** : tuple or list of McField objects
      結合するMcFieldオブジェクトのリストまたはタプル。結合する次元以外は同じ形状でなければならない。
     **axis** : int ot str, optional
      結合する軸を指定する。次元名('lon','lat','lev','time')で指定することもできる。デフォルトは0で先頭。

    :Returns:
     **out** : McField instance
      

    **Examples**
     >>> field1.grid.dims
     ['time', 'lev', 'lat', 'lon']
     >>> field2.grid.dims
     ['time', 'lev', 'lat', 'lon']
     >>> field1.shape, field2.shape
     ((2, 3, 73, 144), (4, 3, 73, 144))
     >>> field1.grid.time
     array([2009-10-11 00:00:00, 2009-10-12 00:00:00], dtype=object)
     >>> field2.grid.time
     array([2009-10-13 00:00:00, 2009-10-14 00:00:00, 2009-10-15 00:00:00,
            2009-10-16 00:00:00], dtype=object)
     >>> result = pymet.mcfield.join((field1, field2), axis='time')
     >>> result.shape
     (6, 3, 73, 144)
     >>> result.grid.time
     array([2009-10-11 00:00:00, 2009-10-12 00:00:00, 2009-10-13 00:00:00,
            2009-10-14 00:00:00, 2009-10-15 00:00:00, 2009-10-16 00:00:00], dtype=object)
            
    """
    if not isinstance(args, list) and not isinstance(args, tuple):
        raise TypeError, "input must be tuple or list of McField instance."
    if len(args)<2:
        raise ValueError, "more than two fields must be inputed."

    for arg in args:
        if not isinstance(arg, McField):
            raise TypeError, "input field must be McField instance."
        
    grid = args[0].grid.copy()
    if isinstance(axis, str):
        dimname = axis
        axis = grid.dims.index(axis)
    else:
        dimname = grid.dims[axis]

    data = np.ma.concatenate(args, axis=axis)
    value = np.hstack([getattr(arg.grid,dimname).copy() for arg in args])
    setattr(grid, dimname, value)
    
    return McField(data, name=grid.name, grid=grid, mask=data.mask)

