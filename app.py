import streamlit as st
from influxdb_client import InfluxDBClient
import pandas as pd

st.set_page_config(page_title="IoT Dashboard", layout="wide")

st.title("Dashboard IoT")

# Conexión InfluxDB Cloud
client = InfluxDBClient(
    url=st.secrets["INFLUX_URL"],
    token=st.secrets["INFLUX_TOKEN"],
    org=st.secrets["INFLUX_ORG"]
)

query_api = client.query_api()

bucket = st.secrets["INFLUX_BUCKET"]

# Query ejemplo (cámbialo luego a tus datos reales)
query = f'''
from(bucket: "{bucket}")
|> range(start: -1h)
|> limit(n: 10)
'''

tables = query_api.query(query)

data = []
for table in tables:
    for record in table.records:
        data.append([record.get_time(), record.get_value()])

df = pd.DataFrame(data, columns=["time", "value"])

st.dataframe(df)

st.line_chart(df.set_index("time"))
