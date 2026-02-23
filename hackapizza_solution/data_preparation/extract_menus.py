"""Extract structured menu data from 34 PDF restaurant menus using LLM.

Uses pypdfium2 for fast PDF text extraction, then gpt-5-mini with Pydantic
structured output to extract restaurant, chef, licenses, dishes, ingredients,
and techniques.

Usage:
    cd <project_root>
    ./pizza_env/bin/python -m hackapizza_solution.data_preparation.extract_menus
"""

import json
import sys
from pathlib import Path
from pydantic import BaseModel

import pypdfium2 as pdfium
from datapizza.clients.openai import OpenAIClient
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from hackapizza_solution.config import (
    OPENAI_API_KEY, MODEL_FAST, MENU_DIR, MENUS_JSON, DATA_DIR,
)

load_dotenv()


# --- Pydantic models for structured extraction ---

class Dish(BaseModel):
    name: str
    ingredients: list[str]
    techniques: list[str]


class License(BaseModel):
    code: str
    grade: int


class Chef(BaseModel):
    name: str
    licenses: list[License]


class RestaurantMenu(BaseModel):
    restaurant: str
    planet: str
    chef: Chef
    dishes: list[Dish]


EXTRACTION_PROMPT = """You are a data extraction expert. Given the text of a restaurant menu PDF,
extract ALL information into the structured format requested.

CRITICAL RULES:
- Extract the restaurant name exactly as written
- For the planet: infer from the restaurant name or text (e.g. "di Asgard" = Asgard, "delle Dune" = Arrakis, etc.)
- The 10 planets are: Tatooine, Asgard, Namecc, Arrakis, Krypton, Pandora, Cybertron, Ego, Montressosr, Klyntar
- For chef licenses, extract ALL mentioned licenses using these codes:
  P = Psionica, t = Temporale, G = Gravitazionale, e+ = Antimateria,
  Mx = Magnetica, Q = Quantistica, c = Luce, LTK = LTK
  The value is the grade/level number. Roman numerals must be converted to arabic (I=1, II=2, III=3, IV=4, V=5, VI=6, VII=7, VIII=8, IX=9, X=10, XI=11, XII=12, XIII=13)
  If the text says "beyond level X" or "superior to X", use X+1.
- For each dish: extract the EXACT name, ALL ingredients listed, and ALL techniques listed
- Do NOT skip any dish, ingredient, or technique
- Keep original Italian names exactly as written"""


def parse_pdf_to_text(pdf_path: Path) -> str:
    """Fast PDF text extraction using pypdfium2."""
    pdf = pdfium.PdfDocument(str(pdf_path))
    pages_text = []
    for page in pdf:
        textpage = page.get_textpage()
        pages_text.append(textpage.get_text_range())
        textpage.close()
        page.close()
    pdf.close()
    return "\n\n".join(pages_text)


def extract_menu(client: OpenAIClient, pdf_text: str) -> RestaurantMenu:
    """Use LLM structured output to extract menu data."""
    response = client.structured_response(
        input=f"{EXTRACTION_PROMPT}\n\n--- MENU TEXT ---\n{pdf_text}",
        output_cls=RestaurantMenu,
    )
    return response.structured_data[0]


def run():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    client = OpenAIClient(
        api_key=OPENAI_API_KEY,
        model=MODEL_FAST,
    )

    pdf_files = sorted(MENU_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} menu PDFs to process\n")

    all_menus = []
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Processing {pdf_path.name}...")
        try:
            text = parse_pdf_to_text(pdf_path)
            if not text.strip():
                print(f"  WARNING: No text extracted, skipping")
                continue
            menu = extract_menu(client, text)
            menu_dict = menu.model_dump()
            licenses_dict = {lic["code"]: lic["grade"] for lic in menu_dict["chef"]["licenses"]}
            menu_dict["chef"]["licenses"] = licenses_dict
            all_menus.append(menu_dict)
            n_dishes = len(menu_dict["dishes"])
            print(f"  -> {menu_dict['restaurant']} ({menu_dict['planet']}) - {n_dishes} dishes, chef: {menu_dict['chef']['name']}")
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    MENUS_JSON.write_text(
        json.dumps(all_menus, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nSaved {len(all_menus)} menus to {MENUS_JSON}")


if __name__ == "__main__":
    run()
