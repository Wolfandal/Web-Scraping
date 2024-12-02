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

# Création des répertoires de sortie
os.makedirs("rendu PDF", exist_ok=True)
os.makedirs("Images Indiana Jones", exist_ok=True)
os.makedirs("rendu CSV", exist_ok=True)

# --- 1. EXTRACTION DU SOMMAIRE --- 
# Requête pour récupérer le contenu de la page Indiana Jones
response_indiana_jones = requests.get(url_indiana_jones)
soup_indiana_jones = BeautifulSoup(response_indiana_jones.content, 'html.parser')

# Recherche de la div contenant le sommaire avec l'ID 'vector-toc'
toc = soup_indiana_jones.find('div', {'id': 'vector-toc'})
toc_text = "Sommaire de la page Indiana Jones\n\n"

if toc:
    # Récupération des items de la table des matières (éléments de niveau 1)
    toc_items = toc.find_all('li', {'class': 'toclevel-1'})
    for item in toc_items:
        # Extraire le numéro et le titre
        number = item.find('span', {'class': 'tocnumber'}).text if item.find('span', {'class': 'tocnumber'}) else ""
        title = item.find('span', {'class': 'toctext'}).text if item.find('span', {'class': 'toctext'}) else ""
        toc_text += f"{number} {title}\n"
else:
    toc_text += "Aucun sommaire trouvé.\n"

# Suppression des liens de navigation
toc_text = toc_text.replace("[", "").replace("]", "")

# --- 2. SAUVEGARDE DU SOMMAIRE DANS UN PDF ---
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 10, toc_text)
pdf.output("rendu PDF/Sommaire Indiana Jones.pdf")
print("Sommaire enregistré dans 'rendu PDF/Sommaire Indiana Jones.pdf'")

# --- 3. TÉLÉCHARGEMENT DES IMAGES --- 
img_tags = soup_indiana_jones.find_all('img')
output_dir = "Images Indiana Jones"
downloaded_images = []

for index, img in enumerate(img_tags):
    img_url = img.get('src')
    if img_url and img_url.startswith('/'):  # Si l'URL est relative
        img_url = urllib.parse.urljoin('https://fr.wikipedia.org', img_url)

    try:
        img_data = requests.get(img_url).content
        img_name = f"image_{index}.jpg"
        img_name = re.sub(r'[^\w\s.-]', '', img_name)  # Nettoyage du nom de fichier

        # Éviter les duplications
        if img_url not in downloaded_images:
            with open(os.path.join(output_dir, img_name), 'wb') as f:
                f.write(img_data)
            downloaded_images.append(img_url)
            print(f"Image sauvegardée : {os.path.join(output_dir, img_name)}")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de l'image {img_url}: {e}")

print("Toutes les images ont été traitées.")

# --- 4. EXTRACTION DES JEUX VIDÉO --- 
games = []
ul_elements = soup_indiana_jones.find_all('ul')

# Recherche des jeux vidéo dans les <ul> potentiels
for ul in ul_elements:
    for li in ul.find_all('li'):
        # Recherche de l'année et du titre
        year_tag = li.find('a', href=re.compile(r"(\d{4})_en_jeu_vid%C3%A9o"))
        title_tag = li.find('i')

        if year_tag and title_tag:
            year = year_tag.text.strip()
            title = title_tag.text.strip()

            # Description : texte de l'élément <li> sans l'année ni le titre
            description = li.get_text(strip=True)
            description = description.replace(year, "").replace(title, "").strip(" –:")

            # Enregistrement dans la liste des jeux
            games.append({
                "Date": year,
                "Titre": title,
                "Description": description
            })

# Sauvegarde des données des jeux vidéo en JSON
json_file_path = "rendu PDF/Jeux Indiana Jones.json"
with open(json_file_path, "w", encoding="utf-8") as json_file:
    json.dump(games, json_file, ensure_ascii=False, indent=4)

print(f"Liste des jeux vidéo sauvegardée en JSON : {json_file_path}")

# Création du DataFrame et sauvegarde des jeux vidéo dans un fichier Excel
df = pd.DataFrame(games)
excel_file_path = "rendu PDF/Jeux Indiana Jones.xlsx"
df.to_excel(excel_file_path, index=False)
print(f"Liste des jeux vidéo sauvegardée en Excel : {excel_file_path}")

# --- 5. EXTRACTION DES DONNÉES DE POPULATION DE L'ALLEMAGNE ---
url_allemagne = "https://www.worldometers.info/world-population/germany-population/"
response_allemagne = requests.get(url_allemagne)
soup_allemagne = BeautifulSoup(response_allemagne.content, 'html.parser')

# Recherche du tableau contenant les données
table = soup_allemagne.find('table', {'class': 'table table-striped table-bordered table-hover table-condensed table-list'})

# Initialisation d'une liste pour stocker les données extraites
population_data = []

if table:
    # Récupérer les lignes du tableau, en ignorant l'en-tête
    rows = table.find_all('tr')[1:6]  # Extraire les 5 premières lignes (hors en-tête)
    
    for row in rows:
        cols = row.find_all('td')  # Extraire toutes les colonnes de la ligne
        
        if len(cols) >= 6:
            # Extraction des données pour chaque ligne
            year = int(cols[0].text.strip())  # Première colonne (année) sous forme d'entier
            population = cols[1].text.strip() + " habitants"  # Deuxième colonne (population) avec le suffixe "habitants"
            migrants = cols[4].text.strip() + " migrants"  # Cinquième colonne (migrants) avec le suffixe "migrants"
            avg_age = cols[5].text.strip() + " ans"  # Sixième colonne (âge moyen) avec le suffixe "ans"
            
            # Tentative de conversion du rang en nombre
            try:
                rank = float(cols[6].text.strip())  # Dernière colonne (rang) sous forme de flottant
            except ValueError:
                rank = None  # Si la conversion échoue, on affecte None au rang
            
            # Ajouter les données dans la liste
            population_data.append({
                "Année": year,
                "Population Totale": population,
                "Migrants": migrants,
                "Âge Moyen": avg_age,
                "Rang": rank
            })

# Sauvegarde des données dans un fichier CSV
csv_file_path = "rendu CSV/Allemagne.csv"
df_population = pd.DataFrame(population_data)
df_population.to_csv(csv_file_path, index=False, encoding="utf-8")
print(f"Les données de la population de l'Allemagne ont été enregistrées dans {csv_file_path}")

print("\nTâches terminées :")
print("- Sommaire enregistré dans 'rendu PDF/Sommaire Indiana Jones.pdf'")
print("- Images enregistrées dans le dossier 'Images Indiana Jones'")
print("- Liste des jeux vidéo enregistrée en JSON et Excel dans 'rendu PDF/'")
print("- Données de la population de l'Allemagne enregistrées dans 'rendu CSV/Allemagne.csv'")
