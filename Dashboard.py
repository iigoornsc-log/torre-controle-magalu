import streamlit as st
import pandas as pd
import plotly.express as px
import math
import gspread
from google.oauth2.service_account import Credentials
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Torre de Controle | Magalu", page_icon="🛍️", layout="wide", initial_sidebar_state="expanded")

# --- INJEÇÃO DE CSS (DESIGN: SOFT UI) ---
st.markdown("""
<style>
    .stApp { background-color: #F4F7F6; color: #2C3E50; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    h1, h2, h3 { color: #2C3E50 !important; font-weight: 800; letter-spacing: -0.5px; }
    hr { border-top: 2px solid #EAEDED; border-radius: 2px; }
    [data-testid="stDataFrame"] { 
        border: none !important; 
        border-radius: 12px !important; 
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important; 
        overflow: hidden !important; 
    }
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        box-shadow: 2px 0 15px rgba(0, 0, 0, 0.03);
        border-right: none;
    }
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #EAEDED !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
    }
</style>
""", unsafe_allow_html=True)

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- COMPONENTE DE KPI ---
def exibir_kpi(titulo, valor, subtitulo="", cor="#0086FF"):
    st.markdown(f"""
    <div style="
        background-color: #FFFFFF; border-radius: 12px; padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04); border-left: 6px solid {cor};
        margin-bottom: 15px; transition: transform 0.2s ease, box-shadow 0.2s ease;
    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(0, 0, 0, 0.08)';" 
      onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(0, 0, 0, 0.04)';">
        <p style="margin: 0; font-size: 13px; color: #7F8C8D; font-weight: 600; text-transform: uppercase;">{titulo}</p>
        <h2 style="margin: 5px 0; font-size: 32px; color: #2C3E50; font-weight: 800;">{valor}</h2>
        <p style="margin: 0; font-size: 13px; color: #95A5A6; font-weight: 500;">{subtitulo}</p>
    </div>
    """, unsafe_allow_html=True)

