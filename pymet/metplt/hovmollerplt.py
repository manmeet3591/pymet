# coding:utf-8
#------------------------------------------------------------
#--- Hovmollerプロット
#------------------------------------------------------------
import matplotlib.pyplot as plt
import matplotlib.dates
import matplotlib.ticker
from datetime import datetime
import pymet.tools as tools
import numpy as np
import ticker

__all__ = ['hovplot','hovcontour','hovcontourf']

def hovplot(xy,time,**kwargs):
    ur"""
    ホフメラー図のプロット。

    :Arguments:
     **xy** : array_like
      x or y or 緯度経度座標。
     **time** : array_like of datetime objects
      時間軸。datetimeオブジェクトのarray。
    :Returns*
     **CR**

    **Keyword**

     =========== ============ ======================================================
     Value       Default      Description
     =========== ============ ======================================================
     xylab       None         横軸を経度表示にする場合は'lon',
                              緯度表示にする場合は'lat'を指定する
     fmt         %Hz%d%b\\n%Y 時間軸ラベルの表示形式
     =========== ============ ======================================================

    :Returns:
     **CR**

    **Examples**      
    """
    ax = kwargs.get('ax',plt.gca())
    ax.set_ylim(time.max(),time.min())
    fmt = kwargs.pop('fmt','%HZ%d%b\n%Y')
    
    if isinstance(time[0], datetime) :
        if fmt==None:
            ax.yaxis.set_major_formatter(matplotlib.ticker.NullFormatter())
        else:
            ax.yaxis.set_major_formatter(ticker.DateFormatter(fmt=fmt))

    xylab = kwargs.pop('xylab',None)            
    if xylab=='lon':
        ax.xaxis.set_major_formatter(ticker.XaxisFormatter())
    elif xylab=='lat':
        ax.xaxis.set_major_formatter(ticker.YaxisFormatter())        
    return ax.plot(xy,time,*args,**kwargs)


def hovcontour(xy,time,data,*args,**kwargs):
    ur"""
    ホフメラー図のコンタープロット。

    :Arguments:
     **xy** : array_like
      x or y or 緯度経度座標。
     **time** : array_like of datetime objects
      時間軸。datetimeオブジェクトのarray。
     **data** : 2darray
      プロットするデータ。
    :Returns:
     **CR**

    **Keyword**
    
     =========== ============ ======================================================
     Value       Default      Description
     =========== ============ ======================================================
     colors      'k'          コンターの色。
     cint        None         コンター間隔。指定しない場合は自動で決定される。
     cintlab     True         図の右下にcontour interval= 'cint unit'の形式で
                              コンター間隔の説明を表示。cintを指定した場合に有効。
     labunit     ''           cinttext=Trueの場合に表示する単位。
     hoffset     0            コンター間隔を表す文字列の位置のオフセット
     voffset     auto         コンター間隔を表す文字列の位置のオフセット
     xylab       None         横軸を経度表示にする場合は'lon',
                              緯度表示にする場合は'lat'を指定する
     fmt         %Hz%d%b\\n%Y 時間軸ラベルの表示形式
     =========== ============ ======================================================


    **Examples**
      
    """
    ax = kwargs.get('ax',plt.gca())
    kwargs.setdefault('colors','k')
    ax.set_ylim(time.max(),time.min())
           
    fmt = kwargs.pop('fmt','%HZ%d%b\n%Y')
    if isinstance(time[0],datetime):
        ax.yaxis.set_major_formatter(ticker.DateFormatter(fmt=fmt))

    xylab = kwargs.pop('xylab',None)        
    if xylab=='lon':
        ax.xaxis.set_major_formatter(ticker.XaxisFormatter())
    elif xylab=='lat':
        ax.xaxis.set_major_formatter(ticker.YaxisFormatter())        
        
    cint = kwargs.pop('cint', None)        
    if cint != None:
        kwargs.setdefault('locator',matplotlib.ticker.MultipleLocator(cint))
        if kwargs.pop('cintlab',True):
            hoffset = kwargs.pop('hoffset', 0)
            voffset = -FontProperties(size=rcParams['font.size']).get_size_in_points() - rcParams['xtick.major.pad'] - rcParams['xtick.major.size']
            voffset = kwargs.pop('voffset', voffset)                
            labunit = kwargs.pop('labunit', '')
            ax.annotate('contour interval = %g %s' % (cint, labunit),
                        xy=(1, 0), xycoords='axes fraction',
                        xytext=(hoffset, voffset), textcoords='offset points',
                        ha='right',va='top')
        
    return ax.contour(xy,time,data,*args,**kwargs)

def hovcontourf(xy,time,data,*args,**kwargs):
    ur"""
    ホフメラー図の塗りつぶしコンタープロット。

    :Arguments:
     **xy** : array_like
      x or y or 緯度経度座標。
     **time** : array_like of datetime objects
      時間軸。datetimeオブジェクトのarray。
     **data** : 2darray
      プロットするデータ。
    :Returns:
     **CF**

     
    **Keyword**
     独自キーワード
    
     =========== ============ ======================================================
     Value       Default      Description
     =========== ============ ======================================================
     colors      'k'          コンターの色。
     cint        None         コンター間隔。指定しない場合は自動で決定される。
     xylab       None         横軸を経度表示にする場合は'lon',
                              緯度表示にする場合は'lat'を指定する
     fmt         %Hz%d%b\\n%Y 時間軸ラベルの表示形式
     =========== ============ ======================================================
     
     basemapと共通のキーワード(デフォルトを独自に設定しているもの)
     
     ========== ======= ======================================================
     Value      Default Description
     ========== ======= ======================================================
     exntend    'both'
     ========== ======= ======================================================
     
    **Examples**
     .. plot:: ../examples/hovcontourf.py
    
    """
    ax = kwargs.get('ax',plt.gca())
    ax.set_ylim(time.max(),time.min())
    kwargs.setdefault('extend', 'both')
    
    fmt = kwargs.pop('fmt','%HZ%d%b\n%Y')    
    if isinstance(time[0],datetime):
        ax.yaxis.set_major_formatter(ticker.DateFormatter(fmt=fmt))

    xylab = kwargs.pop('xylab',None)        
    if xylab=='lon':
        ax.xaxis.set_major_formatter(ticker.XaxisFormatter())
    elif xylab=='lat':
        ax.xaxis.set_major_formatter(ticker.YaxisFormatter())        

    cint = kwargs.pop('cint', None)        
    if cint != None:
        kwargs.setdefault('locator',matplotlib.ticker.MultipleLocator(cint))
        
    return ax.contourf(xy,time,data,*args,**kwargs)

