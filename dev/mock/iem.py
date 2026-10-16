import json, datetime as dt, random
random.seed(1)
def cli_rows(y, m1, d1, m2, d2):
    rows=[]; d=dt.date(y,m1,d1)
    while d<=dt.date(y,m2,d2):
        hi=70+random.randint(-8,10); lo=48+random.randint(-6,8)
        rows.append({'valid':d.isoformat(),'station':'KIAD','name':'WASHINGTON DULLES','high':hi,'low':lo,'high_normal':69,'low_normal':46,'high_record':88,'high_record_years':[1941],'low_record':28,'low_record_years':[1987],
          'precip':random.choice(['0.00','0.00','T','0.12','0.45']),'precip_normal':'0.12','precip_record':'2.10','precip_record_years':[1976],'snow':'0.0','precip_month':'1.0','precip_month_normal':'1.5','precip_jan1':'30.0','precip_jan1_normal':'33.0','snow_jul1':'0.0','snow_jul1_normal':'0.1','snow_month':'0.0','snow_month_normal':'0.0'})
        d+=dt.timedelta(days=1)
    return rows
json.dump({'results':cli_rows(2026,1,1,10,15)}, open('cli2026.json','w'))
json.dump({'results':cli_rows(2025,1,1,12,31)}, open('cli2025.json','w'))
json.dump({'type':'FeatureCollection','features':[{'id':'KIAD','properties':{'sid':'KIAD','sname':'Dulles','ncei91':'USW00093738','archive_end':None},'geometry':{'type':'Point','coordinates':[-77.45,38.93]}}]}, open('clinet.json','w'))
