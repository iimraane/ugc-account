# UGC Helper 🎬

Assistant de bureau pour créer des comptes UGC manuellement, plus vite.

## Ce que ça fait

Une petite fenêtre flottante qui reste au premier plan pendant que tu navigues sur ugc.fr :

- **📋 Copier Email** — copie le prochain email disponible dans le presse-papier
- **📋 Copier MDP** — copie un mot de passe sécurisé généré automatiquement
- **🔗 Lien UGC** — surveille Gmail et détecte automatiquement le lien d'activation UGC dès qu'il arrive (même dans les spams)
- **✅ Suivant** — sauvegarde le compte dans `resultats.txt` et passe au suivant

## Installation

```bash
pip install -r requirements.txt
```

## Configuration Gmail

Voir [setup_gmail.md](setup_gmail.md) pour les instructions de configuration de l'API Gmail (1 seule fois).

## Lancement

```bash
python helper.py
```

## Fichiers

| Fichier | Rôle |
|---------|------|
| `helper.py` | Application principale |
| `emails.txt` | Liste d'emails (1 par ligne, max 50 chars) |
| `resultats.txt` | Comptes créés (`email:password`) |
| `credentials.json` | Credentials OAuth Google (voir setup) |
| `token.json` | Token auto-généré au premier lancement |
| `setup_gmail.md` | Guide de configuration Gmail API |
# ugc-account
