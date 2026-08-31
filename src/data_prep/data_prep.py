import pandas as pd
from datetime import datetime
import os

def limpa_dataframe(df_path: str) -> pd.DataFrame:
    try:
        df = pd.read_json(df_path)
    except FileNotFoundError:
        print(f"Erro: O arquivo {df_path} não foi encontrado.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro inesperado ao ler {df_path}: {e}")
        return pd.DataFrame()

    if not df.empty:
        df.dropna(inplace=True)

        df["data_publicacao"] = pd.to_datetime(
            df["data_publicacao"].str.replace("Publicada em ", "", regex=False).str.strip(), 
            format="%d/%m/%Y",
            errors="coerce" 
        ).dt.strftime("%Y/%m/%d")
        df.dropna(subset=["data_publicacao"], inplace=True) # remove linhas onde a data falhou

        df["titulo"] = df["titulo"].str.replace(r"^\s*\d+\s*[-–—]\s*", "", regex=True)
        df["texto"] = df["texto"].str.replace(r"\s+", " ", regex=True)

    return df

def main():
    df_noticias = limpa_dataframe("data/raw/noticias.json")
    df_boletins = limpa_dataframe("data/raw/boletins.json")

    os.makedirs("data/clean", exist_ok=True)

    try:
        if not df_noticias.empty:
            df_noticias.to_json("data/clean/cleaned_noticias.json", orient="records", force_ascii=False, indent=4)
            print("Notícias limpas e salvas com sucesso.")
            
        if not df_boletins.empty:
            df_boletins.to_json("data/clean/cleaned_boletins.json", orient="records", force_ascii=False, indent=4)
            print("Boletins limpos e salvos com sucesso.")
            
    except Exception as e:
        print(f"Erro ao salvar os arquivos limpos: {e}")

if __name__ == "__main__":
    main()