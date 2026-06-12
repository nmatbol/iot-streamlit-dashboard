import streamlit as st
from influxdb_client import InfluxDBClient
import pandas as pd
import plotly.express as px

# =====================================
# CONFIGURACIÓN DE LA PÁGINA
# =====================================

st.set_page_config(
    page_title="Estación Meteorológica Albufera",
    layout="wide"
)

st.title("Dashboard Albufera Weather Station")
st.markdown("Datos almacenados en InfluxDB Cloud")

# =====================================
# CONFIGURACIÓN INFLUXDB CLOUD
# =====================================

#INFLUX_URL = "https://eu-central-1-1.aws.cloud2.influxdata.com/"
#INFLUX_TOKEN = "hg475TtMSOO4U7dQVWIbijmK-1JFpfbhxUtmuS6QS4v-H3xNZ21k6XnEukiTVfzGNF4GZBVRvpvlR0cEqAofKg=="
#INFLUX_ORG = "UPV"
#INFLUX_BUCKET = "albuferaws"

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
    "Periodo",
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

# =====================================
# QUERY TEMPERATURA
# =====================================

query = f'''
from(bucket: "{bucket}")
  |> range(start: -{periodo})
  |> filter(fn: (r) => r._measurement == "weather_station")
  |> filter(fn: (r) => r._field == "temperature")
  |> sort(columns: ["_time"])
'''

try:

    df = query_api.query_data_frame(query)

    # Si Influx devuelve varios DataFrames, los unimos
    if isinstance(df, list):
        df = pd.concat(df, ignore_index=True)

    if not df.empty:

        # Seleccionamos solo columnas útiles
        df = df[["_time", "_value"]]

        df.columns = ["Fecha", "Temperatura"]

        # =====================================
        # MÉTRICA ACTUAL
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

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Temperatura actual",
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

        st.divider()

        # =====================================
        # GRÁFICA
        # =====================================

        st.subheader("Evolución de la temperatura")

        fig_temp = px.line(
            df,
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

        # =====================================
        # TABLA
        # =====================================

        with st.expander("Ver datos"):
            st.dataframe(
                df.sort_values(
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
