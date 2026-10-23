"""Dashboard Boréal Assurances : Portefeuille, Technique et clients, Exploitation, Définitions.

Alimenté uniquement par les marts de l'entrepôt (schéma marts) et par les définitions
d'indicateurs de analyse/indicateurs.py, partagées avec les notebooks du dossier.
Lancement : make dashboard
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analyse.indicateurs import decomposer_sp, indicateurs, lire, ratios

SEUIL_SP = 0.70  # justification : page Définitions
BLEU, ROUGE, GRIS, VERT = "#4f81bd", "#c0504d", "#7f7f7f", "#9bbb59"

st.set_page_config(page_title="Boréal Assurances · Pilotage", page_icon="📊", layout="wide")


# --- Données (marts uniquement, mises en cache) ----------------------------------------------------

@st.cache_data(show_spinner=False)
def charger(nom: str, ordre: str = "ALL") -> pd.DataFrame:
    return lire(f"SELECT * FROM marts.{nom} ORDER BY {ordre}")


mensuel = charger("mart_portefeuille_mensuel")
technique = charger("mart_technique")
retention = charger("mart_retention_contrats")
clients = charger("mart_clients", "client_id")
sinistres = charger("mart_sinistres", "sinistre_id")


# --- Filtres croisés ------------------------------------------------------------------------------

st.sidebar.title("Filtres")
annees = sorted(mensuel["annee"].unique())
periode = st.sidebar.select_slider("Période (années)", options=annees, value=(annees[0], annees[-1]),
                                   help="Années de survenance des sinistres et d'acquisition des primes. 2025 : janvier à juin.")
produits = st.sidebar.multiselect("Produit", ["AUTO", "HABITATION"], default=["AUTO", "HABITATION"])
regions = st.sidebar.multiselect("Région", sorted(mensuel["region"].dropna().unique()), placeholder="Toutes")
canaux = st.sidebar.multiselect("Canal", ["AGENT", "COURTIER", "WEB"], placeholder="Tous")
zones = st.sidebar.multiselect("Zone de risque", [1, 2, 3, 4, 5], placeholder="Toutes")
hors_atypique = st.sidebar.toggle("Exclure le sinistre atypique (2,48 M€, 2023)", value=False,
                                  help="Le sinistre 1129 pèse 22 % de toute la charge 2020-2025 (règle SIN_08).")
st.sidebar.caption("Les filtres s'appliquent à toutes les pages, sauf la page Exploitation. "
                   "La rétention n'est filtrable que par produit et période de souscription.")


def filtrer(df: pd.DataFrame, colonne_annee: str = "annee", avec_periode: bool = True) -> pd.DataFrame:
    masque = df["produit"].isin(produits)
    if avec_periode:
        masque &= df[colonne_annee].between(*periode)
    if regions and "region" in df:
        masque &= df["region"].isin(regions)
    if canaux and "canal_distribution" in df:
        masque &= df["canal_distribution"].isin(canaux)
    if zones and "zone_risque" in df:
        masque &= df["zone_risque"].isin(zones)
    return df[masque]


def avec_charge(df: pd.DataFrame) -> pd.DataFrame:
    """Utilise la charge hors sinistre atypique si l'option est cochée."""
    if hors_atypique:
        df = df.copy()
        df["charge"] = df["charge_hors_atypique"]
    return df


def pct(x: float) -> str:
    return "–" if pd.isna(x) else f"{100 * x:,.1f} %".replace(",", " ").replace(".", ",")


def euros(x: float) -> str:
    return "–" if pd.isna(x) else f"{x:,.0f} €".replace(",", " ")


# --- Page 1 : Portefeuille ------------------------------------------------------------------------

