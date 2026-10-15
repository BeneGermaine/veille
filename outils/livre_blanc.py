"""Met en page le livre blanc (A4) à partir de l'export Markdown du document validé.

Usage : python3 outils/livre_blanc.py
Entrée : livre-blanc/livre-blanc.md (export du doc), livre-blanc/img/*.jpg, livre-blanc/fonts/*.woff2
Sortie : livre-blanc/livre-blanc.html et assets/livre-blanc-2026.pdf (nécessite Playwright)
"""
import re, html, pathlib
import markdown

RACINE = pathlib.Path(__file__).resolve().parent.parent
LB = RACINE / "livre-blanc"
SORTIE_PDF = RACINE / "assets" / "livre-blanc-2026.pdf"
AUTEUR = "Bénédicte Lallement"
# photo de Bénédicte : livre-blanc/img/portrait.jpg si elle existe, sinon ses initiales
PHOTO = '<img src="img/portrait.jpg" alt="">' if (LB / "img" / "portrait.jpg").exists() else "<span>BL</span>"

# image et style d'ouverture de chaque chapitre (repéré par le début de son titre)
CHAPITRES = {
    "IA": ("ia.jpg", "nb", "vert"),
    "Marketing": ("marketing.jpg", "collage", ""),
    "Communication": ("communication.jpg", "collage", ""),
    "Design": ("design.jpg", "collage", ""),
}
DOMAINES = {"IA": "ia", "Marketing": "mkt", "Communication": "com", "Design": "des"}

md = markdown.Markdown(extensions=["tables", "sane_lists"])


def rendu(texte):
    md.reset()
    h = md.convert(texte)
    # « Ce que ça change : » -> encadré
    h = re.sub(r"<p><em>Ce que ça change :</em>\s*(.*?)</p>",
               r'<div class="chg"><span class="chg-t">Ce que ça change</span><p>\1</p></div>', h, flags=re.S)
    # cases à cocher
    h = h.replace("<li>[ ] ", '<li class="case">')
    # « Le saviez-vous ? » -> encart
    h = re.sub(r"<blockquote>\s*<p><strong>(Le saviez-vous \?[^<]*)</strong></p>",
               r'<aside class="encart"><p class="encart-t">\1</p>', h)
    h = h.replace("</blockquote>", "</aside>")
    # liens : ouverture dans un nouvel onglet
    h = h.replace("<a href=", '<a target="_blank" rel="noopener" href=')
    return h


def sections(texte):
    """Découpe le Markdown en (titre de niveau 2, contenu)."""
    parts = re.split(r"^## (.+)$", texte, flags=re.M)
    intro = parts[0]
    return intro, [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts), 2)]


MOIS = [("janv", "Janvier"), ("févr", "Février"), ("mars", "Mars"), ("avr", "Avril"), ("mai", "Mai"),
        ("juin", "Juin"), ("juill", "Juillet"), ("août", "Août"), ("sept", "Septembre")]


def mois_de(date):
    d = date.lower()
    for k, (cle, nom) in enumerate(MOIS):
        if cle in d:
            return k
    return None


def lignes_tableau(contenu):
    return [[c.strip() for c in l.strip().strip("|").split("|")] for l in contenu.splitlines() if l.startswith("|")][2:]


def inline(texte):
    h = rendu(texte)
    return re.sub(r"^<p>|</p>$", "", h.strip())


def chronologie(contenu):
    """Infographie : neuf cases de mois, un point de couleur par domaine."""
    avant = contenu.split("|")[0].strip()
    par_mois = {k: [] for k in range(9)}
    for date, dom, fait in lignes_tableau(contenu):
        k = mois_de(date)
        if k is None:
            continue
        jour = re.sub(r"\s*(janv|févr|mars|avr|mai|juin|juill|août|sept)\.?$", "", date, flags=re.I).strip()
        if jour.lower() == MOIS[k][1].lower():
            jour = ""
        par_mois[k].append((jour, dom, fait))
    legende = "".join(f'<span class="lg"><i class="d {c}"></i>{n}</span>' for n, c in DOMAINES.items())
    cases = []
    for k in range(9):
        evts = ""
        for j, dom, f in par_mois[k]:
            jj = f"<b>{html.escape(j)}</b> " if j else ""
            evts += f'<li><i class="d {DOMAINES.get(dom, "")}"></i><span>{jj}{html.escape(f)}</span></li>'
        cases.append(f'<div class="mois"><div class="m-tete"><span class="m-num">{k + 1:02d}</span><span class="m-nom">{MOIS[k][1]}</span></div><ul>{evts}</ul></div>')
    return (f'<p class="lede">{html.escape(avant)}</p><div class="legende">{legende}</div>'
            f'<div class="calendrier">{"".join(cases)}</div>'
            '<p class="note">Les sources de chaque fait sont dans les chapitres et dans la liste finale.</p>')


