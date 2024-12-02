import os
import json
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import pandas as pd
import urllib.parse
import re

# URL de la page Wikipédia pour Indiana Jones
url_indiana_jones = "https://fr.wikipedia.org/wiki/Indiana_Jones"
# URL pour les données de la population de l'Allemagne
url_allemagne = "https://www.worldometers.info/world-population/germany-population/"

# Création des répertoires de sortie
os.makedirs("rendu PDF", exist_ok=True)
os.makedirs("Images Indiana Jones", exist_ok=True)
os.makedirs("rendu CSV", exist_ok=True)

# --- 1. EXTRACTION DU SOMMAIRE DE LA PAGE WIKIPÉDIA INDY ---
def extract_toc():
    response_indiana_jones = requests.get(url_indiana_jones)
    soup_indiana_jones = BeautifulSoup(response_indiana_jones.content, 'html.parser')

    toc = soup_indiana_jones.find('div', {'id': 'vector-toc'})
    toc_text = "Sommaire de la page Indiana Jones\n\n"

    if toc:
        toc_items = toc.find_all('li', {'class': 'toclevel-1'})
        for item in toc_items:
            # Trouver le numéro et le titre
            number = item.find('span', {'class': 'tocnumber'}).text if item.find('span', {'class': 'tocnumber'}) else ""
            title = item.find('span', {'class': 'toctext'}).text if item.find('span', {'class': 'toctext'}) else ""
            toc_text += f"{number} {title}\n"
    else:
        toc_text += "Aucun sommaire trouvé.\n"

    toc_text = toc_text.replace("[", "").replace("]", "")
    return toc_text

# Sauvegarde du sommaire dans un fichier PDF
def save_toc_pdf(toc_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Ajout du texte TOC dans le PDF
    pdf.multi_cell(0, 10, toc_text)
    pdf.output("rendu PDF/Sommaire Indiana Jones.pdf")
    print("Sommaire enregistré dans 'rendu PDF/Sommaire Indiana Jones.pdf'")

# --- 2. TÉLÉCHARGEMENT DES IMAGES DE LA PAGE WIKIPÉDIA INDY ---
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

                games.append({
                    "Date": year,
                    "Titre": title,
                    "Description": description
                })

    # Sauvegarde des jeux vidéo en JSON
    json_file_path = "rendu PDF/Jeux Indiana Jones.json"
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(games, json_file, ensure_ascii=False, indent=4)
    print(f"Liste des jeux vidéo sauvegardée en JSON : {json_file_path}")

    # Création du DataFrame et sauvegarde des jeux vidéo dans un fichier Excel
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

                population_data.append({
                    "Année": year,
                    "Population Totale": population,
                    "Migrants": migrants,
                    "Âge Moyen": avg_age,
                    "Rang": rank
                })

    return population_data

# Sauvegarde des données de population en CSV
def save_population_csv(population_data):
    csv_file_path = "rendu CSV/Allemagne.csv"
    df_population = pd.DataFrame(population_data)
    df_population.to_csv(csv_file_path, index=False, encoding="utf-8")
    print(f"Les données de la population de l'Allemagne ont été enregistrées dans {csv_file_path}")

# --- MAIN --- 
def main():
    # 1. Extraire le sommaire et le convertir en PDF
    toc_text = extract_toc()
    save_toc_pdf(toc_text)

    # 2. Télécharger les images
    download_images()

    # 3. Extraire les jeux vidéo et sauvegarder en JSON et Excel
    extract_video_games()

    # 4. Extraire les données de population et sauvegarder en CSV
    population_data = extract_population_data()
    save_population_csv(population_data)

# Lancer le script
if __name__ == "__main__":
    main()

print("\nTâches terminées :")
print("- Sommaire enregistré dans 'rendu PDF/Sommaire Indiana Jones.pdf'")
print("- Images enregistrées dans le dossier 'Images Indiana Jones'")
print("- Liste des jeux vidéo enregistrée en JSON et Excel dans 'rendu PDF/'")
print("- Données de la population de l'Allemagne enregistrées dans 'rendu CSV/Allemagne.csv'")