def page_portefeuille():
    st.title("Portefeuille")
    m = avec_charge(filtrer(mensuel))
    if m.empty:
        st.warning("Aucune donnée pour cette sélection.")
        return
    annee_n = int(m["annee"].max())
    mois_max = int(m.loc[m["annee"] == annee_n, "num_mois"].max())
    # Comparaison à période égale : mêmes mois de l'année précédente
    n = m[(m["annee"] == annee_n) & (m["num_mois"] <= mois_max)]
    # N-1 est pris hors filtre de période, pour toujours disposer de la comparaison
    n1 = avec_charge(filtrer(mensuel, avec_periode=False))
    n1 = n1[(n1["annee"] == annee_n - 1) & (n1["num_mois"] <= mois_max)]

    def kpi(d):
        t = d.sum(numeric_only=True)
        actifs = d[d["mois"] == d["mois"].max()]["contrats_actifs"].sum() if len(d) else np.nan
        return {"primes": t["prime_acquise"], "actifs": actifs,
                "freq": t["nb_sinistres"] / t["annees_police"] if t["annees_police"] else np.nan,
                "cout": t["charge"] / t["nb_sinistres"] if t["nb_sinistres"] else np.nan,
                "sp": t["charge"] / t["prime_acquise"] if t["prime_acquise"] else np.nan,
                "resil": t["nb_resiliations"] / t["annees_police"] if t["annees_police"] else np.nan}

    k, k1 = kpi(n), kpi(n1)
    libelle = f"{annee_n}, janvier à {['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'][mois_max]}"
    st.caption(f"Indicateurs {libelle}, comparés aux mêmes mois de {annee_n - 1}. "
               "Les sinistres sont rattachés à leur mois de survenance ; les montants récents incluent des réserves.")
    if k["sp"] > SEUIL_SP:
        st.error(f"⚠️ Alerte : le S/P {libelle} atteint {pct(k['sp'])}, au-dessus du seuil de {pct(SEUIL_SP)} "
                 "(au-delà, les frais de gestion et d'acquisition ne sont plus couverts : voir Définitions).")
    c = st.columns(3) + st.columns(3)
    def delta(a, b, fmt):
        return None if pd.isna(a) or pd.isna(b) or b == 0 else fmt(a - b)
    c[0].metric("Primes acquises", euros(k["primes"]), delta(k["primes"], k1["primes"], lambda x: ("+" if x > 0 else "") + euros(x)),
                help="Prime annuelle × jours couverts / 365, sur la période.")
    c[1].metric("Contrats actifs (fin de période)", f"{k['actifs']:,.0f}".replace(",", " "),
                delta(k["actifs"], k1["actifs"], lambda x: f"{x:+,.0f}".replace(",", " ")))
    c[2].metric("Fréquence annualisée", pct(k["freq"]), delta(k["freq"], k1["freq"], lambda x: f"{100*x:+.2f} pt".replace(".", ",")),
                delta_color="inverse", help="Sinistres avec suite / années-police.")
    c[3].metric("Coût moyen", euros(k["cout"]), delta(k["cout"], k1["cout"], lambda x: f"{x:+,.0f} €".replace(",", " ")),
                delta_color="inverse", help="Charge (payé + réserve restante) / sinistres avec suite.")
    c[4].metric("S/P", pct(k["sp"]), delta(k["sp"], k1["sp"], lambda x: f"{100*x:+.1f} pt".replace(".", ",")),
                delta_color="inverse", help="Charge / primes acquises.")
    c[5].metric("Taux de résiliation annualisé", pct(k["resil"]), delta(k["resil"], k1["resil"], lambda x: f"{100*x:+.1f} pt".replace(".", ",")),
                delta_color="inverse", help="Résiliations / années-police.")

    # Évolution mensuelle : S/P cumulé depuis janvier, année N contre N-1
    mm = avec_charge(filtrer(mensuel, avec_periode=False))
    mm = mm[mm["annee"].isin([annee_n, annee_n - 1])].groupby(["annee", "num_mois"], as_index=False)[
        ["prime_acquise", "charge", "nb_sinistres", "annees_police", "contrats_actifs", "nb_resiliations"]].sum()
    mm = mm.sort_values(["annee", "num_mois"])
    mm["sp_cumule"] = mm.groupby("annee")["charge"].cumsum() / mm.groupby("annee")["prime_acquise"].cumsum()
    mm["frequence"] = mm["nb_sinistres"] / mm["annees_police"]
    mm["annee"] = mm["annee"].astype(str)
    sp_fin = mm[mm["annee"] == str(annee_n)]["sp_cumule"].iloc[-1]
    sp_fin1 = mm[(mm["annee"] == str(annee_n - 1)) & (mm["num_mois"] == mm[mm["annee"] == str(annee_n)]["num_mois"].max())]["sp_cumule"]
    tendance = "au-dessus" if len(sp_fin1) and sp_fin > sp_fin1.iloc[0] else "en dessous"
    g = px.line(mm, x="num_mois", y="sp_cumule", color="annee", markers=True,
                color_discrete_map={str(annee_n): ROUGE, str(annee_n - 1): GRIS},
                labels={"num_mois": "mois", "sp_cumule": "S/P cumulé depuis janvier", "annee": "année"},
                title=f"Le S/P cumulé {annee_n} est {tendance} de celui de {annee_n - 1} à période égale ({pct(sp_fin)})")
    g.add_hline(y=SEUIL_SP, line_dash="dash", line_color=ROUGE, annotation_text=f"seuil d'alerte {pct(SEUIL_SP)}")
    g.update_yaxes(tickformat=".0%")
    g.update_traces(hovertemplate="mois %{x}<br>S/P cumulé : %{y:.1%}<extra>%{fullData.name}</extra>")
    alerte = mm[(mm["sp_cumule"] > SEUIL_SP)]
    if len(alerte):
        g.add_scatter(x=alerte["num_mois"], y=alerte["sp_cumule"], mode="markers", name="au-dessus du seuil",
                      marker=dict(color=ROUGE, size=14, symbol="circle-open", line=dict(width=3)))
    st.plotly_chart(g, width="stretch")

    col1, col2 = st.columns(2)
    g2 = px.bar(mm, x="num_mois", y="nb_sinistres", color="annee", barmode="group",
                color_discrete_map={str(annee_n): BLEU, str(annee_n - 1): GRIS},
                labels={"num_mois": "mois", "nb_sinistres": "sinistres avec suite survenus", "annee": "année"},
                title="Sinistres par mois de survenance : comparer N à N-1 mois par mois")
    g2.update_traces(hovertemplate="mois %{x}<br>%{y} sinistres<extra>%{fullData.name}</extra>")
    col1.plotly_chart(g2, width="stretch")
    g3 = px.line(mm, x="num_mois", y="contrats_actifs", color="annee", markers=True,
                 color_discrete_map={str(annee_n): BLEU, str(annee_n - 1): GRIS},
                 labels={"num_mois": "mois", "contrats_actifs": "contrats actifs en fin de mois", "annee": "année"},
                 title="Contrats actifs en fin de mois : le portefeuille croît-il encore ?")
    col2.plotly_chart(g3, width="stretch")

    # Historique annuel complet de la sélection
    an = ratios(avec_charge(filtrer(mensuel)).groupby("annee", as_index=False)[
        ["prime_acquise", "charge", "charge_hors_atypique", "nb_sinistres", "annees_police", "nb_resiliations",
         "reserve_restante", "nb_sinistres_sans_suite"]].sum().assign(nb_sinistres_declares=lambda d: d["nb_sinistres"] + d["nb_sinistres_sans_suite"]))
    g4 = go.Figure()
    g4.add_bar(x=an["annee"], y=an["sp"], marker_color=[ROUGE if v > SEUIL_SP else BLEU for v in an["sp"]],
               hovertemplate="%{x}<br>S/P : %{y:.1%}<extra></extra>", name="S/P")
    g4.add_hline(y=SEUIL_SP, line_dash="dash", line_color=ROUGE)
    g4.update_layout(title="S/P annuel : les années en rouge dépassent le seuil (2025 : six mois, réserves incluses)",
                     yaxis_tickformat=".0%", showlegend=False)
    st.plotly_chart(g4, width="stretch")


