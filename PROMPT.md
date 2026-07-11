# The Claude Code prompt — choose your language / choisis ta langue

> **Paste this into Claude Code, not a regular Claude chat.** This guide installs
> software and runs commands on your computer, which a normal chat window cannot do.
> **À coller dans Claude Code, pas dans un chat Claude classique.** Ce guide installe
> des logiciels et lance des commandes sur ton ordinateur, ce qu'un chat classique
> ne peut pas faire.

**Pick your language — the prompt tells Claude which language to answer in.
Choisis ta langue — le prompt indique à Claude dans quelle langue répondre.**

- 🇬🇧 **English** → [jump to the English prompt](#-english)
- 🇫🇷 **Français** → [aller au prompt français](#-français)

---

## 🇬🇧 English

You do not download anything, make any folders, or write any code. Claude Code
does all of it. Open Claude Code, paste the prompt below, send it, and it walks
you through the whole thing one step at a time. The only thing you provide is your
video.

### Starting from scratch (build everything)

```text
Answer me in English throughout.

I want to grade my own road bike fit from a phone video, and I'm starting from
scratch. I don't want to download anything, create folders, or write code myself.
You do all of it. Walk me through it one step at a time in plain English, and stop
and wait for me whenever you need something.

The goal: I'll give you a short SIDE-ON video of me pedaling on my bike (on a
trainer). You measure my body angles at the bottom of the pedal stroke, tell me
what's dialed and what to change (mainly saddle height and reach), and draw a
colored skeleton on the video so I can see it: green = good, orange = borderline,
red = fix.

Here is everything I need you to do, end to end. Do it all yourself:

1. Make a folder (something like "bike-fit") and work inside it. I shouldn't have
   to create it myself.
2. Check whether I already have Python; if not, help me install it. Then install
   the exact open-source libraries this is built on, and read their current docs
   before you write code so you use the right API:
   - ultralytics (the YOLO11 pose model that finds my body joints) -
     https://github.com/ultralytics/ultralytics, docs at https://docs.ultralytics.com.
     Note it is AGPL-3.0 licensed. Install with: pip install ultralytics
   - supervision by Roboflow (helper for reading video frames and drawing) -
     https://github.com/roboflow/supervision. MIT licensed. pip install supervision
   - opencv-python and numpy for the image handling and math.
   Install PyTorch too: if I have an NVIDIA GPU use the CUDA build, otherwise the
   normal CPU build is fine (a short clip runs on CPU, just slower). Make sure
   ffmpeg is available.
3. Build a bike-fit analyzer script. It should:
   - Read a SIDE-ON video and run YOLO11x-pose on each frame (load it with
     YOLO('yolo11x-pose.pt') from ultralytics - use the large 'x' model, because
     the small one can't find the joints accurately through pedaling motion blur).
     For each frame it returns 17 body keypoints per person in COCO order
     (shoulders, elbows, wrists, hips, knees, ankles, etc.), each with an x,y
     pixel position and a confidence. Pick the highest-confidence person, take my
     near-side (camera-side) shoulder, elbow, wrist, hip, knee and ankle, and
     ignore low-confidence points. Angles are just geometry on those points (the
     knee angle is the angle between the hip->knee and ankle->knee lines).
   - Find bottom-dead-center (BDC = the bottom of the pedal stroke, where the
     knee is most extended), but ONLY during real pedaling - ignore me mounting,
     standing next to the bike, or coasting. Measure the median across several
     strokes so one blurry frame can't skew the result.
   - Measure these angles at BDC and grade each green / amber / red against these
     research-backed dynamic road ranges (allow a ~2.5 degree tolerance at the
     edges, since a phone video only resolves to a few degrees):
       - Knee flexion at the bottom: green 30-40 deg. Over ~42 = saddle too low
         (raise it); under ~28 = saddle too high (lower it).
       - Torso from horizontal: green 40-50 deg.
       - Elbow bend: green 15-30 deg.
       - Shoulder angle (torso to upper arm): green ~80-95 deg. Much lower means
         a closed, scrunched cockpit (reach too short or too much weight on the
         hands).
       - Hip angle at the top: ~85-110 deg (report only, flexibility dependent).
   - These ranges are grounded in the bike-fit literature, not made up. Ground your
     grading in these sources, and read them if you can so the numbers are current:
       - The Holmes method (the clinical standard for the knee angle at the bottom
         of the stroke), and joint-angle averages (knee 36 +/- 7 deg, elbow 19 +/- 8
         deg): https://pmc.ncbi.nlm.nih.gov/articles/PMC9219349/
       - A dynamic-vs-static validity study showing angles measured while pedaling
         on video run ~8 deg higher than static goniometer numbers (this is why the
         knee zone is a dynamic 30-40, not the static 25-35):
         https://pubmed.ncbi.nlm.nih.gov/24499342/
       - Practitioner cross-check for the full joint set (torso, shoulder, hip):
         https://www.bikefitadviser.com/blog/not-basic-bike-fit-part-3-bike-fit-joint-angles
   - Draw the colored skeleton on the whole clip, coloring the arm by the worse
     of shoulder/elbow so a closed cockpit actually shows. Save the BDC still.
   - Write a short report with the exact fix, e.g. "knee 45 deg at the bottom ->
     saddle too low, raise ~10mm."
   - Re-encode the overlay to H.264 so it plays on any phone or computer.
4. Ask me for my video file when you're ready. Run it, show me the overlay and the
   report, and explain my results in plain English - what's dialed and what to
   change first.

Go one step at a time. Don't dump everything at once, and don't make me touch any
files or code myself. When you need me to approve a command, just ask and I'll say
yes.
```

### Already cloned this repo? (analyzer already written)

```text
Answer me in English throughout.

This repo is an AI bike-fit tool. Set it up for me (install dependencies with uv or
pip, and ffmpeg if it's missing), then run analyze_bikefit.py on the video I'm about
to give you and explain the report in plain English - what's dialed and what to
change first (mainly saddle height and reach).
```

Or run it yourself — see the [README](README.md#-the-manual-way--run-it-yourself).

---

## 🇫🇷 Français

Tu ne télécharges rien, ne crées aucun dossier, n'écris aucun code. Claude Code
fait tout. Ouvre Claude Code, colle le prompt ci-dessous, envoie-le, et il te
guide pas à pas dans toute la procédure. La seule chose que tu fournis, c'est ta
vidéo.

### Partir de zéro (tout construire)

```text
Réponds-moi en français tout du long.

Je veux noter mon propre réglage de vélo de route (bike fit) à partir d'une vidéo
prise au téléphone, et je pars de zéro. Je ne veux rien télécharger, créer aucun
dossier, ni écrire de code moi-même. Tu fais tout. Guide-moi une étape à la fois
en langage simple, et arrête-toi pour m'attendre chaque fois que tu as besoin de
quelque chose.

Le but : je te donnerai une courte vidéo de PROFIL de moi en train de pédaler sur
mon vélo (sur home-trainer). Tu mesures mes angles corporels au bas du coup de
pédale, tu me dis ce qui est bien réglé et ce qu'il faut changer (surtout hauteur
de selle et allonge), et tu dessines un squelette coloré sur la vidéo pour que je
le voie : vert = bon, orange = limite, rouge = à corriger.

Voici tout ce que je te demande de faire, de bout en bout. Fais tout toi-même :

1. Crée un dossier (par exemple "bike-fit") et travaille dedans. Je ne devrais pas
   avoir à le créer moi-même.
2. Vérifie si j'ai déjà Python ; sinon, aide-moi à l'installer. Puis installe les
   bibliothèques open-source exactes sur lesquelles c'est construit, et lis leur
   documentation à jour avant d'écrire du code pour utiliser la bonne API :
   - ultralytics (le modèle de pose YOLO11 qui trouve mes articulations) -
     https://github.com/ultralytics/ultralytics, docs sur https://docs.ultralytics.com.
     Note : licence AGPL-3.0. Installe avec : pip install ultralytics
   - supervision par Roboflow (aide pour lire les images vidéo et dessiner) -
     https://github.com/roboflow/supervision. Licence MIT. pip install supervision
   - opencv-python et numpy pour le traitement d'image et les calculs.
   Installe aussi PyTorch : si j'ai un GPU NVIDIA utilise la build CUDA, sinon la
   build CPU normale suffit (une courte vidéo tourne sur CPU, juste plus lentement).
   Assure-toi que ffmpeg est disponible.
3. Construis un script d'analyse de bike fit. Il doit :
   - Lire une vidéo de PROFIL et exécuter YOLO11x-pose sur chaque image (charge-le
     avec YOLO('yolo11x-pose.pt') depuis ultralytics - utilise le grand modèle 'x',
     car le petit ne trouve pas les articulations avec assez de précision dans le
     flou de mouvement du pédalage). Pour chaque image il renvoie 17 points-clés du
     corps par personne dans l'ordre COCO (épaules, coudes, poignets, hanches,
     genoux, chevilles, etc.), chacun avec une position x,y en pixels et une
     confiance. Prends la personne la plus confiante, prends mon épaule, coude,
     poignet, hanche, genou et cheville du côté proche (côté caméra), et ignore les
     points peu confiants. Les angles sont de la simple géométrie sur ces points
     (l'angle du genou est l'angle entre les segments hanche->genou et cheville->genou).
   - Trouve le point mort bas (PMB = le bas du coup de pédale, où le genou est le
     plus tendu), mais UNIQUEMENT pendant un vrai pédalage - ignore-moi quand je
     monte sur le vélo, me tiens à côté, ou roue libre. Mesure la médiane sur
     plusieurs coups de pédale pour qu'une image floue ne fausse pas le résultat.
   - Mesure ces angles au PMB et note chacun vert / orange / rouge contre ces
     plages route dynamiques issues de la recherche (tolère ~2,5 degrés aux bords,
     car une vidéo de téléphone ne résout qu'à quelques degrés près) :
       - Flexion du genou en bas : vert 30-40 deg. Au-dessus de ~42 = selle trop
         basse (la remonter) ; en dessous de ~28 = selle trop haute (la baisser).
       - Torse par rapport à l'horizontale : vert 40-50 deg.
       - Flexion du coude : vert 15-30 deg.
       - Angle d'épaule (torse vers bras) : vert ~80-95 deg. Beaucoup plus bas =
         poste de pilotage fermé et tassé (allonge trop courte ou trop de poids sur
         les mains).
       - Angle de hanche en haut : ~85-110 deg (informatif seulement, dépend de la
         souplesse).
   - Ces plages sont fondées sur la littérature du bike fit, pas inventées. Fonde
     ta notation sur ces sources, et lis-les si tu peux pour que les nombres soient
     à jour :
       - La méthode Holmes (standard clinique pour l'angle du genou au bas du coup
         de pédale), et les moyennes d'angles articulaires (genou 36 +/- 7 deg,
         coude 19 +/- 8 deg) : https://pmc.ncbi.nlm.nih.gov/articles/PMC9219349/
       - Une étude de validité dynamique-vs-statique montrant que les angles mesurés
         en pédalant sur vidéo sont ~8 deg plus élevés que les mesures statiques au
         goniomètre (c'est pourquoi la zone genou est un 30-40 dynamique, pas le
         25-35 statique) : https://pubmed.ncbi.nlm.nih.gov/24499342/
       - Recoupement praticien pour l'ensemble des articulations (torse, épaule,
         hanche) : https://www.bikefitadviser.com/blog/not-basic-bike-fit-part-3-bike-fit-joint-angles
   - Dessine le squelette coloré sur toute la vidéo, en colorant le bras selon le
     pire de l'épaule/du coude pour qu'un poste fermé ressorte vraiment. Sauvegarde
     l'image du PMB.
   - Écris un court rapport avec la correction exacte, par ex. "genou 45 deg en bas
     -> selle trop basse, remonter d'environ 10 mm".
   - Ré-encode la vidéo annotée en H.264 pour qu'elle se lise sur n'importe quel
     téléphone ou ordinateur.
4. Demande-moi mon fichier vidéo quand tu es prêt. Lance l'analyse, montre-moi la
   vidéo annotée et le rapport, et explique-moi mes résultats en langage simple -
   ce qui est bien réglé et quoi changer en premier.

Va une étape à la fois. Ne déballe pas tout d'un coup, et ne me fais toucher aucun
fichier ni code moi-même. Quand tu as besoin que j'approuve une commande, demande
simplement et je dirai oui.
```

### Tu as déjà cloné ce dépôt ? (le script d'analyse existe déjà)

```text
Réponds-moi en français tout du long.

Ce dépôt est un outil de bike fit par IA. Installe-le pour moi (les dépendances
avec uv ou pip, et ffmpeg s'il manque), puis lance analyze_bikefit.py sur la vidéo
que je vais te donner et explique-moi le rapport en langage simple - ce qui est
bien réglé et quoi changer en premier (surtout hauteur de selle et allonge).
```

Ou lance-le toi-même — voir le [README français](README.fr.md#-la-méthode-manuelle--lance-le-toi-même).
