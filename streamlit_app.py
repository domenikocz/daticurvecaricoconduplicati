import pandas as pd
import streamlit as st
import io

def elabora_multipli_file():
    st.title("Elaboratore Riepilogo Multi-mese")

    # --- SEZIONE OPZIONI ---
    st.sidebar.header("Opzioni di Elaborazione")
    anno_selezionato = st.sidebar.selectbox("Quale anno vuoi esportare?", [2024, 2025, 2026], index=2)
    moltiplicatore = st.sidebar.number_input("Fattore di moltiplicazione", value=1.0, step=0.1)

    # --- CARICAMENTO FILE ---
    uploaded_files = st.file_uploader("Seleziona i file CSV dei mesi", type="csv", accept_multiple_files=True)

    if not uploaded_files:
        st.info("Inizia caricando uno o più file CSV.")
        return

    dati_mesi = {}
    
    try:
        for uploaded_file in uploaded_files:
            df = pd.read_csv(uploaded_file, sep=';', decimal=',', index_col=False)
            df['Giorno'] = pd.to_datetime(df['Giorno'], format='%d/%m/%Y')
            
            # Filtro per anno
            df = df[df['Giorno'].dt.year == anno_selezionato]
            
            if df.empty:
                continue

            # Calcolo somma delle colonne numeriche e applicazione moltiplicatore
            df['Somma_Giornaliera'] = df.iloc[:, 1:].select_dtypes(include=['number']).sum(axis=1) * moltiplicatore
            
            # Estraiamo il giorno (1-31)
            df['Day'] = df['Giorno'].dt.day
            
            # AGGREGAZIONE DUPLICATI: Se ci sono due righe per lo stesso giorno, le sommiamo
            df_aggregato = df.groupby('Day')['Somma_Giornaliera'].sum()
            
            periodo = df['Giorno'].dt.to_period('M').iloc[0]
            dati_mesi[periodo] = df_aggregato

        if not dati_mesi:
            st.warning(f"Nessun dato trovato per l'anno {anno_selezionato}.")
            return

        periodi_ordinati = sorted(dati_mesi.keys())
        df_finale = pd.DataFrame(index=range(1, 32))
        df_finale.index.name = 'Giorno'

        for p in periodi_ordinati:
            nome_col = p.strftime('%m/%Y')
            df_finale[nome_col] = dati_mesi[p]

        # Calcolo totali
        totali_mensili = df_finale.sum()
        riga_totali = pd.DataFrame([totali_mensili], columns=df_finale.columns, index=['TOTALE MENSILE'])
        df_risultato = pd.concat([df_finale, riga_totali])

        totale_generale = totali_mensili.sum()
        df_risultato['TOTALE GENERALE'] = ""
        df_risultato.at['TOTALE MENSILE', 'TOTALE GENERALE'] = totale_generale

        st.subheader(f"Risultati Anno {anno_selezionato} (x{moltiplicatore})")
        st.write(df_risultato)

        towrite = io.BytesIO()
        df_risultato.to_excel(towrite, index=True)
        towrite.seek(0)
        
        st.download_button(
            label="Scarica File Excel",
            data=towrite,
            file_name=f"riepilogo_{anno_selezionato}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Errore durante l'elaborazione: {e}")

if __name__ == "__main__":
    elabora_multipli_file()
