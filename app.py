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

st.title("Estación Meteorológica Albufera")
st.markdown("Datos almacenados en InfluxDB Cloud")

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
    #df_dir = run_query("wind_direction")


    # =====================================
    # COMPROBAR DATOS
    # =====================================

    if (not df_temp.empty and not df_hum.empty and not df_uv.empty and not df_light.empty and not df_wind.empty):

        # Seleccionamos solo columnas útiles
        df_temp = df_temp[["_time", "_value"]]
        df_temp.columns = ["Fecha", "Temperatura"]

        df_hum = df_hum[["_time", "_value"]]
        df_hum.columns = ["Fecha", "Humedad"]

        df_uv = df_uv[["_time", "_value"]]
        df_uv.columns = ["Fecha", "Índice UV"]

        df_light = df_light[["_time", "_value"]]
        df_light.columns = ["Fecha", "Intensidad de la Luz"]

        # =====================================
        # DIRECCIÓN DEL VIENTO
        # =====================================

        df_wind = df_wind[["_time", "_value"]]
        df_wind.columns = ["Fecha", "Direccion"]

        # Convertir grados → sectores
        df_wind["Sector"] = df_wind["Direccion"].apply(wind_deg_to_dir)

        wind_counts = (df_wind.groupby("Sector").size().reset_index(name="Frecuencia"))

        wind_counts.rename(columns={"Sector": "Direccion"}, inplace=True)

        order = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"] # Orden para la rosa de los vientos

        wind_counts["Direccion"] = pd.Categorical(wind_counts["Direccion"], categories=order, ordered=True)

        wind_counts = wind_counts.sort_values("Direccion")

        # =====================================
        # MÉTRICA
        # =====================================

        temperatura_actual = round(float(df_temp["Temperatura"].iloc[-1]), 1)
        humedad_actual = round(float(df_hum["Humedad"].iloc[-1]), 1)

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

        st.divider()

        # =====================================
        # GRÁFICAS
        # =====================================

        col_temp, col_hum = st.columns(2)

        with col_temp:

            st.subheader("Evolución de la temperatura")
            fig = px.line(df_temp, x="Fecha", y="Temperatura")
            fig.update_layout(template="plotly_dark", height=450)
            st.plotly_chart(fig, use_container_width=True)


        with col_hum:

            st.subheader("Evolución de la humedad")
            fig = px.line(df_hum, x="Fecha", y="Humedad")
            fig.update_layout(template="plotly_dark", height=450)
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # =====================================
        # GRÁFICAS UV Y LUZ
        # =====================================

        col_uv, col_light = st.columns(2)

        with col_uv:

            st.subheader("Índice UV")

            if not df_uv.empty:

                uv_actual = float(df_uv["Índice UV"].iloc[-1])

                st.metric("UV actual", round(uv_actual, 2))

                fig = px.line(df_uv, x="Fecha", y="Índice UV")
                st.plotly_chart(fig, use_container_width=True)

        with col_light:

            st.subheader("Intensidad de la Luz")

            if not df_light.empty:

                fig = px.line(df_light, x="Fecha", y="Intensidad de la Luz")
                st.plotly_chart(fig, use_container_width=True)

        st.divider()
        # =====================================
        # GRÁFICAS VIENTO
        # =====================================
        st.subheader("Dirección del viento (grados)")

        fig_wind = px.line(df_wind, x="Fecha", y="Direccion")

        fig_wind.update_layout(template="plotly_dark", height=350)

        st.plotly_chart(fig_wind, use_container_width=True)


        # =====================================
        # ROSA DE LOS VIENTOS
        # =====================================

        st.subheader("Rosa de los vientos")

        fig = go.Figure()

        fig.add_trace(go.Barpolar(
            r=wind_counts["Frecuencia"],
            theta=wind_counts["Direccion"],
            name="Viento",
            marker_color="deepskyblue"
        ))

        fig.update_layout(
            template="plotly_dark",
            polar=dict(
                angularaxis=dict(direction="clockwise"),
                radialaxis=dict(showticklabels=True)
            ),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("No hay datos disponibles para el periodo seleccionado.")

except Exception as e:
    st.error(f"Error al consultar InfluxDB: {e}")


finally:
    client.close()
