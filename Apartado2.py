# Se prepara el entorno con las bibliotecas necesarias
import streamlit as st          # Para visualizar en web interactiva
import requests                 # Para realizar las peticiones API
import pandas as pd             # Para gestionar tablas y datos
from datetime import datetime   # Para utilizar formatos de fechas  
import pydeck as pdk            # Para mostrar mapas interactivos

# Se configura la pagina web completa con el nombre de la pestaña y la funcionalidad del menú About
st.set_page_config(
    layout="wide", 
    page_title="Consulta de carburantes - Apartado 2",
    menu_items={
        "About": "Aplicación para consultar estaciones de servicio y precios de carburantes. Actividad 3, apartado 2 de Tecnologías Emergentes"
    }
)

# Se definen las funciones a utilizar

#
# Función para hacer las llamadas a las peticiones API con una URL pasada por parámetro:
# - Llama a una API mediante una URL pasada por parámetro
# - Realiza un timeout de 10'' por si la llamada tarda demasiado
# - Devuelve los datos en formato JSON
# - Devuelve un error controlado
def get_json(url):
    try:
        r = requests.get(url, timeout=10)   # Llamada URL
        r.raise_for_status()                # Devuelve error para errores 403, 404, 500..
        return r.json()                     # Devuelve el json devuelto en una lista Python
    except:
        return None

# Datos para realizar la llamada a la API de consulta de Comunidades Autónomas. Devuelve una lista diccionario de código y nombre.
def listar_ccaa():
    url = "https://energia.serviciosmin.gob.es/ServiciosRestCarburantes/PreciosCarburantes/Listados/ComunidadesAutonomas/"
    datos = get_json(url)
    return {item["CCAA"]: item["IDCCAA"] for item in datos} if datos else {}

# Datos para realizar la llamada a la API de consulta de Provincias. Devuelve una lista diccionario de código y nombre.
def listar_provincias():
    url = "https://energia.serviciosmin.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/Listados/Provincias/"
    datos = get_json(url)
    return {item["Provincia"]: item["IDPovincia"] for item in datos} if datos else {}

# Datos para realizar la llamada a la API de consulta de Productos. Devuelve una lista diccionario de código y nombre.
def listar_productos():
    url = "https://energia.serviciosmin.gob.es/ServiciosRestCarburantes/PreciosCarburantes/Listados/ProductosPetroliferos/"
    datos = get_json(url)
    return {item["NombreProducto"]: item["IDProducto"] for item in datos} if datos else {}

# Datos para realizar la llamada a la API de estaciones terrestres por Comunnidad Autónoma. Devuelve una lista diccionario con todos los datos.
def estaciones_por_ccaa(id_ccaa):
    url = f"https://energia.serviciosmin.gob.es/ServiciosRestCarburantes/PreciosCarburantes/EstacionesTerrestres/FiltroCCAA/{id_ccaa}"
    datos = get_json(url)
    return datos.get("ListaEESSPrecio", []) if datos else []

# Datos para realizar la llamada a la API de postes marítimos por Provincia. Devuelve una lista diccionario con todos los datos.
def postes_por_provincia(id_provincia):
    url = f"https://energia.serviciosmin.gob.es/ServiciosRestCarburantes/PreciosCarburantes/PostesMaritimos/FiltroProvincia/{id_provincia}"
    datos = get_json(url)
    return datos.get("ListaEESSPrecio", []) if datos else []

# Datos para realizar la llamada a la API de estaciones terrestres por provincia, producto y fecha. Devuelve una lista diccionario con todos los datos.
def precios_por_provincia_fecha(id_provincia, fecha, id_producto):
    url = f"https://energia.serviciosmin.gob.es/ServiciosRestCarburantes/PreciosCarburantes/EstacionesTerrestresHist/FiltroProvinciaProducto/{fecha}/{id_provincia}/{id_producto}"
    datos = get_json(url)
    return datos.get("ListaEESSPrecio", []) if datos else []

