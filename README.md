# La veille de Bénédicte Lallement

Une veille hebdomadaire IA, marketing, communication et design, pensée pour les responsables marketing et communication B2B. Elle est préparée chaque lundi par un agent IA, relue et validée par Bénédicte, puis publiée ici.

Site : https://benegermaine.github.io/veille/ (une fois GitHub Pages activé)

## Le circuit, chaque lundi

1. **8 h 26 : l'agent fait la veille.** Une tâche planifiée dans Claude cherche les nouvelles de la semaine écoulée, vérifie les dates et les sources, et rédige la veille : le fil conducteur, les chiffres clés, les faits rangés par étape, le métier hors IA et une proposition de « Mon regard ».
2. **Elle arrive dans Notion**, dans la base « Veille hebdo », avec le statut « À relire ». Un mail prévient Bénédicte.
3. **Bénédicte relit et corrige** directement dans la page Notion, et réécrit « Mon regard » avec ses mots.
4. **Publication.** Sur son feu vert, Claude transforme la page en fichier de contenu (`contenu/numeros/NNN.json`), génère les pages du site et les envoie sur GitHub. Le site se met à jour en une à deux minutes.
5. **Diffusion.** Claude propose un post LinkedIn. C'est Bénédicte qui le publie.

## Ce qu'il y a dans ce dépôt

| Dossier ou fichier | À quoi il sert |
|---|---|
| `contenu/numeros/` | Le contenu de chaque numéro, un fichier par semaine. C'est la seule chose qui change chaque lundi. |
| `contenu/livre-blanc.json` | Le titre, l'accroche et le lien du PDF du livre blanc (à créer quand le PDF est prêt). |
| `outils/build.py` | Le script qui fabrique les pages du site à partir du contenu. |
| `assets/style.css` | La charte graphique du site : rouge, vert, noir, blanc cassé, police Arimo. |
| `assets/og/` | Les images qui s'affichent quand on partage un lien sur LinkedIn. |
| `index.html`, `numeros/`, `archives.html`, `livre-blanc.html` | Les pages du site, générées automatiquement. Ne pas les modifier à la main : elles seraient écrasées au numéro suivant. |

## Les archives

- La page d'accueil affiche toujours le dernier numéro.
- Chaque numéro garde sa propre page (`numeros/001.html`, `numeros/002.html`…), avec des liens vers le numéro précédent et le suivant.
- La page « Archives » liste tous les numéros, avec un filtre par thème.
- GitHub garde l'historique de chaque modification : on peut toujours voir une ancienne version ou revenir en arrière (onglet « Commits »).

## Corriger quelque chose après publication

- **Le plus simple** : demander à Claude, qui corrige le fichier de contenu et republie.
- **Soi-même** : sur github.com, ouvrir le fichier `contenu/numeros/NNN.json`, cliquer sur le crayon, corriger le texte entre guillemets, puis « Commit changes ». Demander ensuite à Claude de régénérer les pages.

## Activer le site (une seule fois)

Dans le dépôt sur github.com : **Settings > Pages**, puis « Deploy from a branch », branche **main**, dossier **/ (root)**, et **Save**. Le site est en ligne quelques minutes plus tard.

## Règles éditoriales

- Chaque fait est daté et lié à sa source. Rien n'est inventé.
- Jamais plus de deux faits venant d'un même média.
- Priorité au B2B (marque, notoriété, contenu, communication). Une information surtout B2C est signalée comme telle.
- « Mon regard » est toujours écrit ou validé par Bénédicte.

## Les outils utilisés

Claude (agent de veille et de rédaction) · Notion (rédaction et relecture) · GitHub et GitHub Pages (hébergement gratuit et archives) · LinkedIn (diffusion).
