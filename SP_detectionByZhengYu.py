# -*- coding: utf-8 -*-
"""
Created on Tue Nov 28 20:06:44 2017

@author: xy
"""

import pandas as pd
import math
#from datetime import datetime
import re
import os
import copy
import numpy as np
import urllib2
import json

#批量处理各个文件
path='D:/data'
os.chdir(path)
files=os.listdir(path)
data=pd.DataFrame()
for i in files:
    trajTem=pd.read_csv(i,sep=',',skiprows=6,header=None)
    #数据格式规整以适应算法
    trajTem=trajTem.ix[:,(0,1,5,6)]
    trajTem.columns=['Latitude','Longitude','Date','Time']
    data=data.append(trajTem,ignore_index=True)

#数据预处理    
date=list(data['Date'])
time=list(data['Time'])
year=[];month=[];day=[];hour=[];minute=[];second=[]
for i in range(len(data)):
    d_tem=re.split(r'[-]',date[i])
    t_tem=re.split(r'[:]',time[i])
    year.append(int(d_tem[0]))
    month.append(int(d_tem[1]))
    day.append(int(d_tem[2]))
    hour.append(int(t_tem[0]))
    minute.append(int(t_tem[1]))
    second.append(int(t_tem[2]))
data['year']=year;data['month']=month;data['day']=day;data['hour']=hour;data['minute']=minute;data['second']=second
data=data.drop(['Date','Time'],axis=1)

#角度转换弧度函数
def rad(d):
    return float(d) * math.pi/180.0

#根据经纬度计算两点距离的函数，输出单位是米
EARTH_RADIUS=6378.137
def GetDistance(lng1,lat1,lng2,lat2):
    radLat1 = rad(lat1);
    radLat2 = rad(lat2);
    a = radLat1 - radLat2;
    b = rad(lng1) - rad(lng2);
    s = 2 * math.asin(math.sqrt(math.pow(math.sin(a/2),2) +math.cos(radLat1)*math.cos(radLat2)*math.pow(math.sin(b/2),2)))
    s = s * EARTH_RADIUS;
    s = round(s * 10000,2) / 10;
    return s

#计算中心点的函数,返回中心点的经纬度,data是DataFrame格式的数据集，i，j是位置，i<j
def ComputMeanCoord(data,i,j):
    latitude=list(data['Latitude'])
    longitude=list(data['Longitude'])
    amount=j-i+1
    if amount==0:
        return float(latitude[i]),float(longitude[i])
    sumLongitude=0
    sumLatitude=0
    for k in range(i,j+1):
        sumLatitude+=float(latitude[k])
        sumLongitude+=float(longitude[k])
    return sumLatitude/amount,sumLongitude/amount

#获取停留点的函数
def StayPoint_Detection(data,distThreh,timeThreh):
    latitude=list(data['Latitude'])
    longitude=list(data['Longitude'])
    day=list(data['day']);hour=list(data['hour']);minute=list(data['minute']);second=list(data['second'])
    i=0
    SP=[]
    pointNumber=len(data) #GPS数据点的数目
    while i<pointNumber:
        j=i+1
        Token=0
        while j<pointNumber:
            dist=GetDistance(longitude[i],latitude[i],longitude[j],latitude[j])
            if dist>float(distThreh):
                Time=abs(86400*(day[j-1]-day[i])+3600*(hour[j-1]-hour[i])+60*(minute[j-1]-minute[i])+(second[j-1]-second[i]))
                if Time>timeThreh:
                    S_latitude,S_longitude=ComputMeanCoord(data,i,j-1)
                    #SarvT=datetime.strptime(data.ix[i,5]+'-'+data.ix[i,6],'%Y-%m-%d-%H:%M:%S')
                    SarvT=str(year[i])+'-'+str(month[i])+'-'+str(day[i])+' '+str(hour[i])+':'+str(minute[i])+':'+str(second[i])
                    #SlevT=datetime.strptime(data.ix[j,5]+'-'+data.ix[j,6],'%Y-%m-%d-%H:%M:%S')
                    SlevT=str(year[j-1])+'-'+str(month[j-1])+'-'+str(day[j-1])+' '+str(hour[j-1])+':'+str(minute[j-1])+':'+str(second[j-1])
                    SP.append([S_longitude,S_latitude,SarvT,SlevT,[i,j-1]])
                    i=j
                    Token=1
                break
            j+=1
        if Token!=1:
            i+=1
    return SP

