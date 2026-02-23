import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
COHERE_ENDPOINT = os.getenv("COHERE_ENDPOINT", "https://api.cohere.com")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# --- Models ---
MODEL_FAST = "gpt-5-mini"
MODEL_STRONG = "gpt-5"

# --- Embedding ---
EMBED_MODEL = "embed-v4.0"
EMBED_DIM = 1536

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "hackapizza_dataset"
SOLUTION_DIR = PROJECT_ROOT / "hackapizza_solution"
DATA_DIR = SOLUTION_DIR / "data"

MENU_DIR = DATASET_DIR / "Menu"
CODICE_PDF = DATASET_DIR / "Codice Galattico" / "Codice Galattico.pdf"
MANUALE_PDF = DATASET_DIR / "Misc" / "Manuale di Cucina.pdf"
DISTANZE_CSV = DATASET_DIR / "Misc" / "Distanze.csv"
DISH_MAPPING_JSON = DATASET_DIR / "Misc" / "dish_mapping.json"
BLOGPOST_DIR = DATASET_DIR / "Blogpost"
DOMANDE_CSV = DATASET_DIR / "domande.csv"

MENUS_JSON = DATA_DIR / "menus.json"
BLOGPOST_PCT_JSON = DATA_DIR / "blogpost_percentages.json"

# --- Qdrant collections ---
COLLECTION_CODICE = "codice_galattico"
COLLECTION_MANUALE = "manuale_cucina"
COLLECTION_BLOG = "blogposts"
