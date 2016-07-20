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
    category = ['allProductSupportFlag', 'firstCategoryId', 'secondCategoryId', 'thirdCategoryId', 'fouthCategoryId']
    selectcoupon = pd.DataFrame()
    dropcoupon = pd.DataFrame()
    for j, name in enumerate(list(pd.DataFrame(product_0 ).index)):
        if name in category :
            if name == 'allProductSupportFlag' :
                if coupon.loc[j, 'allProductSupportFlag'] == True :
                    selectcoupon = selectcoupon.append(coupon.loc[j])
                    pass
                else :
                    for i in xrange(len(coupon['supportCategoryVoList'])):
                        item = pd.DataFrame(coupon['supportCategoryVoList'][i])
                        column = list(item.columns)
                        if name in column :
                            underselectcoupon = item[item[name] == product_0[name]]
                            if len(underselectcoupon) > 0 :
                                aaa = list(underselectcoupon['supportFlag'])
                                if aaa[0] :
                                    selectcoupon = selectcoupon.append(coupon.loc[i])
                                else :
                                    dropcoupon = dropcoupon.append(coupon.loc[i])
    
    #print selectcoupon
    if len(selectcoupon) > 0:
        del selectcoupon['supportCategoryVoList']
    
    if len(dropcoupon) > 0:
        del dropcoupon['supportCategoryVoList']
    
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
                if product.forNewMemberFlag[ii] == True :
                    if product.maxInvestAmount[ii] == -1 :
                        product.loc[ ii,'maxInvestAmount'] = product.loc[ii,'remainInvestAmount']
                        
            product = product.sort_values(by = ["productRatio", "productDueDays", "minInvestAmount", "maxInvestAmount"], ascending=[False, True, True, False])
            product['realratio'] = 1.0*product.productRatio*product.productDueDays/365
            product['check'] =  product.remainInvestAmount - product.minInvestAmount
            product = product[product.check >= 0]
            product.index = xrange(len(product))
            self.product = product

        if 'coupon' in kwargs.keys():
            coupon_loc = kwargs['coupon']
            coupon  = pd.DataFrame(json.loads(coupon_loc))
            if len(coupon) > 0:
                coupon['rate'] = 1.0*coupon.couponAmount/(coupon.couponMinInvestAmount - coupon.couponAmount)
                coupon['real_start'] = coupon.couponMinInvestAmount - coupon.couponAmount
                #print coupon
                coupon = coupon.sort_values(by = ['rate', 'real_start'], ascending = [False, True])
                coupon.index = xrange(len(coupon))
                self.coupon = coupon
            
            #print 'self.coupon ='
            #print self.coupon 
        
        if len(self.product) == 0:
            print("Error: The Product list is empty !!!")
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
        inititer = 0
        while (needinvest > 0) and len(new_product) > 0 and inititer < 20:
            inititer += 1
            for i in xrange(len(new_product)):
                if needinvest >= new_product.minInvestAmount[i] :
                
                    if new_product.maxInvestAmount[i] == -1 :
                        tmpinvest = new_product.remainInvestAmount[i]
                    else :
                        tmpinvest = min(new_product.remainInvestAmount[i], new_product.maxInvestAmount[i])

                    if needinvest <= tmpinvest :
                        
                        investproduct.append(new_product.productId[i])
                        usedcoupon.append('')
                        couponvalue.append(0)
                        realrate.append(1.0*new_product.realratio[i])
                        yearrate.append(1.0*new_product.productRatio[i])                        
                        
                        #integer   = round(needinvest/new_product.perIncAmount[i], 0)
                        remainder = needinvest%new_product.perIncAmount[i]                        
                        integer   = needinvest - remainder
                        
                        #print needinvest
                        #print "integer === "
                        #print integer
                        #print "remainder ===="
                        #print remainder
                        
                        if round(1.0*remainder/new_product.perIncAmount[i], 2) == 0:
                            #print "11111111"
                            investamount.append(needinvest)                            
                            realincome.append(needinvest*1.0*new_product.realratio[i])
                            yearincome.append(needinvest*new_product.productRatio[i])
                            needinvest = 0
                            pass
                        else :
                            #print "2222222"
                            investamount.append(integer)
                            realincome.append(integer*1.0*new_product.realratio[i])
                            yearincome.append(integer*new_product.productRatio[i])
                            needinvest = needinvest - integer
                            pass
                        
                        pass
                    else :
                        investproduct.append(new_product.productId[i])
                        usedcoupon.append('')
                        couponvalue.append(0)
                        realrate.append(1.0*new_product.realratio[i])                        
                        yearrate.append(new_product.productRatio[i])                        
                        #integer   = round(new_product.remainInvestAmount[i]/new_product.perIncAmount[i],0)
                        remainder = tmpinvest%new_product.perIncAmount[i]
                        integer   = tmpinvest - remainder
                        
                        if round(1.0*remainder/new_product.perIncAmount[i], 2) == 0:
                            investamount.append(tmpinvest)
                            realincome.append(tmpinvest*1.0*new_product.realratio[i])
                            yearincome.append(tmpinvest*new_product.productRatio[i])
                            needinvest = needinvest - tmpinvest
                            pass
                        else :
                            if integer >= new_product.minInvestAmount[i] :
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
        nocouponresult['investAmount'] = [round(i,2) for i in investamount]
        nocouponresult['couponId'] = usedcoupon
        #nocouponresult['couponvalue'] = couponvalue
        #nocouponresult['realrate'] = [round(i,3) for i in realrate]
        nocouponresult['incomeTotal'] = [round(i,2) for i in realincome]
        #nocouponresult['yearrate'] = yearrate
        #nocouponresult['yearincome'] = [round(i, 2) for i in yearincome]

        if len(investproduct) == 0:
            #print("Warning: No Optimize Investment Satisfied !!! \n")
            #print("===================================================")
            sys.exit(22)
                
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
        
        #for ii in range(len(newer_product)):
        #    if newer_product.maxInvestAmount[ii] == -1 :
        #        newer_product.loc[ii, 'maxInvestAmount'] = newer_product.remainInvestAmount[ii]
        #newer_product = newer_product[newer_product.minInvestAmount <= needinvest]
        #print newer_product
        #print unused_coupon
        
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
                                        realincome.append(tmpinvest*1.0*newer_product.realratio[0])
                                        yearincome.append(tmpinvest*newer_product.productRatio[0])
                                        needinvest = needinvest - tmpinvest + newer_coupon.couponAmount[step]
                                        pass
                                    else :
                                        if integer >= newer_product.minInvestAmount[0] :
                                            investamount.append(integer)
                                            realincome.append(integer*1.0*newer_product.realratio[0])
                                            yearincome.append(integer*newer_product.productRatio[0])
                                            needinvest = needinvest - integer + newer_coupon.couponAmount[step]
                                        pass
                                    pass
                                else :
                                    #integer   = round(newer_product.remainInvestAmount[0]/newer_product.perIncAmount[0],0)
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
                                            needinvest = needinvest - integer+ newer_coupon.couponAmount[step]
                                        pass
                                    pass
                                break
                            pass
                        pass
                    else :
                        #print '333333333'
                        investproduct.append(newer_product.productId[0])
                        usedcoupon.append('')
                        couponvalue.append(0)
                        realrate.append(1.0*newer_product.realratio[0])
                        yearrate.append(newer_product.productRatio[0])
                        tmp_invest = min(newer_product.maxInvestAmount[0], newer_product.remainInvestAmount[0])
                        
                        if tmp_invest <= needinvest:
                            #integer   = round(tmp_invest/newer_product.perIncAmount[0],0)
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
                            #integer   = round(needinvest/newer_product.perIncAmount[0],0)
                            remainder = needinvest%newer_product.perIncAmount[0]
                            integer   = needinvest - remainder
                            if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                                investamount.append(needinvest)
                                realincome.append(needinvest*1.0*newer_product.realratio[0])
                                yearincome.append(needinvest*newer_product.productRatio[0])
                                needinvest = 0
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
                        #print "444444"
                        #integer   = round(tmp_invest/newer_product.perIncAmount[0],0)
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
                        #integer   = round(needinvest/newer_product.perIncAmount[0],0)
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
        #print "&&&&&&&&&&&&&&&&&&&&&&&&&"
        #print unused_coupon
                
        iter = 0
        while ( len(unused_coupon) > 0 and iter <= 15) :
            iter += 1
            #print iter
            #print "needinvest   = " +str(needinvest)
            # calculate best product for each coupon one by one 
            coupon_0 = unused_coupon.loc[0]
            
            if "allProductSupportFlag" in list(pd.DataFrame(coupon_0).index) :
                if coupon_0['allProductSupportFlag'] == True :
                    tmp_product = new_product
                    pass
                pass
            else :
                tmp_product = couponMatchPorduct(coupon_0, new_product)                     
                pass
            tmp_product = tmp_product[tmp_product.minInvestAmount >= (unused_coupon.couponMinInvestAmount[0] - unused_coupon.couponAmount[0])]
            tmp_product = tmp_product[tmp_product.minInvestAmount <= needinvest]

            if len(tmp_product) > 0 :

                if len(unused_coupon) == 1:
                    tmp_product = tmp_product.sort_values(by = ["minInvestAmount", "productRatio"], ascending=[False, False])
                    tmp_product.index = xrange(len(tmp_product))
                    pass
                else :
                    tmp_product = tmp_product.sort_values(by = ["minInvestAmount", "productRatio"], ascending=[True, False])
                    tmp_product.index = xrange(len(tmp_product))
                    pass
                
                for i in xrange(len(tmp_product)) :
                    real_invest = max(unused_coupon.couponMinInvestAmount[0], tmp_product.minInvestAmount[i])
                    if needinvest >= (real_invest - unused_coupon.couponAmount[0]) :

                        if len(unused_coupon) == 1:
                            if needinvest - 2*real_invest > 0:
                                remainder = real_invest%tmp_product.perIncAmount[i]
                                integer   = real_invest - remainder
                                if round(1.0*remainder/tmp_product.perIncAmount[i], 2) == 0:
                                    if real_invest <= tmp_product.remainInvestAmount[i]:
                                        investamount.append(real_invest)
                                        realincome.append(real_invest*1.0*tmp_product.realratio[i])
                                        yearincome.append(real_invest*tmp_product.productRatio[i])
                                        needinvest = needinvest - real_invest
                                        
                                        investproduct.append(tmp_product.productId[i])
                                        usedcoupon.append(unused_coupon.couponId[0])
                                        couponvalue.append(unused_coupon.couponAmount[0])
                                        realrate.append(1.0*tmp_product.realratio[i])
                                        yearrate.append(tmp_product.productRatio[i])
                                        
                                        used_product = new_product[new_product.productId == tmp_product.productId[i]].index
                                        new_product.loc[ used_product[0], "remainInvestAmount"] -= real_invest

                                        pass
                                    pass
                                pass
                            else :
                                
                                tmp_invest = min(needinvest, tmp_product.remainInvestAmount[i])
                                
                                if tmp_invest >= real_invest :
                                    remainder = tmp_invest%tmp_product.perIncAmount[i]
                                    integer   = tmp_invest - remainder
                                    
                                    if round(1.0*remainder/tmp_product.perIncAmount[i], 2) == 0:
                                        investamount.append(tmp_invest)
                                        realincome.append(tmp_invest*1.0*tmp_product.realratio[i])
                                        yearincome.append(tmp_invest*tmp_product.productRatio[i])
                                        needinvest = needinvest - tmp_invest
                                        
                                        investproduct.append(tmp_product.productId[i])
                                        usedcoupon.append(unused_coupon.couponId[0])
                                        couponvalue.append(unused_coupon.couponAmount[0])
                                        realrate.append(1.0*tmp_product.realratio[i])
                                        yearrate.append(tmp_product.productRatio[i])
                                        
                                        used_product = new_product[new_product.productId == tmp_product.productId[i]].index
                                        new_product.loc[ used_product[0], "remainInvestAmount"] -= tmp_invest

                                        pass
                                    else :                                        
                                        if real_invest <= integer:
                                            investamount.append(integer)
                                            realincome.append(integer*1.0*tmp_product.realratio[i])
                                            yearincome.append(integer*tmp_product.productRatio[i])
                                            needinvest = needinvest - integer
                                            
                                            investproduct.append(tmp_product.productId[i])
                                            usedcoupon.append(unused_coupon.couponId[0])
                                            couponvalue.append(unused_coupon.couponAmount[0])
                                            realrate.append(1.0*tmp_product.realratio[i])
                                            yearrate.append(tmp_product.productRatio[i])
                                            
                                            used_product = new_product[new_product.productId == tmp_product.productId[i]].index
                                            new_product.loc[ used_product[0], "remainInvestAmount"] -= integer 

                                            pass
                                        pass
                                    pass
                                pass
                            pass
                        else :
                            
                            remainder = real_invest%tmp_product.perIncAmount[i]
                            integer   = real_invest - remainder
                            
                            if round(1.0*remainder/tmp_product.perIncAmount[i], 2) == 0:
                                if real_invest <= tmp_product.remainInvestAmount[i] :
                                    investamount.append(real_invest)
                                    realincome.append(real_invest*1.0*tmp_product.realratio[i])
                                    yearincome.append(real_invest*tmp_product.productRatio[i])
                                    needinvest = needinvest - real_invest
                                    
                                    used_product = new_product[new_product.productId == tmp_product.productId[i]].index
                                    new_product.loc[ used_product[0], "remainInvestAmount"] -= real_invest
                                    
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
                        new_product['check'] = new_product.remainInvestAmount - new_product.minInvestAmount
                        new_product = new_product[new_product.check >= 0]
                        new_product.index = xrange(len(new_product)) 
                        break
                        pass
                    else :
                        if i < (len(tmp_product) - 1) :
                            pass
                        else :
                            unused_coupon = unused_coupon.drop(0)
                            unused_coupon.index = xrange(len(unused_coupon))
                            new_product['check'] = new_product.remainInvestAmount - new_product.minInvestAmount
                            new_product = new_product[new_product.check >= 0]
                            new_product.index = xrange(len(new_product))
                            break
                            pass
                        pass
                    pass
                pass
            else :
                unused_coupon = unused_coupon.drop(0)
                unused_coupon.index = xrange(len(unused_coupon))
                new_product['check'] = new_product.remainInvestAmount - new_product.minInvestAmount
                new_product = new_product[new_product.check >= 0]
                new_product.index = xrange(len(new_product))                
                break
                pass

        new_product['check'] = new_product.remainInvestAmount - new_product.minInvestAmount
        new_product = new_product[new_product.check >= 0]
        new_product.index = xrange(len(new_product))
        
        
        if len(new_product) > 0:
            if needinvest >= min(new_product.minInvestAmount):
                nocouponresult = self.nocoupon(needinvest, deadline, new_product)

        couponresult['productId'] = investproduct
        couponresult['investAmount'] = investamount
        couponresult['couponId'] = usedcoupon
        #couponresult['couponvalue'] = couponvalue
        #couponresult['realrate'] = [round(i, 3) for i in realrate]
        couponresult['incomeTotal'] = [round(i, 2) for i in realincome]
        #couponresult['yearrate'] = yearrate
        #couponresult['yearincome'] = [round(i, 2) for i in yearincome]
        
        #print couponresult
        #print "*"*30
        #print nocouponresult
        
        investment = couponresult.append(nocouponresult)
        investment.index = xrange(len(investment))
        investment = cleaninvest(investment)
        
        #print nocouponresult
        #print "  *********** The Final Investment *********** \n"
        #print investment
        
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
        
        #if len(self.coupon) == 0:            
        #    result = self.nocoupon(needinvest, deadline, self.product)
        #else :
        #    result = self.usecoupon(needinvest, deadline)
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
	
	
