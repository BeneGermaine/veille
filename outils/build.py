"""Génère le site de la veille à partir des fichiers de contenu.

Usage : python3 outils/build.py            (génère les pages HTML)
        python3 outils/build.py --og       (génère aussi les images de partage LinkedIn, nécessite Playwright)

Entrée : contenu/numeros/NNN.json (un fichier par numéro)
Sortie : index.html (dernier numéro), numeros/NNN.html, archives.html, livre-blanc.html, assets/og/NNN.png
"""
import json, html, pathlib, sys, datetime

RACINE = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://benegermaine.github.io/veille/"
AUTEUR = "Bénédicte Lallement"
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Arimo:wght@400;700&display=swap">'
TONS = ["t-noir", "t-vert", "t-creme", "t-rouge"]
LIRE_ETUDE = "Lire l'étude"
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

e = lambda s: html.escape(str(s), quote=True)


# ---------- illustrations (formes simples dans les couleurs de la charte) ----------
def illustration(nom, ton):
    ink = "#f5f5f2" if ton == "t-noir" else "#111111"
    fond = "#111111" if ton != "t-noir" else "#f5f5f2"
    R, V, C = "#e64855", "#cbe170", "#f5f5f2"
    accent = R if ton != "t-rouge" else V
    s = {
        "pub": f'''<rect x="40" y="30" width="320" height="240" rx="14" fill="{C}" stroke="{ink}" stroke-width="6"/>
            <rect x="40" y="30" width="320" height="36" rx="14" fill="{ink}"/><circle cx="66" cy="48" r="6" fill="{accent}"/><circle cx="86" cy="48" r="6" fill="{V}"/>
            <rect x="70" y="88" width="190" height="34" rx="17" fill="#d9d5cf"/><rect x="140" y="134" width="190" height="34" rx="17" fill="{ink}" opacity=".85"/>
            <rect x="70" y="186" width="260" height="62" fill="{V}" stroke="#111" stroke-width="5"/>
            <text x="86" y="224" font-family="Arimo,Arial" font-weight="700" font-size="22" fill="#111">ANNONCE</text>''',
        "mesure": f'''<line x1="50" y1="260" x2="360" y2="260" stroke="{ink}" stroke-width="6"/>
            <rect x="70" y="200" width="44" height="60" fill="{ink}"/><rect x="134" y="168" width="44" height="92" fill="{ink}"/>
            <rect x="198" y="120" width="44" height="140" fill="{ink}"/><rect x="262" y="70" width="44" height="190" fill="{accent}" stroke="#111" stroke-width="5"/>
            <circle cx="300" cy="96" r="44" fill="none" stroke="{V}" stroke-width="10"/><line x1="332" y1="128" x2="362" y2="158" stroke="{V}" stroke-width="12" stroke-linecap="round"/>''',
        "trace": f'''<rect x="90" y="24" width="220" height="256" fill="{C}" stroke="{ink}" stroke-width="6"/>
            <g stroke="#d9d5cf" stroke-width="10" stroke-linecap="round"><line x1="120" y1="64" x2="280" y2="64"/><line x1="120" y1="94" x2="260" y2="94"/><line x1="120" y1="124" x2="280" y2="124"/><line x1="120" y1="154" x2="230" y2="154"/></g>
            <g fill="none" stroke="{accent}" stroke-width="6"><path d="M150 250 q50-60 100 0"/><path d="M135 250 q65-85 130 0"/><path d="M120 250 q80-110 160 0"/><path d="M165 250 q35-36 70 0"/></g>''',
        "outil": f'''<rect x="30" y="60" width="170" height="130" fill="{C}" stroke="{ink}" stroke-width="6"/>
            <g stroke="#d9d5cf" stroke-width="8"><line x1="50" y1="92" x2="170" y2="92"/><line x1="50" y1="116" x2="150" y2="116"/></g>
            <rect x="120" y="110" width="170" height="130" fill="{V}" stroke="#111" stroke-width="6"/>
            <g stroke="#111" stroke-width="3"><line x1="120" y1="153" x2="290" y2="153"/><line x1="120" y1="196" x2="290" y2="196"/><line x1="177" y1="110" x2="177" y2="240"/><line x1="233" y1="110" x2="233" y2="240"/></g>
            <rect x="220" y="40" width="150" height="100" fill="{accent}" stroke="#111" stroke-width="6"/>
            <path d="M330 170 l10 24 24 10 -24 10 -10 24 -10-24 -24-10 24-10z" fill="{ink}"/>''',
        "marche": f'''<line x1="40" y1="262" x2="370" y2="262" stroke="{ink}" stroke-width="6"/>
            <path d="M50 236 L130 200 L200 214 L280 140 L360 70" fill="none" stroke="{accent}" stroke-width="12" stroke-linejoin="round"/>
            <circle cx="360" cy="70" r="16" fill="{V}" stroke="#111" stroke-width="5"/>
            <rect x="60" y="40" width="130" height="70" fill="{ink}"/><text x="76" y="88" font-family="Arimo,Arial" font-weight="700" font-size="34" fill="{fond if ton=='t-noir' else C}">+11,9</text>''',
        "media": f'''<rect x="50" y="40" width="230" height="220" fill="{C}" stroke="{ink}" stroke-width="6"/>
            <rect x="70" y="62" width="190" height="40" fill="#111"/>
            <g stroke="#d9d5cf" stroke-width="10"><line x1="70" y1="130" x2="260" y2="130"/><line x1="70" y1="160" x2="230" y2="160"/><line x1="70" y1="190" x2="250" y2="190"/><line x1="70" y1="220" x2="200" y2="220"/></g>
            <path d="M330 60 v150" stroke="{accent}" stroke-width="16"/><path d="M296 186 l34 46 34-46z" fill="{accent}" stroke="#111" stroke-width="4"/>''',
    }.get(nom)
    if not s:
        return ""
    return f'<svg viewBox="0 0 400 300" role="img" aria-hidden="true" focusable="false">{s}</svg>'


