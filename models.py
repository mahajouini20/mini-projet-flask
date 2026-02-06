"""
Modèles SQLAlchemy pour l'application de suivi des factures et commandes
Module: Développement Web avec Python - TP Noté
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
from time import time

db = SQLAlchemy()


class Role(db.Model):
    """Modèle pour les rôles utilisateur"""
    __tablename__ = 'role'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    
    # Relations
    users = db.relationship('User', backref='role', lazy=True)
    
    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):
    """Modèle pour les utilisateurs avec authentification"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    photo = db.Column(db.String(255), nullable=True)  # ✅ NOUVEAU CHAMP pour la photo de profil

    
    # Clé étrangère vers Role
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False, default=2)
    
    def set_password(self, password):
        """Hash le mot de passe"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=600):
        """Génère un token JWT pour réinitialiser le mot de passe (10 min par défaut)"""
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            'your-secret-key-change-in-production',  # À changer en production
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_password_token(token):
        """Vérifie le token de réinitialisation"""
        try:
            id = jwt.decode(
                token,
                'your-secret-key-change-in-production',
                algorithms=['HS256']
            )['reset_password']
        except:
            return None
        return User.query.get(id)
    
    def is_admin(self):
        """Vérifie si l'utilisateur est admin"""
        return self.role and self.role.name == 'Admin'
    
    def __repr__(self):
        return f'<User {self.username}>'


class Produit(db.Model):
    """Modèle pour la table Produit"""
    __tablename__ = 'produit'
    
    CodP = db.Column(db.Integer, primary_key=True)
    Lib = db.Column(db.String(100), nullable=False)
    PU = db.Column(db.Float, nullable=False)
    QteS = db.Column(db.Integer, nullable=False)
    Seuil = db.Column(db.Integer, nullable=False)
    photo = db.Column(db.String(255), nullable=True)  # Chemin vers la photo du produit
    
    # Relations
    pcs = db.relationship('PC', backref='produit', lazy=True)
    
    def __repr__(self):
        return f'<Produit {self.CodP}: {self.Lib}>'


class Client(db.Model):
    """Modèle pour la table Client"""
    __tablename__ = 'client'
    
    CodC = db.Column(db.Integer, primary_key=True)
    NomC = db.Column(db.String(100), nullable=False)
    CreditC = db.Column(db.Float, nullable=False)
    AdrC = db.Column(db.String(200), nullable=False)
    Email = db.Column(db.String(120), nullable=True)
    
    # Relations
    commandes = db.relationship('Commande', backref='client', lazy=True,cascade="all, delete-orphan" )
    factures = db.relationship('Facture', backref='client', lazy=True,cascade="all, delete-orphan" )
    
    def __repr__(self):
        return f'<Client {self.CodC}: {self.NomC}>'


class Commande(db.Model):
    """Modèle pour la table Commande"""
    __tablename__ = 'commande'
    
    NumC = db.Column(db.String(20), primary_key=True)
    DatC = db.Column(db.Date, nullable=False)
    CodC = db.Column(db.Integer, db.ForeignKey('client.CodC'), nullable=False)
    NumF = db.Column(db.Integer, db.ForeignKey('facture.NumF'), nullable=True)
    
    # Relations
    pcs = db.relationship('PC', backref='commande', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Commande {self.NumC}>'


class Facture(db.Model):
    """Modèle pour la table Facture"""
    __tablename__ = 'facture'
    
    NumF = db.Column(db.Integer, primary_key=True)
    MontF = db.Column(db.Float)
    DatF = db.Column(db.Date, nullable=False)
    CodC = db.Column(db.Integer, db.ForeignKey('client.CodC'), nullable=False)
    document_path = db.Column(db.String(255), nullable=True)  # Chemin vers le justificatif
    statut = db.Column(db.String(20), default='En attente')  # En attente, Payée, Annulée
    
    # Relations
    commandes = db.relationship('Commande', backref='facture', lazy=True)
    
    def __repr__(self):
        return f'<Facture {self.NumF}>'


class PC(db.Model):
    """Modèle pour la table PC (Produit-Commande) - Table d'association"""
    __tablename__ = 'pc'
    
    CodP = db.Column(db.Integer, db.ForeignKey('produit.CodP'), primary_key=True)
    NumC = db.Column(db.String(20), db.ForeignKey('commande.NumC'), primary_key=True)
    QteC = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f'<PC Produit:{self.CodP} Commande:{self.NumC} Qté:{self.QteC}>'