# Para mostrar un mapa con las latitudes y longitudes de los datos seleccionados enviadas por parámetro.
def mostrar_mapa(df):
    # Renombrar columnas
    df.rename(columns={"Longitud (WGS84)": "Longitud", "Latitud (WGS84)": "Latitud"}, inplace=True)
    
    # Limpiar coordenadas
    df = df[df["Latitud"].astype(str).str.strip() != ""]
    df = df[df["Longitud"].astype(str).str.strip() != ""]
    
    # Convertir coordenadas a float y reemplazar "," por "."
    df["Latitud"] = df["Latitud"].astype(str).str.replace(",", ".", regex=False).astype(float)
    df["Longitud"] = df["Longitud"].astype(str).str.replace(",", ".", regex=False).astype(float)
    
    # Centrar el mapa automáticament en el promedio de todos los puntos a mostrar
    midpoint = (df["Latitud"].mean(), df["Longitud"].mean())

   # Capa de puntos
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[Longitud, Latitud]',
        get_radius=200,
        get_color=[0, 122, 255],
        pickable=True,
    )

    # Capa de mapa base (OpenStreetMap)
    tile_layer = pdk.Layer(
        "TileLayer",
        data=None,
        min_zoom=0,
        max_zoom=19,
        tile_size=256,
        url_template="https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png"
    )

    # Muestra el Rótulo de la API de la estación al pasar el ratón por encima
    tooltip = {
        "html": "<b>{Rótulo}</b>",
        "style": {"backgroundColor": "white", "color": "black"}
    }

    # Configuración vista inicial
    view_state = pdk.ViewState(
        latitude=midpoint[0],
        longitude=midpoint[1],
        zoom=10,
        pitch=0,
    )

    # Muestra el mapa
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=view_state,
        layers=[tile_layer, scatter_layer],
        tooltip=tooltip
    ))

# Se carga la consulta de Comunidades Autónomas por defecto
if "vista" not in st.session_state:
    st.session_state["vista"] = "ccaa"   # Vista por defecto

# Función para cambiar de vista
def cambiar_vista(v):
    st.session_state["vista"] = v

# Título de la página centrado
st.markdown(
    "<h1 style='text-align:center;'>Consulta de carburantes - Apartado 2</h1>",
    unsafe_allow_html=True
)

# Se muestran y configuran los botones para navegar a cada una de las consultas
izquierda, colA, colB, colC, derecha = st.columns([1, 1, 1, 1, 1])

with colA:
    st.button("Estaciones por CCAA", on_click=cambiar_vista, args=("ccaa",))

with colB:
    st.button("Postes marítimos", on_click=cambiar_vista, args=("postes",))

with colC:
    st.button("Precios por provincia y día", on_click=cambiar_vista, args=("precios",))


# Se llaman a las 3 APIS para guardar los datos maestros de Comunidades Autónomas, Provincias y Productos
ccaa_dict = listar_ccaa()
prov_dict = listar_provincias()
prod_dict = listar_productos()

# 1.- Consulta de estaciones por Comunidad Autónoma
if st.session_state["vista"] == "ccaa":

    st.header("Estaciones de servicio por Comunidad Autónoma")
    
    # Desplegable con las Comunidades Autónomas seleccionadas de la API
    ccaa_sel = st.selectbox("Selecciona una Comunidad Autónoma", list(ccaa_dict.keys()))
    
    # Al seleccionar una CCAA se realiza la llamada a la API estaciones por CCAA para mostrar los datos.
    id_ccaa = ccaa_dict[ccaa_sel]
    estaciones = estaciones_por_ccaa(id_ccaa)

    df1 = pd.DataFrame(estaciones)

    # Se muestran las columnas deseadas
    cols_drop = [
        c for c in df1.columns 
        if "Precio" in c 
        or "Producto" in c 
        or "Bio" in c 
        or "Éster" in c 
        or "Ester" in c
    ]
    df1 = df1.drop(columns=cols_drop, errors="ignore")

    # Contador de registros encontrados
    st.subheader(f"Estaciones encontradas: {len(df1)}")
    st.dataframe(df1, use_container_width=True, height=500)

    df1.rename(columns={"Longitud (WGS84)": "Longitud", "Latitud (WGS84)": "Latitud"}, inplace=True)

    # Se muestra el mapa con los valores seleccionados de la API
    if "Latitud" in df1.columns and "Longitud" in df1.columns:
        st.subheader("Mapa de estaciones")
        mostrar_mapa(df1)