# --- CONEXÃO INTELIGENTE COM O GOOGLE ---
def conectar_google():
    try:
        cred_dict = json.loads(st.secrets["google_json"])
        creds = Credentials.from_service_account_info(cred_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    except:
        caminho_local = 'C:/Users/ign_oliveira/Documents/Analises Agendas/credential_key.json'
        creds = Credentials.from_service_account_file(caminho_local, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    
    return gspread.authorize(creds)

# --- EXTRAÇÃO DE DADOS ---
@st.cache_data(ttl=300)
def carregar_dados():
    df = pd.DataFrame()
    df_itens = pd.DataFrame()
    df_plan = pd.DataFrame()
    df_transf = pd.DataFrame()
    
    try:
        cliente_google = conectar_google()
        planilha_principal = cliente_google.open_by_key('1WA5GjT1f-jpQ4Sw_OfvXBERyz5MehfH7uaFrIfUMrtw')
        
        # ==============================================================================
        # 0. RECUPERANDO A BASE DE MINUTOS (APC FULL)
        # ==============================================================================
        apc_full_dict = {}
        try:
            try:
                ws_apc = planilha_principal.worksheet("APC_FULL")
                dados_apc = ws_apc.get_all_values()
                if len(dados_apc) > 1:
                    for row in dados_apc[1:]:
                        apc_full_dict[str(row[0]).strip().upper()] = pd.to_numeric(row[1], errors='coerce')
            except:
                df_apc_csv = pd.read_csv('Apcfull.csv', sep=None, engine='python') 
                for _, row in df_apc_csv.iterrows():
                    apc_full_dict[str(row.iloc[0]).strip().upper()] = pd.to_numeric(row.iloc[1], errors='coerce')
        except: pass

        # ==============================================================================
        # 1. ABA CONSOLIDADO (COM UNIFICAÇÃO DE AGENDAS & REGRA DA MADEIRA)
        # ==============================================================================
        ws_consolidado = planilha_principal.worksheet("CONSOLIDADO")
        dados_consolidado = ws_consolidado.get_all_values() 
        if dados_consolidado and len(dados_consolidado) > 1:
            df_raw = pd.DataFrame(dados_consolidado[1:], columns=dados_consolidado[0])
            df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()]
            df_raw = df_raw.loc[:, df_raw.columns != '']
            df_raw.columns = df_raw.columns.str.strip().str.upper()
            
            map_cons = {}
            alvos_cons = set()
            for c in df_raw.columns:
                if 'AGENDA' in c and 'Agenda' not in alvos_cons: map_cons[c] = 'Agenda'; alvos_cons.add('Agenda')
                elif 'DATA' in c and 'Data' not in alvos_cons: map_cons[c] = 'Data'; alvos_cons.add('Data')
                elif 'FORNECEDOR' in c and 'Fornecedor' not in alvos_cons: map_cons[c] = 'Fornecedor'; alvos_cons.add('Fornecedor')
                elif 'LINHA' in c and 'Linhas' not in alvos_cons: map_cons[c] = 'Linhas'; alvos_cons.add('Linhas')
                elif 'CATEGORIA' in c and 'Categoria' not in alvos_cons: map_cons[c] = 'Categoria'; alvos_cons.add('Categoria')
                elif ('PEÇA' in c or 'PECA' in c) and 'Qtd Peças' not in alvos_cons: map_cons[c] = 'Qtd Peças'; alvos_cons.add('Qtd Peças')
                elif 'STATUS' in c and 'Status' not in alvos_cons: map_cons[c] = 'Status'; alvos_cons.add('Status')
            
            df_raw = df_raw.rename(columns=map_cons)
            df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()]
            
            for col in ['Agenda', 'Data', 'Fornecedor', 'Linhas', 'Categoria', 'Status']:
                if col not in df_raw.columns: df_raw[col] = ''
            if 'Qtd Peças' not in df_raw.columns: df_raw['Qtd Peças'] = 0
            else: df_raw['Qtd Peças'] = pd.to_numeric(df_raw['Qtd Peças'], errors='coerce').fillna(0)
            if 'É Ofensor?' not in df_raw.columns: df_raw['É Ofensor?'] = 'Não'

            df_raw['Pecas_Madeira'] = df_raw.apply(
                lambda r: r['Qtd Peças'] if 'MADEIRA' in str(r.get('Linhas', '')).upper() else 0, 
                axis=1
            )

            df_raw['Data'] = pd.to_datetime(df_raw['Data'], errors='coerce', dayfirst=True).dt.normalize()
            df_raw = df_raw[df_raw['Agenda'].astype(str).str.strip() != '']
            df_raw['Agenda'] = df_raw['Agenda'].astype(str).str.split('.').str[0].str.strip()

            def padronizar_status(val):
                v = str(val).upper().strip()
                if 'AGENDADO' in v: return 'Agendado'
                if 'PATIO' in v or 'PÁTIO' in v or 'AGUARDANDO' in v: return 'Aguardando'
                if 'RECEB' in v: return 'Recebido'
                if 'COMPARECEU' in v or 'SHOW' in v: return 'No-Show'
                if 'TRANSITO' in v or 'TRÂNSITO' in v: return 'Em Trânsito'
                if 'DESCARGA' in v: return 'Em Descarga'
                return v.title()

            df_raw['Status'] = df_raw['Status'].apply(padronizar_status)

            df = df_raw.groupby(['Data', 'Agenda']).agg(
                Fornecedor=('Fornecedor', 'first'),
                Status=('Status', 'first'),
                Linhas=('Linhas', lambda x: ', '.join(sorted(set([str(i).strip() for i in x.dropna() if str(i).strip()])))),
                Qtd_SKUs=('Agenda', 'count'),
                Qtd_Pecas=('Qtd Peças', 'sum'),
                Pecas_Madeira=('Pecas_Madeira', 'sum'),
                E_Ofensor=('É Ofensor?', 'first')
            ).reset_index()

            df = df.rename(columns={'Qtd_SKUs': 'Qtd SKUs', 'Qtd_Pecas': 'Qtd Peças', 'E_Ofensor': 'É Ofensor?'})

            df['Agenda_Texto'] = df['Agenda']
            df['Canal'] = df['Agenda_Texto'].apply(lambda x: 'Fulfillment' if len(str(x)) >= 6 else '1P Fornecedor')

            def calcular_minutos(row):
                try:
                    canal = row.get('Canal', '')
                    forn_original = str(row.get('Fornecedor', '')).strip().upper()
                    
                    if canal == 'Fulfillment':
                        for chave_forn, tempo in apc_full_dict.items():
                            if chave_forn in forn_original:
                                if tempo > 300:
                                    return 60.0
                                return float(tempo)
                        return 60.0
                    else:
                        linhas = str(row.get('Linhas', '')).upper()
                        maior_tempo = 0 
                        
                        for l in linhas.split(','):
                            t = 90
                            if 'MADEIRA' in l: 
                                if row.get('Pecas_Madeira', 0) > 10:
                                    t = 180 if 'TUBRAX' in forn_original else 427
                                else:
                                    t = 90
                            elif 'PNEU' in l: t = 240
                            elif 'TRANSFERENCIA RUIM' in l: t = 40
                            elif 'TRANSFERENCIA' in l: t = 240
                            elif 'MERCADO' in l: t = 150
                            elif 'ELETRO' in l: t = 95
                            elif 'COFRE' in l: t = 90
                            elif 'IMAGEM' in l: t = 90
                            elif 'COLCHÃO' in l or 'ESTOFADO' in l: t = 60
                            
                            if t > maior_tempo: maior_tempo = t
                        
                        return float(maior_tempo) if maior_tempo > 0 else 60.0
                except:
                    return 60.0
            
            df['Tempo_APC_Minutos'] = df.apply(calcular_minutos, axis=1)

        # ==============================================================================
        # 2. ABA ITEM AGENDA
        # ==============================================================================
        try:
            ws_itens = planilha_principal.worksheet("Item Agenda")
            dados_itens = ws_itens.get_all_values()
            if dados_itens and len(dados_itens) > 1:
                df_itens = pd.DataFrame(dados_itens[1:], columns=dados_itens[0])
                df_itens = df_itens.loc[:, ~df_itens.columns.duplicated()]
                df_itens = df_itens.loc[:, df_itens.columns != '']
                df_itens.columns = df_itens.columns.str.strip().str.upper()
                
                map_itens = {}
                alvos_itens = set()
                for c in df_itens.columns:
                    if 'AGENDA' in c and 'Agenda' not in alvos_itens: map_itens[c] = 'Agenda'; alvos_itens.add('Agenda')
                    elif ('SKU' in c or 'COMPITEM' in c or 'CÓDIGO' in c or 'CODIGO' in c) and 'SKU' not in alvos_itens: map_itens[c] = 'SKU'; alvos_itens.add('SKU')
                    elif ('DESCRI' in c or 'PRODUTO' in c) and 'Descrição' not in alvos_itens: map_itens[c] = 'Descrição'; alvos_itens.add('Descrição')
                    elif 'LINHA' in c and 'Linhas' not in alvos_itens: map_itens[c] = 'Linhas'; alvos_itens.add('Linhas')
                    elif 'CATEGORIA' in c and 'Categoria' not in alvos_itens: map_itens[c] = 'Categoria'; alvos_itens.add('Categoria')
                    elif ('PEÇA' in c or 'PECA' in c or 'QTCOMP' in c) and 'Qtd Peças' not in alvos_itens: map_itens[c] = 'Qtd Peças'; alvos_itens.add('Qtd Peças')
                
                df_itens = df_itens.rename(columns=map_itens)
                df_itens = df_itens.loc[:, ~df_itens.columns.duplicated()]
                if 'Agenda' in df_itens.columns: df_itens['Agenda'] = df_itens['Agenda'].astype(str).str.split('.').str[0].str.strip()
        except: pass 

        # ==============================================================================
        # 3. ABA PLANEJAMENTO
        # ==============================================================================
        try:
            ws_plan = planilha_principal.worksheet("PLANEJAMENTO")
            dados_plan = ws_plan.get_all_values()
            if dados_plan and len(dados_plan) > 1:
                df_plan = pd.DataFrame(dados_plan[1:], columns=dados_plan[0])
                df_plan = df_plan.loc[:, ~df_plan.columns.duplicated()]
                df_plan = df_plan.loc[:, df_plan.columns != '']
                df_plan.columns = df_plan.columns.str.strip().str.lower()
                if 'data' in df_plan.columns: df_plan['data'] = pd.to_datetime(df_plan['data'], format='%d/%m/%Y', errors='coerce').dt.normalize()
                if 'quantidade_planejado' in df_plan.columns: df_plan['quantidade_planejado'] = pd.to_numeric(df_plan['quantidade_planejado'], errors='coerce').fillna(0)
                if 'quantidade_real' in df_plan.columns: df_plan['quantidade_real'] = pd.to_numeric(df_plan['quantidade_real'], errors='coerce').fillna(0)
                if 'categoria' in df_plan.columns:
                    def traduzir_categoria(cat):
                        c = str(cat).upper().strip()
                        if 'MADEIRA SIMPLES' in c: return 'COLCHÕES/ESTOFADOS'
                        if 'COLCH' in c or 'ESTOFADO' in c or 'FREEPASS' in c: return 'COLCHÕES/ESTOFADOS'
                        if any(x in c for x in ['AR E VENTILA', 'AUDIO', 'BB/BR', 'CLIENTE', 'ECOMM', 'FERRAMENTA', 'DIVERSOS', 'IMPORTADO', 'LIVRO', 'MODA', 'MOVEIS ENCOMENDA', 'MULTI CD', 'PORTATEIS', 'ROTEIRO', 'UD/CM']): return 'DIVERSOS PEQUENOS'
                        if any(x in c for x in ['BELEZA', 'BENS DE CONSUMO', 'MERCADO']): return 'MERCADO'
                        if 'COFRE' in c: return 'COFRES'
                        if 'ELETRO PESADO' in c: return 'ELETRO PESADO'
                        if 'IMAGEM' in c: return 'IMAGEM'
                        if 'MADEIRA' in c or 'FRACIONADO' in c: return 'MADEIRA'
                        if 'PNEU' in c: return 'PNEUS'
                        return c 
                    df_plan['categoria'] = df_plan['categoria'].apply(traduzir_categoria)
        except: pass 

        # ==============================================================================
        # 4. PLANILHA DE TRANSFERÊNCIAS (DIA/MÊS/ANO INTELIGENTE)
        # ==============================================================================
        try:
            planilha_transf = cliente_google.open_by_key('1PMgqjZr2nieniRShicaPyxAe6J6j7I04FFE5aNWnm_s')
            ws_transf = planilha_transf.get_worksheet(0) 
            dados_transf = ws_transf.get_all_values()
            
            if dados_transf and len(dados_transf) > 1:
                df_transf = pd.DataFrame(dados_transf[1:], columns=dados_transf[0])
                df_transf = df_transf.loc[:, ~df_transf.columns.duplicated()]
                df_transf = df_transf.loc[:, df_transf.columns != '']
                df_transf.columns = df_transf.columns.str.strip().str.upper()
                
                if 'QTDE' in df_transf.columns:
                    df_transf['QTDE'] = pd.to_numeric(df_transf['QTDE'], errors='coerce').fillna(0)
                
                # Inteligência de parsing para aceitar múltiplos formatos sem gerar erro
                if 'DATA REF' in df_transf.columns:
                    df_transf['DATA_FILTRO'] = pd.to_datetime(df_transf['DATA REF'], errors='coerce', dayfirst=True).dt.normalize()
                else:
                    df_transf['DATA_FILTRO'] = pd.NaT
        except Exception as e:
            pass 

    except Exception as e: 
        st.error(f"🚨 Erro crítico de conexão com o Banco de Dados do Google: {e}")
        
    return df, df_itens, df_plan, df_transf

