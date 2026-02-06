"""
Formulaires Flask-WTF pour l'application
Module: Développement Web avec Python - Mini-Projet
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional
from models import User


class LoginForm(FlaskForm):
    """Formulaire de connexion"""
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')


class RegistrationForm(FlaskForm):
    """Formulaire d'inscription"""
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(),
        Length(min=3, max=80, message='Le nom d\'utilisateur doit contenir entre 3 et 80 caractères')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Prénom', validators=[Length(max=100)])
    last_name = StringField('Nom', validators=[Length(max=100)])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(),
        Length(min=6, message='Le mot de passe doit contenir au moins 6 caractères')
    ])
    password2 = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(),
        EqualTo('password', message='Les mots de passe doivent correspondre')
    ])
    submit = SubmitField('S\'inscrire')
    
    def validate_username(self, username):
        """Vérifie que le nom d'utilisateur n'existe pas déjà"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Ce nom d\'utilisateur est déjà utilisé. Veuillez en choisir un autre.')
    
    def validate_email(self, email):
        """Vérifie que l'email n'existe pas déjà"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Cet email est déjà utilisé. Veuillez en choisir un autre.')


class ResetPasswordRequestForm(FlaskForm):
    """Formulaire de demande de réinitialisation de mot de passe"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Demander la réinitialisation')


class ResetPasswordForm(FlaskForm):
    """Formulaire de réinitialisation de mot de passe"""
    password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(),
        Length(min=6, message='Le mot de passe doit contenir au moins 6 caractères')
    ])
    password2 = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(),
        EqualTo('password', message='Les mots de passe doivent correspondre')
    ])
    submit = SubmitField('Réinitialiser le mot de passe')


class ProductUploadForm(FlaskForm):
    """Formulaire d'upload de photo produit"""
    photo = FileField('Photo du produit', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images seulement!')
    ])
    submit = SubmitField('Télécharger')


class FactureUploadForm(FlaskForm):
    """Formulaire d'upload de justificatif facture"""
    document = FileField('Justificatif (PDF, Image)', validators=[
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'PDF ou images seulement!')
    ])
    submit = SubmitField('Télécharger')


class EditProductForm(FlaskForm):
    """Formulaire d'édition de produit"""
    Lib = StringField('Libellé', validators=[DataRequired(), Length(max=100)])
    PU = FloatField('Prix Unitaire', validators=[DataRequired()])
    QteS = IntegerField('Quantité en Stock', validators=[DataRequired()])
    Seuil = IntegerField('Seuil d\'alerte', validators=[DataRequired()])
    photo = FileField('Photo', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images seulement!')
    ])
    submit = SubmitField('Enregistrer')


class ClientForm(FlaskForm):
    """Formulaire d'édition de client"""
    NomC = StringField('Nom', validators=[DataRequired(), Length(max=100)])
    AdrC = StringField('Adresse', validators=[DataRequired(), Length(max=200)])
    Email = StringField('Email', validators=[Optional(), Email()])
    CreditC = FloatField('Crédit', validators=[DataRequired()])
    submit = SubmitField('Enregistrer')


class ChangePasswordForm(FlaskForm):
    """Formulaire de changement de mot de passe"""
    old_password = PasswordField('Mot de passe actuel', validators=[DataRequired()])
    new_password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(),
        Length(min=6, message='Le mot de passe doit contenir au moins 6 caractères')
    ])
    new_password2 = PasswordField('Confirmer le nouveau mot de passe', validators=[
        DataRequired(),
        EqualTo('new_password', message='Les mots de passe doivent correspondre')
    ])
    submit = SubmitField('Changer le mot de passe')
    
    # Ajoutez ces classes à votre fichier forms.py existant

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from models import User

class EditProfileForm(FlaskForm):
    """Formulaire de modification de profil"""
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(message="Le nom d'utilisateur est requis"),
        Length(min=3, max=50, message="Entre 3 et 50 caractères")
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message="L'email est requis"),
        Email(message="Email invalide")
    ])
    
    first_name = StringField('Prénom', validators=[
        Length(max=50, message="Maximum 50 caractères")
    ])
    
    last_name = StringField('Nom', validators=[
        Length(max=50, message="Maximum 50 caractères")
    ])
    
    current_password = PasswordField('Mot de passe actuel', validators=[Optional()])
    
    new_password = PasswordField('Nouveau mot de passe', validators=[
        Optional(),
        Length(min=6, message="Au moins 6 caractères")
    ])
    
    confirm_password = PasswordField('Confirmer le nouveau mot de passe', validators=[
        EqualTo('new_password', message="Les mots de passe ne correspondent pas")
    ])
    
    submit = SubmitField('Enregistrer les modifications')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Ce nom d\'utilisateur est déjà pris.')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Cet email est déjà utilisé.')


class ProfilePhotoForm(FlaskForm):
    """Formulaire pour uploader une photo de profil"""
    photo = FileField('Photo de profil', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images uniquement (JPG, PNG, GIF)')
    ])
    
    submit = SubmitField('Télécharger')
    
class DeleteForm(FlaskForm):
    """Formulaire simple pour suppression (CSRF uniquement)"""
    submit = SubmitField("Supprimer")