#输入距离阈值和时间阈值
distThreh=input("Please input dc:")
timeThreh=input("Please input tc:")

#最终结果保存成DataFrame格式
end=StayPoint_Detection(data,distThreh,timeThreh)
output=pd.DataFrame(end,columns=['longitude','latitude','arriveTime','leftTime','scope']) 

#计算停留点的平均速度和方差
def SpeedCom(data,sp):
    day=copy.deepcopy(list(data['day']));hour=copy.deepcopy(list(data['hour']))
    minute=copy.deepcopy(list(data['minute']));second=copy.deepcopy(list(data['second']))
    latitude=copy.deepcopy(list(data['Latitude']))
    longitude=copy.deepcopy(list(data['Longitude']))
    #index=copy.deepcopy(list(sp['index']))
    scope=copy.deepcopy(list(sp['scope']))
    avgSpeed=[]
    varSpeed=[]
    for sc in scope:
        speed=[]
        for i in range(sc[0],sc[1]):
            dis=abs(GetDistance(longitude[i],latitude[i],longitude[i+1],latitude[i+1]))
            time=abs(86400*(day[i]-day[i+1])+3600*(hour[i]-hour[i+1])+60*(minute[i+1]-minute[i+1])+(second[i]-second[i+1]))
            speed.append(dis/time)
        avgspeed=sum(speed)/len(speed)
        avgSpeed.append(avgspeed)
        varSpeed.append(sum(np.power(np.array(speed)-avgspeed,2))/len(speed))
    return avgSpeed,varSpeed

#计算去一个停留点的代价，即距离和时间的花费
def costCom(data,sp):
    day=copy.deepcopy(list(data['day']));hour=copy.deepcopy(list(data['hour']))
    minute=copy.deepcopy(list(data['minute']));second=copy.deepcopy(list(data['second']))
    latitude=copy.deepcopy(list(data['Latitude']))
    longitude=copy.deepcopy(list(data['Longitude']))
    scope=copy.deepcopy(list(sp['scope']))
    timeCost=[]
    distCost=[]
    for i in range(len(scope)-1):
        start,end=scope[i][1],scope[i+1][0]
        time=abs(86400*(day[start]-day[end])+3600*(hour[start]-hour[end])+60*(minute[start]-minute[end])+(second[start]-second[end]))
        timeCost.append(time)
        dist=0.0
        for j in range(start,end):
            dist+=GetDistance(longitude[j],latitude[j],longitude[j+1],latitude[j+1])
        distCost.append(dist)
    timeCost.insert(0,sum(timeCost)/len(timeCost))
    distCost.insert(0,sum(distCost)/len(distCost))
    return timeCost,distCost

#计算轮廓系数的函数
def silhouetteCoefficient(sp,data):
    sCoefficient=[]
    scope=copy.deepcopy(list(sp['scope']))
    latitude=copy.deepcopy(list(data['Latitude']))
    longitude=copy.deepcopy(list(data['Longitude']))
    for sco in scope:
        start,end=sco[0],sco[1]
        a_o=[]
        b_o=[]
        for i in range(start,end+1):
            dis=0.0
            for j in range(start,end+1):
                if i!=j:
                    dis+=GetDistance(longitude[i],latitude[i],longitude[j],latitude[j])
            a_o.append(dis/(end-start))
            minSearch=[]
            for sco_s in scope:
                dist=0.0
                if sco_s!=sco:
                    start_s,end_s=sco_s[0],sco_s[1]
                    for k in range(start_s,end_s+1):
                        dist+=GetDistance(longitude[i],latitude[i],longitude[k],latitude[k])
                    minSearch.append(dist/(end_s-start_s))
            b_o.append(min(minSearch))
        s_o=[(b_o[i]-a_o[i])/max(b_o[i],a_o[i]) for i in range(len(a_o))]
        sCoefficient.append(sum(s_o)/len(s_o))
    return sCoefficient

avgSpeed,varSpeed=SpeedCom(data,output)
timeCost,distCost=costCom(data,output)
output['avgSpeed']=avgSpeed
output['varSpedd']=varSpeed
output['timeCost']=timeCost
output['distCost']=distCost
      
sil=silhouetteCoefficient(output,data)
output['silhouetteCoefficient']=sil

