"""Construit le dossier PDF (dossier/SAGDO_Boreal.pdf) à partir des documents du dépôt.

Étapes :
1. rend les diagrammes Mermaid des documents en images (Chrome via Playwright) ;
2. capture les pages du dashboard (Streamlit lancé sur un port dédié) ;
3. assemble couverture, sommaire, note exécutive, chapitres et annexes en un HTML (pandoc) ;
4. imprime le PDF (Chrome), relève la page de chaque titre et réimprime avec le sommaire paginé.

Usage : make dossier   (nécessite Google Chrome, pandoc et l'entrepôt construit par make run)
"""

import hashlib
import html
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.request
from datetime import date
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright
from pypdf import PdfReader

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "dossier"
FIGURES = DOSSIER / "figures"
SORTIE = DOSSIER / "SAGDO_Boreal.pdf"
PORT = 8599
# Nombre de morceaux de capture repris dans le dossier, par page du dashboard
GARDER = {"": 1, "page_technique": 2, "page_exploitation": 1, "page_definitions": 0}

CHAPITRES = [
    # (numéro affiché, fichier, titre)
    (None, "docs/note_executive.md", "Note exécutive"),
    (None, "dossier/sections/introduction.md", "Introduction"),
    ("1", "docs/architecture.md", "Architecture et ingestion"),
    ("2", "docs/qualite_modelisation.md", "Qualité des données et modélisation"),
    ("3", "docs/analyse_technique.md", "Analyse technique du portefeuille"),
    ("4", "docs/clients_sinistres.md", "Clients et gestion des sinistres"),
    ("5", "dossier/sections/dashboard_exploitation.md", "Dashboard, exploitation et documentation"),
    ("6", "docs/rgpd.md", "Protection des données personnelles (RGPD)"),
    (None, "dossier/sections/conclusion.md", "Conclusion"),
    (None, "dossier/sections/annexes.md", "Annexes"),
]

MERMAID = """<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:white;font-family:Helvetica,Arial}</style></head>
<body><pre class="mermaid">%s</pre><script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs";
mermaid.initialize({startOnLoad: true, theme: "neutral", flowchart: {useMaxWidth: false}, er: {useMaxWidth: false}});
</script></body></html>"""


# --- 1. Diagrammes -------------------------------------------------------------------------------

def rendre_diagrammes(navigateur, sources: dict[str, str]) -> dict[str, str]:
    """Rend chaque bloc Mermaid en PNG (mis en cache par empreinte du code)."""
    images = {}
    for code in sources:
        nom = f"mermaid_{hashlib.sha1(code.encode()).hexdigest()[:10]}.png"
        chemin = DOSSIER / "diagrammes" / nom
        chemin.parent.mkdir(exist_ok=True)
        if not chemin.exists():
            page = navigateur.new_page(device_scale_factor=2, viewport={"width": 1600, "height": 1200})
            page.set_content(MERMAID % html.escape(code))
            page.wait_for_selector("pre.mermaid svg g", state="attached", timeout=30000)
            page.wait_for_timeout(1500)  # fin du tracé (polices, positions)
            if "Syntax error" in page.inner_text("body"):
                raise RuntimeError(f"Diagramme Mermaid invalide :\n{code}")
            page.locator("pre.mermaid svg").screenshot(path=str(chemin))
            page.close()
        images[code] = nom
    return images


# --- 2. Captures du dashboard -----------------------------------------------------------------------

