import streamlit as st
import pandas as pd
import plotly.express as px
import math
import gspread
from google.oauth2.service_account import Credentials
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Torre de Controle | Magalu", page_icon="🛍️", layout="wide", initial_sidebar_state="expanded")

# --- INJEÇÃO DE CSS PREMIUM (RELEVO E SOMBRAS) ---
st.markdown("""
<style>
    .stApp { background-color: #F4F7F6; color: #2C3E50; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    h1, h2, h3 { color: #2C3E50 !important; font-weight: 800; letter-spacing: -0.5px; }
    hr { border-top: 2px solid #EAEDED; border-radius: 2px; }
    
    /* Tabelas com borda arredondada e sombra */
    [data-testid="stDataFrame"] { 
        border: none !important; 
        border-radius: 12px !important; 
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important; 
        overflow: hidden !important; 
    }
    
    /* EFEITO RELEVO NOS GRÁFICOS (NOVO) */
    [data-testid="stPlotlyChart"] {
        background-color: #FFFFFF;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        padding: 15px 10px 5px 10px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    [data-testid="stPlotlyChart"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
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

# --- FUNÇÃO DE ESTILIZAÇÃO DE GRÁFICOS (NOVO) ---
def aplicar_estilo_premium(fig):
    """Aplica bordas brancas, transparência e grid clean para visual de relevo/3D."""
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Segoe UI, Roboto, sans-serif", color='#2C3E50'),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(255, 255, 255, 0.95)",
            font_size=13,
            font_family="Segoe UI",
            bordercolor="#EAEDED"
        ),
        margin=dict(t=40, b=20, l=20, r=20)
    )
    # Borda branca grossa e opacidade dão o efeito de peças separadas (Modern UI)
    fig.update_traces(
        marker=dict(line=dict(width=2, color='#FFFFFF')),
        opacity=0.88
    )
    # Grid sutil apenas no eixo Y para não poluir
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F0F3F4', griddash='dot')
    fig.update_xaxes(showgrid=False)
    return fig

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

# --- EXTRAÇÃO DE DADOS (MULTIPLAS PLANILHAS & AGRUPAMENTOS) ---
@st.cache_data(ttl=300)
def carregar_dados():
    df = pd.DataFrame()
    df_itens = pd.DataFrame()
    df_plan = pd.DataFrame()
    df_transf = pd.DataFrame()
    df_excecoes = pd.DataFrame()
    
    try:
        cliente_google = conectar_google()
        planilha_principal = cliente_google.open_by_key('1WA5GjT1f-jpQ4Sw_OfvXBERyz5MehfH7uaFrIfUMrtw')
        
        # ==============================================================================
        # 0. RECUPERANDO A BASE DE MINUTOS E EXCEÇÕES
        # ==============================================================================
        apc_full_dict = {}
        try:
            ws_apc = planilha_principal.worksheet("APC_FULL")
            dados_apc = ws_apc.get_all_values()
            if len(dados_apc) > 1:
                for row in dados_apc[1:]:
                    apc_full_dict[str(row[0]).strip().upper()] = pd.to_numeric(row[1], errors='coerce')
        except:
            try:
                df_apc_csv = pd.read_csv('Apcfull.csv', sep=None, engine='python') 
                for _, row in df_apc_csv.iterrows():
                    apc_full_dict[str(row.iloc[0]).strip().upper()] = pd.to_numeric(row.iloc[1], errors='coerce')
            except: pass
            
        try:
            ws_excecoes = planilha_principal.worksheet("EXCECOES_1P")
            dados_excecoes = ws_excecoes.get_all_values()
            if len(dados_excecoes) > 1:
                df_excecoes = pd.DataFrame(dados_excecoes[1:], columns=dados_excecoes[0])
                df_excecoes.columns = df_excecoes.columns.str.strip() 
                if 'Data da Vaga' in df_excecoes.columns:
                    df_excecoes['Data da Vaga'] = pd.to_datetime(df_excecoes['Data da Vaga'], dayfirst=True, errors='coerce').dt.normalize()
        except: pass

        # ==============================================================================
        # 1. ABA CONSOLIDADO
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

            # --- NOVO: TRADUTOR UNIVERSAL DE LINHAS PARA APC ---
            def categorizar_linha(linha_raw):
                l = str(linha_raw).upper()
                # Regras prioritárias (ex: Madeira Simples é estofado, não madeira)
                if 'MADEIRA SIMPLES' in l or 'COLCH' in l or 'ESTOFADO' in l or 'FREEPASS' in l:
                    return 'COLCHAO/ESTOFADO'
                if 'FRACIONADO' in l or 'MADEIRA' in l or 'MOVEIS ENCOMENDA' in l:
                    return 'MADEIRA'
                if 'BELEZA' in l or 'BENS DE CONSUMO' in l or 'MERCADO' in l or 'ALIMENT' in l:
                    return 'MERCADO'
                if 'COFRE' in l:
                    return 'COFRE'
                if 'ELETRO PESADO' in l or 'ELETRO' in l:
                    return 'ELETRO PESADO'
                if 'IMAGEM' in l:
                    return 'IMAGEM'
                if 'PNEU' in l:
                    return 'PNEU'
                if 'TRANSFERENCIA RUIM' in l:
                    return 'TRANSFERENCIA RUIM'
                if 'TRANSFERENCIA' in l:
                    return 'TRANSFERENCIA'
                return 'DIV PEQUENOS' # Default para UD/CM, Livros, Ferramentas, etc.

            # Aplica o tradutor
            df_raw['Categoria_Padrao'] = df_raw['Linhas'].apply(categorizar_linha)

            # Agora conta as peças de madeira baseado na categoria traduzida!
            df_raw['Pecas_Madeira'] = df_raw.apply(
                lambda r: r['Qtd Peças'] if r['Categoria_Padrao'] == 'MADEIRA' else 0, 
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
                Categorias=('Categoria_Padrao', lambda x: ', '.join(sorted(set([str(i).strip() for i in x.dropna() if str(i).strip()])))),
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
                    categorias = str(row.get('Categorias', '')).upper()
                    
                    def calcular_pela_categoria():
                        maior_tempo = 0 
                        # Agora ele divide e verifica a categoria padrão, não a linha raw
                        for cat in categorias.split(','):
                            t = 90 
                            cat = cat.strip()
                            
                            if 'MADEIRA' in cat: 
                                if row.get('Pecas_Madeira', 0) > 10:
                                    t = 110 if 'TUBRAX' in forn_original else 427
                                else:
                                    t = 90
                            elif 'PNEU' in cat: t = 240
                            elif 'TRANSFERENCIA RUIM' in cat: t = 40
                            elif 'TRANSFERENCIA' in cat: t = 240
                            elif 'MERCADO' in cat: t = 150
                            elif 'ELETRO PESADO' in cat: t = 95
                            elif 'COFRE' in cat: t = 90
                            elif 'IMAGEM' in cat: t = 90
                            elif 'COLCHAO/ESTOFADO' in cat: t = 60
                            
                            if t > maior_tempo: maior_tempo = t
                        
                        return float(maior_tempo) if maior_tempo > 0 else 60.0

                    if canal == 'Fulfillment':
                        for chave_forn, tempo in apc_full_dict.items():
                            if chave_forn in forn_original:
                                if tempo > 300: 
                                    return 60.0
                                return float(tempo)
                        return calcular_pela_categoria()
                    else:
                        return calcular_pela_categoria()
                except:
                    return 60.0
            
            df['Tempo_APC_Minutos'] = df.apply(calcular_minutos, axis=1)

        # ==============================================================================
        # 2. ABA ITEM AGENDA (1P E FULFILLMENT)
        # ==============================================================================
        df_itens_1p = pd.DataFrame()
        df_itens_full = pd.DataFrame()

        try:
            ws_itens = planilha_principal.worksheet("Item Agenda")
            dados_itens = ws_itens.get_all_values()
            if dados_itens and len(dados_itens) > 1:
                df_itens_1p = pd.DataFrame(dados_itens[1:], columns=dados_itens[0])
                df_itens_1p = df_itens_1p.loc[:, ~df_itens_1p.columns.duplicated()]
                df_itens_1p.columns = df_itens_1p.columns.str.strip().str.upper()
                
                map_itens = {}
                alvos_itens = set()
                for c in df_itens_1p.columns:
                    if 'AGENDA' in c and 'Agenda' not in alvos_itens: map_itens[c] = 'Agenda'; alvos_itens.add('Agenda')
                    elif ('SKU' in c or 'COMPITEM' in c or 'CÓDIGO' in c) and 'SKU' not in alvos_itens: map_itens[c] = 'SKU'; alvos_itens.add('SKU')
                    elif ('DESCRI' in c or 'PRODUTO' in c) and 'Descrição' not in alvos_itens: map_itens[c] = 'Descrição'; alvos_itens.add('Descrição')
                    elif 'LINHA' in c and 'Linhas' not in alvos_itens: map_itens[c] = 'Linhas'; alvos_itens.add('Linhas')
                    elif 'CATEGORIA' in c and 'Categoria' not in alvos_itens: map_itens[c] = 'Categoria'; alvos_itens.add('Categoria')
                    elif ('PEÇA' in c or 'PECA' in c or 'QTCOMP' in c) and 'Qtd Peças' not in alvos_itens: map_itens[c] = 'Qtd Peças'; alvos_itens.add('Qtd Peças')
                
                df_itens_1p = df_itens_1p.rename(columns=map_itens)
        except: pass 

        try:
            ws_itens_full = planilha_principal.worksheet("Item Agenda Seller")
            dados_itens_full = ws_itens_full.get_all_values()
            if dados_itens_full and len(dados_itens_full) > 1:
                df_itens_full = pd.DataFrame(dados_itens_full[1:], columns=dados_itens_full[0])
                df_itens_full = df_itens_full.loc[:, ~df_itens_full.columns.duplicated()]
                df_itens_full.columns = df_itens_full.columns.str.strip().str.upper()
                
                map_full = {
                    'CODAGENDA': 'Agenda',
                    'ITEM': 'SKU',
                    'DESCRIÇÃO SKU': 'Descrição',
                    'LINHA': 'Linhas',
                    'ITEMS.LIST.ELEMENT.CATEGORY.FAMILY.NAME': 'Categoria',
                    'QTAGENDA': 'Qtd Peças'
                }
                df_itens_full = df_itens_full.rename(columns=lambda x: map_full.get(x, x))
        except: pass

        df_itens = pd.concat([df_itens_1p, df_itens_full], ignore_index=True)
        if not df_itens.empty and 'Agenda' in df_itens.columns:
            df_itens['Agenda'] = df_itens['Agenda'].astype(str).str.split('.').str[0].str.strip()

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
        # 4. PLANILHA DE TRANSFERÊNCIAS (LENDO A COLUNA V - POSIÇÃO 21)
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
                
                if df_transf.shape[1] >= 22:
                    col_v_nome = df_transf.columns[21]
                    df_transf['DATA_FILTRO'] = pd.to_datetime(df_transf[col_v_nome], errors='coerce', dayfirst=True).dt.normalize()
                    df_transf['NOME_COL_V'] = col_v_nome
                else:
                    df_transf['DATA_FILTRO'] = pd.NaT
                    df_transf['NOME_COL_V'] = 'DATA_FILTRO'
        except Exception as e:
            pass 

    except Exception as e: 
        st.error(f"🚨 Erro crítico de conexão com o Banco de Dados do Google: {e}")
        
    return df, df_itens, df_plan, df_transf, df_excecoes

df, df_itens, df_plan, df_transf, df_excecoes = carregar_dados()

if df.empty and df_transf.empty:
    st.warning("⏳ Aguardando dados das planilhas para renderizar o Dashboard.")
    st.stop()

# --- BARRA LATERAL E NAVEGAÇÃO ---
st.sidebar.image("https://magalog.com.br/opengraph-image.jpg?fdd536e7d35ec9da", width=300)
st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.header("📍 Menu de Navegação")
pagina = st.sidebar.radio("Ir para:", ["🏠 Painel Operacional", "📅 Previsão de Agendas", "📈 Simulador Cenário", "👷 Simulador Mão de Obra", "🧩 Planejamento Lego", "🚛 Transferências", "📝 Solicitações Extras"])
st.sidebar.markdown("---")

if st.sidebar.button("🔄 Atualizar Dados Agora", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.header("📅 Período de Análise")

hoje = pd.Timestamp.now(tz='America/Sao_Paulo').date()
primeiro_dia_mes = hoje.replace(day=1)

if hoje.month == 12:
    ultimo_dia_mes = hoje.replace(day=31)
else:
    ultimo_dia_mes = (hoje.replace(month=hoje.month+1, day=1) - pd.Timedelta(days=1))

datas_selecionadas = st.sidebar.date_input(
    "Selecione o Início e o Fim:", 
    value=(primeiro_dia_mes, ultimo_dia_mes), 
    format="DD/MM/YYYY"
)

if len(datas_selecionadas) == 2: data_inicio, data_fim = datas_selecionadas
else: data_inicio = data_fim = datas_selecionadas[0]

ts_inicio = pd.to_datetime(data_inicio)
ts_fim = pd.to_datetime(data_fim)

# ==============================================================================
# PÁGINA 1: PAINEL OPERACIONAL
# ==============================================================================
if pagina == "🏠 Painel Operacional":
    df_filtrado = df[(df['Data'] >= ts_inicio) & (df['Data'] <= ts_fim)]
    
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Parâmetros Operacionais")
    capacidade_diaria = st.sidebar.number_input("Equipes Disponíveis/Dia", min_value=1, max_value=30, value=6)
    pessoas_por_equipe = st.sidebar.number_input("Pessoas por Equipe", min_value=1, max_value=20, value=6)
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
            fig_1p = px.bar(df_limite_1p, x='Data', y='Agendas_Validas', text='Agendas_Validas', color='Estourou_Limite', color_discrete_map={False: '#3498DB', True: '#E74C3C'}, labels={'Agendas_Validas': 'Agendas', 'Estourou_Limite': 'Acima do Limite?'}, title="Veiculos agendados (1P)")
            fig_1p.add_hline(y=limite_agendas_1p, line_dash="solid", line_width=3, line_color="#E74C3C", annotation_text=f"Capacidade: {limite_agendas_1p}")
            fig_1p.update_traces(textposition='outside')
            fig_1p = aplicar_estilo_premium(fig_1p) # <- ESTILO APLICADO AQUI
            st.plotly_chart(fig_1p, use_container_width=True)
            
            if not df_excecoes.empty and 'Data da Vaga' in df_excecoes.columns:
                df_ex_filtro = df_excecoes[(df_excecoes['Data da Vaga'] >= ts_inicio) & (df_excecoes['Data da Vaga'] <= ts_fim)].copy()
                if not df_ex_filtro.empty:
                    df_ex_filtro['Data da Vaga'] = df_ex_filtro['Data da Vaga'].dt.strftime('%d/%m/%Y')
                    with st.expander("💡 Visualizar Justificativas de Vagas Extras no Período", expanded=False):
                        colunas_desejadas = ['Data da Vaga', 'Fornecedor', 'Solicitante', 'Qtd Peças', 'Qtd SKUs']
                        colunas_existentes = [c for c in colunas_desejadas if c in df_ex_filtro.columns]
                        st.dataframe(df_ex_filtro[colunas_existentes], use_container_width=True, hide_index=True)

        with col_1p_2:
            st.subheader("Balanço 1P")
            exibir_kpi("Dias Acima do Limite", df_limite_1p['Estourou_Limite'].sum(), "Necessita adequação", "#E74C3C")
            exibir_kpi("Volume 1P", df_limite_1p['Total_1P'].sum(), "Total de agendas 1P", "#3498DB")
            exibir_kpi("Isentos (Cofres)", df_limite_1p['Qtd_Cofres'].sum(), "Não consomem doca padrão", "#95A5A6")
    else: st.info("Nenhuma agenda do canal 1P Fornecedor encontrada.")

    # ====================================================================
    # NOVA VISÃO: PLANEJAMENTO LEGO LADO A LADO COM 1P
    # ====================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("🧩 Planejamento Lego: Vagas Liberadas Lego")
    
    if not df_plan.empty:
        # Filtra a base do Lego pelas mesmas datas do filtro lateral
        df_plan_1p = df_plan[(df_plan['data'] >= ts_inicio) & (df_plan['data'] <= ts_fim)].copy()
        
        if not df_plan_1p.empty:
            # Aplica a mesma regra de isenção (Cofres não gastam doca)
            df_plan_1p['Vagas_Validas'] = df_plan_1p.apply(lambda x: x['quantidade_planejado'] if 'COFRE' not in str(x['categoria']).upper() else 0, axis=1)
            df_plan_1p['Vagas_Isentas'] = df_plan_1p.apply(lambda x: x['quantidade_planejado'] if 'COFRE' in str(x['categoria']).upper() else 0, axis=1)
            
            # Agrupa os volumes por dia
            df_limite_lego = df_plan_1p.groupby('data').agg(
                Total_Planejado=('quantidade_planejado', 'sum'),
                Vagas_Validas=('Vagas_Validas', 'sum'),
                Vagas_Isentas=('Vagas_Isentas', 'sum')
            ).reset_index()
            
            df_limite_lego['Estourou_Limite'] = df_limite_lego['Vagas_Validas'] > limite_agendas_1p
            
            col_lg1, col_lg2 = st.columns([2, 1])
            with col_lg1:
                fig_lego = px.bar(
                    df_limite_lego, x='data', y='Vagas_Validas', text='Vagas_Validas', 
                    color='Estourou_Limite', color_discrete_map={False: '#3498DB', True: '#E74C3C'}, 
                    labels={'Vagas_Validas': 'Vagas Liberadas', 'Estourou_Limite': 'Acima do Limite?'}, 
                    title="Vagas Planejadas no Lego (1P)"
                )
                fig_lego.add_hline(y=limite_agendas_1p, line_dash="solid", line_width=3, line_color="#E74C3C", annotation_text=f"Capacidade: {limite_agendas_1p}")
                fig_lego.update_traces(textposition='outside')
                fig_lego.update_layout(xaxis=dict(tickformat="%d/%m/%Y"), showlegend=False)
                fig_lego = aplicar_estilo_premium(fig_lego)
                st.plotly_chart(fig_lego, use_container_width=True)
                
            with col_lg2:
                st.subheader("Balanço Lego (Planejado)")
                exibir_kpi("Dias Estourados (Lego)", df_limite_lego['Estourou_Limite'].sum(), "Dias acima do plano", "#E74C3C")
                exibir_kpi("Volume Planejado", df_limite_lego['Total_Planejado'].sum(), "Total vagas liberadas", "#3498DB")
                exibir_kpi("Isentos (Cofres)", df_limite_lego['Vagas_Isentas'].sum(), "Não entra na capacidade Carros", "#95A5A6")
        else:
            st.info("Nenhuma vaga liberada no Lego para o período filtrado.")
    else:
        st.info("Aba de planejamento Lego vazia ou indisponível.")

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
    df_apc['Custo_HE'] = df_apc['Horas_Extras'] * pessoas_por_equipe * custo_hora_extra

    if not df_apc.empty:
        st.markdown("### 📊 Visão Acumulada")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1: exibir_kpi("Média Equipes/Dia", math.ceil(df_apc['Equipes Necessárias'].mean()), "Recurso Humano", "#3498DB")
        with col_m2: exibir_kpi("Dias em Sobrecarga", len(df_apc[df_apc['Gap_Equipes'] > 0]), f"De {len(df_apc)} analisados", "#E74C3C")
        with col_m3: exibir_kpi("Déficit Projetado", f"{df_apc['Horas_Extras'].sum()} h", f"Custo HE: {formatar_moeda(df_apc['Custo_HE'].sum())}", "#E74C3C")
        with col_m4: exibir_kpi("Agendas Expostas", df_filtrado_op[df_filtrado_op['Data'].isin(df_apc[df_apc['Gap_Equipes'] > 0]['Data'])]['Agenda_Texto'].nunique(), "Cargas com risco", "#F39C12")
        
        fig_equipes = px.bar(df_apc, x='Data', y='Equipes Necessárias', text='Equipes Necessárias', color_discrete_sequence=['#3498DB'], title="Necessidade Diária de Mão de Obra")
        fig_equipes.add_hline(y=capacidade_diaria, line_dash="solid", line_width=3, line_color="#E74C3C", annotation_text=f"Headcount Fixo ({capacidade_diaria})")
        fig_equipes.update_traces(textposition='outside')
        fig_equipes = aplicar_estilo_premium(fig_equipes) # <- ESTILO APLICADO AQUI
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
            fig_canais = px.pie(df_dia_critico.groupby('Canal')['Tempo_APC_Minutos'].sum().reset_index(), values='Tempo_APC_Minutos', names='Canal', hole=0.5, color_discrete_map={'Fulfillment': '#3498DB', '1P Fornecedor': '#F39C12'}, title="Distribuição por Canal")
            fig_canais.update_traces(textposition='inside', textinfo='percent+label')
            fig_canais = aplicar_estilo_premium(fig_canais) # <- ESTILO APLICADO AQUI
            fig_canais.update_layout(showlegend=False)
            st.plotly_chart(fig_canais, use_container_width=True)
            
        with col_tab:
            st.markdown("**Cargas do Dia (👇 Clique em uma linha para inspecionar)**")
            df_tabela_dia = df_dia_critico[['Status', 'Canal', 'Linhas', 'Agenda_Texto', 'Fornecedor', 'Qtd Peças', 'Tempo_APC_Minutos']].rename(columns={'Agenda_Texto': 'Agenda', 'Tempo_APC_Minutos': 'APC (Min)'}).sort_values(by='APC (Min)', ascending=False).reset_index(drop=True)
            
            evento_agenda = st.dataframe(
                df_tabela_dia, 
                use_container_width=True, 
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )

        st.markdown("### 📦 Detalhamento da Carga")
        linhas_sel = evento_agenda.selection.rows
        
        if linhas_sel:
            indice_agenda = linhas_sel[0]
            agenda_selecionada = df_tabela_dia.iloc[indice_agenda]['Agenda']
            
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
                    df_fornecedor_temp = df_tabela_dia[df_tabela_dia['Agenda'] == agenda_selecionada]
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
        else:
            st.info("👆 Selecione uma carga na tabela acima para ver os produtos dela.")
            
    else: st.success("✅ A operação fluiu sem gargalos no período analisado!")

# ==============================================================================
# PÁGINA 2: PREVISÃO DE AGENDAS (CENÁRIO SÊNIOR)
# ==============================================================================
elif pagina == "📅 Previsão de Agendas":
    st.title("📅 Previsão de Agendas | Visão Estratégica")
    st.markdown(f"**Projeção de Cenário para o período:** {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    
    df_filtrado_prev = df[(df['Data'] >= ts_inicio) & (df['Data'] <= ts_fim)].copy() if not df.empty else pd.DataFrame()
    
    df_1p_prev = df_filtrado_prev[df_filtrado_prev['Canal'] == '1P Fornecedor'] if not df_filtrado_prev.empty else pd.DataFrame()
    df_full_prev = df_filtrado_prev[df_filtrado_prev['Canal'] == 'Fulfillment'] if not df_filtrado_prev.empty else pd.DataFrame()

    df_transf_prev = pd.DataFrame()
    if not df_transf.empty and 'DATA_FILTRO' in df_transf.columns:
        df_transf_prev = df_transf[(df_transf['DATA_FILTRO'] >= ts_inicio) & (df_transf['DATA_FILTRO'] <= ts_fim)].copy()
    
    agendas_1p = df_1p_prev['Agenda_Texto'].nunique() if not df_1p_prev.empty else 0
    agendas_full = df_full_prev['Agenda_Texto'].nunique() if not df_full_prev.empty else 0
    cargas_transf = df_transf_prev['ID_CARGA_PCP'].nunique() if not df_transf_prev.empty and 'ID_CARGA_PCP' in df_transf_prev.columns else 0
    
    pecas_1p = df_1p_prev['Qtd Peças'].sum() if not df_1p_prev.empty else 0
    pecas_full = df_full_prev['Qtd Peças'].sum() if not df_full_prev.empty else 0
    pecas_transf = df_transf_prev['QTDE'].sum() if not df_transf_prev.empty and 'QTDE' in df_transf_prev.columns else 0
    
    min_op = df_filtrado_prev['Tempo_APC_Minutos'].sum() if not df_filtrado_prev.empty else 0
    min_fixo = 1200 if pd.to_datetime(data_inicio).weekday() < 5 else 0 
    eq_projetadas = math.ceil((min_op + min_fixo) / 427)

    st.markdown("### 📊 Resumo Executivo")
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1: exibir_kpi("Equipes APC Necessárias", eq_projetadas, "Headcount projetado", "#E74C3C")
    with col_k2: exibir_kpi("Total de Veículos", agendas_1p + agendas_full + cargas_transf, "Agendas + Transferências", "#34495E")
    with col_k3: exibir_kpi("Volume Físico Estimado", f"{(pecas_1p + pecas_full + pecas_transf):,.0f}".replace(',', '.'), "Peças Totais", "#9B59B6")
    with col_k4: exibir_kpi("Agendas 1P", agendas_1p, "Fornecedor Tradicional", "#0086FF")

    df_macro = pd.DataFrame({
        'Canal': ['1P Fornecedor', 'Fulfillment', 'Transferência'],
        'Veiculos': [agendas_1p, agendas_full, cargas_transf],
        'Pecas': [pecas_1p, pecas_full, pecas_transf]
    })

    col_g1, col_g2 = st.columns(2)
    cores_canais = {'1P Fornecedor': '#0086FF', 'Fulfillment': '#F39C12', 'Transferência': '#9B59B6'}
    
    with col_g1:
        fig_v = px.pie(df_macro, values='Veiculos', names='Canal', title='Distribuição de Doca (Veículos)', hole=0.5, color='Canal', color_discrete_map=cores_canais)
        fig_v.update_traces(textposition='inside', textinfo='percent+label')
        fig_v = aplicar_estilo_premium(fig_v) # <- ESTILO APLICADO AQUI
        fig_v.update_layout(showlegend=False)
        st.plotly_chart(fig_v, use_container_width=True)

    with col_g2:
        fig_p = px.pie(df_macro, values='Pecas', names='Canal', title='Composição de Volume Físico (Peças)', hole=0.5, color='Canal', color_discrete_map=cores_canais)
        fig_p.update_traces(textposition='inside', textinfo='percent+label')
        fig_p = aplicar_estilo_premium(fig_p) # <- ESTILO APLICADO AQUI
        fig_p.update_layout(showlegend=False)
        st.plotly_chart(fig_p, use_container_width=True)

    st.markdown("---")

    st.markdown("### 🔍 Drill-Down por Canal Operacional")
    tab_1p, tab_full, tab_transf = st.tabs(["📦 1P Fornecedor", "🛍️ Seller / Fulfillment", "🚛 Malha / Transferências"])

    def renderizar_detalhe(df_dados, cor_hex, nome_canal):
        if df_dados.empty:
            st.info(f"Nenhum dado de {nome_canal} previsto para esta data.")
            return
        
        c1, c2 = st.columns([1, 2])
        df_linha = df_dados.groupby('Linhas').agg(Agendas=('Agenda_Texto', 'nunique'), Peças=('Qtd Peças', 'sum')).reset_index().sort_values(by='Peças', ascending=False).head(8)
        
        with c1:
            st.markdown(f"**Top Categorias ({nome_canal})**")
            fig_bar = px.bar(df_linha, x='Peças', y='Linhas', orientation='h', text='Peças', color_discrete_sequence=[cor_hex])
            fig_bar.update_traces(textposition='outside')
            fig_bar = aplicar_estilo_premium(fig_bar) # <- ESTILO APLICADO AQUI
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0), xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with c2:
            st.markdown(f"**Painel de Fornecedores ({nome_canal})**")
            df_forn = df_dados.groupby('Fornecedor').agg(Agendas=('Agenda_Texto', 'nunique'), SKUs=('Qtd SKUs', 'sum'), Peças=('Qtd Peças', 'sum')).reset_index().sort_values(by='Peças', ascending=False)
            max_p = float(df_forn['Peças'].max()) if not df_forn.empty else 100.0
            
            st.dataframe(
                df_forn, use_container_width=True, hide_index=True, height=350,
                column_config={
                    "Peças": st.column_config.ProgressColumn("Volume Físico (Peças)", format="%.0f", min_value=0, max_value=max_p),
                    "Fornecedor": st.column_config.TextColumn("Nome do Fornecedor / Parceiro")
                }
            )

    with tab_1p:
        renderizar_detalhe(df_1p_prev, '#0086FF', '1P')

    with tab_full:
        renderizar_detalhe(df_full_prev, '#F39C12', 'Fulfillment')

    with tab_transf:
        if df_transf_prev.empty or 'ID_CARGA_PCP' not in df_transf_prev.columns:
            st.info("Nenhuma Transferência prevista para esta data.")
        else:
            c_t1, c_t2 = st.columns([1, 2])
            
            df_modal = df_transf_prev.groupby('MODAL2').agg(Peças=('QTDE', 'sum')).reset_index().sort_values(by='Peças', ascending=False)
            with c_t1:
                st.markdown("**Volume por Modalidade**")
                fig_t = px.bar(df_modal, x='Peças', y='MODAL2', orientation='h', text='Peças', color_discrete_sequence=['#9B59B6'])
                fig_t.update_traces(textposition='outside')
                fig_t = aplicar_estilo_premium(fig_t) # <- ESTILO APLICADO AQUI
                fig_t.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0), xaxis_title="", yaxis_title="")
                st.plotly_chart(fig_t, use_container_width=True)
            
            with c_t2:
                st.markdown("**Relação de Cargas Programadas**")
                df_id = df_transf_prev.groupby('ID_CARGA_PCP').agg(
                    CD_Origem=('CD_EMPRESA', 'first') if 'CD_EMPRESA' in df_transf_prev.columns else ('ID_CARGA_PCP', 'first'),
                    Modalidade=('MODAL2', 'first') if 'MODAL2' in df_transf_prev.columns else ('ID_CARGA_PCP', 'first'),
                    Peças=('QTDE', 'sum')
                ).reset_index().sort_values(by='Peças', ascending=False)
                
                df_id['CD_Origem'] = 'CD ' + df_id['CD_Origem'].astype(str)
                max_t = float(df_id['Peças'].max()) if not df_id.empty else 100.0
                
                st.dataframe(
                    df_id.rename(columns={'ID_CARGA_PCP': 'ID Carga'}),
                    use_container_width=True, hide_index=True, height=350,
                    column_config={"Peças": st.column_config.ProgressColumn("Volume Físico (Peças)", format="%.0f", min_value=0, max_value=max_t)}
                )

# ==============================================================================
# NOVA PÁGINA: Simulador Cenário (ESTRESSE DE MALHA CONTÍNUO)
# ==============================================================================
elif pagina == "📈 Simulador Cenário":
    col_titulo, col_reset = st.columns([4, 1])
    with col_titulo:
        st.title("📈 Simulador Cenário ")
        st.markdown("Adicione novas cargas em múltiplos dias e veja o impacto cumulativo na semana inteira. O sistema **salva as suas adições** enquanto você navega pelas datas!")
    
    # --- INICIALIZA A MEMÓRIA PERSISTENTE DO ROBO ---
    if 'simulador_cargas' not in st.session_state:
        st.session_state['simulador_cargas'] = {}

    with col_reset:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Limpar Simulação", use_container_width=True):
            st.session_state['simulador_cargas'] = {} # Apaga a memória
            st.rerun()

    # 1. Prepara a Base Real
    df_base_periodo = df[(df['Data'] >= ts_inicio) & (df['Data'] <= ts_fim)].copy()
    
    if not df_base_periodo.empty:
        st.markdown("---")
        st.markdown("### 🎛️ Filtro de Cenário Base")
        canais_disponiveis = df_base_periodo['Canal'].unique().tolist()
        
        canais_selecionados = st.multiselect(
            "Selecione quais canais você quer manter no cálculo ANTES de simular o estresse:", 
            options=canais_disponiveis, 
            default=canais_disponiveis
        )
        
        df_filtrado_sim = df_base_periodo[df_base_periodo['Canal'].isin(canais_selecionados)]
        
        # Base de datas para não sumir o gráfico se tirar os filtros
        df_apc_base = df_base_periodo[['Data']].drop_duplicates()
        
        if not df_filtrado_sim.empty:
            df_agg = df_filtrado_sim.groupby('Data').agg({'Tempo_APC_Minutos': 'sum', 'Agenda_Texto': 'nunique'}).reset_index()
            df_apc_base = pd.merge(df_apc_base, df_agg, on='Data', how='left').fillna(0)
        else:
            df_apc_base['Tempo_APC_Minutos'] = 0
            df_apc_base['Agenda_Texto'] = 0
            
        # Adiciona a Transferência Fixa
        df_apc_base['Min_Transf_Fixa'] = df_apc_base['Data'].apply(lambda x: 1200 if x.weekday() < 5 else 0)
        df_apc_base['Minutos_Originais'] = df_apc_base['Tempo_APC_Minutos'] + df_apc_base['Min_Transf_Fixa']
        df_apc_base['Equipes_Originais'] = df_apc_base['Minutos_Originais'].apply(lambda x: math.ceil(x / 427))
        df_apc_base['Data_Str'] = df_apc_base['Data'].dt.strftime('%d/%m/%Y')
        
        st.markdown("---")
        
        # 2. Painel de Injeção de Carga
        col_painel, col_resumo = st.columns([2, 1])
        
        with col_painel:
            st.markdown("### 🧪 Injetar Cargas por Dia")
            dia_alvo = st.selectbox("Selecione o Dia para adicionar as cargas:", df_apc_base['Data_Str'].tolist())
            
            # Resgata os números que o usuário já tinha salvo para este dia
            if dia_alvo not in st.session_state['simulador_cargas']:
                st.session_state['simulador_cargas'][dia_alvo] = {'mad': 0, 'ele': 0, 'pne': 0, 'mer': 0, 'cof': 0, 'div': 0}
            
            sim_dia = st.session_state['simulador_cargas'][dia_alvo]
            
            c_in1, c_in2, c_in3 = st.columns(3)
            with c_in1:
                val_mad = st.number_input("🪵 Madeira (+427m)", 0, 50, sim_dia['mad'])
                val_ele = st.number_input("📺 Eletro (+95m)", 0, 50, sim_dia['ele'])
            with c_in2:
                val_pne = st.number_input("🛞 Pneus (+240m)", 0, 50, sim_dia['pne'])
                val_mer = st.number_input("🛒 Mercado (+150m)", 0, 50, sim_dia['mer'])
            with c_in3:
                val_cof = st.number_input("🔒 Cofre/Img (+90m)", 0, 50, sim_dia['cof'])
                val_div = st.number_input("📦 Div/Full (+60m)", 0, 100, sim_dia['div'])
                
            # Salva imediatamente de volta na memória
            st.session_state['simulador_cargas'][dia_alvo] = {
                'mad': val_mad, 'ele': val_ele, 'pne': val_pne, 'mer': val_mer, 'cof': val_cof, 'div': val_div
            }

        # 3. Lógica de Simulação Cumulativa (A MÁGICA ACONTECE AQUI)
        df_apc_simulado = df_apc_base.copy()
        df_apc_simulado['Minutos_Simulados'] = df_apc_simulado['Minutos_Originais']
        df_apc_simulado['Cenario'] = 'Real Base'
        
        # O robô varre a memória e injeta os carros em TODOS os dias que você mexeu
        for d_str, injecoes in st.session_state['simulador_cargas'].items():
            min_add = (injecoes['mad'] * 427) + (injecoes['ele'] * 95) + (injecoes['pne'] * 240) + (injecoes['mer'] * 150) + (injecoes['cof'] * 90) + (injecoes['div'] * 60)
            if min_add > 0:
                idx = df_apc_simulado['Data_Str'] == d_str
                df_apc_simulado.loc[idx, 'Minutos_Simulados'] += min_add
                df_apc_simulado.loc[idx, 'Cenario'] = 'Simulado'
                
        # Recalcula a quantidade de equipes finais para cada dia
        df_apc_simulado['Equipes_Simuladas'] = df_apc_simulado['Minutos_Simulados'].apply(lambda x: math.ceil(x / 427))
        
        # 4. Resultado Específico do Dia Selecionado na Tela
        with col_resumo:
            st.markdown(f"### 🎯 Impacto no dia {dia_alvo}")
            linha_alvo = df_apc_simulado[df_apc_simulado['Data_Str'] == dia_alvo].iloc[0]
            
            min_injetados_hoje = linha_alvo['Minutos_Simulados'] - linha_alvo['Minutos_Originais']
            eq_originais = linha_alvo['Equipes_Originais']
            eq_simuladas = linha_alvo['Equipes_Simuladas']
            delta_eq = eq_simuladas - eq_originais
            
            if min_injetados_hoje == 0:
                st.info("Nenhuma carga extra salva para este dia. Reflete a base atual.")
            else:
                cor_alerta = "#E74C3C" if delta_eq > 0 else "#2ECC71"
                txt_alerta = f"🚨 Requer +{int(delta_eq)} Equipe(s) extra" if delta_eq > 0 else "✅ Absorvido pela ociosidade"
                
                exibir_kpi("Novo Headcount Necessário", int(eq_simuladas), txt_alerta, cor_alerta)
                exibir_kpi("Carga Horária Total", f"{linha_alvo['Minutos_Simulados']:,.0f} min", f"+{min_injetados_hoje} min adicionados", "#F39C12")

        st.markdown("---")
        st.markdown("### 📈 Projeção da Semana (Com todos os dias simulados)")
        
        # Gráfico mostra a semana toda com as barras vermelhas onde houve injeção
        fig_sim = px.bar(
            df_apc_simulado.sort_values(by='Data'), 
            x='Data', 
            y='Equipes_Simuladas', 
            text='Equipes_Simuladas', 
            color='Cenario',
            color_discrete_map={'Real Base': '#3498DB', 'Simulado': '#E74C3C'},
            title="Evolução de Mão de Obra Necessária"
        )
        fig_sim.update_traces(textposition='outside')
        fig_sim.update_layout(xaxis=dict(tickformat="%d/%m/%Y"))
        fig_sim = aplicar_estilo_premium(fig_sim)
        
        col_graf_esq, col_graf_dir = st.columns([5, 1])
        with col_graf_esq:
            st.plotly_chart(fig_sim, use_container_width=True)
            
    else:
        st.warning("Não há dados carregados para gerar a simulação no período selecionado.")

# ==============================================================================
# PÁGINA 3: PROVA DE SOBRECARGA (COMERCIAL)
# ==============================================================================
elif pagina == "👷 Simulador Mão de Obra":
    st.title("⚖️ Análise de Mão de obra")
    st.markdown("Esta visão simula o cenário do dia selecionado, balanceando as cargas de acordo com a quantidade de equipes disponíveis.")
    
    dias_disponiveis = sorted(df[df['Data'].notna()]['Data'].dt.strftime('%d/%m/%Y').unique())
    
    if dias_disponiveis:
        st.sidebar.markdown("---")
        st.sidebar.header("⚙️ Parâmetros da Simulação")
        dia_simulacao = st.sidebar.selectbox("Escolha um dia para balancear as cargas:", dias_disponiveis)
        
        total_equipes = st.sidebar.number_input("Total de Equipes Disponíveis", min_value=1, max_value=20, value=6)
        eq_transf = st.sidebar.number_input("Equipes focadas em Transferência", min_value=0, max_value=total_equipes, value=min(3, total_equipes))
        max_madeira = max(0, total_equipes - eq_transf) 
        eq_madeira = st.sidebar.number_input("Equipes focadas em Madeira", min_value=0, max_value=max_madeira, value=min(2, max_madeira))
        
        df_simulacao = df[df['Data'].dt.strftime('%d/%m/%Y') == dia_simulacao].copy()
        
        tempo_equipes = {i: 0 for i in range(1, total_equipes + 1)}
        
        def nomear_equipe(i):
            if i <= eq_transf: return f'Eq. {i} 👷 (Transf)'
            elif i <= eq_transf + eq_madeira: return f'Eq. {i} 👷 (Madeira)'
            else: return f'Eq. {i} 👷 Misto'
            
        nomes_equipes = {i: nomear_equipe(i) for i in range(1, total_equipes + 1)}
        
        cargas_alocadas = []
        data_obj = pd.to_datetime(dia_simulacao, format='%d/%m/%Y')
        
        eq_disponiveis_transf = list(range(1, eq_transf + 1)) if eq_transf > 0 else list(tempo_equipes.keys())
        
        if data_obj.weekday() < 5:
            for i in range(5):
                eq_num = min(eq_disponiveis_transf, key=lambda k: tempo_equipes[k])
                tempo_equipes[eq_num] += 240
                cargas_alocadas.append({
                    'Equipe': nomes_equipes[eq_num],
                    'Tipo Carga': 'Transferência Fixa (240m)',
                    'Minutos': 240,
                    'Detalhe': f'Transf CD Origem {i+1}'
                })
        
        cargas_madeira_lista = []
        cargas_restante = []
        for _, row in df_simulacao.iterrows():
            minutos = row['Tempo_APC_Minutos']
            linhas = str(row['Linhas']).upper()
            forn = str(row['Fornecedor']).strip().title()
            tipo = 'Carga Fulfillment' if row['Canal'] == 'Fulfillment' else 'Carga 1P/Misto'
            
            if 'MADEIRA' in linhas and row.get('Pecas_Madeira', 0) > 10:
                cargas_madeira_lista.append((minutos, 'Carga Madeira', f'Madeira: {forn[:15]}'))
            else:
                cargas_restante.append((minutos, tipo, forn[:15]))
                
        cargas_madeira_lista.sort(key=lambda x: x[0], reverse=True)
        cargas_restante.sort(key=lambda x: x[0], reverse=True)
        
        inicio_madeira = eq_transf + 1
        fim_madeira = eq_transf + eq_madeira
        eq_disponiveis_madeira = list(range(inicio_madeira, fim_madeira + 1)) if eq_madeira > 0 else list(tempo_equipes.keys())
        
        for min_val, tipo, det in cargas_madeira_lista:
            eq_num = min(eq_disponiveis_madeira, key=lambda k: tempo_equipes[k])
            tempo_equipes[eq_num] += min_val
            cargas_alocadas.append({
                'Equipe': nomes_equipes[eq_num],
                'Tipo Carga': tipo,
                'Minutos': min_val,
                'Detalhe': det
            })
            
        for min_val, tipo, det in cargas_restante:
            eq_num = min(tempo_equipes.keys(), key=lambda k: tempo_equipes[k])
            tempo_equipes[eq_num] += min_val
            cargas_alocadas.append({
                'Equipe': nomes_equipes[eq_num],
                'Tipo Carga': tipo,
                'Minutos': min_val,
                'Detalhe': det
            })
            
        df_mochila = pd.DataFrame(cargas_alocadas)
        
        if not df_mochila.empty:
            df_mochila['Ordem'] = df_mochila['Equipe'].str.extract(r'(\d+)').astype(int)
            df_mochila = df_mochila.sort_values(by="Ordem")
            
            minutos_totais = sum(tempo_equipes.values())
            capacidade_total_cd = total_equipes * 427
            equipes_estouradas = sum(1 for v in tempo_equipes.values() if v > 427)
            
            st.markdown("---")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1: exibir_kpi("Equipes em Sobrecarga", f"{equipes_estouradas} de {total_equipes}", "Mesmo equalizando 100%", "#E74C3C")
            with col_s2: exibir_kpi("Demanda Exigida no Dia", f"{int(minutos_totais)} min", f"Capacidade Real: {capacidade_total_cd} min", "#9B59B6")
            
            saldo = minutos_totais - capacidade_total_cd
            if saldo > 0:
                with col_s3: exibir_kpi("Déficit Inevitável", f"+{int(saldo)} min", "Tempo faltante", "#E74C3C")
            else:
                with col_s3: exibir_kpi("Déficit Inevitável", "0 min", "Operação dentro do limite", "#2ECC71")

            fig_mochila = px.bar(
                df_mochila, x='Equipe', y='Minutos', color='Tipo Carga', text='Detalhe',
                title=f"Balanceamento Dinâmico de Cargas - Dia {dia_simulacao}",
                color_discrete_map={
                    'Transferência Fixa (240m)': '#8E44AD', 'Carga Madeira': '#E67E22', 
                    'Carga Fulfillment': '#3498DB', 'Carga 1P/Misto': '#2ECC71'
                }
            )
            
            fig_mochila.add_hline(y=427, line_dash="solid", line_width=3, line_color="#E74C3C", annotation_text="Capacidade Máxima do Turno (427 min)", annotation_position="top left", annotation_font_color="#E74C3C")
            fig_mochila.update_traces(textposition='inside', insidetextanchor='middle')
            fig_mochila = aplicar_estilo_premium(fig_mochila)
            
            # --- AJUSTE DE DIMENSÕES ---
            fig_mochila.update_layout(
                height=800,       # Mantém a altura que ficou excelente
                bargap=0.15       # Espaço menor entre as barras (deixa elas mais gordinhas)
            )
            
            # Tiramos as margens laterais! Agora ele vai ocupar 100% da tela e respirar melhor
            st.plotly_chart(fig_mochila, use_container_width=True)
            
        else:
            st.warning("Nenhuma carga encontrada para o dia selecionado.")
    else:
        st.warning("Não há dados carregados para gerar a simulação.")

# ==============================================================================
# PÁGINA 4: MATRIZ DE PLANEJAMENTO (S&OP COMERCIAL)
# ==============================================================================
elif pagina == "🧩 Planejamento Lego":
    st.title("🧩 Visão planejamento capacidade LEGO")

    df_plan_filtrado = df_plan[(df_plan['data'] >= ts_inicio) & (df_plan['data'] <= ts_fim)].copy() if not df_plan.empty else pd.DataFrame()

    if not df_plan.empty:
        st.markdown("### 🎯 Planejamento Mensal do Comercial")
        st.write("Digite as vagas aprovadas (LEGO) e clique em Salvar. O sistema gravará na Nuvem (Google Sheets).")
        
        categorias_existentes = sorted([c for c in df_plan['categoria'].unique() if pd.notna(c) and str(c).strip() != ''])
        df_base_categorias = pd.DataFrame({'CATEGORIA': categorias_existentes})
        
        try:
            cliente_google = conectar_google()
            planilha_principal = cliente_google.open_by_key('1WA5GjT1f-jpQ4Sw_OfvXBERyz5MehfH7uaFrIfUMrtw')
            ws_metas = planilha_principal.worksheet("METAS_LEGO")
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

                    cliente_google = conectar_google()
                    ws_principal = cliente_google.open_by_key('1WA5GjT1f-jpQ4Sw_OfvXBERyz5MehfH7uaFrIfUMrtw')
                    try: ws_metas = ws_principal.worksheet("METAS_LEGO")
                    except: ws_metas = ws_principal.add_worksheet(title="METAS_LEGO", rows="100", cols="2")
                        
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
        with col_e1: exibir_kpi("Meta (LEGO)", f"{meta_total:,.0f}".replace(',', '.'), "Plano do Mês", "#3498DB")
        with col_e2: exibir_kpi("Agendado", f"{realizado_total:,.0f}".replace(',', '.'), "Agendamentos Realizados", "#9B59B6")
        
        cor_saldo = "#2ECC71" if saldo_total >= 0 else "#E74C3C"
        texto_saldo = "Vagas Livres" if saldo_total >= 0 else "Risco Global"
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
        
        st.markdown("### 🧩 Distribução Planejado x Realizado (LEGO)")
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
# PÁGINA 5: HISTÓRICO 325 (TRANSFERÊNCIAS)
# ==============================================================================
elif pagina == "🚛 Transferências" or pagina == "🚛 Histórico325":
    st.title("🚛 Visão de Transferências")
    
    if not df_transf.empty:
        df_transf_periodo = df_transf[(df_transf['DATA_FILTRO'] >= ts_inicio) & (df_transf['DATA_FILTRO'] <= ts_fim)].copy()

        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filtros de Transferência")
        
        opcoes_modal = sorted(df_transf_periodo['MODAL2'].dropna().unique()) if 'MODAL2' in df_transf_periodo.columns else []
        modal_selecionado = st.sidebar.multiselect("Tipo de Carga (Modal)", options=opcoes_modal, default=opcoes_modal)
        
        if 'MODAL2' in df_transf_periodo.columns:
            df_transf_periodo = df_transf_periodo[df_transf_periodo['MODAL2'].isin(modal_selecionado)]

        if 'ID_CARGA_PCP' in df_transf_periodo.columns:
            
            def compor_modalidade(series):
                return ' | '.join(sorted([str(x).strip() for x in series.dropna().unique() if str(x).strip() != '']))

            nome_col_v = df_transf_periodo['NOME_COL_V'].iloc[0] if 'NOME_COL_V' in df_transf_periodo.columns else 'DATA_FILTRO'

            resumo_tabela = df_transf_periodo.groupby('ID_CARGA_PCP').agg(
                DATA_PRODUCAO=('DATA SEPARACAO', 'first') if 'DATA SEPARACAO' in df_transf_periodo.columns else ('DATA_FILTRO', 'first'),
                LIBERACAO=('DATA LIBERAÇÃO', 'first') if 'DATA LIBERAÇÃO' in df_transf_periodo.columns else ('DATA_FILTRO', 'first'),
                CD_ORIGEM=('CD_EMPRESA', 'first') if 'CD_EMPRESA' in df_transf_periodo.columns else ('ID_CARGA_PCP', 'first'),
                DATA_ENTREGA=('DATA ENTREGA CLIENTE', 'first') if 'DATA ENTREGA CLIENTE' in df_transf_periodo.columns else ('DATA_FILTRO', 'first'),
                MODALIDADE=('MODAL2', compor_modalidade) if 'MODAL2' in df_transf_periodo.columns else ('ID_CARGA_PCP', 'first'),
                SKUS=('PRODUTO', 'nunique') if 'PRODUTO' in df_transf_periodo.columns else ('ID_CARGA_PCP', 'nunique'),
                PECAS=('QTDE', 'sum') if 'QTDE' in df_transf_periodo.columns else ('ID_CARGA_PCP', 'count'),
                DATA_CD=(nome_col_v, 'first')
            ).reset_index()

            resumo_tabela['CD_ORIGEM'] = 'CD ' + resumo_tabela['CD_ORIGEM'].astype(str)
            for col in ['DATA_PRODUCAO', 'LIBERACAO', 'DATA_ENTREGA', 'DATA_CD']:
                if col in resumo_tabela.columns:
                    resumo_tabela[col] = pd.to_datetime(resumo_tabela[col], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y').fillna('-')
            
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
            st.caption("👈 Clique em qualquer linha da tabela abaixo para ver os itens da carga.")
            
            evento_tabela = st.dataframe(
                resumo_tabela, 
                use_container_width=True, 
                hide_index=True,
                on_select="rerun", 
                selection_mode="single-row"
            )

            linhas_selecionadas = evento_tabela.selection.rows

            if linhas_selecionadas:
                indice_clicado = linhas_selecionadas[0]
                id_selecionado = resumo_tabela.iloc[indice_clicado]['ID2900 (Carga)']

                st.markdown("---")
                st.markdown(f"### 📦 Inspecionar Itens: Carga {id_selecionado}")
                
                df_detalhe = df_transf_periodo[df_transf_periodo['ID_CARGA_PCP'] == id_selecionado].copy()
                
                if not df_detalhe.empty:
                    desc_col = next((c for c in df_detalhe.columns if 'DESCRI' in c), None)
                    prod_col = next((c for c in df_detalhe.columns if 'PRODUTO' in c or 'SKU' in c), None)
                    qtd_col = next((c for c in df_detalhe.columns if 'QTDE' in c or 'QTD' in c), None)
                    ped_col = next((c for c in df_detalhe.columns if 'PED_ORIGEM' in c), 'NU_PED_ORIGEM')
                    mod_col = next((c for c in df_detalhe.columns if 'MODAL2' in c), 'MODAL2')
                    
                    total_pecas_id = df_detalhe[qtd_col].sum() if qtd_col else 0
                    total_skus_id = df_detalhe[prod_col].nunique() if prod_col else 0
                    
                    col_det1, col_det2 = st.columns(2)
                    with col_det1: exibir_kpi("📦 SKUs Distintos", total_skus_id, "Mix de produtos", "#3498DB")
                    with col_det2: exibir_kpi("🔢 Total de Peças", f"{total_pecas_id:,.0f}".replace(',', '.'), "Volume Físico", "#9B59B6")
                    
                    cols_to_show = []
                    rename_dict = {}
                    
                    if prod_col in df_detalhe.columns: cols_to_show.append(prod_col); rename_dict[prod_col] = 'Produto'
                    if desc_col in df_detalhe.columns: cols_to_show.append(desc_col); rename_dict[desc_col] = 'Descrição'
                    if qtd_col in df_detalhe.columns: cols_to_show.append(qtd_col); rename_dict[qtd_col] = 'Qtd'
                    if ped_col in df_detalhe.columns: cols_to_show.append(ped_col); rename_dict[ped_col] = 'Pedido Origem'
                    if mod_col in df_detalhe.columns: cols_to_show.append(mod_col); rename_dict[mod_col] = 'Modal'
                    
                    if cols_to_show:
                        df_exibir = df_detalhe[cols_to_show].rename(columns=rename_dict)
                        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
                    else:
                        st.warning("Colunas de detalhamento não encontradas na base.")
                else:
                    st.warning("Nenhum detalhe encontrado para esta carga.")
            else:
                st.info("👆 Selecione uma carga na tabela acima para ver os detalhes dos produtos.")

            st.markdown("---")
            st.markdown("### 📈 Análise de Fluxo")
            
            graf_col1, graf_col2 = st.columns([2, 1])
            with graf_col1:
                evolucao = resumo_tabela.groupby('Data Produção')['Peças'].sum().reset_index()
                fig_transf = px.bar(evolucao, x='Data Produção', y='Peças', text='Peças', title="Volume de Peças por Dia", color_discrete_sequence=['#9B59B6'])
                fig_transf.update_traces(textposition='outside')
                fig_transf = aplicar_estilo_premium(fig_transf) # <- ESTILO APLICADO AQUI
                st.plotly_chart(fig_transf, use_container_width=True)
            
            with graf_col2:
                fig_modal = px.pie(resumo_tabela, values='Peças', names='Modalidade', title="Distribuição por Modal", hole=0.4, color_discrete_sequence=px.colors.sequential.Purples_r)
                fig_modal = aplicar_estilo_premium(fig_modal) # <- ESTILO APLICADO AQUI
                st.plotly_chart(fig_modal, use_container_width=True)

        else:
            st.warning("A coluna 'ID_CARGA_PCP' não foi encontrada na planilha de Transferências.")
    else:
        st.warning("⚠️ Planilha de Transferências não carregou. O e-mail do robô está como Leitor nela?")

# ==============================================================================
# PÁGINA 6: REGISTRO DE SOLICITAÇÕES EXTRAS
# ==============================================================================
elif pagina == "📝 Solicitações Extras":
    st.title("📝 Registro de Vagas Extras 1P")
    st.markdown("Utilize este canal para registrar exceções autorizadas pelo Comercial que justifiquem o estouro do Teto Diário de Agendas.")

    st.markdown("### ➕ Nova Solicitação")
    with st.form(key="form_excecao", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            data_vaga = st.date_input("Data autorizada para a vaga", format="DD/MM/YYYY")
            fornecedor_extra = st.text_input("Fornecedor / Transportadora")
            solicitante = st.text_input("Comercial Solicitante (Quem autorizou?)")
        with col_f2:
            qtd_pecas_extra = st.number_input("Quantidade Estimada de Peças", min_value=0, step=1)
            qtd_skus_extra = st.number_input("Quantidade Estimada de SKUs", min_value=0, step=1)
        
        submit_excecao = st.form_submit_button("💾 Salvar Registro")

        if submit_excecao:
            if not fornecedor_extra or not solicitante:
                st.error("⚠️ Por favor, preencha o Fornecedor e o Solicitante.")
            else:
                try:
                    cliente_google = conectar_google()
                    ws_principal = cliente_google.open_by_key('1WA5GjT1f-jpQ4Sw_OfvXBERyz5MehfH7uaFrIfUMrtw')
                    
                    try:
                        ws_excecoes = ws_principal.worksheet("EXCECOES_1P")
                    except:
                        ws_excecoes = ws_principal.add_worksheet(title="EXCECOES_1P", rows="100", cols="6")
                        ws_excecoes.append_row(["Data da Vaga", "Fornecedor", "Solicitante", "Qtd Peças", "Qtd SKUs", "Data do Registro"])
                    
                    ws_excecoes.append_row([
                        data_vaga.strftime("%d/%m/%Y"), 
                        fornecedor_extra.strip().upper(), 
                        solicitante.strip().title(), 
                        int(qtd_pecas_extra), 
                        int(qtd_skus_extra), 
                        pd.Timestamp.now(tz='America/Sao_Paulo').strftime("%d/%m/%Y %H:%M:%S")
                    ])
                    
                    st.success("✅ Vaga extra registrada com sucesso! Ela já justificará o Teto de Agendas no Painel Operacional.")
                except Exception as e:
                    st.error(f"🚨 Erro ao salvar na nuvem: {e}")

    st.markdown("---")
    st.markdown("### 📚 Histórico de Exceções")
    
    if not df_excecoes.empty and 'Data da Vaga' in df_excecoes.columns:
        df_exibir = df_excecoes.copy()
        df_exibir['Data da Vaga'] = df_exibir['Data da Vaga'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma exceção válida registrada ou as colunas não batem com o padrão.")








