"""Génère le site de la veille à partir des fichiers de contenu.

Usage : python3 outils/build.py            (génère les pages HTML)
        python3 outils/build.py --og       (génère aussi les images de partage LinkedIn, nécessite Playwright)

Entrée : contenu/numeros/NNN.json (un fichier par numéro)
Sortie : index.html (dernier numéro), numeros/NNN.html, archives.html, livre-blanc.html, assets/og/NNN.png
"""
import json, html, pathlib, sys, datetime, unicodedata

RACINE = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://benegermaine.github.io/veille/"
AUTEUR = "Bénédicte Lallement"
# Avant le lancement officiel : on demande aux moteurs de recherche de ne pas indexer le site. Mettre "" le jour du lancement.
ROBOTS = ""  # site ouvert à l'indexation depuis le 19 octobre 2026
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Arimo:wght@400;700&display=swap">'
LIRE_ETUDE = "Lire l'étude"
# formulaire d'inscription Brevo (liste « Veille Béné Germaine », double confirmation, mail de bienvenue)
INSCRIPTION = "https://24cb74ef.sibforms.com/serve/MUIFANd7p_vAfp7q87HCAQnkAHyVEC7nthoTSX8Zp-39994pa6a52hki5X2kDXJINWiUD_KhGiNL5eFfgOc4gZXLvCxY3oYLDSdFGuMYtTJ-fdrNZw-XoVtxdn8sOUlsg09zqTcFgab5zRkRE43vgRpUT3mqLaEcpN4GSb5C1N0ph_sN6iCILFCL0-a8g9VjLank4ZXp7f-6kn-rYA=="
LIEN_INSCRIPTION = lambda txt, cls="": f'<a{(" class=" + chr(34) + cls + chr(34)) if cls else ""} href="{INSCRIPTION}" target="_blank" rel="noopener" data-goatcounter-click="inscription-veille" data-goatcounter-title="Inscription à la veille">{txt} <span aria-hidden="true">↗</span></a>'
# mesure d'audience GoatCounter (sans cookies) : https://benegermaine.goatcounter.com
GOATCOUNTER = '<script data-goatcounter="https://benegermaine.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>'
# apparition douce des blocs au défilement (désactivée si l'utilisateur limite les animations)
APPARITION = """<script>(function(){var d=document.documentElement;if(!("IntersectionObserver" in window)||matchMedia("(prefers-reduced-motion: reduce)").matches)return;d.classList.add("anim");
var o=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){x.target.classList.add("vu");o.unobserve(x.target);}});},{rootMargin:"0px 0px -8% 0px"});
document.querySelectorAll(".reveal,.fait,.k,.mgrid article,.cgrid article,.regard blockquote").forEach(function(el){el.classList.add("reveal");o.observe(el);});})();
(function(){var bar=document.querySelector(".collant"),som=document.querySelector(".sommaire"),haut=document.querySelector(".haut-page");
var liens=bar?[].slice.call(bar.querySelectorAll("a")):[],cibles=liens.map(function(a){return document.getElementById(a.dataset.cible);}),verrou=0;
if(bar)bar.hidden=false;
function marquer(i){liens.forEach(function(a,k){if(k===i)a.setAttribute("aria-current","true");else a.removeAttribute("aria-current");});}
function maj(){var y=window.scrollY;
 if(haut)haut.classList.toggle("visible",y>700);
 if(!bar||!som)return;
 bar.classList.toggle("visible",som.getBoundingClientRect().bottom<0);
 if(Date.now()<verrou)return;
 var actif=-1;cibles.forEach(function(el,k){if(el&&el.getBoundingClientRect().top<=140)actif=k;});
 if(window.innerHeight+y>=document.documentElement.scrollHeight-4)actif=cibles.length-1;
 marquer(actif);}
liens.forEach(function(a,k){a.addEventListener("click",function(){marquer(k);verrou=Date.now()+900;});});
var t=0;window.addEventListener("scroll",function(){if(!t){t=requestAnimationFrame(function(){t=0;maj();});}},{passive:true});maj();
if(haut)haut.addEventListener("click",function(ev){ev.preventDefault();window.scrollTo({top:0,behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth"});});})();</script>"""
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

e = lambda s: html.escape(str(s), quote=True)


