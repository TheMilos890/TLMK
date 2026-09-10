import streamlit as st
import pandas as pd

# Configuración de la página del Dashboard
st.set_page_config(page_title="Dashboard de Trámites por Ejecutivo y Mes", page_icon="📊", layout="wide")

# --- CONTROL DE NAVEGACIÓN Y ESTADO ---
if 'pagina_actual' not in st.session_state:
    st.session_state.pagina_actual = "dashboard"
if 'detalle_seleccion' not in st.session_state:
    st.session_state.detalle_seleccion = {"ejecutivo": None, "categoria": None}
if 'ediciones_guardadas' not in st.session_state:
    st.session_state.ediciones_guardadas = {}

def cambiar_pagina(pagina):
    st.session_state.pagina_actual = pagina
    st.rerun()

def ir_a_detalle(ejecutivo, categoria):
    st.session_state.detalle_seleccion = {"ejecutivo": ejecutivo, "categoria": categoria}
    st.session_state.pagina_actual = "detalle"
    st.rerun()

def volver_al_dashboard():
    st.session_state.pagina_actual = "dashboard"
    st.session_state.detalle_seleccion = {"ejecutivo": None, "categoria": None}
    st.rerun()

# 1. Widget para subir el archivo Excel (disponible en la barra lateral)
uploaded_file = st.sidebar.file_uploader("📁 Sube tu archivo Excel (.xlsx o .xls)", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Cargar nuevo archivo y mantener modificaciones previas
        if 'df_global' not in st.session_state or st.session_state.get('uploaded_file_name') != uploaded_file.name:
            df = pd.read_excel(uploaded_file, sheet_name="ReporteValidacion")
            df.columns = df.columns.astype(str).str.strip()
            
            columnas_requeridas = ['DNI', 'EJECUTIVO', 'ESTADO', 'V_CANTADAS', 'F_VENTA']
            faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if faltantes:
                st.error(f"Faltan las siguientes columnas obligatorias: {', '.join(faltantes)}")
                st.stop()
            
            if 'OBSERVACION' not in df.columns:
                df['OBSERVACION'] = ""
            if 'ESTADO_RESCATE' not in df.columns:
                df['ESTADO_RESCATE'] = ""
            if 'FECHA_GESTION' not in df.columns:
                df['FECHA_GESTION'] = ""
            
            # Limpieza y preparación
            df['EJECUTIVO'] = df['EJECUTIVO'].astype(str).str.strip().str.upper()
            df['ESTADO'] = df['ESTADO'].astype(str).str.strip().str.upper()
            df['V_CANTADAS'] = df['V_CANTADAS'].astype(str).str.strip().str.upper()
            df['DNI'] = df['DNI'].astype(str).str.strip()
            df['OBSERVACION'] = df['OBSERVACION'].astype(str).fillna("")
            df['ESTADO_RESCATE'] = df['ESTADO_RESCATE'].astype(str).fillna("")
            df['FECHA_GESTION'] = df['FECHA_GESTION'].astype(str).fillna("")

            # Recuperar ediciones guardadas en memoria para no perder datos al subir un archivo nuevo
            for idx, row in df.iterrows():
                dni = row['DNI']
                if dni in st.session_state.ediciones_guardadas:
                    df.at[idx, 'OBSERVACION'] = st.session_state.ediciones_guardadas[dni].get('OBSERVACION', "")
                    df.at[idx, 'ESTADO_RESCATE'] = st.session_state.ediciones_guardadas[dni].get('ESTADO', "")
            
            # Conversión estricta de fecha con formato DD/MM/YYYY
            fechas_convertidas = pd.to_datetime(df['F_VENTA'], format='%d/%m/%Y', errors='coerce')
            fechas_convertidas = fechas_convertidas.fillna(pd.to_datetime(df['F_VENTA'], errors='coerce'))
            
            df['MES_VENTA'] = fechas_convertidas.dt.to_period('M').astype(str)
            df['MES_VENTA'] = df['MES_VENTA'].fillna('SIN FECHA').replace('NAT', 'SIN FECHA')
            
            st.session_state.df_global = df
            st.session_state.uploaded_file_name = uploaded_file.name

        df = st.session_state.df_global

        # --- MENÚ DE NAVEGACIÓN EN BARRA LATERAL ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("📌 Menú de Navegación")
        if st.sidebar.button("📊 Dashboard Principal", use_container_width=True):
            volver_al_dashboard()
        if st.sidebar.button("⚠️ Gestión de Observadas (Editable)", use_container_width=True):
            cambiar_pagina("observadas")

        # ==========================================
        # VISTA 1: DASHBOARD PRINCIPAL
        # ==========================================
        if st.session_state.pagina_actual == "dashboard":
            st.title("📊 Dashboard de Control de Trámites")
            st.markdown("Filtra los datos por **Ejecutivo** y por **Mes de Venta** (`F_VENTA`).")

            st.markdown("---")
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                lista_ejecutivos = sorted([str(e) for e in df['EJECUTIVO'].unique() if str(e) != 'NAN'])
                lista_ejecutivos.insert(0, "TODOS")
                ejecutivo_seleccionado = st.selectbox("👤 Filtrar por Ejecutivo:", options=lista_ejecutivos)
                
            with col_f2:
                meses_unicos = [str(m) for m in df['MES_VENTA'].unique() if str(m) != 'SIN FECHA']
                lista_meses = sorted(meses_unicos, reverse=True)
                if 'SIN FECHA' in df['MES_VENTA'].values:
                    lista_meses.append('SIN FECHA')
                lista_meses.insert(0, "TODOS")
                mes_seleccionado = st.selectbox("📅 Filtrar por Mes de Venta (F_VENTA):", options=lista_meses)
            
            df_trabajo = df.copy()
            if ejecutivo_seleccionado != "TODOS":
                df_trabajo = df_trabajo[df_trabajo['EJECUTIVO'] == ejecutivo_seleccionado]
            if mes_seleccionado != "TODOS":
                df_trabajo = df_trabajo[df_trabajo['MES_VENTA'] == mes_seleccionado]
            
            cant_formalizadas = df_trabajo[df_trabajo['ESTADO'] == "WF FORMALIZADO"]['DNI'].nunique()
            cant_presentadas = df_trabajo[df_trabajo['ESTADO'] == "WF PRESENTADO"]['DNI'].nunique()
            cant_observadas = df_trabajo[df_trabajo['V_CANTADAS'] == "OBSERVADA"]['DNI'].nunique()
            cant_devueltas = df_trabajo[df_trabajo['ESTADO'] == "WF DEVUELTO"]['DNI'].nunique()
            
            st.markdown("---")
            st.subheader(f"Resumen de Métricas (Ejecutivo: {ejecutivo_seleccionado} | Mes: {mes_seleccionado})")
            
            cols = st.columns(4)
            with cols[0]:
                st.metric(label="FORMALIZADAS", value=cant_formalizadas)
            with cols[1]:
                st.metric(label="PRESENTADAS", value=cant_presentadas)
            with cols[2]:
                st.metric(label="OBSERVADAS", value=cant_observadas)
            with cols[3]:
                st.metric(label="DEVUELTAS", value=cant_devueltas)
                
            st.markdown("---")
            st.subheader("📋 Resumen Consolidado por Ejecutivo")
            
            df_tabla_base = df.copy()
            if mes_seleccionado != "TODOS":
                df_tabla_base = df_tabla_base[df_tabla_base['MES_VENTA'] == mes_seleccionado]
            if ejecutivo_seleccionado != "TODOS":
                df_tabla_base = df_tabla_base[df_tabla_base['EJECUTIVO'] == ejecutivo_seleccionado]
                
            df_f_form = df_tabla_base[df_tabla_base['ESTADO'] == "WF FORMALIZADO"]
            df_f_pres = df_tabla_base[df_tabla_base['ESTADO'] == "WF PRESENTADO"]
            df_f_obs  = df_tabla_base[df_tabla_base['V_CANTADAS'] == "OBSERVADA"]
            df_f_dev  = df_tabla_base[df_tabla_base['ESTADO'] == "WF DEVUELTO"]
            df_f_rech = df_tabla_base[df_tabla_base['V_CANTADAS'] == "RECHAZADA"]
            df_f_pend = df_tabla_base[df_tabla_base['V_CANTADAS'] == "PENDIENTE"]
            
            res_form = df_f_form.groupby('EJECUTIVO')['DNI'].nunique().rename('FORMALIZADAS')
            res_pres = df_f_pres.groupby('EJECUTIVO')['DNI'].nunique().rename('PRESENTADAS')
            res_obs  = df_f_obs.groupby('EJECUTIVO')['DNI'].nunique().rename('OBSERVADAS')
            res_dev  = df_f_dev.groupby('EJECUTIVO')['DNI'].nunique().rename('DEVUELTAS')
            res_rech = df_f_rech.groupby('EJECUTIVO')['DNI'].nunique().rename('RECHAZADAS')
            res_pend = df_f_pend.groupby('EJECUTIVO')['DNI'].nunique().rename('PENDIENTES')
            
            df_resumen_ejecutivos = pd.concat([res_form, res_pres, res_obs, res_dev, res_rech, res_pend], axis=1).fillna(0).astype(int)
            df_resumen_ejecutivos['TOTAL'] = df_resumen_ejecutivos.sum(axis=1)
            df_resumen_ejecutivos = df_resumen_ejecutivos.sort_values(by='TOTAL', ascending=False).reset_index()
            df_resumen_ejecutivos.index = range(1, len(df_resumen_ejecutivos) + 1)
            
            df_estilizado = df_resumen_ejecutivos.style.set_properties(
                **{'text-align': 'center'}, subset=['FORMALIZADAS', 'PRESENTADAS', 'OBSERVADAS', 'DEVUELTAS', 'RECHAZADAS', 'PENDIENTES', 'TOTAL']
            ).set_properties(
                **{'text-align': 'left'}, subset=['EJECUTIVO']
            )
            
            st.dataframe(df_estilizado, use_container_width=True)
            
            st.markdown("### 🔍 Ver Detalle Específico")
            col_sel1, col_sel2, col_sel3 = st.columns([2, 2, 1])
            with col_sel1:
                ejecutivo_elegido = st.selectbox("Selecciona Ejecutivo:", options=df_resumen_ejecutivos['EJECUTIVO'].tolist(), key="sel_ejec_detalle")
            with col_sel2:
                categoria_elegida = st.selectbox("Selecciona Categoría:", options=['FORMALIZADAS', 'PRESENTADAS', 'OBSERVADAS', 'DEVUELTAS', 'RECHAZADAS', 'PENDIENTES', 'TOTAL'], key="sel_cat_detalle")
            with col_sel3:
                st.write("")
                st.write("")
                if st.button("🚀 Ver Detalle", type="primary"):
                    ir_a_detalle(ejecutivo_elegido, categoria_elegida)

        # ==========================================
        # VISTA 2: PÁGINA DE DETALLE ESPECÍFICO
        # ==========================================
        elif st.session_state.pagina_actual == "detalle":
            ejecutivo_actual = st.session_state.detalle_seleccion["ejecutivo"]
            categoria_actual = st.session_state.detalle_seleccion["categoria"]

            if not ejecutivo_actual or not categoria_actual:
                volver_al_dashboard()

            if st.button("⬅️ Volver al Dashboard Principal"):
                volver_al_dashboard()

            st.title(f"📄 Detalle de Registros: {ejecutivo_actual}")
            st.subheader(f"Categoría: {categoria_actual}")
            st.markdown("---")

            df_base_ejecutivo = df[df['EJECUTIVO'] == ejecutivo_actual]

            if categoria_actual == 'FORMALIZADAS':
                df_detalle_final = df_base_ejecutivo[df_base_ejecutivo['ESTADO'] == "WF FORMALIZADO"]
            elif categoria_actual == 'PRESENTADAS':
                df_detalle_final = df_base_ejecutivo[df_base_ejecutivo['ESTADO'] == "WF PRESENTADO"]
            elif categoria_actual == 'OBSERVADAS':
                df_detalle_final = df_base_ejecutivo[df_base_ejecutivo['V_CANTADAS'] == "OBSERVADA"]
            elif categoria_actual == 'DEVUELTAS':
                df_detalle_final = df_base_ejecutivo[df_base_ejecutivo['ESTADO'] == "WF DEVUELTO"]
            elif categoria_actual == 'RECHAZADAS':
                df_detalle_final = df_base_ejecutivo[df_base_ejecutivo['V_CANTADAS'] == "RECHAZADA"]
            elif categoria_actual == 'PENDIENTES':
                df_detalle_final = df_base_ejecutivo[df_base_ejecutivo['V_CANTADAS'] == "PENDIENTE"]
            else:
                df_detalle_final = df_base_ejecutivo[
                    (df_base_ejecutivo['ESTADO'].isin(["WF FORMALIZADO", "WF PRESENTADO", "WF DEVUELTO"])) | 
                    (df_base_ejecutivo['V_CANTADAS'].isin(["OBSERVADA", "RECHAZADA", "PENDIENTE"]))
                ]

            st.info(f"Mostrando **{len(df_detalle_final)}** registros en total (**{df_detalle_final['DNI'].nunique()}** DNI únicos).")
            st.dataframe(df_detalle_final, use_container_width=True)

        # ==========================================
        # VISTA 3: APARTADO NETAMENTE DE "OBSERVADAS" (EDITABLE)
        # ==========================================
        elif st.session_state.pagina_actual == "observadas":
            if st.button("⬅️ Volver al Dashboard Principal"):
                volver_al_dashboard()

            st.title("⚠️ Apartado Exclusivo: Trámites OBSERVADAS")
            st.markdown("Filtra por mes y modifica en **tiempo real**. Las ediciones se mantendrán incluso si subes un archivo nuevo.")

            df_obs_completo = df[df['V_CANTADAS'] == "OBSERVADA"].copy()

            if len(df_obs_completo) == 0:
                st.warning("No hay registros con estado OBSERVADA en el archivo actual.")
            else:
                # --- FILTRO POR MES ---
                meses_unicos_obs = [str(m) for m in df_obs_completo['MES_VENTA'].unique() if str(m) != 'SIN FECHA']
                lista_meses_obs = sorted(meses_unicos_obs, reverse=True)
                if 'SIN FECHA' in df_obs_completo['MES_VENTA'].values:
                    lista_meses_obs.append('SIN FECHA')
                lista_meses_obs.insert(0, "TODOS")
                
                mes_seleccionado_obs = st.selectbox("📅 Filtrar Observadas por Mes de Venta:", options=lista_meses_obs, key="filtro_mes_obs")
                
                if mes_seleccionado_obs != "TODOS":
                    df_obs_completo = df_obs_completo[df_obs_completo['MES_VENTA'] == mes_seleccionado_obs]

                # Conversión de F_VENTA para ordenamiento correcto
                df_obs_completo['F_VENTA_DT'] = pd.to_datetime(df_obs_completo['F_VENTA'], format='%d/%m/%Y', errors='coerce')
                df_obs_completo['F_VENTA_DT'] = df_obs_completo['F_VENTA_DT'].fillna(pd.to_datetime(df_obs_completo['F_VENTA'], errors='coerce'))
                df_obs_completo = df_obs_completo.sort_values(by='F_VENTA_DT', ascending=True)
                df_obs_completo['F_VENTA_STR'] = df_obs_completo['F_VENTA_DT'].dt.strftime('%d.%m.%y').fillna(df_obs_completo['F_VENTA'].astype(str))

                # Procesar FECHA_GESTION para HORA_OBS y T_ESPERA
                df_obs_completo['FECHA_GESTION_DT'] = pd.to_datetime(df_obs_completo['FECHA_GESTION'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
                df_obs_completo['FECHA_GESTION_DT'] = df_obs_completo['FECHA_GESTION_DT'].fillna(pd.to_datetime(df_obs_completo['FECHA_GESTION'], errors='coerce'))
                df_obs_completo['HORA_OBS_STR'] = df_obs_completo['FECHA_GESTION_DT'].dt.strftime('%d/%m/%Y %H:%M:%S').fillna(df_obs_completo['FECHA_GESTION'].astype(str))

                now = pd.Timestamp.now()
                
                # --- CAPTURAR EDICIONES PREVIAS DEL EDITOR SI EXISTEN (Para renderizar ATENDIDO al primer cambio) ---
                if "editor_observadas" in st.session_state and "edited_rows" in st.session_state["editor_observadas"]:
                    for idx_str, cambios in st.session_state["editor_observadas"]["edited_rows"].items():
                        idx_real = int(df_obs_completo.index[int(idx_str)])
                        if "ESTADO" in cambios:
                            df_obs_completo.loc[idx_real, 'ESTADO_RESCATE'] = cambios["ESTADO"]
                        if "MOTIVO_OBSERVACION" in cambios:
                            df_obs_completo.loc[idx_real, 'OBSERVACION'] = cambios["MOTIVO_OBSERVACION"]

                # Función para el conteo regresivo con la nueva lógica ATENDIDO
                def calcular_t_espera(row):
                    estado_actual = str(row['ESTADO_RESCATE']).strip().upper()
                    if estado_actual in ["RESCATADA", "ENVIADO"]:
                        return "ATENDIDO"
                        
                    dt = row['FECHA_GESTION_DT']
                    if pd.isna(dt):
                        return "NO DISPONIBLE"
                    elapsed = now - dt
                    if elapsed >= pd.Timedelta(hours=24):
                        return "DISPONIBLE"
                    else:
                        return "NO DISPONIBLE"

                df_obs_completo['T_ESPERA'] = df_obs_completo.apply(calcular_t_espera, axis=1)
                df_obs_completo['ID_FILA'] = df_obs_completo.index
                
                # Columnas ordenadas y renombradas
                df_para_editar = df_obs_completo[['ID_FILA', 'EJECUTIVO', 'DNI', 'V_CANTADAS', 'F_VENTA_STR', 'OBSERVACION', 'ESTADO_RESCATE', 'HORA_OBS_STR', 'T_ESPERA']].copy()
                df_para_editar.rename(columns={
                    'F_VENTA_STR': 'F_VENTA', 
                    'ESTADO_RESCATE': 'ESTADO',
                    'HORA_OBS_STR': 'HORA_OBS',
                    'OBSERVACION': 'MOTIVO_OBSERVACION'
                }, inplace=True)
                
                df_editado = st.data_editor(
                    df_para_editar,
                    column_config={
                        "ID_FILA": None,
                        "EJECUTIVO": st.column_config.TextColumn("EJECUTIVO", disabled=True),
                        "DNI": st.column_config.TextColumn("DNI", disabled=True),
                        "V_CANTADAS": st.column_config.TextColumn("V_CANTADAS", disabled=True),
                        "F_VENTA": st.column_config.TextColumn("F_VENTA", disabled=True),
                        "MOTIVO_OBSERVACION": st.column_config.TextColumn("MOTIVO_OBSERVACION", help="Haz doble clic para editar o borrar texto"),
                        "ESTADO": st.column_config.SelectboxColumn(
                            "ESTADO",
                            options=["", "RESCATADA", "PENDIENTE", "ENVIADO"],
                            required=False,
                            help="Selecciona RESCATADA, PENDIENTE o ENVIADO"
                        ),
                        "HORA_OBS": st.column_config.TextColumn("HORA_OBS", disabled=True),
                        "T_ESPERA": st.column_config.TextColumn("T_ESPERA", disabled=True),
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="editor_observadas"
                )

                # Sincronizar cambios en memoria y en df_global
                for idx, row in df_editado.iterrows():
                    fila_original = int(row['ID_FILA'])
                    dni_fila = row['DNI']
                    
                    df.loc[fila_original, 'OBSERVACION'] = row['MOTIVO_OBSERVACION']
                    df.loc[fila_original, 'ESTADO_RESCATE'] = row['ESTADO']
                    
                    # Guardamos la edición en memoria persistente usando el DNI
                    st.session_state.ediciones_guardadas[dni_fila] = {
                        'OBSERVACION': row['MOTIVO_OBSERVACION'],
                        'ESTADO': row['ESTADO']
                    }

                st.success("✅ Ediciones guardadas automáticamente. Puedes subir un Excel actualizado y se mantendrán los motivos y estados.")

                def convertir_df_a_excel(df_input):
                    from io import BytesIO
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_input.to_excel(writer, index=False, sheet_name='ReporteValidacion')
                    return output.getvalue()

                excel_actualizado = convertir_df_a_excel(df)
                st.download_button(
                    label="📥 Descargar Excel Completo Actualizado",
                    data=excel_actualizado,
                    file_name="reporte_validación_actualizado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo. Detalle: {e}")
else:
    st.info("👈 Por favor, sube tu archivo Excel en la barra lateral para comenzar.")