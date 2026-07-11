# 🚲 AI Bike Fit

**🌍 Language / Langue : [🇬🇧 English](README.md) · 🇫🇷 Français (cette page)**

**Note ton propre réglage vélo (bike fit) grâce à l'IA — gratuitement.**

Filme-toi en train de pédaler sur home-trainer, et cet outil note ton réglage
vélo comme le ferait un fitter professionnel. Il suit tes articulations, mesure
les angles au bas du coup de pédale, et dessine un squelette coloré sur la vidéo :

- 🟢 **vert** = réglé aux petits oignons
- 🟠 **orange** = limite
- 🔴 **rouge** = à corriger

Puis il te dit le changement exact à faire, par ex. *« genou trop tendu, baisse
ta selle d'environ 8 mm ».*

Il lit les mêmes angles corporels qu'un fitter payant regarde (hauteur de selle
via ton genou, allonge via ton épaule et ton coude), les note contre des plages
issues de la recherche publiée, et te donne un avant/après que tu peux vraiment
voir.

---

## Deux façons de l'utiliser

### 🟢 La méthode facile — laisse Claude Code tout faire

Tu ne télécharges rien, ne crées aucun dossier, n'écris aucun code.
[Claude Code](https://claude.com/claude-code) (l'agent de code gratuit dans ton
terminal) fait tout à ta place.

1. Installe Claude Code.
2. Ouvre-le dans un dossier vide.
3. Colle le prompt depuis [`PROMPT.md`](PROMPT.md) (version française disponible) et envoie-le.
4. Donne-lui ta vidéo quand il la demande.

Il te guide pas à pas dans toute la procédure. **C'est la voie recommandée si tu
n'es pas technique.**

### 🔧 La méthode manuelle — lance-le toi-même

Pour ceux à l'aise avec un terminal.

**Installation en une commande** (installe uv, toutes les dépendances et ffmpeg
pour toi) :

```bash
git clone https://github.com/guzlz/ai-bike-fit.git
cd ai-bike-fit
# Windows :
powershell -ExecutionPolicy Bypass -File setup.ps1
# macOS / Linux :
bash setup.sh
```

Puis lance : `uv run python analyze_bikefit.py --input ma-video.mov --out out_fit`

**Ou installe à la main** — deux options :

