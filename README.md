# 🛒 E-Commerce Flask - Système de Gestion Complet

## 📸  Vidéo de démonstration

[Regarder la vidéo](https://drive.google.com/file/d/1wCnikBYAiIEOVwsTS-dm6ClXCH-TbBFJ/view?usp=sharing)


Système complet de gestion e-commerce développé avec Flask, incluant la gestion des produits, commandes, factures, utilisateurs et profils avec photos.

---

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Technologies utilisées](#-technologies-utilisées)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Structure du projet](#-structure-du-projet)
- [Utilisation](#-utilisation)
- [API REST](#-api-rest)
- [Captures d'écran](#-captures-décran)
## ✨ Fonctionnalités

### 🔐 Authentification & Sécurité
- ✅ Système d'authentification complet (inscription, connexion, déconnexion)
- ✅ Gestion des rôles (Administrateur, Client)
- ✅ Réinitialisation du mot de passe par email
- ✅ Protection CSRF sur tous les formulaires
- ✅ Rate limiting sur les routes sensibles
- ✅ Hachage sécurisé des mots de passe (Werkzeug)
- ✅ Tokens JWT pour l'API REST

### 👤 Gestion des Profils
- ✅ Page de profil personnalisée
- ✅ Upload de photo de profil
- ✅ Modification des informations personnelles
- ✅ Changement de mot de passe
- ✅ Affichage de la photo dans le menu

### 👥 Gestion des Utilisateurs (Admin)
- ✅ Liste complète avec statistiques
- ✅ Ajout d'utilisateur avec formulaire modal
- ✅ Modification des informations
- ✅ Activation/Désactivation de comptes
- ✅ Suppression d'utilisateur
- ✅ Recherche en temps réel
- ✅ Affichage des photos de profil

### 📦 Gestion des Produits (Admin)
- ✅ Liste des produits avec photos
- ✅ Ajout de produit avec upload d'image
- ✅ Modification des informations
- ✅ Gestion du stock et seuils d'alerte
- ✅ Suppression de produit
- ✅ Indicateurs de stock faible

### 🛍️ Catalogue & Panier (Client)
- ✅ Catalogue de produits avec filtres
- ✅ Ajout au panier
- ✅ Modification des quantités
- ✅ Validation de commande
- ✅ Vérification du stock en temps réel
- ✅ Badge de nombre d'articles dans le panier

### 📋 Gestion des Commandes
- ✅ Liste des commandes (Admin)
- ✅ Détails complets d'une commande
- ✅ Historique des commandes (Client)
- ✅ Calcul automatique des montants
- ✅ Suppression de commande (Admin)
- ✅ Recherche et filtrage

### 🧾 Gestion des Factures
- ✅ Génération automatique de factures
- ✅ Liste des factures avec statuts
- ✅ Détails de facture avec produits
- ✅ Historique par client
- ✅ Calcul du CA total
- ✅ Statistiques financières

### 👨‍💼 Gestion des Clients (Admin)
- ✅ Liste des clients
- ✅ Historique des commandes par client
- ✅ Total des achats par client
- ✅ Informations de contact

### 📊 Dashboard Administrateur
- ✅ Statistiques en temps réel
  - Total clients, produits, commandes, factures
  - Chiffre d'affaires total
- ✅ Top 5 clients
- ✅ Produits en alerte de stock
- ✅ Factures par statut
- ✅ Graphique CA mensuel (12 derniers mois)
- ✅ Charts interactifs (Chart.js)

### 🔌 API REST
- ✅ Authentification JWT
- ✅ Endpoints pour clients, produits, commandes, factures
- ✅ Format JSON
- ✅ Documentation des endpoints

---

## 🛠️ Technologies utilisées

### Backend
- **Python 3.8+** - Langage de programmation
- **Flask 3.0+** - Framework web
- **Flask-Login** - Gestion des sessions utilisateur
- **Flask-Mail** - Envoi d'emails
- **Flask-WTF** - Gestion des formulaires
- **Flask-Limiter** - Rate limiting
- **SQLAlchemy** - ORM pour la base de données
- **PyMySQL** - Connecteur MySQL
- **Werkzeug** - Sécurité et utilitaires
- **PyJWT** - Tokens d'authentification

### Frontend
- **Bootstrap 5.3** - Framework CSS
- **Font Awesome 6.4** - Icônes
- **Chart.js 4.4** - Graphiques
- **JavaScript Vanilla** - Interactivité

### Base de données
- **MySQL 8.0+** - Système de gestion de base de données

---

## 📦 Prérequis

Avant de commencer, assurez-vous d'avoir installé :

- **Python 3.8 ou supérieur**
  ```bash
  python --version
  ```

- **MySQL 8.0 ou supérieur**
  ```bash
  mysql --version
  ```

- **pip** (gestionnaire de paquets Python)
  ```bash
  pip --version
  ```

---

## 🚀 Installation

### 1. Cloner le projet

```bash
git clone https://github.com/votre-username/ecommerce-flask.git
cd ecommerce-flask
```

### 2. Créer un environnement virtuel

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

**Contenu de `requirements.txt`:**
```
Flask==3.0.0
Flask-Login==0.6.3
Flask-Mail==0.9.1
Flask-WTF==1.2.1
Flask-Limiter==3.5.0
SQLAlchemy==2.0.23
PyMySQL==1.1.0
Werkzeug==3.0.1
PyJWT==2.8.0
email-validator==2.1.0
cryptography==41.0.7
```

### 4. Créer la base de données MySQL

```sql
-- Se connecter à MySQL
mysql -u root -p

-- Créer la base de données
CREATE DATABASE commerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Créer un utilisateur (optionnel)
CREATE USER 'ecommerce_user'@'localhost' IDENTIFIED BY 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON commerce.* TO 'ecommerce_user'@'localhost';
FLUSH PRIVILEGES;

-- Quitter MySQL
EXIT;
```

### 5. Configurer l'application

Modifiez `app.py` avec vos paramètres :

```python
# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:votre_mdp@localhost/commerce'

# Configuration email (optionnel)
app.config['MAIL_USERNAME'] = 'votre_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'votre_mot_de_passe_app'
app.config['MAIL_DEFAULT_SENDER'] = 'votre_email@gmail.com'

# Clé secrète (CHANGEZ-LA !)
app.config['SECRET_KEY'] = 'votre-cle-secrete-super-securisee-changez-moi'
```

### 6. Initialiser la base de données

```bash
python app.py
```

Au premier lancement, l'application va :
- ✅ Créer toutes les tables
- ✅ Créer les rôles (Admin, User)
- ✅ Créer un utilisateur admin par défaut

**Identifiants par défaut:**
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANT:** Changez ce mot de passe immédiatement !

### 7. Créer les dossiers nécessaires

```bash
mkdir -p static/uploads/profiles
mkdir -p static/uploads/produits
```

**Windows:**
```bash
mkdir static\uploads\profiles
mkdir static\uploads\produits
```

---

## ⚙️ Configuration

### Configuration Email (optionnel)

Pour activer la réinitialisation de mot de passe par email :

1. **Activez l'accès "Applications moins sécurisées" sur Gmail**
   OU
2. **Créez un mot de passe d'application:**
   - Allez sur https://myaccount.google.com/security
   - Activez la validation en deux étapes
   - Générez un mot de passe d'application
   - Utilisez ce mot de passe dans `app.py`

### Variables d'environnement (recommandé)

Créez un fichier `.env` :

```env
SECRET_KEY=votre-cle-secrete-ultra-securisee
DATABASE_URI=mysql+pymysql://root:password@localhost/commerce
MAIL_USERNAME=votre_email@gmail.com
MAIL_PASSWORD=votre_mot_de_passe_app
MAIL_DEFAULT_SENDER=votre_email@gmail.com
```

Puis modifiez `app.py` :

```python
import os
from dotenv import load_dotenv

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
# etc...
```

---

## 📁 Structure du projet

```
ecommerce-flask/
│
├── app.py                      # Application principale Flask
├── models.py                   # Modèles SQLAlchemy
├── forms.py                    # Formulaires WTForms
├── requirements.txt            # Dépendances Python
├── README.md                   # Ce fichier
│
├── templates/                  # Templates Jinja2
│   ├── base.html              # Template de base
│   ├── auth/                  # Templates d'authentification
│   │   ├── login.html
│   │   ├── register.html
│   │   └── reset_password.html
│   ├── admin/                 # Templates admin
│   │   ├── dashboard.html
│   │   ├── clients.html
│   │   ├── produits.html
│   │   ├── commandes.html
│   │   ├── detail_commande.html
│   │   ├── factures.html
│   │   └── users.html
│   ├── catalogue.html         # Catalogue produits
│   ├── panier.html           # Panier
│   ├── mes_commandes.html    # Historique commandes client
│   ├── mes_factures.html     # Historique factures client
│   ├── profil.html           # Page de profil
│   ├── detail_facture.html   # Détails d'une facture
│   └── factures_client.html  # Factures d'un client
│
└── static/                    # Fichiers statiques
    ├── uploads/              # Fichiers uploadés
    │   ├── profiles/        # Photos de profil
    │   └── produits/        # Photos de produits
    └── images/              # Images du site
```

---

## 💻 Utilisation

### Démarrer l'application

```bash
python app.py
```

L'application sera accessible sur : **http://127.0.0.1:5000**

### Comptes par défaut

**Administrateur:**
- Username: `admin`
- Password: `admin123`

**Créer un compte client:**
- Utilisez le formulaire d'inscription
- OU créez-le depuis l'interface admin

### Flux d'utilisation

#### En tant qu'Admin:

1. **Connexion** → Dashboard
2. **Gestion des produits** → Ajouter/Modifier/Supprimer
3. **Gestion des utilisateurs** → Créer/Modifier/Activer
4. **Voir les commandes** → Détails/Factures
5. **Statistiques** → Dashboard avec graphiques

#### En tant que Client:

1. **Connexion/Inscription**
2. **Parcourir le catalogue**
3. **Ajouter au panier**
4. **Valider la commande**
5. **Consulter mes commandes/factures**
6. **Gérer mon profil**

---

## 🔌 API REST

### Authentification

**Obtenir un token JWT:**

```bash
POST /api/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Réponse:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "Admin"
  }
}
```



## 🔒 Sécurité

### Mesures de sécurité implémentées:

- ✅ **Protection CSRF** sur tous les formulaires
- ✅ **Hachage des mots de passe** (Werkzeug)
- ✅ **Rate limiting** (5 tentatives de connexion/minute)
- ✅ **Validation des données** côté serveur
- ✅ **Tokens JWT** pour l'API
- ✅ **Protection contre les injections SQL** (SQLAlchemy ORM)
- ✅ **Validation des uploads** (types de fichiers, taille)
- ✅ **Sessions sécurisées** (Flask-Login)
- ✅ **Mots de passe forts** (minimum 6 caractères)

</div>



