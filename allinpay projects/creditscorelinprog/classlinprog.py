# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 14:56:14 2017

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
import os;
sys.path.append("allinpay projects/creditscorelinprog")
from imp import reload
import creditscore
reload(creditscore)
from creditscore import CreditScore
import numpy as np
import pandas as pd
import time
from scipy.optimize import linprog
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold
from sklearn.feature_selection import VarianceThreshold
from sklearn.feature_selection import RFECV
from sklearn.feature_selection import SelectFromModel
from sklearn.feature_selection import SelectKBest



class CreditScoreLinearProgramming(CreditScore):
    
    def LinProg_trainandtest(self, testsize, cv, feature_sel, varthreshold, nclusters, \
                             cmethod, resmethod, cutoff_good, cutoff_bad, error_cost_ratio):

        #分割数据集为训练集和测试集
        data_feature = self.data.ix[:, self.data.columns != 'default']
        data_target = self.data['default']
        X_train, X_test, y_train, y_test = train_test_split(data_feature, data_target, test_size=testsize, random_state=0)
        
        
        #对训练集做变量粗分类和woe转化，并据此对测试集做粗分类和woe转化
        X_train, X_test = self.binandwoe_traintest(X_train, y_train, X_test, nclusters, cmethod)
            
        #在train中做变量筛选, sklearn.feature_selection中的方法
        if feature_sel == "VarianceThreshold":
            selector = VarianceThreshold(threshold = varthreshold)
            X_train1 = pd.DataFrame(selector.fit_transform(X_train))
            X_train1.columns = X_train.columns[selector.get_support(True)]
            X_test1 = X_test[X_train1.columns]
        elif feature_sel == "RFECV":
            estimator = LogisticRegression()
            selector = RFECV(estimator, step=1, cv=cv)
            X_train1 = pd.DataFrame(selector.fit_transform(X_train, y_train))
            X_train1.columns = X_train.columns[selector.get_support(True)]
            X_test1 = X_test[X_train1.columns]
        elif feature_sel == "SelectFromModel":
            estimator = LogisticRegression()
            selector = SelectFromModel(estimator)
            X_train1 = pd.DataFrame(selector.fit_transform(X_train, y_train))
            X_train1.columns = X_train.columns[selector.get_support(True)]
            X_test1 = X_test[X_train1.columns]
        elif feature_sel == "SelectKBest":
            selector = SelectKBest()
            X_train1 = pd.DataFrame(selector.fit_transform(X_train, y_train))
            X_train1.columns = X_train.columns[selector.get_support(True)]
            X_test1 = X_test[X_train1.columns]
        else:
            X_train1, X_test1 = X_train, X_test        
            
        #重采样resampling 解决样本不平衡问题
        X_train1, y_train = self.imbalanceddata (X_train1, y_train, resmethod)             
        
        # 线性规划的前m项为回归系数（特征数），后n项为每个人
        
        # 目标函数前半部分
        opt_coeff = [0]*X_train1.shape[1]
        
        # 线性限制的条件和系数（线性限制必须为<=），以及各变量的限制条件
        res_bound = []
        res_coeff = []
        var_bound = []
        
        for i in range(X_train1.shape[0]):
            if y_train.iloc[i] == 0:
                bound_temp = cutoff_good
                coeff_temp = list(X_train1.iloc[i,:])
                opt_coeff = opt_coeff + [1]
            elif y_train.iloc[i] == 1:
                bound_temp = -cutoff_bad
                coeff_temp = [-l for l in list(X_train1.iloc[i,:])]
                opt_coeff = opt_coeff + [error_cost_ratio]
            else:
                print('error')
            
            coeff_dist = [0]*i + [-1] + [0]*(X_train1.shape[0]-i-1)
            coeff_temp = coeff_temp + coeff_dist

            res_coeff.append(coeff_temp)
            res_bound.append(bound_temp)
             
            
        for j in range(X_train1.shape[1]):
            var_bound.append((None, None))
        
        for j in range(X_train1.shape[0]):
            var_bound.append((0, None))

#        var_bound = tuple(var_bound)
        
        result = linprog(opt_coeff, A_ub = res_coeff, b_ub = res_bound , bounds = var_bound,\
               options={"maxiter": 10000,'tol': 1e-9, "disp": True})
        
#        return result
#        print(result.x)
        predcoeff = result.x[:X_train1.shape[1]]
        for i in range(0,len(predcoeff)):
            print(i+1, predcoeff[i])

        score = np.dot(X_test1,predcoeff)
#        scoretrain = np.dot(X_train1,predcoeff)
        #训练并预测模型
#        classifier = LogisticRegression()  # 使用类，参数全是默认的
#        classifier.fit(X_train1, y_train)  
#        predicted = classifier.predict(X_test)
#        probability = classifier.predict_proba(X_test1)

        predresult = pd.DataFrame({'target' : y_test, 'score' : score})
        predresult['predicted'] = (score > cutoff_bad).astype(int)
#        predresult = pd.DataFrame({'target' : y_train, 'score' : scoretrain})
#        predresult['predicted'] = (scoretrain < cutoff_bad).astype(int)
        
        
        return predresult