# --- Page 2 : Technique et clients ----------------------------------------------------------------

ORDRE_AGES = ["18-25", "26-35", "36-50", "51-65", "66+", "Inconnu"]


def barres_sp(t: pd.DataFrame, axe: str, libelle: str, action: str):
    """S/P par segment ; le titre nomme le segment le plus cher de la sélection et l'action associée."""
    d = indicateurs(avec_charge(t), [axe])
    d[axe] = d[axe].astype(str)
    ordre = ORDRE_AGES if axe == "tranche_age" else sorted(d[axe])
    pire = d.loc[d["sp"].idxmax()]
    titre = f"{libelle.capitalize()} {pire[axe]} : S/P le plus élevé ({pct(pire['sp'])})<br>→ {action}"
    g = px.bar(d, x=axe, y="sp", labels={axe: libelle, "sp": "S/P"}, title=titre,
               category_orders={axe: [o for o in ordre if o in set(d[axe])]},
               custom_data=["frequence", "cout_moyen", "prime_moyenne", "annees_police"],
               color=d["sp"] > SEUIL_SP, color_discrete_map={True: ROUGE, False: BLEU})
    g.update_traces(hovertemplate="%{x}<br>S/P : %{y:.1%}<br>fréquence : %{customdata[0]:.2%}<br>"
                                  "coût moyen : %{customdata[1]:,.0f} €<br>prime moyenne : %{customdata[2]:,.0f} €"
                                  "<br>années-police : %{customdata[3]:,.0f}<extra></extra>")
    g.add_hline(y=SEUIL_SP, line_dash="dash", line_color=ROUGE)
    g.update_layout(showlegend=False, yaxis_tickformat=".0%")
    return g


