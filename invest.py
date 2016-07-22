#!/usr/local/bin/python

#coding:-*-utf-8-*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import numpy as np
#from scipy.optimize import minimize
import pandas as pd
import time
import os
import warnings
warnings.filterwarnings("ignore")
import json
import getopt

def dotMultiply(a,b):
    """ dot multiply 
    example: A = [1, 2, 3], B = [2, 3, 4], then
    return C = [1*2, 2*3, 3*4] = [2, 6, 12]
    """
    result = []
    for i in xrange(len(a)):
        result.append(a[i]*b[i])
    return result
#***********************************************************************

def formula(a,b):
    """ Formula Expression
    example : A = ['x', 'y', 'z'], B = [1, 2, 3], then 
    return : C = 1*x + 2*y + 3*z
    """
    exp = []
    for i, v in enumerate(a):
        exp.append(str(b[i])+"*"+v)
        if i < len(a) -1 :
            exp.append("+")
    return ' '.join(i for i in exp)

#***********************************************************************
def couponMatchPorduct(coupon_0, product):
    """ Create Product list for each Product """
    selectedproduct = pd.DataFrame()
    dropproduct     = pd.DataFrame()
    category = ['firstCategoryId', 'secondCategoryId', 'thirdCategoryId', 'fouthCategoryId']
    for i in xrange(len(coupon_0['supportCategoryVoList'])):
        item = coupon_0['supportCategoryVoList'][i]
        if item["supportFlag"] :
            for name in item.keys() :
                if name in category :
                    selectedproduct = selectedproduct.append(product[product[name] == item[name]])
        else :
            for name in item.keys() :
                if name in category :
                    dropproduct = dropproduct.append(product[product[name] == item[name]])
    if len(dropproduct) > 0:
        droplist = list(dropproduct.index)
        for i in droplist:
            selectedproduct = selectedproduct.drop(i)   
    
    if len(selectedproduct) > 0 :
        selectedproduct = selectedproduct.drop_duplicates()
        
    return selectedproduct

#********************************************************************
def productMatchCoupon(product_0, coupon):

    category = ['firstCategoryId', 'secondCategoryId', 'thirdCategoryId', 'fouthCategoryId']
    selectcoupon = pd.DataFrame()
    dropcoupon = pd.DataFrame()
    
    for i in xrange(len(coupon)) :
        if coupon.loc[i, "allProductSupportFlag"] == True:
            selectcoupon = selectcoupon.append(coupon.loc[i])
        else :
            for j, name in enumerate(list(pd.DataFrame(product_0 ).index)):
                if name in category :
                    for ii in xrange(len(coupon['supportCategoryVoList'])):
                        item = pd.DataFrame(coupon['supportCategoryVoList'][ii])
                        column = list(item.columns)
                        if name in column :
                            underselectcoupon = item[item[name] == product_0[name]]
                            if len(underselectcoupon) > 0 :
                                aaa = list(underselectcoupon['supportFlag'])
                                if aaa[0] :
                                    selectcoupon = selectcoupon.append(coupon.loc[ii])
                                else :
                                    dropcoupon = dropcoupon.append(coupon.loc[ii])
    
    if len(dropcoupon.index) > 0:
        for j in dropcoupon.index :
            selectcoupon = selectcoupon.drop(j)
    
    if len(selectcoupon) > 0 :
        selectcoupon = selectcoupon.drop_duplicates()
    
    return selectcoupon


#***********************************************************************
def json2DataFrame(jsonpath):
    """ Read Json data into DataFrame """
    jsondata = json.load(open(jsonpath,'r'))
    product  = pd.DataFrame(jsondata)
    return product
#***************************************************************************
def cleaninvest(result) :
    columns = list(set(result.productId))
    for i in columns:
        tmp1 = result[result.productId == i]
        if len(tmp1) >= 2:
            for ii in tmp1.index :
                if len(list(tmp1.couponId[ii])) > 0 :
                    t = ii
                else :
                    result.loc[t, 'investAmount'] += tmp1.loc[ii, 'investAmount']
                    result.loc[t, 'incomeTotal'] += tmp1.loc[ii, 'incomeTotal']
                    result = result.drop(ii)
    result.index = xrange(len(result))
    return result   
#*************************************************************************

