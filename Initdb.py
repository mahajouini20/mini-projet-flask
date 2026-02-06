from app import app, db
from models import Client, Commande, Facture, Produit, PC, User, Role
from datetime import datetime


def init_database():
    
    with app.app_context():
        # Supprimer toutes les tables existantes
        db.drop_all()
        
        # Créer toutes les tables
        db.create_all()
        
        print("Tables créées avec succès!")
        
        # Insertion des Clients
        clients = [
            Client(CodC=1000, NomC='Slim', CreditC=120000, AdrC='Kef', Email='slim@example.com'),
            Client(CodC=1200, NomC='Sami', CreditC=50000, AdrC='Monastir', Email='sami@example.com'),
            Client(CodC=1210, NomC='Fatma', CreditC=20000, AdrC='Sfax', Email='fatma@example.com'),
            Client(CodC=1250, NomC='Mohamed', CreditC=50000, AdrC='Tunis', Email='mohamed@example.com'),
            Client(CodC=1360, NomC='Ali', CreditC=400000, AdrC='Sousse', Email='ali@example.com'),
            Client(CodC=1400, NomC='Mahmoud', CreditC=200000, AdrC='Zagouan', Email='mahmoud@example.com'),
            Client(CodC=1580, NomC='Adel', CreditC=250000, AdrC='Adel', Email='adel@example.com'),
        ]
        
        for client in clients:
            db.session.add(client)
        
        print("Clients insérés!")
        
        # Insertion des Produits
        produits = [
            Produit(CodP=2, Lib='Ecran', PU=400000, QteS=15, Seuil=5),
            Produit(CodP=3, Lib='CD-ROM', PU=150000, QteS=20, Seuil=3),
            Produit(CodP=5, Lib='Clavier', PU=25000, QteS=40, Seuil=10),
            Produit(CodP=9, Lib='Souris', PU=5000, QteS=100, Seuil=20),
            Produit(CodP=10, Lib='Imprimante', PU=500000, QteS=50, Seuil=8),
        ]
        
        for produit in produits:
            db.session.add(produit)
        
        print("Produits insérés!")
        
        # Insertion des Factures (AVANT les commandes car Commande référence Facture)
        factures = [
            Facture(NumF=10, CodC=1250, DatF=datetime(2024, 7, 16), MontF=None),
            Facture(NumF=40, CodC=1200, DatF=datetime(2024, 8, 17), MontF=None),
            Facture(NumF=50, CodC=1400, DatF=datetime(2024, 9, 14), MontF=None),
            Facture(NumF=100, CodC=1400, DatF=datetime(2024, 10, 22), MontF=None),
            Facture(NumF=220, CodC=1210, DatF=datetime(2024, 11, 12), MontF=None),
            Facture(NumF=300, CodC=1250, DatF=datetime(2024, 11, 23), MontF=None),
        ]
        
        for facture in factures:
            db.session.add(facture)
        
        print("Factures insérées!")
        
        # Insertion des Commandes
        commandes = [
            Commande(NumC='c10', CodC=1250, DatC=datetime(2024, 9, 15), NumF=10),
            Commande(NumC='c40', CodC=1200, DatC=datetime(2022, 8, 7), NumF=40),
            Commande(NumC='c200', CodC=1250, DatC=datetime(2025, 11, 10), NumF=300),
            Commande(NumC='c50', CodC=1400, DatC=datetime(2023, 9, 12), NumF=50),
            Commande(NumC='c100', CodC=1400, DatC=datetime(2024, 10, 20), NumF=100),
            Commande(NumC='c220', CodC=1210, DatC=datetime(2023, 11, 10), NumF=220),
            Commande(NumC='c300', CodC=1250, DatC=datetime(2024, 11, 25), NumF=300),
        ]
        
        for commande in commandes:
            db.session.add(commande)
        
        print("Commandes insérées!")
        
        # Insertion des PC (Produit-Commande)
        pcs = [
            PC(CodP=2, NumC='c10', QteC=200),
            PC(CodP=2, NumC='c220', QteC=100),
            PC(CodP=2, NumC='c200', QteC=120),
            PC(CodP=3, NumC='c40', QteC=300),
            PC(CodP=3, NumC='c50', QteC=40),
            PC(CodP=5, NumC='c10', QteC=100),
            PC(CodP=5, NumC='c300', QteC=70),
            PC(CodP=9, NumC='c10', QteC=300),
            PC(CodP=9, NumC='c40', QteC=500),
            PC(CodP=10, NumC='c40', QteC=100),
            PC(CodP=10, NumC='c100', QteC=100),
            PC(CodP=10, NumC='c300', QteC=100),
        ]
        
        for pc in pcs:
            db.session.add(pc)
        
        print("Relations PC insérées!")
        print("Relations PC insérées!")
        
        # Création des rôles
        admin_role = Role(id=1, name='Admin', description='Administrateur système')
        user_role = Role(id=2, name='User', description='Utilisateur standard')
        
        db.session.add(admin_role)
        db.session.add(user_role)
        
        print("Rôles créés!")
        
        # Création de l'utilisateur admin
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='System',
            role_id=1
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        
        print("Utilisateur admin créé!")
      
        
        
        # Validation de la transaction
        db.session.commit()
        
        print("\n✓ Base de données initialisée avec succès!")
        print(f"✓ {len(clients)} clients insérés")
        print(f"✓ {len(produits)} produits insérés")
        print(f"✓ {len(commandes)} commandes insérées")
        print(f"✓ {len(factures)} factures insérées")
        print(f"✓ {len(pcs)} relations produit-commande insérées")


if __name__ == '__main__':
    init_database()