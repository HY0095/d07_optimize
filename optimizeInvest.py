import numpy as np
from scipy.optimize import minimize
import pandas as pd
import os
import sys

def dotMultiply(a,b):
    """ dot multiply 
    example: A = [1, 2, 3], B = [2, 3, 4], then
    return C = [1*2, 2*3, 3*4] = [2, 6, 12]
    """
    result = []
    for i in np.arange(len(a)):
        result.append(a[i]*b[i])
    return result

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

class optimizeInvest(object):
    
    def __init__(self, **kwargs):
        
        self.coupon  = pd.DataFrame()
        self.product = pd.DataFrame()
        #self.needinvest = needinvest
        if 'product' in kwargs.keys():
            product_loc = kwargs['product']
            if not os.path.exists(product_loc) :
                print("Error : Produc file is not exists !!!")
                sys.exit(11)
            else :
                product = pd.read_csv(product_loc)
                product = product.sort_values(by = ["rate", "month", "starting"], ascending=[False, True, True])
                product.index = range(len(product))
                self.product = product
                self.raw_investratio = [0 for i in range(len(product))]
                                
        if 'coupon' in kwargs.keys():
            coupon_loc = kwargs['coupon']
            #print(coupon_loc)
            if not os.path.exists(coupon_loc):
                print("Error : Coupon file is not exist !!!")
                sys.exit(11)
            else :
                coupon = pd.read_csv(coupon_loc)
                coupon['rate'] = 1.0*coupon.rebate/(coupon.starting - coupon.rebate)
                coupon['real_start'] = coupon.starting - coupon.rebate
                #print coupon
                coupon = coupon.sort_values(by = ['rate', 'real_start'], ascending = [False, True])
                coupon.index = range(len(coupon))
                self.coupon = coupon
        
        if len(product) == 0:
            print("Error: The Product list is empty !!!")
            sys.exit(12)
        else :
            #print product
            pass
        #print(self.coupon)
        #print(self.product)
    
    
    def nocoupon(self, needinvest, month):
        """--- No Coupon Model ---"""
        tmp = 0
        investratio = []
        total = needinvest
        tmp_product = self.product[self.product.month <= month]
        new_product =  tmp_product[tmp_product.starting <= needinvest]
        new_product.index = range(len(new_product))
        prod_cnt    = len(new_product)  
        product     = new_product
        profits     = dotMultiply(product.rate, product.starting)
                    
        if prod_cnt == 0:
            print("Warning : No product satisfy the Deadline !!! \n")
            print("===================================================")
            print "\n ------ 非券投资组合 ------ \n"
            print("非券组合 = ....... \n")
            print("非券收益 = 0 " )            
            sys.exit(21)
        
        while needinvest > 0 :
            for i in range(len(new_product)):
                if needinvest >= new_product.starting[i] :
                    if needinvest <= new_product.outlanding[i] :
                        investratio.append( 1.0*needinvest/new_product.starting[i] )
                        needinvest = 0
                    else :
                        investratio.append( 1.0*new_product.outlanding[i]/new_product.starting[i] )
                        needinvest = needinvest - new_product.outlanding[i]
                        new_product = new_product.loc[range(i+1, len(new_product)), :]
                        new_product.index = range(len(new_product))
                    break
                else :
                    investratio.append(0)
                    new_product = new_product.loc[range(i+1, len(new_product)), :]
                    new_product.index = range(len(new_product))
                    break
            if len(new_product) == 0:
                print("Warning : No more product for investing !!! \n")
                break
        #result = np.dot(profits, investratio)
        if max(investratio) == 0:
            print("Warning: No Optimize Investment Satisfied !!! \n")
            print("===================================================")
            print "\n ------ 非券投资组合 ------ \n"
            portfolio = []
            profit = 0
            print("非券组合 = ....... \n")
            print("非券收益 = 0 " )
        else :
            portfolio = dotMultiply(investratio, product.loc[[i for i in range(len(investratio))], :].starting)
            profit = np.dot(investratio, profits[:len(investratio)])
            if len(new_product) == 0:
                print("The Residual Investment is "+ str(total - sum(portfolio))+"\n")
            expression = formula(product.product_id[:len(portfolio)], portfolio)
            print("===================================================")
            print "\n ------ 非券投资组合 ------ \n"
            print("非券组合 = "+expression)
            print("非券收益 = " + str(round(profit, 2)))
        return [investratio, portfolio, round(profit, 2)]
    
    def usecoupon(self, needinvest, month, freshman):
        """--- Coupon Model ---"""
        topk = 0
        result_coupon = []
        result_nocoupon = []
        # 1. Choose coupons which satisfy [duedays <= deadline and real_start <= needinvest ]
        unused_coupon = self.coupon[self.coupon.month <= month]
        unused_coupon = unused_coupon[unused_coupon.real_start <= needinvest]
        unused_coupon.index = range(len(unused_coupon))
        # 2. Choose product which satisfy [duedays <= deadline and starting <= needinvest ]
        new_product = self.product[self.product.month <= month]
        #new_product =  tmp_product[tmp_product.starting <= needinvest]
        new_product.index = range(len(new_product))
        
        #print new_product
        #print unused_coupon
        
        newer_product = new_product[new_product.rate == 0.1]
        newer_coupon  = unused_coupon[unused_coupon.coupon_desc == 'fresh']
        if len(newer_coupon) > 0:
            newer_coupon  = newer_coupon.sort_values(by = ["starting", "rate"], ascending=[False, False])
            newer_coupon.index = range(len(newer_coupon))
            #print(newer_coupon)
            
        #newer_coupon  = newer_coupon[newer_coupon.]
        #real_invest  = max(unused_coupon.starting[0], tmp_product.starting[i])
        if max(new_product.rate) == 0.1:
            newer_product.index = range(len(newer_product))
            newer_coupon  = unused_coupon[unused_coupon.coupon_desc == 'fresh']
            if len(newer_coupon) > 0:
                newer_coupon  = newer_coupon.sort_values(by = ["starting", "rate"], ascending=[False, False])
                newer_coupon.index = range(len(newer_coupon))
                rebate  = newer_coupon.rebate[0]
                
                if (needinvest + rebate) >= newer_product.starting[0] and (needinvest + rebate) <= freshman:
                    couponinvest  = [needinvest]
                    couponproduct = [newer_product.product_id[0]]
                    #print(newer_coupon.coupon_id[0])
                    usedcoupon    = [newer_coupon.coupon_id[0]]
                    couponvalue   = [newer_coupon.rebate[0]]
                    #实际收益  
                    print '实际收益'
                    couponrate    = [1.0*newer_product.rate[0]*newer_product.duedays[0]/365]
                    #年化收益
                    couponportfolio = [newer_product.rate[0]]
                    
                    needinvest = 0
                    new_product = new_product.drop(0)
                    new_product.index = range(len(new_product))
                    self.product = new_product
                    useed_coupon = unused_coupon[unused_coupon.coupon_id == newer_coupon.coupon_id[0]].index
                    unused_coupon   = unused_coupon.drop(useed_coupon[0])
                    unused_coupon.index = range(len(unused_coupon))
                    pass
                elif (needinvest + rebate) < newer_product.starting[0]:
                    couponinvest   = []
                    couponproduct  = []
                    usedcoupon     = []
                    couponvalue    = []
                    couponrate     = []
                    couponportfolio = []
                    pass
                elif needinvest + newer_coupon.rebate[0] > freshman :
                    couponinvest  = [freshman]
                    #print(newer_coupon.coupon_id[0])
                    couponproduct = [newer_product.product_id[0]]
                    usedcoupon    = [newer_coupon.coupon_id[0]]
                    couponvalue   = [newer_coupon.rebate[0]]
                    couponrate    = [1.0*newer_product.rate[0]*newer_product.duedays[0]/365]
                    couponportfolio = [newer_product.rate[0]]
                    #needinvest = needinvest + newer_coupon.rebate[0] - freshman
                    needinvest = needinvest - freshman
                    new_product = new_product.drop(0)
                    new_product.index = range(len(new_product))
                    self.product = new_product
                    
                    useed_coupon = unused_coupon[unused_coupon.coupon_id == newer_coupon.coupon_id[0]].index
                    #print useed_coupon
                    unused_coupon   = unused_coupon.drop(useed_coupon[0])
                    #unused_coupon   = newer_coupon.drop(0)
                    unused_coupon.index = range(len(unused_coupon))
                    pass
                pass
            else :
                if needinvest >= newer_product.starting[0] and needinvest <= freshman :
                    couponinvest  = [needinvest]
                    couponproduct = [newer_product.product_id[0]]
                    couponvalue   = [newer_coupon.rebate[0]]
                    couponrate    = [1.0*newer_product.rate[0]*newer_product.duedays[0]/365]
                    couponportfolio = [newer_product.rate[0]]
                    usedcoupon    = ['NULL']
                    needinvest  = 0
                    new_product = new_product.drop(0)
                    new_product.index = range(len(new_product))
                    self.product = new_product
                    pass
                elif needinvest > freshman :
                    couponinvest  = [freshman]
                    couponproduct = [newer_product.product_id[0]]
                    couponvalue   = [newer_coupon.rebate[0]]
                    couponrate    = [1.0*newer_product.rate[0]*newer_product.duedays[0]/365]
                    couponportfolio = [newer_product.rate[0]]
                    usedcoupon    = ['NULL']
                    needinvest  = needinvest - freshman
                    new_product = new_product.drop(0)
                    new_product.index = range(len(new_product))
                    self.product = new_product
                    pass
                elif needinvest < newer_product.starting[0] :
                    couponinvest  = []
                    couponproduct = []
                    usedcoupon    = []
                    couponvalue   = []
                    couponrate    = []
                    couponportfolio= []
                    pass
                pass
            pass
        
        else :
            couponinvest  = []
            couponproduct = []
            usedcoupon    = []
            couponvalue   = []
            couponrate    = []
            couponportfolio = []
            pass

        iter = 0

        while ( len(unused_coupon) > 0 and iter <= 10) :
            iter += 1
            #print "iter = " + str(iter)
            #print " ***** unused_coupon ***** "
            #print unused_coupon
            tmp_product = new_product[new_product.starting >= (unused_coupon.starting[0] - unused_coupon.rebate[0])]
            tmp_product = tmp_product[tmp_product.starting <= needinvest]
            tmp_product = tmp_product[tmp_product.month == unused_coupon.month[0]]
            #print tmp_product
            if len(tmp_product) > 0 :
                tmp_product = tmp_product.sort_values(by = ["starting", "rate"], ascending=[True, False])
                tmp_product.index = range(len(tmp_product))
                #print tmp_product
                if len(unused_coupon) == 1:
                    tmp_product = tmp_product.sort_values(by = ["starting", "rate"], ascending=[False, False])
                    tmp_product.index = range(len(tmp_product))
                    pass
                else :
                    tmp_product = tmp_product.sort_values(by = ["starting", "rate"], ascending=[True, False])
                    tmp_product.index = range(len(tmp_product))
                    pass
                
                for i in range(len(tmp_product)) :
                    real_invest = max(unused_coupon.starting[0], tmp_product.starting[i])
                    if needinvest >= (real_invest - unused_coupon.rebate[0]) :
                        #real_invest = max(unused_coupon.starting[0], tmp_product.starting[0])
                        if len(unused_coupon) == 1:
                            if needinvest -2*real_invest > 0:
                                couponinvest.append(real_invest)
                                needinvest = needinvest - real_invest
                                pass
                            else :
                                couponinvest.append(needinvest)
                                needinvest = 0
                                pass
                        else :
                            couponinvest.append(real_invest)
                            needinvest = needinvest - real_invest
                            pass
                        
                        couponproduct.append(tmp_product.product_id[i])
                        usedcoupon.append(unused_coupon.coupon_id[0])
                        couponvalue.append(unused_coupon.rebate[0])
                        couponrate.append(1.0*tmp_product.rate[0]*tmp_product.duedays[0]/365)
                        couponportfolio.append(tmp_product.rate[i])

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
            
        print "******************************"
        print "couponinvest    = " + ','.join([str(i) for i in couponinvest])
        print "couponproduct   = " + ','.join(couponproduct)
        print "usedcoupon      = " + ','.join(usedcoupon)
        print "needinvest      = " + str(needinvest)
        print "couponvalue     = " + ','.join([str(i) for i in couponvalue])
        print "couponrate      = " + ','.join([str(i) for i in couponrate])
        print "couponportfolio = " + ','.join([str(i) for i in couponportfolio])

        if len(couponproduct) > 0:
            #couponinvest[0] += needinvest
            coupon_invest = formula(couponproduct, couponinvest)
            realprofit    = np.dot(couponinvest, couponrate)                               
            couponprofit  = np.dot(couponinvest, couponportfolio)
        else :
            coupon_invest = ""
            couponrate    = []
            couponprofit  = []

        #print couponproduct
        if needinvest < min(new_product.starting) :
            if len(couponproduct) > 0 :
                couponinvest[0] += needinvest
                coupon_invest = formula(couponproduct, couponinvest)
                realprofit    = np.dot(couponinvest, couponrate)
                couponprofit = np.dot(couponinvest, couponportfolio)
            else :
                print "No Product Satisfy Your Input !!!"
                sys.exit(21)            
        else :
            result_nocoupon = self.nocoupon(needinvest, month)
        
        realprofit   += sum(couponvalue)
        couponprofit += sum(couponvalue)
        
        result_coupon = [couponinvest, couponproduct, usedcoupon, couponvalue, couponrate, couponportfolio]
        
        print "\n ------ 优惠券投资组合 ------ \n"
        print "优惠券组合 = " + coupon_invest
        print "优惠券抵现 = " + str(couponvalue)
        print "实际收益  = " + str(round(realprofit,2))
        print "年化收益  = " + str(couponprofit)
        
        return result_coupon, result_nocoupon
    
    def invest(self, needinvest, month, freshman):
        
        """--- Optimize Invest --- 
        IF User has coupons, then Coupon Model
        IF User doesn't have coupon, then use No Coupon model
        """
        
        if len(self.coupon) == 0:
            print " **** No Coupon Model **** \n"
            result = self.nocoupon(needinvest, month)
        else :
            print " Coupon Model !!! "
            result = self.usecoupon(needinvest, month, freshman)
        
        return result
            