# 2.- Consulta de postes por provincia
elif st.session_state["vista"] == "postes":

    st.header("Postes marítimos por Provincia")
    
    # Desplegable con las Provincias seleccionadas de la API
    prov_sel = st.selectbox("Selecciona una provincia", list(prov_dict.keys()))
    
    # Al seleccionar una Provincia se realiza la llamada a la API postes marítimos por Provincia para mostrar los datos.
    id_prov = prov_dict[prov_sel]
    postes = postes_por_provincia(id_prov)

    df2 = pd.DataFrame(postes)

    # Se muestran las columnas deseadas
    cols_drop = [c for c in df2.columns if "Precio" in c or "Producto" in c]
    df2 = df2.drop(columns=cols_drop, errors="ignore")

    # Contador de registros encontrados
    st.subheader(f"Postes marítimos encontrados: {len(df2)}")
    st.dataframe(df2, use_container_width=True, height=500)

    df2.rename(columns={"Longitud (WGS84)": "Longitud", "Latitud (WGS84)": "Latitud"}, inplace=True)

    if "Latitud" in df2.columns and "Longitud" in df2.columns:
        st.subheader("Mapa de postes marítimos")
        mostrar_mapa(df2)

# 3.- Consulta de precios por provincia y fecha
elif st.session_state["vista"] == "precios":

    st.header("Precios de carburantes por Provincia, Producto y Día")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Desplegable con los Provincias seleccionadas de la API
        prov_sel2 = st.selectbox("Provincia", list(prov_dict.keys()))

    with col2:
        # Objeto para seleccionar una fecha
        fecha_sel = st.date_input("Fecha", datetime.today())

    with col3:
        # Desplegable con los Productos seleccionados de la API
        prod_sel2 = st.selectbox("Carburante", list(prod_dict.keys()))

    id_prov2 = prov_dict[prov_sel2]
    id_prod2 = prod_dict[prod_sel2]
    fecha_api = fecha_sel.strftime("%d-%m-%Y")
   
    precios = precios_por_provincia_fecha(id_prov2, fecha_api, id_prod2)

    if not precios:
        st.warning("⚠ No hay datos disponibles para esta combinación de provincia, fecha y carburante.")
        st.stop()

    df3 = pd.DataFrame(precios)

    # Asegurar que la columna PrecioProducto existe
    if "PrecioProducto" not in df3.columns:
        df3["PrecioProducto"] = None

    # Filtrar solo estaciones con precio válido
    df3 = df3[
        df3["PrecioProducto"].notna() &
        (df3["PrecioProducto"] != "") &
        (df3["PrecioProducto"] != "0,000")
    ]

    if df3.empty:
        st.warning("⚠ No hay estaciones con precio válido para este carburante.")
        st.stop()

    # Limpiar coordenadas consultas anteriores
    for col in ["Latitud", "Longitud", "Longitud (WGS84)"]:
        if col in df3.columns:
            df3.drop(columns=[col], inplace=True)

    # Añadir las coordenadas para poder pintar el mapa
    df3["Latitud"] = pd.Series(precios).apply(lambda x: x.get("Latitud"))
    df3["Longitud"] = pd.Series(precios).apply(lambda x: x.get("Longitud (WGS84)"))

    # Renombrar longitud
    df3.rename(columns={"Longitud (WGS84)": "Longitud"}, inplace=True)

    # Convertir coordenadas a float
    df3 = df3[df3["Latitud"].astype(str).str.strip() != ""]
    df3 = df3[df3["Longitud"].astype(str).str.strip() != ""]

    df3["Latitud"] = df3["Latitud"].astype(str).str.replace(",", ".", regex=False).astype(float)
    df3["Longitud"] = df3["Longitud"].astype(str).str.replace(",", ".", regex=False).astype(float)

    # Seleccionar columnas deseadas
    columnas = ["Rótulo", "Dirección", "Localidad", "Municipio", "PrecioProducto", "Latitud", "Longitud"]
    df3 = df3[[c for c in columnas if c in df3.columns]]

    # Contador de registros encontrados
    st.subheader(f"Registros encontrados: {len(df3)}")
    st.dataframe(df3, use_container_width=True, height=500)

    # Mostrar mapa solo si hay coordenadas válidas
    if df3["Latitud"].notna().any() and df3["Longitud"].notna().any():
        st.subheader("Mapa de estaciones con precio disponible")
        mostrar_mapa(df3)
    else:
        st.info("No hay coordenadas disponibles para mostrar el mapa.")