def items_gras(contenu):
    """Liste numérotée « 1. **Titre.** texte » -> [(titre, texte)]."""
    return [(m.group(1).rstrip("."), m.group(2)) for m in re.finditer(r"^\d+\.\s+\*\*(.+?)\*\*\s*(.*)$", contenu, flags=re.M)]


def essentiel(contenu):
    chapo = contenu.split("\n\n")[0]
    cartes = "".join(f'<div class="carte c{i % 3}"><span class="c-num">{i + 1}</span><h3>{html.escape(t)}</h3><p>{inline(x)}</p></div>'
                     for i, (t, x) in enumerate(items_gras(contenu)))
    return f'<p class="lede">{html.escape(chapo)}</p><div class="cartes">{cartes}</div>'


def chiffres(contenu):
    avant = contenu.split("|")[0].strip()
    cases = "".join(f'<div class="kc {"r" if i % 2 == 0 else "v"}"><strong>{html.escape(c)}</strong><p>{html.escape(q)}</p><small>{html.escape(s)}</small></div>'
                    for i, (c, q, s) in enumerate(lignes_tableau(contenu)))
    return f'<p class="lede">{html.escape(avant)}</p><div class="kgrille">{cases}</div>'


def tendances(contenu):
    chapo = contenu.split("\n\n")[0]
    partie_t, _, partie_a = contenu.partition("### ")
    blocs = "".join(f'<div class="tend t{i}"><span class="t-num">{i + 1:02d}</span><h3>{html.escape(t)}</h3><p>{inline(x)}</p></div>'
                    for i, (t, x) in enumerate(items_gras(partie_t)))
    titre_a = partie_a.splitlines()[0].strip() if partie_a else ""
    actions = re.findall(r"^- \[ \] (.+)$", partie_a, flags=re.M)
    plan = ""
    if actions:
        lis = "".join(f"<li>{inline(a)}</li>" for a in actions)
        plan = f'<div class="plan"><p class="plan-k">Passer à l\'action</p><h3>{html.escape(titre_a)}</h3><ul>{lis}</ul></div>'
    return f'<p class="lede">{html.escape(chapo)}</p><div class="tendances">{blocs}</div>{plan}'


def regard(contenu):
    return (f'<div class="auteur"><div class="photo-a">{PHOTO}</div><div><p class="a-nom">{AUTEUR}</p>'
            '<p class="a-titre">Responsable / Directrice Marketing &amp; Communication B2B</p>'
            "<p class=\"a-tags\">Stratégie de marque · Contenu · Marketing automation · Marketing augmenté par l'IA · +16 ans</p>"
            "<p class=\"a-pourquoi\">J'ai mis en place cette veille pour suivre chaque semaine ce qui change dans nos métiers, "
            "et pour montrer concrètement comment je travaille avec l'IA : elle cherche et pré-analyse, je vérifie, je choisis et je décide.</p></div></div>"
            f'<div class="regard-txt">{rendu(contenu)}<p class="sig">{AUTEUR}</p></div>')


def sources(contenu, methode):
    intro = contenu.split("\n\n")[0]
    blocs, titre, items = [], None, []
    for l in contenu.splitlines()[1:]:
        m_t = re.match(r"^\*\*(.+)\*\*$", l.strip())
        m_i = re.match(r"^- \[(.+?)\]\((.+?)\),\s*(.*)$", l.strip())
        if m_t:
            if titre:
                blocs.append((titre, items))
            titre, items = m_t.group(1), []
        elif m_i:
            reste = m_i.group(3)
            coupe = re.search(r"\s(et|;)\s\[", reste)
            lien_txt, suite = (reste[:coupe.start()], reste[coupe.start():]) if coupe else (reste, "")
            item = f'<a href="{html.escape(m_i.group(2))}">{html.escape(lien_txt.strip().rstrip(","))}</a>'
            if suite:
                item += " " + inline(suite.strip())
            items.append(item)
    if titre:
        blocs.append((titre, items))
    groupes = "".join(f'<div class="s-g"><p class="s-t">{html.escape(t)}</p><ul>{"".join(f"<li>{i}</li>" for i in its)}</ul></div>' for t, its in blocs)
    return (f'<div class="methode"><h2>Comment cette veille est faite</h2>{rendu(methode)}</div>'
            f'<h2 class="s-h2">Sources</h2><p class="s-intro">{html.escape(intro)} Chaque source est cliquable.</p><div class="s-col">{groupes}</div>')


