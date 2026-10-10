import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# Configuration générale
st.set_page_config(page_title="Dashboard Décisionnel International", layout="wide")
st.title("🌍 Tableau de Bord Commercial & Prédictif")
st.markdown("Plateforme d'aide à la décision basée sur une base de données SQL et du Machine Learning.")

# 1. Extraction des données via SQL
conn = sqlite3.connect('commerce.db')
query = """
SELECT 
    v.id AS vente_id,
    v.date,
    v.region,
    v.produit,
    v.quantite,
    v.prix_unitaire,
    v.cout_unitaire,
    (v.quantite * v.prix_unitaire) AS chiffre_affaires,
    ((v.quantite * v.prix_unitaire) - (v.quantite * v.cout_unitaire)) AS marge_brute,
    e.nom AS commercial,
    e.performance AS score_commercial
FROM Ventes v
JOIN Employes e ON v.id_employe = e.id
"""
df = pd.read_sql_query(query, conn)
conn.close()

df['date'] = pd.to_datetime(df['date'])

# 2. Barre latérale (Filtres)
st.sidebar.header("🎯 Filtres d'Analyse")
regions_disponibles = ["Toutes"] + sorted(list(df['region'].unique()))
region_selectionnee = st.sidebar.selectbox("Filtrer par Région :", regions_disponibles)

df_filtre = df.copy()
if region_selectionnee != "Toutes":
    df_filtre = df_filtre[df_filtre['region'] == region_selectionnee]

# 3. Organisation en Onglets
tab1, tab2 = st.tabs(["📊 Suivi Commercial & KPIs", "🤖 Data Science & Prévisions des Ventes"])

# ---------------------------------------------------------
# ONGLET 1 : ANALYSE COMMERCIALE & KPIs
# ---------------------------------------------------------
with tab1:
    # Indicateurs clés
    ca_total = df_filtre['chiffre_affaires'].sum()
    marge_totale = df_filtre['marge_brute'].sum()
    taux_marge = (marge_totale / ca_total * 100) if ca_total > 0 else 0
    nb_trans = len(df_filtre)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 CA Global", f"{ca_total:,.0f} €")
    col2.metric("📈 Marge Brute", f"{marge_totale:,.0f} €")
    col3.metric("📊 Taux de Marge", f"{taux_marge:.1f} %")
    col4.metric("📦 Volume Ventes", f"{nb_trans} transactions")

    st.markdown("---")

    col_gauche, col_droite = st.columns(2)
    with col_gauche:
        st.subheader("🏆 Top Produits par Chiffre d'Affaires")
        ventes_prod = df_filtre.groupby('produit')['chiffre_affaires'].sum().reset_index()
        ventes_prod = ventes_prod.sort_values(by='chiffre_affaires', ascending=True)
        fig_prod = px.bar(ventes_prod, x='chiffre_affaires', y='produit', orientation='h',
                          color='chiffre_affaires', color_continuous_scale='Blues')
        st.plotly_chart(fig_prod, use_container_width=True)

    with col_droite:
        st.subheader("🌐 Répartition Géographique du CA")
        ca_reg = df_filtre.groupby('region')['chiffre_affaires'].sum().reset_index()
        fig_reg = px.pie(ca_reg, names='region', values='chiffre_affaires', hole=0.4)
        st.plotly_chart(fig_reg, use_container_width=True)

    st.subheader("👥 Analyse Comparative des Commerciaux")
    perf_comm = df_filtre.groupby('commercial').agg({
        'chiffre_affaires': 'sum',
        'marge_brute': 'sum',
        'score_commercial': 'mean'
    }).reset_index().sort_values(by='chiffre_affaires', ascending=False)
    
    fig_comm = px.bar(
        perf_comm, x='commercial', y='chiffre_affaires',
        color='score_commercial', color_continuous_scale='Viridis',
        labels={'score_commercial': 'Score Perf (%)', 'chiffre_affaires': 'CA (€)'},
        title="Performance financière vs Score d'évaluation du vendeur"
    )
    st.plotly_chart(fig_comm, use_container_width=True)

# ---------------------------------------------------------
# ONGLET 2 : DATA SCIENCE & PRÉVISION DU CA FUTUR
# ---------------------------------------------------------
with tab2:
    st.header("📈 Prévision du Chiffre d'Affaires par Machine Learning")
    st.markdown("""
    Ce modèle analyse **la tendance historique des ventes mensuelles** pour projeter le chiffre d'affaires 
    sur les mois à venir afin d'aider à la planification des approvisionnements et à la gestion budgétaire.
    """)

    # A. Préparation des séries temporelles (Agrégation mensuelle)
    df_mensuel = df_filtre.copy()
    df_mensuel['mois'] = df_mensuel['date'].dt.to_period('M').dt.to_timestamp()
    serie_mensuelle = df_mensuel.groupby('mois')['chiffre_affaires'].sum().reset_index()
    serie_mensuelle = serie_mensuelle.sort_values('mois').reset_index(drop=True)

    if len(serie_mensuelle) >= 6:
        # B. Entraînement du modèle de régression
        serie_mensuelle['index_temps'] = np.arange(len(serie_mensuelle))
        
        X = serie_mensuelle[['index_temps']]
        y = serie_mensuelle['chiffre_affaires']
        
        modele = LinearRegression()
        modele.fit(X, y)

        # C. Paramètre de projection (Slider)
        horizon = st.slider("Choisissez l'horizon de prévision (en mois) :", min_value=1, max_value=12, value=6)

        # D. Calcul des prévisions futures
        derniere_date = serie_mensuelle['mois'].max()
        dates_futures = [derniere_date + pd.DateOffset(months=i) for i in range(1, horizon + 1)]
        indices_futurs = np.arange(len(serie_mensuelle), len(serie_mensuelle) + horizon).reshape(-1, 1)
        previsions_ca = modele.predict(indices_futurs)

        df_previsions = pd.DataFrame({
            'mois': dates_futures,
            'chiffre_affaires_prevu': previsions_ca
        })

        # Affichage du total prévisionnel
        ca_estime = df_previsions['chiffre_affaires_prevu'].sum()
        st.info(f"🔮 **Chiffre d'affaires estimé sur les {horizon} prochains mois : {ca_estime:,.0f} €**")

        # E. Graphique interactif Plotly combinant Passé et Futur
        fig_prev = go.Figure()

        # Courbe historique réelle
        fig_prev.add_trace(go.Scatter(
            x=serie_mensuelle['mois'],
            y=serie_mensuelle['chiffre_affaires'],
            mode='lines+markers',
            name='CA Réel Historique',
            line=dict(color='#1f77b4', width=3)
        ))

        # Courbe prédictive future
        fig_prev.add_trace(go.Scatter(
            x=df_previsions['mois'],
            y=df_previsions['chiffre_affaires_prevu'],
            mode='lines+markers',
            name='Projection Machine Learning',
            line=dict(color='#ff7f0e', width=3, dash='dash')
        ))

        fig_prev.update_layout(
            title="Évolution historique et Projection du CA futur",
            xaxis_title="Période (Mois)",
            yaxis_title="Chiffre d'Affaires (€)",
            hovermode="x unified"
        )

        st.plotly_chart(fig_prev, use_container_width=True)

    else:
        st.warning("Données insuffisantes pour faire une prévision avec ce filtre.")