df, df_itens, df_plan, df_transf = carregar_dados()

if df.empty and df_transf.empty:
    st.warning("⏳ Aguardando dados das planilhas para renderizar o Dashboard.")
    st.stop()

# --- BARRA LATERAL E NAVEGAÇÃO ---
st.sidebar.image("https://magalog.com.br/opengraph-image.jpg?fdd536e7d35ec9da", width=300)
st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.header("📍 Menu de Navegação")
pagina = st.sidebar.radio("Ir para:", ["🏠 Painel Operacional", "🧩 Planejamento Lego", "🚛 Histórico325"])
st.sidebar.markdown("---")

# ==============================================================================
# INTELIGÊNCIA DO FILTRO DE DATAS (LIVRE DE TRAVAS)
# ==============================================================================
st.sidebar.header("📅 Período de Análise")

# Prepara os valores padrão
if pagina == "🚛 Histórico325" and not df_transf.empty and not df_transf['DATA_FILTRO'].isna().all():
    data_min_padrao = df_transf['DATA_FILTRO'].min().date()
    data_max_padrao = df_transf['DATA_FILTRO'].max().date()
else:
    data_min_padrao = df['Data'].min().date() if not df.empty else pd.to_datetime('today').date()
    data_max_padrao = df['Data'].max().date() if not df.empty else pd.to_datetime('today').date()

# O Calendário destravado (sem min_value e max_value)
datas_selecionadas = st.sidebar.date_input(
    "Selecione o Início e o Fim:", 
    value=(data_min_padrao, data_max_padrao), 
    format="DD/MM/YYYY"
)