def cle_theme(t):
    """« Communication » -> « communication », pour colorer l'étiquette du thème."""
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if c.isalnum() and not unicodedata.combining(c))


# ---------- morceaux de page ----------
def tete(titre, description, chemin, image=None, base=""):
    og = f'<meta property="og:image" content="{SITE}{image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="627"><meta name="twitter:card" content="summary_large_image">' if image else ""
    return f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titre)}</title><meta name="description" content="{e(description)}"><meta name="author" content="{AUTEUR}">{ROBOTS}
<link rel="canonical" href="{SITE}{chemin}">
<meta property="og:type" content="article"><meta property="og:locale" content="fr_FR"><meta property="og:site_name" content="Béné Germaine · la veille du lundi de {AUTEUR}">
<meta property="og:title" content="{e(titre)}"><meta property="og:description" content="{e(description)}"><meta property="og:url" content="{SITE}{chemin}">{og}
{FONTS}<link rel="stylesheet" href="{base}assets/style.css"><link rel="icon" href="{base}assets/favicon.svg" type="image/svg+xml"></head><body>'''


def barre(base, actif):
    def l(href, txt, cle, cls=""):
        cur = ' aria-current="page"' if cle == actif else ""
        return f'<a href="{base}{href}"{cur}{(" class=" + chr(34) + cls + chr(34)) if cls else ""}>{txt}</a>'
    return f'''<header class="site wrap"><div class="max"><a class="logo" href="{base}index.html" aria-label="Béné Germaine, la veille du lundi de {AUTEUR} : accueil"><span class="l-bene">Béné</span><span class="l-wm"><span class="gsq">G</span>ermaine<span class="pt">.</span></span></a>
<nav aria-label="Navigation du site">{l("index.html","Dernier numéro","index")}{l("archives.html","Archives","archives")}{l("livre-blanc.html","Le livre blanc","lb")}</nav></div></header>'''


def pied(base):
    return f'''<footer class="pied wrap"><div class="max"><p>Chaque lundi, une veille IA, marketing, communication et design, datée et sourcée. Préparée avec un agent IA, relue et validée par {AUTEUR}. Chaque fait est vérifié, mais une erreur reste possible : signalez-la et elle sera corrigée. {LIEN_INSCRIPTION("Recevoir la veille chaque lundi")}</p></div></footer><a class="haut-page" href="#" aria-label="Remonter en haut de la page">↑</a>{GOATCOUNTER}{APPARITION}</body></html>'''


def photo(base, img, cls="photo"):
    """Insère une image seulement si le fichier existe dans le dépôt (sinon rien).
    style "photo" : passée en noir et blanc avec un aplat de couleur décalé (effet collage), la couleur revient au survol.
    style "collage" : image déjà colorée, affichée telle quelle."""
    if not img or not (RACINE / img["src"]).exists():
        return ""
    cap = f'<figcaption>{e(img["legende"])}</figcaption>' if img.get("legende") else ""
    style = "nb" if img.get("style", "photo") == "photo" else "collage"
    acc = " acc-vert" if img.get("accent") == "vert" else ""
    return f'<figure class="{cls} {style}{acc} reveal"><img src="{base}{e(img["src"])}" alt="{e(img.get("alt", ""))}" loading="lazy">{cap}</figure>'


def lien_out(url, label, petit=""):
    p = f" <small>{e(petit)}</small>" if petit else ""
    return f'<a href="{e(url)}" target="_blank" rel="noopener">{e(label)}{p} <span aria-hidden="true">↗</span></a>'


def bloc_fait(f):
    c = f.get("chiffre", ["", ""])
    note = f'<span class="tag b2c">{e(f["note"])}</span>' if f.get("note") else ""
    sources = "".join(lien_out(s[2], "Lire l'article complet", s[0] + (", " + s[1] if s[1] else "")) for s in f["sources"])
    return f'''<article class="fait">
  <div><div class="tags">{"".join(f'<span class="tag t-{cle_theme(t)}">{e(t)}</span>' for t in f["themes"])}{note}</div>
    <h3>{e(f["titre"])}</h3><p>{e(f["resume"])}</p><div class="out">{sources}</div></div>
  <div><div class="fig"><small>Le chiffre</small><strong>{e(c[0])}</strong><span>{e(c[1])}</span></div>
  <div class="chg"><h4>Ce que ça change pour une équipe marketing B2B</h4><p>{e(f["impact"])}</p></div></div>