class optimizeInvest(object):
    
    def __init__(self, **kwargs):        
        self.coupon  = pd.DataFrame()
        self.product = pd.DataFrame()
        if 'product' in kwargs.keys():
            product_loc = kwargs['product']
            product  = pd.DataFrame(json.loads(product_loc))
            for ii in xrange(len(product)):
                if product.maxInvestAmount[ii] == -1 :
                    product.loc[ ii,'maxInvestAmount'] = product.loc[ii,'remainInvestAmount']
                    pass
                    
                if product.loc[ii, "remainInvestAmount"] < product.loc[ii, "minInvestAmount"] :
                    product = product.drop(ii)                    
                        
            
            product['realratio'] = 1.0*product.productRatio*product.productDueDays/365
            product['check'] =  product.remainInvestAmount - product.minInvestAmount
            product = product.sort_values(by = ["realratio", "productDueDays", "minInvestAmount", "maxInvestAmount"], ascending=[False, True, True, False])
            product = product[product.check >= 0]
            del product['check']
            product.index = xrange(len(product))
            self.product = product

        if 'coupon' in kwargs.keys():
            coupon_loc = kwargs['coupon']
            coupon  = pd.DataFrame(json.loads(coupon_loc))
            if len(coupon) > 0:
                coupon['rate'] = 1.0*coupon.couponAmount/(coupon.couponMinInvestAmount - coupon.couponAmount)
                coupon['real_start'] = coupon.couponMinInvestAmount - coupon.couponAmount
                coupon = coupon.sort_values(by = ['couponAmount', 'couponMinInvestAmount'], ascending = [False, True])
                coupon.index = xrange(len(coupon))
                self.coupon = coupon
        
        if len(self.product) == 0:
            #print("Error: The Product list is empty !!!")
            sys.exit(12)
        else :
            pass
        
    def nocoupon(self, needinvest, deadline, product):
        """--- No Coupon Model ---"""
        tmp = 0
        investratio = []
        total = needinvest
        tmp_product = product[product.productDueDays <= deadline]
        new_product =  tmp_product[tmp_product.minInvestAmount <= needinvest]
        new_product.index = xrange(len(new_product))
        prod_cnt    = len(new_product)  
        product     = new_product        
        nocouponresult = pd.DataFrame()
        investproduct = []
        usedcoupon    = []
        couponvalue   = []
        realrate    = []
        realincome  = []
        yearrate = []
        yearincome = []
        investamount = []        
                
        if prod_cnt == 0:
            #print("Warning : No product satisfy the Deadline !!! \n")
            sys.exit(21)
        
        #print new_product
        niter = 0
        maxiter = len(new_product)
        while (needinvest > 0) and len(new_product) > 0 and niter <= maxiter:
            niter += 1
            for i in xrange(len(new_product)):
                if needinvest >= new_product.loc[i, 'minInvestAmount'] :
                    if new_product.loc[i, 'maxInvestAmount'] == -1 :
                        tmpinvest = new_product.loc[i, 'remainInvestAmount']
                    else :
                        tmpinvest = min(new_product.loc[i, 'remainInvestAmount'], new_product.loc[i, 'maxInvestAmount'])
                    
                    if needinvest <= tmpinvest :

                        remainder = needinvest%new_product.loc[i, 'perIncAmount']                        
                        integer   = needinvest - remainder
                        
                        if round(1.0*remainder/new_product.loc[i, 'perIncAmount'], 2) == 0:
                            
                            investproduct.append(new_product.loc[i, 'productId'])
                            usedcoupon.append('')
                            couponvalue.append(0)
                            realrate.append(1.0*new_product.loc[i, 'realratio'])
                            yearrate.append(1.0*new_product.loc[i, 'productRatio'])
                            
                            investamount.append(needinvest)                            
                            realincome.append(needinvest*1.0*new_product.realratio[i])
                            yearincome.append(needinvest*new_product.productRatio[i])
                            needinvest = 0
                            pass
                        else :
                            #print "2222222"
                            if integer >=  new_product.minInvestAmount[i] :
                                investproduct.append(new_product.productId[i])
                                usedcoupon.append('')
                                couponvalue.append(0)
                                realrate.append(1.0*new_product.realratio[i])
                                yearrate.append(1.0*new_product.productRatio[i])
                                
                                investamount.append(integer)
                                realincome.append(integer*1.0*new_product.realratio[i])
                                yearincome.append(integer*new_product.productRatio[i])
                                needinvest = needinvest - integer
                            pass
                        
                        pass
                    else :                        
                        remainder = tmpinvest%new_product.perIncAmount[i]
                        integer   = tmpinvest - remainder
                        
                        if round(1.0*remainder/new_product.perIncAmount[i], 2) == 0:
                            investproduct.append(new_product.productId[i])
                            usedcoupon.append('')
                            couponvalue.append(0)
                            realrate.append(1.0*new_product.realratio[i])
                            yearrate.append(new_product.productRatio[i])
                            
                            investamount.append(tmpinvest)
                            realincome.append(tmpinvest*1.0*new_product.realratio[i])
                            yearincome.append(tmpinvest*new_product.productRatio[i])
                            needinvest = needinvest - tmpinvest
                            pass
                        else :
                            if integer >= new_product.minInvestAmount[i] :
                                
                                investproduct.append(new_product.productId[i])
                                usedcoupon.append('')
                                couponvalue.append(0)
                                realrate.append(1.0*new_product.realratio[i])
                                yearrate.append(new_product.productRatio[i]) 
                                
                                investamount.append(integer)
                                realincome.append(integer*1.0*new_product.realratio[i])
                                yearincome.append(integer*new_product.productRatio[i])
                                needinvest = needinvest - integer
                                pass
                            pass
                        pass
                    new_product = new_product.loc[xrange(i+1, len(new_product)), :]
                    new_product.index = xrange(len(new_product))
                    break
                else :
                    new_product = new_product.loc[xrange(i+1, len(new_product)), :]
                    new_product.index = xrange(len(new_product))
                    break

        
        nocouponresult['productId'] = investproduct
        nocouponresult['investAmount'] = investamount
        nocouponresult['couponId'] = usedcoupon
        nocouponresult['incomeTotal'] = realincome

        if len(investproduct) == 0:
            #print("Warning: No Optimize Investment Satisfied !!! \n")
            sys.exit(12)
                
        return nocouponresult    
    
    def usecoupon(self, needinvest, deadline):
        
        """--- Coupon Model ---"""
        topk = 0
        result_coupon = []
        result_nocoupon = []
        unused_coupon   = pd.DataFrame()
        investresult = pd.DataFrame()
        # 1. Choose coupons which satisfy [duedays <= deadline and real_start <= needinvest ]
        #unused_coupon = self.coupon[self.coupon.deadline <= deadline]
        if len(self.coupon) > 0:
            unused_coupon = self.coupon[self.coupon.couponMinInvestAmount <= needinvest]
            unused_coupon.index = xrange(len(unused_coupon))
        # 2. Choose product which satisfy [duedays <= deadline and starting <= needinvest ]
        new_product = self.product[self.product.productDueDays <= deadline]
        if len(new_product) > 0:
            #new_product =  tmp_product[tmp_product.starting <= needinvest]
            new_product.index = xrange(len(new_product))
            pass
        else :
            #print "No Product Satisfy Your Input, Please Use longer Deadline !!!"
            sys.exit(22)
        
        #print new_product
        #print unused_coupon
        couponresult = pd.DataFrame()
        nocouponresult = pd.DataFrame()
        investproduct = []
        usedcoupon    = []
        couponvalue   = []
        realrate    = []
        realincome  = []
        yearrate = []
        yearincome = []
        investamount    = []
        
        newer_product = new_product[new_product.forNewMemberFlag == True]        
        
        # Just for Freshman 
        if len(newer_product) > 0 :
            newer_product = newer_product[newer_product.minInvestAmount <= needinvest]
            # is a freshman,  first select a best product, then select a best coupon for freahman
            
            if len(newer_product) >0 :
                for ij in list(newer_product.index):
                    new_product = new_product.drop(ij)
                    pass
                
                newer_product.index = xrange(len(newer_product))
                                
                if len(unused_coupon) > 0:
                    newer_coupon   = productMatchCoupon(newer_product.loc[0], unused_coupon)
                    pass
                else :
                    newer_coupon = pd.DataFrame()
                    pass
                if len(newer_coupon) > 0:
                    newer_coupon  = newer_coupon[newer_coupon.couponMinInvestAmount <= min(newer_product.maxInvestAmount[0], newer_product.remainInvestAmount[0])]
                    newer_coupon  = newer_coupon.sort_values(by = ["couponMinInvestAmount", "rate"], ascending=[False, False])
                    newer_coupon.index = xrange(len(newer_coupon))
                    #print "##############"
                    #print newer_coupon
                    if len(newer_coupon) > 0:
                        for step in xrange(len(newer_coupon)) :
                            if newer_coupon.couponMinInvestAmount[step] <= needinvest :
                                investproduct.append(newer_product.productId[0])
                                usedcoupon.append(newer_coupon.couponId[step])
                                couponvalue.append(newer_coupon.couponAmount[step])
                                realrate.append(1.0*newer_product.realratio[0])
                                yearrate.append(newer_product.productRatio[0])
                                useed_coupon = unused_coupon[unused_coupon.couponId == newer_coupon.couponId[step]].index
                                unused_coupon   = unused_coupon.drop(useed_coupon[0])
                                unused_coupon.index = xrange(len(unused_coupon))
                                
                                tmpinvest = min(newer_product.maxInvestAmount[0], newer_product.remainInvestAmount[0])
                                if tmpinvest <= needinvest :
                                    #integer   = round(newer_product.maxInvestAmount[0]/newer_product.perIncAmount[0],0)
                                    remainder = tmpinvest%newer_product.perIncAmount[0]
                                    integer =  tmpinvest- remainder
                                    if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                                        investamount.append(tmpinvest)
                                        realincome.append(tmpinvest*1.0*newer_product.realratio[0] + newer_coupon.couponAmount[step])
                                        yearincome.append(tmpinvest*newer_product.productRatio[0] + newer_coupon.couponAmount[step])
                                        needinvest = needinvest - tmpinvest + newer_coupon.couponAmount[step]
                                        pass
                                    else :
                                        if integer >= newer_product.minInvestAmount[0] :
                                            investamount.append(integer)
                                            realincome.append(integer*1.0*newer_product.realratio[0] + newer_coupon.couponAmount[step])
                                            yearincome.append(integer*newer_product.productRatio[0] + newer_coupon.couponAmount[step])
                                            needinvest = needinvest - integer + newer_coupon.couponAmount[step]
                                        pass
                                    pass
                                else :
                                    remainder = needinvest%newer_product.perIncAmount[0]
                                    integer   = needinvest - remainder
                                    if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                                        investamount.append(needinvest)
                                        realincome.append(needinvest*1.0*newer_product.realratio[0] + newer_coupon.couponAmount[step])
                                        yearincome.append(needinvest*newer_product.productRatio[0] + newer_coupon.couponAmount[step])
                                        needinvest    = 0
                                        pass
                                    else :
                                        if integer >= newer_product.minInvestAmount[0] :
                                            investamount.append(integer)
                                            realincome.append(integer*1.0*newer_product.realratio[0] + newer_coupon.couponAmount[step])
                                            yearincome.append(integer*newer_product.productRatio[0] + newer_coupon.couponAmount[step])
                                            needinvest = needinvest - integer+ newer_coupon.couponAmount[step]
                                        pass
                                    pass
                                break
                            pass
                        pass
                    else :
                        #print '333333333'
                        investproduct.append(newer_product.loc[0,'productId'])
                        usedcoupon.append('')
                        couponvalue.append(0)
                        realrate.append(1.0*newer_product.loc[0, 'realratio'])
                        yearrate.append(newer_product.loc[0, 'productRatio'])
                        
                        tmp_invest = min(newer_product.loc[0, 'maxInvestAmount'], newer_product.loc[0, "remainInvestAmount"])
                        
                        if tmp_invest <= needinvest:
                            #integer   = round(tmp_invest/newer_product.perIncAmount[0],0)
                            remainder = tmp_invest%newer_product.loc[0,'perIncAmount']
                            integer   = tmp_invest - remainder
                            
                            if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                                investamount.append(tmp_invest)
                                realincome.append(tmp_invest*1.0*newer_product.realratio[0])
                                yearincome.append(tmp_invest*newer_product.productRatio[0])
                                needinvest = needinvest - tmp_invest
                                pass
                            else :
                                if integer >= newer_product.minInvestAmount[0] :
                                    investamount.append(integer)
                                    realincome.append(integer*1.0*newer_product.realratio[0])
                                    yearincome.append(integer*newer_product.productRatio[0])
                                    needinvest = needinvest - integer
                                pass
                            pass
                        else :
                            remainder = needinvest%newer_product.perIncAmount[0]
                            integer   = needinvest - remainder
                            if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                                investamount.append(needinvest)
                                realincome.append(needinvest*1.0*newer_product.realratio[0])
                                yearincome.append(needinvest*newer_product.productRatio[0])
                                needinvest    = 0
                                pass
                            else :
                                if integer >= newer_product.minInvestAmount[0] :
                                    investamount.append(integer)
                                    realincome.append(integer*1.0*newer_product.realratio[0])
                                    yearincome.append(integer*newer_product.productRatio[0])
                                    needinvest = needinvest - integer
                                pass
                            pass
                        pass
                    pass
                else :
                    investproduct.append(newer_product.productId[0])
                    usedcoupon.append('')
                    couponvalue.append(0)
                    realrate.append(1.0*newer_product.realratio[0])
                    yearrate.append(newer_product.productRatio[0])
                    #print '333333333'
                    tmp_invest = min(newer_product.maxInvestAmount[0], newer_product.remainInvestAmount[0])  
                    if tmp_invest <= needinvest:
                        remainder = tmp_invest%newer_product.perIncAmount[0]
                        integer   = tmp_invest - remainder                        
                        if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                            investamount.append(tmp_invest)
                            realincome.append(tmp_invest*1.0*newer_product.realratio[0])
                            yearincome.append(tmp_invest*newer_product.productRatio[0])
                            needinvest    = needinvest - tmp_invest 
                            pass
                        else :
                            if integer >= newer_product.minInvestAmount[0] :
                                investamount.append(integer)
                                realincome.append(integer*1.0*newer_product.realratio[0])
                                yearincome.append(integer*newer_product.productRatio[0])
                                needinvest = needinvest - integer
                            pass
                        pass
                    else :
                        remainder = needinvest%newer_product.perIncAmount[0]
                        integer   = needinvest - remainder                        
                        if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                            investamount.append(needinvest)
                            realincome.append(needinvest*1.0*newer_product.realratio[0])
                            yearincome.append(needinvest*newer_product.productRatio[0])
                            needinvest    = 0
                            pass
                        else :
                            if integer >= newer_product.minInvestAmount[0] :
                                investamount.append(integer)
                                realincome.append(integer*1.0*newer_product.realratio[0])
                                yearincome.append(integer*newer_product.productRatio[0])
                                needinvest = needinvest - integer
                            pass
                        pass
                    pass
                pass
            pass
        
        iter = 0
        maxiter = len(unused_coupon)
        while ( len(unused_coupon) > 0 and iter <= maxiter) :
            iter += 1
            coupon_0 = unused_coupon.loc[0]

            if "allProductSupportFlag" in list(pd.DataFrame(coupon_0).index) :
                if coupon_0['allProductSupportFlag'] == True :
                    tmp_product = new_product
                    pass
                else :
                    tmp_product = couponMatchPorduct(coupon_0, new_product)
                    pass
                pass
            else :
                tmp_product = couponMatchPorduct(coupon_0, new_product)                     
                pass
            
            #tmp_product = tmp_product[tmp_product.minInvestAmount >= (unused_coupon.loc[0,'couponMinInvestAmount'] - unused_coupon.loc[0,'couponAmount'])]
            tmp_product = tmp_product[tmp_product.minInvestAmount <= needinvest]
            tmp_product = tmp_product[tmp_product.maxInvestAmount >= unused_coupon.loc[0,'couponMinInvestAmount']]

            if len(tmp_product) > 0 :

                if len(unused_coupon) == 1:
                    tmp_product = tmp_product.sort_values(by = ["realratio","minInvestAmount"], ascending=[False, False])
                    tmp_product.index = xrange(len(tmp_product))
                    pass
                else :
                    tmp_product = tmp_product.sort_values(by = ["realratio","minInvestAmount"], ascending=[False, True])
                    tmp_product.index = xrange(len(tmp_product))
                    pass
                
                for i in xrange(len(tmp_product)) :
                    real_invest = max(unused_coupon.couponMinInvestAmount[0], tmp_product.minInvestAmount[i])
                    if needinvest >= real_invest :

                        if len(unused_coupon) == 1:
                            if needinvest - 2*real_invest > 0:
                                remainder = real_invest%tmp_product.perIncAmount[i]
                                integer   = real_invest - remainder
                                if round(1.0*remainder/tmp_product.perIncAmount[i], 2) == 0:
                                    if real_invest <= tmp_product.maxInvestAmount[i]:
                                        investamount.append(real_invest)
                                        realincome.append(real_invest*1.0*tmp_product.realratio[i] + unused_coupon.couponAmount[0])
                                        yearincome.append(real_invest*tmp_product.productRatio[i] + unused_coupon.couponAmount[0])
                                        needinvest = needinvest - real_invest
                                        
                                        investproduct.append(tmp_product.productId[i])
                                        usedcoupon.append(unused_coupon.couponId[0])
                                        couponvalue.append(unused_coupon.couponAmount[0])
                                        realrate.append(1.0*tmp_product.realratio[i])
                                        yearrate.append(tmp_product.productRatio[i])
                                        
                                        used_product = new_product[new_product.productId == tmp_product.loc[i, 'productId']].index
                                        new_product.loc[ used_product[0], "maxInvestAmount"] -= real_invest

                                        pass
                                    pass
                                pass
                            else :
                                
                                tmp_invest = min(needinvest, tmp_product.maxInvestAmount[i])
                                
                                if tmp_invest >= real_invest :
                                    remainder = tmp_invest%tmp_product.perIncAmount[i]
                                    integer   = tmp_invest - remainder
                                    
                                    if round(1.0*remainder/tmp_product.perIncAmount[i], 2) == 0:
                                        investamount.append(tmp_invest)
                                        realincome.append(tmp_invest*1.0*tmp_product.realratio[i] + unused_coupon.couponAmount[0])
                                        yearincome.append(tmp_invest*tmp_product.productRatio[i] + unused_coupon.couponAmount[0])
                                        needinvest = needinvest - tmp_invest
                                        
                                        investproduct.append(tmp_product.productId[i])
                                        usedcoupon.append(unused_coupon.couponId[0])
                                        couponvalue.append(unused_coupon.couponAmount[0])
                                        realrate.append(1.0*tmp_product.realratio[i])
                                        yearrate.append(tmp_product.productRatio[i])
                                        
                                        used_product = new_product[new_product.productId == tmp_product.loc[i, 'productId']].index
                                        new_product.loc[ used_product[0], "maxInvestAmount"] -= tmp_invest

                                        pass
                                    else :                                        
                                        if real_invest <= integer:
                                            investamount.append(integer)
                                            realincome.append(integer*1.0*tmp_product.loc[i, 'realratio'] + unused_coupon.loc[0, 'couponAmount'])
                                            yearincome.append(integer*tmp_product.loc[i, 'productRatio'] + unused_coupon.loc[0, 'couponAmount'])
                                            needinvest = needinvest - integer
                                            
                                            investproduct.append(tmp_product.loc[i, 'productId'])
                                            usedcoupon.append(unused_coupon.loc[0, 'couponId'])
                                            couponvalue.append(unused_coupon.loc[0, 'couponAmount'])
                                            realrate.append(1.0*tmp_product.loc[i, 'realratio'])
                                            yearrate.append(tmp_product.loc[i, 'productRatio'])
                                            
                                            used_product = new_product[new_product.productId == tmp_product.loc[i,'productId']].index
                                            new_product.loc[ used_product[0], "maxInvestAmount"] -= integer
                                            pass
                                        pass
                                    pass
                                pass
                            pass
                        else :                            
                            remainder = real_invest%tmp_product.perIncAmount[i]
                            integer   = real_invest - remainder
                            
                            if round(1.0*remainder/tmp_product.perIncAmount[i], 2) == 0:
                                if real_invest <= tmp_product.loc[i, 'maxInvestAmount'] :
                                    investamount.append(real_invest)
                                    realincome.append(real_invest*1.0*tmp_product.realratio[i] + unused_coupon.couponAmount[0])
                                    yearincome.append(real_invest*tmp_product.productRatio[i] + unused_coupon.couponAmount[0])
                                    needinvest = needinvest - real_invest
                                    
                                    used_product = new_product[new_product.productId == tmp_product.loc[i,'productId']].index
                                    new_product.loc[ used_product[0], "maxInvestAmount"] -= real_invest
                                    
                                    investproduct.append(tmp_product.productId[i])
                                    usedcoupon.append(unused_coupon.couponId[0])
                                    couponvalue.append(unused_coupon.couponAmount[0])
                                    realrate.append(1.0*tmp_product.realratio[i])
                                    yearrate.append(tmp_product.productRatio[i])
                                    pass
                                pass
                            pass
                        unused_coupon = unused_coupon.drop(0)
                        unused_coupon.index = xrange(len(unused_coupon))
                        new_product.loc[:,'check'] = new_product.maxInvestAmount - new_product.minInvestAmount
                        new_product = new_product[new_product.check >= 0]
                        del new_product['check']
                        new_product.index = xrange(len(new_product))
                        break
                        pass
                    else :
                        if i < (len(tmp_product) - 1) :
                            pass
                        else :
                            unused_coupon = unused_coupon.drop(0)
                            unused_coupon.index = xrange(len(unused_coupon))
                            new_product['check'] = new_product.maxInvestAmount - new_product.minInvestAmount
                            new_product = new_product[new_product.check >= 0]
                            del new_product['check']
                            new_product.index = xrange(len(new_product))
                            break
                            pass
                        pass
                    pass
                pass            
            else :
                unused_coupon = unused_coupon.drop(0)
                unused_coupon.index = xrange(len(unused_coupon))
                pass

        new_product['check'] = new_product.maxInvestAmount - new_product.minInvestAmount
        new_product = new_product[new_product.check >= 0]
        del new_product['check']
        new_product.index = xrange(len(new_product))
        
        if len(new_product) > 0:
            if needinvest >= min(new_product.minInvestAmount):
                nocouponresult = self.nocoupon(needinvest, deadline, new_product)

        couponresult['productId'] = investproduct
        couponresult['investAmount'] = investamount
        couponresult['couponId'] = usedcoupon
        couponresult['incomeTotal'] = realincome        
        investment = couponresult.append(nocouponresult)
        investment.index = xrange(len(investment))
        investment = cleaninvest(investment)
        
        jsonresult = ''
        
        if len(investment) > 0:
            for tt in xrange(len(investment)):
                if tt == 0 :
                    jsonresult = pd.DataFrame.to_json(pd.DataFrame(investment.loc[tt]))
                    pass
                else :
                    tmpjosn = pd.DataFrame.to_json(pd.DataFrame(investment.loc[tt]))
                    jsonresult = jsonresult[:-1] +',' +tmpjosn[1:]
                    pass
                pass
            pass

        return jsonresult
    
    
    def invest(self, needinvest, deadline):
        
        """--- Optimize Invest --- 
        IF User has coupons, then Coupon Model
        IF User doesn't have coupon, then use No Coupon model
        """
        
        result = self.usecoupon(needinvest, deadline)
        
        return result

