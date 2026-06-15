import streamlit as st
from influxdb_client import InfluxDBClient
import pandas as pd
import plotly.express as px

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
    [
        "30m",
        "1h",
        "3h",
        "6h",
        "12h",
        "24h",
        "2d",
        "7d",
        "30d",
        "90d",
        "180d"
    ],
    index=5
)

try:
    # =====================================
    # QUERY TEMPERATURA
    # =====================================

    query_temp = f'''
    from(bucket: "{bucket}")
      |> range(start: -{periodo})
      |> filter(fn: (r) => r._measurement == "weather_station")
      |> filter(fn: (r) => r._field == "temperature")
      |> sort(columns: ["_time"])
    '''

    df_temp = query_api.query_data_frame(query_temp)

    # Si Influx devuelve varios DataFrames, los unimos
    if isinstance(df_temp, list):
        df_temp = pd.concat(df_temp, ignore_index=True)

    # =====================================
    # QUERY HUMEDAD
    # =====================================

    query_hum = f'''
    from(bucket: "{bucket}")
      |> range(start: -{periodo})
      |> filter(fn: (r) => r._measurement == "weather_station")
      |> filter(fn: (r) => r._field == "humidity")
      |> sort(columns: ["_time"])
    '''

    df_hum = query_api.query_data_frame(query_hum)

    if isinstance(df_hum, list):
        df_hum = pd.concat(df_hum, ignore_index=True)

    # =====================================
    # COMPROBAR DATOS
    # =====================================

    if not df_temp.empty and not df_hum.empty:

        # Seleccionamos solo columnas útiles
        df_temp = df_temp[["_time", "_value"]]
        df_temp.columns = ["Fecha", "Temperatura"]

        df_hum = df_hum[["_time", "_value"]]
        df_hum.columns = ["Fecha", "Humedad"]

        # =====================================
        # MÉTRICAS TEMPERATURA
        # =====================================

        temperatura_actual = round(
            float(df["Temperatura"].iloc[-1]), 1
        )

        temperatura_max = round(
            float(df["Temperatura"].max()), 1
        )

        temperatura_min = round(
            float(df["Temperatura"].min()), 1
        )

        temperatura_media = round(
            float(df["Temperatura"].mean()), 1
        )

        # =====================================
        # MÉTRICAS HUMEDAD
        # =====================================

        humedad_actual = round(
            float(df_hum["Humedad"].iloc[-1]), 1
        )

        humedad_max = round(
            float(df_hum["Humedad"].max()), 1
        )

        humedad_min = round(
            float(df_hum["Humedad"].min()), 1
        )

        humedad_media = round(
            float(df_hum["Humedad"].mean()), 1
        )

        # =====================================
        # KPIs TEMPERATURA
        # =====================================

        st.subheader("Temperatura")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Actual",
                f"{temperatura_actual} °C"
            )

        with col2:
            st.metric(
                "Máxima",
                f"{temperatura_max} °C"
            )

        with col3:
            st.metric(
                "Mínima",
                f"{temperatura_min} °C"
            )

        with col4:
            st.metric(
                "Media",
                f"{temperatura_media} °C"
            )

        # =====================================
        # KPIs HUMEDAD
        # =====================================

        st.subheader("Humedad")

        col5, col6, col7, col8 = st.columns(4)

        with col5:
            st.metric(
                "Actual",
                f"{humedad_actual} % RH"
            )

        with col6:
            st.metric(
                "Máxima",
                f"{humedad_max} % RH"
            )

        with col7:
            st.metric(
                "Mínima",
                f"{humedad_min} % RH"
            )

        with col8:
            st.metric(
                "Media",
                f"{humedad_media} % RH"
            )

        st.divider()

        # =====================================
        # GRÁFICAS
        # =====================================

        col_temp, col_hum = st.columns(2)

        with col_temp:

            st.subheader("Evolución de la temperatura")

            fig_temp = px.line(
                df_temp,
                x="Fecha",
                y="Temperatura"
            )

            fig_temp.update_layout(
                template="plotly_dark",
                height=450,
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis_title="",
                yaxis_title="°C"
            )

            st.plotly_chart(
                fig_temp,
                use_container_width=True
            )

        with col_hum:

            st.subheader("Evolución de la humedad")

            fig_hum = px.line(
                df_hum,
                x="Fecha",
                y="Humedad"
            )

            fig_hum.update_layout(
                template="plotly_dark",
                height=450,
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis_title="",
                yaxis_title="% RH"
            )

            st.plotly_chart(
                fig_hum,
                use_container_width=True
            )



        # =====================================
        # TABLA
        # =====================================

        with st.expander("Ver datos de Temperatura"):
            st.dataframe(
                df.sort_values(
                    by="Fecha",
                    ascending=False
                ),
                use_container_width=True
            )

        with st.expander("Ver datos de Humedad"):
            st.dataframe(
                df_hum.sort_values(
                    by="Fecha",
                    ascending=False
                ),
                use_container_width=True
            )

    else:
        st.warning("No hay datos disponibles para el periodo seleccionado.")

except Exception as e:
    st.error(f"Error al consultar InfluxDB: {e}")


finally:
    client.close()
