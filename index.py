import os
import json
import requests
from bs4 import BeautifulSoup
import pdfkit
import pandas as pd
import urllib.parse
import re

# URL des pages
url_indiana_jones = "https://fr.wikipedia.org/wiki/Indiana_Jones"
url_allemagne = "https://www.worldometers.info/world-population/germany-population/"

# Création des répertoires de sortie
os.makedirs("rendu PDF", exist_ok=True)
os.makedirs("Images Indiana Jones", exist_ok=True)
os.makedirs("rendu CSV", exist_ok=True)

# --- 1. EXTRACTION DU SOMMAIRE DE LA PAGE WIKIPÉDIA ---
def extract_toc():
    response_indiana_jones = requests.get(url_indiana_jones)
    soup_indiana_jones = BeautifulSoup(response_indiana_jones.content, 'html.parser')
    toc_div = soup_indiana_jones.find("div", {"class": "vector-toc"})
    toc_html = ""
    if toc_div:
        for unwanted in toc_div.find_all(["button", "span"], {"class": ["toc-toggle", "vector-toc-expand", "vector-toc-collapse"]}):
            unwanted.decompose()
        toc_html = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Sommaire de Indiana Jones</title>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1 {{ text-align: center; }}
                ul {{ list-style: none; padding: 0; }}
                li {{ margin-bottom: 8px; }}
            </style>
        </head>
        <body>
            <h1>Sommaire de la page Indiana Jones</h1>
            {toc_div.prettify()}
        </body>
        </html>
        """
    else:
        toc_html = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Sommaire de Indiana Jones</title>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1 {{ text-align: center; }}
            </style>
        </head>
        <body>
            <h1>Sommaire de la page Indiana Jones</h1>
            <p>Aucun sommaire trouvé.</p>
        </body>
        </html>
        """
    return toc_html

def save_toc_pdf_with_pdfkit(toc_html):
    output_file = "rendu PDF/Sommaire Indiana Jones.pdf"
    options = {"encoding": "UTF-8", "enable-local-file-access": None}
    pdfkit.from_string(toc_html, output_file, options=options)
    print(f"Sommaire enregistré dans {output_file}")

# --- 2. TÉLÉCHARGEMENT DES IMAGES DE LA PAGE WIKIPÉDIA ---
def download_images():
    response_indiana_jones = requests.get(url_indiana_jones)
    soup_indiana_jones = BeautifulSoup(response_indiana_jones.content, 'html.parser')
    img_tags = soup_indiana_jones.find_all('img')
    output_dir = "Images Indiana Jones"
    downloaded_images = []
    for index, img in enumerate(img_tags):
        img_url = img.get('src')
        if img_url and img_url.startswith('/'):
            img_url = urllib.parse.urljoin('https://fr.wikipedia.org', img_url)
        try:
            img_data = requests.get(img_url).content
            img_name = f"image_{index}.jpg"
            img_name = re.sub(r'[^\w\s.-]', '', img_name)
            if img_url not in downloaded_images:
                with open(os.path.join(output_dir, img_name), 'wb') as f:
                    f.write(img_data)
                downloaded_images.append(img_url)
                print(f"Image sauvegardée : {os.path.join(output_dir, img_name)}")
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de l'image {img_url}: {e}")
    print("Toutes les images ont été traitées.")

# --- 3. EXTRACTION DES JEUX VIDÉO ET SAUVEGARDE EN JSON & EXCEL ---
def extract_video_games():
    response_indiana_jones = requests.get(url_indiana_jones)
    soup_indiana_jones = BeautifulSoup(response_indiana_jones.content, 'html.parser')
    games = []
    ul_elements = soup_indiana_jones.find_all('ul')
    for ul in ul_elements:
        for li in ul.find_all('li'):
            year_tag = li.find('a', href=re.compile(r"(\d{4})_en_jeu_vid%C3%A9o"))
            title_tag = li.find('i')
            if year_tag and title_tag:
                year = year_tag.text.strip()
                title = title_tag.text.strip()
                description = li.get_text(strip=True)
                description = description.replace(year, "").replace(title, "").strip(" –:")
                games.append({"Date": year, "Titre": title, "Description": description})
    json_file_path = "rendu PDF/Jeux Indiana Jones.json"
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(games, json_file, ensure_ascii=False, indent=4)
    print(f"Liste des jeux vidéo sauvegardée en JSON : {json_file_path}")
    df = pd.DataFrame(games)
    excel_file_path = "rendu PDF/Jeux Indiana Jones.xlsx"
    df.to_excel(excel_file_path, index=False)
    print(f"Liste des jeux vidéo sauvegardée en Excel : {excel_file_path}")

# --- 4. EXTRACTION DES DONNÉES DE POPULATION DE L'ALLEMAGNE ---
def extract_population_data():
    response_allemagne = requests.get(url_allemagne)
    soup_allemagne = BeautifulSoup(response_allemagne.content, 'html.parser')
    table = soup_allemagne.find('table', {'class': 'table table-striped table-bordered table-hover table-condensed table-list'})
    population_data = []
    if table:
        rows = table.find_all('tr')[1:6]
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 6:
                year = int(cols[0].text.strip())
                population = cols[1].text.strip() + " habitants"
                migrants = cols[4].text.strip() + " migrants"
                avg_age = cols[5].text.strip() + " ans"
                try:
                    rank = float(cols[6].text.strip())
                except ValueError:
                    rank = None
                population_data.append({"Année": year, "Population Totale": population, "Migrants": migrants, "Âge Moyen": avg_age, "Rang": rank})
    return population_data

def save_population_csv(population_data):
    csv_file_path = "rendu CSV/Allemagne.csv"
    df_population = pd.DataFrame(population_data)
    df_population.to_csv(csv_file_path, index=False, encoding="utf-8")
    print(f"Les données de la population de l'Allemagne ont été enregistrées dans {csv_file_path}")

# --- MAIN ---
def main():
    toc_html = extract_toc()
    save_toc_pdf_with_pdfkit(toc_html)
    download_images()
    extract_video_games()
    population_data = extract_population_data()
    save_population_csv(population_data)

if __name__ == "__main__":
    main()

print("\nTâches terminées :")
print("- Sommaire enregistré dans 'rendu PDF/Sommaire Indiana Jones.pdf'")
print("- Images enregistrées dans le dossier 'Images Indiana Jones'")
print("- Liste des jeux vidéo enregistrée en JSON et Excel dans 'rendu PDF/'")
print("- Données de la population de l'Allemagne enregistrées dans 'rendu CSV/Allemagne.csv'")