def tips():
	"""Display the usage tips"""
	print "Please use: "+sys.argv[0]+" [options]"
	print "usage:%s --product=value --coupon=value --investamount=value --terminal=value"
	print "usage:%s -p value -c value -i value -t value "
	sys.exit(2)

def validateopts(opts):
    for option, value in opts:
        if option  in ["-h", "--help"]:
            tips()
        elif option in ["--product", "-p"]:
            product = str(value)
        elif option in ["--coupon", "-c"]:
            coupon = str(value)
        elif option in ['--investamount', "-i"]:
            investamount = int(value)
        elif option in ['--terminal', '-t']:
            deadline = int(value)
            pass
        pass
    return product, coupon, investamount, deadline
  
def main():
    
    try:
        opts,args = getopt.getopt(sys.argv[1:],"hp:c:i:t:d",["product=","coupon=","investamount=","terminal=","help"])
        pass
    except getopt.GetoptError:
        #tips()
        pass
    
    #print "*******************"
    #print opts
    
    if len(opts) >= 1:
        product, coupon, investamount, deadline = validateopts(opts)
        pass
    else:
        #print "ErrorMessage: Please Check What Your Input !"
        #tips()
        sys.exit(2)
        pass
    
    #print "product      = " + product
    #print "coupon       = " + coupon
    #print "investamount = " + str(investamount)
    #print "deadline     = " + str(deadline)
    
    optime = optimizeInvest(product=product, coupon=coupon)
    result = optime.invest(investamount, deadline)
    print result
    #os.environ['result'] = result
    #os.system('echo $result')

if __name__ == '__main__':
    
    start_CPU = time.clock()
    t1 = time.time()
    main()
    end_CPU = time.clock()
    t2 = time.time()
    print "CPU Costs   : %f seconds" %  (end_CPU - start_CPU)
    print "Total Costs : %f seconds" % (t2 - t1)
	
	
