#!/usr/bin/env python3
"""Génère un jeu de données SYNTHÉTIQUE de prospection CRM (assurance, Québec).

Toutes les données sont inventées : noms, adresses, téléphones et courriels
sont fictifs. Ce script sert uniquement à démontrer un pipeline ETL et un
tableau de bord, inspiré d'un stage en développement de données.

Usage :
    python generate_data.py
    -> écrit data/prospects_brut.csv (25 000 lignes)
"""

import random
import string
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)

N_LIGNES = 25_000

PRENOMS = [
    "Marie", "Jean", "Sophie", "Pierre", "Julie", "Marc", "Isabelle", "François",
    "Catherine", "Michel", "Nathalie", "Daniel", "Anne", "Éric", "Caroline",
    "Stéphane", "Manon", "Sébastien", "Chantal", "Martin", "Sylvie", "Patrick",
    "Mélanie", "Louis", "Josée", "Alexandre", "Gabrielle", "Nicolas", "Émilie",
    "David", "Audrey", "Jonathan", "Karine", "Mathieu", "Valérie", "Simon",
    "Geneviève", "Hugo", "Annie", "Kevin", "Marie-Claude", "Olivier", "Stéphanie",
    "Guillaume", "Jessica", "Vincent", "Camille", "Antoine", "Laurence",
]

NOMS = [
    "Tremblay", "Gagnon", "Roy", "Côté", "Bouchard", "Gauthier", "Morin",
    "Lachance", "Fortin", "Gagné", "Ouellet", "Pelletier", "Bélanger",
    "Lévesque", "Bergeron", "Leblanc", "Paquin", "Girard", "Simard", "Poirier",
    "Thibault", "Côté", "Dubois", "Martin", "Lavoie", "Giroux", "Lefebvre",
    "Bernier", "Fournier", "Cloutier", "Dufour", "Bédard", "Poulin", "St-Pierre",
    "Nadeau", "Grenier", "Lessard", "Marchand", "Côté", "Lapointe",
]

RUES = [
    "rue Sainte-Catherine", "boulevard René-Lévesque", "avenue du Mont-Royal",
    "rue Saint-Denis", "boulevard Saint-Laurent", "rue Sherbrooke",
    "avenue Papineau", "rue Ontario", "boulevard Rosemont", "rue Rachel",
    "avenue Laurier", "rue Beaubien", "boulevard Pie-IX", "rue Villeray",
    "avenue Van Horne", "rue Jean-Talon", "boulevard Langelier",
    "rue Notre-Dame", "avenue de Lorimier", "rue Masson", "rue Fleury",
    "boulevard Henri-Bourassa", "rue Jarry", "avenue du Parc",
]

# (ville, poids relatif)
VILLES = [
    ("Montréal", 0.34),
    ("Québec", 0.16),
    ("Laval", 0.10),
    ("Trois-Rivières", 0.09),
    ("Gatineau", 0.08),
    ("Sherbrooke", 0.07),
    ("Lévis", 0.06),
    ("Saguenay", 0.05),
    ("Terrebonne", 0.03),
    ("Longueuil", 0.02),
]

AGENTS = [
    "A. Tremblay", "J. Gagnon", "M. Roy", "S. Côté",
    "P. Bouchard", "L. Gauthier", "C. Morin", "D. Fortin",
]

SOURCES = ["Téléphone", "Courriel", "Porte-à-porte", "Référencement"]

STATUTS = ["Nouveau", "Contacté", "Qualifié", "Converti", "Perdu"]
POIDS_STATUTS = [0.22, 0.30, 0.18, 0.14, 0.16]

