import streamlit as st
from influxdb_client import InfluxDBClient
import pandas as pd

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
    ["24h", "7d", "30d"],
    index=0
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
            float(df["Temperatura"].iloc[-1]),
            1
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Temperatura actual",
                f"{temperatura_actual} °C"
            )

        # =====================================
        # GRÁFICA
        # =====================================

        st.subheader("Evolución de la temperatura")

        st.line_chart(
            df.set_index("Fecha")
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
