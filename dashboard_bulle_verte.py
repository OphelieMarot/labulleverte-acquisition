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
    # Générateur de 10 lignes avec l'Adresse et sans la colonne Action
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
        "Adresse": [
            "12 route des Vallées, 33000", "45 avenue de la Forêt, 17000", "8 place de l'Église, 24000",
            "1 chemin du Lac, 40150", "99 route Bleue, 64200", "5 boulevard Fleuri, 86000",
            "22 allée des Pins, 33120", "7 rue du Marché, 19100", "14 avenue du Pont, 87000",
            "3 place de la Mairie, 64000"
        ],
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
        ]
    })

with st.spinner("Connexion aux bases de données..."):
    df = pd.DataFrame()
    
 if "DIRECT" in source_donnees or "LIVE" in source_donnees:
        try:
            # 1. On augmente le temps d'attente à 30 secondes pour le fichier national
            url = f"https://diffuseur.datatourisme.fr/webservice/74a3c8b7a789a8ab9a1448f5f9c53d71/{API_KEY}"
            reponse = requests.get(url, timeout=30)
            
            if reponse.status_code == 200:
                try:
                    donnees = reponse.json()
                    # 2. On vérifie le format spécifique de l'État (@graph)
                    pois = donnees.get('@graph', donnees.get('data', []))
                    
                    if pois:
                        df = pd.DataFrame([{"Nom": p.get('rdfs:label', p.get('name', 'Inconnu')), "Région": region_choisie, "Type": type_structure} for p in pois])
                    else:
                        st.error("❌ Le fichier a été reçu, mais il ne contient pas les données sous le format attendu.")
                        st.json(donnees) # Ceci affichera la structure du fichier à l'écran
                        df = generer_fausses_donnees(region_choisie, type_structure)
                except Exception as e:
                    st.error(f"❌ Le format reçu n'est pas du JSON lisible. Il s'agit probablement d'un fichier ZIP. (Détail: {e})")
                    df = generer_fausses_donnees(region_choisie, type_structure)
            else:
                st.warning(f"❌ L'API DATAtourisme a refusé l'accès. Code d'erreur : {reponse.status_code}")
                df = generer_fausses_donnees(region_choisie, type_structure)
        except Exception as e:
            st.warning(f"❌ Le téléchargement est trop long ou le serveur est inaccessible. (Détail: {e})")
            df = generer_fausses_donnees(region_choisie, type_structure)
            
    else:
        # Mode Fichiers Locaux - Branché sur VOS fichiers
        if type_structure == "Tous les hébergements":
            fichiers = ["Export_Campings.csv", "Export_Hôtels.csv", "Export_Office du tourisme.csv"]
            liste_df = []
            for f in fichiers:
                if os.path.exists(f):
                    liste_df.append(pd.read_csv(f, sep=';', encoding='utf-8', on_bad_lines='skip'))
            
            if liste_df:
                df = pd.concat(liste_df, ignore_index=True)
            else:
                st.warning("💡 Aucun fichier trouvé. Activation de l'échantillon.")
                df = generer_fausses_donnees(region_choisie, type_structure)
                
        else:
            fichier_a_charger = ""
            if type_structure == "Campings (HPA)":
                fichier_a_charger = "Export_Campings.csv"
            elif type_structure == "Hôtels":
                fichier_a_charger = "Export_Hôtels.csv"
            elif type_structure == "Offices de Tourisme":
                fichier_a_charger = "Export_Office du tourisme.csv"

            if os.path.exists(fichier_a_charger):
                df = pd.read_csv(fichier_a_charger, sep=';', encoding='utf-8', on_bad_lines='skip')
            else:
                st.warning(f"💡 Le fichier {fichier_a_charger} est introuvable. Activation de l'échantillon.")
                df = generer_fausses_donnees(region_choisie, type_structure)

if not df.empty:
    st.success(f"✅ Données qualifiées et prêtes pour la séquence '{type_structure}'.")
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 Exporter la liste (CSV)", data=csv, file_name="Prospects_LaBulleVerte.csv", mime="text/csv")
else:
    st.error("Aucune donnée à afficher.")
