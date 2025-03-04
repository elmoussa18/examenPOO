import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox, QStackedWidget
)
from PyQt5.QtCore import Qt
from app import BFEMApp  # Importer l'application principale


class LoginApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gestion du BFEM - Connexion")
        self.setGeometry(100, 100, 400, 400)
        self.setStyleSheet("background-color: #1E1E1E; color: white;")

        # Stack pour gérer les pages
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Création des pages
        self.login_page = self.create_login_page()
        self.signup_page = self.create_signup_page()
        self.add_jury_page = self.create_add_jury_page()

        # Ajout des pages au stack
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.signup_page)
        self.stack.addWidget(self.add_jury_page)

        # Afficher la page de connexion par défaut
        self.stack.setCurrentWidget(self.login_page)

    def create_login_page(self):
        """Crée la page de connexion."""
        page = QWidget()
        layout = QVBoxLayout()

        # Titre
        label_title = QLabel("🔑 Connexion")
        label_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00A8E8;")
        layout.addWidget(label_title)

        # Champ Email
        self.login_email_input = QLineEdit()
        self.login_email_input.setPlaceholderText("Entrez votre email")
        self.login_email_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #2C2C2C; color: white;")
        layout.addWidget(self.login_email_input)

        # Champ Mot de passe
        self.login_password_input = QLineEdit()
        self.login_password_input.setPlaceholderText("Entrez votre mot de passe")
        self.login_password_input.setEchoMode(QLineEdit.Password)
        self.login_password_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #2C2C2C; color: white;")
        layout.addWidget(self.login_password_input)

        # Bouton Connexion
        login_button = QPushButton("Se connecter")
        login_button.setStyleSheet("background-color: #00A8E8; color: white; padding: 10px; border-radius: 5px;")
        login_button.clicked.connect(self.verify_login)
        layout.addWidget(login_button)

        # Bouton pour aller à la page d'inscription
        signup_button = QPushButton("S'inscrire")
        signup_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
        signup_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.signup_page))
        layout.addWidget(signup_button)

        # Bouton pour aller à la page d'ajout de jury
        add_jury_button = QPushButton("Ajouter un jury")
        add_jury_button.setStyleSheet("background-color: #FF5722; color: white; padding: 10px; border-radius: 5px;")
        add_jury_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.add_jury_page))
        layout.addWidget(add_jury_button)

        page.setLayout(layout)
        return page

    def create_signup_page(self):
        """Crée la page d'inscription d'un membre du jury."""
        page = QWidget()
        layout = QVBoxLayout()

        # Titre
        label_title = QLabel("📝 Inscription")
        label_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00A8E8;")
        layout.addWidget(label_title)

        # Champ Nom
        self.signup_nom_input = QLineEdit()
        self.signup_nom_input.setPlaceholderText("Nom")
        self.signup_nom_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #2C2C2C; color: white;")
        layout.addWidget(self.signup_nom_input)

        # Champ Prénom
        self.signup_prenom_input = QLineEdit()
        self.signup_prenom_input.setPlaceholderText("Prénom")
        self.signup_prenom_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #2C2C2C; color: white;")
        layout.addWidget(self.signup_prenom_input)

        # Champ Email
        self.signup_email_input = QLineEdit()
        self.signup_email_input.setPlaceholderText("Email")
        self.signup_email_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #2C2C2C; color: white;")
        layout.addWidget(self.signup_email_input)

        # Champ Mot de passe
        self.signup_password_input = QLineEdit()
        self.signup_password_input.setPlaceholderText("Mot de passe")
        self.signup_password_input.setEchoMode(QLineEdit.Password)
        self.signup_password_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #2C2C2C; color: white;")
        layout.addWidget(self.signup_password_input)

        # Bouton Inscription
        signup_button = QPushButton("S'inscrire")
        signup_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
        signup_button.clicked.connect(self.register_member)
        layout.addWidget(signup_button)

        # Bouton pour revenir à la page de connexion
        back_button = QPushButton("Retour à la connexion")
        back_button.setStyleSheet("background-color: #FF5722; color: white; padding: 10px; border-radius: 5px;")
        back_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.login_page))
        layout.addWidget(back_button)

        page.setLayout(layout)
        return page

    def create_add_jury_page(self):
        """Crée la page d'ajout d'un jury."""
        page = QWidget()
        layout = QVBoxLayout()

        # Titre
        label_title = QLabel("➕ Ajouter un jury")
        label_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00A8E8;")
        layout.addWidget(label_title)

        # Champ IA
        self.jury_ia_input = QLineEdit()
        self.jury_ia_input.setPlaceholderText("IA")
        self.jury_ia_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #2C2C2C; color: white;")
        layout.addWidget(self.jury_ia_input)

        # Champ IEF
        self.jury_ief_input = QLineEdit()
        self.jury_ief_input.setPlaceholderText("IEF")
        self.jury_ief_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #2C2C2C; color: white;")
        layout.addWidget(self.jury_ief_input)

        # Champ Localité
        self.jury_localite_input = QLineEdit()
        self.jury_localite_input.setPlaceholderText("Localité")
        self.jury_localite_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #2C2C2C; color: white;")
        layout.addWidget(self.jury_localite_input)

        # Champ Centre d'examen
        self.jury_centre_input = QLineEdit()
        self.jury_centre_input.setPlaceholderText("Centre d'examen")
        self.jury_centre_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #2C2C2C; color: white;")
        layout.addWidget(self.jury_centre_input)

        # Champ Président du jury
        self.jury_president_input = QLineEdit()
        self.jury_president_input.setPlaceholderText("Président du jury")
        self.jury_president_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #2C2C2C; color: white;")
        layout.addWidget(self.jury_president_input)

        # Champ Téléphone
        self.jury_telephone_input = QLineEdit()
        self.jury_telephone_input.setPlaceholderText("Téléphone")
        self.jury_telephone_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #2C2C2C; color: white;")
        layout.addWidget(self.jury_telephone_input)

        # Bouton Ajouter
        add_button = QPushButton("Ajouter")
        add_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
        add_button.clicked.connect(self.add_jury)
        layout.addWidget(add_button)

        # Bouton pour revenir à la page de connexion
        back_button = QPushButton("Retour à la connexion")
        back_button.setStyleSheet("background-color: #FF5722; color: white; padding: 10px; border-radius: 5px;")
        back_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.login_page))
        layout.addWidget(back_button)

        page.setLayout(layout)
        return page

    def verify_login(self):
        """Vérifie si l'utilisateur existe dans la base de données."""
        email = self.login_email_input.text().strip()
        password = self.login_password_input.text().strip()

        if not email or not password:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs.")
            return

        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Vérification de l'utilisateur dans la base de données
            cursor.execute("SELECT id, nom, prenom ,email FROM membre_jury WHERE email = ? AND mot_de_passe = ?", (email, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                QMessageBox.information(self, "Succès", "Connexion réussie !")

                # Ouvrir l'application principale avec l'ID du membre du jury connecté
                self.main_window = BFEMApp(user[3])  # user[0] est l'ID du membre du jury
                self.main_window.show()
                self.close()  # Fermer la fenêtre de connexion

            else:
                QMessageBox.critical(self, "Erreur", "Email ou mot de passe incorrect.")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")

    def register_member(self):
        """Inscrit un nouveau membre du jury."""
        nom = self.signup_nom_input.text().strip()
        prenom = self.signup_prenom_input.text().strip()
        email = self.signup_email_input.text().strip()
        password = self.signup_password_input.text().strip()

        if not nom or not prenom or not email or not password:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs.")
            return

        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Vérifier si l'email existe déjà
            cursor.execute("SELECT id FROM membre_jury WHERE email = ?", (email,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Erreur", "Cet email est déjà utilisé.")
                return

            # Ajouter le membre du jury
            cursor.execute("""
                INSERT INTO membre_jury (nom, prenom, email, mot_de_passe, jury_id)
                VALUES (?, ?, ?, ?, ?)
            """, (nom, prenom, email, password, 1))  # Remplacez 1 par l'ID du jury approprié

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Succès", "Inscription réussie !")
            self.stack.setCurrentWidget(self.login_page)  # Revenir à la page de connexion

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")

    def add_jury(self):
        """Ajoute un nouveau jury."""
        ia = self.jury_ia_input.text().strip()
        ief = self.jury_ief_input.text().strip()
        localite = self.jury_localite_input.text().strip()
        centre_examen = self.jury_centre_input.text().strip()
        president_jury = self.jury_president_input.text().strip()
        telephone = self.jury_telephone_input.text().strip()

        if not ia or not ief or not localite or not centre_examen or not president_jury or not telephone:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs.")
            return

        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Ajouter le jury
            cursor.execute("""
                INSERT INTO jury (ia, ief, localite, centre_examen, president_jury, telephone)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ia, ief, localite, centre_examen, president_jury, telephone))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Succès", "Jury ajouté avec succès !")
            self.stack.setCurrentWidget(self.login_page)  # Revenir à la page de connexion

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")


if __name__ == "__main__":
    app = QApplication([])
    window = LoginApp()
    window.show()
    app.exec_()