def ouverture(num, titre, contenu):
    cle = titre.split(" ")[0].rstrip(":")
    img, style, acc = CHAPITRES.get(cle, (None, "", ""))
    paras = contenu.split("\n\n", 1)
    chapo, reste = paras[0], (paras[1] if len(paras) > 1 else "")
    nom, _, sous = titre.partition(" : ")
    fig = f'<figure class="ouv-img {style} {acc}"><img src="img/{img}" alt=""></figure>' if img else ""
    return f'''<section class="chapitre">
  <header class="ouv"><div class="ouv-ligne"><div class="ouv-num">{num:02d}</div><div><p class="ouv-k">{html.escape(nom)}</p><h2>{html.escape((sous[:1].upper() + sous[1:]) if sous else nom)}</h2></div></div>
  <p class="ouv-chapo">{html.escape(chapo)}</p>{fig}</header>
  <div class="corps">{rendu(reste)}</div></section>'''


def construire():
    texte = (LB / "livre-blanc.md").read_text()
    titre = texte.splitlines()[0].lstrip("# ").strip()
    intro, secs = sections(texte)
    accroche = [p for p in intro.split("\n\n") if p.strip() and not p.startswith("#") and "@" not in p][0].strip()
    corps, num = [], 0
    methode = next((c for t, c in secs if t.startswith("Comment")), "")
    for t, c in secs:
        if t.startswith("L'essentiel"):
            corps.append(f'<section class="pleine essentiel"><p class="k">En bref</p><h2>{html.escape(t)}</h2>{essentiel(c)}</section>')
        elif t.startswith("Neuf mois"):
            corps.append(f'<section class="pleine chrono"><p class="k">Chronologie</p><h2>{html.escape(t)}</h2>{chronologie(c)}</section>')
        elif t.split(" ")[0].rstrip(":") in CHAPITRES:
            num += 1
            corps.append(ouverture(num, t, c))
        elif t.startswith("Les chiffres"):
            corps.append(f'<section class="chiffres-s"><p class="k">En chiffres</p><h2>{html.escape(t)}</h2>{chiffres(c)}</section>')
        elif t.startswith("Cinq tendances"):
            corps.append(f'<section class="pleine"><p class="k">Et maintenant ?</p><h2>{html.escape(t)}</h2>{tendances(c)}</section>')
        elif t.startswith("Mon regard"):
            corps.append(f'<section class="pleine regard"><p class="k">Pour conclure</p><h2>{html.escape(t)}</h2>{regard(c)}</section>')
        elif t.startswith("Sources"):
            corps.append(f'<section class="pleine sources">{sources(c, methode)}</section>')
    nom_titre, _, sous_titre = titre.partition(" — ")
    page = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{html.escape(titre)}</title>
<style>{CSS}</style></head><body>
<section class="couverture">
  <figure><img src="img/couverture.jpg" alt=""></figure>
  <div class="couv-txt"><p class="couv-k">Livre blanc · Janvier à septembre 2026</p>
  <h1>{html.escape(nom_titre)}</h1><p class="couv-sous">{html.escape(sous_titre)}</p>
  <p class="couv-acc">{html.escape(accroche)}</p>
  <p class="couv-aut"><strong>{AUTEUR}</strong> · Marketing et communication B2B · Octobre 2026</p></div>
