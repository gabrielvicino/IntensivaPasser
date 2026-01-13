import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import re

# ==============================================================================
# 0. CONFIGURAÇÃO VISUAL (ESTILO GOOGLE / CLEAN)
# ==============================================================================
st.set_page_config(
    page_title="Intensiva Pacer",
    page_icon="📃",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS para forçar estilo "Google Medical" (Azul #1a73e8 e Branco)
st.markdown("""
<style>
    /* Fundo e Fonte */
    .stApp { background-color: #ffffff; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    
    /* Botões (Azul Google) */
    .stButton > button { 
        background-color: #1a73e8; 
        color: white; 
        border-radius: 6px; 
        border: none; 
        height: 45px; 
        font-weight: 600; 
        font-size: 15px; 
        width: 100%; 
        transition: background-color 0.2s; 
    }
    .stButton > button:hover { background-color: #1557b0; color: white; }
    
    /* Áreas de Texto */
    .stTextArea textarea { 
        background-color: #f8f9fa; 
        border: 1px solid #dadce0; 
        border-radius: 6px; 
        font-family: 'Consolas', 'Courier New', monospace; 
        font-size: 14px; 
    }
    .stTextArea textarea:focus { border-color: #1a73e8; box-shadow: 0 0 0 1px #1a73e8; }
    
    /* Títulos */
    h1, h2, h3 { color: #202124; }
    
    /* Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        background-color: #f1f3f4; 
        border-radius: 5px 5px 0px 0px; 
        color: #5f6368; 
        font-weight: 600; 
    }
    .stTabs [aria-selected="true"] { 
        background-color: #ffffff; 
        color: #1a73e8; 
        border-top: 3px solid #1a73e8; 
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. SEGREDOS E CHAVES
# ==============================================================================
# ATENÇÃO: A chave OpenAI anterior estava dando Erro 401 (Inválida).
# Você DEVE substituir "COLE_SUA_NOVA_CHAVE_AQUI" por uma chave nova gerada em platform.openai.com
KEYS = {
    "google": "AIzaSyAO1P8Vo82k13ubKZ5-qPqJW1DUQRAFLe4",
    "openai": "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" 
}
# Nota: Se a chave acima continuar dando erro 401, é porque ela foi realmente bloqueada pela OpenAI.

# ==============================================================================
# 2. PROMPTS MESTRES (CÉREBROS DA IA) - DO ARQUIVO EXTRATOR_PRO.PY
# ==============================================================================

PADRAO_EXAMES = """
# PROMPT MESTRE - EXTRAÇÃO DE DADOS LABORATORIAIS

ATUE COMO:
Um Pacer Especialista em Extração de Dados Laboratoriais.
Seu objetivo é processar texto bruto (PDF, OCR, fragmentos) e transformá-lo em um registro de evolução médica padronizado e conciso.

---

### 1. DIRETRIZES DE SEGURANÇA (CRÍTICO)
1. PROIBIDO INVENTAR VALORES: Se o dado não consta no texto, não o invente. Não calcule nada (exceto conversão de Leucócitos < 500).
2. IGNORAR AUSENTES: Se um biomarcador ou grupo inteiro não existir no texto, pule-o. Não deixe espaços vazios ou pipes duplos consecutivos.
3. FIDELIDADE: Apenas extraia números e resultados. Não copie textos descritivos ou diagnósticos.

---

### 2. ESTRUTURA DE SAÍDA (LAYOUT RÍGIDO)

A resposta deve ter exatamente duas partes:

PARTE 1: BLOCO DE CÓPIA
O resultado deve vir dentro de um bloco de código `text` (code block).
IMPORTANTE: O conteúdo deve ter obrigatoriamente DUAS LINHAS distintas (use `Enter` / quebra de linha):

Linha 1: [Nome do Paciente] [HC (se disponível)]
Linha 2: [Data DD/MM/AAAA] – [Sequência de Exames]

PARTE 2: LISTA DE EXCLUSÃO
Texto simples listando os nomes dos exames presentes no original que foram ignorados por não estarem na lista alvo (ex: TSH, Colesterol, Sorologias, VPM).

---

### 3. REGRAS DE FORMATAÇÃO E SEPARADORES

1. SEPARADOR PADRÃO ( | ): Use Pipe com espaços (" | ") para separar TODOS os exames individuais e grupos.
2. SEPARADOR INTERNO ( / ): Use Barra com espaços (" / ") EXCLUSIVAMENTE dentro de: Fórmula Leucocitária, URINA I e GASOMETRIA.
3. DECIMAIS: Use Vírgula (padrão PT-BR).
4. UNIDADES: Remova todas (mg/dL, U/L, etc). Mantenha apenas:
   - "%" para: Ht, Fórmula Leucocitária, SatO2, SvO2 e TP Atividade.
   - "s" para: TTPa.

---

### 4. SEQUÊNCIA DE EXTRAÇÃO (ORDEM RÍGIDA)

Extraia os dados na ordem abaixo. Use " | " para separar os itens.

GRUPO 1: HEMATOLOGIA
Ordem: Hb | Ht | [Se Hb < 9,0: VCM | HCM | RDW] | Leuco (Fórmula) | Plaq
- Hb: 1 casa decimal.
- Ht: inteiro + %.
- REGRA CONDICIONAL: Se e somente se Hb < 9,0, inclua VCM, HCM e RDW (inteiros) logo após o Ht. Caso contrário, omita-os.
- Leuco: Ponto para milhar. (Se < 500, multiplique por 1.000).
- Fórmula: ([Se >0: Mielo A% / Meta B% /] Bast X% / Seg Y% / Linf Z% / Mon W% / Eos K% / Bas J%)
  * ATENÇÃO: Se houver Mielócitos ou Metamielócitos positivos (>0), insira-os no início da fórmula (antes de Bastões). Se forem zero ou não citados, omita-os.
- Plaq: Ponto para milhar.

GRUPO 2: RENAL / ELETRÓLITOS
Ordem: Cr | Ur | Na | K | Mg | Pi | CaT
- Cr: 1 casa decimal.
- Ur, Na: Inteiros.
- K, Mg, Pi, CaT: 1 casa decimal.

GRUPO 3: HEPÁTICO
Ordem: TGP | TGO | FAL | GGT | BT (BD) | Alb | Amil | Lipas
- Enzimas: Inteiros.
- BT (BD): 1 casa decimal. Formato: Total (Direta).
- Alb: 1 casa decimal.

GRUPO 4: INFLAMATÓRIOS
Ordem: PCR | Trop
- PCR: Inteiro.
- Trop: 2 casas decimais.

GRUPO 5: COAGULAÇÃO
Ordem: TP Ativ | RNI | TTPa | TTPa rel
- TP Ativ: Número + s. (RNI: 1 casa decimal). Ex TP 12,2s (1,4)
- TTPa: Número + s. (rel: 1 casa decimal). Ex TTPA 10,3s (0,9)

GRUPO 6: URINA I (EAS)
Se houver dados, use esta string fixa exata com barras internas:
Urn: Leu Est: [Val] / Nit: [Val] / Leuco [Val] / Hm : [Val] / Prot: [Val] / Cet: [Val] / Glic: [Val]
- Use "Pos" (com cruzes se houver, ex: "Pos ++") ou "Neg".

GRUPO 7: GASOMETRIA 
Identifique se a gasometria é ARTERIAL, VENOSA ou MISTA (Ambas). Use barras "/" para separar os itens DENTRO do bloco da gasometria.

A. SE ARTERIAL: Prefixo: "Gas Art" Ordem: pH / pCO2 / pO2 / HCO3 / BE / SatO2 / Lac / AG / Cl / Na / K / Cai

Formatação:
pH, Cai: 2 casas decimais.

pCO2, pO2, HCO3, AG, Cl, Na: Inteiros.

BE: 1 casa decimal (Obrigatório manter sinal positivo "+" ou negativo "-").

SatO2: Inteiro + %.

Lac, K: 1 casa decimal.

B. SE VENOSA: Prefixo: "Gas Ven" Ordem: pH / pCO2 / HCO3 / BE / SvO2 / Lac / AG / Cl / Na / K / Cai

Nota: Substitua SatO2 por SvO2. Omita pO2.

Formatação: Idêntica à arterial.

C. SE MISTA (Duas gasometrias no mesmo input): Ordem: [Bloco Arterial Completo] | [Bloco Venoso Completo]

Separe os dois blocos com o pipe " | "

---

### 5. GABARITO DE CENÁRIOS (SIGA ESTES MODELOS)

Use os exemplos abaixo como molde estrito para a formatação final, respeitando a quebra de linha entre o Nome e a Data.

CENÁRIO A: APENAS GASOMETRIA ARTERIAL
(Exemplo: Hb < 9,0 com índices. Sem Mielo/Meta. Gaso Arterial Completa)
```text
Carlos Eduardo Souza 9876543/2
29/12/2025 – Hb 8,0 | Ht 24% | VCM 82 | HCM 27 | RDW 15 | Leuco 12.500 (Bast 2% / Seg 68% / Linf 20% / Mon 6% / Eos 4% / Bas 0%) | Plaq 150.000 | Cr 1,2 | Ur 45 | Na 138 | K 4,0 | Mg 1,8 | Pi 3,5 | CaT 8,9 | TGP 32 | TGO 35 | FAL 80 | GGT 45 | BT 1,0 (0,3) | Alb 3,8 | Amil 65 | Lipas 40 | PCR 12 | Trop 0,01 | TP Ativ 14,2s (1,1) | TTPa 30s (1,0) | Urn: Leu Est: Neg / Nit: Neg / Leuco 4.000 / Hm : 2.000 / Prot: Neg / Cet: Neg / Glic: Neg | Gas Art pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15
LISTA DE EXCLUSÃO: Colesterol Total, HDL, LDL, Triglicérides, TSH, T4 Livre, VPM, CHCM, Densidade (Urina), pH (Urina).

CENÁRIO B: APENAS GASOMETRIA VENOSA (Exemplo: Hb < 9,0. Com Mielócitos e Metamielócitos positivos. Gaso Venosa com SvO2)

Plaintext

Carlos Eduardo Souza 9876543/2
29/12/2025 – Hb 8,0 | Ht 24% | VCM 80 | HCM 26 | RDW 18 | Leuco 14.500 (Mielo 2% / Meta 3% / Bast 4% / Seg 75% / Linf 10% / Mon 6% / Eos 0% / Bas 0%) | Plaq 450.000 | Cr 2,8 | Ur 95 | Na 135 | K 5,2 | Mg 1,9 | Pi 4,5 | CaT 8,2 | TGP 40 | TGO 45 | FAL 110 | GGT 55 | BT 0,8 (0,2) | Alb 2,1 | Amil 50 | Lipas 35 | PCR 180 | Trop 0,02 | TP Ativ 12,3s (1,2) | TTPa 34s (1,1) | Urn: Leu Est: Pos ++ / Nit: Pos / Leuco >100 / Hm : 50 / Prot: Pos ++++ / Cet: Neg / Glic: Neg | Gas Ven pH 7,25 / pCO2 50 / HCO3 18 / BE -6,1 / SvO2 65% / Lac 2,5 / AG 12 / Cl 105 / Na 135 / K 5,2 / Cai 1,05
LISTA DE EXCLUSÃO: Colesterol Total, HDL, LDL, Triglicérides, TSH, T4 Livre, VPM, CHCM, Densidade (Urina), pH (Urina).

CENÁRIO C: GASOMETRIA MISTA (DUAS GASOMETRIAS) (Exemplo: Bloco Arterial completo | Pipe separador | Bloco Venoso resumido)

Plaintext

Carlos Eduardo Souza 9876543/2
29/12/2025 – Hb 8,0 | Ht 24% | VCM 82 | HCM 27 | RDW 15 | Leuco 12.500 (Bast 2% / Seg 68% / Linf 20% / Mon 6% / Eos 4% / Bas 0%) | Plaq 150.000 | Cr 1,2 | Ur 45 | Na 138 | K 4,0 | Mg 1,8 | Pi 3,5 | CaT 8,9 | TGP 32 | TGO 35 | FAL 80 | GGT 45 | BT 1,0 (0,3) | Alb 3,8 | Amil 65 | Lipas 40 | PCR 12 | Trop 0,01 | TP Ativ 30,2s (1,1) | TTPa 30s (1,0) | Urn: Leu Est: Neg / Nit: Neg / Leuco 4.000 / Hm : 2.000 / Prot: Neg / Cet: Neg / Glic: Neg | Gas Art pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,0 / SatO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15 | Gas Ven pCO2 45 / SvO2 70%
LISTA DE EXCLUSÃO: Colesterol Total, HDL, LDL, Triglicérides, TSH, T4 Livre, VPM, CHCM, Densidade (Urina), pH (Urina).
"""

PADRAO_PRESCRICAO = """
# SYSTEM ROLE: PACER DE PROCESSAMENTO DE DADOS CLÍNICOS

## 1. MISSÃO CRÍTICA
Você é uma engine de extração de dados clínicos de alta precisão. Sua função é receber texto bruto e desorganizado de prescrições clínicas (medicações, dieta e soluções) e convertê-lo em uma SAÍDA ESTRUTURADA E PADRONIZADA (Plaintext).

## 2. REGRAS GLOBAIS DE CONTROLE (ZERO TOLERANCE)
1.  **SILÊNCIO ABSOLUTO:** Não gere nenhum texto de conversação (intro, conclusão, observações). Apenas o bloco de código ` ```text `.
2.  **FIDELIDADE DE CONTEÚDO:** É PROIBIDO inventar, alucinar ou inferir medicamentos/doses não presentes. É PROIBIDO omitir itens de Dieta, Medicação ou Solução. Apenas é PERMITIDO extração de dados e limpeza de formatação.
3.  **ORDENAÇÃO É MANDATÓRIA:** Uma lista fora da ordem estrita de vias é considerada um erro fatal. Processe a lista inteira na memória antes de gerar a saída.

---

## 3. ESTRUTURA DE SAÍDA (HIERARQUIA ESTRITA)
A resposta deve seguir esta ordem exata, separada por linhas em branco:
1.  CABEÇALHO
2.  (Linha em branco)
3.  DIETA
4.  (Linha em branco)
5.  MEDICAÇÕES (Ordenadas por lógica mestre)
6.  (Linha em branco)
7.  SOLUÇÕES
8.  (Linha em branco)

> A numeração é **contínua e global**, iniciando em 1 no bloco DIETA e continuando sequencialmente até SOLUÇÕES.

---

## 4. ALGORITMOS DE EXTRAÇÃO E FORMATAÇÃO

### A. CABEÇALHO
Formate os dados extraídos conforme o template abaixo.
* **Nome:** Title Case.
* **Idade:** Apenas o número.
* **Datas:** DD/MM/AAAA.
**Template:**
`[Nome Completo] - [Idade] anos - [Registro] - [Leito]`
`Prescrição: [Data Início] até [Data Fim]`

### B. BLOCO DIETA (E CUIDADOS NUTRICIONAIS)
**Título:** `DIETA`
**Lógica de Inclusão:**
1.  Todos os itens originais da seção "Dieta".
2.  **MOVER PARA CÁ:** Suplementos Orais/Enterais e NPP (Nutrição Parenteral), mesmo que estejam em outras seções no texto bruto.
3.  **FILTRO DE CUIDADOS:** Incluir APENAS cuidados de hidratação (Ex: "Água livre", "Lavagem de sonda"). Ignorar outros cuidados.

**Regras de Texto e Quebra:**
* **REGRA DE SPLIT:** Se a descrição da dieta contiver múltiplas características distintas (ex: Tipo da fórmula E Consistência/Textura), separe-as em linhas numeradas diferentes.
* Substitua ponto e vírgula `;` no meio da descrição por ` para ` (Ex: "Diabetes; Hipossódica" -> "Diabetes para Hipossódica").

REGRA DE UNICIDADE (DIETA):
Pode existir NO MÁXIMO um item de cada categoria abaixo no bloco DIETA:

- Dieta Oral
- Hidratação Oral
- Suplemento (Oral ou Enteral)
- Dieta Enteral
- Dieta Parenteral (NPP)

Se o texto bruto contiver múltiplos itens da MESMA categoria:
- Consolidar em um único item quando forem complementares
- Priorizar a descrição mais específica e completa
- Descartar duplicações evidentes

A violação desta regra (mais de um item final da mesma categoria)
é considerada ERRO CRÍTICO de processamento.

**Algoritmo de Ordenação (Hierarquia Nutricional):**
1.  Dieta Oral
2.  Suplemento Oral
3.  Hidratação Oral
4.  Dieta Enteral
5.  Suplemento Enteral
6.  Dieta Parenteral (NPP)

**EXEMPLO DE EXTRAÇÃO (DIETA):**
*Input:* "2. Enteral Oligomerica 1.2kcal. 3. NPP Adulto 1300kcal. 4. Água livre 200ml. 5. Oral se acordado para disfagia"
*Output:*
`1. Oral para disfagia`
`1. Água livre 200ml`
`2. Enteral oligomérica 1200kcal`
`3. NPP adulto 1300kcal`


### C. BLOCO MEDICAÇÕES (KERNEL DE ORDENAÇÃO)
**Título:** `MEDICAÇÕES`
**ATENÇÃO CRÍTICA:** Não imprima os medicamentos na ordem de leitura. Você deve ler todos, armazenar e aplicar o algoritmo abaixo antes de escrever.

#### PASSO 1: PADRONIZAÇÃO DE DADOS
* **Nome:** Fármaco + Concentração Comercial (Ex: Morfina 10mg/ml Inj / Sinvastatina 20mg Cp).
* **Dose Prescrita:** A quantidade efetiva que o paciente vai tomar (Ex: 40mg; 1 amp; 40gts). **NUNCA** confunda a concentração do frasco com a dose prescrita no final da linha.
* **Unidades:** Converta para minúsculo (amp, cmp, cap, ui, gts).
* **Via (Mapeamento Obrigatório):**
    * EV -> **Endovenoso**
    * IM -> **Intramuscular**
    * SC -> **Subcutâneo**
    * VO -> **Oral**
    * Inalatória/Nebulização -> **Inalatória**
    * SNG/SNE/GTT -> **Por Sonda** ou **Enteral**
    * VR -> **Retal**

#### PASSO 2: LÓGICA DE FREQUÊNCIA
* **CASO A (Fixos):** Horários (4/4h, 6/6h) ou Diários (1x ao dia).
    * **REGRA 24H:** Converta "24/24h" para "**1 vez ao dia**".
    * *Separador:* **" x "**
* **CASO B (SN):** ACM, SOS, Se necessário.
    * *Separador:* **" ; "**

#### PASSO 3: ALGORITMO DE CLASSIFICAÇÃO (SORTING)
Organize a lista final seguindo rigorosamente esta hierarquia de clusterização.

**GRUPO 1: MEDICAMENTOS FIXOS (Topo)**
*Dentro deste grupo, ordene estritamente por VIA:*
1.  **Endovenoso** (Prioridade Máxima)
2.  **Intramuscular**
3.  **Subcutâneo**
4.  **Oral**
5.  **Por Sonda / Enteral**
6.  **Retal**
7.  **Outras** (Tópico, Inalatória)

**GRUPO 2: MEDICAMENTOS SE NECESSÁRIO (Fundo)**
*Dentro deste grupo, ordene estritamente por VIA:*
1.  **Endovenoso**
2.  **Intramuscular**
3.  **Subcutâneo**
4.  **Oral / Sonda**
5.  **Retal**
6.  **Outras**

*(Desempate dentro da mesma via e grupo: Ordem Alfabética)*

**Formato Final da Linha (TRAVA DE SEGURANÇA):**
`N. [Nome Fármaco + Conc Comercial]; [Dose Prescrita]; [Via Padronizada]; [Dose Prescrita] [Separador] [Frequência]`

**EXEMPLO DE EXTRAÇÃO (MEDICAÇÕES):**
*Input Bruto Desordenado:*
- Sinvastatina 20mg (Dose: 40mg, Oral, 24/24h)
- Dipirona 1g (Dose: 1g, EV, Se febre)
- Amicacina 500mg (Dose: 1AMP, EV, 24/24h)
- Morfina (Dose: 2mg, EV, Se dor)

*Output Ordenado Corretamente:*
`1. Amicacina 500mg; 1 amp; Endovenoso; 1 amp x 1 vez ao dia` (EV Fixo Primeiro)
`2. Sinvastatina 20mg; 40 mg; Oral; 40 mg x 1 vez ao dia` (Oral Fixo Depois. Nota: Dose 40mg repetida)
`3. Dipirona 1g; 1 g; Endovenoso; Se Necessário` (EV SN Primeiro)
`4. Morfina; 2 mg; Endovenoso; Se Necessário` (EV SN Segundo)

### D. BLOCO SOLUÇÕES
**Título:** `SOLUÇÕES`
**Conteúdo:** Soros, Diluentes, Infusões Contínuas. (NPP vai para Dieta).
**Ordenação:** Seguir a mesma lógica das Medicações (Fixos > SN).
**Sanitização de Texto:**
* Combine os componentes usando "+".
* **REGRA DE VOLUME REAL (CRÍTICA):** Se houver dois volumes listados para o diluente (ex: "Cloreto de Sodio 250mL INJ 245 mL"), você deve escolher **SEMPRE** o volume específico de preparo (o número "quebrado" ou menor, ex: 245 mL) e **IGNORAR** o volume nominal do frasco (ex: 250 mL).
* Limpeza: Remova "Base", "INJ", "Solução". Use "ml" minúsculo.

**EXEMPLO DE EXTRAÇÃO (SOLUÇÕES):**
*Input:* "Norepinefrina 4mg/4mL Inj 4 AMP + Cloreto de Sodio 0,9% 250mL INJ 234 mL"
*Output:*
`1. Norepinefrina 4 amp + Cloreto de Sodio 0,9% 234 ml; Endovenoso; A Critério Médico`

### E. FILTRAGEM (O QUE IGNORAR)
Remova impiedosamente:
* Sinais vitais, Peso, Controle de Acesso, Identificação de médicos, Cabeçalhos de página, Textos de rodapé administrativos.
* Qualquer "CUIDADO" que não seja de hidratação/nutrição.

---

## 5. EXEMPLO MESTRE DE REFERÊNCIA (PRESCRIÇÃO COMPLETA)
Use este exemplo como prova real de como aplicar todas as regras simultaneamente.

Exemplo 1- 

José Claudio Ruy - 74 anos - 1570869/3 - 643A
Prescrição: 09/01/2026 até 10/01/2026

DIETA
1. Branda hipossódica e constipante
2. Água livre pela SNE 500 ml/dia
3. Enteral hiperproteica 600 kcal
4. NPP Individualizada 600 kcal

MEDICAÇÕES
5. Dipirona 1g Inj; 2 g; Endovenoso; 2 g x 6/6h
6. Sacarato de Hidróxido Férrico 100mg Inj; 200 mg; Endovenoso; 200 mg x a cada 2 dias
7. Morfina 10mg/ml Inj; 3 mg; Endovenoso; 3 mg x 1 vez ao dia
8. Omeprazol 20mg Cap; 40 mg; Oral; 40 mg x 1 vez ao dia

SOLUÇÕES
9. Norepinefrina 4 amp + Cloreto de Sodio 0,9% 234 ml; Endovenoso; A Critério Médico
10. Cloreto de Sodio 0,9% 500 ml; Endovenoso; Se Necessário

Exemplo 2- 

Sergio Ricardo De Oliveira - 48 anos - 1567537/7 - Leito 631C
Prescrição: 04/12/2025 até 05/12/2025

DIETA
1. Dieta oral para encefalopatia hepática
2. Dieta enteral oligomérica 300kcal

MEDICAÇÕES
3. Fluconazol 200mg Inj; 400 mg; Endovenoso; 400 mg x a cada 3 dias

Exemplo 3- 

Maria Aparecida De Lanes - 75 anos - 1270983/0 - 449B
Prescrição: 04/12/2025 até 05/12/2025

DIETA
1. Dieta oral liquidificada para diabetes

MEDICAÇÕES
2. Escopolamina 20mg/ml Inj; 20 mg; Endovenoso; 20 mg x 12/12h
3. Furosemida 20mg Inj; 2 amp; Endovenoso; 2 amp x 8/8h
4. Piperacilina 4g + Tazobactam 0,5g Inj; 2,25 g; Endovenoso; 2,25 g x 8/8h
5. Sacarato de Hidróxido Férrico 100mg Inj; 2 amp; Endovenoso; 2 amp x a cada 2 dias
6. Heparina 5.000ui; 5.000 ui; Subcutâneo; 5.000 ui x 12/12h
7. Hidralazina 25mg Cp; 25 mg; Oral; 25 mg x 8/8h
8. Levotiroxina 25mcg Cp; 25 mcg; Oral; 25 mcg x 1 vez ao dia
9. Simeticona 75mg/ml Gts; 40 gts; Oral; 40 gts x 8/8h
10. Sinvastatina 20mg Cp; 40 mg; Oral; 40 mg x 1 vez ao dia
11. Ácido Acetilsalicílico 100mg Cp; 100 mg; Por Sonda; 100 mg x 1 vez ao dia
12. Ipratrópio 0,25mg/ml Gts; 40 gts; Inalatória; 40 gts x 12/12h
13. Dipirona 1g Inj; 1 g; Endovenoso; Se Necessário
14. Glicose 50% Inj; 20 ml; Endovenoso; Se Necessário
15. Norepinefrina 4mg/4ml Inj; 4 amp; Endovenoso; Se Necessário
16. Ondansetrona 8mg Inj; 8 mg; Endovenoso; Se Necessário
17. Piperacilina 4g + Tazobactam 0,5g Inj; 0,75 g; Endovenoso; Se Necessário

SOLUÇÕES
18. Norepinefrina 4 amp + Glicose 5% 250 ml; Endovenoso; A Critério Médico
"""

# ==============================================================================
# 3. GESTÃO DE ESTADO (MEMÓRIA VOLÁTIL)
# ==============================================================================
if "prompt_exames" not in st.session_state:
    st.session_state["prompt_exames"] = PADRAO_EXAMES
if "prompt_prescricao" not in st.session_state:
    st.session_state["prompt_prescricao"] = PADRAO_PRESCRICAO

# Armazenar resultados para não sumir ao trocar de aba
if "out_exame" not in st.session_state: st.session_state["out_exame"] = ""
if "out_presc" not in st.session_state: st.session_state["out_presc"] = ""

# ==============================================================================
# 4. LÓGICA DE PROCESSAMENTO
# ==============================================================================
def processar(prompt_mestre, texto_entrada, motor_escolhido):
    if not texto_entrada.strip():
        st.warning("⚠️ O campo de entrada está vazio.")
        return None
    
    resultado = ""
    try:
        if motor_escolhido == "OpenAI (GPT-4o)":
            if not KEYS["openai"]:
                st.error("❌ Chave OpenAI não configurada ou vazia.")
                return None
            
            # ATENÇÃO: Se der erro 401, a chave abaixo está REVOGADA/BLOQUEADA.
            client = OpenAI(api_key=KEYS["openai"])
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt_mestre},
                    {"role": "user", "content": texto_entrada}
                ],
                temperature=0
            )
            resultado = response.choices[0].message.content

        elif motor_escolhido == "Google (Gemini)":
            if not KEYS["google"]:
                st.error("❌ Chave Google não configurada.")
                return None
            
            genai.configure(api_key=KEYS["google"])
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config={"temperature": 0}
            )
            response = model.generate_content(f"{prompt_mestre}\n\nINPUT:\n{texto_entrada}")
            resultado = response.text
        
        # Limpeza do Markdown
        limpo = re.sub(r"```text|```", "", resultado).strip()
        return limpo

    except Exception as e:
        # Mostra erro amigável na tela
        if "401" in str(e):
             st.error("🚨 ERRO DE CHAVE API (401): A senha da OpenAI está incorreta, expirada ou foi bloqueada. Você precisa gerar uma nova em platform.openai.com e colar no código.")
        else:
             st.error(f"Erro no processamento: {str(e)}")
        return None

# ==============================================================================
# 5. INTERFACE (FRONT-END)
# ==============================================================================

# Cabeçalho e Barra Lateral
with st.sidebar:
    st.title("⚙️ Ajustes")
    motor_selecionado = st.radio("Motor IA", ["OpenAI (GPT-4o)", "Google (Gemini)"], index=0)
    st.info("ℹ️ Modo Profissional Ativado")
    st.divider()
    if st.button("Limpar Tudo"):
        st.session_state["out_exame"] = ""
        st.session_state["out_presc"] = ""
        st.rerun()

st.title("🏥 Extrator Clínico Pro")

# Abas Principais
tab_exames, tab_prescricao, tab_editor = st.tabs(["🧪 EXAMES", "💊 PRESCRIÇÃO", "📝 EDITOR DE REGRAS"])

# --- ABA EXAMES ---
with tab_exames:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📥 Entrada")
        # ADICIONADO key="in_exame" PARA EVITAR CONFLITO
        txt_exame = st.text_area("Cole os exames aqui:", height=500, key="in_exame", label_visibility="collapsed")
        btn_proc_exame = st.button("⚡ PROCESSAR EXAMES", type="primary", key="btn_proc_exame")
    
    with col2:
        st.markdown("### 📤 Saída Padronizada")
        if btn_proc_exame:
            with st.spinner("Processando dados laboratoriais..."):
                res = processar(st.session_state["prompt_exames"], txt_exame, motor_selecionado)
                if res:
                    st.session_state["out_exame"] = res
                    st.success("Concluído!")
        
        # ADICIONADO key="out_exame_txt" PARA EVITAR O ERRO DUPLICATE ID
        st.text_area("Resultado:", value=st.session_state["out_exame"], height=500, key="out_exame_txt", label_visibility="collapsed")

# --- ABA PRESCRIÇÃO ---
with tab_prescricao:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📥 Entrada")
        # ADICIONADO key="in_presc" PARA EVITAR CONFLITO
        txt_presc = st.text_area("Cole a prescrição aqui:", height=500, key="in_presc", label_visibility="collapsed")
        btn_proc_presc = st.button("⚡ PROCESSAR PRESCRIÇÃO", type="primary", key="btn_proc_presc")
    
    with col2:
        st.markdown("### 📤 Saída Estruturada")
        if btn_proc_presc:
            with st.spinner("Organizando prescrição..."):
                res = processar(st.session_state["prompt_prescricao"], txt_presc, motor_selecionado)
                if res:
                    st.session_state["out_presc"] = res
                    st.success("Concluído!")
        
        # ADICIONADO key="out_presc_txt" PARA EVITAR O ERRO DUPLICATE ID
        st.text_area("Resultado:", value=st.session_state["out_presc"], height=500, key="out_presc_txt", label_visibility="collapsed")

# --- ABA EDITOR ---
with tab_editor:
    st.warning("⚠️ As alterações feitas aqui valem apenas para a sessão atual (memória volátil).")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Regras de EXAMES")
        novo_prompt_exame = st.text_area("Editor Exames", value=st.session_state["prompt_exames"], height=600, key="edit_prompt_exame")
        if st.button("Salvar Regras de Exames", key="btn_save_exame"):
            st.session_state["prompt_exames"] = novo_prompt_exame
            st.toast("Regras de Exames atualizadas!", icon="✅")

    with col2:
        st.subheader("Regras de PRESCRIÇÃO")
        novo_prompt_presc = st.text_area("Editor Prescrição", value=st.session_state["prompt_prescricao"], height=600, key="edit_prompt_presc")
        if st.button("Salvar Regras de Prescrição", key="btn_save_presc"):
            st.session_state["prompt_prescricao"] = novo_prompt_presc
            st.toast("Regras de Prescrição atualizadas!", icon="✅")