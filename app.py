import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Tickets - Sincronizado", layout="wide")

@st.cache_data
def cargar_datos_pro():
    df = pd.read_excel('tickets.xlsx')
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.dropna(how='all')

    df['INICIO'] = pd.to_datetime(df['INICIO'], dayfirst=True, errors='coerce')
    df['FIN'] = pd.to_datetime(df['FIN'], dayfirst=True, errors='coerce')

    def nombre_mes_año(fecha):
        if pd.isna(fecha): return None
        meses = {
            1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio',
            7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'
        }
        return f"{meses[fecha.month]} {fecha.year}"

    df['MES_INICIO_LABEL'] = df['INICIO'].apply(nombre_mes_año).fillna("Fecha Inválida")
    df['MES_CIERRE_LABEL'] = df['FIN'].apply(nombre_mes_año).fillna("Abierto")
    df['FACTURACIÓN'] = df['FACTURACIÓN'].astype(str).replace(['nan', 'None', ''], 'No facturado').str.strip()
    
    return df

try:
    df = cargar_datos_pro()
    opciones_cierre = sorted([m for m in df['MES_CIERRE_LABEL'].unique() if m != "Abierto"], reverse=True)
    mes_sel = st.sidebar.selectbox("Mes de Cierre", opciones_cierre)
    df_filtrado = df[df['MES_CIERRE_LABEL'] == mes_sel].copy()

    # --- MAPEO DE COLORES DINÁMICO ---
    # Obtenemos todos los meses únicos presentes para asignarles un color fijo
    todos_los_meses = list(df['MES_INICIO_LABEL'].unique()) + list(df['FACTURACIÓN'].unique())
    todos_los_meses = list(set(todos_los_meses)) # Quitar duplicados
    
    # Usamos una paleta de Plotly (puedes usar 'Prism', 'Safe', 'Bold', etc.)
    colores_lista = px.colors.qualitative.Prism
    mapa_colores = {mes: colores_lista[i % len(colores_lista)] for i, mes in enumerate(todos_los_meses)}
    mapa_colores["No facturado"] = "#BF00FF" # Forzamos rojo para lo no facturado

    st.title(f"📊 Reporte Sincronizado - {mes_sel}")

    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.pie(df_filtrado, names='MES_INICIO_LABEL', title="Origen (Apertura)",
                      hole=0.4, color='MES_INICIO_LABEL', color_discrete_map=mapa_colores)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = px.pie(df_filtrado, names='FACTURACIÓN', title="Mes de Facturación",
                      hole=0.4, color='FACTURACIÓN', color_discrete_map=mapa_colores)
        st.plotly_chart(fig2, use_container_width=True)

    # --- TABLA CON COLORES SINCRONIZADOS ---
    st.markdown("### Detalle de Tickets (Colores sincronizados con gráficas)")
    
    df_filtrado['MIN'] = pd.to_numeric(df_filtrado['MIN'], errors='coerce').fillna(0)
    df_filtrado = df_filtrado.sort_values(by='MIN', ascending=False)

    columnas_tabla = ['INICIO', 'MES_INICIO_LABEL', 'N° TICKET', 'FIN', 'FALLA', 'USUARIO', 'TECNICO', 'MIN', 'HORAS', 'FACTURACIÓN']
    cols_existentes = [c for c in columnas_tabla if c in df_filtrado.columns]

    def aplicar_colores_sincronizados(row):
        estilos = ['' for _ in row.index]
        
        # Color para la celda INICIO (basado en su mes de origen)
        if 'INICIO' in row.index:
            idx_ini = row.index.get_loc('INICIO')
            color_ini = mapa_colores.get(row['MES_INICIO_LABEL'], "#FFFFFF")
            estilos[idx_ini] = f'background-color: {color_ini}; color: white; font-weight: bold'
            
        # Color para la celda FACTURACIÓN (basado en el mes que dice la celda)
        if 'FACTURACIÓN' in row.index:
            idx_fac = row.index.get_loc('FACTURACIÓN')
            color_fac = mapa_colores.get(row['FACTURACIÓN'], "#FFFFFF")
            estilos[idx_fac] = f'background-color: {color_fac}; color: white; font-weight: bold'
            
        return estilos

    st.dataframe(
        df_filtrado[cols_existentes].style.apply(aplicar_colores_sincronizados, axis=1),
        use_container_width=True
    )

except Exception as e:
    st.error(f"Error: {e}")