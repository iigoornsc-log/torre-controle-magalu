import streamlit as st
import pandas as pd
import plotly.express as px
import math
import gspread
from google.oauth2.service_account import Credentials
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Torre de Controle | Magalu", page_icon="🛍️", layout="wide", initial_sidebar_state="expanded")

# ==============================================================================
# 🤖 POP-UP DE BOAS-VINDAS A.R.I. (APARECE SÓ 1x AO ENTRAR)
# ==============================================================================
if "ari_boas_vindas" not in st.session_state:
    st.session_state["ari_boas_vindas"] = True
    st.markdown("""
    <style>
        @keyframes slideInLeftARI {
            0% { transform: translateX(-120%); opacity: 0; visibility: visible; }
            10% { transform: translateX(0); opacity: 1; visibility: visible; }
            90% { transform: translateX(0); opacity: 1; visibility: visible; }
            100% { transform: translateX(-120%); opacity: 0; visibility: hidden; }
        }
        
        .ari-popup-container {
            position: fixed;
            bottom: 40px;
            left: 30px;
            background: linear-gradient(135deg, #0A192F 0%, #112240 100%);
            color: #E6F1FF;
            padding: 20px 25px;
            border-radius: 12px;
            border-left: 5px solid #64FFDA;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            z-index: 999999;
            max-width: 350px;
            animation: slideInLeftARI 20s forwards; /* Duração de 10 segundos */
            font-family: 'Nunito Sans', sans-serif;
        }
        
        .ari-popup-container h4 {
            margin: 0 0 10px 0;
            color: #64FFDA !important;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .ari-popup-container p {
            margin: 0;
            font-size: 13px;
            line-height: 1.5;
            color: #A8B2D1;
        }
    </style>
    
    <div class="ari-popup-container">
        <h4>
            <div style="width: 8px; height: 8px; background-color: #64FFDA; border-radius: 50%; box-shadow: 0 0 10px #64FFDA; animation: ari-blink 1.5s infinite;"></div>
            A.R.I. ONLINE
        </h4>
        <p>Este sistema conta com o <b>A.R.I. (Agente de Recebimento Inteligente)</b> para análises e planejamento tático.<br><br>
        As funções com auxílio de I.A. estarão identificadas com um selo nas páginas. <b>Sempre revise os dados</b> antes de executar qualquer ação.<br><br>
        <i>💡 Se você tiver interesse em saber mais sobre o que o A.R.I. faz, aperte no botão <b>"❓ FAQ A.R.I"</b> no menu lateral para entender todas as suas funções e onde ele está presente!</i></p>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 🎨 FRONT-END SÊNIOR | IDENTIDADE VISUAL MAGALU E A.R.I.
# ==============================================================================
st.markdown("""
<style>
    /* Importando Fonte Tecnológica e Limpa */
    @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800;900&display=swap');

    .stApp { 
        background-color: #F5F7FA; 
        font-family: 'Nunito Sans', sans-serif; 
        color: #2D3436;
    }
    
    h1, h2, h3, h4, h5, h6 { 
        color: #1E272E !important; 
        font-family: 'Nunito Sans', sans-serif !important;
        font-weight: 800 !important; 
        letter-spacing: -0.5px; 
    }
    
    hr { border-top: 2px solid #E1E8ED; border-radius: 2px; margin-top: 2rem; margin-bottom: 2rem; }
    
    /* Paineis e DataFrames: Bordas suaves e Sombras flutuantes */
    [data-testid="stDataFrame"], [data-testid="stPlotlyChart"] { 
        background-color: #FFFFFF !important; 
        border-radius: 16px !important; 
        box-shadow: 0 4px 20px rgba(0, 134, 255, 0.05) !important; 
        padding: 10px;
        border: 1px solid #F0F3F5;
        transition: all 0.3s ease;
    }
    
    [data-testid="stPlotlyChart"]:hover {
        box-shadow: 0 10px 30px rgba(0, 134, 255, 0.1) !important;
        transform: translateY(-3px);
    }

    /* Menu Lateral Branco e Elegante */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E1E8ED;
        box-shadow: 4px 0 20px rgba(0,0,0,0.02);
    }
    
    /* Customização dos Botões (Estilo Magalu) */
    .stButton>button {
        background: linear-gradient(135deg, #0086FF 0%, #006DCC 100%);
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        font-size: 15px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(0, 134, 255, 0.2);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0, 134, 255, 0.4);
        color: #FFFFFF;
    }
    
    /* Expanders Limpos */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #E1E8ED !important;
        font-weight: 700 !important;
        color: #0086FF !important;
    }

    /* ========================================================= */
    /* 🤖 SELO INLINE A.R.I. (FUTURISTA / NEON)                  */
    /* ========================================================= */
    .ari-inline-badge {
        background: linear-gradient(135deg, #0A192F 0%, #112240 100%);
        color: #64FFDA;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 1px;
        text-transform: uppercase;
        box-shadow: 0 0 10px rgba(100, 255, 218, 0.2);
        border: 1px solid #64FFDA;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        animation: ari-pulse 2.5s infinite;
        vertical-align: middle;
        margin-left: 15px;
    }

    .ari-dot {
        width: 6px;
        height: 6px;
        background-color: #64FFDA;
        border-radius: 50%;
        box-shadow: 0 0 8px #64FFDA;
        animation: ari-blink 1.5s infinite;
    }

    @keyframes ari-pulse {
        0% { box-shadow: 0 0 8px rgba(100, 255, 218, 0.2); transform: scale(1); }
        50% { box-shadow: 0 0 15px rgba(100, 255, 218, 0.6); transform: scale(1.02); }
        100% { box-shadow: 0 0 8px rgba(100, 255, 218, 0.2); transform: scale(1); }
    }

    @keyframes ari-blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
</style>
""", unsafe_allow_html=True)

# --- 🤖 GERADOR DE TÍTULOS COM SELO A.R.I ---
def titulo_com_ari(texto_titulo, texto_selo="IA - A.R.I"):
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 1rem; margin-top: 1rem;">
        <h2 style="margin: 0; padding: 0; color: #1E272E; font-family: 'Nunito Sans', sans-serif; font-weight: 800; letter-spacing: -0.5px;">{texto_titulo}</h2>
        <div class="ari-inline-badge">
            <div class="ari-dot"></div>
            <span>{texto_selo}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- ESTILIZADOR DE GRÁFICOS (PLOTLY SÊNIOR) ---
def aplicar_estilo_premium(fig):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Nunito Sans, sans-serif", color='#2D3436', size=13),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(255, 255, 255, 0.95)", 
            font_size=14, 
            font_family="Nunito Sans", 
            bordercolor="#E1E8ED",
            font_color="#1E272E"
        ),
        margin=dict(t=50, b=20, l=20, r=20),
        title_font=dict(size=18, color='#1E272E', family="Nunito Sans", weight='bold')
    )
    # Borda branca que dá o efeito de "fatias soltas" super moderno
    fig.update_traces(marker=dict(line=dict(width=1.5, color='#FFFFFF')), opacity=0.9)
    # Linhas de grade tracejadas (muito mais limpo)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E1E8ED', griddash='dash', tickfont=dict(color='#8395A7', size=12))
    fig.update_xaxes(showgrid=False, tickfont=dict(color='#8395A7', size=12), title_font=dict(color='#8395A7'))
    return fig

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- COMPONENTE DE KPI VIVO E MODERNO ---
def exibir_kpi(titulo, valor, subtitulo="", cor="#0086FF"):
    # Converte o HEX para RGB para fazer a sombra brilhar na mesma cor
    cor_hex = cor.lstrip('#')
    if len(cor_hex) == 6:
        r, g, b = tuple(int(cor_hex[i:i+2], 16) for i in (0, 2, 4))
        sombra_hover = f"rgba({r}, {g}, {b}, 0.25)"
    else:
        sombra_hover = "rgba(0, 134, 255, 0.25)"

    # HTML TODO JUNTO PARA O STREAMLIT NÃO SE PERDER
    st.markdown(f"""
    <div style="background: #FFFFFF; border-radius: 16px; padding: 22px 20px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03); border-top: 5px solid {cor}; margin-bottom: 16px; position: relative; overflow: hidden; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 25px {sombra_hover}';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(0, 0, 0, 0.03)';">
        <div style="position: absolute; top: -15px; right: -15px; width: 70px; height: 70px; background: {cor}; opacity: 0.08; border-radius: 50%;"></div>
        <p style="margin: 0; font-size: 13px; color: #576574; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">{titulo}</p>
        <h2 style="margin: 8px 0; font-size: 36px; color: #1E272E; font-weight: 900; line-height: 1.1;">{valor}</h2>
        <p style="margin: 0; font-size: 13px; color: #8395A7; font-weight: 600;">{subtitulo}</p>
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

# --- MOTOR DE INTELIGÊNCIA ARTIFICIAL GLOBAL ---
def consultar_ia_contextual(prompt_contexto, mensagem_carregamento="🧠 IA analisando cenário..."):
    import google.generativeai as genai
    try:
        # Puxando a chave com segurança direto do cofre do Streamlit
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"]) 
        modelo_nome = next((m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods), "gemini-pro")
        model = genai.GenerativeModel(modelo_nome)

        with st.spinner(mensagem_carregamento):
            # Passando a variável correta para o modelo gerar a resposta
            resposta = model.generate_content(prompt_contexto)
            return resposta.text
    except Exception as e:
        return f"🚨 Falha de comunicação com a IA: {e}"

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

            # --- TRADUTOR UNIVERSAL DE LINHAS PARA APC ---
            def categorizar_linha(linha_raw):
                l = str(linha_raw).upper()
                if 'MADEIRA SIMPLES' in l or 'COLCH' in l or 'ESTOFADO' in l or 'FREEPASS' in l:
                    return 'COLCHAO/ESTOFADO'
                if 'FRACIONADO' in l or 'MADEIRA' in l or 'MOVEIS ENCOMENDA' in l:
                    return 'MADEIRA'
                if 'BELEZA' in l or 'BENS DE CONSUMO' in l or 'MERCADO' in l or 'ALIMENT' in l:
                    return 'MERCADO'
                if 'COFRE' in l: return 'COFRE'
                if 'ELETRO PESADO' in l or 'ELETRO' in l: return 'ELETRO PESADO'
                if 'IMAGEM' in l: return 'IMAGEM'
                if 'PNEU' in l: return 'PNEU'
                if 'TRANSFERENCIA RUIM' in l: return 'TRANSFERENCIA RUIM'
                if 'TRANSFERENCIA' in l: return 'TRANSFERENCIA'
                return 'DIV PEQUENOS' 

            df_raw['Categoria_Padrao'] = df_raw['Linhas'].apply(categorizar_linha)

            df_raw['Pecas_Madeira'] = df_raw.apply(
                lambda r: r['Qtd Peças'] if r['Categoria_Padrao'] == 'MADEIRA' else 0, axis=1
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

                    # REGRA EXPRESSA
                    if 'ARTELY' in forn_original or 'ARTANY' in forn_original: return 20.0

                    forn_limpo = forn_original.replace(" ", "") 
                    categorias = str(row.get('Categorias', '')).upper()

                    def calcular_pela_categoria():
                        maior_tempo = 0 
                        for cat in categorias.split(','):
                            t = 90 
                            cat = cat.strip()
                            if 'MADEIRA' in cat: 
                                if row.get('Pecas_Madeira', 0) > 10:
                                    t = 110 if 'TUBRAX' in forn_original else 427
                                else: t = 90
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
                            chave_forn_str = str(chave_forn).strip()
                            if chave_forn_str == '': continue 
                            chave_limpa = chave_forn_str.upper().replace(" ", "")
                            if chave_limpa in forn_limpo:
                                if pd.isna(tempo) or tempo <= 0: break
                                if tempo > 300: return calcular_pela_categoria() 
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
        # 3. ABA PLANEJAMENTO (LEGO)
        # ==============================================================================
        try:
            ws_plan = planilha_principal.worksheet("PLANEJAMENTO")
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
                    # 1. Salva a original consertando erros de acentuação do arquivo
                    def limpar_caracteres_originais(cat):
                        c = str(cat).upper().strip()
                        dict_correcao = {
                            'AR E VENTILAÃ‡ÃƒO': 'AR E VENTILAÇÃO',
                            'COLCHÃƒO/ ESTOFADOS': 'COLCHÃO/ ESTOFADOS',
                            'COLCHÃƒO': 'COLCHÃO',
                            'BENS DE CONSUMO - ALIMENTÃ\x8DCIOS': 'BENS DE CONSUMO - ALIMENTÍCIOS'
                        }
                        for errado, certo in dict_correcao.items():
                            c = c.replace(errado, certo)
                        return c.replace('Ã‡ÃƒO', 'ÇÃO').replace('ÃƒO', 'ÃO').replace('Ã\x8D', 'Í').replace('Ã‡', 'Ç').replace('Ãƒ', 'Ã')

                    df_plan['categoria_original'] = df_plan['categoria'].apply(limpar_caracteres_originais)

                    # 2. Traduz a categoria para o painel gerencial de S&OP
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

# 1. BOTÃO DO FAQ A.R.I. (Clean e Minimalista)
if st.sidebar.button("❓ FAQ A.R.I", key="botao_faq_ari_unico", use_container_width=True):
    st.session_state["mostrar_faq_ari"] = not st.session_state.get("mostrar_faq_ari", False)

# Subtítulo "grudado" embaixo do botão para compor o bloco visual
st.sidebar.markdown("""
    <div style="text-align: center; margin-top: -12px; margin-bottom: 15px;">
        <span style="font-size: 11.5px; color: #8395A7; font-weight: 600;">Conheça a IA de Análise de Recebimento Inteligente</span>
    </div>
""", unsafe_allow_html=True)

# 2. O TEXTO DO FAQ (Aparece só se o botão for clicado)
if st.session_state.get("mostrar_faq_ari", False):
    st.sidebar.markdown(
        """<div style="background-color: #F8F9FA; padding: 15px; border-radius: 10px; border-left: 4px solid #64FFDA; margin-bottom: 15px; font-size: 13px;">
<b style="color: #1E272E;">🤖 Onde o A.R.I atua?</b><br><br>
<b>1. IA Recebimento (Omni-Radar):</b><br>
Conectado a 100% da malha (Lego, APC, Nuvem). O A.R.I. analisa ofensores da semana, rastreia SKUs e calcula risco de hora extra.<br><br>
<b>2. Planejamento Lego:</b><br>
O A.R.I. cruza o saldo de vagas liberadas pelo Comercial com o Risco de Gargalo Operacional, sugerindo remanejamento inteligente de cargas para evitar o caos.<br><br>
<b>3. Matriz de Risco:</b><br>
Analiso todos os perfis de carga, identifico os mais demorados, e alerto caso tenha vários deles no mesmo dia.<br><br>
<b>4. Simulador Mão de Obra:</b><br>
Tento distribuir da melhor forma as agendas do dia para a quantidade de equipes disponíveis.<br><br>
<b>5. Possíveis Gargalos:</b><br>
Analiso seu cenário operacional de forma complexa, listo os dias com riscos e deixo uma lista prontinha para você consultar o perfil do dia.<br><br>
<hr style="margin: 10px 0; border-top: 1px solid #E1E8ED;">
<i style="color: #576574; line-height: 2;">Procure pelo <span class="ari-inline-badge" style="margin: 0 4px; transform: scale(0.85); transform-origin: center; display: inline-flex;"><span class="ari-dot"></span><span>IA - A.R.I</span></span> nas páginas para ativar a IA!</i>
</div>""", 
        unsafe_allow_html=True
    )

# 3. A LOGO DO MAGALOG (Agora abaixo de tudo)
st.sidebar.image("https://magalog.com.br/opengraph-image.jpg?fdd536e7d35ec9da", width=300)
st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.header("📍 Menu de Navegação")
pagina = st.sidebar.radio("Ir para:", ["🏠 Painel Operacional", "📅 Previsão de Agendas", "📈 Simular Cenários", "👷 Simulador Mão de Obra", "🧩 Planejamento Lego", "🚛 Transferências", "📝 Solicitações Extras", "📦 Registro de Backlog", "🧩 Slotting (Vagas Extras)","📊 GD (Gestão Diária)"])
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
            fig_1p = px.bar(df_limite_1p, x='Data', y='Agendas_Validas', text='Agendas_Validas', color='Estourou_Limite', color_discrete_map={False: '#3498DB', True: '#E74C3C'}, labels={'Agendas_Validas': 'Agendas', 'Estourou_Limite': 'Acima do Limite?'}, title="Consumo da Capacidade Diária (Realizado 1P)")
            fig_1p.add_hline(y=limite_agendas_1p, line_dash="solid", line_width=3, line_color="#E74C3C", annotation_text=f"Capacidade: {limite_agendas_1p}")
            fig_1p.update_traces(textposition='outside')
            fig_1p.update_layout(xaxis=dict(tickformat="%d/%m/%Y"), showlegend=False)
            fig_1p = aplicar_estilo_premium(fig_1p)
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
    st.markdown("### 🧱 Planejamento Lego: Vagas Liberadas pelo Comercial")

    if not df_plan.empty:
        df_plan_1p = df_plan[(df_plan['data'] >= ts_inicio) & (df_plan['data'] <= ts_fim)].copy()

        if not df_plan_1p.empty:
            df_plan_1p['Vagas_Validas'] = df_plan_1p.apply(lambda x: x['quantidade_planejado'] if 'COFRE' not in str(x['categoria']).upper() else 0, axis=1)
            df_plan_1p['Vagas_Isentas'] = df_plan_1p.apply(lambda x: x['quantidade_planejado'] if 'COFRE' in str(x['categoria']).upper() else 0, axis=1)

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
                    title="Vagas Planejadas no Lego (Previsão 1P)"
                )
                fig_lego.add_hline(y=limite_agendas_1p, line_dash="solid", line_width=3, line_color="#E74C3C", annotation_text=f"Capacidade: {limite_agendas_1p}")
                fig_lego.update_traces(textposition='outside')
                fig_lego.update_layout(xaxis=dict(tickformat="%d/%m/%Y"), showlegend=False)
                fig_lego = aplicar_estilo_premium(fig_lego)
                st.plotly_chart(fig_lego, use_container_width=True)

            with col_lg2:
                st.subheader("Balanço Lego (Planejado)")
                exibir_kpi("Dias Estourados", df_limite_lego['Estourou_Limite'].sum(), "Dias acima do plano", "#E74C3C")
                exibir_kpi("Volume Planejado", df_limite_lego['Total_Planejado'].sum(), "Total vagas liberadas", "#3498DB")
                exibir_kpi("Isentos (Cofres)", df_limite_lego['Vagas_Isentas'].sum(), "Não consumem doca padrão", "#95A5A6")
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
        fig_equipes = aplicar_estilo_premium(fig_equipes)
        st.plotly_chart(fig_equipes, use_container_width=True)

    # ====================================================================
    # NOVA VISÃO: MATRIZ DE RISCO CRÍTICO SÊNIOR (DEEP ANALYTICS A.R.I.)
    # ====================================================================
    st.markdown("---")
    titulo_com_ari("🚨 Matriz de Risco Crítico")
    st.markdown("O A.R.I. vasculhou o detalhe de SKUs e Volume de **cada agenda** para prever travamento de endereçamento e impactos de recebimento. Clique nos alertas para expandir os detalhes.")

    df_risco = df_filtrado_op.copy()
    col_sku = 'Qtd SKUs' if 'Qtd SKUs' in df_risco.columns else 'Qtd_SKUs'

    dias_criticos_report = []

    for dia, df_dia in df_risco.groupby('Data'):
        cargas_altissimo = []
        alertas_dia = []
        cargas_detalhadas = [] 

        # 🧠 O SEGREDO: Memória do A.R.I para não contar a mesma agenda duas vezes!
        agendas_vistas_altissimo = set()
        agendas_vistas_atencao = set()

        # 1. Regra de Volume de Agendas no Dia (Trava Endereço)
        # Remove as linhas duplicadas de agenda para olhar o cenário real
        df_dia_unico = df_dia.drop_duplicates(subset=['Agendas']) if 'Agendas' in df_dia.columns else df_dia
        agendas_por_cat = df_dia_unico['Categorias'].astype(str).str.upper().value_counts()
        for cat, qtd in agendas_por_cat.items():
            if qtd >= 8 and any(x in cat for x in ['ELETRO', 'IMAGEM']):
                alertas_dia.append(f"📍 **Risco Trava Endereço:** {qtd} agendas de {cat} simultâneas.")

        # 2. Avaliação Linha a Linha (Mutações de Risco)
        for _, row in df_dia.iterrows():
            cat = str(row.get('Categorias', '')).upper()
            linha = str(row.get('Linhas', '')).upper()
            pecas = pd.to_numeric(row.get('Qtd Peças', 0), errors='coerce') or 0
            skus = pd.to_numeric(row.get(col_sku, 1), errors='coerce') or 1

            agenda_id = str(row.get('Agendas', row.get('Fornecedor', 'N/D')))
            nome_exibicao = cat.title() if cat else linha.title()

            is_altissimo = False
            motivo = ""
            alerta_secundario = ""

            # Regra: Base Altíssima
            if 'MADEIRA' in cat or 'MADEIRA' in linha:
                is_altissimo = True; motivo = "Madeira"
            elif 'PNEU' in cat or 'PNEU' in linha:
                is_altissimo = True; motivo = "Pneus"
            elif 'AR CONDICIONADO' in cat or 'AR CONDICIONADO' in linha:
                is_altissimo = True; motivo = "Ar Condicionado"

            # Mutação: Volume Massivo (>1000 peças)
            elif pecas >= 1000 and any(x in cat or x in linha for x in ['PORTATEIS', 'UD', 'CM', 'FERRAMENTA', 'DIVERSOS', 'AUDIO', 'AUTOMOTIVO', 'MERCADO', 'BLOCADO']):
                is_altissimo = True; motivo = f"{nome_exibicao} (>1k peças)"

            # Mutação: Fragmentação de SKUs (>10 SKUs)
            elif skus >= 10 and any(x in cat or x in linha for x in ['BENS DE CONSUMO', 'FREEPASS', 'ALIMENTO']):
                is_altissimo = True; motivo = f"{nome_exibicao} (>10 SKUs)"

            # Alertas Secundários
            if any(x in cat or x in linha for x in ['COLCH', 'ESTOFADO', 'MO2']) and skus >= 5:
                alerta_secundario = f"{nome_exibicao} super fragmentado"
            if 'COFRE' in cat and pecas >= 5000:
                alerta_secundario = f"Volume brutal de Cofres"
            if any(x in cat for x in ['BB', 'BR', 'BKF']) and pecas >= 400:
                alerta_secundario = f"Carga pesada de {nome_exibicao}"

            registrou_algo = False

            # 🛡️ VERIFICAÇÃO DE DUPLICIDADE: Só conta se a Agenda for inédita para aquele problema
            if is_altissimo:
                chave_alt = f"{agenda_id}-{motivo}"
                if chave_alt not in agendas_vistas_altissimo:
                    cargas_altissimo.append(motivo)
                    agendas_vistas_altissimo.add(chave_alt)
                    registrou_algo = True

            if alerta_secundario:
                chave_at = f"{agenda_id}-{alerta_secundario}"
                if chave_at not in agendas_vistas_atencao:
                    alertas_dia.append(f"🟡 **Atenção:** Agenda {agenda_id} - {alerta_secundario} ({pecas:,.0f} pts / {skus} skus).".replace(',', '.'))
                    agendas_vistas_atencao.add(chave_at)
                    registrou_algo = True

            # Se for um risco novo (já bloqueou os duplicados), joga na tabela de Raio-X
            if registrou_algo:
                cargas_detalhadas.append({
                    "Agenda / Origem": agenda_id,
                    "Categoria": nome_exibicao,
                    "Motivo do Risco": motivo if is_altissimo else alerta_secundario,
                    "Qtd Peças": pecas,
                    "Qtd SKUs": skus
                })

        # 3. O Veredito do Dia
        if len(cargas_altissimo) >= 3 or alertas_dia:
            dia_str = dia.strftime('%d/%m/%Y')
            resumo_altissimo = pd.Series(cargas_altissimo).value_counts()
            txt_altissimo = ", ".join([f"{qtd} {nome}" for nome, qtd in resumo_altissimo.items()])

            # Define a gravidade do título do Expander
            if len(cargas_altissimo) >= 3:
                titulo_alerta = f"🚨 DIA {dia_str}: RISCO DETECTADO ({len(cargas_altissimo)} Cargas de Alta Complexidade)"
                cor_status = "#C0392B"
            elif len(cargas_altissimo) > 0:
                titulo_alerta = f"⚠️ DIA {dia_str}: AVISO DE RISCO ({len(cargas_altissimo)} Cargas de Alta Complexidade)"
                cor_status = "#D35400"
            else:
                titulo_alerta = f"🟡 DIA {dia_str}: ATENÇÃO REQUERIDA (Travamento de Endereço/SKUs)"
                cor_status = "#F39C12"

            dias_criticos_report.append({
                "titulo": titulo_alerta,
                "cor": cor_status,
                "txt_altissimo": txt_altissimo,
                "qtd_altissimo": len(cargas_altissimo),
                "alertas": alertas_dia,
                "df_detalhes": pd.DataFrame(cargas_detalhadas) if cargas_detalhadas else pd.DataFrame()
            })

    # Renderiza o relatório na tela (Os famosos Expanders Interativos)
    if dias_criticos_report:
        st.error("⚠️ **O A.R.I. detectou configurações críticas de carga que exigem plano de ação imediato:**")

        for rep in dias_criticos_report:
            with st.expander(rep["titulo"]):
                if rep["qtd_altissimo"] >= 3:
                    st.markdown(f"<span style='color: {rep['cor']}; font-weight: bold;'>O A.R.I. identificou uma combinação fatal:</span> {rep['txt_altissimo']}. Isso inviabiliza a doca.", unsafe_allow_html=True)
                elif rep["qtd_altissimo"] > 0:
                    st.markdown(f"<span style='color: {rep['cor']}; font-weight: bold;'>O A.R.I. mapeou:</span> {rep['txt_altissimo']}.", unsafe_allow_html=True)

                for alerta in rep["alertas"]:
                    st.markdown(alerta)

                st.markdown("<br>", unsafe_allow_html=True)

                # Tabela de Detalhes (O Drill-down)
                if not rep["df_detalhes"].empty:
                    st.markdown("🔍 **Raio-X das Agendas :**")
                    st.dataframe(rep["df_detalhes"], use_container_width=True, hide_index=True)
    else:
        st.success("✅ **A.R.I. INFORMA:** Cenário Operacional limpo. Nenhuma mutação de risco (ex: Diversos com >1k peças ou excesso de SKUs) identificada no período.")

    st.markdown("---")
    titulo_com_ari("🔥 Possíveis Gargalos")
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
            fig_canais = aplicar_estilo_premium(fig_canais)
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
# 🎨 REESTRUTURAÇÃO COMPLETA: PÁGINA 1 - PREVISÃO DE AGENDAS (VISÃO DASHBOARD)
# ==============================================================================
elif pagina == "📅 Previsão de Agendas":
    # 1. BARRA DE FILTROS SUPERIOR
    col_vaz_1, col_fil_data, col_vaz_2 = st.columns([2, 2, 2])
    with col_fil_data:
        data_padrao = ts_inicio.date() if 'ts_inicio' in locals() else pd.Timestamp.now().date()
        data_consulta_dashboard = st.date_input("🗓️ Selecione o Dia para Previsão", data_padrao)
    st.markdown("<br>", unsafe_allow_html=True)

    # 🔍 TRATAMENTO DE DATA
    data_alvo = data_consulta_dashboard 

    # 2. LOCALIZAÇÃO DA TABELA DE TRANSFERÊNCIA
    base_transf = pd.DataFrame()
    for nome_var in ['df_transf', 'df_transferencia', 'df_transferencias', 'df_plan_transf']:
        if nome_var in globals():
            base_transf = globals()[nome_var]
            break

    if base_transf.empty:
        try:
            url_t = "https://docs.google.com/spreadsheets/d/1PMgqjZr2nieniRShicaPyxAe6J6j7I04FFE5aNWnm_s/export?format=csv"
            base_transf = pd.read_csv(url_t)
        except:
            pass

    # --- FILTRAGEM DE TRANSFERÊNCIA ---
    df_transf_ia = pd.DataFrame()
    if not base_transf.empty:
        col_dt_t = next((c for c in base_transf.columns if 'DATA' in str(c).strip().upper()), None)
        if col_dt_t:
            base_transf[col_dt_t] = pd.to_datetime(base_transf[col_dt_t], errors='coerce')
            df_transf_ia = base_transf[base_transf[col_dt_t].dt.date == data_alvo].copy()

    # --- FILTRAGEM DE 1P/SELLER (BASE PRINCIPAL) ---
    df_dia = df[pd.to_datetime(df['Data']).dt.date == data_alvo].copy() if not df.empty and 'Data' in df.columns else pd.DataFrame()

    # --- IDENTIFICAÇÃO DE COLUNAS PRINCIPAIS ---
    col_ag = 'Agendas' if 'Agendas' in df_dia.columns else ('Agenda' if 'Agenda' in df_dia.columns else (df_dia.columns[0] if not df_dia.empty else None))
    col_pc = 'Qtd Peças' if 'Qtd Peças' in df_dia.columns else None
    col_sk = 'Qtd SKUs' if 'Qtd SKUs' in df_dia.columns else ('Qtd_SKUs' if 'Qtd_SKUs' in df_dia.columns else None)
    col_ct = 'Categorias' if 'Categorias' in df_dia.columns else ('Linhas' if 'Linhas' in df_dia.columns else None)
    col_cn = next((c for c in df_dia.columns if str(c).strip().upper() in ['CANAL', 'ORIGEM']), None)

    # Separa 1P e Seller
    if col_cn and not df_dia.empty:
        df_dia['C_AUX'] = df_dia[col_cn].astype(str).str.upper()
        df_1p_ia = df_dia[df_dia['C_AUX'].str.contains('1P', na=False)].copy()
        df_seller_ia = df_dia[df_dia['C_AUX'].str.contains('FULFILLMENT|SELLER|3P', na=False)].copy()
    else:
        df_1p_ia = df_dia.copy()
        df_seller_ia = pd.DataFrame()

    # --- 🛡️ CÁLCULO DOS KPIS TOTAIS (AGORA BLINDADO CONTRA KEYERROR) ---
    tot_ag_main = df_dia[col_ag].nunique() if (col_ag and not df_dia.empty) else 0
    tot_pc_main = df_dia[col_pc].sum() if (col_pc and not df_dia.empty) else 0
    tot_sk_main = df_dia[col_sk].sum() if (col_sk and not df_dia.empty) else 0

    # Acha colunas da transferência dinamincamente e com segurança
    col_ag_t = next((c for c in df_transf_ia.columns if 'AGENDA' in str(c).upper()), None) if not df_transf_ia.empty else None
    col_pc_t = next((c for c in df_transf_ia.columns if 'PEÇA' in str(c).upper() or 'PECAS' in str(c).upper() or 'QTD' in str(c).upper() or 'QUANT' in str(c).upper()), None) if not df_transf_ia.empty else None

    # Só soma se a coluna realmente existir (Isso mata o KeyError!)
    tot_ag_tra = df_transf_ia[col_ag_t].nunique() if (col_ag_t and col_ag_t in df_transf_ia.columns) else 0
    tot_pc_tra = pd.to_numeric(df_transf_ia[col_pc_t], errors='coerce').sum() if (col_pc_t and col_pc_t in df_transf_ia.columns) else 0

    # 3. CABEÇALHO KPI NEON SÊNIOR
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #FF6F61 0%, #0086FF 100%); padding: 20px 25px; border-radius: 16px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0, 134, 255, 0.2); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div style="display: flex; align-items: center; gap: 15px; color: #FFFFFF; font-family: 'Nunito Sans', sans-serif;">
            <div class="ari-dot" style="width: 16px; height: 16px; box-shadow: 0 0 15px #64FFDA; background-color: #64FFDA;"></div>
            <h3 style="margin: 0; color: #FFFFFF !important; font-weight: 900; font-size: 26px; letter-spacing: -0.5px;">Dashboard {data_alvo.strftime('%d/%m/%Y')}</h3>
        </div>
        <div style="display: flex; gap: 15px; flex-wrap: wrap;">
            <div style="background-color: #FFFFFF; padding: 12px 25px; border-radius: 12px; text-align: center; box-shadow: 0 8px 20px rgba(0,0,0,0.15); min-width: 120px;">
                <span style="font-size: 11px; font-weight: 800; color: #8395A7; text-transform: uppercase;">Agendas</span><br>
                <span style="font-size: 24px; font-weight: 900; color: #1E272E;">{tot_ag_main + tot_ag_tra:,.0f}</span>
            </div>
            <div style="background-color: #FFFFFF; padding: 12px 25px; border-radius: 12px; text-align: center; box-shadow: 0 8px 20px rgba(0,0,0,0.15); min-width: 120px;">
                <span style="font-size: 11px; font-weight: 800; color: #8395A7; text-transform: uppercase;">Peças</span><br>
                <span style="font-size: 24px; font-weight: 900; color: #0086FF;">{tot_pc_main + tot_pc_tra:,.0f}</span>
            </div>
        </div>
    </div>
    """.replace(',', '.'), unsafe_allow_html=True)

    # 4. COLUNAS (1P | SELLER | TRANSF)
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"#### 🛒 1P ({tot_ag_main})")
        if not df_1p_ia.empty and col_ct:
            st.plotly_chart(px.bar(df_1p_ia.groupby(col_ct).size().reset_index(name='Qtd'), y=col_ct, x='Qtd', orientation='h', height=250), use_container_width=True)
            with st.expander("Ver Agendas 1P"):
                st.dataframe(df_1p_ia, use_container_width=True, hide_index=True)
        else: st.info("Sem dados 1P")

    with c2:
        qtd_sel = df_seller_ia[col_ag].nunique() if (not df_seller_ia.empty and col_ag) else 0
        st.markdown(f"#### 🚚 Seller ({qtd_sel})")
        if not df_seller_ia.empty and col_ct:
            st.plotly_chart(px.bar(df_seller_ia.groupby(col_ct).size().reset_index(name='Qtd'), y=col_ct, x='Qtd', orientation='h', height=250), use_container_width=True)
            with st.expander("Ver Agendas Seller"):
                st.dataframe(df_seller_ia, use_container_width=True, hide_index=True)
        else: st.info("Sem dados Seller")

    with c3:
        st.markdown(f"#### 📦 Transf ({tot_ag_tra})")
        if not df_transf_ia.empty:
            col_ct_t = next((c for c in df_transf_ia.columns if 'CAT' in str(c).upper() or 'LINHA' in str(c).upper() or 'TIPO' in str(c).upper()), None)

            if col_ct_t:
                st.plotly_chart(px.bar(df_transf_ia.groupby(col_ct_t).size().reset_index(name='Qtd'), y=col_ct_t, x='Qtd', orientation='h', height=250, color_discrete_sequence=['#FF6F61']), use_container_width=True)

            with st.expander("Ver Agendas Transf"):
                st.dataframe(df_transf_ia, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Sem transferências nesta data.")
            if st.checkbox("Debug: Ver base bruta Transf"):
                st.write(base_transf.head(5) if not base_transf.empty else "Tabela Vazia")

# ==============================================================================
# PÁGINA 2.5: Simulador Cenário APC
# ==============================================================================
elif pagina == "📈 Simular Cenários":
    col_titulo, col_reset = st.columns([4, 1])
    with col_titulo:
        st.title("📈 Simulador Cenário APC | Estresse de Malha")
        st.markdown("Adicione novas cargas em múltiplos dias e veja o impacto cumulativo na semana inteira. O sistema **salva as suas adições** enquanto você navega pelas datas!")

    if 'simulador_cargas' not in st.session_state:
        st.session_state['simulador_cargas'] = {}

    with col_reset:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Limpar Simulação", use_container_width=True):
            st.session_state['simulador_cargas'] = {}
            st.rerun()

    df_base_periodo = df[(df['Data'] >= ts_inicio) & (df['Data'] <= ts_fim)].copy()

    if not df_base_periodo.empty:
        st.markdown("---")
        st.markdown("### 🎛️ Filtro de Cenário Base")
        canais_disponiveis = df_base_periodo['Canal'].unique().tolist()
        canais_selecionados = st.multiselect("Selecione quais canais você quer manter no cálculo ANTES de simular o estresse:", options=canais_disponiveis, default=canais_disponiveis)

        df_filtrado_sim = df_base_periodo[df_base_periodo['Canal'].isin(canais_selecionados)]
        df_apc_base = df_base_periodo[['Data']].drop_duplicates()

        if not df_filtrado_sim.empty:
            df_agg = df_filtrado_sim.groupby('Data').agg({'Tempo_APC_Minutos': 'sum', 'Agenda_Texto': 'nunique'}).reset_index()
            df_apc_base = pd.merge(df_apc_base, df_agg, on='Data', how='left').fillna(0)
        else:
            df_apc_base['Tempo_APC_Minutos'] = 0
            df_apc_base['Agenda_Texto'] = 0

        df_apc_base['Min_Transf_Fixa'] = df_apc_base['Data'].apply(lambda x: 1200 if x.weekday() < 5 else 0)
        df_apc_base['Minutos_Originais'] = df_apc_base['Tempo_APC_Minutos'] + df_apc_base['Min_Transf_Fixa']
        df_apc_base['Equipes_Originais'] = df_apc_base['Minutos_Originais'].apply(lambda x: math.ceil(x / 427))
        df_apc_base['Data_Str'] = df_apc_base['Data'].dt.strftime('%d/%m/%Y')

        st.markdown("---")
        col_painel, col_resumo = st.columns([2, 1])

        with col_painel:
            st.markdown("### 🧪 Injetar Cargas por Dia")
            dia_alvo = st.selectbox("Selecione o Dia para adicionar as cargas:", df_apc_base['Data_Str'].tolist())

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

            st.session_state['simulador_cargas'][dia_alvo] = {'mad': val_mad, 'ele': val_ele, 'pne': val_pne, 'mer': val_mer, 'cof': val_cof, 'div': val_div}

        df_apc_simulado = df_apc_base.copy()
        df_apc_simulado['Minutos_Simulados'] = df_apc_simulado['Minutos_Originais']
        df_apc_simulado['Cenario'] = 'Real Base'

        for d_str, injecoes in st.session_state['simulador_cargas'].items():
            min_add = (injecoes['mad'] * 427) + (injecoes['ele'] * 95) + (injecoes['pne'] * 240) + (injecoes['mer'] * 150) + (injecoes['cof'] * 90) + (injecoes['div'] * 60)
            if min_add > 0:
                idx = df_apc_simulado['Data_Str'] == d_str
                df_apc_simulado.loc[idx, 'Minutos_Simulados'] += min_add
                df_apc_simulado.loc[idx, 'Cenario'] = 'Simulado'

        df_apc_simulado['Equipes_Simuladas'] = df_apc_simulado['Minutos_Simulados'].apply(lambda x: math.ceil(x / 427))

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

        fig_sim = px.bar(
            df_apc_simulado.sort_values(by='Data'), x='Data', y='Equipes_Simuladas', text='Equipes_Simuladas', 
            color='Cenario', color_discrete_map={'Real Base': '#3498DB', 'Simulado': '#E74C3C'}, title="Evolução de Mão de Obra Necessária"
        )
        fig_sim.update_traces(textposition='outside')
        fig_sim.update_layout(xaxis=dict(tickformat="%d/%m/%Y"))
        fig_sim = aplicar_estilo_premium(fig_sim)

        col_graf_esq, col_graf_dir = st.columns([5, 1])
        with col_graf_esq: st.plotly_chart(fig_sim, use_container_width=True)
    else: st.warning("Não há dados carregados para gerar a simulação no período selecionado.")

# ==============================================================================
# PÁGINA 3: PROVA DE SOBRECARGA (COMERCIAL)
# ==============================================================================
elif pagina == "👷 Simulador Mão de Obra":
    titulo_com_ari("⚖️ Análise de Mão de obra")
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
                cargas_alocadas.append({'Equipe': nomes_equipes[eq_num], 'Tipo Carga': 'Transferência Fixa (240m)', 'Minutos': 240, 'Detalhe': f'Transf CD Origem {i+1}'})

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
            cargas_alocadas.append({'Equipe': nomes_equipes[eq_num], 'Tipo Carga': tipo, 'Minutos': min_val, 'Detalhe': det})

        for min_val, tipo, det in cargas_restante:
            eq_num = min(tempo_equipes.keys(), key=lambda k: tempo_equipes[k])
            tempo_equipes[eq_num] += min_val
            cargas_alocadas.append({'Equipe': nomes_equipes[eq_num], 'Tipo Carga': tipo, 'Minutos': min_val, 'Detalhe': det})

        df_mochila = pd.DataFrame(cargas_alocadas)

        if not df_mochila.empty:
            df_mochila['Ordem'] = df_mochila['Equipe'].str.extract(r'(\d+)').astype(int)
            df_mochila = df_mochila.sort_values(by="Ordem")

            minutos_totais = sum(tempo_equipes.values())
            capacidade_total_cd = total_equipes * 427
            equipes_estouradas = sum(1 for v in tempo_equipes.values() if v > 427)

            # ====================================================================
            # 🧠 IA EMBUTIDA: A.R.I. ESTRATEGISTA DE TROPA
            # ====================================================================
            st.markdown("---")
            col_ia_tropa_txt, col_ia_tropa_btn = st.columns([3, 1])
            with col_ia_tropa_txt:
                st.markdown("### 🧠 A.R.I. | Otimizador de Headcount")
                st.caption("Deixe o A.R.I. analisar a volumetria exata deste dia e sugerir a melhor formação tática para as suas equipes operacionais.")

            with col_ia_tropa_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                btn_ia_tropa = st.button("✨ Sugerir Formação Ideal", use_container_width=True)

            if btn_ia_tropa:
                # O A.R.I junta todos os pedaços de carga do dia para entender a guerra
                qtd_transf_fixa = sum(1 for x in cargas_alocadas if 'Transferência Fixa' in x['Tipo Carga'])
                qtd_mad = len(cargas_madeira_lista)
                min_mad = sum(x[0] for x in cargas_madeira_lista)
                qtd_outras = len(cargas_restante)
                min_outras = sum(x[0] for x in cargas_restante)

                prompt_tropa = f"""
                Você é o A.R.I., Estrategista Logístico do CD2900 Magalu.
                
                [CENÁRIO OPERACIONAL DO DIA {dia_simulacao}]:
                - Headcount Total Disponível: {total_equipes} equipes.
                - Capacidade Máxima por Equipe: 427 minutos úteis.
                - Minutos Totais Exigidos pela Carga: {minutos_totais} min.
                
                [PERFIL DA CARGA A SER DESCARREGADA]:
                - Transferências Fixas: {qtd_transf_fixa} rotas de 240 minutos cada.
                - Cargas de Madeira (Críticas): {qtd_mad} cargas (Totalizando {min_mad} minutos).
                - Cargas Diversas (1P/Full): {qtd_outras} cargas (Totalizando {min_outras} minutos).
                
                [SUA MISSÃO TÁTICA]:
                Como devemos configurar nossas {total_equipes} equipes no painel (Quantas focadas em Transferência, quantas focadas em Madeira e quantas ficarão Mistas) para que a distribuição das barras no gráfico fique o mais reta (equalizada) possível, evitando que uma equipe exploda de 427 minutos enquanto outra fica à toa?
                
                [REGRAS DE RESPOSTA]:
                1. Dê a ordem direta de como o usuário deve preencher o menu lateral. Ex: "Para equalizar hoje, coloque X na Transferência, Y na Madeira."
                2. Explique a matemática por trás da sua escolha de forma curta e genérica.
                3. Se os minutos exigidos pela carga ({minutos_totais}) forem MAIORES que a capacidade total ({capacidade_total_cd}), emita um "🚨 ALERTA DE COLAPSO" dizendo que a melhor formação apenas ameniza os danos, mas o déficit de horas extras é inevitável. Seja curto e direto!
                """

                resposta_ia = consultar_ia_contextual(prompt_tropa, "🧠 Simulando milhares de combinações de equipes...")

                st.info("💡 **Formação Tática sugerida pelo A.R.I.:**")
                st.markdown(resposta_ia)
            # ====================================================================

            st.markdown("---")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1: exibir_kpi("Equipes em Sobrecarga", f"{equipes_estouradas} de {total_equipes}", "Mesmo equalizando 100%", "#E74C3C")
            with col_s2: exibir_kpi("Demanda Exigida no Dia", f"{int(minutos_totais)} min", f"Capacidade Real: {capacidade_total_cd} min", "#9B59B6")

            saldo = minutos_totais - capacidade_total_cd
            if saldo > 0: 
                with col_s3: 
                    exibir_kpi("Déficit Inevitável", f"+{int(saldo)} min", "Tempo faltante", "#E74C3C")
            else: 
                with col_s3: 
                    exibir_kpi("Déficit Inevitável", "0 min", "Operação dentro do limite", "#2ECC71")

            fig_mochila = px.bar(
                df_mochila, x='Equipe', y='Minutos', color='Tipo Carga', text='Detalhe', title=f"Balanceamento Dinâmico de Cargas - Dia {dia_simulacao}",
                color_discrete_map={'Transferência Fixa (240m)': '#8E44AD', 'Carga Madeira': '#E67E22', 'Carga Fulfillment': '#3498DB', 'Carga 1P/Misto': '#2ECC71'}
            )

            fig_mochila.add_hline(y=427, line_dash="solid", line_width=3, line_color="#E74C3C", annotation_text="Capacidade Máxima do Turno (427 min)", annotation_position="top left", annotation_font_color="#E74C3C")
            fig_mochila.update_traces(textposition='inside', insidetextanchor='middle')
            fig_mochila = aplicar_estilo_premium(fig_mochila)
            fig_mochila.update_layout(height=800, bargap=0.15)
            st.plotly_chart(fig_mochila, use_container_width=True)
        else: st.warning("Nenhuma carga encontrada para o dia selecionado.")
    else: st.warning("Não há dados carregados para gerar a simulação.")

# ==============================================================================
# PÁGINA 4: MATRIZ DE PLANEJAMENTO (S&OP COMERCIAL)
# ==============================================================================
elif pagina == "🧩 Planejamento Lego":
    st.title("🧩 Visão planejamento capacidade LEGO")

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Parâmetros do Lego")
    limite_agendas_1p = st.sidebar.number_input("Teto Agendas 1P/Dia", min_value=1, max_value=50, value=14)

    df_plan_filtrado = df_plan[(df_plan['data'] >= ts_inicio) & (df_plan['data'] <= ts_fim)].copy() if not df_plan.empty else pd.DataFrame()

    if not df_plan.empty:
        st.markdown("### 🎯 Planejamento Mensal do Comercial")
        st.write("Digite as vagas aprovadas (LEGO) e clique em Salvar. O sistema gravará na Nuvem (Google Sheets).")

        # 1. USA AS CATEGORIAS TRADUZIDAS PARA AS METAS E SALDO
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

        # 2. BALANÇO POR CATEGORIA TRADUZIDA
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
        st.markdown("#### 🔍 Fechamento por Categoria (Metas Agrupadas)")

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

        # 3. MATRIZ DE ACOMPANHAMENTO DIÁRIO (ORIGINAL)
        st.markdown("### 🧩 Distribuição Diária: Planejado x Realizado (Linhas Originais)")

        # Legenda do Heatmap de Cores
        st.markdown("""
        <div style="display: flex; gap: 15px; margin-bottom: 15px;">
            <div style="padding: 6px 12px; background-color: #FADBD8; color: #C0392B; border-radius: 6px; font-weight: bold; font-size: 13px;">🔴 Esgotado / Estourado (0 vagas)</div>
            <div style="padding: 6px 12px; background-color: #FDEBD0; color: #D35400; border-radius: 6px; font-weight: bold; font-size: 13px;">🟡 Atenção (Apenas 1 vaga)</div>
            <div style="padding: 6px 12px; background-color: #D5F5E3; color: #27AE60; border-radius: 6px; font-weight: bold; font-size: 13px;">🟢 Livre (2+ vagas disponíveis)</div>
        </div>
        """, unsafe_allow_html=True)

        if not df_plan_filtrado.empty:
            pivot = pd.pivot_table(
                df_plan_filtrado, index='categoria_original', columns='data', 
                values=['quantidade_planejado', 'quantidade_real'], aggfunc='sum', fill_value=0
            )
            pivot = pivot.swaplevel(0, 1, axis=1).sort_index(axis=1, level=0)

            # Remove linhas que não tem planejamento nem agendamento no período filtrado
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
                            val_real = df_pivot.loc[indice, (data_str, 'REALIZADO')]
                            val_plan = df_pivot.loc[indice, (data_str, 'PLANEJADO')]

                            css = ''
                            if pd.isna(val_real) and pd.isna(val_plan):
                                css += 'color: rgba(0,0,0,0); background-color: rgba(0,0,0,0); ' 
                            elif val_real == 0 and val_plan == 0:
                                css += 'color: rgba(0,0,0,0); background-color: rgba(0,0,0,0); ' 
                            else:
                                if tipo == 'REALIZADO':
                                    vagas = val_plan - val_real
                                    # Lógica de Cores por Disponibilidade
                                    if vagas <= 0:
                                        css += 'background-color: #FADBD8; color: #C0392B; font-weight: bold; border-right: 2px solid #EAEDED;' 
                                    elif vagas == 1:
                                        css += 'background-color: #FDEBD0; color: #D35400; font-weight: bold; border-right: 2px solid #EAEDED;' 
                                    else:
                                        css += 'background-color: #D5F5E3; color: #27AE60; font-weight: bold; border-right: 2px solid #EAEDED;' 
                                else:
                                    # Planejado ganha uma cor neutra para não poluir a tela
                                    css += 'background-color: #F8F9FA; color: #7F8C8D; font-weight: bold; border-left: 2px solid #EAEDED;'

                            estilos.loc[indice, coluna] = css
                    return estilos

                tabela_estilizada = pivot.style.format("{:.0f}").apply(formatar_tabela_lego, axis=None)
                st.dataframe(tabela_estilizada, use_container_width=True, height=600)

                # ====================================================================
                # 🧠 IA EMBUTIDA: ASSISTENTE DE REDISTRIBUIÇÃO LEGO vs APC
                # ====================================================================
                st.markdown("---")
                col_ia_txt, col_ia_btn = st.columns([3, 1])
                with col_ia_txt:
                    st.markdown("### 🧠 Otimização de Malha com IA")
                    st.caption("A IA cruzará o saldo de vagas desta tabela com o risco de Hora Extra (APC) para sugerir a redistribuição de cargas.")

                with col_ia_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_ia_lego = st.button("✨ Sugerir Redistribuição", use_container_width=True)

                if btn_ia_lego:
                    # 1. DADOS DO LEGO (Detalhado por Categoria e Vagas Livres)
                    df_plan_ia = df_plan_filtrado.copy()
                    df_plan_ia['data_str'] = df_plan_ia['data'].dt.strftime('%d/%m/%Y')
                    # Marca os isentos para a IA saber que Cofre não conta no teto
                    df_plan_ia['Isento'] = df_plan_ia['categoria'].apply(lambda x: 'Sim' if 'COFRE' in str(x).upper() else 'Não')

                    txt_vagas_lego = df_plan_ia.groupby(['data_str', 'categoria', 'Isento']).agg(
                        Planejado=('quantidade_planejado', 'sum'),
                        Realizado=('quantidade_real', 'sum')
                    ).reset_index()
                    # A "Gordura" que a gente pode mexer
                    txt_vagas_lego['Saldo_Livre'] = txt_vagas_lego['Planejado'] - txt_vagas_lego['Realizado']
                    tabela_vagas_prompt = txt_vagas_lego.to_csv(index=False, sep='|')

                    # 2. RESUMO DO TETO 1P (O Risco do Comercial - Limite Físico)
                    df_resumo_teto = df_plan_ia[df_plan_ia['Isento'] == 'Não'].groupby('data_str').agg(
                        Total_Planejado=('quantidade_planejado', 'sum'),
                        Total_Realizado=('quantidade_real', 'sum')
                    ).reset_index()
                    tabela_teto_prompt = df_resumo_teto.to_csv(index=False, sep='|')

                    # 3. DADOS DE APC (O Risco de Mão de Obra)
                    df_base_apc = df[(df['Data'] >= ts_inicio) & (df['Data'] <= ts_fim)].copy()
                    if not df_base_apc.empty:
                        df_base_apc['Data_Str'] = df_base_apc['Data'].dt.strftime('%d/%m/%Y')
                        df_gargalo = df_base_apc.groupby('Data_Str').agg({'Tempo_APC_Minutos': 'sum'}).reset_index()
                        df_gargalo['Equipes_Necessarias'] = (df_gargalo['Tempo_APC_Minutos'] / 427).apply(math.ceil)
                        tabela_gargalo_prompt = df_gargalo.to_csv(index=False, sep='|')
                    else:
                        tabela_gargalo_prompt = "Sem dados de APC."

                    # 4. PROMPT FINAL (A Mente do Arquiteto S&OP)
                    prompt_final = f"""
                    Seu nome é A.R.I (Agente de Recebimento Inteligente) a sua função é da um suporte para o planejamento operacional, seja um cara simpatico mas que entenda do assunto.

                    [LEIS DA FÍSICA DO CD2900 - DECORE]:
                    1. TETO DE AGENDAS 1P: O limite máximo é de {limite_agendas_1p} carros/dia (Ignorar 'COFRES', pois são isentos).
                    2. LIMITE DE EQUIPES (APC): Máximo de 6 equipes/dia.
                    3. REGRA DE OURO (TIMING): Se num dia sobrecarregado o 'Realizado' for igual ou maior que o 'Planejado', nós PERDEMOS O TIMING. Não podemos alterar o que já foi agendado.
                    4. AÇÃO: Você só pode sugerir mover cargas de um dia crítico SE houver 'Saldo_Livre' (Planejado > Realizado) daquela categoria.
                    
                    [TABELA 1: CAPACIDADE DIÁRIA (TOTAL DE CARROS PLANEJADOS VS LIMITE DE {limite_agendas_1p})]:
                    {tabela_teto_prompt}

                    [TABELA 2: CUSTO DE MÃO DE OBRA (APC VS LIMITE DE 6 EQUIPES)]:
                    {tabela_gargalo_prompt}

                    [TABELA 3: DETALHAMENTO DE VAGAS POR CATEGORIA (BUSQUE AQUI O 'SALDO_LIVRE' PARA MOVER)]:
                    {tabela_vagas_prompt}

                    TAREFA TÁTICA:
                    1. Cruze as três tabelas. Ache os dias que vão capotar a doca (Seja pelo Teto Físico de {limite_agendas_1p} carros OU por exigir mais de 6 equipes).
                    2. Verifique se nesses dias de caos ainda existe 'Saldo_Livre' em alguma categoria na Tabela 3. Se não tiver saldo (Realizado já bateu o planejado), diga: "Dia X estourado, mas perdemos o timing de atuação. As cargas já estão confirmadas."
                    3. Se houver 'Saldo_Livre', dê uma ordem exata de REMANEJAMENTO: Indique qual categoria bloquear no dia crítico e para qual dia transferir (escolha um dia onde os carros < {limite_agendas_1p} e a equipe < 6).
                    4. Responda em formato de 'Plano de Ação' com bullet points. Seja cirúrgico, sem blá-blá-blá.
                    """

                    resposta_ia = consultar_ia_contextual(prompt_final, "🧠 Cruzando capacidade, Teto de agendas do mês, e Vagas no Lego...")

                    # Exibe a resposta
                    st.info("💡 **Veredito da Inteligência Artificial:**")
                    st.markdown(resposta_ia)
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
                fig_transf = aplicar_estilo_premium(fig_transf)
                st.plotly_chart(fig_transf, use_container_width=True)

            with graf_col2:
                fig_modal = px.pie(resumo_tabela, values='Peças', names='Modalidade', title="Distribuição por Modal", hole=0.4, color_discrete_sequence=px.colors.sequential.Purples_r)
                fig_modal = aplicar_estilo_premium(fig_modal)
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
            fornecedor_extra = st.text_input("Fornecedor")
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

# ==============================================================================
# PÁGINA 7: REGISTRO DE BACKLOG (SOBRAS DE DOCA)
# ==============================================================================
elif pagina == "📦 Registro de Backlog":
    st.title("📦 Registro de Backlog Diário")
    st.markdown("Registre aqui as cargas que não puderam ser descarregadas no dia previsto e precisaram ser roladas para o dia seguinte. Isso gerará um histórico de gargalos operacionais.")

    st.markdown("### ➕ Novo Registro de Backlog")
    with st.form(key="form_backlog", clear_on_submit=True):
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            data_backlog = st.date_input("Data Original do Agendamento", format="DD/MM/YYYY")
            agenda_backlog = st.text_input("Número da Agenda / ID")
            forn_backlog = st.text_input("Fornecedor / Transportadora")
        with col_b2:
            cat_backlog = st.text_input("Categoria / Linha")
            motivo_backlog = st.selectbox(
                "Motivo da BackLog", 
                ["Operacional", "Ocupação (Armazém)", "Acima da Capacidade (Equipe)", "Tempo Hábil", "Sistêmico / Outros"]
            )
            qtd_pecas_backlog = st.number_input("Quantidade de Peças (Opcional)", min_value=0, step=1)

        submit_backlog = st.form_submit_button("💾 Salvar Backlog na Nuvem")

        if submit_backlog:
            if not agenda_backlog or not forn_backlog:
                st.error("⚠️ Por favor, preencha pelo menos a Agenda e o Fornecedor.")
            else:
                try:
                    cliente_google = conectar_google()
                    ws_principal = cliente_google.open_by_key('1WA5GjT1f-jpQ4Sw_OfvXBERyz5MehfH7uaFrIfUMrtw')

                    # Tenta achar a aba, se não existir, o robô cria sozinho!
                    try:
                        ws_backlog = ws_principal.worksheet("BACKLOG")
                    except:
                        ws_backlog = ws_principal.add_worksheet(title="BACKLOG", rows="100", cols="7")
                        ws_backlog.append_row(["Data Original", "Agenda", "Fornecedor", "Categoria", "Motivo", "Qtd Peças", "Data do Registro"])

                    ws_backlog.append_row([
                        data_backlog.strftime("%d/%m/%Y"),
                        agenda_backlog.strip(),
                        forn_backlog.strip().upper(),
                        cat_backlog.strip().upper(),
                        motivo_backlog,
                        int(qtd_pecas_backlog),
                        pd.Timestamp.now(tz='America/Sao_Paulo').strftime("%d/%m/%Y %H:%M:%S")
                    ])
                    st.success("✅ Backlog registrado com sucesso! Os dados já estão na nuvem.")
                except Exception as e:
                    st.error(f"🚨 Erro ao salvar: {e}")

    st.markdown("---")
    st.markdown("### 📚 Histórico de Backlogs Registrados")

    # O robô lê a planilha de Backlog em tempo real para exibir na tela
    try:
        cliente_google = conectar_google()
        ws_principal = cliente_google.open_by_key('1WA5GjT1f-jpQ4Sw_OfvXBERyz5MehfH7uaFrIfUMrtw')
        ws_backlog_hist = ws_principal.worksheet("BACKLOG")
        dados_hist = ws_backlog_hist.get_all_values()

        if len(dados_hist) > 1:
            df_hist_backlog = pd.DataFrame(dados_hist[1:], columns=dados_hist[0])
            st.dataframe(df_hist_backlog, use_container_width=True, hide_index=True)

            st.markdown("#### Gargalos (Motivos)")
            col_g1, col_g2 = st.columns([1, 2])

            with col_g1:
                resumo_motivos = df_hist_backlog['Motivo'].value_counts().reset_index()
                resumo_motivos.columns = ['Motivo', 'Quantidade']
                fig_motivos = px.pie(resumo_motivos, values='Quantidade', names='Motivo', hole=0.5, color_discrete_sequence=px.colors.sequential.Teal)
                fig_motivos.update_traces(textposition='inside', textinfo='percent+label')
                fig_motivos = aplicar_estilo_premium(fig_motivos)
                fig_motivos.update_layout(showlegend=False)
                st.plotly_chart(fig_motivos, use_container_width=True)
        else:
            st.info("Ainda não há backlogs registrados no sistema.")
    except:
        st.info("A planilha de BACKLOG será criada automaticamente assim que você registrar a primeira sobra acima.")

# ==============================================================================
# 🧩 NOVA PÁGINA: SLOTTING INTELIGENTE (VAGAS EXTRAS DO COMERCIAL)
# ==============================================================================
elif pagina == "🧩 Slotting (Vagas Extras)":
    titulo_com_ari("🧩 Slotting Inteligente (S&OP)")
    st.markdown("""
    Analise pedidos do Comercial e encontre o dia ideal para encaixe, respeitando a 
    **Matriz de Risco** e a operação de **Segunda a Sexta**.
    """)

    texto_comercial = st.text_area(
        "📥 Cole o pedido do Comercial aqui:", 
        height=150, 
        placeholder="Ex: Preciso encaixar 2 carretas da Artely de madeira..."
    )

    if st.button("✨ A.R.I. - Analisar e Sugerir Slotting", type="primary", use_container_width=True):
        if not texto_comercial.strip():
            st.warning("⚠️ Cole o texto antes de rodar.")
        else:
            with st.spinner("🧠 A.R.I. calculando janelas de oportunidade..."):

                # --- PASSO A: MAPA DE CAPACIDADE (BLOQUEANDO FIM DE SEMANA) ---
                hoje = pd.Timestamp.now().date()
                # Aumentamos para 20 dias para garantir que achamos dias úteis suficientes
                dias_futuros = [hoje + pd.Timedelta(days=i) for i in range(20)]

                mapa_capacidade = []
                for d in dias_futuros:
                    # 🛡️ REGRA: 0=Segunda, 4=Sexta, 5=Sábado, 6=Domingo
                    if d.weekday() >= 5:
                        mapa_capacidade.append(f"- {d.strftime('%d/%m/%Y')} ({d.strftime('%A')}): ⛔ FECHADO (Fim de Semana).")
                        continue

                    df_dia = df[pd.to_datetime(df['Data']).dt.date == d] if 'Data' in df.columns else pd.DataFrame()

                    if df_dia.empty:
                        mapa_capacidade.append(f"- {d.strftime('%d/%m/%Y')}: DISPONÍVEL (0 Agendas).")
                        continue

                    # Cálculos do Dia
                    col_ag = 'Agendas' if 'Agendas' in df_dia.columns else (df_dia.columns[0] if not df_dia.empty else None)
                    tot_agendas = df_dia[col_ag].nunique() if col_ag else 0

                    col_cat = 'Categorias' if 'Categorias' in df_dia.columns else ('Linhas' if 'Linhas' in df_dia.columns else None)
                    col_pc = 'Qtd Peças' if 'Qtd Peças' in df_dia.columns else None

                    pecas_ud_div = 0
                    if col_cat and col_pc:
                        filtro_ud = df_dia[col_cat].astype(str).str.upper().str.contains('DIVERSOS|UD|UTILIDADES')
                        pecas_ud_div = pd.to_numeric(df_dia.loc[filtro_ud, col_pc], errors='coerce').sum()

                    mapa_capacidade.append(
                        f"- {d.strftime('%d/%m/%Y')}: {tot_agendas} Agendas. Vol. UD/Diversos: {pecas_ud_div:,.0f} peças."
                    )

                mapa_texto = "\n".join(mapa_capacidade)

                # --- PASSO B: O PROMPT (REFORÇANDO SEGUNDA A SEXTA) ---
                prompt_slotting = f"""
                Você é o A.R.I., Especialista Sênior em Slotting no CD2900 Magalu.
                
                [PEDIDO DO COMERCIAL]:
                {texto_comercial}

                [MAPA DE CAPACIDADE]:
                {mapa_texto}

                [REGRAS CRÍTICAS DE NEGÓCIO]:
                1. 🗓️ OPERAÇÃO APENAS DE SEGUNDA A SEXTA. Nunca sugira sábado ou domingo (marcados como FECHADO no mapa).
                2. 📈 LIMITE DE DIVERSOS/UD: Máximo de 4.000 peças acumuladas por dia nessas categorias.
                3. 🚚 LIMITE DE AGENDAS: Máximo 30 agendas/dia (ou 35 se houver pouca carga de Fulfillment).
                4. 🔍 ANÁLISE DE RISCO: Não coloque cargas complexas (Madeira/Pneu) em dias que já estão carregados.

                [RESPOSTA]:
                Explique sua decisão e forneça a tabela: Fornecedor | Categoria | Qtd Peças | Retorno CD | Justificativa.
                """

                resposta_ia = consultar_ia_contextual(prompt_slotting, "🧠 Analisando dias úteis e volumetria...")

                st.markdown("---")
                st.markdown("### 📋 Veredito de Slotting do A.R.I.")
                st.markdown(resposta_ia)

                # Botão de Download (CSV)
                try:
                    linhas_tabela = [l for l in resposta_ia.split('\n') if '|' in l and '---' not in l]
                    if len(linhas_tabela) > 1:
                        import io
                        csv_buffer = io.StringIO()
                        for l in linhas_tabela:
                            linha_csv = ",".join([c.strip() for c in l.split('|') if c.strip()])
                            csv_buffer.write(linha_csv + "\n")
                        st.download_button(label="📥 Baixar Retorno CD (Excel)", data=csv_buffer.getvalue().encode('utf-8-sig'), file_name="Slotting_ARI.csv", mime="text/csv")
                except: pass

# ==============================================================================
# 📊 NOVA PÁGINA: GD (GESTÃO DIÁRIA) - STATUS, PRODUTIVIDADE E ARMAZENAGEM
# ==============================================================================
elif pagina == "📊 GD (Gestão Diária)":
    titulo_com_ari("📊 GD - Gestão Diária ")
    st.markdown("Acompanhamento em tempo real do status das agendas, performance tática e pendências de armazenagem.")

    # 1. FILTROS DA GD (COM AJUSTE DINÂMICO E VISÃO GERAL)
    col_f1, col_f2, col_f3, col_f4 = st.columns([1.5, 1.5, 2, 2])
    with col_f1:
        data_gd = st.date_input("🗓️ Data da Gestão Diária", pd.Timestamp.now().date())
    with col_f2:
        # Espaçamento invisível para alinhar o botão com as caixas de texto
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        visao_geral = st.toggle("🌍 Visão Geral", value=False, help="Ative para ver TODAS as pendências. Desative para ver só os atrasados.")
    with col_f3:
        qtd_transf_gd = st.number_input("📦 Qtd Transferências (Hoje)", min_value=0, max_value=20, value=5)
    with col_f4:
        equipes_fisicas_gd = st.number_input("👷 Equipes Físicas no Turno", min_value=1, max_value=30, value=5)

    st.markdown("---")

    # 2. CONEXÃO COM AS BASES DE DADOS (USANDO CREDENCIAIS PARA PLANILHAS PRIVADAS)
    @st.cache_data(ttl=300)
    def puxar_bases_completas_gd():
        # URL da Armazenagem (Ajustada para baixar o CSV da aba específica)
        url_pend = "https://docs.google.com/spreadsheets/d/1Yptk_tfdkuhZCK_saApWQMNynjlaQQeEQjqn4lNcgZk/gviz/tq?tqx=out:csv&sheet=BaseDadosPendArm"

        url_prod = "https://docs.google.com/spreadsheets/d/1bj5vIu8LOIWqaW5evogwQeyrJd9yj1iQkXHbJKvTeks/gviz/tq?tqx=out:csv&sheet=FECHAMENTO"
        url_status = "https://docs.google.com/spreadsheets/d/1NWH9BHXgUmS-6WCQ8AjAHbt8DUHIvgQLRJ8hwUSDC7U/gviz/tq?tqx=out:csv&sheet=Painel%20de%20Controle"

        try: df_p = pd.read_csv(url_prod)
        except: df_p = pd.DataFrame()

        try: df_s = pd.read_csv(url_status)
        except: df_s = pd.DataFrame()

        try: 
            # Se você deixar pública, essa linha aqui vai voar!
            df_pe = pd.read_csv(url_pend)
        except: 
            df_pe = pd.DataFrame()

        return df_p, df_s, df_pe

    with st.spinner("Sincronizando com as credenciais do ROUT..."):
        df_prod, df_status, df_pend = puxar_bases_completas_gd()
        # Usa a base global de transferência que você já tem no app
        df_transf_base = df.copy() if 'df' in globals() else pd.DataFrame()

    # --- 🧠 LÓGICA DE PRODUTIVIDADE (ÚLTIMOS 30 DIAS + REMOÇÃO DE OUTLIERS) ---
    meta_total = 0
    realizado_total = 0
    ganho_pct = 0.0

    total_equipes_gd = equipes_fisicas_gd
    equipes_efetivas = total_equipes_gd

    if not df_prod.empty:
        col_dt_p = next((c for c in df_prod.columns if 'DATA' in c.upper()), None)
        if col_dt_p:
            df_prod[col_dt_p] = pd.to_datetime(df_prod[col_dt_p], dayfirst=True, errors='coerce')
            data_fim = pd.Timestamp(data_gd)
            data_inicio = data_fim - pd.Timedelta(days=30)

            df_prod_periodo = df_prod[(df_prod[col_dt_p] >= data_inicio) & (df_prod[col_dt_p] <= data_fim)].copy()

            col_meta = next((c for c in df_prod_periodo.columns if 'META' in c.upper()), None)
            col_real = next((c for c in df_prod_periodo.columns if 'REALIZADO' in c.upper()), None)

            if col_meta and col_real and not df_prod_periodo.empty:
                df_prod_periodo[col_meta] = pd.to_numeric(df_prod_periodo[col_meta].astype(str).str.replace(',', '.'), errors='coerce')
                df_prod_periodo[col_real] = pd.to_numeric(df_prod_periodo[col_real].astype(str).str.replace(',', '.'), errors='coerce')

                df_prod_limpo = df_prod_periodo[(df_prod_periodo[col_real] <= 427) & (df_prod_periodo[col_real] >= 10)].copy()

                meta_total = df_prod_limpo[col_meta].sum()
                realizado_total = df_prod_limpo[col_real].sum()

                if realizado_total > 0:
                    fator_produtividade = meta_total / realizado_total
                    ganho_pct = (fator_produtividade - 1) * 100
                    equipes_efetivas = total_equipes_gd * fator_produtividade

    cor_ganho = "#27AE60" if ganho_pct >= 0 else "#E74C3C"
    sinal_ganho = "+" if ganho_pct >= 0 else ""
    texto_saldo = f"📅 Histórico 30 dias (cargas entre 10 e 427 min)"

    # --- 🧠 LÓGICA DE CÁLCULO REAL DO APC ---
    import math
    apc_dia = 0
    base_apc = df_filtrado_op if 'df_filtrado_op' in globals() else (df_transf_base if not df_transf_base.empty else pd.DataFrame())

    if not base_apc.empty and 'Data' in base_apc.columns:
        df_base_dia = base_apc[pd.to_datetime(base_apc['Data']).dt.date == data_gd].copy()
        if not df_base_dia.empty and 'Tempo_APC_Minutos' in df_base_dia.columns:
            soma_minutos_cargas = df_base_dia['Tempo_APC_Minutos'].sum()
            min_transf_fixa = (qtd_transf_gd * 240) if data_gd.weekday() < 5 else 0
            minutos_totais = soma_minutos_cargas + min_transf_fixa
            apc_dia = math.ceil(minutos_totais / 427)

    # CABEÇALHO DE PRODUTIVIDADE
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
        <div style="flex: 1; background-color: #FFFFFF; padding: 15px 20px; border-radius: 10px; border-left: 5px solid #8395A7; box-shadow: 0 4px 6px rgba(0,0,0,0.05); min-width: 200px;">
            <div style="font-size: 12px; font-weight: 800; color: #576574; text-transform: uppercase;">APC - DIA (Equipes Necessárias)</div>
            <div style="font-size: 26px; font-weight: 900; color: #1E272E;">{apc_dia}</div>
        </div>
        <div style="flex: 1; background-color: #FFFFFF; padding: 15px 20px; border-radius: 10px; border-left: 5px solid #00C6FF; box-shadow: 0 4px 6px rgba(0,0,0,0.05); min-width: 200px;">
            <div style="font-size: 12px; font-weight: 800; color: #576574; text-transform: uppercase;">Equipes Disponíveis</div>
            <div style="font-size: 26px; font-weight: 900; color: #0086FF;">{total_equipes_gd}</div>
        </div>
        <div style="flex: 1; background-color: #FFFFFF; padding: 15px 20px; border-radius: 10px; border-left: 5px solid {cor_ganho}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); min-width: 200px;">
            <div style="font-size: 12px; font-weight: 800; color: #576574; text-transform: uppercase;">Ganho Produtivo</div>
            <div style="font-size: 26px; font-weight: 900; color: {cor_ganho};">
                {equipes_efetivas:.1f} <span style="font-size: 14px; vertical-align: middle;">({sinal_ganho}{ganho_pct:.1f}%)</span>
            </div>
            <div style="font-size: 11px; font-weight: 700; color: {cor_ganho}; margin-top: 5px;">{texto_saldo}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================================================
    # --- 🧠 LÓGICA DE PENDÊNCIA DE ARMAZENAGEM (FILTRO RETROATIVO OU GERAL) ---
    # ==========================================================================
    tot_etq_pend, tot_agendas_pend, tot_pecas_pend, pct_agrupada = 0, 0, 0, 0

    if not df_pend.empty:
        df_pend.columns = df_pend.columns.str.strip().str.upper()

        # 🛠️ AJUSTE 1: Converter DT_CONFERENCIA para data
        if 'DT_CONFERENCIA' in df_pend.columns:
            df_pend['DT_CONF_DT'] = pd.to_datetime(df_pend['DT_CONFERENCIA'], errors='coerce').dt.date

            # 💡 A MÁGICA DO BOTÃO: Só corta a data se a "Visão Geral" estiver DESLIGADA
            if not visao_geral:
                df_pend = df_pend[df_pend['DT_CONF_DT'] < data_gd].copy()

        # KPIs após passar (ou não) pelo filtro
        if not df_pend.empty:
            tot_etq_pend = df_pend['NU_ETIQUETA'].nunique() if 'NU_ETIQUETA' in df_pend.columns else 0
            tot_agendas_pend = df_pend['CD_AGENDA'].nunique() if 'CD_AGENDA' in df_pend.columns else 0
            tot_pecas_pend = pd.to_numeric(df_pend['QT_CONFERIDO'], errors='coerce').sum() if 'QT_CONFERIDO' in df_pend.columns else 0

            if tot_etq_pend > 0 and 'TP_RECEBIMENTO' in df_pend.columns:
                qtd_agrupada = df_pend[df_pend['TP_RECEBIMENTO'].astype(str).str.contains('AGRUPADA', na=False, case=False)].shape[0]
                pct_agrupada = (qtd_agrupada / df_pend.shape[0]) * 100

    st.markdown("### 📦 Status de Armazenagem")

    # 💡 Aviso dinâmico na tela para o usuário saber o que está olhando
    if visao_geral:
        st.info("🌍 **Visão Geral ATIVADA:** Exibindo o volume TOTAL (incluindo as cargas conferidas hoje).")
    else:
        st.info(f"⏳ **Visão Retroativa:** Exibindo APENAS o que foi conferido até o dia { (data_gd - pd.Timedelta(days=1)).strftime('%d/%m/%Y') }.")

    # 🟢 AQUI ESTÃO OS KPIS QUE TINHAM SUMIDO!
    st.markdown(f"""
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px;">
        <div style="flex: 1; min-width: 180px; background-color: #FFFFFF; border-left: 5px solid #F39C12; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; color: #576574; font-weight: 800; text-transform: uppercase;">Etiquetas Pendentes</div>
            <div style="font-size: 24px; font-weight: 900; color: #1E272E;">{tot_etq_pend}</div>
            <div style="font-size: 11px; color: #8395A7;">{pct_agrupada:.1f}% Agrupadas / {100-pct_agrupada:.1f}% Normal</div>
        </div>
        <div style="flex: 1; min-width: 180px; background-color: #FFFFFF; border-left: 5px solid #E67E22; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; color: #576574; font-weight: 800; text-transform: uppercase;">Agendas Pendentes</div>
            <div style="font-size: 24px; font-weight: 900; color: #1E272E;">{tot_agendas_pend}</div>
        </div>
        <div style="flex: 1; min-width: 180px; background-color: #FFFFFF; border-left: 5px solid #D35400; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; color: #576574; font-weight: 800; text-transform: uppercase;">Peças Pendentes</div>
            <div style="font-size: 24px; font-weight: 900; color: #1E272E;">{tot_pecas_pend:,.0f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================================================
    # VISÃO 1: 🚀 IMPACTO NA TRANSFERÊNCIA (PRIORIDADES COM PEDIDO)
    # ==========================================================================
    st.markdown("### Prioridade de Armazenagem (Pedidos Travados)")

    if not df_pend.empty:
        if 'MODALIDADE' in df_pend.columns:
            # Filtra apenas o que tem pedido (RTY ou ABA)
            filtro_modalidade = df_pend['MODALIDADE'].astype(str).str.upper().str.contains('RTY|RESLOG', na=False, regex=True)
            df_pedidos = df_pend[filtro_modalidade].copy()

            if not df_pedidos.empty:
                df_prioridade = df_pedidos.groupby(['CD_AGENDA', 'FORNECEDOR']).agg({
                    'NU_ETIQUETA': 'nunique', 
                    'QT_CONFERIDO': 'sum'     
                }).reset_index().rename(columns={
                    'NU_ETIQUETA': 'Etiquetas_com_Pedido',
                    'QT_CONFERIDO': 'Peças_Liberadas'
                })

                df_prioridade = df_prioridade.sort_values(by='Peças_Liberadas', ascending=False)

                col_im1, col_im2 = st.columns([1, 2])
                with col_im1:
                    st.metric("Agendas c/ Pedido Travado", df_prioridade['CD_AGENDA'].nunique())
                    st.metric("Peças C/ Pedido (RTY/RESLOG)", f"{df_prioridade['Peças_Liberadas'].sum():,.0f}")
                with col_im2:
                    st.dataframe(
                        df_prioridade[['CD_AGENDA', 'FORNECEDOR', 'Etiquetas_com_Pedido', 'Peças_Liberadas']],
                        column_config={
                            "CD_AGENDA": "Agenda",
                            "FORNECEDOR": "Fornecedor",
                            "Etiquetas_com_Pedido": "Qtd Etiquetas (RTY/RESLOG)",
                            "Peças_Liberadas": "Peças a Liberar"
                        },
                        hide_index=True, use_container_width=True
                    )
            else:
                st.success("✅ Nenhuma pendência na visão atual possui pedidos (RTY).")
        else:
            st.info("⚠️ Coluna MODALIDADE não encontrada na base.")

    # ==========================================================================
    # VISÃO 2: 📋 LISTA GERAL DE PENDÊNCIAS DE ARMAZENAGEM
    # ==========================================================================
    st.markdown("### 📋 Pendências de Armazenagem")

    if not df_pend.empty:
        # Agrupa tudo que está na base de pendência (respeitando o botão de Visão Geral/Retroativa)
        df_geral_pend = df_pend.groupby(['CD_AGENDA', 'FORNECEDOR']).agg({
            'NU_ETIQUETA': 'nunique',
            'QT_CONFERIDO': 'sum'
        }).reset_index().rename(columns={
            'NU_ETIQUETA': 'Total_Etiquetas',
            'QT_CONFERIDO': 'Total_Peças'
        })

        # Ordena pelas agendas maiores primeiro
        df_geral_pend = df_geral_pend.sort_values(by='Total_Peças', ascending=False)

        st.dataframe(
            df_geral_pend,
            column_config={
                "CD_AGENDA": "Agenda Pendente",
                "FORNECEDOR": "Fornecedor",
                "Total_Etiquetas": "Volume (Etiquetas/Paletes)",
                "Total_Peças": "Peças a Guardar"
            },
            hide_index=True, use_container_width=True
        )
    else:
        st.info("Nenhuma pendência para exibir nesta visão.")

    # ==========================================================================
    # --- 🧠 LÓGICA DE STATUS DA DOCA (PAINEL DE CONTROLE) ---
    # ==========================================================================
    st.markdown("---")
    st.markdown("### 🚚 Status das Agendas na Doca")

    df_status_dia = pd.DataFrame()
    col_dt_s = None

    if not df_status.empty:
        df_status.columns = df_status.columns.astype(str).str.strip().str.upper()
        col_dt_s = next((c for c in df_status.columns if 'DATA AGENDA' in c), None)
        if not col_dt_s: col_dt_s = next((c for c in df_status.columns if 'DATA' in c), None)

        if col_dt_s:
            df_status['Data_Extraida'] = df_status[col_dt_s].astype(str).str.strip().str.split(' ').str[0]
            df_status['Data_Filtro'] = pd.to_datetime(df_status['Data_Extraida'], format='%d/%m/%Y', errors='coerce')
            if df_status['Data_Filtro'].isna().all():
                df_status['Data_Filtro'] = pd.to_datetime(df_status['Data_Extraida'], dayfirst=True, errors='coerce')

            df_status['Data_Filtro'] = df_status['Data_Filtro'].dt.date
            df_status_dia = df_status[df_status['Data_Filtro'] == data_gd].copy()

    mapa_status = {
        'AUSENTE': ('AUSENTE', '#2C3E50'),
        'LANÇAMENTO': ('AG LANÇAMENTO', '#E67E22'),
        'COMERCIAL': ('COMERCIAL', '#C0392B'),
        'P-EXTERNO': ('P-EXTERNO', '#16A085'),
        'DOCA': ('EM DOCA', '#F39C12'),
        'PROCESSO': ('EM PROCESSO', '#2980B9'),
        'OK': ('FINALIZADA', '#27AE60'),
        'DEVOLVIDO': ('DEVOLVIDO', '#8E44AD')
    }

    cards_html = ""
    col_st = next((c for c in df_status_dia.columns if 'STATUS' in str(c).upper()), None)
    col_ag_s = next((c for c in df_status_dia.columns if 'AGENDA' in str(c).upper() and 'WMS' not in str(c).upper()), df_status_dia.columns[0] if not df_status_dia.empty else None)
    col_pc_s = next((c for c in df_status_dia.columns if 'PEÇA' in str(c).upper() or 'PECA' in str(c).upper()), None)

    tot_agendas_status, tot_pecas_status = 0, 0

    if not df_status_dia.empty and col_st:
        for chave, (nome_exibicao, cor) in mapa_status.items():
            df_filtro = df_status_dia[df_status_dia[col_st].astype(str).str.upper().str.contains(chave, na=False)]
            qtd_ag = df_filtro.shape[0] 
            qtd_pc = pd.to_numeric(df_filtro[col_pc_s], errors='coerce').sum() if col_pc_s else 0

            tot_agendas_status += qtd_ag
            tot_pecas_status += qtd_pc

            cards_html += f"""<div style="flex: 1; min-width: 110px; background-color: #FFFFFF; border: 1px solid #E1E8ED; border-radius: 6px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; margin-bottom: 10px;">
<div style="background-color: {cor}; color: #FFFFFF; font-size: 11px; font-weight: bold; padding: 6px 0;">{nome_exibicao}</div>
<div style="display: flex; border-bottom: 1px solid #E1E8ED;">
<div style="flex: 1; padding: 8px 0; border-right: 1px solid #E1E8ED;">
<div style="font-size: 10px; color: #8395A7;">AG.</div>
<div style="font-size: 16px; font-weight: bold; color: #1E272E;">{qtd_ag}</div>
</div>
<div style="flex: 1; padding: 8px 0;">
<div style="font-size: 10px; color: #8395A7;">PEÇAS</div>
<div style="font-size: 16px; font-weight: bold; color: #1E272E;">{qtd_pc:,.0f}</div>
</div>
</div>
</div>"""

    cards_html += f"""<div style="flex: 1; min-width: 110px; background-color: #FFFFFF; border: 1px solid #E1E8ED; border-radius: 6px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; margin-bottom: 10px;">
<div style="background-color: #1E272E; color: #FFFFFF; font-size: 11px; font-weight: bold; padding: 6px 0;">TOTAL</div>
<div style="display: flex; border-bottom: 1px solid #E1E8ED;">
<div style="flex: 1; padding: 8px 0; border-right: 1px solid #E1E8ED;">
<div style="font-size: 10px; color: #8395A7;">AG.</div>
<div style="font-size: 16px; font-weight: bold; color: #1E272E;">{tot_agendas_status}</div>
</div>
<div style="flex: 1; padding: 8px 0;">
<div style="font-size: 10px; color: #8395A7;">PEÇAS</div>
<div style="font-size: 16px; font-weight: bold; color: #1E272E;">{tot_pecas_status:,.0f}</div>
</div>
</div>
</div>"""

    st.markdown(f'<div style="display: flex; gap: 8px; flex-wrap: wrap;">{cards_html.replace(",", ".")}</div><br>', unsafe_allow_html=True)

    # TABELA DETALHADA E FILTRO DE STATUS
    st.markdown("### 🔍 Detalhamento das Agendas na Doca")
    if not df_status_dia.empty and col_st:
        status_unicos = df_status_dia[col_st].dropna().unique().tolist()
        status_selecionados = st.multiselect("Filtrar por Status:", options=status_unicos, default=status_unicos)
        df_exibicao = df_status_dia[df_status_dia[col_st].isin(status_selecionados)]
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma agenda localizada no Painel de Controle para esta data.")
# ==========================================================================
    # 🔍 NOVA VISÃO: PRODUTOS COM RESLOG (VISÃO CONSOLIDADA POR CARGA)
    # ==========================================================================
    st.markdown("---")
    titulo_com_ari("📦 Resumo de Agendas com RESLOG (Restrição Logística)")

    if not df_itens.empty:
        # Padronização da base
        df_reslog = df_itens.copy()
        df_reslog.columns = df_reslog.columns.str.strip().str.upper()
        df_reslog = df_reslog.loc[:, ~df_reslog.columns.duplicated()]

        # Buscador de colunas
        col_agenda = next((c for c in df_reslog.columns if c in ['AGENDA', 'CODAGENDA']), None)
        col_sku = next((c for c in df_reslog.columns if c in ['SKU', 'COMPITEM', 'ITEM', 'CÓDIGO', 'CODIGO']), None)
        col_pecas = next((c for c in df_reslog.columns if c in ['QTD PEÇAS', 'QTAGENDA', 'QTCOMP', 'QTDE']), None)
        col_dt = next((c for c in df_reslog.columns if c in ['DTAGENDA', 'DATA AGENDA', 'DATA']), None)
        col_forn = next((c for c in df_reslog.columns if c in ['FORNE_PRINC', 'FORNECEDOR']), None)
        col_linha = next((c for c in df_reslog.columns if c in ['LINHA', 'LINHAS', 'CATEGORIA']), None)

        if col_dt and 'RESLOG' in df_reslog.columns:
            df_reslog['DATA_FORMATADA'] = pd.to_datetime(df_reslog[col_dt], dayfirst=True, errors='coerce').dt.date
            
            # Filtro: Apenas o que tem RESLOG >= 1 na data selecionada
            df_reslog_filtrado = df_reslog[
                (df_reslog['DATA_FORMATADA'] == data_gd) & 
                (pd.to_numeric(df_reslog['RESLOG'], errors='coerce').fillna(0) >= 1)
            ].copy()

            if not df_reslog_filtrado.empty:
                # 🛡️ Força a coluna a ser número antes de qualquer conta!
                if col_pecas:
                    df_reslog_filtrado[col_pecas] = pd.to_numeric(df_reslog_filtrado[col_pecas], errors='coerce').fillna(0)

                # 1. KPIs GERAIS (Soma total do dia)
                qtd_agendas_reslog = int(df_reslog_filtrado[col_agenda].nunique()) if col_agenda else 0
                qtd_skus_reslog = int(df_reslog_filtrado[col_sku].nunique()) if col_sku else 0
                qtd_pecas_reslog = df_reslog_filtrado[col_pecas].sum() if col_pecas else 0
                vol_pecas_str = f"{qtd_pecas_reslog:,.0f}".replace(",", ".")

                # 3. Renderização dos KPIs (FORMATO COMPACTO)
                st.markdown(f"""
                <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px;">
                    <div style="flex: 1; min-width: 180px; background-color: #FFFFFF; border-left: 5px solid #E67E22; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="font-size: 11px; color: #576574; font-weight: 800; text-transform: uppercase;">Agendas Impactadas</div>
                        <div style="font-size: 24px; font-weight: 900; color: #1E272E;">{qtd_agendas_reslog}</div>
                        <div style="font-size: 11px; color: #8395A7;">Total de veículos</div>
                    </div>
                    <div style="flex: 1; min-width: 180px; background-color: #FFFFFF; border-left: 5px solid #3498DB; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="font-size: 11px; color: #576574; font-weight: 800; text-transform: uppercase;">Total de SKUs</div>
                        <div style="font-size: 24px; font-weight: 900; color: #1E272E;">{qtd_skus_reslog}</div>
                        <div style="font-size: 11px; color: #8395A7;">Itens c/ restrição</div>
                    </div>
                    <div style="flex: 1; min-width: 180px; background-color: #FFFFFF; border-left: 5px solid #9B59B6; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="font-size: 11px; color: #576574; font-weight: 800; text-transform: uppercase;">Volume de Peças</div>
                        <div style="font-size: 24px; font-weight: 900; color: #1E272E;">{vol_pecas_str}</div>
                        <div style="font-size: 11px; color: #8395A7;">Físico total</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 4. TABELA AGRUPADA (Simplificada)
                st.write("**Detalhamento de Cargas com Restrição:**")
                
                # Definimos as colunas para o agrupamento
                group_cols = [c for c in [col_agenda, col_forn, col_linha] if c]
                
                if group_cols:
                    # Agrupamos os dados
                    df_resumo_cargas = df_reslog_filtrado.groupby(group_cols).agg({
                        col_sku: 'nunique', # Conta quantos itens diferentes
                        col_pecas: 'sum'    # Soma as peças totais da carga
                    }).reset_index()

                    # Renomeia colunas para a exibição ficar profissional
                    novos_nomes = ['Agenda', 'Fornecedor', 'Linha/Categoria'][:len(group_cols)] + ['Qtd SKUs', 'Total Peças']
                    df_resumo_cargas.columns = novos_nomes
                    
                    st.dataframe(
                        df_resumo_cargas.sort_values(by='Total Peças', ascending=False),
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.success(f"✅ Nenhuma restrição RESLOG identificada para o dia {data_gd.strftime('%d/%m/%Y')}.")
        else:
            st.error("⚠️ Estrutura de colunas (DTAGENDA/RESLOG) não encontrada na base.")
    else:
        st.info("Aguardando carregamento da base de Itens para verificar RESLOG.")
