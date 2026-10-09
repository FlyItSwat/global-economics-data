"""World Bank API client and reusable economic-data transformations."""
import requests
import pandas as pd

INDICATORS = {
    "GDP growth (annual %)": "NY.GDP.MKTP.KD.ZG",
    "Inflation, consumer prices (annual %)": "FP.CPI.TOTL.ZG",
    "Unemployment, total (% of labor force)": "SL.UEM.TOTL.ZS",
    "GDP per capita (current US$)": "NY.GDP.PCAP.CD",
    "Life expectancy at birth (years)": "SP.DYN.LE00.IN",
    "Population, total": "SP.POP.TOTL",
}
COUNTRIES = {"India":"IND", "United States":"USA", "China":"CHN", "United Kingdom":"GBR", "Japan":"JPN", "Germany":"DEU", "Brazil":"BRA", "South Africa":"ZAF", "Indonesia":"IDN", "Bangladesh":"BGD", "France":"FRA", "Nigeria":"NGA", "Singapore":"SGP", "Australia":"AUS", "Canada":"CAN"}

def parse_world_bank(payload):
    """Parse two-element World Bank JSON response into normalized observations."""
    if not isinstance(payload,list) or len(payload)!=2 or not isinstance(payload[1],list):
        raise ValueError("Unexpected World Bank API response")
    rows=[]
    for item in payload[1]:
        if not isinstance(item,dict) or item.get('value') is None: continue
        try:
            rows.append({'country':item['country']['value'], 'code':item['countryiso3code'],
                         'year':int(item['date']), 'value':float(item['value'])})
        except (KeyError,TypeError,ValueError):
            continue
    return pd.DataFrame(rows,columns=['country','code','year','value'])

def get_indicator(codes,indicator,start=2000,end=2025,session=None):
    if not codes or not all(c in COUNTRIES.values() for c in codes):
        raise ValueError('Select valid countries')
    if indicator not in INDICATORS.values() or start>end or start<1960 or end>2100:
        raise ValueError('Invalid indicator or year range')
    api=session if session is not None else requests
    url=f"https://api.worldbank.org/v2/country/{';'.join(codes)}/indicator/{indicator}"
    response=api.get(url,params={'format':'json','date':f'{start}:{end}','per_page':20000},timeout=25)
    response.raise_for_status()
    payload=response.json()
    if isinstance(payload,list) and payload and isinstance(payload[0],dict):
        pages=int(payload[0].get('pages',1))
        if pages>1:
            raise ValueError('Response exceeds one page; narrow your selection')
    return parse_world_bank(payload)

def latest_by_country(df):
    if df.empty: return df.copy()
    return df.sort_values('year').drop_duplicates('code',keep='last').sort_values('value',ascending=False).reset_index(drop=True)

def compare_years(df,year_a,year_b):
    """Returns absolute and percent changes; percent undefined when base is zero."""
    a=df[df.year==year_a].set_index('code')['value']
    b=df[df.year==year_b].set_index('code')['value']
    both=pd.concat([a.rename('start'),b.rename('end')],axis=1).dropna()
    both['change']=both['end']-both['start']
    both['percent_change']=(both['change']/both['start'].abs()*100).where(both['start']!=0)
    return both.reset_index()
