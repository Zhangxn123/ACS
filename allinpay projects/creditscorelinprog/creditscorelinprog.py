# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 14:56:45 2017

@author: yesf
"""
##############################################################################
#为方便与logistic模型结果的比对，评分卡为“颠倒型”，也就是分数越高，违约可能越大
#线性规划的基本想法是将评分卡设置为特征的线性组合后，最小化错判的分值差
#如果好人的得分高于好人线，或者坏人的得分低于坏人线，则判定为错判
# 目标函数：min sum(a_i)
# 约束条件：
# i = customer, j = category
# if not default, sum(C_j*X_ij)-a_i <= cutoff_good
# if default, sum(C_j*X_ij)+a_i >= cutoff_bad
# for any i, a_i >= 0, for any j, C_j no constraint
##############################################################################

import sys;
sys.path.append("allinpay projects/creditscorelinprog")
from imp import reload
import classlinprog
reload(classlinprog)

##############################################################################
##############################################################################
#一，初始化模型数据
##############################################################################
##############################################################################

#dataname = 'HMEQ'
dataname = 'german'
#dataname = 'taiwancredit'
LinProgmodel = classlinprog.CreditScoreLinearProgramming(dataname)
self = LinProgmodel

##############################################################################
##############################################################################
#二，设置模型参数
##############################################################################
##############################################################################
#1,粗分类和woe转换设置
#粗分类时聚类的数量
nclusters=10
#粗分类时聚类的方法,kmeans,DBSCAN,Birch，quantile(等分位数划分)，None(等距划分)
#cmethod = 'equal'
cmethod = 'quantile'
#cmethod = 'kmeans'
#cmethod = 'Birch'
#method = 'DBSCAN'
#2，训练集和测试集的划分
# 测试样本大小
testsize = 0.3
#交叉检验法分割数量
nsplit = 5
#3，变量筛选设置
feature_sel = 'origin'
#feature_sel = "VarianceThreshold"
#feature_sel = "RFECV"
#feature_sel == "SelectFromModel"
#feature_sel == "SelectKBest"
cv = 10
varthreshold = 0.2
#4,样本重采样
#4.0 不重采样
resmethod = None
#4.1 欠采样 undersampling
#resmethod = 'ClusterCentroids'
#resmethod = 'CondensedNearestNeighbour'
#resmethod = 'NearMiss'
#resmethod = 'RandomUnderSampler'
#4.2 过采样 oversampling
#resmethod = 'ADASYN'
#resmethod = 'RandomOverSampler'
#resmethod = 'SMOTE'
#4.3 过采样欠采样结合
#resmethod = 'SMOTEENN'
#resmethod = 'SMOTETomek'
#5 Linear Programming 的变量
cutoff_good = -3  ## cutoff_good 应当为负
cutoff_bad = cutoff_good   ## cutoff_bad 应当大于或等于cutoff_good
error_cost_ratio = 5

##############################################################################
##############################################################################
#三，建模并预测
##############################################################################
##############################################################################
#单次的train and test
predresult = self.LinProg_trainandtest(testsize, cv, feature_sel, varthreshold,\
            nclusters, cmethod, resmethod, cutoff_good, cutoff_bad, error_cost_ratio)
#K重train and test
#predresult = self.LinProg_trainandtest_kfold(nsplit, cv, feature_sel, varthreshold, nclusters, cmethod, resmethod)
#check = ((predresult.target!=predresult.predicted)*abs(predresult.probability-cutoff_bad)).sum()
#print('check=', check)
#ratio = (predresult.target==predresult.predicted).sum()/predresult.shape[0]
#print('correct ratio=', ratio)
##############################################################################
##############################################################################
#四，模型预测结果评估
##############################################################################
##############################################################################
#对模型总体预测能力的评价：
self.modelmetrics_binary(predresult)