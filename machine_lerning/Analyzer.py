#!/usr/bin/env python
# coding: utf-8

# In[1]:


# -*- coding: utf-8 -*-

import pymysql
import pandas as pd
import re
from datetime import datetime
from datetime import timedelta
import time
import sys

sys.path.append('C:/Users/JG/abangers/machine_learning')


class MarketDB():
    
    def read_krx_code(self):
        """ 엑셀파일 불러와서 종목코드와 회사이름만 남기고 전부 제거 후 code 비어있는 앞부분 0으로 채우기 """
        
        url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
        krx = pd.read_html(url, header=0)[0]  # read_html은 url에 있는 table전체를 가져와서 DataFrame으로 만들어 줌
        krx = krx[['종목코드', '회사명']]
        krx = krx.rename(columns={'종목코드': 'code', '회사명': 'company'})
        krx.code = krx.code.map('{:06d}'.format)
        return krx
    
    def krx_to_dict(self):
        """ 깔끔해진 krx를 불러와서 dict으로 만듦 ; {"code" : "company"} """
        
        krx = self.read_krx_code()   
        
        self.codes = dict()     
        for idx in range(len(krx)):
            self.codes[krx['code'].values[idx]] = krx['company'].values[idx]
        return self.codes
    
    # 1 
    def date_adjustment(self, start_date):
        """전일비(diff)의 부호를 설정하기 위해 날짜를 변경"""
        
        self.start_date = datetime.strptime(start_date,'%Y-%m-%d') # 원래 날짜를 self.star_date에 저장
        start_date = self.start_date - timedelta(days=1)
        start_date = start_date.strftime('%Y-%m-%d') # 시작날의 하루 전 날짜  
        return self.start_date, start_date
    
    # 2
    def code_adjustment(self, code):
        """회사를 한글 or 코드를 적어도 상관없도록 미리 만들어 놓은 dict를 이용"""
        
        codes = self.krx_to_dict()
        
        if re.match('\d', code): # 코드가 숫자일 경우
            company_name = codes['{}'.format(code)]
            code = code              
        else:
            rev_codes = dict(map(reversed,codes.items())) # 코드가 문자일 경우
            company_name = code        
            code = rev_codes['{}'.format(code)]   
        return code, company_name
    
    # 3
    def read_mySQL(self, code, start_date, end_date):
        """ mySQL DB에서 데이터를 끌어오기 """
        
        with self.conn.cursor() as curs:
            sql= """

            SELECT * FROM daily_price
            WHERE code = '{}' AND date BETWEEN '{}' AND '{}';

            """.format(code, start_date, end_date)
            curs.execute(sql)        
        return curs.fetchall()
    
    # 4
    def modify_diff(self, df):
        """ 전일비(diff)에 부호설정 """
        
        a_df = df.copy()['diff'] # copy()를 이용하지 않으면 SettingWithCopyWarning 뜸
        for i in range(1,len(df)):
            a_df[i] = df['close'][i] - df['close'][i-1]
        b_df = df.copy()[1:]
        b_df['diff'] = a_df
        return b_df.reset_index(drop=True) # 인덱스 번호 재설정
        
    # 5
    def print_status(self,company_name, code, df):
        """ 진행과정 print """
        
        print('# {}({}) : 총 {}개 완료 '.format(company_name, code, len(df)), end='\r')  
        

    def get_daily_price(self ,code, start_date=None ,end_date=None): 
        self.conn = pymysql.connect(host='localhost', user='root',password='qet[]zc//!@92', db='investar', charset='utf8') 
        
        col_name = ['code', 'date', 'open', 'high', 'low', 'close','diff', 'volume']
        
        # 1
        self.start_date, start_date= self.date_adjustment(start_date)
        
        # 2
        code, company_name = self.code_adjustment(code)
        
        # 3
        self.stock_df = pd.DataFrame(self.read_mySQL(code, start_date, end_date), columns = col_name)
        
        # 4
        self.stock_df = self.modify_diff(self.stock_df)
        
        # 5
        self.print_status(company_name, code, self.stock_df)  
        
        self.conn.close()
        return self.stock_df