# ---------- morceaux de page ----------
def tete(titre, description, chemin, image=None, base=""):
    og = f'<meta property="og:image" content="{SITE}{image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="627"><meta name="twitter:card" content="summary_large_image">' if image else ""
    return f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titre)}</title><meta name="description" content="{e(description)}"><meta name="author" content="{AUTEUR}">
<link rel="canonical" href="{SITE}{chemin}">
<meta property="og:type" content="article"><meta property="og:locale" content="fr_FR"><meta property="og:site_name" content="La veille de {AUTEUR}">
<meta property="og:title" content="{e(titre)}"><meta property="og:description" content="{e(description)}"><meta property="og:url" content="{SITE}{chemin}">{og}
{FONTS}<link rel="stylesheet" href="{base}assets/style.css"></head><body>'''


def barre(base, actif):
    def l(href, txt, cle, cls=""):
        cur = ' aria-current="page"' if cle == actif else ""
        return f'<a href="{base}{href}"{cur}{(" class=" + chr(34) + cls + chr(34)) if cls else ""}>{txt}</a>'
    return f'''<header class="site wrap"><div class="max"><a class="nom" href="{base}index.html">La veille de {AUTEUR}</a>
<nav aria-label="Navigation du site">{l("index.html","Dernier numéro","index")}{l("archives.html","Archives","archives")}{l("livre-blanc.html","Le livre blanc","lb","lb")}</nav></div></header>'''


def pied(base):
    return f'''<footer class="wrap"><div class="max"><span>Chaque lundi, une veille IA, marketing, communication et design, datée et sourcée. Préparée avec un agent IA, relue et validée par {AUTEUR}. Chaque fait est vérifié, mais une erreur reste possible : signalez-la et elle sera corrigée.</span></div></footer></body></html>'''


def lien_out(url, label, petit=""):
    p = f" <small>{e(petit)}</small>" if petit else ""
    return f'<a href="{e(url)}" target="_blank" rel="noopener">{e(label)}{p} <span aria-hidden="true">↗</span></a>'


def bloc_fait(f):
    c = f.get("chiffre", ["", ""])
    note = f'<span class="tag b2c">{e(f["note"])}</span>' if f.get("note") else ""
    sources = "".join(lien_out(s[2], "Lire l'article complet", s[0] + (", " + s[1] if s[1] else "")) for s in f["sources"])
    return f'''<article class="fait">
  <div class="fig"><strong>{e(c[0])}</strong><span>{e(c[1])}</span></div>
  <div><div class="tags">{"".join(f'<span class="tag">{e(t)}</span>' for t in f["themes"])}{note}</div>
    <h3>{e(f["titre"])}</h3><p>{e(f["resume"])}</p><div class="out">{sources}</div></div>
  <div class="chg"><h4>Ce que ça change pour une équipe marketing B2B</h4><p>{e(f["impact"])}</p></div>
