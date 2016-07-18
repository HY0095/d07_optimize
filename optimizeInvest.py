import numpy as np
from scipy.optimize import minimize
import pandas as pd
import os
import sys
import json

def dotMultiply(a,b):
    """ dot multiply 
    example: A = [1, 2, 3], B = [2, 3, 4], then
    return C = [1*2, 2*3, 3*4] = [2, 6, 12]
    """
    result = []
    for i in np.arange(len(a)):
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
    for i in range(len(coupon_0['supportCategoryVoList'])):
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
    for name in list(pd.DataFrame(product_0 ).index):
        if name in category :
            for i in range(len(coupon['supportCategoryVoList'])):
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

class optimizeInvest(object):
    
    def __init__(self, **kwargs):
        
        self.coupon  = pd.DataFrame()
        self.product = pd.DataFrame()
        if 'product' in kwargs.keys():
            product_loc = kwargs['product']
            if not os.path.exists(product_loc) :
                print("Error : Produc file is not exists !!!")
                sys.exit(11)
            else :
                product  = pd.DataFrame(json.load(open(product_loc,'r')))
                product = product.sort_values(by = ["productRatio", "productDueDays", "minInvestAmount", "maxInvestAmount"], ascending=[False, True, True, False])
                product.index = range(len(product))
                self.product = product
                self.raw_investratio = [0 for i in range(len(product))]
                                
        if 'coupon' in kwargs.keys():
            coupon_loc = kwargs['coupon']
            if not os.path.exists(coupon_loc):
                print("Error : Coupon file is not exist !!!")
                sys.exit(11)
            else :
                coupon  = pd.DataFrame(json.load(open(coupon_loc,'r')))
                coupon['rate'] = 1.0*coupon.couponAmount/(coupon.couponMinInvestAmount - coupon.couponAmount)
                coupon['real_start'] = coupon.couponMinInvestAmount - coupon.couponAmount
                #print coupon
                coupon = coupon.sort_values(by = ['rate', 'real_start'], ascending = [False, True])
                coupon.index = range(len(coupon))
                self.coupon = coupon
        
        if len(product) == 0:
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
        new_product.index = range(len(new_product))
        prod_cnt    = len(new_product)  
        product     = new_product        
        nocouponresult = pd.DataFrame()
        investproduct = []
        usedcoupon    = []
        couponvalue   = []
        #实际收益率  
        realrate    = []
        realincome  = []
        #年化收益率
        yearrate = []
        yearincome = []
        investamount = []        
                
        if prod_cnt == 0:
            print("Warning : No product satisfy the Deadline !!! \n")
            print("===================================================")
            print "\n ------ 非券投资组合 ------ \n"
            print("非券组合 = ....... \n")
            print("非券收益 = 0 " )            
            sys.exit(21)
        
        while (needinvest > 0) or len(new_product) == 0 :
            for i in range(len(new_product)):
                if needinvest >= new_product.minInvestAmount[i] :
                    if needinvest <= new_product.remainInvestAmount[i] :
                        
                        investproduct.append(new_product.productId[i])
                        usedcoupon.append('')
                        couponvalue.append(0)
                        realrate.append(1.0*new_product.productRatio[i]*new_product.productDueDays[i]/365)
                        yearrate.append(1.0*new_product.productRatio[i])                        
                        integer   = round(needinvest/new_product.perIncAmount[i], 0)
                        remainder = needinvest%new_product.perIncAmount[i]
                        
                        if round(1.0*remainder/new_product.perIncAmount[i], 2) == 0:
                            #print "11111111"
                            investamount.append(needinvest)                            
                            realincome.append(needinvest*1.0*new_product.productRatio[i]*new_product.productDueDays[i]/365)
                            yearincome.append(needinvest*new_product.productRatio[i])
                            needinvest = 0
                            pass
                        else :
                            #print "2222222"
                            investamount.append(integer*round(new_product.perIncAmount[i], 0))
                            realincome.append(integer*round(new_product.perIncAmount[i], 0)*1.0*new_product.productRatio[i]*new_product.productDueDays[0]/365)
                            yearincome.append(integer*round(new_product.perIncAmount[i], 0)*new_product.productRatio[i])
                            needinvest = needinvest - integer*round(new_product.perIncAmount[i], 0)
                            pass
                        
                        pass
                    else :
                        investproduct.append(new_product.productId[i])
                        usedcoupon.append('')
                        couponvalue.append(0)
                        realrate.append(1.0*new_product.productRatio[i]*new_product.productDueDays[i]/365)                        
                        yearrate.append(new_product.productRatio[i])                        
                        integer   = round(new_product.remainInvestAmount[i]/new_product.perIncAmount[i],0)
                        remainder = new_product.remainInvestAmount[i]%new_product.perIncAmount[i]
                        
                        if round(1.0*remainder/new_product.perIncAmount[i], 2) == 0:
                            investamount.append(new_product.remainInvestAmount[i])
                            realincome.append(new_product.remainInvestAmount[i]*1.0*new_product.productRatio[i]*new_product.productDueDays[0]/365)
                            yearincome.append(new_product.remainInvestAmount[i]*new_product.productRatio[i])
                            needinvest = needinvest - new_product.remainInvestAmount[i]
                            pass
                        else :
                            investamount.append(integer*round(new_product.perIncAmount[i], 0))
                            realincome.append(integer*round(new_product.perIncAmount[i], 0)*1.0*new_product.productRatio[i]*new_product.productDueDays[0]/365)
                            yearincome.append(integer*round(new_product.perIncAmount[i], 0)*new_product.productRatio[i])
                            needinvest = needinvest - integer*round(new_product.perIncAmount[i], 0)
                            pass
                        pass
                    new_product = new_product.loc[range(i+1, len(new_product)), :]
                    new_product.index = range(len(new_product))
                    break
                else :
                    new_product = new_product.loc[range(i+1, len(new_product)), :]
                    new_product.index = range(len(new_product))
                    break

        nocouponresult['investproduct'] = investproduct
        nocouponresult['investamount'] = [round(i,2) for i in investamount]
        nocouponresult['usedcoupon'] = usedcoupon
        nocouponresult['couponvalue'] = couponvalue
        nocouponresult['realrate'] = [round(i,3) for i in realrate]
        nocouponresult['realincome'] = [round(i,2) for i in realincome]
        nocouponresult['yearrate'] = yearrate
        nocouponresult['yearincome'] = [round(i, 2) for i in yearincome]

        if len(investproduct) == 0:
            print("Warning: No Optimize Investment Satisfied !!! \n")
            print("===================================================")
            print "\n ------ 非券投资组合 ------ \n"
            print("非券组合 = ....... \n")
            print("非券收益 = 0 ")
                
        return nocouponresult
    
    def usecoupon(self, needinvest, deadline):
        
        """--- Coupon Model ---"""
        topk = 0
        result_coupon = []
        result_nocoupon = []
        investresult = pd.DataFrame()
        # 1. Choose coupons which satisfy [duedays <= deadline and real_start <= needinvest ]
        #unused_coupon = self.coupon[self.coupon.deadline <= deadline]
        unused_coupon = self.coupon[self.coupon.couponMinInvestAmount <= needinvest]
        unused_coupon.index = range(len(unused_coupon))
        # 2. Choose product which satisfy [duedays <= deadline and starting <= needinvest ]
        new_product = self.product[self.product.productDueDays <= deadline]
        if len(new_product) > 0:
            #new_product =  tmp_product[tmp_product.starting <= needinvest]
            new_product.index = range(len(new_product))
            pass
        else :
            print "No Product Satisfy Your Input, Please Use longer Deadline !!!"
            sys.exit(22)
        
        #print new_product
        #print unused_coupon
        couponresult = pd.DataFrame()
        investproduct = []
        usedcoupon    = []
        couponvalue   = []
        #实际收益率 
        realrate    = []
        realincome  = []
        #年化收益率
        yearrate = []
        yearincome = []
        investamount    = []
        
        newer_product = new_product[new_product.forNewMemberFlag == True]
        newer_product = newer_product[newer_product.minInvestAmount <= needinvest]
        #print newer_product
        #print unused_coupon
        
        # Just for Freshman 
        if len(newer_product) > 0 :
            # is a freshman,  first select a best product, then select a best coupon for freahman
            
            for ij in list(newer_product.index):
                new_product = new_product.drop(ij)

            newer_coupon   = productMatchCoupon(newer_product.loc[0], unused_coupon)

            if len(newer_coupon) > 0:
                
                newer_coupon  = newer_coupon[newer_coupon.couponMinInvestAmount <= newer_product.maxInvestAmount[0]]
                newer_coupon  = newer_coupon.sort_values(by = ["couponMinInvestAmount", "rate"], ascending=[False, False])
                newer_coupon.index = range(len(newer_coupon))
                
                #print "##############"
                #print newer_coupon
                
                if len(newer_coupon) > 0:
                    for step in range(len(newer_coupon)) :
                        if newer_coupon.couponMinInvestAmount[step] <= needinvest :
                            investproduct.append(newer_product.productId[0])
                            usedcoupon.append(newer_coupon.couponId[step])
                            couponvalue.append(newer_coupon.couponAmount[step])
                            realrate.append(1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                            yearrate.append(newer_product.productRatio[0])
                            useed_coupon = unused_coupon[unused_coupon.couponId == newer_coupon.couponId[step]].index
                            
                            unused_coupon   = unused_coupon.drop(useed_coupon[0])
                            unused_coupon.index = range(len(unused_coupon))
                            
                            if newer_product.maxInvestAmount[0] <= needinvest :
                                
                                integer   = round(newer_product.maxInvestAmount[0]/newer_product.perIncAmount[0],0)
                                remainder = newer_product.maxInvestAmount[0]%newer_product.perIncAmount[0]    
                                
                                if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                                    investamount.append(newer_product.maxInvestAmount[0])
                                    realincome.append(newer_product.maxInvestAmount[0]*1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                                    yearincome.append(newer_product.maxInvestAmount[0]*newer_product.productRatio[0])
                                    needinvest = needinvest - newer_product.maxInvestAmount[0] + newer_coupon.couponAmount[step]
                                    pass
                                else :
                                    investamount.append(integer*newer_product.perIncAmount[0])
                                    realincome.append(integer*newer_product.perIncAmount[0]*1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                                    yearincome.append(integer*newer_product.perIncAmount[0]*newer_product.productRatio[0])
                                    needinvest = needinvest - integer*newer_product.perIncAmount[0] + newer_coupon.couponAmount[step]
                                    pass
                            else :
                                integer   = round(newer_product.remainInvestAmount[0]/newer_product.perIncAmount[0],0)
                                remainder = newer_product.remainInvestAmount[0]%newer_product.perIncAmount[0]
                                
                                if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                                    investamount.append(needinvest)
                                    realincome.append(needinvest*1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                                    yearincome.append(needinvest*newer_product.productRatio[0])
                                    needinvest    = 0
                                    pass
                                else :
                                    investamount.append(integer*new_product.perIncAmount[0])
                                    realincome.append(integer*new_product.perIncAmount[0]*1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                                    yearincome.append(integer*new_product.perIncAmount[0]*newer_product.productRatio[0])
                                    needinvest = needinvest - integer*new_product.perIncAmount[0] + newer_coupon.couponAmount[step]
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
                    realrate.append(1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                    yearrate.append(newer_product.productRatio[0])
                    
                    tmp_invest = min(newer_product.maxInvestAmount[0], newer_product.remainInvestAmount[0])
                    
                    print tmp_invest
                    
                    if tmp_invest <= needinvest:
                        
                        integer   = round(tmp_invest/newer_product.perIncAmount[0],0)
                        remainder = tmp_invest%newer_product.perIncAmount[0]
                        
                        if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                            investamount.append(tmp_invest)
                            realincome.append(tmp_invest*1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                            yearincome.append(tmp_invest*newer_product.productRatio[0])
                            needinvest    = needinvest - tmp_invest
                            pass
                        else :
                            investamount.append(integer*newer_product.perIncAmount[0])
                            realincome.append(integer*newer_product.perIncAmount[0]*1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                            yearincome.append(integer*newer_product.perIncAmount[0]*newer_product.productRatio[0])
                            needinvest = needinvest - integer*newer_product.perIncAmount[0]
                            pass
                        pass
                    else :
                        
                        integer   = round(needinvest/newer_product.perIncAmount[0],0)
                        remainder = needinvest%newer_product.perIncAmount[0]
                        
                        if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                            investamount.append(needinvest)
                            realincome.append(needinvest*1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                            yearincome.append(needinvest*newer_product.productRatio[0])
                            needinvest    = 0
                            pass
                        else :
                            investamount.append(integer*newer_product.perIncAmount[0])
                            realincome.append(integer*newer_product.perIncAmount[0]*1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                            yearincome.append(integer*newer_product.perIncAmount[0]*newer_product.productRatio[0])
                            needinvest = needinvest - integer*newer_product.perIncAmount[0]
                            pass
                        pass
                    pass
                pass
            
            else :
                
                investproduct.append(newer_product.productId[0])
                usedcoupon.append('')
                couponvalue.append(0)
                realrate.append(1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                yearrate.append(newer_product.productRatio[0])
                
                #print '333333333'
                tmp_invest = min(newer_product.maxInvestAmount[0], newer_product.remainInvestAmount[0])
                
                if tmp_invest <= needinvest:                    
                    integer   = round(tmp_invest/newer_product.perIncAmount[0],0)
                    remainder = tmp_invest%newer_product.perIncAmount[0]
                    if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                        investamount.append(tmp_invest)
                        realincome.append(tmp_invest*1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                        yearincome.append(tmp_invest*newer_product.productRatio[0])
                        needinvest    = 0
                        pass
                    else :
                        investamount.append(integer*newer_product.perIncAmount[0])
                        realincome.append(integer*newer_product.perIncAmount[0]*1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                        yearincome.append(integer*newer_product.perIncAmount[0]*newer_product.productRatio[0])
                        needinvest = needinvest - integer*newer_product.perIncAmount[0]
                        pass
                    pass
                else :
                    integer   = round(needinvest/newer_product.perIncAmount[0],0)
                    remainder = needinvest%newer_product.perIncAmount[0]
                    if round(1.0*remainder/newer_product.perIncAmount[0], 2) == 0:
                        investamount.append(needinvest)
                        realincome.append(needinvest*1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                        yearincome.append(needinvest*newer_product.productRatio[0])
                        needinvest    = 0
                        pass
                    else :
                        investamount.append(integer*newer_product.perIncAmount[0])
                        realincome.append(integer*newer_product.perIncAmount[0]*1.0*newer_product.productRatio[0]*newer_product.productDueDays[0]/365)
                        yearincome.append(integer*newer_product.perIncAmount[0]*newer_product.productRatio[0])
                        needinvest = needinvest - integer*newer_product.perIncAmount[0]
                        pass
                    pass
                pass
            pass
        #print "&&&&&&&&&&&&&&&&&&&&&&&&&"
        #print unused_coupon
        
        iter = 0
        while ( len(unused_coupon) > 0 and iter <= 15) :
            iter += 1
            print iter
            print "needinvest   = " +str(needinvest)
            # calculate best product for each coupon one by one 
            coupon_0 = unused_coupon.loc[0]
            tmp_product = couponMatchPorduct(coupon_0, new_product)                     
            tmp_product = tmp_product[tmp_product.minInvestAmount >= (unused_coupon.couponMinInvestAmount[0] - unused_coupon.couponAmount[0])]
            tmp_product = tmp_product[tmp_product.minInvestAmount <= needinvest]

            if len(tmp_product) > 0 :

                if len(unused_coupon) == 1:
                    tmp_product = tmp_product.sort_values(by = ["minInvestAmount", "productRatio"], ascending=[False, False])
                    tmp_product.index = range(len(tmp_product))
                    pass
                else :
                    tmp_product = tmp_product.sort_values(by = ["minInvestAmount", "productRatio"], ascending=[True, False])
                    tmp_product.index = range(len(tmp_product))
                    pass
                
                for i in range(len(tmp_product)) :
                    real_invest = max(unused_coupon.couponMinInvestAmount[0], tmp_product.minInvestAmount[i])
                    if needinvest >= (real_invest - unused_coupon.couponAmount[0]) :
                        #real_invest = max(unused_coupon.starting[0], tmp_product.starting[0])
                        if len(unused_coupon) == 1:
                            if needinvest -2*real_invest > 0:
                                investamount.append(real_invest)
                                realincome.append(real_invest*1.0*tmp_product.productRatio[0]*tmp_product.productDueDays[0]/365)
                                yearincome.append(real_invest*tmp_product.productRatio[0])
                                needinvest = needinvest - real_invest
                                pass
                            else :
                                integer   = round(needinvest,0)/round(tmp_product.perIncAmount[i],0)
                                remainder = round(needinvest,0)%round(tmp_product.perIncAmount[i],0)
                                
                                if round(1.0*remainder/tmp_product.perIncAmount[i], 2) == 0:
                                    investamount.append(needinvest)
                                    realincome.append(needinvest*1.0*tmp_product.productRatio[i]*tmp_product.productDueDays[0]/365)
                                    yearincome.append(needinvest*tmp_product.productRatio[i])
                                    needinvest = 0
                                    pass
                                else :
                                    investamount.append(integer*round(tmp_product.perIncAmount[i], 0))
                                    realincome.append(integer*round(tmp_product.perIncAmount[i], 0)*1.0*tmp_product.productRatio[0]*tmp_product.productDueDays[0]/365)
                                    yearincome.append(integer*round(tmp_product.perIncAmount[i], 0)*tmp_product.productRatio[0])
                                    needinvest = needinvest - integer*round(tmp_product.perIncAmount[i], 0)
                                    pass
                                pass
                        else :
                            investamount.append(real_invest)
                            needinvest = needinvest - real_invest
                            pass
                        
                        investproduct.append(tmp_product.product_id[i])
                        usedcoupon.append(unused_coupon.coupon_id[0])
                        couponvalue.append(unused_coupon.rebate[0])
                        realrate.append(1.0*tmp_product.productRatio[i]*tmp_product.duedays[0]/365)
                        yearrate.append(tmp_product.productRatio[i])
                        unused_coupon = unused_coupon.drop(0)
                        unused_coupon.index = range(len(unused_coupon))
                        break
                        pass
                    else :
                        if i < (len(tmp_product) - 1) :
                            pass
                        else :
                            unused_coupon = unused_coupon.drop(0)
                            unused_coupon.index = range(len(unused_coupon))
                            break
                            pass
                            
            else :
                unused_coupon = unused_coupon.drop(0)
                unused_coupon.index = range(len(unused_coupon))
                break

        #print new_product
        
        #print needinvest
        
        if len(new_product) > 0:
            if needinvest >= min(new_product.minInvestAmount):
                nocouponresult = self.nocoupon(needinvest, deadline, new_product)

        couponresult['investproduct'] = investproduct
        couponresult['investamount'] = investamount
        couponresult['usedcoupon'] = usedcoupon
        couponresult['couponvalue'] = couponvalue
        couponresult['realrate'] = [round(i, 3) for i in realrate]
        couponresult['realincome'] = [round(i, 2) for i in realincome]
        couponresult['yearrate'] = yearrate
        couponresult['yearincome'] = [round(i, 2) for i in yearincome]
        

        investment = couponresult.append(nocouponresult)
        investment.index = range(len(investment))
        
        print "  *********** 最终投资组合 *********** \n"
        print investment
        
        return pd.DataFrame.to_json(investment)
    
    def invest(self, needinvest, deadline):
        
        """--- Optimize Invest --- 
        IF User has coupons, then Coupon Model
        IF User doesn't have coupon, then use No Coupon model
        """
        
        if len(self.coupon) == 0:
            result = self.nocoupon(needinvest, deadline, self.product)
        else :
            result = self.usecoupon(needinvest, deadline)
        
        return result
            

