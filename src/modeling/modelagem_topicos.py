import pandas as pd
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.corpus import stopwords
from hdbscan import HDBSCAN

nltk.download('stopwords', quiet=True)
stopwords_pt = stopwords.words('portuguese')
stopwords_personalizadas = stopwords_pt + [
    "ufsj", "prof", "profa", "professor", "professora", "edson", "nucci", "romano",
    "sobre", "dia", "ano", "após", "nesta", "via", "campus"
]

def main():
    try:
            df_noticias = pd.read_json("data/clean/cleaned_noticias.json")
    except:
        print(f"Erro: O arquivo de notícias não foi encontrado.")
        return
    
    try:
            df_boletins = pd.read_json("data/clean/cleaned_boletins.json")
    except:
        print(f"Erro: O arquivo de boletins não foi encontrado.")
        return

    df_unificado = pd.concat([df_noticias, df_boletins])

    textos_treino = df_unificado["texto"].to_list()
    datas_treino = df_unificado["data_publicacao"].to_list()
    
    print(f"Total de textos válidos extraídos: {len(textos_treino)}")
    print(f"Total de datas válidas extraídas: {len(datas_treino)}")
    
    modelo_embedding = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
    vectorizer_model = CountVectorizer(
        stop_words = stopwords_personalizadas,
        token_pattern = r'(?u)\b[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ]+\b', # apenas palavras (sem números como "2024").
        ngram_range = (1, 2) # permite a criação de tópicos com pares de palavras, ex: "banca defesa".
        )
    
    hdbscan_model = HDBSCAN(
        min_cluster_size=10, 
        min_samples=3, 
        metric='euclidean', 
        cluster_selection_method='eom', 
        prediction_data=True)
    
    modelo_topicos = BERTopic(
        embedding_model = modelo_embedding,
        vectorizer_model = vectorizer_model,
        hdbscan_model = hdbscan_model,
        language = "multilingual",
        nr_topics = "auto"
    )

    print("Treinando o modelo BERTopic com os textos extraídos...")
    topicos, probabilidades = modelo_topicos.fit_transform(textos_treino)

    df_topicos = modelo_topicos.get_topic_info()
    df_topicos.to_json("data/clean/info_topicos.json", orient="records", force_ascii=False, indent=4)
    print("Tabela de tópicos salva em 'data/clean/info_topicos.json'.")

    topicos_tempo = modelo_topicos.topics_over_time(textos_treino, datas_treino, nr_bins=20)
    topicos_tempo.to_json("data/clean/topicos_tempo.json", orient="records", force_ascii=False, indent=4)
    print("Evolução temporal salva em 'data/clean/topicos_tempo.json'.")

    df_documentos = modelo_topicos.get_document_info(textos_treino)
    df_documentos.to_json("data/clean/info_documentos.json", orient="records", force_ascii=False, indent=4)
    print("Distribuição de documentos salva em 'data/clean/info_documentos.json'.")

    hierarquia = modelo_topicos.hierarchical_topics(textos_treino)
    arvore = modelo_topicos.get_topic_tree(hierarquia)
    with open("data/clean/arvore_topicos.txt", "w", encoding="utf-8") as f:
        f.write(arvore)
    print("Árvore hierárquica salva em 'data/clean/arvore_topicos.txt'.")

    modelo_topicos.save("data/clean/modelo_topicos_ufsj", serialization="safetensors", save_embedding_model=True)
    print("Modelo BERTopic salvo na pasta 'data/clean/modelo_topicos_ufsj'.")
    
if __name__ == "__main__":
    main()