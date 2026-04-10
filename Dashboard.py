import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import datetime
from datetime import date

# --- 1. CONFIGURAÇÃO DA PÁGINA (MOBILE OPTIMIZED) ---
st.set_page_config(
    page_title="Magalu | Gestão de Carga e Descarga", 
    layout="wide", 
    initial_sidebar_state="collapsed" # No celular, já abre recolhido (Menu Hamburguer)
)

# --- 2. CSS DE ALTO NÍVEL (UI/UX MOBILE MAGALU) ---
st.markdown("""
    <style>
    .stApp { background-color: #F4F6F9; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
    
    * { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    p, div, span { color: #334155; }
    
    .magalu-page-title { color: #0086FF; font-size: 22px; font-weight: 800; margin-bottom: 5px; line-height: 1.2;}
    .magalu-page-subtitle { color: #64748B; font-size: 13px; margin-bottom: 20px; }
    
    .magalu-ribbon {
        background-color: #0086FF; color: #FFFFFF; padding: 6px 16px; font-size: 14px; font-weight: 600;
        display: inline-block; border-radius: 0px 4px 4px 0px; margin-bottom: 10px; margin-top: 15px;
        position: relative; left: -1rem; box-shadow: 0 2px 4px rgba(0,134,255,0.2);
    }
    
    .magalu-card {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04); margin-bottom: 15px;
    }
    
    /* OTIMIZAÇÃO MOBILE: Botões grandes e fáceis de tocar */
    .stButton>button {
        background-color: #0086FF; color: white; border: none; border-radius: 8px;
        font-weight: 700; font-size: 16px; padding: 0.8rem 1rem; height: auto;
        box-shadow: 0 4px 6px rgba(0, 134, 255, 0.2);
    }
    .stButton>button:hover { background-color: #0073E6; color: white; }
    
    /* Inputs amigáveis para dedos */
    input, .stSelectbox div[data-baseweb="select"] { border-radius: 6px !important; min-height: 45px !important;}
    
    /* KPIs responsivos */
    .kpi-card { background-color: #FFFFFF; border-radius: 8px; padding: 12px; border-left: 4px solid #0086FF; margin-bottom: 10px;}
    .kpi-title { color: #6B7280; font-size: 12px; font-weight: 700; text-transform: uppercase; }
    .kpi-value { color: #111827; font-size: 20px; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CONEXÃO GOOGLE SHEETS ---
def conectar_google():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        cred_dict = json.loads(st.secrets["google_json"])
        creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
    except:
        creds = Credentials.from_service_account_file(r'C:\Users\IIGOORNSC\Documents\CargaDescarga\credential_key.json', scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def carregar_dados_financeiros():
    client = conectar_google()
    sh = client.open_by_key("1NWH9BHXgUmS-6WCQ8AjAHbt8DUHIvgQLRJ8hwUSDC7U")
    ws = sh.worksheet("HISTÓRICO 2025")
    return pd.DataFrame(ws.get_all_values()[1:], columns=ws.get_all_values()[0])

@st.cache_data(ttl=60)
def carregar_equipe():
    client = conectar_google()
    sh = client.open_by_key("1lrX3wQ41ncVMLzCaqGIQlbwvd_0n-AYOyU-NH1ge5oI")
    ws = sh.worksheet("QUADRO CARGA e DESCARGA")
    return pd.DataFrame(ws.get_all_records())

@st.cache_data(ttl=10) # Atualiza a cada 10 segundos para dar a visão em "Tempo Real"
def carregar_log_produtividade():
    client = conectar_google()
    sh = client.open_by_key("1lrX3wQ41ncVMLzCaqGIQlbwvd_0n-AYOyU-NH1ge5oI")
    try:
        ws = sh.worksheet("LOG_PRODUTIVIDADE")
        return pd.DataFrame(ws.get_all_records())
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def carregar_aux():
    client = conectar_google()
    sh = client.open_by_key("1lrX3wQ41ncVMLzCaqGIQlbwvd_0n-AYOyU-NH1ge5oI") # Usando sua planilha de equipe/aux
    try:
        ws = sh.worksheet("aux")
        return pd.DataFrame(ws.get_all_records())
    except:
        return pd.DataFrame()

def gravar_absenteismo(dados_para_gravar):
    client = conectar_google()
    sh = client.open_by_key("1lrX3wQ41ncVMLzCaqGIQlbwvd_0n-AYOyU-NH1ge5oI")
    try:
        ws_log = sh.worksheet("LOG_ABSENTEISMO")
        ws_log.append_rows(dados_para_gravar)
        return True
    except:
        st.error("Erro: Aba 'LOG_ABSENTEISMO' não encontrada.")
        return False

def gravar_produtividade(lista_de_linhas):
    client = conectar_google()
    sh = client.open_by_key("1lrX3wQ41ncVMLzCaqGIQlbwvd_0n-AYOyU-NH1ge5oI")
    try:
        ws_log = sh.worksheet("LOG_PRODUTIVIDADE")
        # Agora ele recebe várias linhas de uma vez (Eventos simultâneos)
        ws_log.append_rows(lista_de_linhas)
        return True
    except:
        st.error("Erro: Crie a aba 'LOG_PRODUTIVIDADE' na planilha de equipe.")
        return False

def gravar_conclusao_doca(dados_finalizados, linha_encerramento_log):
    client = conectar_google()
    sh = client.open_by_key("1lrX3wQ41ncVMLzCaqGIQlbwvd_0n-AYOyU-NH1ge5oI")
    try:
        # 1. Registra o histórico definitivo com o tempo de duração
        ws_final = sh.worksheet("DOCAS_FINALIZADAS")
        ws_final.append_rows([dados_finalizados])

        # 2. Registra o encerramento no Log de Produtividade para a doca sumir da visão ativa
        ws_log = sh.worksheet("LOG_PRODUTIVIDADE")
        ws_log.append_rows([linha_encerramento_log])

        return True
    except Exception as e:
        st.error(f"Erro ao finalizar doca: {e}")
        return False

# --- 4. TRATAMENTO DE DADOS FINANCEIROS ---
def formatar_moeda_br(valor):
    if pd.isna(valor) or valor == 0: return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def tratar_dados(df_h):
    df_h['STATUS'] = df_h['STATUS'].astype(str).str.strip().str.upper()
    df_h['AGENDA WMS'] = df_h['AGENDA WMS'].astype(str).str.strip().str.upper()
    df_h['DATA AGENDA'] = df_h['DATA AGENDA'].astype(str).str.strip()
    df_h['DATA AGENDADA'] = pd.to_datetime(df_h['DATA AGENDA'], dayfirst=True, errors='coerce')
    df_h = df_h.dropna(subset=['DATA AGENDADA']).copy()

    df_h['PRIORIDADE_STATUS'] = df_h['STATUS'].apply(lambda x: 1 if x == 'OK' else (0 if x == 'AUSENTE' else -1))
    df_h = df_h.sort_values(by=['AGENDA WMS', 'PRIORIDADE_STATUS', 'DATA AGENDADA'], ascending=[True, False, False])
    mask_wms_valido = ~df_h['AGENDA WMS'].isin(['', '-', 'NAN', 'NONE'])
    df_com_wms = df_h[mask_wms_valido].drop_duplicates(subset=['AGENDA WMS'], keep='first')
    df_sem_wms = df_h[~mask_wms_valido]
    df_h = pd.concat([df_com_wms, df_sem_wms], ignore_index=True).drop(columns=['PRIORIDADE_STATUS'])

    df_h['ANO'] = df_h['DATA AGENDADA'].dt.year.astype('Int64')
    df_h['MES_ORDENACAO'] = df_h['DATA AGENDADA'].dt.to_period('M')
    meses_pt = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
    df_h['MES_NOME'] = df_h['DATA AGENDADA'].dt.month.map(meses_pt) + "/" + df_h['ANO'].astype(str)

    def limpar_moeda(valor):
        if pd.isna(valor) or str(valor).strip() == '': return 0.0
        v = str(valor).upper().replace('R$', '').replace(' ', '').strip()
        if v in ['', '-', 'OK', 'NAOÉCOBRADO']: return 0.0
        if '.' in v and ',' in v: v = v.replace('.', '').replace(',', '.')
        elif '.' in v: v = v.replace('.', '')
        elif ',' in v: v = v.replace(',', '.')
        try: return round(float(v), 2)
        except ValueError: return 0.0

    df_h['VALOR_REAL'] = df_h['VALOR'].apply(limpar_moeda) if 'VALOR' in df_h.columns else 0.0

    df_h['LINHA'] = df_h['LINHA'].astype(str).str.strip().str.upper()
    df_h['FORNECEDOR/SELLER'] = df_h['FORNECEDOR/SELLER'].astype(str).str.strip().str.upper()
    df_h['CATEGORIA'] = df_h['CATEGORIA'].astype(str).str.strip().str.upper()

    def eh_interno(forn):
        if forn.startswith(('MAGAZINE', 'FILIAL')): return True
        if re.match(r'^C[D\d]', forn): return True 
        return False
    df_h = df_h[~df_h['FORNECEDOR/SELLER'].apply(eh_interno)]

    mask_full = df_h['LINHA'].str.contains('FULL', na=False) | df_h['CATEGORIA'].str.contains('FULL', na=False)
    df_full = df_h[mask_full].copy()
    df_main = df_h[~mask_full].copy()

    pag_l = df_main[df_main['VALOR_REAL'] > 0]['LINHA'].unique()
    pag_c = df_main[df_main['VALOR_REAL'] > 0]['CATEGORIA'].unique()
    df_main = df_main[(df_main['LINHA'].isin([l for l in pag_l if l != ''])) | (df_main['CATEGORIA'].isin([c for c in pag_c if c != '']))].copy()

    df_ok = df_main[(df_main['STATUS'] == 'OK') & (df_main['VALOR_REAL'] > 0)]
    m_linha = df_ok.groupby('LINHA')['VALOR_REAL'].mean().to_dict()
    m_cat = df_ok.groupby('CATEGORIA')['VALOR_REAL'].mean().to_dict()

    df_main['VALOR_PERDIDO'] = 0.0
    mask_aus = df_main['STATUS'] == 'AUSENTE'
    df_main.loc[mask_aus, 'VALOR_PERDIDO'] = df_main.loc[mask_aus, 'LINHA'].map(m_linha)
    mask_zero = mask_aus & (df_main['VALOR_PERDIDO'].isna() | (df_main['VALOR_PERDIDO'] == 0))
    df_main.loc[mask_zero, 'VALOR_PERDIDO'] = df_main.loc[mask_zero, 'CATEGORIA'].map(m_cat)
    df_main['VALOR_PERDIDO'] = df_main['VALOR_PERDIDO'].fillna(0).round(2)

    df_full['VALOR_ESTIMADO'] = df_full['CATEGORIA'].map(m_cat)
    df_full.loc[df_full['CATEGORIA'] == 'DIVERSOS', 'VALOR_ESTIMADO'] = 350.00
    df_full['VALOR_ESTIMADO'] = df_full['VALOR_ESTIMADO'].fillna(500.00).round(2)

    return df_main, df_full


# ==========================================
# 🚀 MENU DE NAVEGAÇÃO LATERAL (MOBILE)
# ==========================================
st.sidebar.markdown('<div class="magalu-ribbon" style="left: 0;">Módulos do App</div>', unsafe_allow_html=True)
pagina_selecionada = st.sidebar.radio(
    "",
    ["📋 Absenteísmo (Doca)", "🚛 Gestão de Docas", "📊 Financeiro (Diretoria)"]
)
st.sidebar.markdown("---")

# ==========================================
# PÁGINA 1: MÓDULO DE ABSENTEÍSMO (MOBILE)
# ==========================================
if pagina_selecionada == "📋 Absenteísmo (Doca)":
    st.markdown('<div class="magalu-page-title">Lançamento de Ocorrências</div>', unsafe_allow_html=True)
    st.markdown('<div class="magalu-page-subtitle">Pátio / Docas</div>', unsafe_allow_html=True)

    try:
        df_equipe = carregar_equipe()

        # Filtros empilhados para caber no celular
        st.markdown('<div class="magalu-card">', unsafe_allow_html=True)
        data_chamada = st.date_input("Data", date.today())
        busca = st.text_input("🔍 Buscar Colaborador", placeholder="Matrícula ou Nome...")
        st.markdown('</div>', unsafe_allow_html=True)

        if busca:
            df_filtrado = df_equipe[df_equipe['NOME'].str.contains(busca, case=False, na=False) | df_equipe['ID'].astype(str).str.contains(busca, na=False)].copy()
        else:
            df_filtrado = df_equipe.copy()

        df_filtrado['OCORRÊNCIA'] = "PRESENTE" 
        opcoes_ocorrencia = ["PRESENTE", "FALTA", "DSR", "BH", "LICENÇA", "ATESTADO"]

        st.markdown('<div class="magalu-ribbon">Registro da Equipe</div>', unsafe_allow_html=True)

        # TRUQUE MOBILE: Ocultamos 'CARGO' e 'TURNO' visualmente (None), mas o dataframe mantém para gravar!
        df_editado = st.data_editor(
            df_filtrado[['ID', 'NOME', 'CARGO', 'TURNO', 'OCORRÊNCIA']],
            column_config={
                "OCORRÊNCIA": st.column_config.SelectboxColumn("Status", options=opcoes_ocorrencia, required=True, width="medium"),
                "ID": st.column_config.TextColumn("Matrícula", disabled=True, width="small"),
                "NOME": st.column_config.TextColumn("Nome", disabled=True, width="large"),
                "CARGO": None, # Oculto no celular
                "TURNO": None, # Oculto no celular
            },
            hide_index=True,
            use_container_width=True,
            key="editor_chamada"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Botão gigante (Full Width)
        if st.button("Gravar no Sistema", use_container_width=True):
            ocorrencias = df_editado[df_editado['OCORRÊNCIA'] != "PRESENTE"]
            if not ocorrencias.empty:
                lista_final = []
                data_str = data_chamada.strftime("%d/%m/%Y")
                for index, row in ocorrencias.iterrows():
                    lista_final.append([data_str, row['ID'], row['NOME'], row['OCORRÊNCIA'], row['TURNO']])
                with st.spinner("Gravando..."):
                    sucesso = gravar_absenteismo(lista_final)
                    if sucesso:
                        st.success(f"✅ {len(lista_final)} registros salvos!")
                        st.cache_data.clear()
            else:
                st.warning("Nenhuma falta marcada.")

    except Exception as e:
        st.error(f"Erro na conexão com RH: {e}")

# ==========================================
# PÁGINA 2: DASHBOARD FINANCEIRO E DRE
# ==========================================
elif pagina_selecionada == "📊 Financeiro (Diretoria)":
    try:
        with st.spinner('Lendo faturamento...'):
            df_raw = carregar_dados_financeiros()
            df, df_full = tratar_dados(df_raw)

        st.sidebar.markdown('<div class="magalu-ribbon" style="left: 0; font-size: 12px;">Parâmetros</div>', unsafe_allow_html=True)
        hoje = datetime.date.today()
        ontem = hoje - datetime.timedelta(days=1)
        d_min = df['DATA AGENDADA'].min().date() if not df.empty else datetime.date(2025, 1, 1)
        d_max_limite = max(hoje, datetime.date(2026, 12, 31))

        selecao = st.sidebar.date_input("Período", value=(d_min, hoje), min_value=d_min, max_value=d_max_limite)
        if isinstance(selecao, tuple) and len(selecao) == 2:
            data_ini, data_fim = selecao
        else:
            data_ini = selecao[0] if isinstance(selecao, (tuple, list)) else selecao
            data_fim = data_ini

        st.sidebar.markdown('<div style="font-size: 12px; color: #64748B; margin-top: 10px;">Custo de Folha</div>', unsafe_allow_html=True)
        qtd_pessoas = st.sidebar.number_input("Equipe", min_value=1, value=40, step=1)
        salario_base = st.sidebar.number_input("R$/Pessoa", min_value=0.0, value=2100.0, step=100.0)
        custo_mensal_equipe = qtd_pessoas * salario_base

        mask_data_main = (df['DATA AGENDADA'].dt.date >= data_ini) & (df['DATA AGENDADA'].dt.date <= data_fim)
        mask_data_full = (df_full['DATA AGENDADA'].dt.date >= data_ini) & (df_full['DATA AGENDADA'].dt.date <= data_fim)
        df_f = df[mask_data_main].copy()
        df_full_f = df_full[mask_data_full].copy()

        st.markdown('<div class="magalu-page-title">DRE Operacional</div>', unsafe_allow_html=True)
        st.markdown(f"<div class='magalu-page-subtitle'>{data_ini.strftime('%d/%m')} até {data_fim.strftime('%d/%m')}</div>", unsafe_allow_html=True)

        if not df_f.empty:
            rec = df_f[df_f['STATUS'] == 'OK']
            aus = df_f[df_f['STATUS'] == 'AUSENTE']

            # No celular, não usamos colunas para os KPIs principais, deixamos empilhar
            st.markdown(f'<div class="kpi-card" style="border-left-color: #00C853;"><div class="kpi-title">💰 Faturamento</div><div class="kpi-value">{formatar_moeda_br(rec["VALOR_REAL"].sum())}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-card" style="border-left-color: #FF3366;"><div class="kpi-title">📉 Perda Ausentes</div><div class="kpi-value">{formatar_moeda_br(aus["VALOR_PERDIDO"].sum())}</div></div>', unsafe_allow_html=True)

            layout_clean = dict(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Segoe UI, sans-serif", color='#334155'))

            st.markdown('<div class="magalu-ribbon">Gráfico DRE Mensal</div>', unsafe_allow_html=True)
            st.markdown('<div class="magalu-card">', unsafe_allow_html=True)

            ev_mes = df_f.groupby(['MES_ORDENACAO', 'MES_NOME']).agg(ARRECADADO=('VALOR_REAL', 'sum'), PERDIDO=('VALOR_PERDIDO', 'sum')).reset_index().sort_values('MES_ORDENACAO')
            if not ev_mes.empty:
                ev_mes['FOLHA_CUSTO'] = custo_mensal_equipe
                ev_mes['LUCRO_BRUTO'] = ev_mes['ARRECADADO'] - ev_mes['FOLHA_CUSTO']

                fig3 = make_subplots(specs=[[{"secondary_y": True}]])
                fig3.add_trace(go.Bar(x=ev_mes['MES_NOME'], y=ev_mes['ARRECADADO'], name="Faturamento", marker_color='#0086FF'), secondary_y=False)
                fig3.add_trace(go.Bar(x=ev_mes['MES_NOME'], y=ev_mes['FOLHA_CUSTO'], name="Custo Folha", marker_color='#94A3B8'), secondary_y=False)

                # No celular, escondemos o texto das barras para não poluir, o gerente passa o dedo para ler (Hover)
                fig3.update_layout(**layout_clean, barmode='group', showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5), margin=dict(t=50, b=0, l=0, r=0))
                fig3.update_yaxes(visible=False)
                st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro no módulo: {e}")

# ==========================================
# PÁGINA 3: GESTÃO DE DOCAS E PRODUTIVIDADE
# ==========================================
elif pagina_selecionada == "🚛 Gestão de Docas":
    st.markdown('<div class="magalu-page-title">Gestão de Docas</div>', unsafe_allow_html=True)
    st.markdown('<div class="magalu-page-subtitle">Acompanhe e movimente a equipe em tempo real.</div>', unsafe_allow_html=True)

    # Criando as Abas para o Celular
    aba1, aba2 = st.tabs(["👀 Visão das Docas (Agora)", "✍️ Apontar / Movimentar"])

    # --- ABA 1: VISÃO EM TEMPO REAL ---
    with aba1:
        df_log = carregar_log_produtividade()
        df_aux = carregar_aux() # Carrega a base de agendas

        if not df_aux.empty:
            df_aux['AGENDA WMS'] = df_aux['AGENDA WMS'].astype(str).str.strip()

        if not df_log.empty:
            df_log['DATA_HORA_DT'] = pd.to_datetime(df_log['DATA_HORA'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
            df_ativos = df_log.sort_values('DATA_HORA_DT', ascending=False).drop_duplicates(subset=['DOCA'], keep='first')
            df_ativos = df_ativos[df_ativos['AUXILIARES'].notna() & (df_ativos['AUXILIARES'] != '') & (df_ativos['AUXILIARES'] != 'ENCERRADO')]

            if df_ativos.empty:
                st.info("Nenhuma doca ativa no momento. Pátio limpo! 🍃")
            else:
                for index, row in df_ativos.iterrows():
                    # --- INTELIGÊNCIA: Busca na base AUX ---
                    agenda_str = str(row['AGENDA']).strip()
                    info = {'LINHA': '-', 'SKU': '-', 'PEÇAS': '-', 'VALOR': '-', 'PAGTO': '-', 'STATUS': '-'}

                    if not df_aux.empty and agenda_str in df_aux['AGENDA WMS'].values:
                        aux_row = df_aux[df_aux['AGENDA WMS'] == agenda_str].iloc[0]

                        pagto_str = "✅ Sim" if str(aux_row.get('PAGAMENTO', '')).upper() == 'TRUE' else "⏳ Pendente"
                        valor_desc = aux_row.get('R$ DESCARGA', '-')
                        if str(valor_desc).replace('.','',1).isdigit():
                            valor_desc = f"R$ {float(valor_desc):,.2f}".replace(',','X').replace('.',',').replace('X','.')

                        info = {
                            'LINHA': aux_row.get('LINHA', '-'),
                            'SKU': aux_row.get('SKU', '-'),
                            'PEÇAS': aux_row.get('PEÇAS', '-'),
                            'VALOR': valor_desc,
                            'PAGTO': pagto_str,
                            'STATUS': aux_row.get('STATUS', '-')
                        }

                    with st.container(border=True):
                        c_title, c_time = st.columns([7, 3])
                        c_title.markdown(f"<h4 style='margin:0; color:#0086FF;'>Doca {row['DOCA']}</h4>", unsafe_allow_html=True)
                        c_time.markdown(f"<div style='text-align:right; font-size:11px; color:#64748B; margin-top:5px;'>⌚ Início: {row['DATA_HORA']}</div>", unsafe_allow_html=True)

                        st.markdown(f"<div style='font-size: 13px; margin: 8px 0px 4px 0px;'><b>Agenda:</b> {row['AGENDA']} | <b>Líder:</b> {row['CONFERENTE']}</div>", unsafe_allow_html=True)

                        # NOVO BLOCO: Detalhes da Carga
                        st.markdown(f"""
                        <div style='font-size: 11.5px; color: #475569; background-color: #F8FAFC; padding: 6px; border-radius: 4px; margin-bottom: 8px; border: 1px solid #E2E8F0;'>
                            <b>Linha:</b> {info['LINHA']} &nbsp;|&nbsp; <b>SKU:</b> {info['SKU']} &nbsp;|&nbsp; <b>Peças:</b> {info['PEÇAS']}<br>
                            <b>Valor Carga:</b> {info['VALOR']} &nbsp;|&nbsp; <b>Pagamento:</b> {info['PAGTO']} &nbsp;|&nbsp; <b>Status:</b> <span style="color:#0086FF; font-weight:bold;">{info['STATUS']}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        c_eq, c_btn = st.columns([7, 3])
                        c_eq.markdown(f"<div style='font-size: 12px; color: #0086FF; background-color: #E6F2FF; padding: 6px; border-radius: 4px;'><b>Equipe:</b> {row['AUXILIARES']}</div>", unsafe_allow_html=True)

                        with c_btn:
                            if st.button("✅ Finalizar", key=f"btn_fin_{row['DOCA']}_{index}", type="primary", use_container_width=True):
                                agora_dt = datetime.datetime.now()
                                inicio_dt = row['DATA_HORA_DT']
                                duracao = agora_dt - inicio_dt
                                total_minutos = int(duracao.total_seconds() / 60)
                                horas, mins = total_minutos // 60, total_minutos % 60
                                tempo_str = f"{horas:02d}:{mins:02d}"

                                auxiliares_lista = [x.strip() for x in str(row['AUXILIARES']).split(',')]
                                dados_conclusao = [
                                    agora_dt.strftime("%d/%m/%Y"), str(row['DOCA']), str(row['AGENDA']), 
                                    str(row['CONFERENTE']), len(auxiliares_lista), row['AUXILIARES'], 
                                    row['DATA_HORA'], agora_dt.strftime("%H:%M:%S"), tempo_str
                                ]
                                linha_log_fecha = [agora_dt.strftime("%d/%m/%Y %H:%M:%S"), str(row['DOCA']), row['AGENDA'], row['CONFERENTE'], "ENCERRADO"]

                                with st.spinner("Finalizando..."):
                                    if gravar_conclusao_doca(dados_conclusao, linha_log_fecha):
                                        st.success(f"Doca finalizada em {tempo_str}!")
                                        st.cache_data.clear()
                                        st.rerun()
        else:
            st.info("O Log ainda está vazio.")

   # ==========================================================
    # LÓGICA DE GRAVAÇÃO E POP-UP (MÓDULO DE DOCAS)
    # ==========================================================
    def processar_gravacao_doca(doca_sel, agenda_sel, conferente_sel, equipe_sel, conflitos, info_docas, encerrar):
        agora_dt = datetime.datetime.now()
        agora_str = agora_dt.strftime("%d/%m/%Y %H:%M:%S")

        linhas_para_gravar = []

        # Define os textos base
        if encerrar:
            auxiliares_str = "ENCERRADO"
            agenda_final = agenda_sel if agenda_sel else "-"
            conferente_final = conferente_sel if conferente_sel else "-"
        else:
            auxiliares_str = ", ".join(equipe_sel)
            agenda_final = agenda_sel
            conferente_final = conferente_sel

        # 1º EVENTO: Registra a nova Doca (ou o encerramento dela)
        linhas_para_gravar.append([agora_str, str(doca_sel).strip(), agenda_final, conferente_final, auxiliares_str])

        # 2º EVENTO: Se houver transferência, tira o cara da doca antiga automaticamente
        if conflitos and not encerrar:
            docas_afetadas = set(conflitos.values())
            # Soma 1 segundo na data/hora para a atualização não atropelar o banco
            agora_dt = agora_dt + datetime.timedelta(seconds=1)
            agora_str_2 = agora_dt.strftime("%d/%m/%Y %H:%M:%S")

            for d_antiga in docas_afetadas:
                eq_antiga = info_docas[d_antiga]['equipe'].copy()
                # Tira apenas as pessoas que foram movidas
                for p_movida in [p for p, d in conflitos.items() if d == d_antiga]:
                    if p_movida in eq_antiga:
                        eq_antiga.remove(p_movida)

                nova_eq_str = ", ".join(eq_antiga) if eq_antiga else "ENCERRADO"
                linhas_para_gravar.append([agora_str_2, d_antiga, info_docas[d_antiga]['agenda'], info_docas[d_antiga]['conferente'], nova_eq_str])

        return gravar_produtividade(linhas_para_gravar)

    # Função que desenha o Pop-up na tela
    @st.dialog("⚠️ Confirmação de Transferência")
    def exibir_popup_transferencia(doca_sel, agenda_sel, conferente_sel, equipe_sel, conflitos, info_docas):
        st.write("O sistema detectou que alguns colaboradores já estão alocados em outras docas ativas:")

        for p, d in conflitos.items():
            st.markdown(f"- **{p}** (Sairá da Doca **{d}**)")

        st.write(f"Deseja confirmar a transferência para a **Doca {doca_sel}**?")
        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        if c1.button("✅ Sim, Transferir", use_container_width=True):
            with st.spinner("Atualizando docas..."):
                if processar_gravacao_doca(doca_sel, agenda_sel, conferente_sel, equipe_sel, conflitos, info_docas, False):
                    st.cache_data.clear()
                    st.rerun() # Fecha o pop-up e recarrega a tela automaticamente

        if c2.button("❌ Cancelar", use_container_width=True):
            st.rerun() # Apenas fecha o pop-up

    # --- ABA 2: LANÇAMENTO E MOVIMENTAÇÃO ---
    with aba2:
        try:
            df_equipe = carregar_equipe()
            lista_auxiliares = df_equipe[df_equipe['NOME'].notna()]['NOME'].unique().tolist()
            lista_auxiliares = [nome for nome in lista_auxiliares if str(nome).strip() != '']

            # Mapeamento do Status Atual
            df_log = carregar_log_produtividade()
            mapa_pessoas = {}
            info_docas = {}

            if not df_log.empty:
                df_log['DATA_HORA_DT'] = pd.to_datetime(df_log['DATA_HORA'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
                df_ativos = df_log.sort_values('DATA_HORA_DT', ascending=False).drop_duplicates(subset=['DOCA'], keep='first')
                df_ativos = df_ativos[df_ativos['AUXILIARES'].notna() & (df_ativos['AUXILIARES'] != '') & (df_ativos['AUXILIARES'] != 'ENCERRADO')]

                for _, row in df_ativos.iterrows():
                    doca_atual = str(row['DOCA']).strip()
                    eq_atual = [x.strip() for x in str(row['AUXILIARES']).split(',')]
                    info_docas[doca_atual] = {'agenda': row['AGENDA'], 'conferente': row['CONFERENTE'], 'equipe': eq_atual}
                    for p in eq_atual:
                        mapa_pessoas[p] = doca_atual

            # Formulário de Interface
            st.markdown('<div class="magalu-card">', unsafe_allow_html=True)
            st.markdown('<b style="color: #0086FF;">📍 Nova Alocação / Atualizar Doca</b>', unsafe_allow_html=True)

            # 1. Pede a Agenda primeiro para poder puxar os dados
            agenda_sel = st.text_input("Nº da Agenda (Aperte Enter para buscar)", placeholder="Ex: 51183")
            
            doca_padrao = ""
            conf_padrao = ""
            df_aux = carregar_aux()
            
            # Se digitou a agenda e ela existe na base 'aux', tenta puxar doca e conferente
            if agenda_sel and not df_aux.empty:
                df_aux['AGENDA WMS'] = df_aux['AGENDA WMS'].astype(str).str.strip()
                match = df_aux[df_aux['AGENDA WMS'] == agenda_sel.strip()]
                if not match.empty:
                    st.success("✅ Agenda localizada na base!")
                    if 'DOCA' in match.columns: doca_padrao = str(match.iloc[0]['DOCA'])
                    if 'CONFERENTE' in match.columns: conf_padrao = str(match.iloc[0]['CONFERENTE'])
            
            col1, col2 = st.columns(2)
            with col1:
                # Se achou a doca, já vem preenchida
                doca_sel = st.text_input("Número da Doca", value=doca_padrao, placeholder="Ex: 68")
            with col2:
                # Se achou o conferente, já vem preenchido
                conferente_sel = st.text_input("Nome do Conferente", value=conf_padrao, placeholder="Ex: Edson")


            st.markdown('<br>', unsafe_allow_html=True)

            equipe_sel = st.multiselect("Equipe Alocada Agora", options=lista_auxiliares)

            # Análise de Conflitos Oculta
            conflitos = {}
            for pessoa in equipe_sel:
                if pessoa in mapa_pessoas:
                    doca_antiga = mapa_pessoas[pessoa]
                    if doca_antiga != str(doca_sel).strip():
                        conflitos[pessoa] = doca_antiga

        except Exception as e:
            st.error(f"Erro no módulo de Docas: {e}")