def page_technique():
    st.title("Technique et clients")
    t = filtrer(technique)
    if t.empty:
        st.warning("Aucune donnée pour cette sélection.")
        return
    st.subheader("Ratio sinistres sur primes par segment")
    c1, c2 = st.columns(2)
    c1.plotly_chart(barres_sp(t, "zone_risque", "zone", "vérifier que la prime suit la fréquence"), width="stretch")
    c2.plotly_chart(barres_sp(t, "formule", "formule", "revoir sa prime et ses garanties"), width="stretch")
    c3, c4 = st.columns(2)
    c3.plotly_chart(barres_sp(t, "canal_distribution", "canal", "comparer hors sinistre atypique avant d'agir"), width="stretch")
    c4.plotly_chart(barres_sp(t, "tranche_age", "tranche d'âge", "contrôler l'adéquation du tarif"), width="stretch")
    st.caption("Barres rouges : S/P au-dessus du seuil d'alerte. Survolez une barre pour la fréquence, le coût moyen et la prime moyenne.")

    st.subheader("Décomposition de l'évolution du S/P")
    annuel = indicateurs(avec_charge(t), ["annee"])
    if len(annuel) >= 2 and (annuel["nb_sinistres"] > 0).all():
        d = decomposer_sp(annuel)
        long = d.melt(id_vars="annee", value_vars=["effet_frequence", "effet_cout_moyen", "effet_prime_moyenne"],
                      var_name="effet", value_name="points")
        long["effet"] = long["effet"].map({"effet_frequence": "fréquence", "effet_cout_moyen": "coût moyen", "effet_prime_moyenne": "prime moyenne"})
        g = px.bar(long, x="annee", y="points", color="effet", barmode="relative",
                   color_discrete_map={"fréquence": BLEU, "coût moyen": ROUGE, "prime moyenne": VERT},
                   title="Le coût moyen explique l'essentiel des variations du S/P ; la prime moyenne est figée<br>→ piloter les sinistres graves et réviser les primes",
                   labels={"annee": "année", "points": "contribution à la variation du S/P"})
        g.add_scatter(x=d["annee"], y=d["variation_sp"], mode="markers", marker=dict(color="black", size=10), name="variation totale",
                      hovertemplate="%{x}<br>variation : %{y:+.1%}<extra></extra>")
        g.update_traces(selector=dict(type="bar"), hovertemplate="%{x}<br>%{fullData.name} : %{y:+.1%}<extra></extra>")
        g.update_layout(yaxis_tickformat="+.0%")
        st.plotly_chart(g, width="stretch")
        st.caption("Méthode LMDI : S/P = fréquence × coût moyen / prime moyenne ; la somme des effets égale la variation. "
                   "L'effet du volume de contrats sur le ratio est nul par construction.")
    else:
        st.info("Sélection trop étroite pour décomposer l'évolution (il faut au moins deux années avec sinistres).")

    st.subheader("Clients")
    c1, c2 = st.columns(2)
    r = retention[retention["cellule_complete"] & retention["produit"].isin(produits) & retention["cohorte"].between(*periode)]
    if len(r):
        mat = r.groupby(["cohorte", "anciennete_annees"])[["nb_retenus", "nb_contrats"]].sum()
        mat = (mat["nb_retenus"] / mat["nb_contrats"]).unstack()
        g = px.imshow(mat.values, x=[f"{a} an{'s' if a > 1 else ''}" for a in mat.columns], y=[str(c) for c in mat.index],
                      color_continuous_scale="Blues", zmin=0.4, zmax=1, text_auto=".0%", aspect="auto",
                      title="Rétention par cohorte : 14 % des contrats perdus dès la 1re année<br>→ cibler la première échéance",
                      labels=dict(x="ancienneté", y="cohorte de souscription", color="rétention"))
        g.update_traces(hovertemplate="cohorte %{y}, %{x}<br>rétention : %{z:.1%}<extra></extra>")
        c1.plotly_chart(g, width="stretch")
        c1.caption("Seules les cellules entièrement observables au 30/06/2025 sont affichées.")
    cl = clients[clients["produits"].apply(lambda p: any(x in p.split("+") for x in produits))]
    if regions:
        cl = cl[cl["region"].isin(regions)]
    v = cl["valeur_observee"].sort_values(ascending=False).to_numpy()
    if len(v) and v.sum() > 0:
        cumul = np.cumsum(v) / v.sum()
        x = 100 * np.arange(1, len(v) + 1) / len(v)
        part20 = cumul[max(int(0.2 * len(v)) - 1, 0)]
        g = go.Figure(go.Scatter(x=x, y=cumul, line=dict(color=BLEU),
                                 hovertemplate="%{x:.0f} % des clients<br>%{y:.0%} de la valeur<extra></extra>"))
        g.add_hline(y=1, line_dash="dash", line_color=GRIS)
        g.update_layout(title=f"Concentration de la valeur : 20 % des clients font {part20:.0%} de la valeur nette",
                        xaxis_title="% des clients, du plus rentable au moins rentable",
                        yaxis_title="valeur cumulée / valeur totale", yaxis_tickformat=".0%")
        c2.plotly_chart(g, width="stretch")
        c2.caption("Valeur observée = primes acquises − sinistres payés, 2020 à juin 2025. Filtres produit et région appliqués.")