</article>'''


def date_fr(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day if d.day > 1 else '1er'} {MOIS[d.month - 1]} {d.year}"


def page_numero(n, prec, suiv, base):
    et = []
    for i, x in enumerate(n["etapes"]):
        faits = "".join(bloc_fait(n["faits"][fid]) for fid in x["faits"])
        enc = ""
        if x.get("encart"):
            enc = f'<aside class="encart"><h4>{e(x["encart"]["titre"])}</h4><p>{e(x["encart"]["texte"])}</p></aside>'
        et.append(f'''<section class="etape wrap {("ton-rouge", "ton-vert")[i % 2]}" id="{x["id"]}" aria-labelledby="h-{x["id"]}"><div class="max">
  <div class="etape-tete"><span class="rang gsq" aria-hidden="true">{i + 1:02d}</span><div><p class="kicker">Le fil de la semaine</p><h2 id="h-{x["id"]}">{e(x["titre"])}</h2></div></div>
  {photo(base, x.get("image"))}{faits}{enc}</div>
</section>''')
    entrees = [(x["id"], f"{i + 1:02d}", x["titre"]) for i, x in enumerate(n["etapes"])]
    if n.get("metier"): entrees.append(("metier", "+", "Le métier, au-delà de l'IA"))
    if n.get("contexte"): entrees.append(("contexte", "+", "Le contexte"))
    if (n.get("regard") or {}).get("texte"): entrees.append(("regard", "+", "Mon regard"))
    sommaire = "".join(f'<li><a href="#{a}"><b>{b}</b><span>{e(c)}</span><i aria-hidden="true">↓</i></a></li>' for a, b, c in entrees)
    collant = "".join(f'<a href="#{a}" data-cible="{a}">{b if b != "+" else e(c.split(",")[0])}</a>' for a, b, c in entrees)
    cles = "".join(f'<div class="k"><strong>{e(k["chiffre"])}</strong><p>{e(k["texte"])}</p><a href="{e(k["url"])}" target="_blank" rel="noopener">{e(k["source"])} ↗</a></div>' for k in n["chiffres_cles"])
    reg = n.get("regard") or {}
    regard = ""
    if reg.get("texte"):
        tag = '<span class="brouillon">Proposition de texte, à réécrire par Bénédicte</span>' if reg.get("statut") == "proposition" else ""
        regard = f'<section class="regard wrap" id="regard" aria-labelledby="t-reg"><div class="etroit"><p class="kicker" id="t-reg">Mon regard</p><blockquote><p>{e(reg["texte"])}</p><footer>{AUTEUR}</footer></blockquote>{tag}</div></section>'
    metier = ""
    if n.get("metier"):
        cartes = "".join(f'''<article><div class="tags"><span class="tag t-{cle_theme(m["theme"])}">{e(m["theme"])}</span></div><strong class="n">{e(m["chiffre"])}</strong>