if len(datas_selecionadas) == 2: data_inicio, data_fim = datas_selecionadas
else: data_inicio = data_fim = datas_selecionadas[0]

# ==============================================================================
# PÁGINA 1: PAINEL OPERACIONAL
# ==============================================================================
if pagina == "🏠 Painel Operacional":
    df_filtrado = df[(df['Data'].dt.date >= data_inicio) & (df['Data'].dt.date <= data_fim)]
    
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Parâmetros Operacionais")
    capacidade_diaria = st.sidebar.number_input("Equipes Disponíveis/Dia", min_value=1, max_value=30, value=6)
    custo_hora_extra = st.sidebar.number_input("Custo da Hora Extra (R$)", min_value=1.0, value=9.0, format="%.2f")
    limite_agendas_1p = st.sidebar.number_input("Teto Agendas 1P/Dia", min_value=1, max_value=50, value=14)

    st.sidebar.markdown("---")
    canal_selecionado = st.sidebar.multiselect("🏢 Canal de Entrada", options=df_filtrado['Canal'].unique(), default=df_filtrado['Canal'].unique())
    status_operacao = st.sidebar.multiselect("🚦 Status da Carga", options=df_filtrado['Status'].unique(), default=df_filtrado['Status'].unique())
    
    if 'É Ofensor?' in df_filtrado.columns:
        status_ofensor = st.sidebar.multiselect("⚠️ Risco de Planejamento", options=df_filtrado['É Ofensor?'].unique(), default=df_filtrado['É Ofensor?'].unique())
        df_filtrado_op = df_filtrado[(df_filtrado['É Ofensor?'].isin(status_ofensor)) & (df_filtrado['Canal'].isin(canal_selecionado)) & (df_filtrado['Status'].isin(status_operacao))]
    else:
        df_filtrado_op = df_filtrado[(df_filtrado['Canal'].isin(canal_selecionado)) & (df_filtrado['Status'].isin(status_operacao))]

    st.title("📦 Torre de Controle Inbound | CD2900")
    st.markdown(f"**Visão Executiva:** {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    st.markdown("---")

    st.header("🚦 Painel Operacional")
    col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5, col_kpi6 = st.columns(6)

    qtd_agendado = len(df_filtrado_op[df_filtrado_op['Status'] == 'Agendado'])
    qtd_transito = len(df_filtrado_op[df_filtrado_op['Status'] == 'Em Trânsito'])
    qtd_aguardando = len(df_filtrado_op[df_filtrado_op['Status'] == 'Aguardando'])
    qtd_descarga = len(df_filtrado_op[df_filtrado_op['Status'] == 'Em Descarga'])
    qtd_recebido = len(df_filtrado_op[df_filtrado_op['Status'] == 'Recebido'])
    qtd_noshow = len(df_filtrado_op[df_filtrado_op['Status'] == 'No-Show'])
    total_agendas = len(df_filtrado_op)
    taxa_noshow = (qtd_noshow / total_agendas * 100) if total_agendas > 0 else 0

    with col_kpi1: exibir_kpi("📅 Agendado", qtd_agendado, "Total de agendas", "#3498DB")
    with col_kpi2: exibir_kpi("🚛 Em Trânsito", qtd_transito, "A caminho do CD", "#9B59B6")
    with col_kpi3: exibir_kpi("⏳ Pátio", qtd_aguardando, "Aguardando doca", "#F39C12")
    with col_kpi4: exibir_kpi("⚙️ Em Descarga", qtd_descarga, "Operação rodando", "#1ABC9C")
    with col_kpi5: exibir_kpi("✅ Recebido", qtd_recebido, "Finalizados", "#2ECC71")
    with col_kpi6: exibir_kpi("❌ No-Show", qtd_noshow, f"{taxa_noshow:.1f}% de quebra", "#E74C3C")

    st.markdown("---")

    st.header("📉 Painel de Ausências (Detalhamento)")
    df_noshow = df_filtrado_op[df_filtrado_op['Status'] == 'No-Show'].copy()

    col_aus_full, col_aus_1p = st.columns(2)
    with col_aus_full:
        st.markdown("#### Ausência FULL")
        df_aus_full = df_noshow[df_noshow['Canal'] == 'Fulfillment'][['Agenda', 'Fornecedor', 'Qtd SKUs', 'Qtd Peças']].rename(columns={'Qtd SKUs': 'SKU', 'Qtd Peças': 'Peças'})
        if not df_aus_full.empty:
            st.dataframe(df_aus_full, use_container_width=True, hide_index=True)
            st.caption(f"**Total Geral (Peças):** {df_aus_full['Peças'].sum():,.0f}".replace(',', '.'))
        else: st.info("Nenhuma ausência de Fulfillment registrada no período.")

    with col_aus_1p:
        st.markdown("#### Ausência 1P Fornecedor")
        df_aus_1p = df_noshow[df_noshow['Canal'] == '1P Fornecedor'][['Agenda', 'Fornecedor', 'Linhas', 'Qtd SKUs', 'Qtd Peças']].rename(columns={'Linhas': 'Linha', 'Qtd SKUs': 'SKU', 'Qtd Peças': 'Peças'})
        if not df_aus_1p.empty:
            st.dataframe(df_aus_1p, use_container_width=True, hide_index=True)
            st.caption(f"**Total Geral (Peças):** {df_aus_1p['Peças'].sum():,.0f}".replace(',', '.'))
        else: st.info("Nenhuma ausência de 1P registrada no período.")

    st.markdown("---")

    st.header("📏 Recebimento: Teto de Agendas 1P")
    df_1p = df_filtrado_op[df_filtrado_op['Canal'] == '1P Fornecedor'].copy()

    if not df_1p.empty:
        df_1p['E_Cofre'] = df_1p['Linhas'].apply(lambda x: 1 if 'COFRE' in str(x).upper() else 0)
        df_1p['Agenda_Valida_Limite'] = 1 - df_1p['E_Cofre'] 
        
        df_limite_1p = df_1p.groupby('Data').agg(Total_1P=('Agenda_Texto', 'count'), Qtd_Cofres=('E_Cofre', 'sum'), Agendas_Validas=('Agenda_Valida_Limite', 'sum')).reset_index()
        df_limite_1p['Estourou_Limite'] = df_limite_1p['Agendas_Validas'] > limite_agendas_1p
        
        col_1p_1, col_1p_2 = st.columns([2, 1])
        with col_1p_1:
            fig_1p = px.bar(df_limite_1p, x='Data', y='Agendas_Validas', text='Agendas_Validas', color='Estourou_Limite', color_discrete_map={False: '#3498DB', True: '#E74C3C'}, labels={'Agendas_Validas': 'Agendas', 'Estourou_Limite': 'Acima do Limite?'})
            fig_1p.add_hline(y=limite_agendas_1p, line_dash="dot", line_color="#E74C3C", annotation_text=f"Capacidade: {limite_agendas_1p}")
            fig_1p.update_traces(textposition='outside')
            fig_1p.update_layout(xaxis=dict(tickformat="%d/%m/%Y"), showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_1p, use_container_width=True)
            
        with col_1p_2:
            st.subheader("Balanço 1P")
            exibir_kpi("Dias Acima do Limite", df_limite_1p['Estourou_Limite'].sum(), "Necessita adequação", "#E74C3C")
            exibir_kpi("Volume 1P", df_limite_1p['Total_1P'].sum(), "Total de agendas 1P", "#3498DB")
            exibir_kpi("Isentos (Cofres)", df_limite_1p['Qtd_Cofres'].sum(), "Não consomem doca padrão", "#95A5A6")
    else: st.info("Nenhuma agenda do canal 1P Fornecedor encontrada.")

    st.markdown("---")

    st.header("👥 Visão APC - CD2900")
    df_apc = df_filtrado_op.groupby('Data').agg({'Tempo_APC_Minutos': 'sum', 'Agenda_Texto': 'count'}).reset_index()
    df_apc['Min_Transf_Fixa'] = df_apc['Data'].apply(lambda x: 1200 if x.weekday() < 5 else 0)
    df_apc['Minutos Totais'] = df_apc['Tempo_APC_Minutos'] + df_apc['Min_Transf_Fixa']
    df_apc['Equipes Necessárias'] = df_apc['Minutos Totais'].apply(lambda x: math.ceil(x / 427))
    df_apc['Gap_Equipes'] = df_apc['Equipes Necessárias'] - capacidade_diaria
    df_apc['Minutos_Disponiveis'] = capacidade_diaria * 427
    df_apc['Deficit_Minutos'] = df_apc.apply(lambda row: max(0, row['Minutos Totais'] - row['Minutos_Disponiveis']), axis=1)
    df_apc['Horas_Extras'] = (df_apc['Deficit_Minutos'] / 60).apply(math.ceil)
    df_apc['Custo_HE'] = df_apc['Horas_Extras'] * custo_hora_extra

    if not df_apc.empty:
        st.markdown("### 📊 Visão Acumulada")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1: exibir_kpi("Média Equipes/Dia", math.ceil(df_apc['Equipes Necessárias'].mean()), "Recurso Humano", "#3498DB")
        with col_m2: exibir_kpi("Dias em Sobrecarga", len(df_apc[df_apc['Gap_Equipes'] > 0]), f"De {len(df_apc)} analisados", "#E74C3C")
        with col_m3: exibir_kpi("Déficit Projetado", f"{df_apc['Horas_Extras'].sum()} h", f"Custo HE: {formatar_moeda(df_apc['Custo_HE'].sum())}", "#E74C3C")
        with col_m4: exibir_kpi("Agendas Expostas", df_filtrado_op[df_filtrado_op['Data'].isin(df_apc[df_apc['Gap_Equipes'] > 0]['Data'])]['Agenda_Texto'].nunique(), "Cargas com risco", "#F39C12")
        
        fig_equipes = px.bar(df_apc, x='Data', y='Equipes Necessárias', text='Equipes Necessárias', color_discrete_sequence=['#3498DB'])
        fig_equipes.add_hline(y=capacidade_diaria, line_dash="solid", line_color="#E74C3C", annotation_text=f"Headcount Fixo ({capacidade_diaria})")
        fig_equipes.update_traces(textposition='outside')
        fig_equipes.update_layout(xaxis=dict(tickformat="%d/%m/%Y"), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis_title="Qtd Equipes", title="Necessidade Diária de Mão de Obra")
        st.plotly_chart(fig_equipes, use_container_width=True)

    st.markdown("---")
    st.header("🔥 Possíveis Gargalos")
    df_apc_sobrecarga = df_apc[df_apc['Gap_Equipes'] > 0]

    if not df_apc_sobrecarga.empty:
        col_sel1, col_sel2 = st.columns([1, 3])
        with col_sel1: dia_selecionado = st.selectbox("Inspecionar dia crítico:", df_apc_sobrecarga['Data'].dt.strftime('%d/%m/%Y').tolist())
        
        df_dia_critico = df_filtrado_op[df_filtrado_op['Data'].dt.strftime('%d/%m/%Y') == dia_selecionado].copy()
        dados_apc_dia = df_apc[df_apc['Data'].dt.strftime('%d/%m/%Y') == dia_selecionado].iloc[0]
        
        st.markdown(f"### 🎯 Analise Operacional: {dia_selecionado}")
        met_col1, met_col2, met_col3, met_col4 = st.columns(4)
        with met_col1: exibir_kpi("Equipes Necessárias", dados_apc_dia['Equipes Necessárias'], "Demanda do dia", "#3498DB")
        with met_col2: exibir_kpi("Capacidade Atual", capacidade_diaria, "Headcount Fixo", "#95A5A6")
        with met_col3: exibir_kpi("🚨 H.E. Projetadas", f"{dados_apc_dia['Horas_Extras']} h", f"Custo: {formatar_moeda(dados_apc_dia['Custo_HE'])}", "#E74C3C")
        with met_col4: exibir_kpi("Volume de Peças", f"{df_dia_critico['Qtd Peças'].sum():,.0f}".replace(',', '.'), "Físico", "#9B59B6")
        
        col_chart, col_tab = st.columns([1, 2])
        with col_chart:
            fig_canais = px.pie(df_dia_critico.groupby('Canal')['Tempo_APC_Minutos'].sum().reset_index(), values='Tempo_APC_Minutos', names='Canal', hole=0.4, color_discrete_map={'Fulfillment': '#3498DB', '1P Fornecedor': '#F39C12'})
            fig_canais.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_canais, use_container_width=True)
        with col_tab:
            st.dataframe(df_dia_critico[['Status', 'Canal', 'Linhas', 'Agenda_Texto', 'Fornecedor', 'Qtd Peças', 'Tempo_APC_Minutos']].rename(columns={'Agenda_Texto': 'Agenda', 'Tempo_APC_Minutos': 'APC (Min)'}).sort_values(by='APC (Min)', ascending=False), use_container_width=True, hide_index=True)

        st.markdown("### 📦 Inspecionar Carga")
        agenda_selecionada = st.selectbox("Escolha uma agenda do dia para ver o detalhamento:", df_dia_critico['Agenda_Texto'].unique())
        
        if not df_itens.empty and 'Agenda' in df_itens.columns:
            agenda_limpa = str(agenda_selecionada).split('.')[0].strip()
            df_produtos_agenda = df_itens[df_itens['Agenda'] == agenda_limpa].copy()
            
            if not df_produtos_agenda.empty: 
                colunas_exibir = [c for c in ['SKU', 'Descrição', 'Linhas', 'Categoria'] if c in df_produtos_agenda.columns]
                
                if 'Qtd Peças' in df_produtos_agenda.columns:
                    df_produtos_agenda['Qtd Peças'] = pd.to_numeric(df_produtos_agenda['Qtd Peças'], errors='coerce').fillna(0)
                    resumo_itens = df_produtos_agenda.groupby(colunas_exibir)['Qtd Peças'].sum().reset_index()
                    total_pecas = resumo_itens['Qtd Peças'].sum()
                else:
                    resumo_itens = df_produtos_agenda.groupby(colunas_exibir).size().reset_index(name='Qtd Itens')
                    total_pecas = resumo_itens['Qtd Itens'].sum()
                
                total_skus = len(resumo_itens)
                df_fornecedor_temp = df_dia_critico[df_dia_critico['Agenda_Texto'] == agenda_selecionada]
                fornecedor_nome = df_fornecedor_temp['Fornecedor'].iloc[0] if not df_fornecedor_temp.empty else "Não Informado"

                st.markdown(f"#### Resumo da Agenda: {agenda_limpa}")
                kpi_c1, kpi_c2, kpi_c3 = st.columns(3)
                with kpi_c1: exibir_kpi("📦 Qtd de SKUs", f"{total_skus}", "Itens distintos", "#3498DB")
                with kpi_c2: exibir_kpi("🔢 Qtd Peças Totais", f"{total_pecas:,.0f}".replace(',', '.'), "Volume da carga", "#9B59B6")
                with kpi_c3: exibir_kpi("🏢 Fornecedor", f"{fornecedor_nome[:22]}", "Origem", "#F39C12")
                
                st.dataframe(resumo_itens, use_container_width=True, hide_index=True)
            else: 
                st.warning(f"Os itens da agenda {agenda_limpa} não foram encontrados na base.")
        else:
            st.warning("Base de Itens indisponível.")
    else: st.success("✅ A operação fluiu sem gargalos no período analisado!")


