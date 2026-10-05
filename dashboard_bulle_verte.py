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

API_KEY = "438930b1-43ad-4b12-8870-c3b4937240da"

def generer_fausses_donnees(region, type_struct):
    nom_type = "Hôtel" if type_struct == "Hôtels" else "Camping" if type_struct == "Campings (HPA)" else "Office"
    return pd.DataFrame({
        "Nom": [
            f"{nom_type} de la Vallée", f"Le Grand {nom_type} Nature", f"Éco-Domaine ({nom_type})",
            f"{nom_type} des Pins", f"Le Petit {nom_type} Bleu", f"{nom_type} du Lac"
        ],
        "Région": [region] * 6,
        "Type": [type_struct] * 6,
        "Adresse": ["12 route des Vallées, 33000", "45 avenue de la Forêt, 17000", "8 place de l'Église, 24000", "1 chemin du Lac, 40150", "99 route Bleue, 64200", "5 boulevard Fleuri, 86000"],
        "Email": ["direction@vallee.fr", "contact@grand-nature.fr", "hello@ecodomaine.com", "info@les-pins.fr", "resa@petitbleu.com", "contact@dulac.fr"],
        "Téléphone": ["04 11 22 33 44", "04 55 66 77 88", "04 99 88 77 66", "04 22 33 44 55", "04 66 77 88 99", "04 12 34 56 78"]
    })

# LE BOUTON DE DÉCLENCHEMENT EST ICI :
if st.sidebar.button("🚀 Lancer l'extraction"):
    with st.spinner("Connexion aux bases de données en cours..."):
        df = pd.DataFrame()
        
        if "DIRECT" in source_donnees or "LIVE" in source_donnees:
            try:
                url = f"https://diffuseur.datatourisme.fr/webservice/74a3c8b7a789a8ab9a1448f5f9c53d71/{API_KEY}"
                reponse = requests.get(url, timeout=30)
                
                if reponse.status_code == 200:
                    try:
                        donnees = reponse.json()
                        pois = donnees.get('@graph', donnees.get('data', []))
                        if pois:
                            df = pd.DataFrame([{"Nom": p.get('rdfs:label', p.get('name', 'Inconnu')), "Région": region_choisie, "Type": type_structure} for p in pois])
                        else:
                            st.error("❌ Le fichier ne contient pas les données attendues.")
                            df = generer_fausses_donnees(region_choisie, type_structure)
                    except Exception as e:
                        st.error(f"❌ Le format reçu n'est pas du JSON lisible. (Détail: {e})")
                        df = generer_fausses_donnees(region_choisie, type_structure)
                else:
                    st.warning(f"❌ L'API DATAtourisme a refusé l'accès. Code : {reponse.status_code}")
                    df = generer_fausses_donnees(region_choisie, type_structure)
            except Exception as e:
                st.warning(f"❌ Surcharge mémoire ou serveur inaccessible. (Détail: {e})")
                df = generer_fausses_donnees(region_choisie, type_structure)
                
        else:
            if type_structure == "Tous les hébergements":
                fichiers = ["Export_Campings.csv", "Export_Hôtels.csv", "Export_Office du tourisme.csv"]
                liste_df = [pd.read_csv(f, sep=';', encoding='utf-8', on_bad_lines='skip') for f in fichiers if os.path.exists(f)]
                if liste_df:
                    df = pd.concat(liste_df, ignore_index=True)
                else:
                    st.warning("💡 Aucun fichier trouvé. Activation de l'échantillon.")
                    df = generer_fausses_donnees(region_choisie, type_structure)
            else:
                fichiers_map = {"Campings (HPA)": "Export_Campings.csv", "Hôtels": "Export_Hôtels.csv", "Offices de Tourisme": "Export_Office du tourisme.csv"}
                fichier_a_charger = fichiers_map.get(type_structure, "")
                if os.path.exists(fichier_a_charger):
                    df = pd.read_csv(fichier_a_charger, sep=';', encoding='utf-8', on_bad_lines='skip')
                else:
                    st.warning(f"💡 Fichier {fichier_a_charger} introuvable. Activation de l'échantillon.")
                    df = generer_fausses_donnees(region_choisie, type_structure)

    if not df.empty:
        st.success(f"✅ Données qualifiées et prêtes pour la séquence '{type_structure}'.")
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 Exporter la liste (CSV)", data=csv, file_name="Prospects_LaBulleVerte.csv", mime="text/csv")
else:
    st.info("👈 Ajustez vos filtres dans le menu de gauche et cliquez sur 'Lancer l'extraction' pour démarrer.")
