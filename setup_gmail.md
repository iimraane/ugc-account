# Configuration API Gmail pour UGC Helper

L'outil **UGC Helper** utilise l'API Gmail pour surveiller ta boîte mail (et tes spams) et extraire automatiquement le lien d'activation envoyé par UGC.

Voici les étapes pour configurer cela (1 seule fois) :

## Étape 1 : Obtenir le `credentials.json`

Puisque tu as déjà un projet Google Cloud pour `subscription-helper`, tu peux le réutiliser, ou en créer un nouveau.

1. Rends-toi sur la [Console Google Cloud - Credentials](https://console.cloud.google.com/apis/credentials).
2. Vérifie que tu es sur le bon projet (en haut à gauche).
3. Clique sur **"+ CRÉER DES IDENTIFIANTS"** (Create Credentials) > **ID client OAuth** (OAuth client ID).
4. Sélectionnez le type d'application : **"Application de bureau"** (Desktop app).
5. Nomme-la par exemple "UGC Helper" et clique sur **Créer**.
6. Une modale s'affiche. Clique sur le bouton **"TÉLÉCHARGER LE FICHIER JSON"** (Download JSON).
7. Renomme ce fichier en `credentials.json`.
8. Place ce fichier `credentials.json` dans le même dossier que `helper.py` (c'est-à-dire dans `c:\Users\windos 10\Desktop\Ugc-account\`).

## Étape 2 : Activer l'API (Si ce n'est pas déjà fait)

1. Rends-toi sur [Vues d'ensemble des API](https://console.cloud.google.com/apis/library/gmail.googleapis.com).
2. Assure-toi que l'API Gmail est **Activée** (Enabled).

## Étape 3 : Lancement

1. Ouvre ton terminal / ligne de commande.
2. Installe les dépendances :
   ```bash
   pip install -r requirements-helper.txt
   ```
3. Lance l'outil :
   ```bash
   python helper.py
   ```
4. **La première fois**, une fenêtre de ton navigateur va s'ouvrir te demandant de te connecter à ton compte Google et d'autoriser l'application. 
   - Accepte les permissions (c'est ton propre projet donc c'est sécurisé).
   - Un fichier `token.json` sera généré automatiquement. Tu n'auras plus besoin de te reconnecter les prochaines fois !

---

*Note: Lors de la création d'un compte sur le site UGC, l'outil va automatiquement interroger Gmail toutes les 10 secondes. Dès que le mail d'activation est reçu, le bouton s'allumera en rose, clignotera, et te permettra d'ouvrir le lien directement.*
