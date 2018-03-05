# -*- coding: utf-8 -*-
"""
Created on Mon Mar 05 15:11:43 2018

@author: xy
"""

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
output=similar(output,distThreh)
sil=silhouetteCoefficient(output,data)
output['silhouetteCoefficient']=sil
