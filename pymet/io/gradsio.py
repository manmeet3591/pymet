# coding:utf-8
"""
"""
from grads import GaCore
from pymet.field import McField, McGrid
from pymet.tools import d2s, s2d
import numpy as np
from datetime import datetime
import os, os.path

__all__ = ['GradsIO']

class GradsIO:
    u"""
    pygradsを用いてMcFieldデータを読み込むためのクラス。

    :Arguments:
      **Echo** : bool, optional
         gradsの出力を標準出力に表示するかどうか。デフォルトはFalse。

    .. note::


    **Examples**
     >>> gaio = pymet.io.GradsIO()

    **Attrubutes**

    ======= ====================================
    ga
    ======= ====================================

    **Methods**
    .. currentmodule:: pymet.io.gradsio.GradsIO
    
    ..  autosummary::

        open
        command
        setdim
        get
        __init__

    """
    def __init__(self, Echo=False):
        ga = GaCore('grads -b', Echo=Echo)
        self.ga = ga
        self.fn = 0   # 開いているファイル数
        self.vars = []
        self._first = True
        
    def open(self, fname, Quiet=True):
        u"""
        ctlファイル、またはnetCDFファイルを開く。

        :Arguments:
         **fname** : str
          ctlファイル、またはnetCDFファイルパス。netCDF形式は拡張子(.nc or .netcdf)で判断する。
         **Quiet** : bool, optional          
        """
        if fname[:7]!='http://' and not os.path.isfile(fname):
            raise IOError, "cannot find {0}".format(fname)
    
        root, ext = os.path.splitext(fname)
        if ext.upper() == '.NC' or ext.upper() == '.NETCDF':
            ftype='SDF'
        else:
            ftype='default'
        self.ga.open(fname, ftype=ftype, Quiet=Quiet)
        
        self.fn = self.fn + 1
        self.ga('set dfile '+str(self.fn))
        qfile = self.ga.query('file')
        self.vars.append(qfile.vars)

        if self._first:
            coords = self.ga.coords()
            if coords.lon[-1] - coords.lon[0] == 360.:            
                self.ga('set lon %f %f' % (coords.lon[0], coords.lon[-2]))
            self._first = False
            
    def close(self, fid=-1):
        u"""
        fidで指定したファイル番号のファイルを閉じる。

        :Arguments:
         **fid** : int, optional
          閉じるファイル番号。指定しない場合は、最後に開いたファイルを閉じる。
        """
        if fid > self.fn:
            raise ValueError, "the number of opened files is less than "+str(fid)
        elif fid == -1:
            fid = self.fn
        self.ga('close '+str(fid))
        self.vars.pop(fid-1)
        self.fn = self.fn - 1
        
    def allclose(self):
        u"""
        開いているすべてのファイルを閉じる。
        """
        self.ga('allclose')
        self.fn = 0
        self._first = True
        self.vars = []
        
    def command(self,command_string):
        u"""
        コマンドをGrADSに送る。

        :Arguments:
         **command_string** : string
          コマンド。
        """
        self.ga.cmd(command_string)
        
    def setdim(self, lon=None, lat=None, lev=None, time=None, ens=None, x=None, y=None, z=None, t=None):
        u"""
        GrADSの次元を設定する

        :Arguments:
         **lon** : tuple or float
          経度。
         **lat** : tuple or float
          緯度。
         **lev** : tuple or float
          鉛直次元。
         **time** : tuple or datetime
          時間次元。
         **ens** : tuple or int or str
          アンサンブル次元。'all'を指定すると全てのアンサンブルメンバーを指定。
         **x, y, z, t**  : tuple or int
          x,y,z,t次元で指定する場合。lon,lat,lev,timeが指定してあれば、そちらが優先される。
        """
        if isinstance(lon, tuple):
            self.ga.cmd('set lon %f %f' % lon)
        elif lon != None:
            self.ga.cmd('set lon %f' % lon)
        elif isinstance(x, tuple):
            self.ga('set x %d %d' % x)
        elif x != None:
            self.ga('set x %d' % x)
        else:
            coords = self.ga.coords()
            if coords.lon[-1] - coords.lon[0] == 360.:            
                self.ga.cmd('set lon %f %f' % (coords.lon[0], coords.lon[-2]))
            
        if isinstance(lat, tuple):
            self.ga.cmd('set lat %f %f' % lat)
        elif lat!=None:
            self.ga.cmd('set lat %f' % lat)
        elif isinstance(y, tuple):
            self.ga('set y %d %d' % y)
        elif y != None:
            self.ga('set y %d' % y)
            
        if isinstance(lev, tuple):
            self.ga('set lev %f %f' % lev)
        elif lev!=None:
            self.ga('set lev %f' % lev)
        elif isinstance(t, tuple):
            self.ga('set z %d %d' % z)
        elif z != None:
            self.ga('set z %d' % z)
            
        if isinstance(time, tuple):
            self.ga('set time %s %s' % (d2s(time[0]), d2s(time[1])))
        elif time != None:
            self.ga('set time %s' % d2s(time))
        elif isinstance(t, tuple):
            self.ga('set t %d %d' % t)
        elif t != None:
            self.ga('set t %d' % t)
            
        if isinstance(ens, tuple):
            self.ga('set e %d %d' % ens)
        elif type(ens) == type(int(1)):
            self.ga('set e %d' % ens)
        elif ens=='all':
            self.ga('set e 1 %d' % self.ga.query('file',Quiet=True).ne)
        
    def get(self, var, fid=None):
        u"""
        指定した変数をMcFieldオブジェクトとして取得する。

        :Arguments:
         **var** : str
          変数名または、ave(変数名, dim=, dim=)。
         **fid** : int, optional
          ファイルを複数開いている場合にファイルidを指定する。指定しない場合は先頭から探して、
          指定した変数を含む最もファイルidの小さいファイルから読み込む。
        :Returns:
         **field** : McField object
        """
        # 開かれているファイルの変数リストから探す
        if 'ave(' in var:
            gavar = var[4:].split(',')[0]
        else:
            gavar = var
        if fid==None:
            for i, fvars in enumerate(self.vars):
                if gavar in fvars:
                    fid = i+1
                    break
        if fid==None:
            raise ValueError, "Cannot find variable {0} in sill opened files".format(gavar)

        # デフォルトファイルを変更
        self.ga('set dfile '+str(fid))

        # 次元を調べる
        dh = self.ga.query('dims', Quiet=True)
        info = self.ga.coords()
        ne, nt, nz, ny, nx = dh.ne, dh.nt, dh.nz, dh.ny, dh.nx
        e1, e2 = dh.ei
        t1, t2 = dh.ti
        z1, z2 = dh.zi

        # 次元の値を取得する
        lon  = np.asarray(info.lon, dtype=np.float32)
        lat  = np.asarray(info.lat, dtype=np.float32)
        lev  = np.asarray(info.lev, dtype=np.float32)
        time = np.asarray([s2d(d) for d in info.time])
        ens  = np.asarray(info.ens)

        # データを取得
        out = np.zeros((ne,nt,nz,ny,nx))
        ## 4次元以上はgradsでは同時に扱えないのでループする
        ## 少ない次元を優先的にループ
        
        if nz == max(ne, nt, nz):
            try:
                for i, e in enumerate(range(e1,e2+1)):
                    self.ga.cmd('set e %d' % e)
                    for j, t in enumerate(range(t1,t2+1)):
                        self.ga.cmd('set t %d' % t)
                        out[i,j,:,:,:]  = np.asarray(self.ga.eval(var), dtype=np.float32).reshape((nz,ny,nx))
                        self.ga.Writer.flush()
            except:
                self.ga.flush()
                self.ga.setdim(dh)
                raise
        elif nt == max(ne, nt, nz):
            try:
                for i, e in enumerate(range(e1,e2+1)):
                    self.ga.cmd('set e %d' % e)
                    for k, z in enumerate(range(z1,z2+1)):
                        self.ga.cmd('set z %d' % z)
                        out[i,:,k,:,:]  = np.asarray(self.ga.eval(var), dtype=np.float32).reshape((nt,ny,nx))
                        self.ga.Writer.flush()
            except:
                self.ga.flush()
                self.ga.setdim(dh)
                raise
        else:
            try:
                for j, t in enumerate(range(t1,t2+1)):
                    self.ga.cmd('set t %d' % t)
                    for k, z in enumerate(range(z1,z2+1)):
                        self.ga.cmd('set z %d' % z)
                        out[:,j,k,:,:]  = np.asarray(self.ga.eval(var), dtype=np.float32).reshape((ne,ny,nx))
                        self.ga.Writer.flush()
            except:
                self.ga.flush()
                self.ga.setdim(dh)
                raise
        out  = np.squeeze(out)
        out  = np.ma.array(out, mask=(out==info.undef))
        self.ga.flush()
        self.ga.setdim(dh)

        # McFieldオブジェクトを作成
        grid = McGrid(name=var, lon=lon, lat=lat, lev=lev, time=time, ens=ens)
        field = McField(out, name=var, grid=grid, mask=out.mask)

        return field