</article>'''


def date_fr(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day if d.day > 1 else '1er'} {MOIS[d.month - 1]} {d.year}"


def page_numero(n, prec, suiv, base):
    et = []
    for i, x in enumerate(n["etapes"]):
        ton = TONS[i % len(TONS)]
        faits = "".join(bloc_fait(n["faits"][fid]) for fid in x["faits"])
        enc = ""
        if x.get("encart"):
            enc = f'<aside class="encart"><span class="i" aria-hidden="true">?</span><div><h4>{e(x["encart"]["titre"])}</h4><p>{e(x["encart"]["texte"])}</p></div></aside>'
        et.append(f'''<section class="etape" id="{x["id"]}" aria-labelledby="h-{x["id"]}">
  <div class="wrap {ton}"><div class="max etape-tete">
    <div><div class="rang">{i + 1}</div><h2 id="h-{x["id"]}">{e(x["titre"])}</h2></div>
    <div class="ill">{illustration(x.get("illustration", ""), ton)}</div></div></div>
  <div class="etape-corps wrap"><div class="max">{faits}{enc}</div></div>
</section>''')
    sommaire = "".join(f'<li><a href="#{x["id"]}"><b>{i + 1}</b><span>{e(x["titre"])}</span><span aria-hidden="true">↓</span></a></li>' for i, x in enumerate(n["etapes"]))
    cles = "".join(f'<div class="k"><strong>{e(k["chiffre"])}</strong><p>{e(k["texte"])}</p><a href="{e(k["url"])}" target="_blank" rel="noopener">Source : {e(k["source"])} ↗</a></div>' for k in n["chiffres_cles"])
    reg = n.get("regard") or {}
    regard = ""
    if reg.get("texte"):
        tag = '<span class="brouillon">Proposition de texte, à réécrire par Bénédicte</span>' if reg.get("statut") == "proposition" else ""
        regard = f'<section class="regard wrap" aria-labelledby="t-reg"><div class="max"><span class="guillemet" aria-hidden="true">“</span><div><h2 id="t-reg">Mon regard</h2><p>{e(reg["texte"])}</p>{tag}</div></div></section>'
    metier = ""
    if n.get("metier"):
        cartes = "".join(f'''<article><div class="haut"><div><div class="tags"><span class="tag">{e(m["theme"])}</span></div><strong class="n">{e(m["chiffre"])}</strong></div>{illustration(m.get("illustration", ""), "t-creme")}</div>
<h3>{e(m["titre"])}</h3><p>{e(m["texte"])}</p><div class="chg"><h4>Ce que ça change</h4><p>{e(m["impact"])}</p></div>
<div class="out">{"".join(lien_out(s[2], "Lire l'article complet", s[0] + ", " + s[1]) for s in m["sources"])}</div></article>''' for m in n["metier"])
        metier = f'<section class="metier wrap" aria-labelledby="t-met"><div class="max"><h2 id="t-met">Le métier, au-delà de l\'IA</h2><p class="lede">Marketing, communication, design : ce qui bouge dans nos métiers, IA ou pas.</p><div class="mgrid">{cartes}</div></div></section>'
    ctx = ""
    if n.get("contexte"):
        ctx = '<section class="ctx wrap" aria-labelledby="t-ctx"><div class="max"><h2 id="t-ctx">Le contexte</h2><p class="lede">Ce qui éclaire la semaine, au-delà de ses sept jours.</p><div class="cgrid">' + "".join(
            f'<article><h3>{e(c["titre"])}</h3><p>{e(c["texte"])}</p><div class="out">{lien_out(c["url"], LIRE_ETUDE, c["source"])}</div></article>' for c in n["contexte"]) + "</div></div></section>"
    tend = f'<section class="tendance wrap"><div class="max"><h2>La tendance de fond</h2><p>{e(n["tendance"])}</p></div></section>' if n.get("tendance") else ""
    aussi = ""
    if n.get("aussi"):
        aussi = '<section class="aussi wrap" aria-labelledby="t-aussi"><div class="max"><h2 id="t-aussi">À surveiller aussi</h2><ul>' + "".join(
            f'<li>{e(a["texte"])} <a href="{e(a["url"])}" target="_blank" rel="noopener">Lire sur {e(a["source"])} ↗</a></li>' for a in n["aussi"]) + "</ul></div></section>"
    p = f'<a href="{base}numeros/{prec["slug"]}.html">← N° {prec["numero"]} · {e(prec["label"])}</a>' if prec else '<span class="vide">Premier numéro</span>'
    s = f'<a href="{base}numeros/{suiv["slug"]}.html">N° {suiv["numero"]} · {e(suiv["label"])} →</a>' if suiv else f'<a href="{base}archives.html">Tous les numéros</a>'
    return f'''<div class="une wrap"><div class="max">
  <div class="meta"><span class="num">N° {n["numero"]}</span><span>{e(n["label"])}</span></div>
  <h1>{e(n["titre"])}</h1>
  <div class="band">IA · MARKETING · COMMUNICATION · DESIGN</div>
  <div class="chapo"><div>{"".join(f"<p>{e(x)}</p>" for x in n["chapo"])}</div>
    <nav class="sommaire" aria-labelledby="t-som"><h2 id="t-som">Le fil de la semaine, en {len(n["etapes"])} temps</h2><ol>{sommaire}</ol></nav></div>
