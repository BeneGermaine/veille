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

# image et style d'ouverture de chaque chapitre (repéré par le début de son titre)
CHAPITRES = {
    "IA": ("ia.jpg", "nb", "vert"),
    "Marketing": ("marketing.jpg", "collage", ""),
    "Communication": ("communication.jpg", "nb", "rouge"),
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


def chronologie(contenu):
    lignes = [l for l in contenu.splitlines() if l.startswith("|")][2:]
    avant = contenu.split("|")[0].strip()
    apres = contenu.rsplit("|", 1)[-1].strip()
    items = []
    for l in lignes:
        date, dom, fait = [c.strip() for c in l.strip("|").split("|")]
        items.append(f'<li><span class="t-date">{html.escape(date)}</span><span class="pill {DOMAINES.get(dom, "")}">{html.escape(dom)}</span><span class="t-fait">{html.escape(fait)}</span></li>')
    return f'{rendu(avant)}<ol class="frise">{"".join(items)}</ol>{rendu(apres)}'


def chiffres(contenu):
    lignes = [l for l in contenu.splitlines() if l.startswith("|")][2:]
    avant = contenu.split("|")[0].strip()
    cases = []
    for i, l in enumerate(lignes):
        c, quoi, src = [x.strip() for x in l.strip("|").split("|")]
        cases.append(f'<div class="kc {"r" if i % 2 == 0 else "v"}"><strong>{html.escape(c)}</strong><p>{html.escape(quoi)}</p><small>{html.escape(src)}</small></div>')
    return f'{rendu(avant)}<div class="kgrille">{"".join(cases)}</div>'


def ouverture(num, titre, contenu):
    cle = titre.split(" ")[0].rstrip(":")
    img, style, acc = CHAPITRES.get(cle, (None, "", ""))
    paras = contenu.split("\n\n", 1)
    chapo, reste = paras[0], (paras[1] if len(paras) > 1 else "")
    nom, _, sous = titre.partition(" : ")
    fig = f'<figure class="ouv-img {style} {acc}"><img src="img/{img}" alt=""></figure>' if img else ""
    return f'''<section class="chapitre">
  <header class="ouv"><div class="ouv-num">{num:02d}</div><p class="ouv-k">{html.escape(nom)}</p><h2>{html.escape((sous[:1].upper() + sous[1:]) if sous else nom)}</h2>
  <p class="ouv-chapo">{html.escape(chapo)}</p></header>{fig}
  <div class="corps">{rendu(reste)}</div></section>'''


def construire():
    texte = (LB / "livre-blanc.md").read_text()
    titre = texte.splitlines()[0].lstrip("# ").strip()
    intro, secs = sections(texte)
    accroche = [p for p in intro.split("\n\n") if p.strip() and not p.startswith("#") and "@" not in p][0].strip()
    corps, num = [], 0
    for t, c in secs:
        if t.startswith("Neuf mois"):
            corps.append(f'<section class="page-section"><p class="k">Chronologie</p><h2>{html.escape(t)}</h2>{chronologie(c)}</section>')
        elif t.startswith("Les chiffres"):
            corps.append(f'<section class="page-section"><p class="k">En chiffres</p><h2>{html.escape(t)}</h2>{chiffres(c)}</section>')
        elif t.split(" ")[0].rstrip(":") in CHAPITRES:
            num += 1
            corps.append(ouverture(num, t, c))
        elif t.startswith("Mon regard"):
            corps.append(f'<section class="page-section regard"><p class="k">Pour conclure</p><h2>{html.escape(t)}</h2><div class="regard-txt">{rendu(c)}<p class="sig">{AUTEUR}</p></div></section>')
        elif t.startswith("Sources"):
            corps.append(f'<section class="page-section sources"><h2>{html.escape(t)}</h2>{rendu(c)}</section>')
        elif t.startswith("L'essentiel"):
            corps.append(f'<section class="page-section essentiel"><p class="k">En bref</p><h2>{html.escape(t)}</h2>{rendu(c)}</section>')
        elif t.startswith("Comment"):
            corps.append(f'<section class="suite methode"><h2>{html.escape(t)}</h2>{rendu(c)}</section>')
        else:
            corps.append(f'<section class="page-section"><h2>{html.escape(t)}</h2>{rendu(c)}</section>')
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
@page{size:A4;margin:18mm 17mm 20mm}
@page:first{margin:0}
:root{--rouge:#e64855;--vert:#cbe170;--noir:#111;--gris:#6b6564;--doux:#f6f5f2;--ligne:#e6e2dd}
*{box-sizing:border-box}
body{margin:0;font-family:Arimo,"Liberation Sans",Arial,sans-serif;color:var(--noir);font-size:10.2pt;line-height:1.55;-webkit-print-color-adjust:exact;print-color-adjust:exact}
a{color:inherit;text-decoration:underline;text-decoration-color:var(--rouge);text-underline-offset:2px}
h2{font-size:24pt;line-height:1.08;letter-spacing:-.02em;margin:0 0 12pt}
h3{font-size:12pt;margin:16pt 0 6pt}
p{margin:0 0 8pt}
strong{font-weight:700}
ul,ol{margin:0 0 10pt;padding-left:16pt}
li{margin-bottom:4pt}
.k,.ouv-k{font-size:8pt;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--rouge);margin:0 0 6pt}

/* couverture */
.couverture{height:297mm;display:flex;flex-direction:column;page-break-after:always;break-after:page}
.couverture figure{margin:0;height:150mm;overflow:hidden}
.couverture img{width:100%;height:100%;object-fit:cover;display:block}
.couv-txt{flex:1;padding:16mm 17mm 14mm;display:flex;flex-direction:column}
.couv-k{font-size:8.5pt;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--rouge);margin:0 0 8pt}
.couverture h1{font-size:40pt;line-height:1;letter-spacing:-.035em;margin:0}
.couv-sous{font-size:15pt;font-weight:700;margin:8pt 0 0;color:var(--noir)}
.couv-sous::after{content:"";display:block;width:34pt;height:6pt;border-radius:3pt;background:var(--vert);margin-top:12pt}
.couv-acc{font-size:11pt;line-height:1.5;color:#333;max-width:150mm;margin-top:12pt}
.couv-aut{margin-top:auto;font-size:9pt;color:var(--gris);border-top:1px solid var(--ligne);padding-top:8pt}

/* sections pleine page */
.page-section{break-before:page}
.suite{margin-top:22pt;padding-top:14pt;border-top:1px solid var(--ligne)}
.suite h2{font-size:16pt}
.essentiel ol{list-style:none;padding:0;counter-reset:e}
.essentiel ol li{counter-increment:e;position:relative;padding:8pt 0 8pt 30pt;border-bottom:1px solid var(--ligne);margin:0}
.essentiel ol li::before{content:counter(e);position:absolute;left:0;top:6pt;font-size:16pt;font-weight:700;color:var(--rouge)}
.essentiel > p:first-of-type{font-size:12pt;line-height:1.5}

/* frise chronologique */
.frise{list-style:none;padding:0;margin:8pt 0 10pt;border-left:2px solid var(--noir)}
.frise li{display:grid;grid-template-columns:62pt 70pt 1fr;gap:8pt;align-items:baseline;padding:4pt 0 4pt 12pt;margin:0;position:relative;break-inside:avoid;font-size:9pt;line-height:1.4}
.frise li::before{content:"";position:absolute;left:-5pt;top:8pt;width:8pt;height:8pt;border-radius:50%;background:#fff;border:2px solid var(--noir)}
.t-date{font-weight:700}
.pill{font-size:7.5pt;font-weight:700;padding:1pt 6pt;border-radius:9pt;justify-self:start;background:#efeeec}
.pill.ia{background:#fdecee;color:#b8303c}.pill.mkt{background:#f4f8e2;color:#5d6b1e}.pill.com{background:#f1eeee;color:#5c5655}.pill.des{background:#fde9dc;color:#a2481f}

/* ouvertures de chapitre */
.chapitre{break-before:page}
.ouv{position:relative;padding-top:4pt;margin-bottom:12pt}
.ouv-num{font-size:64pt;font-weight:700;line-height:.8;letter-spacing:-.05em;color:var(--rouge);margin-bottom:8pt}
.ouv h2{font-size:22pt;max-width:150mm}
.ouv-chapo{font-size:11.5pt;line-height:1.5;color:#333;max-width:160mm;padding-bottom:12pt;border-bottom:3px solid var(--noir)}
.ouv-img{margin:0 0 14pt;height:62mm;border-radius:6pt;overflow:hidden;position:relative}
.ouv-img img{width:100%;height:100%;object-fit:cover;display:block}
.ouv-img.nb img{filter:grayscale(1) contrast(1.08)}
.ouv-img.nb{border-radius:0;overflow:visible;padding:0 8pt 8pt 0}
.ouv-img.nb::before{content:"";position:absolute;inset:8pt 0 0 8pt;border-radius:6pt;background:var(--vert);z-index:-1}
.ouv-img.nb.rouge::before{background:var(--rouge)}
.ouv-img.nb img{border-radius:6pt;position:relative}
.corps > p > strong:first-child{color:var(--noir)}
.corps > p{break-inside:avoid-page}

/* encadrés */
.chg{background:var(--doux);border-left:3px solid var(--rouge);padding:7pt 10pt;margin:0 0 12pt;break-inside:avoid;border-radius:0 6pt 6pt 0}
.chg-t{display:block;font-size:7.5pt;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--rouge);margin-bottom:2pt}
.chg p{margin:0}
.chapitre:nth-of-type(even) .chg{border-left-color:#b5cc52}
.chapitre:nth-of-type(even) .chg-t{color:#5d6b1e}
.encart{background:#f4f8e2;border-radius:8pt;padding:12pt 14pt 6pt;margin:12pt 0 14pt;break-inside:avoid}
.encart-t{font-weight:700;font-size:11pt;margin-bottom:6pt}
.encart-t::before{content:"";display:inline-block;width:7pt;height:7pt;border-radius:50%;background:var(--rouge);margin-right:7pt;vertical-align:1pt}
.encart ul,.encart ol{margin-bottom:6pt}

/* chiffres */
.kgrille{display:grid;grid-template-columns:repeat(3,1fr);gap:12pt 14pt;margin-top:10pt}
.kc{border-top:3px solid var(--rouge);padding-top:7pt;break-inside:avoid}
.kc.v{border-top-color:var(--vert)}
.kc strong{display:block;font-size:22pt;line-height:1;letter-spacing:-.03em;margin-bottom:5pt}
.kc p{font-size:8.8pt;line-height:1.4;margin:0 0 4pt}
.kc small{font-size:7.5pt;color:var(--gris)}

/* tendances et liste d'actions */
h2 + p{font-size:11pt}
li.case{list-style:none;position:relative;padding-left:4pt}
li.case::before{content:"";position:absolute;left:-14pt;top:2pt;width:9pt;height:9pt;border:1.5px solid var(--noir);border-radius:2pt}
ul:has(> li.case){padding-left:16pt}

/* mon regard */
.regard-txt{border-left:3px solid var(--rouge);padding-left:14pt}
.regard-txt p{font-size:11.5pt;line-height:1.6}
.sig{font-weight:700;font-size:10pt!important;color:var(--gris)}
.methode p{font-size:9.5pt}

/* sources */
.sources{font-size:7.6pt;line-height:1.35}
.sources h2{font-size:18pt}
.sources > p:first-of-type{font-size:8.5pt;color:var(--gris)}
.sources p strong{display:block;font-size:9pt;margin-top:8pt;color:var(--rouge);break-after:avoid}
.sources ul{columns:2;column-gap:14pt;padding-left:10pt}
.sources li{break-inside:avoid;margin-bottom:2.5pt}
.sources a{text-decoration-thickness:.5px}
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
