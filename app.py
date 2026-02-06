from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, send_from_directory, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import inspect
from werkzeug.utils import secure_filename
from functools import wraps
from forms import * 
from forms import EditProfileForm, ProfilePhotoForm, DeleteForm 
from sqlalchemy import func, desc
from datetime import datetime, timedelta,date
import os
import jwt

# Import des modèles et formulaires
from models import db, User, Role, Client, Commande, PC, Produit, Facture

# Configuration de l'application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre-cle-secrete-super-securisee-changez-moi'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:maha@localhost/commerce'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuration Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL', 'votre_email@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('PASSWORD', 'votre_mot_de_passe_app')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL', 'votre_email@gmail.com')

# Configuration Upload
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Extensions autorisées
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# Créer le dossier s’il n’existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialisation des extensions
db.init_app(app)
mail = Mail(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

# Configuration Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)


@login_manager.user_loader
def load_user(user_id):
    """Charge l'utilisateur depuis la base de données"""
    return User.query.get(int(user_id))


# ==================== DÉCORATEURS ====================

def admin_required(f):
    """Décorateur pour restreindre l'accès aux admins"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Accès refusé. Vous devez être administrateur.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def token_required(f):
    """Décorateur pour l'authentification JWT sur l'API"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token manquant!'}), 401
        
        try:
            # Enlever 'Bearer ' du token
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except:
            return jsonify({'message': 'Token invalide!'}), 401
        
        return f(*args, **kwargs)
    
    return decorated


# ==================== ROUTES D'AUTHENTIFICATION ====================

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
            return redirect(url_for('login'))
        
        if not user.is_active:
            flash('Votre compte a été désactivé. Contactez l\'administrateur.', 'warning')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        flash(f'Bienvenue {user.username}!', 'success')
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('dashboard')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def register():
    """Page d'inscription"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Créer le nouvel utilisateur
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role_id=2  # Role User par défaut
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Félicitations, vous êtes maintenant inscrit! Vous pouvez vous connecter.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('login'))


@app.route('/reset_password_request', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def reset_password_request():
    """Demande de réinitialisation de mot de passe"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            token = user.get_reset_password_token()
            send_password_reset_email(user, token)
        
        # Message identique même si l'email n'existe pas (sécurité)
        flash('Un email avec les instructions a été envoyé si l\'adresse existe.', 'info')
        return redirect(url_for('login'))
    
    return render_template('auth/reset_password_request.html', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Réinitialisation du mot de passe avec token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Token invalide ou expiré.', 'danger')
        return redirect(url_for('login'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Votre mot de passe a été réinitialisé.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/reset_password.html', form=form)


def send_password_reset_email(user, token):
    """Envoie l'email de réinitialisation"""
    reset_url = url_for('reset_password', token=token, _external=True)
    
    msg = Message(
        subject='Réinitialisation de votre mot de passe',
        recipients=[user.email],
        html=f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Réinitialisation de mot de passe</h2>
                <p>Bonjour {user.username},</p>
                <p>Pour réinitialiser votre mot de passe, cliquez sur le lien ci-dessous:</p>
                <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Réinitialiser mon mot de passe</a></p>
                <p>Ce lien expire dans 10 minutes.</p>
                <p>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.</p>
                <br>
                <p>Cordialement,<br>L'équipe</p>
            </body>
        </html>
        """
    )
    
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Erreur d'envoi d'email: {e}")


# ==================== ROUTES PRINCIPALES ====================
@app.route('/')
@login_required
def index():
    """Page d'accueil - Redirige selon le rôle"""
    if current_user.is_admin():
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('catalogue'))


@app.route("/dashboard")
@login_required
@admin_required
def dashboard():
    """Dashboard Admin automatique"""

    # ================== STATISTIQUES ==================

    total_clients = Client.query.count()
    total_produits = Produit.query.count()
    total_commandes = Commande.query.count()
    total_factures = Facture.query.count()

    # ================== CA TOTAL ==================

    ca_total = db.session.query(
        func.sum(Produit.PU * PC.QteC)
    ).join(PC, Produit.CodP == PC.CodP).scalar() or 0

    # ================== TOP 5 CLIENTS  ==================

    top_clients = db.session.query(
        Client.NomC,
        func.sum(Produit.PU * PC.QteC).label("ca")
    ).join(Commande, Client.CodC == Commande.CodC) \
     .join(PC, Commande.NumC == PC.NumC) \
     .join(Produit, Produit.CodP == PC.CodP) \
     .group_by(Client.NomC) \
     .order_by(desc("ca")) \
     .limit(5).all() 
    # ================== PRODUITS EN ALERTE ==================

    produits_alerte = Produit.query.filter(
        Produit.QteS <= Produit.Seuil
    ).all()

    # ================== FACTURES PAR STATUT ==================

    factures_en_attente = Facture.query.filter_by(statut="En attente").count()
    factures_payees = Facture.query.filter_by(statut="Payée").count()
    factures_annulees = Facture.query.filter_by(statut="Annulée").count()

    # ================== CA MENSUEL (12 DERNIERS MOIS) ==================

    ca_mensuel = []
    today = datetime.today()

    for i in range(11, -1, -1):
        debut = today - timedelta(days=(i + 1) * 30)
        fin = today - timedelta(days=i * 30)

        ca = db.session.query(
            func.sum(Produit.PU * PC.QteC)
        ).join(PC, Produit.CodP == PC.CodP) \
         .join(Commande, PC.NumC == Commande.NumC) \
         .filter(Commande.DatC.between(debut, fin)) \
         .scalar() or 0

        ca_mensuel.append({
            "mois": debut.strftime("%b %Y"),
            "ca": float(ca)
        })

    # ================== RENDER TEMPLATE ==================

    return render_template(
        "dashboard.html",
        total_clients=total_clients,
        total_produits=total_produits,
        total_commandes=total_commandes,
        total_factures=total_factures,
        ca_total=ca_total,
        top_clients=top_clients,
        produits_alerte=produits_alerte,
        factures_en_attente=factures_en_attente,
        factures_payees=factures_payees,
        factures_annulees=factures_annulees,
        ca_mensuel=ca_mensuel
    )



@app.route('/mon-profil')
@login_required
def mon_profil():
    """Afficher le profil de l'utilisateur"""
    form = EditProfileForm(
        original_username=current_user.username,
        original_email=current_user.email,
        obj=current_user
    )
    photo_form = ProfilePhotoForm()
    return render_template('profil.html', form=form, photo_form=photo_form)


# POUR MODIFIER LE PROFIL
@app.route('/modifier-profil', methods=['POST'])
@login_required
def modifier_profil():
    """Modifier les informations du profil"""
    form = EditProfileForm(
        original_username=current_user.username,
        original_email=current_user.email
    )
    
    if form.validate_on_submit():
        # Mise à jour des informations de base
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        
        # Changement de mot de passe si fourni
        if form.current_password.data and form.new_password.data:
            if current_user.check_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
                flash('Mot de passe modifié avec succès!', 'success')
            else:
                flash('Mot de passe actuel incorrect!', 'danger')
                return redirect(url_for('mon_profil'))
        
        db.session.commit()
        flash('Profil mis à jour avec succès!', 'success')
        return redirect(url_for('mon_profil'))
    
    # Afficher les erreurs
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('mon_profil'))


# POUR UPLOADER LA PHOTO
@app.route('/upload-photo-profil', methods=['POST'])
@login_required
def upload_photo_profil():
    """Uploader/Modifier la photo de profil"""
    form = ProfilePhotoForm()
    
    if form.validate_on_submit():
        file = form.photo.data
        
        if file and allowed_file(file.filename):
            # Supprimer l'ancienne photo si elle existe
            if current_user.photo:
                old_photo_path = os.path.join("static", current_user.photo)
                if os.path.exists(old_photo_path):
                    try:
                        os.remove(old_photo_path)
                    except Exception as e:
                        print(f"Erreur lors de la suppression de l'ancienne photo: {e}")
            
            # Générer un nom de fichier unique
            filename = secure_filename(file.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"profile_{current_user.id}_{timestamp}_{filename}"
            
            # Créer le dossier profiles s'il n'existe pas
            profile_folder = os.path.join(app.config["UPLOAD_FOLDER"], "profiles")
            os.makedirs(profile_folder, exist_ok=True)
            
            # Sauvegarder le fichier
            file_path = os.path.join(profile_folder, filename)
            file.save(file_path)
            
            # Mettre à jour la base de données
            current_user.photo = f"uploads/profiles/{filename}"
            db.session.commit()
            
            flash('Photo de profil mise à jour avec succès!', 'success')
        else:
            flash('Format de fichier non autorisé!', 'danger')
    
    return redirect(url_for('mon_profil'))



def add_photo_column():
    """Ajoute la colonne photo à la table User si elle n'existe pas"""
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        if 'photo' not in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE user ADD COLUMN photo VARCHAR(255)'))
                conn.commit()
            print("Colonne 'photo' ajoutée à la table User")
        else:
            print("Colonne 'photo' déjà présente")




@app.route('/totQteC_Client/<string:CodC_id>')
@login_required
def totQteC_Client(CodC_id):
    """Affiche les commandes d'un client"""
    client = Client.query.get_or_404(int(CodC_id))
    
    resultats = db.session.query(
        Produit.CodP,
        Produit.Lib,
        func.sum(PC.QteC).label('total_qte')
    ).join(
        PC, Produit.CodP == PC.CodP
    ).join(
        Commande, PC.NumC == Commande.NumC
    ).filter(
        Commande.CodC == int(CodC_id)
    ).group_by(
        Produit.CodP,
        Produit.Lib
    ).order_by(
        Produit.CodP
    ).all()
    
    details_commandes = db.session.query(
        Commande.NumC,
        Facture.NumF,
        PC.CodP,
        PC.QteC
    ).join(
        PC, Commande.NumC == PC.NumC
    ).join(
        Facture, Commande.NumF == Facture.NumF 
    ).filter(
        Commande.CodC == int(CodC_id)
    ).order_by(
        Commande.NumC,
        PC.CodP
    ).all()
    
    return render_template(
        'totQteC_Client.html',
        client=client,
        resultats=resultats,
        details=details_commandes
    )


@app.route('/facture/<int:NumF>')
@login_required
def detail_facture(NumF):
    """Affiche les détails d'une facture"""
    facture = Facture.query.get_or_404(NumF)
    client = Client.query.get(facture.CodC)
    commandes = Commande.query.filter_by(NumF=NumF).all()
    
    details_produits = db.session.query(
        Commande.NumC,
        Produit.CodP,
        Produit.Lib,
        Produit.PU,
        PC.QteC,
        (Produit.PU * PC.QteC).label('montant_ligne')
    ).join(
        PC, Commande.NumC == PC.NumC
    ).join(
        Produit, PC.CodP == Produit.CodP
    ).filter(
        Commande.NumF == NumF
    ).order_by(
        Commande.NumC,
        Produit.CodP
    ).all()
    
    montant_total = sum(detail.montant_ligne for detail in details_produits)
    
    return render_template(
        'detail_facture.html',
        facture=facture,
        client=client,
        commandes=commandes,
        details_produits=details_produits,
        montant_total=montant_total
    )


@app.route('/factures_client/<int:CodC>')
@login_required
def factures_client(CodC):
    """Affiche toutes les factures d'un client"""
    client = Client.query.get_or_404(CodC)
    
    factures_info = db.session.query(
        Facture.NumF,
        Facture.DatF,
        Facture.MontF,
        Facture.statut,
        func.count(Commande.NumC.distinct()).label('nb_commandes')
    ).outerjoin(
        Commande, Facture.NumF == Commande.NumF
    ).filter(
        Facture.CodC == CodC
    ).group_by(
        Facture.NumF,
        Facture.DatF,
        Facture.MontF,
        Facture.statut
    ).order_by(
        Facture.DatF.desc()
    ).all()
    
    factures_completes = []
    for facture_info in factures_info:
        montant_calcule = db.session.query(
            func.sum(Produit.PU * PC.QteC)
        ).join(
            PC, Produit.CodP == PC.CodP
        ).join(
            Commande, PC.NumC == Commande.NumC
        ).filter(
            Commande.NumF == facture_info.NumF
        ).scalar()
        
        factures_completes.append({
            'NumF': facture_info.NumF,
            'DatF': facture_info.DatF,
            'MontF': montant_calcule or 0,
            'statut': facture_info.statut,
            'nb_commandes': facture_info.nb_commandes
        })
    
    total_general = sum(f['MontF'] for f in factures_completes)
    
    return render_template(
        'factures_client.html',
        client=client,
        factures=factures_completes,
        total_general=total_general
    )


# ==================== API REST ====================

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def api_login():
    """API: Authentification et génération de token JWT"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Données manquantes'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Identifiants invalides'}), 401
    
    # Générer le token JWT
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.name
        }
    })


@app.route('/api/clients', methods=['GET'])
@token_required
def api_get_clients():
    """API: Liste tous les clients"""
    clients = Client.query.all()
    
    return jsonify({
        'clients': [{
            'CodC': c.CodC,
            'NomC': c.NomC,
            'AdrC': c.AdrC,
            'Email': c.Email,
            'CreditC': c.CreditC
        } for c in clients]
    })


@app.route('/api/clients/<int:CodC>', methods=['GET'])
@token_required
def api_get_client(CodC):
    """API: Détails d'un client"""
    client = Client.query.get_or_404(CodC)
    
    return jsonify({
        'CodC': client.CodC,
        'NomC': client.NomC,
        'AdrC': client.AdrC,
        'Email': client.Email,
        'CreditC': client.CreditC
    })


@app.route('/api/factures', methods=['GET'])
@token_required
def api_get_factures():
    """API: Liste toutes les factures"""
    factures = Facture.query.all()
    
    return jsonify({
        'factures': [{
            'NumF': f.NumF,
            'DatF': f.DatF.isoformat() if f.DatF else None,
            'MontF': f.MontF,
            'CodC': f.CodC,
            'statut': f.statut
        } for f in factures]
    })


@app.route('/api/factures/<int:NumF>', methods=['GET'])
@token_required
def api_get_facture(NumF):
    """API: Détails d'une facture"""
    facture = Facture.query.get_or_404(NumF)
    
    details = db.session.query(
        Commande.NumC,
        Produit.CodP,
        Produit.Lib,
        Produit.PU,
        PC.QteC,
        (Produit.PU * PC.QteC).label('montant')
    ).join(
        PC, Commande.NumC == PC.NumC
    ).join(
        Produit, PC.CodP == Produit.CodP
    ).filter(
        Commande.NumF == NumF
    ).all()
    
    return jsonify({
        'NumF': facture.NumF,
        'DatF': facture.DatF.isoformat() if facture.DatF else None,
        'MontF': facture.MontF,
        'CodC': facture.CodC,
        'statut': facture.statut,
        'details': [{
            'NumC': d.NumC,
            'CodP': d.CodP,
            'Lib': d.Lib,
            'PU': d.PU,
            'QteC': d.QteC,
            'montant': d.montant
        } for d in details]
    })


@app.route('/api/produits', methods=['GET'])
@token_required
def api_get_produits():
    """API: Liste tous les produits"""
    produits = Produit.query.all()
    
    return jsonify({
        'produits': [{
            'CodP': p.CodP,
            'Lib': p.Lib,
            'PU': p.PU,
            'QteS': p.QteS,
            'Seuil': p.Seuil,
            'photo': p.photo
        } for p in produits]
    })


@app.route('/api/stats', methods=['GET'])
@token_required
def api_get_stats():
    """API: Statistiques générales"""
    total_clients = Client.query.count()
    total_factures = Facture.query.count()
    total_commandes = Commande.query.count()
    
    ca_total = db.session.query(func.sum(Produit.PU * PC.QteC)).join(
        PC, Produit.CodP == PC.CodP
    ).scalar() or 0
    
    return jsonify({
        'total_clients': total_clients,
        'total_factures': total_factures,
        'total_commandes': total_commandes,
        'ca_total': float(ca_total)
    })


# ==================== GESTION ADMIN ====================

@app.route('/admin/produits')
@login_required
@admin_required
def admin_produits():
    """Liste des produits pour admin"""
    produits = Produit.query.all()
    return render_template('admin/produits.html', produits=produits)

#route pour l'affichage des clients 
@app.route('/admin/clients')
@login_required
@admin_required
def admin_clients():
    """Liste des clients pour admin"""
    clients = Client.query.all()
    return render_template('admin/clients.html', clients=clients)
#route pour ajouter un client 
@app.route('/admin/client/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_client():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            NomC=form.NomC.data,
            AdrC=form.AdrC.data,
            Email=form.Email.data,
            CreditC=form.CreditC.data
        )
        db.session.add(client)
        db.session.commit()
        flash(f'Client {client.NomC} ajouté avec succès!', 'success')
        return redirect(url_for('admin_clients'))
    return render_template('admin/client_form.html', form=form, title="Ajouter un fournisseur")
#route pour editer un client 
@app.route('/admin/client/<int:CodC>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_client(CodC):
    client = Client.query.get_or_404(CodC)
    form = ClientForm(obj=client)
    if form.validate_on_submit():
        client.NomC = form.NomC.data
        client.AdrC = form.AdrC.data
        client.Email = form.Email.data
        client.CreditC = form.CreditC.data
        db.session.commit()
        flash(f'Client {client.NomC} modifié avec succès!', 'success')
        return redirect(url_for('admin_clients'))
    return render_template('admin/client_form.html', form=form, title="Modifier Client")
#route pour supprimer un client
@app.route('/admin/client/<int:CodC>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_client(CodC):
    client = Client.query.get_or_404(CodC)
    try:
        db.session.delete(client)
        db.session.commit()
        flash(f'Client {client.NomC} supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'danger')
    return redirect(url_for('admin_clients'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Gestion des utilisateurs"""
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/user/<int:user_id>/toggle_active')
@login_required
@admin_required
def toggle_user_active(user_id):
    """Activer/Désactiver un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Vous ne pouvez pas vous désactiver vous-même!', 'warning')
        return redirect(url_for('admin_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "activé" if user.is_active else "désactivé"
    flash(f'L\'utilisateur {user.username} a été {status}.', 'success')
    return redirect(url_for('admin_users'))
# ==================== ROUTES GESTION UTILISATEURS - À AJOUTER DANS app.py ====================

@app.route('/admin/user/add', methods=['POST'])
@login_required
@admin_required
def admin_add_user():
    """Ajouter un nouvel utilisateur"""
    try:
        # Vérifier si l'username existe déjà
        if User.query.filter_by(username=request.form.get('username')).first():
            flash('Ce nom d\'utilisateur existe déjà!', 'danger')
            return redirect(url_for('admin_users'))
        
        # Vérifier si l'email existe déjà
        if User.query.filter_by(email=request.form.get('email')).first():
            flash('Cet email est déjà utilisé!', 'danger')
            return redirect(url_for('admin_users'))
        
        # Créer le nouvel utilisateur
        user = User(
            username=request.form.get('username'),
            email=request.form.get('email'),
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            role_id=int(request.form.get('role_id', 2)),
            is_active=bool(request.form.get('is_active'))
        )
        user.set_password(request.form.get('password'))
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Utilisateur {user.username} créé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la création: {str(e)}', 'danger')
    
    return redirect(url_for('admin_users'))


@app.route('/admin/user/<int:user_id>/details')
@login_required
@admin_required
def admin_user_details(user_id):
    """Récupérer les détails d'un utilisateur (API JSON)"""
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'photo': user.photo,
        'role': user.role.name,
        'role_id': user.role_id,
        'is_active': user.is_active,
        'created_at': user.created_at.strftime('%d/%m/%Y %H:%M') if user.created_at else None,
        'last_login': user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else None
    })


@app.route('/admin/user/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    """Modifier un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    try:
        # Vérifier l'unicité du username
        username = request.form.get('username')
        if username != user.username:
            if User.query.filter_by(username=username).first():
                flash('Ce nom d\'utilisateur existe déjà!', 'danger')
                return redirect(url_for('admin_users'))
        
        # Vérifier l'unicité de l'email
        email = request.form.get('email')
        if email != user.email:
            if User.query.filter_by(email=email).first():
                flash('Cet email est déjà utilisé!', 'danger')
                return redirect(url_for('admin_users'))
        
        # Mettre à jour les informations
        user.username = username
        user.email = email
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.role_id = int(request.form.get('role_id', 2))
        user.is_active = bool(request.form.get('is_active'))
        
        db.session.commit()
        
        flash(f'Utilisateur {user.username} modifié avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la modification: {str(e)}', 'danger')
    
    return redirect(url_for('admin_users'))


@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Supprimer un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    # Empêcher la suppression de son propre compte
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte!', 'danger')
        return redirect(url_for('admin_users'))
    
    try:
        # Supprimer la photo si elle existe
        if user.photo:
            photo_path = os.path.join("static", user.photo)
            if os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except Exception as e:
                    print(f"Erreur suppression photo: {e}")
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        flash(f'Utilisateur {username} supprimé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'danger')
    
    return redirect(url_for('admin_users'))


# ==================== FIN DES ROUTES UTILISATEURS ====================
@app.route('/admin/commandes')
@login_required
@admin_required
def admin_commandes():
    """Liste de toutes les commandes pour l'admin"""
    commandes = db.session.query(
        Commande.NumC,
        Commande.DatC,
        Commande.CodC,
        Commande.NumF,
        Client.NomC
    ).join(
        Client, Commande.CodC == Client.CodC
    ).order_by(
        Commande.DatC.desc()
    ).all()
    
    # Calculer le total pour chaque commande
    commandes_data = []
    for cmd in commandes:
        total = db.session.query(func.sum(Produit.PU * PC.QteC)).join(
            PC, Produit.CodP == PC.CodP
        ).filter(
            PC.NumC == cmd.NumC
        ).scalar() or 0
        
        commandes_data.append({
            'NumC': cmd.NumC,
            'DatC': cmd.DatC,
            'CodC': cmd.CodC,
            'NomC': cmd.NomC,
            'NumF': cmd.NumF,
            'total': total
        })
    delete_form = DeleteForm()  # initialise par défaut
    if request.method == "POST":
        if delete_form.validate_on_submit():
        # traitement de suppression
            flash("Commande supprimée", "success")
            return redirect(url_for("admin_commandes"))

    return render_template('admin/commandes.html', commandes=commandes_data, delete_form=delete_form)
    

@app.route('/admin/commande/<string:NumC>')
@login_required
@admin_required
def admin_detail_commande(NumC):
    """Affiche les détails d'une commande pour l'admin"""
    commande = Commande.query.get_or_404(NumC)
    client = Client.query.get(commande.CodC)
    
    # Récupérer les détails des produits
    details = db.session.query(
        Produit.CodP,
        Produit.Lib,
        Produit.PU,
        Produit.photo,
        PC.QteC,
        (Produit.PU * PC.QteC).label('montant_ligne')
    ).join(
        PC, Produit.CodP == PC.CodP
    ).filter(
        PC.NumC == NumC
    ).all()
    
    # Calculer le montant total
    montant_total = sum(detail.montant_ligne for detail in details)
    
    return render_template(
        'admin/detail_commande.html',
        commande=commande,
        client=client,
        details=details,
        montant_total=montant_total
    )


@app.route('/admin/commande/<string:NumC>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_commande(NumC):
    """Supprimer une commande"""
    form = DeleteForm()
    if form.validate_on_submit():
        
        commande = Commande.query.get_or_404(NumC)
        db.session.delete(commande)
        db.session.commit()

        flash("Commande supprimée avec succès", "success")

    else:
        flash("Erreur CSRF : token invalide", "danger")

    return redirect(url_for("admin_commandes"))



@app.route('/admin/factures')
@login_required
@admin_required
def admin_factures():
    """Liste de toutes les factures pour l'admin"""
    factures = db.session.query(
        Facture.NumF,
        Facture.DatF,
        Facture.MontF,
        Facture.statut,
        Facture.CodC,
        Client.NomC
    ).join(
        Client, Facture.CodC == Client.CodC
    ).order_by(
        Facture.DatF.desc()
    ).all()
    
    # Calculer montants si nécessaire
    factures_data = []
    for f in factures:
        if f.MontF:
            montant = f.MontF
        else:
            montant = db.session.query(func.sum(Produit.PU * PC.QteC)).join(
                PC, Produit.CodP == PC.CodP
            ).join(
                Commande, PC.NumC == Commande.NumC
            ).filter(
                Commande.NumF == f.NumF
            ).scalar() or 0
        
        factures_data.append({
            'NumF': f.NumF,
            'DatF': f.DatF,
            'montant': montant,
            'statut': f.statut,
            'CodC': f.CodC,
            'NomC': f.NomC
        })
    
    return render_template('admin/factures.html', factures=factures_data)

# ==================== INITIALISATION ====================

def init_roles():
    """Initialise les rôles par défaut"""
    if Role.query.count() == 0:
        admin_role = Role(name='Admin', description='Administrateur système')
        user_role = Role(name='User', description='Utilisateur standard')
        
        db.session.add(admin_role)
        db.session.add(user_role)
        db.session.commit()
        
        print("Rôles créés: Admin, User")


def create_admin_user():
    """Crée un utilisateur admin par défaut"""
    if User.query.filter_by(username='admin').first() is None:
        admin_role = Role.query.filter_by(name='Admin').first()
        
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='System',
            role_id=admin_role.id
        )
        admin.set_password('admin123')  # À changer en production!
        
        db.session.add(admin)
        db.session.commit()
        
        print("Utilisateur admin créé: admin / admin123")
def allowed_file(filename):
    """Vérifie si l'extension est autorisée"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/admin/produit/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_new_produit():
    """Ajouter un nouveau produit avec photo optionnelle"""
    form = EditProductForm()

    if form.validate_on_submit():

        filename = None

        # Vérifier si une photo est uploadée
        if form.photo.data:
            file = form.photo.data

            if allowed_file(file.filename):
                filename = secure_filename(file.filename)

                # Chemin complet
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

                # Sauvegarde
                file.save(file_path)
            else:
                flash("Format d'image non autorisé !", "danger")
                return redirect(request.url)

        # Créer le produit
        nouveau_produit = Produit(
            Lib=form.Lib.data,
            PU=form.PU.data,
            QteS=form.QteS.data,
            Seuil=form.Seuil.data,
            photo="uploads/" + filename if filename else None
        )

        db.session.add(nouveau_produit)
        db.session.commit()

        flash("Produit ajouté avec succès !", "success")
        return redirect(url_for('admin_produits'))

    return render_template("admin/new_produit.html", form=form)
@app.route("/admin/produit/<int:codp>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit_produit(codp):
    produit = Produit.query.get_or_404(codp)
    form = EditProductForm(obj=produit)

    if form.validate_on_submit():
        produit.Lib = form.Lib.data
        produit.PU = form.PU.data
        produit.QteS = form.QteS.data
        produit.Seuil = form.Seuil.data

        db.session.commit()
        flash("Produit modifié avec succès !", "success")
        return redirect(url_for("admin_produits"))

    return render_template("admin/edit_produit.html", form=form, produit=produit)
@app.route("/admin/produit/<int:codp>/upload", methods=["GET", "POST"])
@login_required
@admin_required
def admin_upload_photo(codp):
    produit = Produit.query.get_or_404(codp)
    form = ProductUploadForm()

    if form.validate_on_submit():
        file = form.photo.data

        if file:
            filename = secure_filename(file.filename)
            filename = datetime.utcnow().strftime("%Y%m%d%H%M%S_") + filename

            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            produit.photo = "uploads/" + filename
            db.session.commit()

            flash("Photo mise à jour avec succès !", "success")
            return redirect(url_for("admin_produits"))

    return render_template("admin/upload_photo.html", form=form, produit=produit)
@app.route("/admin/produit/<int:codp>/delete")
@login_required
@admin_required
def admin_delete_produit(codp):
    produit = Produit.query.get_or_404(codp)

    # Supprimer aussi la photo si existe
    if produit.photo:
        photo_path = os.path.join("static", produit.photo)
        if os.path.exists(photo_path):
            os.remove(photo_path)

    db.session.delete(produit)
    db.session.commit()

    flash("Produit supprimé avec succès !", "success")
    return redirect(url_for("admin_produits"))

# ==================== CATALOGUE ET PANIER ====================

@app.route('/catalogue')
@login_required
def catalogue():
    """Catalogue de produits pour tous les utilisateurs"""
    produits = Produit.query.filter(Produit.QteS > 0).all()  # Seulement produits en stock
    return render_template('catalogue.html', produits=produits)


@app.route('/ajouter_panier', methods=['POST'])
@login_required
def ajouter_panier():
    """Ajouter un produit au panier"""
    produit_id = request.form.get('produit_id', type=int)
    quantite = request.form.get('quantite', 1, type=int)
    
    produit = Produit.query.get_or_404(produit_id)
    
    # Vérifier stock disponible
    if quantite > produit.QteS:
        flash(f'Stock insuffisant. Seulement {produit.QteS} disponible(s).', 'warning')
        return redirect(url_for('catalogue'))
    
    # Initialiser le panier dans la session si nécessaire
    if 'panier' not in session:
        session['panier'] = []
    
    # Vérifier si le produit est déjà dans le panier
    panier = session['panier']
    produit_existe = False
    
    for item in panier:
        if item['produit_id'] == produit_id:
            item['quantite'] += quantite
            produit_existe = True
            break
    
    if not produit_existe:
        panier.append({
            'produit_id': produit_id,
            'quantite': quantite
        })
    
    session['panier'] = panier
    session.modified = True
    
    flash(f'{produit.Lib} ajouté au panier!', 'success')
    return redirect(url_for('catalogue'))


@app.route('/panier')
@login_required
def voir_panier():
    """Afficher le panier"""
    panier_session = session.get('panier', [])
    panier_details = []
    total = 0
    
    for item in panier_session:
        produit = Produit.query.get(item['produit_id'])
        if produit:
            panier_details.append({
                'produit': produit,
                'quantite': item['quantite']
            })
            total += produit.PU * item['quantite']
    
    return render_template('panier.html', panier=panier_details, total=total)


@app.route('/modifier_quantite_panier', methods=['POST'])
@login_required
def modifier_quantite_panier():
    """Modifier la quantité d'un produit dans le panier"""
    produit_id = request.form.get('produit_id', type=int)
    action = request.form.get('action')
    
    panier = session.get('panier', [])
    
    for item in panier:
        if item['produit_id'] == produit_id:
            if action == 'increase':
                produit = Produit.query.get(produit_id)
                if item['quantite'] < produit.QteS:
                    item['quantite'] += 1
                else:
                    flash('Stock insuffisant', 'warning')
            elif action == 'decrease':
                if item['quantite'] > 1:
                    item['quantite'] -= 1
            break
    
    session['panier'] = panier
    session.modified = True
    
    return redirect(url_for('voir_panier'))


@app.route('/retirer_panier', methods=['POST'])
@login_required
def retirer_panier():
    """Retirer un produit du panier"""
    produit_id = request.form.get('produit_id', type=int)
    
    panier = session.get('panier', [])
    panier = [item for item in panier if item['produit_id'] != produit_id]
    
    session['panier'] = panier
    session.modified = True
    
    flash('Produit retiré du panier', 'info')
    return redirect(url_for('voir_panier'))

@app.route('/valider_commande', methods=['POST'])
@login_required
def valider_commande():
    panier = session.get('panier', [])

    if not panier:
        flash('Votre panier est vide', 'warning')
        return redirect(url_for('catalogue'))

    try:
        # 1. Récupérer ou créer client
        client = Client.query.filter_by(Email=current_user.email).first()

        if not client:
            client = Client(
                NomC=f"{current_user.first_name} {current_user.last_name}"
                if current_user.first_name else current_user.username,
                CreditC=100000,
                AdrC="Adresse à compléter",
                Email=current_user.email
            )
            db.session.add(client)
            db.session.flush()

        # 2. Créer facture
        facture = Facture(
            DatF=date.today(),
            CodC=client.CodC,
            statut="En attente"
        )
        db.session.add(facture)
        db.session.flush()   # للحصول على NumF

        # 3. ✅ Créer commande avec NumC court
        num_commande = f"c{facture.NumF}"

        commande = Commande(
            NumC=num_commande,
            DatC=date.today(),
            CodC=client.CodC,
            NumF=facture.NumF
        )
        db.session.add(commande)
        db.session.flush()

        # 4. Ajouter produits dans PC + mise à jour stock
        montant_total = 0

        for item in panier:
            produit = Produit.query.get(item['produit_id'])

            if produit.QteS < item['quantite']:
                raise Exception(f"Stock insuffisant pour {produit.Lib}")

            # Table PC
            pc = PC(
                CodP=produit.CodP,
                NumC=num_commande,
                QteC=item['quantite']
            )
            db.session.add(pc)

            # Mise à jour stock
            produit.QteS -= item['quantite']

            # Total facture
            montant_total += produit.PU * item['quantite']

        # 5. Mettre à jour montant facture
        facture.MontF = montant_total

        # 6. Commit transaction
        db.session.commit()

        # 7. Vider panier
        session.pop('panier', None)

        flash(f"Commande validée avec succès ! NumC = {num_commande}", "success")
        return redirect(url_for("detail_facture", NumF=facture.NumF))

    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la validation : {str(e)}", "danger")
        return redirect(url_for("voir_panier"))

@app.route('/mes_commandes')
@login_required
def mes_commandes():
    """Afficher les commandes de l'utilisateur connecté"""
    # Récupérer le client associé à l'utilisateur
    client = Client.query.filter_by(Email=current_user.email).first()
    
    if not client:
        return render_template('mes_commandes.html', commandes=[])
    
    # Récupérer toutes les commandes du client
    commandes_data = []
    commandes = Commande.query.filter_by(CodC=client.CodC).order_by(Commande.DatC.desc()).all()
    
    for commande in commandes:
        # Récupérer les détails des produits
        details = db.session.query(
            PC.QteC,
            Produit
        ).join(
            Produit, PC.CodP == Produit.CodP
        ).filter(
            PC.NumC == commande.NumC
        ).all()
        
        # Calculer le total
        total = sum(d.Produit.PU * d.QteC for d in details)
        
        commandes_data.append({
            'NumC': commande.NumC,
            'DatC': commande.DatC,
            'NumF': commande.NumF,
            'details': [{'produit': d.Produit, 'quantite': d.QteC} for d in details],
            'total': total
        })
    
    return render_template('mes_commandes.html', commandes=commandes_data)


@app.route('/mes_factures')
@login_required
def mes_factures():
    """Afficher les factures de l'utilisateur connecté"""
    # Récupérer le client associé à l'utilisateur
    client = Client.query.filter_by(Email=current_user.email).first()
    
    if not client:
        return render_template('mes_factures.html', factures=[], total_general=0)
    
    # Récupérer toutes les factures du client
    factures = Facture.query.filter_by(CodC=client.CodC).order_by(Facture.DatF.desc()).all()
    
    # Calculer les montants si nécessaire
    factures_data = []
    total_general = 0
    
    for facture in factures:
        if facture.MontF:
            montant = facture.MontF
        else:
            # Calculer le montant si pas renseigné
            montant = db.session.query(func.sum(Produit.PU * PC.QteC)).join(
                PC, Produit.CodP == PC.CodP
            ).join(
                Commande, PC.NumC == Commande.NumC
            ).filter(
                Commande.NumF == facture.NumF
            ).scalar() or 0
        
        factures_data.append({
            'NumF': facture.NumF,
            'DatF': facture.DatF,
            'montant': montant,
            'statut': facture.statut
        })
        
        total_general += montant
    
    return render_template('mes_factures.html', factures=factures_data, total_general=total_general)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_roles()
        create_admin_user()
        add_photo_column()  
        print("Base de données initialisée!")
    
    app.run(debug=True, port=5000)