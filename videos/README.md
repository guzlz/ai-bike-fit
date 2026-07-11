# 📁 Put your video here / Mets ta vidéo ici

Drop your side-on pedaling clip in **this folder**, then run the analyzer with its
filename. Your videos stay on your machine — this folder is git-ignored, nothing
here gets pushed to GitHub.

Dépose ta vidéo de pédalage **de profil** dans **ce dossier**, puis lance
l'analyse avec son nom de fichier. Tes vidéos restent sur ta machine — ce dossier
est ignoré par git, rien ici n'est envoyé sur GitHub.

---

### Example / Exemple

1. Copy your clip here and rename it something simple, e.g. `my-ride.mp4`
   *(Copie ta vidéo ici et renomme-la simplement, ex. `ma-video.mp4`)*

2. From the project root, run / Depuis la racine du projet, lance :

   ```bash
   uv run python analyze_bikefit.py --input videos/my-ride.mp4 --out out_fit
   ```

3. Results land in `out_fit/` / Les résultats arrivent dans `out_fit/`
   (`overlay_h264.mp4`, `report.md`, `stills/`).

Supported formats / Formats acceptés: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`.
