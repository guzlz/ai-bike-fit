# How to film your bike-fit clip / Comment filmer ta vidéo de bike fit

The analysis is only as good as the clip. A bad video doesn't give a "bad fit" —
it gives *wrong numbers*. Read this before you film.

L'analyse ne vaut que ce que vaut la vidéo. Une mauvaise vidéo ne donne pas un
"mauvais réglage" — elle donne des *chiffres faux*. Lis ça avant de filmer.

---

## ✅ The checklist / La checklist

| # | 🇬🇧 English | 🇫🇷 Français |
|---|---|---|
| 1 | **Landscape (horizontal), never portrait.** Turn the phone sideways. Portrait crops the bike and wastes pixels on the ceiling. | **Paysage (horizontal), jamais portrait.** Tourne le téléphone sur le côté. Le portrait coupe le vélo et gâche des pixels sur le plafond. |
| 2 | **Full side-on.** Camera exactly at the side of the bike, lens square to it — not in front, behind, or at an angle. You should see the WHOLE bike and your whole body. | **Plein profil.** Caméra exactement sur le côté, objectif perpendiculaire — ni devant, ni derrière, ni en biais. On doit voir TOUT le vélo et tout ton corps. |
| 3 | **Camera at hip/crank height.** Put the phone on a tripod, chair or box at the height of your hip. Filming from standing height (looking down) distorts every angle. | **Caméra à hauteur de hanche/pédalier.** Pose le téléphone sur un trépied, une chaise ou un carton à hauteur de hanche. Filmer depuis debout (en plongée) fausse tous les angles. |
| 4 | **Distance: 2.5–4 m.** Far enough that the whole bike + body fit with a little margin, close enough to stay sharp. Zoom with your feet, not the digital zoom. | **Distance : 2,5–4 m.** Assez loin pour que tout le vélo + le corps tiennent avec une marge, assez près pour rester net. Recule/avance à pied, n'utilise pas le zoom numérique. |
| 5 | **Resolution 1080p or higher, 30–60 fps.** More pixels = the model pins your knee and ankle precisely. Avoid heavy compression (see the WhatsApp warning below). | **Résolution 1080p ou plus, 30–60 fps.** Plus de pixels = le modèle situe précisément genou et cheville. Évite la compression forte (voir l'avertissement WhatsApp ci-dessous). |
| 6 | **Good, even light.** Bright room or daylight. Light on YOU, not behind you (no backlight/window behind). Less motion blur on the feet = better read. | **Bonne lumière, homogène.** Pièce claire ou lumière du jour. La lumière sur TOI, pas derrière (pas de contre-jour/fenêtre dans le dos). Moins de flou sur les pieds = meilleure lecture. |
| 7 | **Nothing blocking the near leg/arm.** Move the fan, bottles, bags, the dog — anything between the camera and your camera-side leg and arm. | **Rien ne cache la jambe/le bras proches.** Écarte ventilateur, bidons, sacs, le chien — tout ce qui est entre la caméra et ta jambe/ton bras côté caméra. |
| 8 | **Trainer is ideal.** You stay in one spot. Pedal steady 20–30 s at an easy effort and your normal cadence. | **Le home-trainer est idéal.** Tu restes au même endroit. Pédale régulièrement 20–30 s à effort facile et ta cadence normale. |
| 9 | **Ride your normal position.** Hands where you actually ride (hoods for most), the whole clip. Don't "pose" — film how you really sit. | **Roule dans ta position habituelle.** Mains là où tu roules vraiment (cocottes pour la plupart), toute la vidéo. Ne "pose" pas — filme comment tu es vraiment. |
| 10 | **Trim to the pedaling part.** Cut the getting-on/off, or use `--start` / `--end`. Mounting frames confuse the bottom-dead-center detection. | **Coupe pour ne garder que le pédalage.** Enlève la montée/descente, ou utilise `--start` / `--end`. Les images de montée perturbent la détection du point mort bas. |

---

## 📐 The 3 geometry rules that make or break it / Les 3 règles de géométrie décisives

If the camera position is wrong, the tool measures the **far** leg (partly hidden
by the frame, distorted by parallax) or gets every angle skewed. Get these three
right above all else.

**Si la position de la caméra est mauvaise, l'outil mesure la jambe ÉLOIGNÉE
(cachée en partie par le cadre, déformée par la parallaxe) ou fausse tous les
angles. Ces trois-là priment sur tout.**

### 1. 📏 Distance: 2.5–4 m / Distance : 2,5–4 m
- 🇬🇧 Stand back so the **whole bike + your whole body** fit the frame with a
  hand's width of margin all around. Too close = parts cut off and lens distortion;
  too far = you're tiny and the joints get imprecise. Move your feet, **never** use
  digital zoom.
- 🇫🇷 Recule pour que **tout le vélo + tout ton corps** tiennent dans le cadre avec
  une marge d'une main tout autour. Trop près = membres coupés et distorsion
  d'objectif ; trop loin = tu es minuscule et les articulations imprécises.
  Déplace-toi à pied, **jamais** de zoom numérique.

### 2. 🎯 Angle: perfectly square (90°) to the bike / Angle : parfaitement perpendiculaire (90°)
- 🇬🇧 The lens must point **straight at the bike's side**, at the level of the
  cranks — not from the front 3/4, not from behind, not tilted. A good check: the
  two wheels should look like **circles of the same size** and overlap as one; if
  the far wheel looks smaller or you see a lot of the front of the bike, you're at
  an angle. This is what puts the skeleton on the wrong (far) leg.
- 🇫🇷 L'objectif doit viser **droit sur le flanc du vélo**, au niveau du pédalier —
  pas de 3/4 avant, pas de derrière, pas incliné. Vérif simple : les deux roues
  doivent apparaître comme **deux cercles de même taille** qui se superposent ; si
  la roue éloignée paraît plus petite ou que tu vois beaucoup l'avant du vélo, tu
  es en biais. C'est ça qui met le squelette sur la mauvaise jambe (l'éloignée).