**Avec [uv](https://docs.astral.sh/uv/) (recommandé — gère Python pour toi) :**

```bash
git clone https://github.com/guzlz/ai-bike-fit.git
cd ai-bike-fit
uv sync
uv run python analyze_bikefit.py --input ma-video.mov --out out_fit
```

**Avec pip :**

```bash
git clone https://github.com/guzlz/ai-bike-fit.git
cd ai-bike-fit

# Installe PyTorch (choisis-en un) :
pip install torch torchvision                                              # CPU
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128  # GPU NVIDIA

pip install -r requirements.txt
python analyze_bikefit.py --input ma-video.mov --out out_fit
```

> **Il te faut aussi [ffmpeg](https://ffmpeg.org/) dans ton PATH :**
> `winget install Gyan.FFmpeg` (Windows) · `brew install ffmpeg` (Mac) ·
> `apt install ffmpeg` (Linux).

Le **premier lancement télécharge le modèle de pose** (`yolo11x-pose.pt`, ~113 Mo)
une seule fois. Sur une machine sans GPU c'est plus lent — ajoute
`--model yolo11n-pose.pt` pour troquer un peu de précision contre de la vitesse.

Si ta vidéo contient la montée/descente du vélo aux extrémités, découpe la fenêtre
de pédalage :

```bash
python analyze_bikefit.py --input ma-video.mov --out out_fit --start 5 --end 35
```

---

## 🎥 Bien filmer (c'est 90 % du résultat)

Un outil de fit ne vaut que ce que vaut la vidéo. Quatre-vingt-dix secondes de
préparation ici t'évitent de refilmer :

- **De profil.** Caméra directement sur le côté du vélo, objectif droit vers toi,
  bien perpendiculaire au vélo. Ni devant, ni derrière, ni en biais.
- **À hauteur de hanche.** Pose le téléphone à la hauteur de ta hanche ou du
  pédalier, sur un support stable. Pas en plongée depuis debout.
- **Rien ne cache ta jambe et ton bras proches.** Écarte le ventilateur, les
  bidons, tout ce qui est entre la caméra et ton corps.
- **Le home-trainer est idéal** (tu restes au même endroit). En extérieur ça
  marche si quelqu'un te filme passant droit, perpendiculaire au profil.
- **Pédale régulièrement 20 à 30 secondes** à effort facile et cadence normale.
- **Bonne lumière.** Pièce claire ou lumière du jour → moins de flou → lecture
  plus précise.
- **Mains là où tu roules d'habitude** (sur les cocottes pour la plupart), pendant
  toute la vidéo.
- **Vélo de route / position route.** Ces plages sont pour un réglage route ou
  home-trainer. Les vélos de tri/CLM sont plus bas et plus agressifs et demandent
  d'autres valeurs.

**Une astuce qui évite de refilmer :** découpe la vidéo pour ne garder que la
partie pédalage (coupe la montée et la descente), ou utilise `--start` / `--end`.

---

## 📊 Ce que tu obtiens

```text
out_fit/
  overlay_h264.mp4     # toute ta vidéo avec le squelette coloré (se lit partout)
  stills/              # l'image au bas du coup de pédale + quelques autres
  report.md            # verdict en clair + la correction exacte
  report.json          # la même chose, structurée
```

`report.md` ressemble à ça (les libellés sont en anglais dans le fichier généré) :

```text
# Bike fit report
- Overall: RED - fix needed

## Angles (deg) vs target
- knee_flexion_bdc: 45 (target 30-40) -> RED
- torso_from_horiz: 44 (target 40-50) -> GREEN
- elbow_flexion: 22 (target 15-30) -> GREEN
- shoulder_angle: 88 (target 80-95) -> GREEN

## Do this
- Knee 45deg at bottom (target 30-40) -> saddle TOO LOW. Raise saddle ~10mm.
```

> 💡 Via la méthode Claude Code (prompt FR), Claude t'explique ce rapport **en
> français** et te dit quoi changer en premier.

Capture l'avant, fais le changement, refilme, et regarde les articulations
passer au vert.

---

## 🎨 Ce que signifient les couleurs

| Angle (de profil) | Zone verte | Rouge signifie |
|---|---|---|
| Genou en bas | 30–40° | > 42 selle trop basse (remonter) ; < 28 trop haute (baisser) |
| Torse par rapport à l'horizontale | 40–50° | > 56 trop redressé ; < 34 très agressif |
| Flexion du coude | 15–30° | proche de 0 = bras verrouillé (assouplir / raccourcir l'allonge) |
| Épaule (torse vers bras) | ~80–95° | poste de pilotage fermé/tassé, poids sur les mains |
| Hanche en haut | ~85–110° | souplesse / allonge (informatif seulement) |

Les sources complètes et la recherche derrière ces nombres sont dans
[`files/bikefit-research-ranges.md`](files/bikefit-research-ranges.md).

---

## 🧠 Comment ça marche (les briques open-source)

- **[Ultralytics YOLO11](https://github.com/ultralytics/ultralytics)** — le modèle
  de vision. Il regarde chaque image et renvoie **17 points-clés du corps**
  (épaules, coudes, poignets, hanches, genoux, chevilles…), chacun avec une
  position en pixels et une confiance. On utilise la variante **pose**
  `yolo11x-pose` (grand modèle, pour rester précis malgré le flou de mouvement du
  pédalage ; les poids sont téléchargés chez Ultralytics au premier lancement, pas
  livrés dans ce dépôt). Tout le reste — trouver le bas du coup de pédale,
  transformer les articulations en angles de fit — est de la géométrie simple.
  *AGPL-3.0.*
- **[supervision](https://github.com/roboflow/supervision)** par Roboflow —
  lecture des images vidéo et dessin des annotations. *MIT.*
- **OpenCV** + **NumPy** pour le traitement d'image et le calcul des angles,
  **PyTorch** pour faire tourner le modèle (sur ton GPU si tu en as un), **ffmpeg**
  pour que la vidéo se lise partout.

Les angles de fit sont notés contre des plages issues des sciences du sport
publiées (méthode Holmes + une étude de validité dynamique-vs-statique). Sources
dans [`files/bikefit-research-ranges.md`](files/bikefit-research-ranges.md).

---

## ⚠️ Notes et limites

- Une vidéo 2D de profil te donne des **plages de population et un excellent point
  de départ, pas un fit pro en 3D**. Pour une douleur persistante, des
  engourdissements ou un gros changement de position, consulte un vrai fitter.
- **Plages route.** Les configs tri/CLM sont plus basses et plus agressives —
  profil différent.
- **Pas un avis médical.** Si quelque chose fait mal, change une seule chose à la
  fois et arrête si ça empire.
- Garde le grand modèle (`yolo11x-pose`) sauf si tu es sur un CPU lent et veux
  juste un aperçu rapide — le petit modèle n'arrive pas à situer ton genou/ta
  cheville dans le flou du pédalage.
- **Change une seule chose par séance** (hauteur de selle OU allonge, pas les
  deux) et refilme, pour savoir ce que chaque changement a produit.

---

## 📄 Licence

Ce projet est sous licence **AGPL-3.0** — voir [`LICENSE`](LICENSE). Il **dépend
de** Ultralytics YOLO11 (AGPL-3.0), que notre code importe directement ; c'est
cette relation d'œuvre combinée qui impose l'AGPL-3.0 à ce projet. L'utiliser
toi-même est gratuit ; l'intégrer dans un produit propriétaire/fermé requiert une
[licence Enterprise Ultralytics](https://www.ultralytics.com/license). supervision
(MIT), OpenCV (Apache-2.0/MIT), NumPy et PyTorch (BSD) sont sous licences
permissives et installés par l'utilisateur — ce dépôt ne les redistribue pas, ni
les poids du modèle. Voir [`NOTICE.md`](NOTICE.md) pour la liste complète des
licences tierces.