</section>
{"".join(corps)}
</body></html>'''
    (LB / "livre-blanc.html").write_text(page)
    return LB / "livre-blanc.html"


CSS = """
@font-face{font-family:Arimo;font-weight:400;src:url(fonts/arimo-latin-400-normal.woff2) format("woff2")}
@font-face{font-family:Arimo;font-weight:700;src:url(fonts/arimo-latin-700-normal.woff2) format("woff2")}
@font-face{font-family:Arimo;font-weight:400;src:url(fonts/arimo-latin-ext-400-normal.woff2) format("woff2");unicode-range:U+0100-024F,U+20AC,U+2026,U+2013}
@font-face{font-family:Arimo;font-weight:700;src:url(fonts/arimo-latin-ext-700-normal.woff2) format("woff2");unicode-range:U+0100-024F,U+20AC,U+2026,U+2013}
@page{size:A4;margin:16mm 16mm 18mm}
@page:first{margin:0}
:root{--rouge:#e64855;--vert:#cbe170;--vertf:#5d6b1e;--noir:#111;--gris:#6b6564;--doux:#f6f5f2;--ligne:#e6e2dd;--rose:#fdecee;--vpale:#f4f8e2}
*{box-sizing:border-box}
body{margin:0;font-family:Arimo,"Liberation Sans",Arial,sans-serif;color:var(--noir);font-size:10pt;line-height:1.5;-webkit-print-color-adjust:exact;print-color-adjust:exact}
a{color:inherit;text-decoration:underline;text-decoration-color:var(--rouge);text-underline-offset:2px}
h2{font-size:24pt;line-height:1.08;letter-spacing:-.02em;margin:0 0 8pt}
h3{font-size:11pt;line-height:1.25;margin:0 0 4pt}
p{margin:0 0 7pt}
ul,ol{margin:0 0 9pt;padding-left:15pt}
li{margin-bottom:3pt}
.k,.ouv-k{font-size:8pt;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--rouge);margin:0 0 5pt}
.lede{font-size:11pt;line-height:1.5;color:#333;margin-bottom:12pt;max-width:165mm}
.pleine{break-before:page}

/* couverture */
.couverture{height:297mm;display:flex;flex-direction:column;break-after:page}
.couverture figure{margin:0;height:150mm;overflow:hidden}
.couverture img{width:100%;height:100%;object-fit:cover;display:block}
.couv-txt{flex:1;padding:16mm 17mm 14mm;display:flex;flex-direction:column}
.couv-k{font-size:8.5pt;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--rouge);margin:0 0 8pt}
.couverture h1{font-size:40pt;line-height:1;letter-spacing:-.035em;margin:0}
.couv-sous{font-size:15pt;font-weight:700;margin:8pt 0 0}
.couv-sous::after{content:"";display:block;width:34pt;height:6pt;border-radius:3pt;background:var(--vert);margin-top:12pt}
.couv-acc{font-size:11pt;line-height:1.5;color:#333;max-width:150mm;margin-top:12pt}
.couv-aut{margin-top:auto;font-size:9pt;color:var(--gris);border-top:1px solid var(--ligne);padding-top:8pt}

/* l'essentiel : 7 cartes en relief doux */
.cartes{display:grid;grid-template-columns:repeat(2,1fr);gap:11pt}
.carte{position:relative;background:#fff;border-radius:12pt;padding:13pt 14pt 11pt 50pt;box-shadow:0 6pt 16pt -8pt rgba(17,17,17,.22),0 0 0 1px var(--ligne);break-inside:avoid}
.carte:last-child{grid-column:1/-1}
.c-num{position:absolute;left:13pt;top:12pt;width:26pt;height:26pt;border-radius:50%;display:grid;place-items:center;font-weight:700;font-size:12pt;background:var(--rouge);color:#fff}
.carte.c1 .c-num{background:var(--vert);color:var(--noir)}
.carte.c2 .c-num{background:var(--noir);color:#fff}
.carte h3{font-size:11pt}
.carte p{font-size:9pt;line-height:1.45;margin:0;color:#333}

/* chronologie : calendrier de 9 mois */
.legende{display:flex;gap:14pt;margin:-4pt 0 10pt;font-size:8.5pt;font-weight:700}
.lg{display:flex;align-items:center;gap:5pt}
.d{display:inline-block;width:8pt;height:8pt;border-radius:50%;flex:none;margin-top:2.5pt}
.d.ia{background:var(--rouge)}.d.mkt{background:#b5cc52}.d.com{background:var(--noir)}.d.des{background:#fff;box-shadow:inset 0 0 0 2px var(--rouge)}
.calendrier{display:grid;grid-template-columns:repeat(3,1fr);gap:9pt}
.mois{background:var(--doux);border-radius:10pt;padding:9pt 10pt 6pt;break-inside:avoid}
.m-tete{display:flex;align-items:baseline;gap:6pt;border-bottom:2px solid var(--noir);padding-bottom:4pt;margin-bottom:6pt}
.m-num{font-size:18pt;font-weight:700;color:var(--rouge);letter-spacing:-.03em;line-height:1}
.m-nom{font-size:10pt;font-weight:700;text-transform:uppercase;letter-spacing:.08em}
.mois ul{list-style:none;padding:0;margin:0}
.mois li{display:flex;gap:6pt;font-size:8.2pt;line-height:1.35;margin-bottom:5pt}
.note{font-size:8.5pt;color:var(--gris);margin-top:8pt}

/* chapitres : à la suite, sans page blanche */
.chapitre{margin-top:20pt}
.ouv{break-inside:avoid;break-after:avoid}
.ouv-ligne{display:flex;align-items:flex-end;gap:12pt;margin-bottom:6pt}
.ouv-num{font-size:52pt;font-weight:700;line-height:.8;letter-spacing:-.05em;color:var(--rouge)}
.ouv h2{font-size:20pt;margin:0}
.ouv-chapo{font-size:10.8pt;line-height:1.5;color:#333;padding-bottom:10pt;border-bottom:3px solid var(--noir);margin-bottom:10pt}
.ouv-img{margin:0 0 12pt;height:56mm;border-radius:8pt;overflow:hidden;position:relative;break-before:avoid}
.ouv-img img{width:100%;height:100%;object-fit:cover;display:block}
.ouv-img.nb{border-radius:0;overflow:visible;padding:0 7pt 7pt 0}
.ouv-img.nb img{filter:grayscale(1) contrast(1.08);border-radius:8pt;position:relative}
.ouv-img.nb::before{content:"";position:absolute;inset:7pt 0 0 7pt;border-radius:8pt;background:var(--vert)}
.corps > p{break-inside:avoid-page}
.corps > p:has(> strong:only-child){break-after:avoid}
.chiffres-s{break-inside:avoid;margin-top:22pt}
.chg{background:var(--doux);border-left:3px solid var(--rouge);padding:6pt 10pt;margin:0 0 11pt;break-inside:avoid;border-radius:0 6pt 6pt 0}
.chg-t{display:block;font-size:7.5pt;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--rouge);margin-bottom:1pt}
.chg p{margin:0}
.chapitre:nth-of-type(even) .chg{border-left-color:#b5cc52}
.chapitre:nth-of-type(even) .chg-t{color:var(--vertf)}
.encart{background:var(--vpale);border-radius:10pt;padding:11pt 13pt 5pt;margin:10pt 0 12pt;break-inside:avoid}
.encart-t{font-weight:700;font-size:11pt;margin-bottom:5pt}
.encart-t::before{content:"";display:inline-block;width:7pt;height:7pt;border-radius:50%;background:var(--rouge);margin-right:7pt;vertical-align:1pt}

/* chiffres */
.kgrille{display:grid;grid-template-columns:repeat(3,1fr);gap:13pt 14pt}
.kc{border-top:3px solid var(--rouge);padding-top:7pt;break-inside:avoid}
.kc.v{border-top-color:var(--vert)}
.kc strong{display:block;font-size:24pt;line-height:1;letter-spacing:-.03em;margin-bottom:5pt}
.kc p{font-size:8.8pt;line-height:1.4;margin:0 0 3pt}
.kc small{font-size:7.5pt;color:var(--gris)}

/* tendances : 5 blocs */
.tendances{display:grid;grid-template-columns:repeat(2,1fr);gap:10pt;margin-bottom:14pt}
.tend{border-radius:12pt;padding:12pt 14pt;break-inside:avoid;position:relative}
.tend.t0{background:var(--rouge);color:#fff}
.tend.t1{background:var(--vert)}
.tend.t2{background:var(--noir);color:#fff}
.tend.t3{background:var(--rose)}
.tend.t4{background:var(--vpale);grid-column:1/-1}
.t-num{display:block;font-size:22pt;font-weight:700;line-height:1;letter-spacing:-.03em;margin-bottom:5pt;opacity:.9}
.tend.t1 .t-num,.tend.t3 .t-num,.tend.t4 .t-num{color:var(--rouge)}
.tend.t2 .t-num{color:var(--vert)}
.tend h3{font-size:12pt}
.tend p{font-size:9pt;line-height:1.45;margin:0}
.tend a{color:inherit}

/* plan d'action */
.plan{border-radius:12pt;padding:13pt 16pt 8pt;box-shadow:0 6pt 16pt -8pt rgba(17,17,17,.22),0 0 0 1px var(--ligne);break-inside:avoid}
.plan-k{font-size:8pt;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--rouge);margin:0 0 3pt}
.plan h3{font-size:13pt;margin-bottom:8pt}
.plan ul{list-style:none;padding:0;columns:2;column-gap:16pt}
.plan li{position:relative;padding-left:16pt;font-size:8.8pt;line-height:1.4;margin-bottom:6pt;break-inside:avoid}
.plan li::before{content:"";position:absolute;left:0;top:1.5pt;width:9pt;height:9pt;border-radius:2.5pt;background:var(--vert);box-shadow:inset 0 0 0 1.5px var(--vertf)}

/* mon regard */
.auteur{display:flex;gap:14pt;align-items:center;background:var(--doux);border-radius:12pt;padding:12pt 14pt;margin-bottom:14pt;break-inside:avoid}
.photo-a{flex:none;width:68pt;height:68pt;border-radius:50%;overflow:hidden;background:var(--rouge);display:grid;place-items:center;box-shadow:0 0 0 4pt var(--vert)}
.photo-a img{width:100%;height:100%;object-fit:cover}
.photo-a span{color:#fff;font-weight:700;font-size:22pt}
.a-nom{font-weight:700;font-size:13pt;margin:0}
.a-titre{font-weight:700;font-size:9.5pt;margin:0 0 2pt}
.a-tags{font-size:8.3pt;color:var(--gris);margin:0 0 5pt}
.a-pourquoi{font-size:9pt;margin:0}
.regard-txt{border-left:3px solid var(--rouge);padding-left:14pt}
.regard-txt p{font-size:10.8pt;line-height:1.6}
.sig{font-weight:700;font-size:10pt!important;color:var(--gris)}

/* méthode + sources sur une page */
.methode{background:var(--doux);border-radius:10pt;padding:10pt 13pt 4pt;margin-bottom:10pt}
.methode h2{font-size:12pt}
.methode p{font-size:8.6pt;line-height:1.45;margin-bottom:5pt}
.s-h2{font-size:15pt;margin-bottom:3pt}
.s-intro{font-size:7.6pt;color:var(--gris);margin-bottom:6pt}
.s-col{columns:3;column-gap:12pt}
.s-g{break-inside:avoid-column;margin-bottom:6pt}
.s-t{font-size:8pt;font-weight:700;color:var(--rouge);margin:0 0 2pt}
.s-g ul{list-style:none;padding:0;margin:0}
.s-g li{font-size:6.9pt;line-height:1.3;margin:0 0 1.6pt;break-inside:avoid}
.s-g a{text-decoration-thickness:.5px}
"""


def pdf(source):
    """La couverture est imprimée sans pied de page, le reste avec titre et numéro de page."""
    from playwright.sync_api import sync_playwright
    from pypdf import PdfReader, PdfWriter
    pied = f'<div style="width:100%;font-family:Arial,sans-serif;font-size:7pt;color:#8a8584;padding:0 17mm;display:flex;justify-content:space-between"><span>Ce qui a changé en 2026 · {AUTEUR}</span><span class="pageNumber"></span></div>'
    tmp_couv, tmp_corps = LB / "_couv.pdf", LB / "_corps.pdf"
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(source.as_uri())
        pg.wait_for_timeout(800)
        pg.pdf(path=str(tmp_couv), format="A4", print_background=True, prefer_css_page_size=True, page_ranges="1")
        pg.pdf(path=str(tmp_corps), format="A4", print_background=True, prefer_css_page_size=True,
               display_header_footer=True, header_template="<span></span>", footer_template=pied)
        b.close()
    w = PdfWriter()
    w.add_page(PdfReader(str(tmp_couv)).pages[0])
    for pge in PdfReader(str(tmp_corps)).pages[1:]:
        w.add_page(pge)
    w.add_metadata({"/Title": "Ce qui a changé en 2026 — IA, marketing, communication, design", "/Author": AUTEUR})
    with open(SORTIE_PDF, "wb") as f:
        w.write(f)
    tmp_couv.unlink(); tmp_corps.unlink()


if __name__ == "__main__":
    pdf(construire())
    print("PDF :", SORTIE_PDF)