# ==============================================================================
# PÁGINA 2: MATRIZ DE PLANEJAMENTO (S&OP COMERCIAL)
# ==============================================================================
elif pagina == "🧩 Planejamento Lego":
    st.title("🧩 Visão planejamento capacidade LEGO")

    df_plan_filtrado = df_plan[(df_plan['data'].dt.date >= data_inicio) & (df_plan['data'].dt.date <= data_fim)].copy() if not df_plan.empty else pd.DataFrame()

    if not df_plan.empty:
        st.markdown("### 🎯 Planejamento Mensal do Comercial")
        st.write("Digite as vagas aprovadas (LEGO) e clique em Salvar. O sistema gravará na Nuvem (Google Sheets).")
        
        categorias_existentes = sorted([c for c in df_plan['categoria'].unique() if pd.notna(c) and str(c).strip() != ''])
        df_base_categorias = pd.DataFrame({'CATEGORIA': categorias_existentes})
        
        try:
            planilha = conectar_google_sheets()
            ws_metas = planilha.worksheet("METAS_LEGO")
            dados_salvos = ws_metas.get_all_values()
            
            if dados_salvos and len(dados_salvos) > 1:
                df_salvo = pd.DataFrame(dados_salvos[1:], columns=dados_salvos[0])
                df_salvo = df_salvo.loc[:, ~df_salvo.columns.duplicated()]
                df_salvo = df_salvo.loc[:, df_salvo.columns != '']
                if 'LEGO (Meta)' in df_salvo.columns:
                    df_salvo['LEGO (Meta)'] = pd.to_numeric(df_salvo['LEGO (Meta)'], errors='coerce').fillna(0)
                df_metas_iniciais = pd.merge(df_base_categorias, df_salvo, on='CATEGORIA', how='left').fillna(0)
            else:
                df_metas_iniciais = df_base_categorias.copy()
                df_metas_iniciais['LEGO (Meta)'] = 0
        except:
            df_metas_iniciais = df_base_categorias.copy()
            df_metas_iniciais['LEGO (Meta)'] = 0

        df_metas_iniciais['LEGO (Meta)'] = df_metas_iniciais['LEGO (Meta)'].astype(int)

        with st.expander("📝 CLIQUE AQUI PARA PREENCHER AS METAS DO MÊS", expanded=False):
            df_metas_editadas = st.data_editor(df_metas_iniciais, use_container_width=True, hide_index=True)
            
            if st.button("💾 Salvar Metas na Nuvem"):
                try:
                    df_para_salvar = df_metas_editadas.copy()
                    df_para_salvar['LEGO (Meta)'] = df_para_salvar['LEGO (Meta)'].astype(str)
                    dados_finais = [df_para_salvar.columns.tolist()] + df_para_salvar.values.tolist()

                    planilha = conectar_google_sheets()
                    try: ws_metas = planilha.worksheet("METAS_LEGO")
                    except: ws_metas = planilha.add_worksheet(title="METAS_LEGO", rows="100", cols="2")
                        
                    ws_metas.clear() 
                    try: ws_metas.update(values=dados_finais, range_name="A1")
                    except: ws_metas.update("A1", dados_finais)
                        
                    st.success("✅ Metas sincronizadas com sucesso no Google Sheets!")
                except Exception as e:
                    st.error(f"🚨 Erro ao salvar na nuvem: {e}")

        resumo_real = df_plan_filtrado.groupby('categoria')['quantidade_real'].sum().reset_index()
        resumo_real.rename(columns={'categoria': 'CATEGORIA', 'quantidade_real': 'CARROS (Realizado)'}, inplace=True)
        
        df_executivo = pd.merge(df_metas_editadas, resumo_real, on='CATEGORIA', how='left').fillna(0)
        df_executivo['VAGAS (Saldo)'] = df_executivo['LEGO (Meta)'] - df_executivo['CARROS (Realizado)']
        
        st.markdown("---")
        st.markdown("### 📊 Balanço Geral do Período")
        
        meta_total = df_executivo['LEGO (Meta)'].sum()
        realizado_total = df_executivo['CARROS (Realizado)'].sum()
        saldo_total = df_executivo['VAGAS (Saldo)'].sum()
        estouradas = len(df_executivo[df_executivo['VAGAS (Saldo)'] < 0])
        
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
        with col_e1: exibir_kpi("Meta (LEGO)", f"{meta_total:,.0f}".replace(',', '.'), "Alvo Comercial", "#3498DB")
        with col_e2: exibir_kpi("Agendado", f"{realizado_total:,.0f}".replace(',', '.'), "Realidade", "#9B59B6")
        
        cor_saldo = "#2ECC71" if saldo_total >= 0 else "#E74C3C"
        texto_saldo = "Capacidade Livre" if saldo_total >= 0 else "Risco Global"
        with col_e3: exibir_kpi("Saldo de Vagas", f"{saldo_total:,.0f}".replace(',', '.'), texto_saldo, cor_saldo)
        with col_e4: exibir_kpi("Categorias Estouradas", estouradas, "Acima da Meta", "#E74C3C")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🔍 Fechamento por Categoria")
        
        df_executivo_limpo = df_executivo[(df_executivo['LEGO (Meta)'] > 0) | (df_executivo['CARROS (Realizado)'] > 0)]
        
        def cor_vagas(val):
            if val < 0: return 'background-color: #FDEDEC; color: #E74C3C; font-weight: bold;'
            elif val > 0: return 'background-color: #EAFAF1; color: #27AE60; font-weight: bold;'
            else: return ''

        tabela_formatada = df_executivo_limpo.style.format(
            formatter="{:.0f}", 
            subset=['LEGO (Meta)', 'CARROS (Realizado)', 'VAGAS (Saldo)']
        ).map(cor_vagas, subset=['VAGAS (Saldo)'])

        st.dataframe(tabela_formatada, use_container_width=True, hide_index=True)

        st.markdown("---")
        
        st.markdown("### 🧩 Tabela Matricial Diária (LEGO)")
        if not df_plan_filtrado.empty:
            pivot = pd.pivot_table(
                df_plan_filtrado, index='categoria', columns='data', 
                values=['quantidade_planejado', 'quantidade_real'], aggfunc='sum', fill_value=0
            )
            pivot = pivot.swaplevel(0, 1, axis=1).sort_index(axis=1, level=0)
            
            pivot = pivot.loc[(pivot != 0).any(axis=1)]

            if not pivot.empty:
                novas_colunas = []
                for data_col, tipo_col in pivot.columns:
                    novas_colunas.append((data_col.strftime('%d/%m/%Y'), 'PLANEJADO' if 'planejado' in tipo_col else 'REALIZADO'))
                pivot.columns = pd.MultiIndex.from_tuples(novas_colunas)
                pivot.loc['Total Geral'] = pivot.sum()

                def formatar_tabela_lego(df_pivot):
                    estilos = pd.DataFrame('', index=df_pivot.index, columns=df_pivot.columns)
                    for coluna in df_pivot.columns:
                        data_str, tipo = coluna
                        for indice in df_pivot.index:
                            valor = df_pivot.loc[indice, coluna]
                            css = ''
                            if pd.isna(valor) or valor == 0:
                                css += 'color: rgba(0,0,0,0); background-color: rgba(0,0,0,0); ' 
                            else:
                                css += 'background-color: #FDEDEC; color: #C0392B; font-weight: bold; ' 
                            if tipo == 'PLANEJADO':
                                css += 'border-left: 2px solid #EAEDED; '
                            elif tipo == 'REALIZADO':
                                css += 'border-right: 2px solid #EAEDED; '
                            estilos.loc[indice, coluna] = css
                    return estilos

                tabela_estilizada = pivot.style.format("{:.0f}").apply(formatar_tabela_lego, axis=None)
                st.dataframe(tabela_estilizada, use_container_width=True, height=600)
            else:
                st.info("Nenhuma vaga com valor preenchido no período selecionado.")
        else:
            st.info("Nenhum dado encontrado para o período filtrado.")
    else:
        st.warning("⚠️ Planilha 'PLANEJAMENTO' vazia ou não encontrada no Google Sheets.")