#通过轮廓系数来判断sp1和sp2是否可以合并为一个sp
def SP_merge(sp1,sp2,data): #sp1、sp2数据类型应为Series
    latitude=copy.deepcopy(list(data['Latitude']))
    longitude=copy.deepcopy(list(data['Longitude']))
    a_o_2=sum([GetDistance(sp2.Longitude,sp2.Latitude,longitude[i],latitude[i]) 
               for i in range(sp2.scope[0],sp2.scope[1]+1)])/(sp2.scope[1]-sp2.scope[0])
    a_o_1=sum([GetDistance(sp1.Longitude,sp1.Latitude,longitude[i],latitude[i]) 
               for i in range(sp1.scope[0],sp1.scope[1]+1)])/(sp1.scope[1]-sp1.scope[0])
    b_o_2=sum([GetDistance(sp2.Longitude,sp2.Latitude,longitude[i],latitude[i]) 
               for i in range(sp1.scope[0],sp1.scope[1]+1)])/(sp1.scope[1]-sp1.scope[0]+1)
    b_o_1=sum([GetDistance(sp1.Longitude,sp1.Latitude,longitude[i],latitude[i]) 
               for i in range(sp2.scope[0],sp2.scope[1]+1)])/(sp2.scope[1]-sp2.scope[0]+1)
    s_o_1=(b_o_1-a_o_1)/max(b_o_1,a_o_1)
    s_o_2=(b_o_2-a_o_2)/max(b_o_2,a_o_2)
    if s_o_1<=0.0 or s_o_2<=0.0:
        return True
    else:
        return False

#通过代表的距离是否小于距离阈值来大致判断停留点是否一致
def similar(sp,dc):
    latitude=copy.deepcopy(list(sp['Latitude']))
    longitude=copy.deepcopy(list(sp['Longitude']))
    i=0;index=list(sp.index)
    for i in index:
        for j in index:
            if i!=j:
                dist=GetDistance(longitude[i],latitude[i],longitude[j],latitude[j])
                if dist<1.5*dc:
                    sp=sp.drop(j,axis=0)
                    index.remove(j)
    return sp

# -*- coding: utf-8 -*-
#使用高德地图web API将GPS坐标转换为高德经纬度坐标
theEnd=[]
for i in range(len(lat)):
    url_convert='http://restapi.amap.com/v3/assistant/coordinate/convert?locations='+str(lon_out[i])+','+str(lat_out[i])+'&coordsys=gps&key=6a70272cca2109c44e1c6888037d7c29&output=JSON'
    html=urllib2.urlopen(url_convert)
    hjson=json.loads(html.read())
    lon_x,lat_y=str(hjson['locations']).split(',') 
    lon_x=float(lon_x)  #转换后的经度
    lat_y=float(lat_y)  #转换后的纬度
    url_search='http://restapi.amap.com/v3/place/around?key=6a70272cca2109c44e1c6888037d7c29&location='+str(lon_x)+','+str(lat_y)+'&radius=1000&output=JSON&page=1&extensions=all'
    html2=urllib2.urlopen(url_search)
    hjson2=json.loads(html2.read())
    if len(hjson2['pois'])!=0:
        fields=hjson2['pois'][0].keys()
        poiData=pd.DataFrame(hjson2['pois'],columns=fields)
        page_num=int(hjson2['count'])/20+1
        types='餐饮服务|道路复数设施|地名地址信息|风景名胜|公共设施|公司企业|购物服务|交通设施服务|金融保险服务|科教文化服务|摩托车服务|汽车服务|汽车维修|汽车销售|商务住宅|生活服务|事件活动|室内设施|体育休闲服务|通行设施|医疗保健服务|政府机构及社会团体|住宿服务'
        #types='100000|110000|120000|130000|140000|150000|160000|170000|180000|190000|200000|220000|900000|970000|010000|020000|030000|040000|050000|060000|070000|080000|090000'
        if page_num!=1:
            for j in range(2,page_num+1):
                url=url_search='http://restapi.amap.com/v3/place/around?key=6a70272cca2109c44e1c6888037d7c29&location='+str(lon_x)+','+str(lat_y)+'&radius=1000&extensions=all&output=JSON&page='+str(j)+'&types='+types
                html_per_page=urllib2.urlopen(url)
                hjson_per_page=json.loads(html_per_page.read())
                #field=hjson_per_page['pois'][0].keys()
                poiData_per_page=pd.DataFrame(hjson_per_page['pois'],columns=fields)
                poiData=poiData.append(poiData_per_page)
            poiData.index=range(len(poiData))
            theEnd.append(poiData)