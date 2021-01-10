# @Author: pipegalera
# @Date:   2020-10-04T21:40:56+02:00
# @Last modified by:   pipegalera
# @Last modified time: 2020-12-25T20:12:56+01:00



import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
from datetime import datetime, date
import locale
locale.setlocale(locale.LC_ALL, 'es_ES')

# Header
st.title("Covid-Navarra")

def get_data():
    # Raw data
    url = "http://www.navarra.es/appsext/DescargarFichero/default.aspx?codigoAcceso=OpenData&fichero=coronavirus\CasosMunicipios_ZR_Covid.csv"
    df = pd.read_csv(url, sep = ';', encoding='latin1', parse_dates=['Fecha'])

    #Tidy data
    df = df.set_index('DesMun')
    df = df.drop(columns = {'CodZR', 'CodMun', 'AcumuladoCasosHastaLaFecha'})
    df.rename(columns = {'DesZR': 'Zona', 'NuevosCasos': 'Casos ese dia'}, inplace = True)
    return df

df = get_data()

###########################################################################
# Total cases of last day and printing the Header
last_day = df['Fecha'].iloc[-1]

st.write("El número total de casos confirmados de COVID-19 en Navarra es", df.cumsum()['Casos ese dia'].iloc[-1], ", a día",  last_day.strftime('%d'), "de", last_day.strftime('%B'), "de", last_day.strftime('%Y'), ". Los datos provienen del Departamento de Salud de Navarra, y son actualizados diariamente. Fuente: [Gobierno Abierto de Navarra](https://gobiernoabierto.navarra.es/es/open-data/datos/positivos-covid-19-por-pcr-distribuidos-por-municipio).")
###########################################################################


# Filter box
st.write("Selecciona los municipios:")
municipios = st.multiselect(
    "", list(df.index.unique().sort_values()), ["TUDELA", "PAMPLONA / IRUÑA"] # defaults
)

if not municipios:
    st.error("Por favor, selecciona al menos un municipio")

# Load data
data_selected = df.loc[municipios].reset_index()

data_header = pd.pivot_table(data_selected, index = 'DesMun', columns = 'Fecha', values = 'Casos ese dia', aggfunc=np.sum, margins= False)

# Tidy data
data_header.columns = data_header.columns.strftime('%d-%b')
data_header = data_header.reset_index()
data_header = data_header.fillna(0)
data_header = data_header.rename(columns = {'DesMun': '', 'All': 'Casos totales'})
data_header = data_header.set_index('')
st.write("Nuevos casos, ultima semana:")
st.write(data_header.iloc[:, :-8:-1])


# Chart
data_ac = data_header.cumsum(axis=1).T.reset_index()
data_ac = pd.melt(data_ac, id_vars = ['Fecha'])
data_ac = data_ac.rename(columns = {'': 'Región', 'value': 'Casos Acumulados'})

st.write("Casos acumulados en los municipios selecionados:")

chart = (
    alt.Chart(data_ac)
    .mark_area(
        opacity=0.5)
    .encode(
        x="Fecha:T",
        y=alt.Y("Casos Acumulados:Q", stack=None),
        color="Región:N",
    )
)
st.altair_chart(chart, use_container_width=True)
