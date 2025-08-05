# 🔧 GUIDE DE RÉSOLUTION - ERREUR 401 (Clé API invalide)

## 🚨 Problème
Vous rencontrez l'erreur : **"Erreur IA : Erreur lors de l'analyse IA: Erreur API: 401"**

Cette erreur indique que la clé API OpenAI utilisée est invalide, expirée ou que vous n'avez pas de crédits disponibles.

## 🔍 DIAGNOSTIC RAPIDE

### 1. Vérifiez votre clé API
```bash
# Testez votre clé API directement
python test_api_key.py sk-votre-cle-api-ici
```

### 2. Vérifiez les sources de clé API
L'application cherche la clé API dans cet ordre :
1. **Clé personnelle** (si configurée dans votre profil)
2. **Variable d'environnement** `OPENAI_API_KEY`
3. **Fichier** `static/openai_key.txt`

## 🛠️ SOLUTIONS

### Solution 1 : Vérifier et corriger la clé API

#### A. Vérifiez votre clé sur OpenAI
1. Allez sur https://platform.openai.com/api-keys
2. Vérifiez que votre clé est active
3. Créez une nouvelle clé si nécessaire

#### B. Vérifiez votre facturation
1. Allez sur https://platform.openai.com/account/billing
2. Vérifiez que vous avez des crédits disponibles
3. Ajoutez une méthode de paiement si nécessaire

### Solution 2 : Configurer la clé dans l'application

#### Option A : Interface utilisateur (Recommandé)
1. Connectez-vous à l'application
2. Allez dans **Profil** > **Configuration API**
3. Sélectionnez "API personnelle"
4. Entrez votre clé API (commence par `sk-`)
5. Cliquez sur "Sauvegarder"

#### Option B : Variable d'environnement
```bash
# Dans votre terminal
export OPENAI_API_KEY="sk-votre-cle-api-ici"

# Ou ajoutez dans votre fichier .env
echo "OPENAI_API_KEY=sk-votre-cle-api-ici" >> .env
```

#### Option C : Fichier de configuration
```bash
# Créez ou modifiez le fichier
echo "sk-votre-cle-api-ici" > static/openai_key.txt
```

### Solution 3 : Redémarrer l'application
```bash
# Arrêtez l'application
# Puis redémarrez
docker-compose down
docker-compose up -d
```

## 🔧 AMÉLIORATIONS APPLIQUÉES

J'ai amélioré la gestion des erreurs pour vous donner des messages plus clairs :

### Messages d'erreur améliorés :
- **Erreur 401** : "Clé API invalide ou expirée. Veuillez vérifier votre clé API dans les paramètres."
- **Erreur 429** : "Limite de taux dépassée. Veuillez réessayer dans quelques minutes."
- **Erreur 500** : "Erreur serveur OpenAI. Veuillez réessayer plus tard."

### Validation améliorée :
- Vérification du format de la clé API
- Messages d'erreur détaillés
- Logging amélioré pour le débogage

## 📝 VÉRIFICATION

### Testez votre configuration :
```bash
# Diagnostic complet
python diagnose_api_key_issue.py

# Test rapide d'une clé
python test_api_key.py sk-votre-cle-api-ici
```

### Vérifiez les logs :
```bash
# Consultez les logs de l'application
docker-compose logs web
```

## 🆘 SI LE PROBLÈME PERSISTE

### 1. Vérifiez les logs détaillés
Les logs contiennent maintenant plus d'informations sur les erreurs API.

### 2. Testez avec curl
```bash
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-votre-cle-api-ici" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Test"}],
    "max_tokens": 10
  }'
```

### 3. Vérifiez votre compte OpenAI
- Clé API active et valide
- Crédits disponibles
- Pas de restrictions géographiques
- Compte en bon état

## 📞 SUPPORT

Si le problème persiste après avoir essayé toutes ces solutions :

1. Vérifiez les logs de l'application
2. Testez votre clé API directement avec le script fourni
3. Vérifiez votre compte OpenAI
4. Contactez le support si nécessaire

---

**Note** : Les améliorations apportées au code permettent maintenant de mieux identifier et résoudre les problèmes de clé API. Les messages d'erreur sont plus informatifs et la validation est plus robuste. 