</div></div>
<section class="chiffres wrap" aria-labelledby="t-k"><div class="max"><h2 id="t-k">Les chiffres à retenir</h2><div class="kgrid">{cles}</div></div></section>
{regard}
{"".join(et)}
{metier}{ctx}{tend}{aussi}
<nav class="pager wrap" aria-label="Numéros"><div class="max">{p}{s}</div></nav>'''


def description(n):
    return f'N° {n["numero"]}, {n["label"]} : {n["titre"]} {n["chapo"][0]}'


def construire(og=False):
    nums = sorted((json.loads(p.read_text()) for p in (RACINE / "contenu" / "numeros").glob("*.json")), key=lambda x: x["numero"])
    (RACINE / "numeros").mkdir(exist_ok=True)
    for i, n in enumerate(nums):
        prec = nums[i - 1] if i > 0 else None
        suiv = nums[i + 1] if i + 1 < len(nums) else None
        img = f'assets/og/{n["slug"]}.png'
        titre = f'{n["titre"]} · La veille n° {n["numero"]}'
        corps = page_numero(n, prec, suiv, "../")
        (RACINE / "numeros" / f'{n["slug"]}.html').write_text(tete(titre, description(n), f'numeros/{n["slug"]}.html', img, "../") + barre("../", "") + corps + pied("../"))
    der = nums[-1]
    (RACINE / "index.html").write_text(
        tete(f'{der["titre"]} · La veille de {AUTEUR}', description(der), "", f'assets/og/{der["slug"]}.png') + barre("", "index") + page_numero(der, nums[-2] if len(nums) > 1 else None, None, "") + pied(""))
    # archives
    themes = sorted({t for n in nums for t in n["themes"]})
    lis = "".join(f'''<li data-themes="{e(",".join(n["themes"]))}"><a href="numeros/{n["slug"]}.html"><span class="n">{n["numero"]}</span>
<div><h2>{e(n["titre"])}</h2><p>{e(" · ".join(x["titre"] for x in n["etapes"]))}</p></div><span class="d">{e(n["periode"])}</span></a></li>''' for n in reversed(nums))
    boutons = '<button type="button" aria-pressed="true" data-t="">Tous</button>' + "".join(f'<button type="button" aria-pressed="false" data-t="{e(t)}">{e(t)}</button>' for t in themes)
    archives = f'''<main class="arch wrap"><div class="max"><h1>Archives</h1><p class="lede">Tous les numéros de la veille, du plus récent au plus ancien. {len(nums)} numéro{"s" if len(nums) > 1 else ""} à ce jour.</p>
