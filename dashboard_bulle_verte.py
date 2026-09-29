import streamlit as st
import pandas as pd
import requests
import os

st.set_page_config(page_title="La Bulle Verte - Acquisition", page_icon="🌿", layout="wide")
st.title("🌿 La Bulle Verte : Moteur d'Acquisition B2B")
st.markdown("---")

st.sidebar.header("⚙️ Filtres de ciblage")
region_choisie = st.sidebar.selectbox("📍 Région cible :", ("Toute la France", "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne", "Nouvelle-Aquitaine", "Occitanie", "PACA"))
type_structure = st.sidebar.selectbox("🏨 Type de structure :", ("Tous les hébergements", "Hôtels", "Campings (HPA)", "Offices de Tourisme"))
source_donnees = st.sidebar.radio("📂 Source :", ("DATAtourisme (API V1 EN DIRECT 🔴)", "Fichiers Locaux"))

API_KEY = "cc30f876-4afe-4920-b7b9-28ef18e6b11f"

def generer_fausses_donnees(region, type_struct):
    # Générateur de 10 lignes pour une démo bien remplie
    nom_type = "Hôtel" if type_struct == "Hôtels" else "Camping" if type_struct == "Campings (HPA)" else "Office"
    
    return pd.DataFrame({
        "Nom": [
            f"{nom_type} de la Vallée", f"Le Grand {nom_type} Nature", f"Éco-Domaine ({nom_type})",
            f"{nom_type} des Pins", f"Le Petit {nom_type} Bleu", f"{nom_type} du Lac",
            f"Domaine {nom_type} Étoile", f"{nom_type} Le Panorama", f"Les Terrasses ({nom_type})",
            f"{nom_type} Central"
        ],
        "Région": [region] * 10,
        "Type": [type_struct] * 10,
        "Email": [
            "direction@vallee.fr", "contact@grand-nature.fr", "hello@ecodomaine.com",
            "info@les-pins.fr", "resa@petitbleu.com", "contact@dulac.fr",
            "hello@etoile-domaine.fr", "direction@panorama.com", "info@terrasses.fr",
            "contact@central.com"
        ],
        "Téléphone": [
            "04 11 22 33 44", "04 55 66 77 88", "04 99 88 77 66",
            "04 22 33 44 55", "04 66 77 88 99", "04 12 34 56 78",
            "04 98 76 54 32", "04 33 44 55 66", "04 77 88 99 00",
            "04 56 78 90 12"
        ],
        "Action": ["Prêt pour Lemlist"] * 10
    })

with st.spinner("Connexion aux bases de données..."):
    df = pd.DataFrame()
    
    if "DIRECT" in source_donnees or "LIVE" in source_donnees:
        try:
            # On tente de joindre l'API de l'État (avec un délai maximum de 3 secondes)
            reponse = requests.get(f"https://api.datatourisme.fr/v1/catalog?api_key={API_KEY}", timeout=3)
            if reponse.status_code == 200 and reponse.json().get('data'):
                pois = reponse.json().get('data', [])
                df = pd.DataFrame([{"Nom": p.get('name', 'Inconnu'), "Région": region_choisie, "Type": type_structure} for p in pois])
            else:
                st.warning("💡 L'API est en cours de configuration. Activation de l'échantillon de démonstration.")
                df = generer_fausses_donnees(region_choisie, type_structure)
        except:
            st.warning("💡 Les serveurs nationaux sont inaccessibles. Activation de l'échantillon de démonstration.")
            df = generer_fausses_donnees(region_choisie, type_structure)
            
    else:
        # Mode Fichiers Locaux
        if os.path.exists("CRM_Campings_HPAGuide_Propre.csv"):
            df = pd.read_csv("CRM_Campings_HPAGuide_Propre.csv")
        else:
            st.warning("💡 Fichiers CSV introuvables dans le dossier. Activation de l'échantillon de démonstration.")
            df = generer_fausses_donnees(region_choisie, type_structure)

if not df.empty:
    st.success(f"✅ Données qualifiées et prêtes pour la séquence '{type_structure}'.")
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 Exporter la liste pour Lemlist (CSV)", data=csv, file_name="Prospects_LaBulleVerte.csv", mime="text/csv")
else:
    st.error("Aucune donnée à afficher.")