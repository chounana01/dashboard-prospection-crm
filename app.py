#!/usr/bin/env python3
"""Tableau de bord — Prospection CRM (données synthétiques).

Application Streamlit (interface en français) pour explorer les données de
prospection générées par generate_data.py et nettoyées par etl.py.

Lancement :
    streamlit run app.py
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

RACINE = Path(__file__).resolve().parent
BASE = RACINE / "data" / "prospects.db"

ORDRE_STATUTS = ["Nouveau", "Contacté", "Qualifié", "Converti", "Perdu"]

st.set_page_config(
    page_title="Tableau de bord — Prospection CRM",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def charger_donnees() -> pd.DataFrame:
    with sqlite3.connect(BASE) as conn:
        df = pd.read_sql("SELECT * FROM prospects", conn)
    df["date_prospection"] = pd.to_datetime(df["date_prospection"])
    return df


def main() -> None:
    st.title("📊 Tableau de bord — Prospection CRM")
    st.caption(
        "Projet personnel de démonstration — données 100 % synthétiques, "
        "inspirées d'un stage en développement de données (CRM d'assurance)."
    )

    if not BASE.exists():
        st.error(
            "Base de données introuvable. Lancez d'abord :\n\n"
            "```\npython generate_data.py\npython etl.py\n```"
        )
        return

    df = charger_donnees()

    # ---------- Filtres (barre latérale) ----------
    st.sidebar.header("Filtres")
    date_min, date_max = df["date_prospection"].min().date(), df["date_prospection"].max().date()
    periode = st.sidebar.date_input(
        "Période de prospection", value=(date_min, date_max),
        min_value=date_min, max_value=date_max,
    )
    agents = st.sidebar.multiselect(
        "Agent", options=sorted(df["agent"].unique()),
        default=sorted(df["agent"].unique()),
    )
    villes = st.sidebar.multiselect(
        "Ville", options=sorted(df["ville"].unique()),
        default=sorted(df["ville"].unique()),
    )

    if len(periode) == 2:
        masque = (
            (df["date_prospection"].dt.date >= periode[0])
            & (df["date_prospection"].dt.date <= periode[1])
            & (df["agent"].isin(agents))
            & (df["ville"].isin(villes))
        )
    else:
        masque = df["agent"].isin(agents) & df["ville"].isin(villes)
    df_f = df[masque]

    if df_f.empty:
        st.warning("Aucun prospect ne correspond aux filtres sélectionnés.")
        return

    # ---------- KPI ----------
    total = len(df_f)
    convertis = int((df_f["statut"] == "Converti").sum())
    taux_conversion = convertis / total * 100
    pipeline = int(df_f.loc[df_f["statut"].isin(["Qualifié", "Converti"]), "montant_potentiel"].sum())
    agents_actifs = df_f["agent"].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Prospects", f"{total:,}".replace(",", " "))
    col2.metric("Taux de conversion", f"{taux_conversion:.1f} %")
    col3.metric("Valeur du pipeline", f"{pipeline:,} $".replace(",", " "))
    col4.metric("Agents actifs", agents_actifs)

    st.divider()

    # ---------- Graphiques ----------
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("Évolution mensuelle des prospects")
        mensuel = (
            df_f.groupby(["mois", "statut"]).size().reset_index(name="prospects")
        )
        fig = px.bar(
            mensuel, x="mois", y="prospects", color="statut",
            category_orders={"statut": ORDRE_STATUTS},
            labels={"mois": "Mois", "prospects": "Prospects"},
        )
        fig.update_layout(xaxis_tickangle=-45, legend_title="Statut")
        st.plotly_chart(fig, use_container_width=True)

    with col_g2:
        st.subheader("Performance par agent")
        par_agent = (
            df_f.groupby("agent")
            .agg(prospects=("id", "count"), convertis=("statut", lambda s: (s == "Converti").sum()))
            .reset_index()
        )
        par_agent["taux_conversion"] = par_agent["convertis"] / par_agent["prospects"] * 100
        par_agent = par_agent.sort_values("convertis", ascending=False)
        fig = px.bar(
            par_agent, x="agent", y="convertis", color="taux_conversion",
            labels={"agent": "Agent", "convertis": "Prospects convertis",
                    "taux_conversion": "Taux de conversion (%)"},
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig, use_container_width=True)

    col_g3, col_g4 = st.columns(2)

    with col_g3:
        st.subheader("Entonnoir de conversion")
        entonnoir = (
            df_f["statut"].value_counts().reindex(ORDRE_STATUTS).fillna(0).reset_index()
        )
        entonnoir.columns = ["statut", "prospects"]
        fig = px.funnel(
            entonnoir, x="prospects", y="statut",
            labels={"prospects": "Prospects", "statut": "Statut"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_g4:
        st.subheader("Répartition par ville et par source")
        par_ville = df_f["ville"].value_counts().reset_index()
        par_ville.columns = ["ville", "prospects"]
        fig_ville = px.bar(
            par_ville, x="ville", y="prospects",
            labels={"ville": "Ville", "prospects": "Prospects"},
        )
        fig_ville.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_ville, use_container_width=True)
        par_source = df_f["source"].value_counts().reset_index()
        par_source.columns = ["source", "prospects"]
        fig_source = px.pie(
            par_source, names="source", values="prospects",
            title="Répartition par source de prospection",
        )
        st.plotly_chart(fig_source, use_container_width=True)

    st.divider()

    # ---------- Table consultable + export ----------
    st.subheader("Prospects")
    recherche = st.text_input("🔎 Rechercher (nom, ville, agent, statut)", "")
    df_table = df_f
    if recherche:
        r = recherche.lower()
        df_table = df_f[
            df_f["nom"].str.lower().str.contains(r, na=False)
            | df_f["prenom"].str.lower().str.contains(r, na=False)
            | df_f["ville"].str.lower().str.contains(r, na=False)
            | df_f["agent"].str.lower().str.contains(r, na=False)
            | df_f["statut"].str.lower().str.contains(r, na=False)
        ]
    st.dataframe(
        df_table.sort_values("date_prospection", ascending=False),
        use_container_width=True, hide_index=True,
    )
    st.download_button(
        "⬇️ Exporter la sélection en CSV",
        df_table.to_csv(index=False).encode("utf-8"),
        file_name="prospects_filtres.csv",
        mime="text/csv",
    )

    st.caption(
        "Données entièrement synthétiques — aucun vrai client, aucun vrai nom. "
        "Projet de démonstration réalisé par Cheikhouna Kébé."
    )


if __name__ == "__main__":
    main()
