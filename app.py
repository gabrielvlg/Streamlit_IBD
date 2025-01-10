import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

# Consultas SQL
queries = {
    "1. Descrição e data das ocorrências de 2024": """
        SELECT Descricao, Data_Da_Ocorrencia
        FROM ocorrencia
        WHERE Data_Da_Ocorrencia > '2023-12-31'
    """,
    "2. Número das ocorrências e fase das operações que são do tipo Voo Privado": """
        SELECT Numero_da_Ocorrencia, Fase_da_Operacao
        FROM operacao
        WHERE Tipo_da_Operacao = 'Voo Privado'
    """,
    "3. Fases e número das ocorrências classificadas como incidentes graves": """
        SELECT O.Numero_da_Ocorrencia, OP.Fase_da_Operacao
        FROM ocorrencia AS O
        NATURAL JOIN operacao AS OP
        WHERE O.Classificacao_da_Ocorrencia = 'Incidente Grave'
    """,
    "4. Código ICAO dos aeródromos de origem, data e classificação das ocorrências de 2024": """
        SELECT V.Aerodromo_de_Origem, O.Data_da_Ocorrencia, O.Classificacao_da_Ocorrencia
        FROM ocorrencia AS O
        NATURAL JOIN voo AS V
        WHERE O.Data_da_Ocorrencia > '2023-12-31' AND V.Aerodromo_de_Origem != 'None'
    """,
    "5. Ocorrências no Aeródromo de Confins (SBCF)": """
        SELECT O.tipo_descricao, O.Data_da_Ocorrencia, O.Classificacao_da_Ocorrencia
        FROM ocorrencia AS O
        NATURAL JOIN voo AS V
        WHERE V.Aerodromo_de_Origem = 'SBCF' OR V.Aerodromo_de_Destino = 'SBCF'
    """,
    "6. Aeródromos de origem sem passageiros ilesos": """
        SELECT DISTINCT V.Aerodromo_de_Origem, O.tipo_descricao
        FROM voo AS V
        NATURAL JOIN ocorrencia AS O
        NATURAL JOIN lesoes_ocorrencia AS LO
        JOIN lesao AS L ON LO.Pessoa_afetada = L.Pessoa_afetada AND LO.Tipo_Lesao = L.Tipo_Lesao
        WHERE NOT EXISTS (
            SELECT 1
            FROM lesoes_ocorrencia AS LO_sub
            JOIN lesao AS L_sub ON LO_sub.Pessoa_afetada = L_sub.Pessoa_afetada AND LO_sub.Tipo_Lesao = L_sub.Tipo_Lesao
            WHERE LO_sub.Numero_da_Ocorrencia = O.Numero_da_Ocorrencia
              AND L_sub.Pessoa_afetada = 'Passageiros'
              AND L_sub.Tipo_Lesao = 'Ileso'
        ) AND V.Aerodromo_de_Origem != 'None';
    """,
    "7. Aeródromos com ocorrências na fase de decolagem": """
        SELECT V.Aerodromo_de_Destino, V.Aerodromo_de_Origem
        FROM ocorrencia AS O
        NATURAL JOIN voo AS V
        NATURAL JOIN operacao AS OP
        WHERE OP.Fase_da_Operacao = 'Decolagem'
    """,
    "8. Quantidade de acidentes por aeródromo público": """
        SELECT COUNT(O.Numero_da_Ocorrencia) AS qtd_ocorrencias, A.ICAO
        FROM ocorrencia AS O
        NATURAL JOIN voo AS V
        JOIN aerodromo AS A ON V.Aerodromo_de_Origem = A.ICAO OR V.Aerodromo_de_Destino = A.ICAO
        WHERE O.Classificacao_da_Ocorrencia = 'Acidente' AND A.Tipo_de_Aerodromo = 'Público'
        GROUP BY A.ICAO
        ORDER BY qtd_ocorrencias DESC;
    """,
    "9. Quantidade de acidentes e incidentes graves por região": """
        SELECT 
            L.Regiao,
            COUNT(CASE WHEN O.Classificacao_da_Ocorrencia = 'Incidente Grave' THEN 1 END) AS qtd_incidentes_graves,
            COUNT(CASE WHEN O.Classificacao_da_Ocorrencia = 'Acidente' THEN 1 END) AS qtd_acidentes
        FROM ocorrencia AS O
        NATURAL JOIN local_ocorrencia
        NATURAL JOIN local AS L
        GROUP BY L.Regiao
    """,
    "10. Ocorrências por fabricante": """
        SELECT 
            A.Nome_do_Fabricante,
            COUNT(AO.Numero_da_Ocorrencia) AS qtd_ocorrencias
        FROM aeronave AS A
        NATURAL JOIN aeronave_ocorrencia AS AO
        NATURAL JOIN ocorrencia AS O
        WHERE A.Nome_do_Fabricante != 'None'
        GROUP BY A.Nome_do_Fabricante
        ORDER BY qtd_ocorrencias DESC;
    """
}

# Função para executar as consultas
@st.cache_data
def execute_query(query):
    conn = sqlite3.connect("ocorrencias.db")  
    try:
        data = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return data

# Interface do Streamlit
st.title("Visualização Interativa de Ocorrências Aéreas")

# Menu para selecionar a consulta
consulta_escolhida = st.selectbox("Selecione uma consulta", list(queries.keys()))

# Executar a consulta selecionada
query = queries[consulta_escolhida]
resultados = execute_query(query)

