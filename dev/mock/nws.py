import json, datetime as dt
now = dt.datetime(2026,10,15,23,45)  # UTC
def ob(t, temp, gust=None):
    return {'timestamp': t.strftime('%Y-%m-%dT%H:%M:00+00:00'), 'temperature':{'value':temp}, 'dewpoint':{'value':temp-5}, 'relativeHumidity':{'value':70},
            'windSpeed':{'value':9.3,'unitCode':'wmoUnit:km_h-1'}, 'windDirection':{'value':200}, 'windGust':{'value':gust,'unitCode':'wmoUnit:km_h-1'},
            'visibility':{'value':16090}, 'barometricPressure':{'value':101800}, 'seaLevelPressure':{'value':101790}, 'textDescription':'Cloudy',
            'presentWeather':[], 'cloudLayers':[{'amount':'OVC','base':{'value':1200}}], 'rawMessage':'KIAD 152352Z 20005KT 10SM OVC040 16/11 A3006 RMK AO2 SLP179 T01610106',
            'precipitationLastHour':{'value':None}, 'maxTemperatureLast24Hours':{'value':None}, 'minTemperatureLast24Hours':{'value':None}, 'heatIndex':{'value':None}, 'windChill':{'value':None}, 'elevation':{'value':95}}
hist = [ob(now - dt.timedelta(hours=h), 16 + (h%5)*0.3) for h in range(0, 30)]
json.dump({'properties':{'forecast':'https://api.weather.gov/gridpoints/LWX/1,1/forecast','cwa':'LWX','gridId':'LWX','observationStations':'https://api.weather.gov/gridpoints/LWX/1,1/stations','relativeLocation':{'properties':{'city':'Ashburn','state':'VA'}}}}, open('points.json','w'))
json.dump({'properties':{'periods':[]}}, open('fc.json','w'))
json.dump({'features':[]}, open('alerts.json','w'))
json.dump({'features':[{'properties':{'stationIdentifier':'KIAD','name':'Washington Dulles','elevation':{'value':95}},'geometry':{'coordinates':[-77.45,38.93]}}]}, open('stations.json','w'))
json.dump({'properties':hist[0]}, open('latest.json','w'))
json.dump({'features':[{'properties':h} for h in hist]}, open('obs.json','w'))
