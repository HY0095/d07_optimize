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
        
        self.coupon = pd.DataFrame()
        self.product = pd.DataFrame()
        #self.needinvest = needinvest
        if 'product' in kwargs.keys():
            product_loc = kwargs['product']
            if not os.path.exists(product_loc) :
                print("Error : Produc file is not exists !!!")
                sys.exit(11)
            else :
                product = pd.read_csv(product_loc)
                product = product.sort_values(by = ["rate", "duedays", "starting"], ascending=[False, True, True])
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
                coupon['rate'] = 1.0*coupon.rebate/coupon.starting
                coupon['real_start'] = coupon.starting - coupon.rebate
                #print coupon
                coupon = coupon.sort_values(by = ['rate', 'real_start', 'duedays'], ascending = [False, True, True])
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
    
    
    def nocoupon(self, needinvest, deadline):
        """--- No Coupon Model ---"""
        tmp = 0
        investratio = []
        total = needinvest
        tmp_product = self.product[self.product.duedays <= deadline]
        new_product =  tmp_product[tmp_product.starting <= needinvest]
        new_product.index = range(len(new_product))
        prod_cnt    = len(new_product)  
        #new_product = tmp_product.loc[range(tmp, prod_cnt),:]
        #new_product.index = range(len(new_product))
        product     = new_product
        profits     = dotMultiply(product.rate, product.starting)
        #print(product)
        #print(profits)
                    
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
    
    
    def usecoupon(self, needinvest, deadline):
        """--- Coupon Model ---"""
        topk = 0
        # 1. Choose coupons which satisfy [duedays <= deadline and real_start <= needinvest ]
        tmp_coupon = self.coupon[self.coupon.duedays <= deadline]
        tmp_coupon = tmp_coupon[tmp_coupon.real_start <= needinvest]
        tmp_coupon.index = range(len(tmp_coupon))
        # 2. Choose product which satisfy [duedays <= deadline and starting <= needinvest ]
        new_product = self.product[self.product.duedays <= deadline]
        #new_product =  tmp_product[tmp_product.starting <= needinvest]
        new_product.index = range(len(new_product))
        
        print new_product
        print tmp_coupon
        
        couponinvest  = []
        couponproduct = []
        usedcoupon    = []
        couponportfolio  = []
        iter = 0
        out_tag = 0
        
        while ( len(tmp_coupon) > 0 and iter <= 5) :
            iter += 1
            print "iter = "+str(iter)
            getone = 0
            #print " ***** tmp_coupon ***** "
            #print tmp_coupon
            tmp_product = new_product[new_product.starting <= (tmp_coupon.starting[0] + tmp_coupon.rebate[0])]
            if len(tmp_product) > 0 :
                tmp_product = tmp_product.sort_values(by = ["rate", "duedays", "starting"], ascending=[False, True, True])
                tmp_product.index = range(len(tmp_product))
                for i in range(len(tmp_product)) :
                    real_invest = max(tmp_coupon.starting[0], tmp_product.starting[i])
                    if needinvest >= (real_invest - tmp_coupon.rebate[0]) :
                        #real_invest = max(tmp_coupon.starting[0], tmp_product.starting[0])
                        couponinvest.append(real_invest + tmp_coupon.rebate[0])
                        couponproduct.append(tmp_product.product_id[i])
                        usedcoupon.append(tmp_coupon.coupon_id[0])
                        couponportfolio.append(tmp_product.rate[i])
                        
                        needinvest = needinvest - real_invest
                        tmp_coupon = tmp_coupon.drop(0)
                        tmp_coupon.index = range(len(tmp_coupon))
                        break
                        pass
                    else :
                        if i < (len(tmp_product) - 1) :
                            pass
                        else :
                            tmp_coupon = tmp_coupon.drop(0)
                            tmp_coupon.index = range(len(tmp_coupon))
                            break
            else :
                tmp_coupon = tmp_coupon.drop(0)
                tmp_coupon.index = range(len(tmp_coupon))
                break
            
            #########
            #for i in range(len(new_product)) :
            #    if needinvest >= tmp_coupon.real_start[0] :
            #        if tmp_coupon.starting[0] >= new_product.starting[i] :
            #            couponinvest.append(tmp_coupon.starting[0])
            #            couponproduct.append(new_product.product_id[i])
            #            usedcoupon.append(tmp_coupon.coupon_id[0])
            #            couponportfolio.append(new_product.rate[i])
            #            
            #            needinvest = needinvest - tmp_coupon.real_start[0]
            #            tmp_coupon = tmp_coupon.drop(0)
            #            tmp_coupon.index = range(len(tmp_coupon))
            #            #new_product = new_product[new_product.starting <= needinvest]
            #            #new_product.index = range(len(new_product))
            #            break
            #        else :
            #            if len(tmp_coupon) > 1:
            #                tmp_rate = 1.0*tmp_coupon.rebate[0]/new_product.starting[i]
            #                if tmp_rate >= tmp_coupon.rebate[1] :
            #                    if needinvest >= (new_product.starting[i] - tmp_coupon.rebate[0]) :
            #                        couponinvest.append(new_product.starting[i])
            #                        couponproduct.append(new_product.product_id[i])
            #                        usedcoupon.append(tmp_coupon.coupon_id[0])
            #                        needinvest = needinvest - new_product.starting[i] + tmp_coupon.rebate[0]
            #                        couponportfolio.append(new_product.rate[i])
            #                    tmp_coupon = tmp_coupon.drop(0)
            #                    tmp_coupon.index = range(len(tmp_coupon))
            #                    break
            #                else :
            #                    tmp_coupon = tmp_coupon.drop(0)
            #                    tmp_coupon.index = range(len(tmp_coupon))
            #                    break
            #            else :
            #                if needinvest >= (new_product.starting[i] - tmp_coupon.rebate[0]) :
            #                    couponinvest.append(new_product.starting[i])
            #                    couponproduct.append(new_product.product_id[i])
            #                    usedcoupon.append(tmp_coupon.coupon_id[0])
            #                    needinvest = needinvest - new_product.starting[i] + tmp_coupon.rebate[0]
            #                    couponportfolio.append(new_product.rate[i])
            #                    
            #                    tmp_coupon = tmp_coupon.drop(0)
            #                    tmp_coupon.index = range(len(tmp_coupon))
            #                    break
            #                else :
            #                    if len(new_product) > 1:
            #                        pass
            #                    else :
            #                        out_tag = 1 
            #                        break
            #    else :
            #        #out_tag = 1
            #        tmp_coupon = tmp_coupon.drop(0)
            #        tmp_coupon.index = range(len(tmp_coupon))
            #        break
            #    #tmp_coupon = tmp_coupon.drop(0)
            #    #tmp_coupon.index = range(len(tmp_coupon))
            #        
        print "******************************"
        print "couponinvest    = " + ','.join([str(i) for i in couponinvest])
        print "couponproduct   = " + ','.join(couponproduct)
        print "usedcoupon      = " + ','.join(usedcoupon)
        print "needinvest      = " + str(needinvest)
        print "couponportfolio = " + ','.join([str(i) for i in couponportfolio])


        if len(couponproduct) > 0:
            #couponinvest[0] += needinvest
            coupon_invest = formula(couponproduct, couponinvest)
            couponprofit = np.dot(couponinvest, couponportfolio)
        else :
            coupon_invest = ""
            couponprofit = []
        #    print "couponprofit  = " + str(couponprofit)
        #    print "coupon_invest = " + coupon_invest
        #    pass
        
        #print couponproduct
        if needinvest < min(new_product.starting) :
            if len(couponproduct) > 0 :
                couponinvest[0] += needinvest
                coupon_invest = formula(couponproduct, couponinvest)
                couponprofit = np.dot(couponinvest, couponportfolio)
            else :
                print "No Product Satisfy Your Input !!!"
                sys.exit(21)
            
        else :
            result_01 = self.nocoupon(needinvest, deadline)
                
        print "\n ------ 优惠券投资组合 ------ \n"
        print "优惠券组合  = " + coupon_invest
        print "优惠券收益  = " + str(couponprofit)
    
    def invest(self, needinvest, deadline):
        
        """--- Optimize Invest --- 
        IF User has coupons, then Coupon Model
        IF User doesn't have coupon, then use No Coupon model
        """

        if len(self.coupon) == 0:
            print " **** No Coupon Model **** \n"
            result = self.nocoupon(needinvest, deadline)
        else :
            print " Coupon Model !!! "
            result = self.usecoupon(needinvest, deadline)
        
        return result
            