### 3. 📷 Height: lens at hip / crank height / Hauteur : objectif à hauteur de hanche / pédalier
- 🇬🇧 Put the phone on a tripod, chair, stack of books or box so the **lens sits at
  the height of your hip or the bottom bracket** — roughly 60–80 cm off the floor
  for most setups. Filming from standing height (looking down) foreshortens your
  torso and makes your position read far more aggressive than it is. Keep the phone
  **dead level** (use the phone's grid/level).
- 🇫🇷 Pose le téléphone sur un trépied, une chaise, une pile de livres ou un carton
  pour que **l'objectif soit à hauteur de ta hanche ou du pédalier** — environ
  60–80 cm du sol dans la plupart des cas. Filmer depuis debout (en plongée) écrase
  ton torse et fait paraître ta position bien plus agressive qu'elle n'est. Garde le
  téléphone **parfaitement de niveau** (utilise la grille/le niveau du téléphone).

> 💡 **The tool now warns you** if it can't tell your near leg from your far leg
> (a sign the camera wasn't square/at the right height). If you see that warning in
> the report, re-shoot with rules 1–3 above.
> **L'outil t'avertit maintenant** s'il n'arrive pas à distinguer ta jambe proche
> de ta jambe éloignée (signe d'une caméra mal placée). Si tu vois cet
> avertissement dans le rapport, refilme en appliquant les règles 1 à 3.

---

## ⚠️ Don't send it through WhatsApp / N'envoie pas via WhatsApp

WhatsApp (and many messaging apps) re-compress video hard and often force it to a
low, vertical resolution. That's exactly the wrong input. **Transfer the original
file** — AirDrop, USB cable, Google Drive/Dropbox "original quality", or email the
file as an attachment (not "share to WhatsApp").

WhatsApp (et beaucoup de messageries) recompressent la vidéo fortement et la
forcent souvent en résolution basse et verticale. C'est exactement le mauvais
format. **Transfère le fichier original** — AirDrop, câble USB, Google
Drive/Dropbox en "qualité d'origine", ou envoie le fichier en pièce jointe par
email (pas "partager vers WhatsApp").

---

## Why it matters (the honest version) / Pourquoi ça compte (la version honnête)

- **Joint angles are ratios, so they barely depend on camera distance** — 2.5 m or
  4 m gives the same knee angle. Distance mainly matters for keeping the whole body
  sharp and in frame, and (later) for any pixels→mm conversion.
- **Portrait + heavy compression is the real killer.** Fewer pixels on your leg
  means the model's knee/ankle points wobble by several pixels, which is several
  degrees of error — enough to flip a green into an amber.
- **Height and angle of the camera DO bias angles.** A camera looking down from
  standing height foreshortens the torso and makes the fit look more aggressive
  than it is. Hip height, dead level, square to the side. Non-negotiable.

- **Les angles articulaires sont des rapports : ils dépendent à peine de la
  distance** — 2,5 m ou 4 m donne le même angle de genou. La distance sert surtout
  à garder tout le corps net et cadré, et (plus tard) à toute conversion pixels→mm.
- **Le portrait + la compression forte, voilà le vrai tueur.** Moins de pixels sur
  ta jambe = les points genou/cheville du modèle bougent de plusieurs pixels, soit
  plusieurs degrés d'erreur — assez pour faire basculer un vert en orange.
- **La hauteur et l'angle de la caméra, EUX, biaisent les angles.** Une caméra en
  plongée depuis debout écrase le torse et fait paraître la position plus agressive
  qu'elle n'est. Hauteur de hanche, parfaitement de niveau, perpendiculaire au
  profil. Non négociable.