# --- Page 3 : Exploitation ------------------------------------------------------------------------

def page_exploitation():
    st.title("Exploitation")
    charg = charger("mart_exploitation_chargements", "source")
    regles = charger("mart_exploitation_regles", "regle_id")
    tests = charger("mart_exploitation_tests", "nom")

    st.subheader("État de la chaîne")
    echecs_tests = tests[~tests["statut"].isin(["PASS", "WARN"])]
    c = st.columns(4)
    c[0].metric("Dernier chargement", f"{charg['dernier_chargement'].max():%d/%m/%Y %H:%M}")
    c[1].metric("Données à jour au", f"{charg['date_metier_max'].max():%d/%m/%Y}", help="Date métier la plus récente (paiement, déclaration, audit).")
    c[2].metric("Tests du dernier lancement", f"{(tests['statut'] == 'PASS').sum()} / {len(tests)} réussis")
    c[3].metric("Anomalies bloquantes", f"{int(regles.loc[regles['traitement'] == 'EXCLURE', 'volume'].sum()):,}".replace(",", " "),
                help="Nombre de déclenchements de règles EXCLURE ; une ligne en quarantaine peut en cumuler plusieurs.")
    if len(echecs_tests):
        st.error(f"⚠️ {len(echecs_tests)} test(s) en échec : le chargement a été interrompu en aval. Détail ci-dessous.")
    else:
        st.success("Tous les tests du dernier lancement sont au vert.")

    t = charg.rename(columns={"source": "source", "nb_fichiers": "fichiers", "lignes_lues": "lignes lues",
                              "lignes_chargees": "lignes chargées", "lignes_rejetees": "rejets à l'ingestion",
                              "dernier_chargement": "dernier chargement", "dernier_fichier": "dernier fichier",
                              "dernier_echec": "dernier échec", "date_metier_max": "date métier la plus récente"})
    st.dataframe(t.drop(columns=["dernier_passage"]), hide_index=True, width="stretch")

    st.subheader("Lignes écartées ou signalées par règle de qualité")
    r = regles[regles["volume"] > 0].sort_values("volume", ascending=False)
    premiere = r.iloc[0]
    g = px.bar(r, x="volume", y="regle_id", color="traitement", orientation="h",
               category_orders={"regle_id": list(r["regle_id"])},
               color_discrete_map={"EXCLURE": ROUGE, "CORRIGER": "#f79646", "SIGNALER": GRIS},
               custom_data=["description", "pct_lignes", "gravite"],
               title=f"{premiere['regle_id']} ({premiere['description'].lower()}) est la première anomalie : {int(premiere['volume'])} lignes"
                     "<br>→ traiter les anomalies à la source avec les services concernés",
               labels={"volume": "lignes concernées", "regle_id": "règle"})
    g.update_traces(hovertemplate="%{y} : %{customdata[0]}<br>%{x} lignes (%{customdata[1]} %)<br>gravité %{customdata[2]}<extra></extra>")
    st.plotly_chart(g, width="stretch")
    with st.expander(f"Les {len(regles)} règles, y compris celles sans anomalie"):
        st.dataframe(regles, hide_index=True, width="stretch")
    with st.expander("Résultats détaillés des tests du dernier lancement"):
        st.dataframe(tests[["nom", "statut", "echecs", "duree_s", "genere_le"]], hide_index=True, width="stretch")

    st.subheader("Délais de gestion des sinistres")
    s = filtrer(sinistres, "annee_survenance")
    q = (s.dropna(subset=["delai_premier_reglement_j"]).groupby("libelle_garantie")["delai_premier_reglement_j"]
         .quantile([0.5, 0.9]).unstack().rename(columns={0.5: "médiane", 0.9: "90e centile"}).reset_index()
         .sort_values("médiane"))
    long = q.melt(id_vars="libelle_garantie", var_name="mesure", value_name="jours")
    g = px.bar(long, x="jours", y="libelle_garantie", color="mesure", barmode="group", orientation="h",
               color_discrete_map={"médiane": BLEU, "90e centile": GRIS},
               title="Premier règlement : environ 50 jours en médiane quelle que soit la garantie<br>→ objectif proposé : 60 jours",
               labels={"libelle_garantie": "garantie", "jours": "jours entre déclaration et premier règlement"})
    g.add_vline(x=60, line_dash="dash", line_color=ROUGE, annotation_text="objectif 60 j")
    g.update_traces(hovertemplate="%{y}<br>%{fullData.name} : %{x:.0f} jours<extra></extra>")
    st.plotly_chart(g, width="stretch")
    p = s.dropna(subset=["delai_premier_reglement_j"])
    if len(p):
        st.caption(f"{pct((p['delai_premier_reglement_j'] <= 60).mean())} des {len(p):,} dossiers payés de la sélection ".replace(",", " ")
                   + "ont reçu un premier règlement sous 60 jours. Les filtres de période, produit, région, canal et zone s'appliquent.")


