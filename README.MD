\# 🏥 Extrator Clínico Pro



\[!\[Streamlit App](https://static.streamlit.io/badges/streamlit\_badge\_black\_white.svg)](https://share.streamlit.io/)



Uma ferramenta de auxílio à decisão clínica e produtividade para médicos intensivistas. O \*\*Extrator Clínico Pro\*\* utiliza Modelos de Linguagem Grande (LLMs) para processar, limpar e padronizar textos brutos de prontuários eletrônicos.



\## 🚀 Funcionalidades



\* \*\*🧪 Padronização de Exames:\*\* Converte texto colado (PDF/OCR) em uma linha de evolução padronizada (Ex: `Hb 12 | Leuco 10.000...`), removendo unidades desnecessárias e filtrando o que importa.

\* \*\*💊 Organização de Prescrições:\*\* Recebe uma lista desordenada de medicações e as reorganiza por via de administração e prioridade (EV > Oral > Sonda), separando Dieta, Antibióticos e Soluções.

\* \*\*🧠 Multi-Motor:\*\* Suporte para \*\*OpenAI (GPT-4o)\*\* e \*\*Google (Gemini 1.5 Pro)\*\*.

\* \*\*🔒 Privacy-First:\*\* Nenhuma informação é salva em banco de dados. O processamento é volátil (RAM) e os dados somem ao fechar a aba.



\## ⚠️ Aviso Legal e Médico (Disclaimer)



\*\*ESTE SOFTWARE É UMA FERRAMENTA DE SUPORTE E NÃO SUBSTITUI O JULGAMENTO CLÍNICO.\*\*



1\.  \*\*Conferência Obrigatória:\*\* O médico deve \*\*sempre\*\* conferir o resultado gerado pela IA com o documento original. Alucinações (erros de geração) podem ocorrer.

2\.  \*\*Dados Sensíveis:\*\* O usuário é responsável por garantir que não está infringindo regras institucionais ao processar dados de pacientes. Recomenda-se o uso de identificadores anonimizados.

3\.  \*\*Sem Garantias:\*\* O software é fornecido "como está", sem garantias de precisão absoluta.



\## 🛠️ Como Usar (Web)



Não é necessário instalar Python ou bibliotecas.



1\.  Acesse o link da aplicação (Deploy no Streamlit Cloud).

2\.  Na barra lateral, insira sua \*\*API Key\*\* (OpenAI ou Google).

&nbsp;   \* \*Nota: As chaves não ficam salvas no servidor. Elas são usadas apenas durante a sessão.\*

3\.  Cole o texto bruto na aba correspondente (Exames ou Prescrição).

4\.  Clique em \*\*Processar\*\*.

5\.  Copie o resultado padronizado.



\## 💻 Instalação Local (Opcional)



Se preferir rodar em sua própria máquina:



```bash

\# Clone o repositório

git clone \[https://github.com/SEU\_USUARIO/extrator-clinico.git](https://github.com/SEU\_USUARIO/extrator-clinico.git)



\# Instale as dependências

pip install -r requirements.txt



\# Execute o Streamlit

streamlit run streamlit\_app.py