def capturer_dashboard(navigateur) -> list[tuple[str, str]]:
    pages = [("", "Portefeuille", "S/P cumulé"), ("page_technique", "Technique et clients", "Rétention par cohorte"),
             ("page_exploitation", "Exploitation", "Premier règlement"), ("page_definitions", "Définitions", "Seuil d'alerte")]
    serveur = subprocess.Popen(
        [str(RACINE / ".venv" / "bin" / "streamlit"), "run", "dashboard/app.py", "--server.headless", "true",
         "--server.port", str(PORT), "--browser.gatherUsageStats", "false"],
        cwd=RACINE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    captures = []
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://localhost:{PORT}/_stcore/health", timeout=1)
                break
            except OSError:
                time.sleep(0.5)
        page = navigateur.new_page(viewport={"width": 1280, "height": 4200}, device_scale_factor=1.5)
        for chemin, titre, repere in pages:
            page.goto(f"http://localhost:{PORT}/{chemin}", wait_until="domcontentloaded")
            page.wait_for_selector(f"text={repere}", timeout=60000)
            page.wait_for_timeout(3000)
            page.add_style_tag(content="header, [data-testid='stToolbar'] {display:none !important}")
            bloc = page.locator("[data-testid='stMainBlockContainer']")
            fichier = FIGURES / f"dashboard_{chemin or 'portefeuille'}.png"
            bloc.screenshot(path=str(fichier))
            morceaux = decouper(fichier)
            captures += [(f, titre) for f in morceaux[:GARDER.get(chemin, 1)]]
        page.close()
    finally:
        serveur.terminate()
    return captures


def decouper(fichier: Path, hauteur_max: int = 1900) -> list[str]:
    """Découpe une capture haute en morceaux tenant sur une page A4."""
    image = Image.open(fichier)
    largeur, hauteur = image.size
    morceaux = []
    for i, haut in enumerate(range(0, hauteur, hauteur_max)):
        morceau = image.crop((0, haut, largeur, min(haut + hauteur_max, hauteur)))
        if morceau.size[1] < 150:
            continue
        nom = f"{fichier.stem}_{i + 1}.png"
        morceau.save(FIGURES / nom)
        morceaux.append(nom)
    return morceaux


# --- 3. Assemblage --------------------------------------------------------------------------------

def adapter(texte: str, numero: str | None, titre: str, images_mermaid: dict[str, str]) -> str:
    lignes = texte.splitlines()
    if lignes and lignes[0].startswith("# "):
        lignes = lignes[1:]
    texte = "\n".join(lignes)
    entete = f"# {numero}. {titre}" if numero else f"# {titre}"
    if numero:
        texte = re.sub(r"^## (\d+)\. ", lambda m: f"## {numero}.{m.group(1)} ", texte, flags=re.M)
        texte = re.sub(r"^### (\d+)\. ", lambda m: f"### {numero}.{m.group(1)} ", texte, flags=re.M)
    def image_diagramme(m):
        if "Entrepôt DuckDB" in m.group(1):
            # Schéma d'architecture : version HTML, plus lisible en A4 que le rendu Mermaid très allongé
            return (DOSSIER / "sections" / "schema_architecture.html").read_text(encoding="utf-8")
        nom = images_mermaid[m.group(1)]
        largeur, hauteur = Image.open(DOSSIER / "diagrammes" / nom).size
        # Diagrammes très allongés (flux de gauche à droite) : pleine largeur pour rester lisibles
        classe = "diagramme-large" if largeur > 2.2 * hauteur else "diagramme"
        return f'<img class="{classe}" src="diagrammes/{nom}">'
    texte = re.sub(r"```mermaid\n(.*?)```", image_diagramme, texte, flags=re.S)
    texte = re.sub(r"!\[([^\]]*)\]\(figures/", r"![\1](../docs/figures/", texte)
    # Liens vers des fichiers du dépôt : on garde le texte (un PDF ne les ouvre pas)
    texte = re.sub(r"(?<!!)\[([^\]]+)\]\((?!http)[^)]+\)", r"\1", texte)
    return f"{entete}\n\n{texte}\n"


def assembler(images_mermaid: dict[str, str], captures: list[tuple[str, str]]) -> str:
    parties = []
    for numero, fichier, titre in CHAPITRES:
        texte = (RACINE / fichier).read_text(encoding="utf-8")
        if "{{lignage}}" in texte:
            lignage = (RACINE / "docs" / "lignage_sp.md").read_text(encoding="utf-8").splitlines()
            texte = texte.replace("{{lignage}}", "## 4. " + lignage[0].lstrip("# ") + "\n" + "\n".join(lignage[1:]))
        if "{{captures}}" in texte:
            blocs = []
            for nom, titre_page in captures:
                blocs.append(f'<figure class="capture"><img src="figures/{nom}"><figcaption>Dashboard · page {titre_page}</figcaption></figure>')
            texte = texte.replace("{{captures}}", '<div class="captures">\n' + "\n".join(blocs) + '\n</div>')
        partie = adapter(texte, numero, titre, images_mermaid)
        if fichier.endswith("note_executive.md"):
            partie = '<div class="note">\n\n' + partie + '\n\n</div>'
        parties.append(partie)
    return "\n\n".join(parties)


def blocs_mermaid() -> list[str]:
    codes = []
    for _, fichier, _ in CHAPITRES:
        codes += [c for c in re.findall(r"```mermaid\n(.*?)```", (RACINE / fichier).read_text(encoding="utf-8"), flags=re.S)
                  if "Entrepôt DuckDB" not in c]
    codes += re.findall(r"```mermaid\n(.*?)```", (RACINE / "docs" / "lignage_sp.md").read_text(encoding="utf-8"), flags=re.S)
    return codes


def couverture() -> str:
    return f"""<section class="couverture">
<div class="bandeau">MarketSense · Cabinet de conseil en données</div>
<h1 class="titre">Construire la chaîne de données et analyser le portefeuille d'un assureur IARD</h1>
<p class="client">Boréal Assurances · auto et habitation · janvier 2020 à juin 2025</p>
<p class="sous-titre">Dossier · M2 Data Engineering et Data Analyse</p>
<div class="auteur">
<p><strong>Teddy Sagdo</strong> (projet individuel)</p>
<p>Dépôt : <code>boreal-Sagdo</code></p>
<p>{date.today():%d/%m/%Y}</p>
</div>
</section>"""


def sommaire(entrees: list[tuple[int, str, str]], pages: dict[str, int]) -> str:
    lignes = ['<section class="sommaire"><h1 class="nontoc">Sommaire</h1><ul>']
    entrees = [e for e in entrees if e[0] == 1 or re.match(r"\d+\.\d+ |[A-Z]\. ", e[2])]
    for niveau, ident, texte in entrees:
        numero = pages.get(ident, "")
        lignes.append(f'<li class="n{niveau}"><a href="#{ident}"><span class="t">{html.escape(texte)}</span>'
                      f'<span class="p">{numero}</span></a></li>')
    lignes.append("</ul></section>")
    return "\n".join(lignes)


def titres(corps: str) -> list[tuple[int, str, str]]:
    return [(int(n), i, re.sub("<[^>]+>", "", t)) for n, i, t in
            re.findall(r'<h([12]) id="([^"]+)"[^>]*>(.*?)</h\1>', corps, flags=re.S)]


def html_complet(corps: str, pages: dict[str, int]) -> str:
    style = (DOSSIER / "style.css").read_text(encoding="utf-8")
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Boréal Assurances · Dossier</title>
<style>{style}</style></head><body>{couverture()}{sommaire(titres(corps), pages)}<main>{corps}</main></body></html>"""


# --- 4. Impression --------------------------------------------------------------------------------

PIED = """<div style="font-size:7.5pt;color:#6b7280;width:100%;padding:0 18mm;display:flex;justify-content:space-between;font-family:Helvetica,Arial">
<span>Boréal Assurances · Dossier M2 Data · Teddy Sagdo</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>"""


def imprimer(navigateur, chemin_html: Path, sortie: Path) -> None:
    page = navigateur.new_page()
    page.goto(chemin_html.as_uri(), wait_until="load")
    page.pdf(path=str(sortie), format="A4", print_background=True, display_header_footer=True,
             header_template="<span></span>", footer_template=PIED,
             margin={"top": "16mm", "bottom": "18mm", "left": "18mm", "right": "18mm"})
    page.close()


def localiser(sortie: Path, entrees: list[tuple[int, str, str]]) -> dict[str, int]:
    """Page de chaque titre, en cherchant les titres dans l'ordre après le sommaire."""
    def normaliser(t: str) -> str:
        # Ligatures (ﬁ, ﬀ) et espaces ajoutés autour du code par l'extraction : on compare sans eux
        return re.sub(r"\s+", "", unicodedata.normalize("NFKC", t))
    textes = [normaliser(p.extract_text() or "") for p in PdfReader(str(sortie)).pages]
    debut = next(i for i, t in enumerate(textes) if t.startswith("Noteexécutive"))
    pages, courante = {}, debut
    for _, ident, texte in entrees:
        cible = normaliser(texte)[:50]
        for i in range(courante, len(textes)):
            if cible in textes[i]:
                pages[ident], courante = i + 1, i
                break
    return pages


def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        navigateur = p.chromium.launch(channel="chrome")
        images = rendre_diagrammes(navigateur, {c: None for c in blocs_mermaid()})
        captures = capturer_dashboard(navigateur)
        markdown = assembler(images, captures)
        (DOSSIER / "dossier.md").write_text(markdown, encoding="utf-8")
        corps = subprocess.run(["pandoc", "-f", "gfm", "-t", "html5", "--wrap=none"], input=markdown,
                               capture_output=True, text=True, check=True).stdout
        chemin_html = DOSSIER / "dossier.html"
        chemin_html.write_text(html_complet(corps, {}), encoding="utf-8")
        imprimer(navigateur, chemin_html, SORTIE)
        pages = localiser(SORTIE, titres(corps))
        chemin_html.write_text(html_complet(corps, pages), encoding="utf-8")
        imprimer(navigateur, chemin_html, SORTIE)
        navigateur.close()
    total = len(PdfReader(str(SORTIE)).pages)
    manquants = [t for _, i, t in titres(corps) if i not in pages]
    print(f"{SORTIE.relative_to(RACINE)} : {total} pages ; titres sans page : {manquants or 'aucun'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