CODES_POSTAUX = {
    "Montréal": ["H1H", "H2X", "H3A", "H4C"],
    "Québec": ["G1X", "G2B", "G1R", "G1V"],
    "Laval": ["H7T", "H7V", "H7N"],
    "Trois-Rivières": ["G8T", "G9A", "G8Y"],
    "Gatineau": ["J8P", "J8T", "J9H"],
    "Sherbrooke": ["J1H", "J1K", "J1M"],
    "Lévis": ["G6V", "G6W"],
    "Saguenay": ["G7H", "G7J"],
    "Terrebonne": ["J6V", "J6W"],
    "Longueuil": ["J4H", "J4K"],
}

DATE_DEBUT = date(2025, 1, 1)
DATE_FIN = date(2026, 11, 15)


def _telephone() -> str:
    """Numéro de téléphone québécois fictif (indicatif 514/438/418/819)."""
    indicatif = random.choice(["514", "438", "418", "819", "450"])
    return f"{indicatif}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"


def _courriel(prenom: str, nom: str) -> str:
    domaine = random.choice(["exemple.ca", "courriel.qc.ca", "mail-exemple.com"])
    base = f"{prenom}.{nom}".lower().replace(" ", "").replace("é", "e").replace("è", "e")
    return f"{base}{random.randint(1, 99)}@{domaine}"


def _ville_ponderee() -> str:
    return random.choices([v for v, _ in VILLES], weights=[p for _, p in VILLES])[0]


def _montant(statut: str) -> int:
    """Montant potentiel annuel estimé de la police (en $ CA)."""
    if statut == "Perdu":
        return 0
    if statut == "Converti":
        return int(random.gauss(2600, 900))
    if statut == "Qualifié":
        return int(random.gauss(1900, 700))
    return int(random.gauss(1200, 600))


def generer(n: int = N_LIGNES) -> pd.DataFrame:
    lignes = []
    nb_jours = (DATE_FIN - DATE_DEBUT).days
    for i in range(1, n + 1):
        prenom = random.choice(PRENOMS)
        nom = random.choice(NOMS)
        ville = _ville_ponderee()
        statut = random.choices(STATUTS, weights=POIDS_STATUTS)[0]
        montant = max(0, _montant(statut))
        lignes.append(
            {
                "id": i,
                "nom": nom,
                "prenom": prenom,
                "adresse": f"{random.randint(10, 9999)} {random.choice(RUES)}",
                "ville": ville,
                "code_postal": random.choice(CODES_POSTAUX[ville])
                + f" {random.randint(1, 9)}{random.choice(string.ascii_uppercase)}{random.randint(1, 9)}",
                "telephone": _telephone(),
                "courriel": _courriel(prenom, nom),
                "agent": random.choice(AGENTS),
                "date_prospection": DATE_DEBUT + timedelta(days=random.randint(0, nb_jours)),
                "source": random.choice(SOURCES),
                "statut": statut,
                "montant_potentiel": montant,
            }
        )

    df = pd.DataFrame(lignes)

    # --- "Saletés" réalistes, pour que l'ETL ait du travail ---
    # 1 % de doublons exacts
    doublons = df.sample(frac=0.01, random_state=7)
    df = pd.concat([df, doublons], ignore_index=True)
    # 1 % de téléphones manquants
    idx_tel = df.sample(frac=0.01, random_state=11).index
    df.loc[idx_tel, "telephone"] = None
    # 0,5 % de courriels manquants
    idx_mail = df.sample(frac=0.005, random_state=13).index
    df.loc[idx_mail, "courriel"] = None
    # Casse incohérente sur quelques villes
    idx_ville = df.sample(frac=0.01, random_state=17).index
    df.loc[idx_ville, "ville"] = df.loc[idx_ville, "ville"].str.upper()

    return df.sample(frac=1, random_state=42).reset_index(drop=True)


def main() -> None:
    racine = Path(__file__).resolve().parent
    sortie = racine / "data" / "prospects_brut.csv"
    sortie.parent.mkdir(parents=True, exist_ok=True)

    df = generer()
    df.to_csv(sortie, index=False)
    print(f"Lignes générées : {len(df)}")
    print(f"Fichier écrit : {sortie}")


if __name__ == "__main__":
    main()
