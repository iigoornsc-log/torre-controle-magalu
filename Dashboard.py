import streamlit as st
import pandas as pd
import plotly.express as px
import math
import gspread
from google.oauth2.service_account import Credentials
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Torre de Controle | Magalu", page_icon="🛍️", layout="wide", initial_sidebar_state="expanded")

# --- INJEÇÃO DE CSS (Identidade Visual Magazine Luiza) ---
st.markdown("""
<style>
    .stApp { background-color: #F4F6F9; color: #333333; }
    h1, h2, h3 { color: #0086FF !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 700; }
    div[data-testid="metric-container"] {
        background-color: #FFFFFF; border: 1px solid #EAEAEA; border-radius: 8px;
        padding: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border-left: 5px solid #0086FF;
    }
    hr { border-top: 2px solid #EAEAEA; }
    .stDataFrame { border: 1px solid #EAEAEA; border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- CONEXÃO INTELIGENTE (LOCAL / NUVEM) ---
def conectar_google_sheets():
    try:
        cred_dict = json.loads(st.secrets["google_json"])
        creds = Credentials.from_service_account_info(cred_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    except:
        caminho_local = 'C:/Users/ign_oliveira/Documents/Analises Agendas/credential_key.json'
        creds = Credentials.from_service_account_file(caminho_local, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    
    client = gspread.authorize(creds)
    return client.open_by_key('1WA5GjT1f-jpQ4Sw_OfvXBERyz5MehfH7uaFrIfUMrtw')

# --- EXTRAÇÃO DOS DADOS DO GOOGLE SHEETS ---
@st.cache_data(ttl=300) # Atualiza a cada 5 minutos
def carregar_dados():
    df = pd.DataFrame()
    df_itens = pd.DataFrame()
    df_plan = pd.DataFrame()
    
    try:
        planilha = conectar_google_sheets()
        
        # ==============================================================================
        # 1. LENDO A ABA CONSOLIDADO (Apenas os KPIs Principais)
        # ==============================================================================
        ws_consolidado = planilha.worksheet("CONSOLIDADO")
        dados_consolidado = ws_consolidado.get_all_values() 
        
        if dados_consolidado and len(dados_consolidado) > 1:
            df = pd.DataFrame(dados_consolidado[1:], columns=dados_consolidado[0])
            df = df.loc[:, ~df.columns.duplicated()]
            df = df.loc[:, df.columns != '']
            
            # Deixa tudo em maiúsculo para evitar erro de digitação do sistema
            df.columns = df.columns.str.strip().str.upper()
            
            # Mapeamento blindado para a aba CONSOLIDADO
            mapeamento_cons = {
                'AGENDA': 'Agenda',
                'DATA': 'Data',
                'FORNECEDOR': 'Fornecedor',
                'LINHA': 'Linhas',
                'CATEGORIA': 'Categoria',
                'QTD SKUS': 'Qtd SKUs',
                'QTD PEÇAS': 'Qtd Peças',
                'STATUS AGENDA': 'Status',
                'STATUS': 'Status'
            }
            df = df.rename(columns=mapeamento_cons)
            
            # Garante que colunas de números não quebrem
            for col in ['Qtd SKUs', 'Qtd Peças']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                else:
                    df[col] = 0

            # Se não vier a coluna Ofensor, criamos para não quebrar a tela
            if 'É Ofensor?' not in df.columns:
                df['É Ofensor?'] = 'Não'

            # Tradutor de Status
            def padronizar_status(val):
                v = str(val).upper().strip()
                if 'AGENDADO' in v: return 'Agendado'
                if 'PATIO' in v or 'PÁTIO' in v or 'AGUARDANDO' in v: return 'Aguardando'
                if 'RECEB' in v: return 'Recebido'
                if 'COMPARECEU' in v or 'SHOW' in v: return 'No-Show'
                if 'TRANSITO' in v or 'TRÂNSITO' in v: return 'Em Trânsito'
                if 'DESCARGA' in v: return 'Em Descarga'
                return v.title()

            if 'Status' in df.columns:
                df['Status'] = df['Status'].apply(padronizar_status)

            # Limpeza final de Data e Agenda
            if 'Data' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce', dayfirst=True).dt.normalize()
            if 'Agenda' in df.columns:
                df = df[df['Agenda'].astype(str).str.strip() != '']
                df['Agenda'] = df['Agenda'].astype(str).str.split('.').str[0].str.strip()
            
            df['Agenda_Texto'] = df['Agenda']
            df['Canal'] = df['Agenda_Texto'].apply(lambda x: 'Fulfillment' if len(x) >= 6 else '1P Fornecedor')

            def calcular_minutos(row):
                canal = row.get('Canal', '')
                fornecedor = str(row.get('Fornecedor', '')).strip().upper()
                if canal == 'Fulfillment': return 60.0 
                else:
                    linhas = str(row.get('Linhas', '')).upper().split(',')
                    maior_tempo = 0 
                    for l in linhas:
                        t = 90
                        if 'MADEIRA' in l: t = 180 if 'TUBRAX' in fornecedor else 427
                        elif 'PNEU' in l: t = 240
                        elif 'TRANSFERENCIA RUIM' in l: t = 40
                        elif 'TRANSFERENCIA' in l: t = 240
                        elif 'MERCADO' in l: t = 150
                        elif 'ELETRO' in l: t = 95
                        elif 'COFRE' in l: t = 90
                        elif 'IMAGEM' in l: t = 90
                        elif 'COLCHÃO' in l or 'ESTOFADO' in l: t = 60
                        if t > maior_tempo: maior_tempo = t
                    return maior_tempo
            
            df['Tempo_APC_Minutos'] = df.apply(calcular_minutos, axis=1)

        # ==============================================================================
        # 2. ABA ITEM AGENDA (A Mágica do "Inspecionar Cargas")
        # ==============================================================================
        try:
            ws_itens = planilha.worksheet("Item Agenda")
            dados_itens = ws_itens.get_all_values()
            if dados_itens and len(dados_itens) > 1:
                df_itens = pd.DataFrame(dados_itens[1:], columns=dados_itens[0])
                df_itens = df_itens.loc[:, ~df_itens.columns.duplicated()]
                df_itens = df_itens.loc[:, df_itens.columns != '']
                df_itens.columns = df_itens.columns.str.strip().str.upper()
                
                # Traduzindo os nomes exclusivos dessa aba
                mapeamento_itens = {
                    'CODAGENDA': 'Agenda',
                    'COMPITEM': 'SKU',
                    'DESCRICAO': 'Descrição',
                    'LINHA': 'Linhas',
                    'CATEGORIA': 'Categoria',
                    'PEÇAS REAL': 'Qtd Peças',
                    'QTCOMP': 'Qtd Peças'
                }
                
                df_itens = df_itens.rename(columns=mapeamento_itens)
                df_itens = df_itens.loc[:, ~df_itens.columns.duplicated()] # Blindagem contra colunas com nomes iguais
                    
                if 'Agenda' in df_itens.columns:
                    df_itens['Agenda'] = df_itens['Agenda'].astype(str).str.split('.').str[0].str.strip()
        except:
            pass 

        # ==============================================================================
        # 3. ABA PLANEJAMENTO
        # ==============================================================================
        try:
            ws_plan = planilha.worksheet("PLANEJAMENTO")
            dados_plan = ws_plan.get_all_values()
            
            if dados_plan and len(dados_plan) > 1:
                df_plan = pd.DataFrame(dados_plan[1:], columns=dados_plan[0])
                df_plan = df_plan.loc[:, ~df_plan.columns.duplicated()]
                df_plan = df_plan.loc[:, df_plan.columns != '']
                
                df_plan.columns = df_plan.columns.str.strip().str.lower()
                if 'data' in df_plan.columns:
                    df_plan['data'] = pd.to_datetime(df_plan['data'], format='%d/%m/%Y', errors='coerce').dt.normalize()
                if 'quantidade_planejado' in df_plan.columns:
                    df_plan['quantidade_planejado'] = pd.to_numeric(df_plan['quantidade_planejado'], errors='coerce').fillna(0)
                if 'quantidade_real' in df_plan.columns:
                    df_plan['quantidade_real'] = pd.to_numeric(df_plan['quantidade_real'], errors='coerce').fillna(0)
                
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
        except:
            pass 
            
    except Exception as e: 
        st.error(f"🚨 Erro crítico ao conectar com o Google Sheets: {e}")
        
    return df, df_itens, df_plan

df, df_itens, df_plan = carregar_dados()

if df.empty:
    st.warning("⏳ Aguardando dados na aba 'CONSOLIDADO' do Google Sheets para renderizar o Dashboard.")
    st.stop()

# --- BARRA LATERAL (MENU & FILTROS) ---
st.sidebar.image("https://magalog.com.br/opengraph-image.jpg?fdd536e7d35ec9da", width=300)
st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.header("📍 Menu de Navegação")
pagina = st.sidebar.radio("Ir para:", ["🏠 Painel Operacional", "🧩 Planejamento Lego"])
st.sidebar.markdown("---")

st.sidebar.header("📅 Período de Análise")
data_min, data_max = df['Data'].min(), df['Data'].max()
datas_selecionadas = st.sidebar.date_input("Selecione o Início e o Fim:", value=(data_min, data_max), min_value=data_min, max_value=data_max, format="DD/MM/YYYY")

if len(datas_selecionadas) == 2: data_inicio, data_fim = datas_selecionadas
else: data_inicio = data_fim = datas_selecionadas[0]

df_filtrado = df[(df['Data'] >= pd.to_datetime(data_inicio)) & (df['Data'] <= pd.to_datetime(data_fim))]

# ==============================================================================
# PÁGINA 1: PAINEL OPERACIONAL
# ==============================================================================
if pagina == "🏠 Painel Operacional":
    
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Parâmetros Operacionais")
    capacidade_diaria = st.sidebar.number_input("Equipes Disponíveis/Dia", min_value=1, max_value=30, value=6)
    custo_hora_extra = st.sidebar.number_input("Custo da Hora Extra (R$)", min_value=1.0, value=9.0, format="%.2f")
    limite_agendas_1p = st.sidebar.number_input("Teto Agendas 1P/Dia", min_value=1, max_value=50, value=14)

    st.sidebar.markdown("---")
    canal_selecionado = st.sidebar.multiselect("🏢 Canal de Entrada", options=df['Canal'].unique(), default=df['Canal'].unique())
    status_operacao = st.sidebar.multiselect("🚦 Status da Carga", options=df['Status'].unique(), default=df['Status'].unique())
    
    if 'É Ofensor?' in df.columns:
        status_ofensor = st.sidebar.multiselect("⚠️ Risco de Planejamento", options=df['É Ofensor?'].unique(), default=df['É Ofensor?'].unique())
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

    col_kpi1.metric("📅 Agendado", qtd_agendado)
    col_kpi2.metric("🚛 Em Trânsito", qtd_transito)
    col_kpi3.metric("⏳ Pátio (Aguardando)", qtd_aguardando)
    col_kpi4.metric("⚙️ Em Descarga", qtd_descarga)
    col_kpi5.metric("✅ Recebido", qtd_recebido)
    col_kpi6.metric("❌ No-Show (Geral)", qtd_noshow, f"{taxa_noshow:.1f}% de quebra", delta_color="inverse")

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
            fig_1p = px.bar(df_limite_1p, x='Data', y='Agendas_Validas', text='Agendas_Validas', color='Estourou_Limite', color_discrete_map={False: '#0086FF', True: '#FF2A2A'}, labels={'Agendas_Validas': 'Agendas', 'Estourou_Limite': 'Acima do Limite?'})
            fig_1p.add_hline(y=limite_agendas_1p, line_dash="dot", line_color="#FF2A2A", annotation_text=f"Capacidade: {limite_agendas_1p}")
            fig_1p.update_traces(textposition='outside')
            fig_1p.update_layout(xaxis=dict(tickformat="%d/%m/%Y"), showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_1p, use_container_width=True)
            
        with col_1p_2:
            st.subheader("Balanço 1P")
            st.metric("Dias Acima do Limite", df_limite_1p['Estourou_Limite'].sum(), "Necessita adequação", delta_color="inverse")
            st.metric("Volume 1P", df_limite_1p['Total_1P'].sum())
            st.metric("Isentos (Cofres)", df_limite_1p['Qtd_Cofres'].sum(), "Não consomem doca padrão")
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
        col_m1.metric("Média de Equipes / Dia", math.ceil(df_apc['Equipes Necessárias'].mean()))
        col_m2.metric("Dias em Sobrecarga", len(df_apc[df_apc['Gap_Equipes'] > 0]), f"De {len(df_apc)} dias analisados", delta_color="inverse")
        col_m3.metric(f"Déficit (Horas Extras)", f"{df_apc['Horas_Extras'].sum()} h", f"Custo: {formatar_moeda(df_apc['Custo_HE'].sum())}", delta_color="inverse")
        col_m4.metric("Agendas Expostas", df_filtrado_op[df_filtrado_op['Data'].isin(df_apc[df_apc['Gap_Equipes'] > 0]['Data'])]['Agenda_Texto'].nunique(), "Cargas com risco de atraso", delta_color="inverse")
        
        fig_equipes = px.bar(df_apc, x='Data', y='Equipes Necessárias', text='Equipes Necessárias', color_discrete_sequence=['#0086FF'])
        fig_equipes.add_hline(y=capacidade_diaria, line_dash="solid", line_color="#FF2A2A", annotation_text=f"Headcount Fixo ({capacidade_diaria})")
        fig_equipes.update_traces(textposition='outside')
        fig_equipes.update_layout(xaxis=dict(tickformat="%d/%m/%Y"), plot_bgcolor='rgba(0,0,0,0)', yaxis_title="Qtd Equipes", title="Necessidade Diária de Mão de Obra")
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
        met_col1.metric("Equipes Necessárias", dados_apc_dia['Equipes Necessárias'])
        met_col2.metric("Capacidade Atual", capacidade_diaria)
        met_col3.metric("🚨 H.E. Projetadas", f"{dados_apc_dia['Horas_Extras']} h", f"Custo: {formatar_moeda(dados_apc_dia['Custo_HE'])}", delta_color="inverse")
        met_col4.metric("Volume de Peças", f"{df_dia_critico['Qtd Peças'].sum():,.0f}".replace(',', '.'))
        
        col_chart, col_tab = st.columns([1, 2])
        with col_chart:
            fig_canais = px.pie(df_dia_critico.groupby('Canal')['Tempo_APC_Minutos'].sum().reset_index(), values='Tempo_APC_Minutos', names='Canal', hole=0.4, color_discrete_map={'Fulfillment': '#0086FF', '1P Fornecedor': '#FF8D00'})
            st.plotly_chart(fig_canais, use_container_width=True)
        with col_tab:
            st.dataframe(df_dia_critico[['Status', 'Canal', 'Linhas', 'Agenda_Texto', 'Fornecedor', 'Qtd Peças', 'Tempo_APC_Minutos']].rename(columns={'Agenda_Texto': 'Agenda', 'Tempo_APC_Minutos': 'APC (Min)'}).sort_values(by='APC (Min)', ascending=False), use_container_width=True, hide_index=True)

        st.markdown("### 📦 Inspecionar Carga")
        agenda_selecionada = st.selectbox("Escolha uma agenda do dia para ver a lista de SKUs embarcados:", df_dia_critico['Agenda_Texto'].unique())
        
        if not df_itens.empty and 'Agenda' in df_itens.columns:
            agenda_limpa = str(agenda_selecionada).split('.')[0].strip()
            df_produtos_agenda = df_itens[df_itens['Agenda'] == agenda_limpa].copy()
            
            if not df_produtos_agenda.empty: 
                colunas_exibir = [c for c in ['SKU', 'Descrição', 'Linhas', 'Categoria'] if c in df_produtos_agenda.columns]
                
                # --- SOMANDO E AGRUPANDO AS PEÇAS ---
                if 'Qtd Peças' in df_produtos_agenda.columns:
                    df_produtos_agenda['Qtd Peças'] = pd.to_numeric(df_produtos_agenda['Qtd Peças'], errors='coerce').fillna(0)
                    resumo_itens = df_produtos_agenda.groupby(colunas_exibir)['Qtd Peças'].sum().reset_index()
                    total_pecas = resumo_itens['Qtd Peças'].sum()
                else:
                    resumo_itens = df_produtos_agenda.groupby(colunas_exibir).size().reset_index(name='Qtd Itens')
                    total_pecas = resumo_itens['Qtd Itens'].sum()
                
                total_skus = len(resumo_itens)
                
                # --- OS 3 NOVOS KPIs EXECUTIVOS ---
                df_fornecedor_temp = df_dia_critico[df_dia_critico['Agenda_Texto'] == agenda_selecionada]
                fornecedor_nome = df_fornecedor_temp['Fornecedor'].iloc[0] if not df_fornecedor_temp.empty else "N/D"

                st.markdown(f"#### Resumo da Agenda: {agenda_limpa}")
                kpi_c1, kpi_c2, kpi_c3 = st.columns(3)
                kpi_c1.metric("📦 Qtd de SKUs", f"{total_skus}", "Itens Distintos")
                kpi_c2.metric("🔢 Qtd Peças Totais", f"{total_pecas:,.0f}".replace(',', '.'), "Volume Físico")
                kpi_c3.metric("🏢 Fornecedor Principal", f"{fornecedor_nome[:25]}") 
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(resumo_itens, use_container_width=True, hide_index=True)
            else: 
                st.warning(f"Os itens da agenda {agenda_limpa} não foram encontrados na aba 'Item Agenda'.")
        else:
            st.warning("A aba 'Item Agenda' está vazia ou a coluna de Agenda não foi identificada.")
    else: st.success("✅ A operação fluiu sem gargalos no período analisado!")


# ==============================================================================
# PÁGINA 2: MATRIZ DE PLANEJAMENTO (S&OP COMERCIAL)
# ==============================================================================
elif pagina == "🧩 Planejamento Lego":
    st.title("🧩 Visão planejamento capacidade LEGO")

    if not df_plan.empty:
        df_plan_filtrado = df_plan[(df_plan['data'] >= pd.to_datetime(data_inicio)) & (df_plan['data'] <= pd.to_datetime(data_fim))].copy()

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
                    try:
                        ws_metas = planilha.worksheet("METAS_LEGO")
                    except:
                        ws_metas = planilha.add_worksheet(title="METAS_LEGO", rows="100", cols="2")
                        
                    ws_metas.clear() 
                    try:
                        ws_metas.update(values=dados_finais, range_name="A1")
                    except:
                        ws_metas.update("A1", dados_finais)
                        
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
        col_e1.metric("Meta Comercial (LEGO)", f"{meta_total:,.0f}".replace(',', '.'))
        col_e2.metric("Agendado", f"{realizado_total:,.0f}".replace(',', '.'))
        col_e3.metric("Saldo de Vagas Restantes", f"{saldo_total:,.0f}".replace(',', '.'), "Risco Global" if saldo_total < 0 else "Capacidade Livre", delta_color="normal" if saldo_total >= 0 else "inverse")
        col_e4.metric("Categorias Estouradas", estouradas, "Acima da Meta", delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🔍 Fechamento por Categoria")
        
        df_executivo_limpo = df_executivo[(df_executivo['LEGO (Meta)'] > 0) | (df_executivo['CARROS (Realizado)'] > 0)]
        
        def cor_vagas(val):
            if val < 0: return 'background-color: #E74C3C; color: white; font-weight: bold;'
            elif val > 0: return 'background-color: #A2D9CE; color: #1E8449; font-weight: bold;'
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
                                css += 'background-color: #FFCDD2; color: #900C3F; font-weight: bold; ' 
                            if tipo == 'PLANEJADO':
                                css += 'border-left: 2px solid #34495E; '
                            elif tipo == 'REALIZADO':
                                css += 'border-right: 2px solid #34495E; '
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
