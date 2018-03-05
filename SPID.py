# -*- coding: utf-8 -*-
"""
Created on Mon Mar 05 15:00:22 2018

@author: xy
"""

import pandas as pd
import numpy as np
import math
import re
import os
import copy
import urllib2
import json

#批量处理各个文件
path='E:/Data/000/Trajectory'
os.chdir(path)
files=os.listdir(path)
data=pd.DataFrame()
for i in files:
    trajTem=pd.read_csv(i,sep=',',skiprows=6,header=None)
    #数据格式规整以适应算法
    trajTem=trajTem.ix[:,(0,1,5,6)]
    trajTem.columns=['Latitude','Longitude','Date','Time']
    data=data.append(trajTem,ignore_index=True)
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

#χ(x)函数
def ka(dis,dc):#dc表示截断距离，dis表示两点之间的距离
    if(dis>=dc):
        return 0
    else:
        return 1

#计算局部密度ρ的函数,输出结果存有局部密度值的list
def density(data,dc):
    latitude=list(data['Latitude'])
    longitude=list(data['Longitude'])
    part_density=[]   #存储局部密度值
    scope=[] #记录每个点计算局部密度的范围
    leftBoundary=0;rightBoundary=len(data)-1 #左边界与右边界
    for i in range(len(data)):
        traigger=True
        left=i-1
        right=i+1
        incrementLeft=1;incrementRight=1 
        while traigger:
            #向左拓展
            if incrementLeft!=0:                
                if left<0:
                    left=leftBoundary
                distanceLeft=GetDistance(longitude[left],latitude[left],longitude[i],latitude[i])
                if (distanceLeft<dc)&(left>leftBoundary):
                    left-=1
                else:
                    incrementLeft=0
            #向右拓展
            if incrementRight!=0:                
                if right>rightBoundary:
                    right=rightBoundary                            
                distanceRight=GetDistance(longitude[i],latitude[i],longitude[right],latitude[right])
                if (distanceRight<dc)&(right<rightBoundary):
                    right+=1
                else:
                    incrementRight=0
            #若左右都停止了拓展，此点的局部密度计算结束
            if (incrementLeft==0)&(incrementRight==0):
                traigger=False
            if (left==leftBoundary)&(incrementRight==0):
                traigger=False
            if (incrementLeft==0)&(right==rightBoundary):
                traigger=False
        if left==leftBoundary:
            scope.append([left,right-1])
            part_density.append(right-left-1)
        elif right==rightBoundary:
            scope.append([left+1,right])
            part_density.append(right-left-1)
        else:
            scope.append([left+1,right-1])
            part_density.append(right-left-2)
    return part_density,scope

dc=input("Please input dc:")
tc=input("Please input tc:")

data['part_density'],data['scope']=density(data,dc)

#反向更新的方法
def SP_search(data,tc):
    SP=[]
    part_density=copy.deepcopy(list(data['part_density']))
    scope=copy.deepcopy(list(data['scope']))
    day=copy.deepcopy(list(data['day']));hour=copy.deepcopy(list(data['hour']))
    minute=copy.deepcopy(list(data['minute']));second=copy.deepcopy(list(data['second']))
    latitude=copy.deepcopy(list(data['Latitude']))
    longitude=copy.deepcopy(list(data['Longitude']))
    traigger=True
    used=[]
    while traigger:
        partD=max(part_density)
        index=part_density.index(partD)
        print('index:',index)
        start=scope[index][0];end=scope[index][1]
        if len(used)!=0:
            for i in used:
                if (scope[i][0]>start)&(scope[i][0]<end):
                    part_density[index]=scope[i][0]-start-1
                    scope[index][1]=scope[i][0]-1
                    print("1_1")
                if (scope[i][1]>start)&(scope[i][1]<end):
                    part_density[index]=end-scope[i][1]-1
                    scope[index][0]=scope[i][1]+1
                    print("1_2")
                if (scope[i][0]<=start)&(scope[i][1]>=end):
                    part_density[index]=0
                    scope[index][0]=0;scope[index][1]=0
                    print("1_3")
            start=scope[index][0];end=scope[index][1]
        timeCross=86400*(day[end]-day[start])+3600*(hour[end]-hour[start])+60*(minute[end]-minute[start])+(second[end]-second[start])
        print('time:',timeCross)
        if timeCross>tc:
            SarvT=str(year[start])+'-'+str(month[start])+'-'+str(day[start])+' '+str(hour[start])+':'+str(minute[start])+':'+str(second[start])
            SlevT=str(year[end])+'-'+str(month[end])+'-'+str(day[end])+' '+str(hour[end])+':'+str(minute[end])+':'+str(second[end])
            SP.append([index,latitude[index],longitude[index],SarvT,SlevT,scope[index]])
            used.append(index)
            for k in range(scope[index][0],scope[index][1]+1):
                part_density[k]=0
        part_density[index]=0
        if max(part_density)==0:
            traigger=False
    return SP


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

SP=SP_search(data,tc)
output=pd.DataFrame(SP)
output.columns=['index','longitude','latitude','arriveTime','leftTime','scope']


output=similar(output,dc)
sil=silhouetteCoefficient(output,data)
output['silhouetteCoefficient']=sil

#output.to_csv('E:/output_avgcoor.csv')    
    

     