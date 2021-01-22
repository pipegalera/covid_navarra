# @Author: pipegalera
# @Date:   2020-10-04T21:40:56+02:00
# @Last modified by:
# @Last modified time: 2021-01-22T10:49:36+01:00



import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import base64
import altair as alt
from datetime import datetime, date
from PIL import Image
import requests
import io
#import locale
#locale.setlocale(locale.LC_ALL, 'es_ES.utf8')

######## LOAD DATA ####################
def load_data():
    url_deaths = "http://www.navarra.es/appsext/DescargarFichero/default.aspx?codigoAcceso=OpenData&fichero=coronavirus\datos_coronavirus_zonas_basicas.csv"

    raw_data = pd.read_csv(url_deaths,
                           sep = ';',
                           decimal=",",
                           encoding='utf-8',
                           usecols = ["Fecha", "Zona Básica", "Casos acumulados", "% por 1000"],
                           parse_dates= ["Fecha"],
                           dayfirst = True)

    culumative_cases = pd.pivot_table(raw_data,
                                      index = "Zona Básica",
                                      columns = "Fecha",
                                      values= "Casos acumulados")

    individual_cases = culumative_cases.diff(axis = 1).fillna(culumative_cases['2020-03-25'].iloc[0])
    last_week_cases = individual_cases.iloc[:,-7:].sum().sum().astype(int)

    return raw_data, culumative_cases, individual_cases, last_week_cases

raw_data, culumative_cases, individual_cases, last_week_cases = load_data()

##################### HEADER #######################################

# For whatever reason, Streamlit display better the images in HTML than in
# Markdown.'img-fluid' is used to make it scale appropriately across devices

header_html = "<img src='https://i.imgur.com/pahDIz7.png' class='img-fluid'>"

st.markdown(header_html, unsafe_allow_html=True,)

st.markdown("---")
st.markdown("""
* :hospital: Número de casos en los últimos 7 días en Navarra: **{}**.
* :zap: Datos actualizados diariamente por el [Gobierno de Navarra](https://gobiernoabierto.navarra.es/es/open-data/datos/positivos-covid-19-por-pcr-distribuidos-por-municipio).
* :point_right: **Selecciona zonas básicas de salud** para saber la evolución de Covid-19 en ellas, así como compararlas (e.g. Tudela Este, Rochapea, Corella...).
""".format(last_week_cases))



######### Municipality selection ############

# Filter box
municipios = st.multiselect(
    "", list(culumative_cases.index.unique().sort_values()), ['Tudela Este', 'Tudela Oeste'] # defaults
)
if not municipios:
    st.error("Por favor, selecciona al menos un municipio")


# Tidy data
def tidy_data(municipios):
    data_selected = individual_cases.loc[municipios]
    data_selected.columns = data_selected.columns.strftime('%d-%b')
    data_selected = data_selected.reset_index()
    data_selected = data_selected.rename(columns = {'Zona Básica': ''})
    data_selected = data_selected.set_index('')

    return data_selected

data_selected = tidy_data(municipios)
last_week_data_selected = data_selected.iloc[:, :-8:-1]

st.markdown("""
            ## Nuevos casos de los últimos 7 días
               """)

st.write(last_week_data_selected)
st.markdown("---")

################ Chart ##########################################

st.markdown("""
            ## Comparación de la evolución de casos positivos por 1000 habitantes.
               """)

# Data used
evolution_data = raw_data[raw_data['Zona Básica'].isin(municipios)]

def make_evolution_chart(evolution_data):
    # Basic chart
    line = alt.Chart(evolution_data, title = ''
    ).mark_line(interpolate='basis', size=3).encode(
        alt.X('Fecha:T'),
        alt.Y('% por 1000:Q', title='Casos acumulados por 1000 habitantes'),
        color= 'Zona Básica')
    # to smooth the line you can use the LOESS transform
    #).transform_loess('Fecha', '% por 1000', groupby=['Zona Básica'])

    # Create a selection that chooses the nearest point & selects based on x-value (Fecha)
    nearest  = alt.selection(type='single', on='mouseover',
                              fields=['Fecha'], nearest=True , empty='none')

    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = alt.Chart(evolution_data).mark_point().encode(
        x='Fecha:T',
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )


    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align='left', dx=5, dy=-7).encode(
        text=alt.condition(nearest, '% por 1000:Q', alt.value(' '))
    )

    # Draw a rule at the location of the selection
    rules = alt.Chart(evolution_data).mark_rule(color='gray').encode(
        x='Fecha:T',
    ).transform_filter(
        nearest
    )

    # Put the five layers into a chart and bind the data
    evolution_chart = alt.layer(
        line, selectors, points, rules, text
    )

    return evolution_chart
evolution_chart = make_evolution_chart(evolution_data)

st.altair_chart(evolution_chart, use_container_width=True)
