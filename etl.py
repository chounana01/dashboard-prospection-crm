#!/usr/bin/env python3
"""Pipeline ETL — Prospection CRM (données synthétiques).

Étapes :
    1. Extraction : lecture de data/prospects_brut.csv
    2. Transformation : déduplication, normalisation (villes, téléphones),
       traitement des valeurs manquantes, colonnes dérivées
    3. Chargement : écriture dans data/prospects.db (table « prospects »)

Chaque étape journalise le nombre de lignes traitées.

Usage :
    python etl.py
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent
ENTREE = RACINE / "data" / "prospects_brut.csv"
SORTIE_DB = RACINE / "data" / "prospects.db"


def normaliser_ville(ville: str) -> str:
    """« MONTREAL » / « montreal » -> « Montréal »."""
    corrections = {
        "Montreal": "Montréal",
        "Quebec": "Québec",
        "Trois-Rivieres": "Trois-Rivières",
        "Levis": "Lévis",
    }
    ville = str(ville).strip().title()
    return corrections.get(ville, ville)


def normaliser_telephone(tel) -> str | None:
    """« 514-555-1234 » / « 5145551234 » -> « (514) 555-1234 »."""
    if pd.isna(tel):
        return None
    chiffres = re.sub(r"\D", "", str(tel))
    if len(chiffres) == 10:
        return f"({chiffres[:3]}) {chiffres[3:6]}-{chiffres[6:]}"
    return str(tel)


def extraire() -> pd.DataFrame:
    df = pd.read_csv(ENTREE)
    print(f"[EXTRACTION] {len(df)} lignes lues depuis {ENTREE.name}")
    return df


def transformer(df: pd.DataFrame) -> pd.DataFrame:
    n_depart = len(df)

    # 1. Doublons exacts (même prospect, mêmes champs)
    df = df.drop_duplicates(subset=["nom", "prenom", "adresse", "date_prospection"])
    print(f"[NETTOYAGE] Doublons supprimés : {n_depart - len(df)}")

    # 2. Lignes inutilisables (sans nom ni ville ni date)
    avant = len(df)
    df = df.dropna(subset=["nom", "ville", "date_prospection"])
    print(f"[NETTOYAGE] Lignes sans nom/ville/date supprimées : {avant - len(df)}")

    # 3. Normalisation des villes
    df["ville"] = df["ville"].astype(str).apply(normaliser_ville)

    # 4. Normalisation des téléphones
    df["telephone"] = df["telephone"].apply(normaliser_telephone)

    # 5. Valeurs manquantes : montant à 0, courriel marqué « non renseigné »
    df["montant_potentiel"] = df["montant_potentiel"].fillna(0).astype(int)
    df["courriel"] = df["courriel"].fillna("non renseigné")
    print(
        "[NETTOYAGE] Téléphones manquants conservés (NULL) : "
        f"{int(df['telephone'].isna().sum())} — montants manquants mis à 0"
    )

    # 6. Dates + colonnes dérivées
    df["date_prospection"] = pd.to_datetime(df["date_prospection"])
    df["mois"] = df["date_prospection"].dt.strftime("%Y-%m")
    df["annee"] = df["date_prospection"].dt.year

    print(f"[TRANSFORMATION] {len(df)} lignes après nettoyage")
    return df


def charger(df: pd.DataFrame) -> None:
    with sqlite3.connect(SORTIE_DB) as conn:
        df.to_sql("prospects", conn, if_exists="replace", index=False)
    print(f"[CHARGEMENT] {len(df)} lignes écrites dans {SORTIE_DB.name} (table « prospects »)")


def main() -> None:
    print("=== ETL — Prospection CRM ===")
    df = extraire()
    df = transformer(df)
    charger(df)
    print("=== ETL terminé ===")


if __name__ == "__main__":
    main()
