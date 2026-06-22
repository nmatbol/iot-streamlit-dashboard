import streamlit as st
from influxdb_client import InfluxDBClient
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =====================================
# CONFIGURACIÓN DE LA PÁGINA
# =====================================

st.set_page_config(
    page_title="Albufera Weather Station",
    layout="wide"
)

st.title("Estación Meteorológica Parque Natural de la Albufera de Valencia")
st.markdown("""
    ### Sobre esta estación
    Esta estación monitoriza en tiempo real las condiciones climatológicas del 
    **Parque Natural de la Albufera de Valencia**. 

    Los datos son recopilados y procesados por el **Grupo de Redes de Computadores (GRC)** de la Universidad Politécnica de Valencia (UPV).
    """)

# =====================================
# CONFIGURACIÓN INFLUXDB CLOUD
# =====================================

client = InfluxDBClient(
    url=st.secrets["INFLUX_URL"],
    token=st.secrets["INFLUX_TOKEN"],
    org=st.secrets["INFLUX_ORG"]
)

query_api = client.query_api()
bucket = st.secrets["INFLUX_BUCKET"]

# =====================================
# SELECTOR TEMPORAL
# =====================================

periodo = st.sidebar.selectbox(
    "Periodo de tiempo",
    ["30m", "1h", "3h", "6h", "12h", "24h", "2d", "7d", "30d", "90d", "180d"],
    index=5
)

def wind_deg_to_dir(deg):
    if pd.isna(deg):
        return None
    if deg < 22.5 or deg >= 337.5:
        return "N"
    elif deg < 67.5:
        return "NE"
    elif deg < 112.5:
        return "E"
    elif deg < 157.5:
        return "SE"
    elif deg < 202.5:
        return "S"
    elif deg < 247.5:
        return "SW"
    elif deg < 292.5:
        return "W"
    else:
        return "NW"