# ==============================================================================
# PÁGINA 3: HISTÓRICO 325 (TRANSFERÊNCIAS)
# ==============================================================================
elif pagina == "🚛 Histórico325":
    st.title("🚛 Visão de Transferências | Histórico325")
    
    if not df_transf.empty:
        df_transf_periodo = df_transf[(df_transf['DATA_FILTRO'].dt.date >= data_inicio) & (df_transf['DATA_FILTRO'].dt.date <= data_fim)].copy()

        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filtros de Transferência")
        
        opcoes_modal = sorted(df_transf_periodo['MODAL2'].dropna().unique()) if 'MODAL2' in df_transf_periodo.columns else []
        modal_selecionado = st.sidebar.multiselect("Tipo de Carga (Modal)", options=opcoes_modal, default=opcoes_modal)
        
        if 'MODAL2' in df_transf_periodo.columns:
            df_transf_periodo = df_transf_periodo[df_transf_periodo['MODAL2'].isin(modal_selecionado)]

        if 'ID_CARGA_PCP' in df_transf_periodo.columns:
            
            def compor_modalidade(series):
                return ' | '.join(sorted([str(x).strip() for x in series.dropna().unique() if str(x).strip() != '']))

            resumo_tabela = df_transf_periodo.groupby('ID_CARGA_PCP').agg(
                DATA_PRODUCAO=('DATA SEPARACAO', 'first') if 'DATA SEPARACAO' in df_transf_periodo.columns else ('DATA_FILTRO', 'first'),
                LIBERACAO=('DATA LIBERAÇÃO', 'first') if 'DATA LIBERAÇÃO' in df_transf_periodo.columns else ('DATA_FILTRO', 'first'),
                CD_ORIGEM=('CD_EMPRESA', 'first') if 'CD_EMPRESA' in df_transf_periodo.columns else ('ID_CARGA_PCP', 'first'),
                DATA_ENTREGA=('DATA ENTREGA CLIENTE', 'first') if 'DATA ENTREGA CLIENTE' in df_transf_periodo.columns else ('DATA_FILTRO', 'first'),
                MODALIDADE=('MODAL2', compor_modalidade) if 'MODAL2' in df_transf_periodo.columns else ('ID_CARGA_PCP', 'first'),
                SKUS=('PRODUTO', 'nunique') if 'PRODUTO' in df_transf_periodo.columns else ('ID_CARGA_PCP', 'nunique'),
                PECAS=('QTDE', 'sum') if 'QTDE' in df_transf_periodo.columns else ('ID_CARGA_PCP', 'count'),
                DATA_CD=('DATA REF', 'first') if 'DATA REF' in df_transf_periodo.columns else ('DATA_FILTRO', 'first')
            ).reset_index()

            resumo_tabela['CD_ORIGEM'] = 'CD ' + resumo_tabela['CD_ORIGEM'].astype(str)
            for col in ['DATA_PRODUCAO', 'LIBERACAO', 'DATA_ENTREGA', 'DATA_CD']:
                if col in resumo_tabela.columns:
                    resumo_tabela[col] = pd.to_datetime(resumo_tabela[col], errors='coerce').dt.strftime('%d/%m/%Y').fillna('-')
            
            resumo_tabela = resumo_tabela.rename(columns={
                'ID_CARGA_PCP': 'ID2900 (Carga)',
                'DATA_PRODUCAO': 'Data Produção',
                'LIBERACAO': 'Liberação Orig.',
                'CD_ORIGEM': 'CD Origem',
                'DATA_ENTREGA': 'DATA ENTREGA',
                'MODALIDADE': 'Modalidade',
                'SKUS': 'Skus',
                'PECAS': 'Peças',
                'DATA_CD': 'DATA CD'
            })

            total_cargas = len(resumo_tabela)
            total_skus = df_transf_periodo['PRODUTO'].nunique() if 'PRODUTO' in df_transf_periodo.columns else 0
            total_pecas = resumo_tabela['Peças'].sum()
            
            st.markdown("### 📊 Indicadores de Transferência")
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: exibir_kpi("🚛 Cargas Esperadas", total_cargas, "Veículos de transf.", "#9B59B6") 
            with col_t2: exibir_kpi("📦 Mix de Produtos", total_skus, "SKUs distintos", "#3498DB")         
            with col_t3: exibir_kpi("🔢 Volume Físico", f"{total_pecas:,.0f}".replace(',', '.'), "Peças a receber", "#2ECC71")

            st.markdown("---")
            
            st.markdown("### 📑 Tabela de Acompanhamento (Master)")
            st.dataframe(resumo_tabela, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("### 📈 Análise de Fluxo")
            
            graf_col1, graf_col2 = st.columns([2, 1])
            with graf_col1:
                evolucao = resumo_tabela.groupby('Data Produção')['Peças'].sum().reset_index()
                fig_transf = px.bar(evolucao, x='Data Produção', y='Peças', text='Peças', title="Volume de Peças por Dia", color_discrete_sequence=['#9B59B6'])
                fig_transf.update_traces(textposition='outside')
                fig_transf.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_transf, use_container_width=True)
            
            with graf_col2:
                fig_modal = px.pie(resumo_tabela, values='Peças', names='Modalidade', title="Distribuição por Modal", hole=0.4, color_discrete_sequence=px.colors.sequential.Purples_r)
                fig_modal.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_modal, use_container_width=True)

        else:
            st.warning("A coluna 'ID_CARGA_PCP' não foi encontrada na planilha de Transferências.")
    else:
        st.warning("⚠️ Planilha de Transferências não carregou. O e-mail do robô está como Leitor nela?")