<h3>{e(m["titre"])}</h3><p>{e(m["texte"])}</p><div class="chg"><h4>Ce que ça change</h4><p>{e(m["impact"])}</p></div>
<div class="out">{"".join(lien_out(s[2], "Lire l'article complet", s[0] + ", " + s[1]) for s in m["sources"])}</div></article>''' for m in n["metier"])
        metier = f'<section class="section wrap" id="metier" aria-labelledby="t-met"><div class="max"><p class="kicker">Au-delà de l\'IA</p><h2 id="t-met">Le métier</h2><p class="lede">Marketing, communication, design : ce qui bouge dans nos métiers, IA ou pas.</p><div class="mgrid">{cartes}</div></div></section>'
    ctx = ""
    if n.get("contexte"):
        ctx = '<section class="section wrap" id="contexte" aria-labelledby="t-ctx"><div class="max"><p class="kicker">Pour prendre du recul</p><h2 id="t-ctx">Le contexte</h2><p class="lede">Ce qui éclaire la semaine, au-delà de ses sept jours.</p><div class="cgrid">' + "".join(
            f'<article><h3>{e(c["titre"])}</h3><p>{e(c["texte"])}</p><div class="out">{lien_out(c["url"], LIRE_ETUDE, c["source"])}</div></article>' for c in n["contexte"]) + "</div></div></section>"
    tend = f'<section class="tendance wrap"><div class="max"><p class="kicker">La tendance de fond</p><p>{e(n["tendance"])}</p></div></section>' if n.get("tendance") else ""
    aussi = ""
    if n.get("aussi"):
        aussi = '<section class="section aussi wrap" aria-labelledby="t-aussi"><div class="max"><h2 id="t-aussi">À surveiller aussi</h2><p class="lede">En bref, avec le lien vers l\'article.</p><ul>' + "".join(
            f'<li>{e(a["texte"])} <a href="{e(a["url"])}" target="_blank" rel="noopener">Lire sur {e(a["source"])} ↗</a></li>' for a in n["aussi"]) + "</ul></div></section>"
    p = f'<a href="{base}numeros/{prec["slug"]}.html">← N° {prec["numero"]} · {e(prec["label"])}</a>' if prec else '<span class="vide">Premier numéro</span>'
    s = f'<a href="{base}numeros/{suiv["slug"]}.html">N° {suiv["numero"]} · {e(suiv["label"])} →</a>' if suiv else f'<a href="{base}archives.html">Tous les numéros →</a>'
    return f'''<div class="bienvenue wrap"><div class="max"><p><strong>Bienvenue dans la veille de {AUTEUR}.</strong> Chaque lundi, ce qui a bougé dans l'IA, le marketing, la communication et le design B2B : quelques faits datés et sourcés, et ce qu'ils changent concrètement pour une équipe marketing. <a href="{base}archives.html">Voir tous les numéros</a> · {LIEN_INSCRIPTION("Recevoir la veille par e-mail")}</p></div></div>
<nav class="collant" aria-label="Parties de ce numéro" hidden><div class="max">{collant}</div></nav>
<div class="une wrap"><div class="max">
  <div class="meta"><span class="num">N° {n["numero"]}</span><span>{e(n["label"])}</span></div>
  <h1>{e(n["titre"])}</h1>
  <div class="une-grille"><div class="chapo">{"".join(f"<p>{e(x)}</p>" for x in n["chapo"])}</div>{photo(base, n.get("image"), "hero")}</div>
</div></div>
<div class="wrap"><div class="max"><nav class="sommaire" aria-labelledby="t-som"><h2 id="t-som">Au sommaire</h2><ol>{sommaire}</ol></nav></div></div>
<section class="chiffres wrap" aria-labelledby="t-k" style="margin-top:clamp(48px,7vw,88px)"><div class="max"><h2 id="t-k">Les chiffres à retenir</h2><div class="kgrid">{cles}</div></div></section>
{"".join(et)}
{metier}{ctx}{tend}{regard}{aussi}
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
<div><h2>{e(n["titre"])}</h2><p>{e(" · ".join(x["titre"] for x in n["etapes"]))}</p></div><span class="d">{e(n["label"])}</span></a></li>''' for n in reversed(nums))
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
    bouton = f'<a class="btn" href="{e(lb["pdf"])}" target="_blank" rel="noopener" data-goatcounter-click="telechargement-livre-blanc" data-goatcounter-title="Téléchargement du livre blanc">Télécharger le livre blanc (PDF) <span aria-hidden="true">↗</span></a>' if dispo else '<span class="btn" aria-disabled="true">Bientôt disponible</span>'
    couv_img = lb.get("couverture")
    a_photo = bool(couv_img) and (RACINE / couv_img).exists()
    couv = (f'<div class="couv" aria-hidden="true">' + (f'<img src="{e(couv_img)}" alt="">' if a_photo else "") +
            f'<div class="titre"><strong>Ce qui a changé en 2026</strong><span>IA · Marketing · Com · Design</span></div></div>')
    if not a_photo:
        couv = couv.replace('class="couv"', 'class="couv sans-photo"')
    page_lb = f'''<main class="lb-page wrap"><div class="max lb-grid"><div>
<p class="kicker">Le livre blanc</p>
<h1>{e(lb.get("titre", "IA, marketing, communication, design : ce qui a changé en 2026"))}</h1>
<p class="lede">{e(lb.get("accroche", ""))}</p>
<ul>{"".join(f"<li>{e(x)}</li>" for x in lb.get("sommaire", []))}</ul>
{bouton} {LIEN_INSCRIPTION("Recevoir la veille chaque lundi", "btn btn-sec")}</div>
{couv}</div></main>'''
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
