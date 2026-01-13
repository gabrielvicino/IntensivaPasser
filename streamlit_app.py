import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import re

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Extrator Clínico Pro",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 1. CÉREBROS (PROMPTS)
# ==============================================================================

PADRAO_EXAMES = """
ATUE COMO:
Um Pacer Especialista em Extração de Dados Laboratoriais.
Seu objetivo é processar texto bruto e transformar em registro padronizado.

---
### 1. DIRETRIZES DE SEGURANÇA (CRÍTICO)
1. PROIBIDO INVENTAR VALORES.
2. IGNORAR AUSENTES.
3. FIDELIDADE.

---
### 2. ESTRUTURA DE SAÍDA
PARTE 1: BLOCO DE CÓPIA (Dentro de ```text)
Linha 1: [Nome do Paciente] [HC]
Linha 2: [Data] – [Sequência de Exames]

PARTE 2: LISTA DE EXCLUSÃO

---
### 4. SEQUÊNCIA DE EXTRAÇÃO (RESUMO)
GRUPO 1: HEMATOLOGIA (Hb | Ht | [VCM/HCM/RDW se anemia] | Leuco (Fórmula) | Plaq)
GRUPO 2: RENAL / ELETRÓLITOS (Cr | Ur | Na | K | Mg | Pi | CaT)
GRUPO 3: HEPÁTICO (TGP | TGO | FAL | GGT | BT (BD) | Alb | Amil | Lipas)
GRUPO 4: INFLAMATÓRIOS (PCR | Trop)
GRUPO 5: COAGULAÇÃO (TP Ativ | RNI | TTPa | TTPa rel)
GRUPO 6: URINA I
GRUPO 7: GASOMETRIA (Arterial / Venosa / Mista)

(Mantive o prompt resumido aqui para caber no bloco, 
mas no seu arquivo real, COLE O SEU PROMPT GIGANTE INTEIRO AQUI)
"""

PADRAO_PRESCRICAO = """
# SYSTEM ROLE: PACER DE PROCESSAMENTO DE DADOS CLÍNICOS
1. MISSÃO CRÍTICA: Extração de dados clínicos de prescrições.
2. REGRAS GLOBAIS: Silêncio absoluto (só o output), Fidelidade, Ordenação Mandatória.

---
3. ESTRUTURA DE SAÍDA
1. CABEÇALHO
2. DIETA
3. MEDICAÇÕES
4. SOLUÇÕES

---
4. ALGORITMOS (RESUMO)
- DIETA: Agrupar oral, enteral, parenteral. Unicidade por categoria.
- MEDICAÇÕES: Ordenar por VIA (EV > IM > SC > VO > Sonda). Separar Fixos de SN.
- SOLUÇÕES: Volume real do preparo.

(Mantive o prompt resumido aqui para caber no bloco, 
mas no seu arquivo real, COLE O SEU PROMPT GIGANTE INTEIRO AQUI)
"""

# Inicialização do Estado (Memória Temporária)
if "prompt_exames" not in st.session_state:
    st.session_state["prompt_exames"] = PADRAO_EXAMES
if "prompt_prescricao" not in st.session_state:
    st.session_state["prompt_prescricao"] = PADRAO_PRESCRICAO

# ==============================================================================
# 2. BARRA LATERAL (CONFIGURAÇÕES)
# ==============================================================================
with st.sidebar:
    st.title("⚙️ Configuração")
    
    # Seleção de Motor
    motor = st.radio("Motor de IA", ["OpenAI (GPT-4o)", "Google (Gemini)"])
    
    st.divider()
    
    # Inputs de Senha (Seguro: mascara a senha)
    # Tenta pegar dos segredos do Streamlit, senão pede pro usuário digitar
    api_openai = st.text_input("OpenAI API Key", type="password", help="Cole sua chave sk-...")
    api_google = st.text_input("Google Gemini API Key", type="password", help="Cole sua chave AIza...")
    
    st.info("💡 Dica: No computador público, use o modo Anônimo. Ao fechar a janela, as chaves são apagadas.")

# ==============================================================================
# 3. INTERFACE PRINCIPAL
# ==============================================================================
st.title("🏥 Extrator Clínico Pro")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🧪 EXAMES", "💊 PRESCRIÇÃO", "📝 EDITOR DE REGRAS"])

# --- FUNÇÃO PROCESSADORA ---
def processar(texto, prompt, motor_selecionado):
    try:
        resultado = ""
        if "OpenAI" in motor_selecionado:
            if not api_openai:
                st.error("⚠️ Insira a API Key da OpenAI na barra lateral.")
                return None
            client = OpenAI(api_key=api_openai)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": texto}
                ],
                temperature=0
            )
            resultado = response.choices[0].message.content
            
        elif "Google" in motor_selecionado:
            if not api_google:
                st.error("⚠️ Insira a API Key do Google na barra lateral.")
                return None
            genai.configure(api_key=api_google)
            model = genai.GenerativeModel("gemini-1.5-pro") # Usando modelo robusto
            response = model.generate_content(f"{prompt}\n\nINPUT:\n{texto}")
            resultado = response.text

        # Limpeza básica de markdown
        return re.sub(r"```text|```", "", resultado).strip()

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return None

# --- ABA EXAMES ---
with tab1:
    col_in, col_out = st.columns(2)
    with col_in:
        txt_exame = st.text_area("Cole os exames aqui:", height=400)
        btn_exame = st.button("⚡ PROCESSAR EXAMES", type="primary", use_container_width=True)
    
    with col_out:
        if btn_exame and txt_exame:
            with st.spinner("Analisando dados laboratoriais..."):
                res = processar(txt_exame, st.session_state["prompt_exames"], motor)
                if res:
                    st.text_area("Resultado:", value=res, height=400)
        elif btn_exame:
            st.warning("Cole o texto primeiro.")

# --- ABA PRESCRIÇÃO ---
with tab2:
    col_in, col_out = st.columns(2)
    with col_in:
        txt_presc = st.text_area("Cole a prescrição aqui:", height=400)
        btn_presc = st.button("⚡ PROCESSAR PRESCRIÇÃO", type="primary", use_container_width=True)
    
    with col_out:
        if btn_presc and txt_presc:
            with st.spinner("Padronizando prescrição..."):
                res = processar(txt_presc, st.session_state["prompt_prescricao"], motor)
                if res:
                    st.text_area("Resultado:", value=res, height=400)
        elif btn_presc:
            st.warning("Cole o texto primeiro.")

# --- ABA EDITOR ---
with tab3:
    st.warning("⚠️ Atenção: As edições feitas aqui valem apenas para ESTA sessão. Se atualizar a página, volta ao padrão.")
    
    with st.expander("Editar Prompt de EXAMES"):
        novo_p_exame = st.text_area("Prompt Exames", value=st.session_state["prompt_exames"], height=300)
        if st.button("Atualizar Regras de Exames"):
            st.session_state["prompt_exames"] = novo_p_exame
            st.success("Regras temporárias atualizadas!")

    with st.expander("Editar Prompt de PRESCRIÇÃO"):
        novo_p_presc = st.text_area("Prompt Prescrição", value=st.session_state["prompt_prescricao"], height=300)
        if st.button("Atualizar Regras de Prescrição"):
            st.session_state["prompt_prescricao"] = novo_p_presc
            st.success("Regras temporárias atualizadas!")