import streamlit as st
import pandas as pd
import plotly.express as px
from economics import COUNTRIES, INDICATORS, get_indicator, latest_by_country, compare_years

st.set_page_config(page_title='Global Economics Data Explorer',page_icon='🌍',layout='wide')
st.title('Global Economics Data Explorer')
st.caption('Compare countries using World Bank World Development Indicators')
with st.sidebar:
    st.header('Explore indicators')
    chosen=st.multiselect('Countries',list(COUNTRIES),default=['India','United States','China'])
    indicator_name=st.selectbox('Indicator',list(INDICATORS))
    start,end=st.slider('Years',1960,2026,(2000,2024))
    source=st.radio('Data source',['Live World Bank API','Illustrative offline sample'])
    st.caption('Latest available year differs by country and indicator. Missing data are not filled.')
@st.cache_data(ttl=3600,show_spinner=False)
def load_live(codes,indicator,start,end):
    return get_indicator(list(codes),indicator,start,end)
try:
    if not chosen: st.info('Select at least one country.'); st.stop()
    if source=='Live World Bank API':
        with st.spinner('Fetching World Bank data...'):
            df=load_live(tuple(COUNTRIES[n] for n in chosen),INDICATORS[indicator_name],start,end)
    else:
        if indicator_name not in ['GDP growth (annual %)','Inflation, consumer prices (annual %)']:
            st.warning('Offline sample only includes GDP growth and inflation. Select one of these indicators.')
            st.stop()
        df=pd.read_csv('sample_data.csv')
        df=df[(df.code.isin([COUNTRIES[n] for n in chosen])) & (df.indicator==INDICATORS[indicator_name]) & df.year.between(start,end)]
        df=df[['country','code','year','value']].copy()
        st.warning('ILLUSTRATIVE SYNTHETIC DATA — not official World Bank observations.')
    if df.empty: st.warning('No observations available for this selection.'); st.stop()
    latest=latest_by_country(df)
    st.subheader(indicator_name)
    st.plotly_chart(px.line(df.sort_values('year'),x='year',y='value',color='country',markers=True,
                            labels={'value':indicator_name,'year':'Year','country':'Country'}),use_container_width=True)
    left,right=st.columns(2)
    with left:
        st.markdown('**Latest available observation per country**')
        st.dataframe(latest[['country','year','value']].rename(columns={'year':'Observation year','value':indicator_name}),hide_index=True,use_container_width=True)
    with right:
        st.plotly_chart(px.bar(latest,x='country',y='value',color='country',hover_data=['year'],
                               labels={'value':indicator_name,'country':'Country'}),use_container_width=True)
    st.subheader('Compare two years')
    a,b=st.columns(2)
    years=sorted(df.year.unique().tolist())
    ya=a.selectbox('Starting year',years,index=0)
    yb=b.selectbox('Ending year',years,index=len(years)-1)
    changes=compare_years(df,ya,yb)
    if changes.empty: st.info('No countries have observations in both selected years.')
    else: st.dataframe(changes,use_container_width=True,hide_index=True)
    st.download_button('Download observations CSV',df.sort_values(['country','year']).to_csv(index=False),
                       'world_bank_comparison.csv','text/csv')
    st.caption('Source: World Bank Indicators API (live mode). Country and year coverage vary. '
               'Comparisons describe correlations, not causal relationships. '
               'Percent change of a rate (e.g. inflation) differs from percentage-point change.')
except Exception as exc:
    st.error(f'Data could not be loaded: {exc}. Try offline sample or a smaller year range.')