# --- Page 4 : Définitions -------------------------------------------------------------------------

def page_definitions():
    st.title("Définitions")
    st.markdown(f"""
Tous les chiffres viennent de l'entrepôt DuckDB (schéma `marts`), reconstruit par `make run`. Ce sont les mêmes que ceux du dossier.

| Indicateur | Définition |
|---|---|
| **Années-police** | Durée de couverture en années : jours couverts / 365. Base de toute fréquence. |
| **Primes acquises** | Prime annuelle × jours couverts / 365 sur la période. |
| **Contrats actifs** | Contrats couverts le dernier jour du mois (ou au 30/06/2025). |
| **Fréquence** | Sinistres avec suite (ouverts ou clôturés) / années-police, sur un an. |
| **Sinistres sans suite** | Sinistres rejetés ou classés sans suite : comptés à part, ils ne coûtent rien. |
| **Charge** | Règlements payés + réserve restante des dossiers encore ouverts. |
| **Coût moyen** | Charge / sinistres avec suite. |
| **Prime moyenne** | Primes acquises / années-police. |
| **S/P** | Charge / primes acquises. Égal à fréquence × coût moyen / prime moyenne. |
| **Taux de résiliation** | Résiliations / années-police, sur un an. |
| **Rétention à n ans** | Part des contrats d'une cohorte non résiliés à leur n-ième anniversaire. Seules les cohortes entièrement observables sont affichées. |
| **Valeur observée d'un client** | Primes acquises − sinistres payés, de 2020 au 30/06/2025. |
| **Délai de premier règlement** | Jours entre la déclaration et le premier paiement (dossiers payés). |
| **Sinistre atypique** | Réserve initiale supérieure à 1 M€ (sinistre 1129, collision 2023, 2,48 M€ payés). |

**Seuil d'alerte du S/P : {pct(SEUIL_SP)}.** Les frais de gestion et d'acquisition d'un assureur IARD représentent couramment 25 à 30 % des primes. Au-delà d'un S/P de 70 %, le ratio combiné (sinistres + frais) approche ou dépasse 100 % : l'activité perd de l'argent. Ce seuil est une hypothèse, à remplacer par le taux de frais réel de Boréal dès qu'il sera connu. Pour mémoire, hors sinistre atypique, le S/P du portefeuille est de 46 % (IC 95 % : 42 à 51 %).

**Rattachement temporel.** Les sinistres sont rattachés à leur date de survenance. Les mois récents sont provisoires : 36 % de la charge 2025 est encore en réserve, et les sinistres survenus mais pas encore déclarés n'apparaissent pas.

**Filtres.** Période, produit, région, canal et zone s'appliquent aux pages Portefeuille, Technique et clients, et aux délais. La rétention se filtre par produit et cohorte ; la valeur client par produit et région.
""")


# Page d'accueil : Portefeuille (BOREAL_PAGE_DEFAUT permet aux tests d'ouvrir une autre page)
defaut = os.environ.get("BOREAL_PAGE_DEFAUT", "page_portefeuille")
navigation = st.navigation([
    st.Page(fonction, title=titre, icon=icone, default=fonction.__name__ == defaut)
    for fonction, titre, icone in [
        (page_portefeuille, "Portefeuille", "📈"),
        (page_technique, "Technique et clients", "🧮"),
        (page_exploitation, "Exploitation", "⚙️"),
        (page_definitions, "Définitions", "📖"),
    ]
])
navigation.run()