<div class="filtres" role="group" aria-label="Filtrer par thème">{boutons}</div><ul class="liste" id="liste">{lis}</ul></div></main>
<script>
document.querySelector(".filtres").addEventListener("click",ev=>{{const b=ev.target.closest("button");if(!b)return;
document.querySelectorAll(".filtres button").forEach(x=>x.setAttribute("aria-pressed",x===b));
document.querySelectorAll("#liste li").forEach(li=>{{li.hidden=!!b.dataset.t&&!li.dataset.themes.split(",").includes(b.dataset.t);}});}});
</script>'''
    (RACINE / "archives.html").write_text(tete(f"Archives · La veille de {AUTEUR}", "Tous les numéros de la veille IA, marketing, communication et design.", "archives.html") + barre("", "archives") + archives + pied(""))
    # livre blanc
    lb_meta = RACINE / "contenu" / "livre-blanc.json"
    lb = json.loads(lb_meta.read_text()) if lb_meta.exists() else {}
    dispo = bool(lb.get("pdf"))
    bouton = f'<a class="btn" href="{e(lb["pdf"])}">Télécharger le livre blanc (PDF)</a>' if dispo else '<span class="btn" aria-disabled="true">Bientôt disponible</span>'
    page_lb = f'''<main class="lb-page wrap"><div class="max lb-grid"><div>
<h1>{e(lb.get("titre", "IA, marketing, communication, design : ce qui a changé en 2026"))}</h1>
<p class="lede">{e(lb.get("accroche", "Neuf mois d'évolutions, de janvier à septembre 2026, lus avec un regard de responsable marketing et communication B2B : les faits marquants, les chiffres, les tendances de fond, et ce qu'ils changent concrètement."))}</p>
<ul>{"".join(f"<li>{e(x)}</li>" for x in lb.get("sommaire", ["Les faits marquants, mois par mois", "IA, marketing, communication, design : ce qui change", "Le saviez-vous : AEO, GEO et AI Act", "Les tendances de fond pour 2027"]))}</ul>
{bouton}</div>
<div class="couv" aria-hidden="true"><span style="font-weight:700">{AUTEUR}</span><strong>Ce qui a changé en 2026</strong><span class="band">IA · MARKETING · COM · DESIGN</span></div></div></main>'''
    (RACINE / "livre-blanc.html").write_text(tete(f"Le livre blanc · La veille de {AUTEUR}", "IA, marketing, communication, design : ce qui a changé de janvier à septembre 2026.", "livre-blanc.html") + barre("", "lb") + page_lb + pied(""))
    (RACINE / ".nojekyll").write_text("")
    if og:
        images_og(nums)
    print(f"{len(nums)} numéro(s) générés.")


def images_og(nums):
    from playwright.sync_api import sync_playwright
    (RACINE / "assets" / "og").mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 627})
        for n in nums:
            k = n["chiffres_cles"][0]
            pg.set_content(f'''<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;box-sizing:border-box}}body{{width:1200px;height:627px;background:#e64855;color:#111;font-family:Arimo,"Liberation Sans",Arial,sans-serif;padding:56px 64px;position:relative;overflow:hidden}}
.s{{font-size:24px;font-weight:700}}h1{{font-size:88px;line-height:.92;letter-spacing:-.045em;margin-top:30px;max-width:12.5ch}}
.b{{position:absolute;left:64px;bottom:52px;display:flex;gap:14px}}.b span{{background:#cbe170;font-weight:700;font-size:24px;padding:10px 16px}}.b em{{font-style:normal;font-size:24px;font-weight:700;background:#111;color:#f5f5f2;padding:10px 16px}}
.k{{position:absolute;right:64px;top:150px;width:300px;background:#111;color:#f5f5f2;padding:26px}}.k b{{display:block;font-size:80px;line-height:1;color:#cbe170;letter-spacing:-.03em}}.k p{{font-size:21px;margin-top:10px}}
</style></head><body><div class="s">La veille de {AUTEUR} · N° {n["numero"]} · {e(n["label"])}</div><h1>{e(n["titre"])}</h1>
<div class="k"><b>{e(k["chiffre"])}</b><p>{e(k["texte"])}</p></div><div class="b"><span>IA · MARKETING · COM · DESIGN</span><em>{sum(len(x["faits"]) for x in n["etapes"])} faits · {len(n["chiffres_cles"])} chiffres clés</em></div></body></html>''')
            pg.screenshot(path=str(RACINE / "assets" / "og" / f'{n["slug"]}.png'))
        b.close()


if __name__ == "__main__":
    construire(og="--og" in sys.argv)
