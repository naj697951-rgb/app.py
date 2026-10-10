import sqlite3
import random
from datetime import datetime, timedelta

# 1. Connexion à la base de données (le fichier se créera tout seul)
conn = sqlite3.connect('commerce.db')
cursor = conn.cursor()

# 2. Création des tables relationnelles
cursor.execute('''
CREATE TABLE IF NOT EXISTS Employes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    region TEXT NOT NULL,
    performance INTEGER NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Ventes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    region TEXT NOT NULL,
    produit TEXT NOT NULL,
    quantite INTEGER NOT NULL,
    prix_unitaire REAL NOT NULL,
    cout_unitaire REAL NOT NULL,
    id_employe INTEGER,
    FOREIGN KEY (id_employe) REFERENCES Employes(id)
)
''')

# Vider les tables si réexécution
cursor.execute('DELETE FROM Ventes')
cursor.execute('DELETE FROM Employes')

# 3. Insertion des Commerciaux (Contexte Commerce International)
commerciaux = [
    ("Sarah Benali", "Europe", 92),
    ("Jean Dupont", "Europe", 85),
    ("David Chen", "Asie-Pacifique", 95),
    ("Mei Lin", "Asie-Pacifique", 88),
    ("Michael Smith", "Amérique du Nord", 78),
    ("Emma Watson", "Amérique du Nord", 91),
    ("Amadou Diallo", "Afrique & Moyen-Orient", 84),
    ("Youssef Mansour", "Afrique & Moyen-Orient", 89)
]

cursor.executemany('''
INSERT INTO Employes (nom, region, performance) VALUES (?, ?, ?)
''', commerciaux)

# Récupérer les IDs et régions des employés créés
cursor.execute('SELECT id, region FROM Employes')
employes_db = cursor.fetchall()

# 4. Insertion de 600 ventes réalistes sur les 2 dernières années
produits_catalogue = [
    {"nom": "Machines Industrielles", "prix": 1200.0, "cout": 750.0},
    {"nom": "Composants Électroniques", "prix": 350.0, "cout": 180.0},
    {"nom": "Matières Premières Bio", "prix": 500.0, "cout": 320.0},
    {"nom": "Textile Haute Performance", "prix": 150.0, "cout": 60.0},
    {"nom": "Solutions Logicielles B2B", "prix": 2500.0, "cout": 500.0}
]

date_debut = datetime(2024, 1, 1)
ventes_data = []

for _ in range(600):
    emp_id, emp_region = random.choice(employes_db)
    prod = random.choice(produits_catalogue)
    
    # Date aléatoire
    nb_jours = random.randint(0, 700)
    date_vente = (date_debut + timedelta(days=nb_jours)).strftime('%Y-%m-%d')
    
    quantite = random.randint(1, 15)
    
    ventes_data.append((
        date_vente,
        emp_region,
        prod["nom"],
        quantite,
        prod["prix"],
        prod["cout"],
        emp_id
    ))

cursor.executemany('''
INSERT INTO Ventes (date, region, produit, quantite, prix_unitaire, cout_unitaire, id_employe)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', ventes_data)

conn.commit()
conn.close()

print(" Succès : Base 'commerce.db' créée avec 8 employés et 600 ventes internationales !")