import json
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

def extrair_texto(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            dados = json.load(file)
        
        textos_extraidos = [dado['texto'] for dado in dados if 'texto' in dado and dado['texto'] and dado['texto'].strip()] 

        # print(f"Total de textos válidos extraídos: {len(textos_extraidos)}")
        # print(textos_extraidos[1])
        return textos_extraidos
        
    except Exception as e:
        print(f"Erro: {e}")
        return []

def main():
    textos_treino = []
    textos_treino = extrair_texto("noticias.json") + extrair_texto("boletins.json")
    
    # print(f"Total de textos válidos extraídos: {len(textos_treino)}")
    
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

    topicos, probabilidades = modelo_topicos.fit_transform(textos_treino)
    
    print(modelo_topicos.get_topic_info())
    
    fig = modelo_topicos.visualize_topics()
    fig.show()
    
if __name__ == "__main__":
    main()