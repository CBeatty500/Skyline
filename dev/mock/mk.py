import json, math, datetime as dt
start = dt.datetime(2026,10,15)
H = 13*24
times = [(start+dt.timedelta(hours=i)).strftime('%Y-%m-%dT%H:%M') for i in range(H)]
def temp(i): return 14+6*math.sin((i%24-9)/24*2*math.pi)
hourly = {'time':times,'temperature_2m':[temp(i) for i in range(H)],'dew_point_2m':[temp(i)-5 for i in range(H)],'relative_humidity_2m':[70]*H,
 'precipitation_probability':[20]*H,'precipitation':[0]*H,'weather_code':[3]*H,'wind_speed_10m':[12]*H,'uv_index':[2]*H,'is_day':[1 if 7<=i%24<=18 else 0 for i in range(H)],
 'cloud_cover':[80]*H,'pressure_msl':[1018]*H,'snowfall':[0]*H,'wind_gusts_10m':[30]*H}
days=[(start+dt.timedelta(days=d)).strftime('%Y-%m-%d') for d in range(13)]
daily={'time':days,'weather_code':[3]*13,'temperature_2m_max':[20]*13,'temperature_2m_min':[8]*13,'precipitation_sum':[0]*13,'snowfall_sum':[0]*13,'precipitation_probability_max':[20]*13,
 'wind_speed_10m_max':[15]*13,'wind_gusts_10m_max':[35]*13,'sunrise':[d+'T07:18' for d in days],'sunset':[d+'T18:30' for d in days],'cloud_cover_mean':[70]*13,'wind_direction_10m_dominant':[200]*13}
base={'latitude':39.04,'longitude':-77.49,'elevation':93,'timezone':'America/New_York','timezone_abbreviation':'EDT','current':{'time':'2026-10-15T19:45','temperature_2m':16,'relative_humidity_2m':70,'dew_point_2m':10,'apparent_temperature':15,'is_day':0,'precipitation':0,'weather_code':3,'pressure_msl':1018,'wind_speed_10m':8,'wind_direction_10m':200,'wind_gusts_10m':20,'cloud_cover':80,'surface_pressure':1007,'visibility':16000},'hourly':hourly,'daily':daily}
json.dump(base,open('base.json','w'))
models={'daily':{'time':days},'hourly':{'time':times}}
for m in ['ecmwf_ifs025','gfs_seamless','icon_seamless','gem_seamless']:
    for k,v in [('temperature_2m_max',20),('temperature_2m_min',8),('precipitation_sum',0),('snowfall_sum',0),('wind_speed_10m_max',15),('wind_gusts_10m_max',35)]:
        models['daily'][f'{k}_{m}']=[v]*13
    models['hourly'][f'temperature_2m_{m}']=hourly['temperature_2m']
    models['hourly'][f'wind_gusts_10m_{m}']=[28]*H
    models['hourly'][f'wind_speed_10m_{m}']=[11]*H
json.dump(models,open('models.json','w'))