# Exibir os resultados
st.subheader(consulta_escolhida)
if not resultados.empty:
    # Filtro de linhas
    linhas_para_mostrar = st.slider("Número de linhas para exibir", min_value=1, max_value=len(resultados), value=10)
    st.dataframe(resultados.head(linhas_para_mostrar))
    
    # Exportar como CSV
    csv = resultados.to_csv(index=False).encode('utf-8')
    st.download_button(label="Baixar CSV", data=csv, file_name='resultados.csv', mime='text/csv')


    # Gráficos personalizados
    st.subheader("Visualização Gráfica")
    if consulta_escolhida == "1. Descrição e data das ocorrências de 2024":
        fig, ax = plt.subplots()
        resultados['Data_da_Ocorrencia'] = pd.to_datetime(resultados['Data_da_Ocorrencia'])
        top_10_datas = resultados['Data_da_Ocorrencia'].value_counts().nlargest(10).sort_index()
        top_10_datas.plot(ax=ax, kind='bar', color='blue')
        ax.set_title("Top 10 Datas com Mais Ocorrências")
        ax.set_ylabel("Quantidade")
        ax.set_xlabel("Data")
        st.pyplot(fig)
    elif consulta_escolhida == "2. Número das ocorrências e fase das operações que são do tipo Voo Privado":
        fig, ax = plt.subplots()
        resultados['Fase_da_Operacao'].value_counts().plot(kind='bar', ax=ax, color='green')
        ax.set_title("Ocorrências por Fase da Operação")
        ax.set_ylabel("Quantidade")
        st.pyplot(fig)
    elif consulta_escolhida == "3. Fases e número das ocorrências classificadas como incidentes graves":
        fig, ax = plt.subplots()
        resultados['Fase_da_Operacao'].value_counts().plot(kind='bar', ax=ax, color='orange')
        ax.set_title("Distribuição das Fases da Operação para Incidentes Graves")
        ax.set_ylabel("Quantidade")
        ax.set_xlabel("Fase da Operação")
        st.pyplot(fig)
    elif consulta_escolhida == "4. Código ICAO dos aeródromos de origem, data e classificação das ocorrências de 2024":
        fig, ax = plt.subplots(figsize=(12, 8))
        resultados.groupby(['Aerodromo_de_Origem', 'Classificacao_da_Ocorrencia']).size().unstack().plot(kind='bar', stacked=True, ax=ax)
        ax.set_title("Classificação das Ocorrências por Aeródromo de Origem (2024)")
        ax.set_ylabel("Quantidade")
        ax.set_xlabel("Aeródromo de Origem")
        st.pyplot(fig)
    elif consulta_escolhida == "5. Ocorrências no Aeródromo de Confins (SBCF)":
        fig, ax = plt.subplots()
        resultados['Tipo_descricao'].value_counts().plot(kind='bar', ax=ax, color='green')
        ax.set_title("Tipos de Ocorrência no Aeródromo de Confins (SBCF)")
        ax.set_ylabel("Quantidade")
        st.pyplot(fig)
    elif consulta_escolhida == "6. Aeródromos de origem sem passageiros ilesos":
        fig, ax = plt.subplots()
        aerodromos_count = resultados['Aerodromo_de_Origem'].value_counts().nlargest(10)
        aerodromos_count.plot(kind='bar', ax=ax, color='purple')
        ax.set_title("Top 10 Aeródromos de Origem com Mais Ocorrências (Sem Passageiros Ilesos)")
        ax.set_ylabel("Quantidade")
        ax.set_xlabel("Aeródromo de Origem")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    elif consulta_escolhida == "7. Aeródromos com ocorrências na fase de decolagem":
        fig, ax = plt.subplots()
        resultados['Origem_Destino'] = resultados['Aerodromo_de_Origem'] + ' -> ' + resultados['Aerodromo_de_Destino']
        top_10_combinacoes = resultados['Origem_Destino'].value_counts().nlargest(10)
        top_10_combinacoes.plot(kind='bar', ax=ax, color='teal')
        ax.set_title("Top 10 Combinações de Aeródromos de Origem e Destino com Mais Ocorrências na Fase de Decolagem")
        ax.set_ylabel("Quantidade")
        ax.set_xlabel("Combinação Origem -> Destino")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    elif consulta_escolhida == "8. Quantidade de acidentes por aeródromo público":
        fig, ax = plt.subplots()
        if 'qtd_ocorrencias' in resultados.columns:
            top_10_aerodromos = resultados.nlargest(10, 'qtd_ocorrencias')
            top_10_aerodromos.plot(x='ICAO', y='qtd_ocorrencias', kind='bar', ax=ax, legend=False, color='purple')
            ax.set_title("Top 10 Aeródromos Públicos com Mais Acidentes")
            ax.set_ylabel("Quantidade de Acidentes")
            ax.set_xlabel("Código ICAO")
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("A coluna 'qtd_ocorrencias' não foi encontrada no resultado da consulta.")
    elif consulta_escolhida == "9. Quantidade de acidentes e incidentes graves por região":
        fig, ax = plt.subplots()
        resultados.plot(x='Regiao', y=['qtd_incidentes_graves', 'qtd_acidentes'], kind='bar', ax=ax)
        ax.set_title("Incidentes Graves e Acidentes por Região")
        ax.set_ylabel("Quantidade")
        st.pyplot(fig)
    elif consulta_escolhida == "10. Ocorrências por fabricante":
        fig, ax = plt.subplots()
        if 'qtd_ocorrencias' in resultados.columns:
            top_10_fabricantes = resultados.nlargest(10, 'qtd_ocorrencias')
            top_10_fabricantes.plot(x='Nome_do_Fabricante', y='qtd_ocorrencias', kind='bar', ax=ax, legend=False, color='orange')
            ax.set_title("Top 10 Fabricantes com Mais Ocorrências")
            ax.set_ylabel("Quantidade de Ocorrências")
            ax.set_xlabel("Nome do Fabricante")
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("A coluna 'qtd_ocorrencias' não foi encontrada no resultado da consulta.")