try:
    def run_query(field):
        # =====================================
        # QUERY GENERAL
        # =====================================
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -{periodo})
          |> filter(fn: (r) => r._measurement == "weather_station")
          |> filter(fn: (r) => r._field == "{field}")
          |> sort(columns: ["_time"])
        '''
        df = query_api.query_data_frame(query)
        # Si Influx devuelve varios DataFrames, los unimos
        if isinstance(df, list):
            df = pd.concat(df, ignore_index=True)
        return df

    # Queries
    df_temp = run_query("temperature")
    df_hum = run_query("humidity")
    df_uv = run_query("uv")
    df_light = run_query("light")
    df_wind = run_query("wind_direction")
    df_pressure = run_query("pressure")
    df_rain = run_query("rain")
    df_rain_total = run_query("rain_total")




    # =====================================
    # COMPROBAR DATOS
    # =====================================

    if not df_temp.empty:
        # Seleccionamos solo columnas útiles
        df_temp = df_temp[["_time", "_value"]].rename(columns={"_time": "Fecha", "_value": "Temperatura"})
    if not df_hum.empty:
        df_hum = df_hum[["_time", "_value"]].rename(columns={"_time": "Fecha", "_value": "Humedad"})
    if not df_uv.empty:
        df_uv = df_uv[["_time", "_value"]].rename(columns={"_time": "Fecha", "_value": "Índice UV"})
    if not df_light.empty:
        df_light = df_light[["_time", "_value"]].rename(columns={"_time": "Fecha", "_value": "Intensidad de la Luz"})
    if not df_pressure.empty:
        df_pressure = df_pressure[["_time", "_value"]].rename(columns={"_time": "Fecha", "_value": "Presión"})
    if not df_rain.empty:
        df_rain = df_rain[["_time", "_value"]].rename(columns={"_time": "Fecha", "_value": "Lluvia"})
    if not df_rain_total.empty:
         df_rain_total = df_rain_total[["_time", "_value"]].rename(columns={"_time": "Fecha", "_value": "LluviaTotal"})

        # =====================================
        # DIRECCIÓN DEL VIENTO
        # =====================================
    if not df_wind.empty:
        df_wind = df_wind[["_time", "_value"]].rename(columns={"_time": "Fecha", "_value": "Direccion"})
        # Convertir grados → sectores
        df_wind["Sector"] = df_wind["Direccion"].apply(wind_deg_to_dir)

        # =====================================
        # MÉTRICAS PRINCIPALES
        # =====================================

        temperatura_actual = round(float(df_temp["Temperatura"].iloc[-1]), 1)
        humedad_actual = round(float(df_hum["Humedad"].iloc[-1]), 1)
        presion_actual = round(float(df_pressure["Presión"].iloc[-1]), 1)
        lluvia_actual = round(float(df_rain["Lluvia"].iloc[-1]), 1)

        st.subheader("Temperatura")
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Actual", f"{temperatura_actual} °C")
        col2.metric("Máxima", f"{df_temp['Temperatura'].max():.1f} °C")
        col3.metric("Mínima", f"{df_temp['Temperatura'].min():.1f} °C")
        col4.metric("Media", f"{df_temp['Temperatura'].mean():.1f} °C")

        st.subheader("Humedad")
        col5, col6, col7, col8 = st.columns(4)

        col5.metric("Actual", f"{humedad_actual} % RH")
        col6.metric("Máxima", f"{df_hum['Humedad'].max():.1f} % RH")
        col7.metric("Mínima", f"{df_hum['Humedad'].min():.1f} % RH")
        col8.metric("Media", f"{df_hum['Humedad'].mean():.1f} % RH")

        st.subheader("Presión atmosférica")
        col9, col10, col11, col12 = st.columns(4)

        col9.metric("Actual", f"{presion_actual} Pa")
        col10.metric("Máxima", f"{df_pressure['Presión'].max():.1f} Pa")
        col11.metric("Mínima", f"{df_pressure['Presión'].min():.1f} Pa")
        col12.metric("Media", f"{df_pressure['Presión'].mean():.1f} Pa")

        st.subheader("Lluvia")
        col13, col14, col15, col16 = st.columns(4)

        col13.metric("Actual", f"{lluvia_actual} mm")
        col14.metric("Máxima", f"{df_rain['Lluvia'].max():.1f} mm")
        col15.metric("Mínima", f"{df_rain['Lluvia'].min():.1f} mm")
        col16.metric("Media", f"{df_rain['Lluvia'].mean():.1f} mm")

        st.divider()

        # =====================================
        # GRÁFICAS
        # =====================================

        col_temp, col_hum = st.columns(2)

        with col_temp:
            st.subheader("Evolución de la temperatura")
            if not df_temp.empty:
                fig = px.line(df_temp, x="Fecha", y="Temperatura")
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de temperatura.")

        with col_hum:
            st.subheader("Evolución de la humedad")
            if not df_hum.empty:
                fig = px.line(df_hum, x="Fecha", y="Humedad")
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de humedad.")

        st.divider()

        # =====================================
        # GRÁFICAS UV Y LUZ
        # =====================================

        col_uv, col_light = st.columns(2)

        with col_uv:
            st.subheader("Índice UV")
            if not df_uv.empty:
                st.metric("UV actual", round(float(df_uv["Índice UV"].iloc[-1]), 2))
                fig = px.line(df_uv, x="Fecha", y="Índice UV")
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de índice UV.")

        with col_light:
            st.subheader("Intensidad de la Luz")
            if not df_light.empty:
                fig = px.line(df_light, x="Fecha", y="Intensidad de la Luz")
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de intensidad de luz.")

        st.divider()

        # =========================================
        # GRÁFICAS DEL VIENTO Y ROSA DE LOS VIENTOS
        # =========================================
        col_v1, col_v2 = st.columns(2)

        with col_v1:
            st.subheader("Histórico Dirección del Viento (Grados)")
            if not df_wind.empty:
                fig_wind = px.line(df_wind, x="Fecha", y="Direccion")
                fig_wind.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350)
                st.plotly_chart(fig_wind, use_container_width=True)
            else:
                st.info("No hay datos de la dirección del viento.")

        with col_v2:
            st.subheader("Rosa de los vientos")
            if not df_wind.empty and not df_wind["Sector"].dropna().empty:
                # Reconstrucción robusta de frecuencias para la Rosa de los Vientos
                order = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
                wind_counts = df_wind.groupby("Sector").size().reindex(order, fill_value=0).reset_index(name="Frecuencia")

                fig_rose = go.Figure()
                fig_rose.add_trace(go.Barpolar(r=wind_counts["Frecuencia"], theta=wind_counts["Sector"], name="Viento", marker_color="deepskyblue"))
                fig_rose.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, polar=dict(angularaxis=dict(direction="clockwise", period=8), radialaxis=dict(showticklabels=True)), showlegend=False)
                st.plotly_chart(fig_rose, use_container_width=True)
            else:
                st.info("No hay datos suficientes para generar la rosa de los vientos.")

        st.divider()

        # =====================================
        # GRÁFICAS PRESIÓN Y PRECIPITACIÓN
        # =====================================
        col_p, col_r = st.columns(2)

        with col_p:
            st.subheader("Presión atmosférica")
            if not df_pressure.empty:
                fig_pressure = px.line(df_pressure, x="Fecha", y="Presión")
                fig_pressure.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, yaxis_title="Pa", xaxis_title="")
                fig_pressure.add_hline(y=101325, line_dash="dash", annotation_text="Presión estándar (Pa)") # 1013.25hPa = 101325Pa
                st.plotly_chart(fig_pressure, use_container_width=True)
            else:
                st.info("No hay datos de presión.")

        with col_r:
            st.subheader("Precipitación")
            if not df_rain.empty:
                fig_rain = px.bar(df_rain, x="Fecha", y="Lluvia")
                fig_rain.update_traces(width=86400000)  # 1 día en milisegundos
                fig_rain.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, xaxis_title="", yaxis_title="mm")
                st.plotly_chart(fig_rain, use_container_width=True)
            else:
                st.info("No hay datos de precipitación.")

        st.divider()

        # =====================================
        # MAPA DE LA UBICACIÓN DE LA WS
        # =====================================
        st.subheader("Ubicación de la Estación Meteorológica")
        lat_WS = 39.31555876334838
        lon_WS = -0.31919030831476836

        # Creamos un diccionario con las coordenadas y lo convertimos a DataFrame
        coordenadas_WS = {'lat': lat_WS,  'lon': lon_WS, 'Nombre': ['Estación GRC - UPV (Albufera)']}
        df_mapa = pd.DataFrame(coordenadas_WS)

        # Mostramos el mapa interactivo
        #st.map(df_mapa, zoom=13, use_container_width=True)


        # Mapa interactivo con Plotly Express
        fig_mapa = px.scatter_mapbox(df_mapa, lat="lat", lon="lon", hover_name="Nombre", color_discrete_sequence=["#ff4b4b"], size_max=15, zoom=13)

        # Estilo y color del mapa
        fig_mapa.update_layout(mapbox_style="carto-positron", mapbox=dict(center=dict(lat=lat_WS, lon=lon_WS), ), margin={"r":0,"t":0,"l":0,"b":0}, height=400)

        st.plotly_chart(fig_mapa, use_container_width=True)



except Exception as e:
    st.error(f"Error al consultar InfluxDB: {e}")


finally:
    client.close()
