import sqlite3
import random
import string
from functools import partial

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QStackedWidget, QFormLayout, QLineEdit, QDateEdit, QComboBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QSpinBox, QDialog, QFrame,
    QAbstractItemView, QDoubleSpinBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument, QTextCursor

from fpdf import FPDF
from fpdf.enums import XPos, YPos  # Pour gérer les positions du texte
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle



class BFEMApp(QMainWindow):
    def __init__(self, email_membre):
        super().__init__()
        self.setWindowTitle("Gestion du BFEM")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("background-color: #1E1E1E; color: white;")

        # Récupérer les informations du jury et du membre
        self.jury_info, self.membre_connecte = self.get_jury_info(email_membre)

        self.theme_sombre = True  # Commence en mode sombre

        # Interface principale
        self.init_ui()

    def init_ui(self):
        """Initialisation de l'interface utilisateur"""
        self.header = self.create_header()
        self.sidebar = self.create_sidebar()
        self.main_content = QStackedWidget()

        # Pages principales
        self.dashboard_page = self.create_dashboard_page()
        self.main_content.addWidget(self.dashboard_page)

        # Page Gestion des candidats
        self.gestion_candidats_page = QLabel("Gestion des candidats", alignment=Qt.AlignCenter)
        self.gestion_candidats_page.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFA500;")
        self.main_content.addWidget(self.gestion_candidats_page)

        # Layout principal
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.sidebar)
        content_layout = QVBoxLayout()
        content_layout.addWidget(self.header)
        content_layout.addWidget(self.main_content)
        main_layout.addLayout(content_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    # header
    def create_header(self):
        """Créer l'en-tête de l'application avec un design moderne"""
        header = QWidget()
        header.setStyleSheet("""
            background-color: #1E1E1E;
            padding: 10px;
            border-bottom: 2px solid #3A3A3A;
        """)
        layout = QHBoxLayout()

        # Bouton Menu
        menu_button = QPushButton("📂 Menu", clicked=self.toggle_sidebar)
        menu_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #666;
            }
        """)

        # Bouton Déconnexion
        logout_button = QPushButton("🔴 Déconnexion", clicked=self.close)
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #FF4444;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #FF5555;
            }
            QPushButton:pressed {
                background-color: #FF6666;
            }
        """)

        # Informations du jury
        jury_label = QLabel(f"📌 {self.jury_info}")
        jury_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #00A8E8;
                font-weight: bold;
            }
        """)

        # Informations du membre connecté
        membre_label = QLabel(f"👤 {self.membre_connecte}")
        membre_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #FFFFFF;
                font-weight: bold;
            }
        """)

        # Ajout des widgets au layout
        layout.addWidget(menu_button)
        layout.addWidget(jury_label)
        layout.addStretch()  # Espace flexible pour pousser les éléments à droite
        layout.addWidget(membre_label)
        layout.addWidget(logout_button)

        header.setLayout(layout)
        return header

    # le sideBar
    def create_sidebar(self):
        """Créer la barre latérale avec sous-menus bien organisés"""
        sidebar = QWidget()
        sidebar.setStyleSheet("background-color: #2C2C2C; padding: 10px;")
        sidebar.setFixedWidth(250)
        layout = QVBoxLayout()

        # 🔹 TABLEAU DE BORD
        self.btn_dashboard = QPushButton("🏠 Tableau de bord",
                                         clicked=lambda: self.main_content.setCurrentWidget(self.dashboard_page))
        self.btn_dashboard.setStyleSheet("background-color: #444; color: white; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.btn_dashboard)

        # 🔹 GESTION DES CANDIDATS
        self.btn_candidats = QPushButton("👥 Gestion des candidats", clicked=self.toggle_candidats_submenu)
        self.btn_candidats.setStyleSheet("background-color: #444; color: white; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.btn_candidats)

        # Sous-menu des candidats
        self.candidats_submenu = QVBoxLayout()
        self.candidats_submenu.setSpacing(5)
        self.candidats_submenu.setContentsMargins(20, 0, 0, 0)

        self.btn_liste_candidats = QPushButton("📋 Liste des candidats", clicked=self.open_liste_candidats)
        self.btn_ajouter_candidat = QPushButton("➕ Ajouter un candidat", clicked=self.open_add_candidat_form)
        self.btn_generer_anonyme = QPushButton("🔀 Générer Anonymat", clicked=self.generer_anonymat)
        self.btn_liste_releves = QPushButton("📜 Liste des relevés", clicked=self.open_liste_releves)

        # Ajout du bouton pour exporter en PDF
        self.btn_liste_candidats_pdf = QPushButton("📄 Liste des candidats en PDF", clicked=self.exporter_candidats_pdf)

        # Appliquer le même style à tous les boutons du sous-menu
        for btn in [self.btn_ajouter_candidat, self.btn_liste_candidats, self.btn_generer_anonyme,
                    self.btn_liste_releves, self.btn_liste_candidats_pdf]:
            btn.setStyleSheet(
                "background-color: #555; color: white; padding: 8px; border-radius: 5px; margin-left: 20px;")

        # Ajouter les boutons au sous-menu
        self.candidats_submenu.addWidget(self.btn_ajouter_candidat)
        self.candidats_submenu.addWidget(self.btn_liste_candidats)
        self.candidats_submenu.addWidget(self.btn_generer_anonyme)
        self.candidats_submenu.addWidget(self.btn_liste_releves)
        self.candidats_submenu.addWidget(self.btn_liste_candidats_pdf)  # ✅ Nouveau bouton ajouté ici

        # Convertir en widget et cacher par défaut
        self.candidats_submenu_widget = QWidget()
        self.candidats_submenu_widget.setLayout(self.candidats_submenu)
        self.candidats_submenu_widget.setVisible(False)
        layout.addWidget(self.candidats_submenu_widget)

        # 🔹 SÉPARATEUR VISUEL
        layout.addWidget(self.create_separator())

        # 🔹 GESTION DU PREMIER TOUR
        self.btn_notes_matieres = QPushButton("📚 Gestion du premier tour", clicked=self.toggle_notes_submenu)
        self.btn_notes_matieres.setStyleSheet(
            "background-color: #444; color: white; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.btn_notes_matieres)

        # Sous-menu des notes et matières
        self.notes_submenu = QVBoxLayout()
        self.notes_submenu.setSpacing(5)
        self.notes_submenu.setContentsMargins(20, 0, 0, 0)

        self.btn_ajouter_matiere = QPushButton("✏️ Ajouter une matière", clicked=self.open_add_matiere_form)
        self.btn_liste_matieres = QPushButton("📋 Liste des matières", clicked=self.open_liste_matieres)
        self.btn_ajouter_note = QPushButton("📝 Ajouter une note", clicked=self.open_add_note_form)  # ✅ Ajout
        self.btn_liste_notes = QPushButton("📊 Liste des notes", clicked=self.open_liste_notes)  # ✅ Ajout

        # Appliquer un style uniforme
        for btn in [self.btn_liste_matieres, self.btn_ajouter_matiere, self.btn_ajouter_note, self.btn_liste_notes]:
            btn.setStyleSheet(
                "background-color: #555; color: white; padding: 8px; border-radius: 5px; margin-left: 20px;")

        # Ajouter les boutons au sous-menu
        self.notes_submenu.addWidget(self.btn_liste_matieres)
        self.notes_submenu.addWidget(self.btn_ajouter_matiere)
        self.notes_submenu.addWidget(self.btn_ajouter_note)  # ✅ Ajout
        self.notes_submenu.addWidget(self.btn_liste_notes)  # ✅ Ajout

        # Convertir en widget et cacher par défaut
        self.notes_submenu_widget = QWidget()
        self.notes_submenu_widget.setLayout(self.notes_submenu)
        self.notes_submenu_widget.setVisible(False)
        layout.addWidget(self.notes_submenu_widget)

        # 🔹 SÉPARATEUR VISUEL
        layout.addWidget(self.create_separator())
        # 🔹 RÉSULTATS PREMIER TOUR
        self.btn_resultats_premier_tour = QPushButton("📊 Résultats Premier Tour", clicked=self.toggle_resultats_submenu)
        self.btn_resultats_premier_tour.setStyleSheet(
            "background-color: #444; color: white; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.btn_resultats_premier_tour)

        # Sous-menu des résultats du premier tour
        self.resultats_submenu = QVBoxLayout()
        self.resultats_submenu.setSpacing(5)
        self.resultats_submenu.setContentsMargins(20, 0, 0, 0)

        self.btn_deliberation = QPushButton("⚖️ Délibération", clicked=self.open_deliberation)
        self.btn_liste_admis = QPushButton("✅ Liste des admis", clicked=self.open_liste_admis)
        self.btn_liste_admissibles = QPushButton("🟠 Liste des admissibles", clicked=self.open_liste_admissibles)
        self.btn_liste_ajournes = QPushButton("❌ Liste des ajournés", clicked=self.open_liste_ajournes)
        self.btn_releve_notes = QPushButton("📄 Relevé de notes", clicked=self.open_releve_notes)

        # Appliquer le même style à tous les boutons du sous-menu
        for btn in [self.btn_deliberation, self.btn_liste_admis, self.btn_liste_admissibles, self.btn_liste_ajournes,
                    self.btn_releve_notes]:
            btn.setStyleSheet(
                "background-color: #555; color: white; padding: 8px; border-radius: 5px; margin-left: 20px;")

        # Ajouter les boutons au sous-menu
        self.resultats_submenu.addWidget(self.btn_deliberation)
        self.resultats_submenu.addWidget(self.btn_liste_admis)
        self.resultats_submenu.addWidget(self.btn_liste_admissibles)
        self.resultats_submenu.addWidget(self.btn_liste_ajournes)
        self.resultats_submenu.addWidget(self.btn_releve_notes)

        # Convertir en widget et cacher par défaut
        self.resultats_submenu_widget = QWidget()
        self.resultats_submenu_widget.setLayout(self.resultats_submenu)
        self.resultats_submenu_widget.setVisible(False)
        layout.addWidget(self.resultats_submenu_widget)

        # 🔹 SÉPARATEUR VISUEL
        layout.addWidget(self.create_separator())

        # 🔹 GESTION DU DEUXIÈME TOUR
        self.btn_notes_matieres_2em_tour = QPushButton("📚 Gestion du deuxième tour",
                                                       clicked=self.toggle_notes_2em_tour_submenu)
        self.btn_notes_matieres_2em_tour.setStyleSheet(
            "background-color: #444; color: white; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.btn_notes_matieres_2em_tour)

        # Sous-menu des notes et matières du 2e tour
        self.notes_2em_tour_submenu = QVBoxLayout()
        self.notes_2em_tour_submenu.setSpacing(5)
        self.notes_2em_tour_submenu.setContentsMargins(20, 0, 0, 0)

        self.btn_ajouter_matiere_2em_tour = QPushButton("✏️ Ajouter une matière du 2e tour",
                                                        clicked=self.open_add_matiere_2em_tour_form)
        self.btn_liste_matieres_2em_tour = QPushButton("📋 Liste des matières du 2e tour",
                                                       clicked=self.open_liste_matieres_2em_tour)
        self.btn_ajouter_note_2em_tour = QPushButton("📝 Ajouter une note du 2e tour",
                                                     clicked=self.open_add_note_2em_tour_form)
        self.btn_liste_notes_2em_tour = QPushButton("📊 Liste des notes du 2e tour",
                                                    clicked=self.open_liste_notes_2em_tour)

        # Appliquer un style uniforme
        for btn in [self.btn_ajouter_matiere_2em_tour, self.btn_liste_matieres_2em_tour, self.btn_ajouter_note_2em_tour,
                    self.btn_liste_notes_2em_tour]:
            btn.setStyleSheet(
                "background-color: #555; color: white; padding: 8px; border-radius: 5px; margin-left: 20px;")

        # Ajouter les boutons au sous-menu
        self.notes_2em_tour_submenu.addWidget(self.btn_liste_matieres_2em_tour)
        self.notes_2em_tour_submenu.addWidget(self.btn_ajouter_matiere_2em_tour)
        self.notes_2em_tour_submenu.addWidget(self.btn_ajouter_note_2em_tour)
        self.notes_2em_tour_submenu.addWidget(self.btn_liste_notes_2em_tour)

        # Convertir en widget et cacher par défaut
        self.notes_2em_tour_submenu_widget = QWidget()
        self.notes_2em_tour_submenu_widget.setLayout(self.notes_2em_tour_submenu)
        self.notes_2em_tour_submenu_widget.setVisible(False)
        layout.addWidget(self.notes_2em_tour_submenu_widget)

        # 🔹 SÉPARATEUR VISUEL
        layout.addWidget(self.create_separator())

        # 🔹 RÉSULTATS DEUXIÈME TOUR
        self.btn_resultats_deuxieme_tour = QPushButton("📊 Résultats Deuxième Tour",
                                                       clicked=self.toggle_resultats_2eme_tour)
        self.btn_resultats_deuxieme_tour.setStyleSheet(
            "background-color: #444; color: white; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(self.btn_resultats_deuxieme_tour)

        # Sous-menu des résultats du deuxième tour
        self.resultats_2eme_tour_submenu = QVBoxLayout()
        self.resultats_2eme_tour_submenu.setSpacing(5)
        self.resultats_2eme_tour_submenu.setContentsMargins(20, 0, 0, 0)

        self.btn_deliberation_2eme_tour = QPushButton("⚖️ Délibération", clicked=self.open_deliberation_2eme_tour)
        self.btn_liste_admis_2eme_tour = QPushButton("✅ Liste des admis", clicked=self.open_liste_admis_2eme_tour)
        self.btn_liste_ajournes_2eme_tour = QPushButton("❌ Liste des ajournés",
                                                        clicked=self.open_liste_ajournes_2eme_tour)
        self.btn_releve_notes_2eme_tour = QPushButton("📄 Relevé de notes", clicked=self.open_releve_notes_2eme_tour)

        # Appliquer le même style à tous les boutons du sous-menu
        for btn in [
            self.btn_deliberation_2eme_tour,
            self.btn_liste_admis_2eme_tour,
            self.btn_liste_ajournes_2eme_tour,
            self.btn_releve_notes_2eme_tour
        ]:
            btn.setStyleSheet(
                "background-color: #555; color: white; padding: 8px; border-radius: 5px; margin-left: 20px;"
            )

        # Ajouter les boutons au sous-menu
        self.resultats_2eme_tour_submenu.addWidget(self.btn_deliberation_2eme_tour)
        self.resultats_2eme_tour_submenu.addWidget(self.btn_liste_admis_2eme_tour)
        self.resultats_2eme_tour_submenu.addWidget(self.btn_liste_ajournes_2eme_tour)
        self.resultats_2eme_tour_submenu.addWidget(self.btn_releve_notes_2eme_tour)

        # Convertir en widget et cacher par défaut
        self.resultats_2eme_tour_submenu_widget = QWidget()
        self.resultats_2eme_tour_submenu_widget.setLayout(self.resultats_2eme_tour_submenu)
        self.resultats_2eme_tour_submenu_widget.setVisible(False)
        layout.addWidget(self.resultats_2eme_tour_submenu_widget)

        # 🔹 SÉPARATEUR VISUEL
        layout.addWidget(self.create_separator())

        # 🔹 PARAMÈTRES
        self.btn_parametres = QPushButton("⚙️ Paramètres", clicked=self.toggle_theme)
        self.btn_parametres.setStyleSheet("background-color: #444; color: white; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.btn_parametres)

        layout.addStretch()  # Pour équilibrer l'espace

        sidebar.setLayout(layout)
        return sidebar

    # separateur des element du sidebare et page d'acceulle

    def create_separator(self):
        """Créer une ligne séparatrice pour organiser visuellement le sidebar"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)  # Créer une ligne horizontale
        line.setStyleSheet("background-color: #000000; height: 1px; margin: 0px;")  # Style noir et hauteur fine
        return line

    def create_dashboard_page(self):
        """Crée la page du tableau de bord avec les statistiques des résultats"""
        dashboard_widget = QWidget()
        layout = QVBoxLayout()

        # Titre du tableau de bord
        title = QLabel("Tableau de Bord - Statistiques des Résultats", alignment=Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50; margin-bottom: 20px;")
        layout.addWidget(title)

        # Statistiques du premier et deuxième tour
        stats_1er_tour = self.get_stats_resultat("resultat")
        stats_2e_tour = self.get_stats_resultat("resultat_2e_tour")

        # Affichage des statistiques dans un layout horizontal pour les comparer
        stats_layout = QHBoxLayout()

        # Premier tour
        stats_1er_tour_label = QLabel(self.format_stats(stats_1er_tour, "Premier Tour"))
        stats_1er_tour_label.setStyleSheet("""
            font-size: 18px; 
            background-color: #f9f9f9; 
            border-radius: 10px; 
            padding: 20px; 
            margin-right: 20px;
            border: 1px solid #ccc;
            color: #333;  /* Texte plus sombre pour une meilleure lisibilité */
            font-weight: bold;  /* Met en gras pour améliorer la visibilité */
        """)
        stats_layout.addWidget(stats_1er_tour_label)

        # Deuxième tour
        stats_2e_tour_label = QLabel(self.format_stats(stats_2e_tour, "Deuxième Tour"))
        stats_2e_tour_label.setStyleSheet("""
            font-size: 18px; 
            background-color: #f9f9f9; 
            border-radius: 10px; 
            padding: 20px; 
            margin-left: 20px;
            border: 1px solid #ccc;
            color: #333;  /* Texte plus sombre pour une meilleure lisibilité */
            font-weight: bold;  /* Met en gras pour améliorer la visibilité */
        """)
        stats_layout.addWidget(stats_2e_tour_label)

        # Ajouter les statistiques au layout principal
        layout.addLayout(stats_layout)

        dashboard_widget.setLayout(layout)
        return dashboard_widget

    def get_stats_resultat(self, table_name):
        """Récupère les statistiques des résultats pour une table donnée (1er ou 2e tour)"""
        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Récupérer les statistiques des résultats
            cursor.execute(f"""
                SELECT 
                    COUNT(*) AS total_candidats,
                    SUM(CASE WHEN presentation = "Admis d'office" THEN 1 ELSE 0 END) AS admis_d_office,
                    SUM(CASE WHEN presentation = 'Admissible' THEN 1 ELSE 0 END) AS admissibles,
                    SUM(CASE WHEN presentation = 'Ajourné' THEN 1 ELSE 0 END) AS ajournes
                FROM {table_name}
            """)

            stats = cursor.fetchone()

            conn.close()

            return {
                "total_candidats": stats[0],
                "admis_d_office": stats[1],
                "admissibles": stats[2],
                "ajournes": stats[3]
            }

        except Exception as e:
            print(f"Erreur lors de la récupération des statistiques : {e}")
            return {
                "total_candidats": 0,
                "admis_d_office": 0,
                "admissibles": 0,
                "ajournes": 0
            }

    def format_stats(self, stats, tour_name):
        """Formate les statistiques pour l'affichage"""
        return f"""
        <b>{tour_name}</b><br>
        <u>Total Candidats:</u> {stats['total_candidats']}<br>
        <u>Admis d'office:</u> {stats['admis_d_office']}<br>
        <u>Admissibles:</u> {stats['admissibles']}<br>
        <u>Ajournés:</u> {stats['ajournes']}<br>
        """

    def toggle_theme(self):
        """Alterner entre le mode clair et le mode sombre"""
        if self.theme_sombre:
            # Passer en mode clair
            self.setStyleSheet("background-color: #F5F5F5; color: black;")
            self.sidebar.setStyleSheet("background-color: #E0E0E0;")
            self.header.setStyleSheet("background-color: #D0D0D0; border-bottom: 2px solid #B0B0B0;")
            self.btn_parametres.setStyleSheet(
                "background-color: #DDD; color: black; padding: 10px; border-radius: 5px;")
        else:
            # Passer en mode sombre
            self.setStyleSheet("background-color: #1E1E1E; color: white;")
            self.sidebar.setStyleSheet("background-color: #2C2C2C;")
            self.header.setStyleSheet("background-color: #1E1E1E; border-bottom: 2px solid #3A3A3A;")
            self.btn_parametres.setStyleSheet(
                "background-color: #444; color: white; padding: 10px; border-radius: 5px;")

        self.theme_sombre = not self.theme_sombre  # Inverser l'état du thème

    # resultat 2em tour
    def toggle_resultats_2eme_tour(self):
        visible = self.resultats_2eme_tour_submenu_widget.isVisible()
        self.resultats_2eme_tour_submenu_widget.setVisible(not visible)

    def open_deliberation_2eme_tour(self):
        """Affiche la page de délibération du deuxième tour et met à jour les résultats"""
        try:
            # Connexion à la base de données
            conn = sqlite3.connect('bfem.db')
            cursor = conn.cursor()

            # Récupérer tous les candidats qui ont des notes pour le 2ᵉ tour
            cursor.execute("""
                SELECT c.id, c.nom, c.prenom
                FROM candidat c
                WHERE c.id IN (
                    SELECT DISTINCT n.candidat_id
                    FROM note n
                    JOIN matiere m ON n.matiere_id = m.id
                    WHERE m.tour = 2
                )
            """)
            candidats = cursor.fetchall()

            for candidat in candidats:
                candidat_id = candidat[0]

                # Récupérer les notes du 2ᵉ tour pour chaque matière associée au 2ᵉ tour
                cursor.execute("""
                    SELECT n.note_deuxieme_tour, m.coefficient, m.nom
                    FROM note n
                    JOIN matiere m ON n.matiere_id = m.id
                    WHERE n.candidat_id = ? AND m.tour = 2
                """, (candidat_id,))
                notes = cursor.fetchall()

                total_points = 0
                total_coefficients = 0

                # Calcul des points et des coefficients
                for note, coefficient, matiere in notes:
                    total_points += note * coefficient
                    total_coefficients += coefficient

                    # Appliquer la règle RM2 (Bonus/Malus pour EPS)
                    if matiere == 'EPS':
                        if note > 10:
                            total_points += (note - 10)  # Bonus pour EPS
                        else:
                            total_points -= (10 - note)  # Malus pour EPS

                    # Appliquer la règle RM3 (Bonus pour épreuves facultatives)
                    if matiere == 'Facultatif' and note > 10:
                        total_points += note - 10  # Bonus pour épreuve facultative

                # Calcul de la moyenne
                if total_coefficients > 0:
                    moyenne = total_points / total_coefficients
                else:
                    moyenne = 0

                # Assurer que la moyenne est entre 0 et 20
                moyenne = max(0, min(moyenne, 20))

                # Détermination du statut (Admis, Admissible, Ajourné, etc.)
                if total_points >= 180:
                    presentation = 'Admis d\'office'
                    repechable = 0
                elif total_points >= 153:
                    presentation = 'Admissible'
                    repechable = 0
                else:
                    presentation = 'Ajourné'
                    repechable = 0

                # Règles de repêchage
                if total_points >= 171 and total_points < 180:
                    repechable = 1
                elif total_points >= 144 and total_points < 153:
                    repechable = 1
                if moyenne >= 12:
                    repechable = 1

                # Mise à jour des résultats dans la table 'resultat_2e_tour'
                cursor.execute("""
                    UPDATE resultat_2e_tour
                    SET total_points = ?, moyenne = ?, repechable = ?, presentation = ?
                    WHERE candidat_id = ?
                """, (total_points, moyenne, repechable, presentation, candidat_id))

            # Committer les changements
            conn.commit()

            # Fermer la connexion
            conn.close()

            # Ajouter un message dans l'interface
            self.deliberation_page = QLabel("⚖️ Délibération du Deuxième Tour terminée", alignment=Qt.AlignCenter)
            self.deliberation_page.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFA500;")
            self.main_content.addWidget(self.deliberation_page)
            self.main_content.setCurrentWidget(self.deliberation_page)

        except sqlite3.Error as e:
            self.show_error_message(f"Erreur lors de la délibération du deuxième tour : {e}")

    def open_liste_admis_2eme_tour(self):
        """Affiche la liste des admis du deuxième tour (180 points et plus)"""
        print("Ouverture de la liste des admis du deuxième tour")

        try:
            # Connexion à la base de données
            conn = sqlite3.connect('bfem.db')
            cursor = conn.cursor()

            # Récupérer les candidats admis (total_points >= 180) du deuxième tour
            cursor.execute("""
                SELECT c.numero_table, c.nom, c.prenom, r.total_points
                FROM resultat_2e_tour r
                JOIN candidat c ON r.candidat_id = c.id
                WHERE r.total_points >= 180
                ORDER BY r.total_points DESC
            """)
            admis = cursor.fetchall()

        except sqlite3.Error as e:
            self.show_error_message(f"❌ Erreur SQLite lors de la récupération des admis du 2ᵉ tour : {e}")
            return  # Stopper l'exécution en cas d'erreur SQL

        finally:
            if conn:
                conn.close()  # Fermer la connexion

        try:
            # Supprimer tout ce qui est affiché avant d'ajouter du nouveau contenu
            for i in reversed(range(self.main_content.count())):
                widget = self.main_content.widget(i)
                if widget:
                    widget.setParent(None)

            if admis:
                # Création d'un QWidget parent pour contenir le tableau et les boutons
                container_widget = QWidget()

                # Création du tableau pour afficher les résultats
                table = QTableWidget()
                table.setRowCount(len(admis))
                table.setColumnCount(4)  # 4 Colonnes (Numéro de table, Nom, Prénom, Total Points)
                table.setHorizontalHeaderLabels(["Numéro Table", "Nom", "Prénom", "Total Points"])
                table.setStyleSheet("""
                    font-size: 16px;
                    border: 1px solid #ccc;
                    background-color: #f9f9f9;
                    selection-background-color: #8BC34A;
                    selection-color: white;
                """)

                # Styliser les titres de colonnes
                table.horizontalHeader().setStyleSheet("""
                background-color: #f7b731;  /* Choisir une couleur de fond différente si tu veux */
                color: black;  /* Texte en noir */
                font-weight: bold;  /* Mettre en gras */
                font-size: 14px;  /* Taille de la police */
                """)

                # Styliser les cellules
                table.setStyleSheet("""
                    QTableWidget::item {
                        border: 1px solid #ccc;
                        padding: 10px;
                    }
                    QTableWidget::item:selected {
                        background-color: #4CAF50;
                        color: white;
                    }
                """)

                # Remplir le tableau avec les données des admis
                for row, (numero_table, nom, prenom, total_points) in enumerate(admis):
                    # Arrondir le total des points à 2 décimales
                    total_points_rounded = round(total_points, 2)
                    table.setItem(row, 0, QTableWidgetItem(str(numero_table)))
                    table.setItem(row, 1, QTableWidgetItem(nom))
                    table.setItem(row, 2, QTableWidgetItem(prenom))
                    table.setItem(row, 3, QTableWidgetItem(str(total_points_rounded)))

                # Ajustements pour améliorer l'affichage du tableau
                table.horizontalHeader().setStretchLastSection(True)  # Ajuste la largeur des colonnes
                table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Désactive l'édition des cellules

                # Création du layout pour le tableau et les boutons
                layout = QVBoxLayout(container_widget)  # Utilisation d'un QVBoxLayout pour empiler les éléments

                # Ajouter le tableau au layout
                layout.addWidget(table)

                # Créer un layout horizontal pour les boutons
                button_layout = QHBoxLayout()

                # Ajouter le bouton pour générer le PDF
                btn_generate_pdf = QPushButton("📑 Générer PDF des admis",
                                               clicked=lambda: self.generate_pdf_admis_2eme_tour(admis))
                btn_generate_pdf.setStyleSheet(
                    "background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
                btn_generate_pdf.setFixedWidth(250)  # Limiter la largeur du bouton

                # Ajouter le bouton pour imprimer
                btn_print = QPushButton("🖨️ Imprimer la liste", clicked=lambda: self.print_table4(table))
                btn_print.setStyleSheet(
                    "background-color: #2196F3; color: white; padding: 10px; border-radius: 5px;")
                btn_print.setFixedWidth(250)  # Limiter la largeur du bouton

                # Ajouter les boutons au layout horizontal
                button_layout.addWidget(btn_generate_pdf, alignment=Qt.AlignCenter)
                button_layout.addWidget(btn_print, alignment=Qt.AlignCenter)

                # Ajouter le layout des boutons à celui principal
                layout.addLayout(button_layout)

                # Ajouter le widget contenant le tableau et les boutons à self.main_content
                self.main_content.addWidget(container_widget)

            else:
                # Afficher un message si aucun admis
                no_admis = QLabel("⚠ Aucun candidat n'a obtenu 180 points ou plus au deuxième tour.",
                                  alignment=Qt.AlignCenter)
                no_admis.setStyleSheet("font-size: 18px; color: #FF0000;")
                self.main_content.addWidget(no_admis)

            # Mettre à jour l'affichage en toute sécurité
            self.main_content.setCurrentIndex(self.main_content.count() - 1)

        except Exception as e:
            self.show_error_message(f"⚠ Erreur inattendue lors de l'affichage du tableau des admis du 2ᵉ tour : {e}")

    def generate_pdf_admis_2eme_tour(self, admis):
        """Génère un fichier PDF avec la liste des admis du deuxième tour sous forme de tableau, avec gestion des pages."""
        try:
            # Créer un fichier PDF
            file_name = "liste_admis_2eme_tour.pdf"
            c = canvas.Canvas(file_name, pagesize=letter)
            width, height = letter  # Taille de la page

            # Ajouter un titre
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, height - 50, "Liste des admis du deuxième tour")

            # Données du tableau
            data = [["Numéro de Table", "Nom", "Prénom", "Points"]]  # En-tête du tableau

            # Ajouter les résultats des candidats avec le total des points arrondi
            for numero_table, nom, prenom, total_points in admis:
                total_points_rounded = round(total_points, 2)
                data.append([str(numero_table), nom, prenom, str(total_points_rounded)])

            # Configuration de la pagination
            max_rows_per_page = 30  # Nombre de lignes max par page
            y_position = height - 100  # Position initiale du tableau
            page_number = 1  # Numéro de page

            # Séparer les données en plusieurs pages
            for i in range(0, len(data), max_rows_per_page):
                if i > 0:
                    c.showPage()  # Nouvelle page
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(100, height - 50, "Liste des admis du deuxième tour")

                # Récupérer les données pour la page actuelle
                data_chunk = data[i:i + max_rows_per_page]

                # Créer un tableau avec les données
                table = Table(data_chunk, colWidths=[100, 150, 150, 100])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # En-tête en gris
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texte en blanc
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centrer les textes
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Police de l'en-tête
                    ('FONTSIZE', (0, 0), (-1, -1), 12),  # Taille de la police
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Espacement en bas de l'en-tête
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Fond beige pour le reste
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black)  # Bordures de tableau
                ]))

                # Dessiner le tableau sur la page
                table.wrapOn(c, width, height)
                table.drawOn(c, 50, y_position - (len(data_chunk) * 20))  # Ajuster position

                # Ajouter le numéro de page
                c.setFont("Helvetica", 10)
                c.drawString(width - 100, 30, f"Page {page_number}")
                page_number += 1

            # Sauvegarder le fichier PDF
            c.save()
            self.show_info_message(f"✅ PDF généré avec succès : {file_name}")

        except Exception as e:
            self.show_error_message(f"❌ Erreur lors de la génération du PDF : {e}")

    def print_table4(self, table):
        """Imprime le tableau"""
        try:
            # Créer un document texte pour l'impression
            document = QTextDocument()
            cursor = QTextCursor(document)

            # Créer un tableau HTML à partir des données du QTableWidget
            html = "<table border='1' cellpadding='5' cellspacing='0'><tr>"
            for col in range(table.columnCount()):
                html += f"<th>{table.horizontalHeaderItem(col).text()}</th>"
            html += "</tr>"

            for row in range(table.rowCount()):
                html += "<tr>"
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    html += f"<td>{item.text() if item else ''}</td>"
                html += "</tr>"
            html += "</table>"

            # Ajouter le tableau HTML au document
            document.setHtml(html)

            # Configurer l'impression
            printer = QPrinter()
            print_dialog = QPrintDialog(printer)
            if print_dialog.exec() == QPrintDialog.Accepted:
                document.print_(printer)  # Imprimer le document
                self.show_info_message("✅ Impression terminée avec succès.")
        except Exception as e:
            self.show_error_message(f"❌ Erreur lors de l'impression : {e}")

    def open_liste_ajournes_2eme_tour(self):
        """Affiche la liste des ajournés du deuxième tour (moins de 153 points)"""
        print("Ouverture de la liste des ajournés du deuxième tour")

        try:
            # Connexion à la base de données
            conn = sqlite3.connect('bfem.db')
            cursor = conn.cursor()

            # Récupérer les candidats ajournés (total_points < 153) du deuxième tour
            cursor.execute("""
                SELECT c.numero_table, c.nom, c.prenom, c.date_naissance, r.total_points
                FROM resultat_2e_tour r
                JOIN candidat c ON r.candidat_id = c.id
                WHERE r.total_points < 153
                ORDER BY r.total_points ASC
            """)
            ajournes = cursor.fetchall()

        except sqlite3.Error as e:
            self.show_error_message(f"❌ Erreur SQLite lors de la récupération des ajournés du 2ᵉ tour : {e}")
            return  # Stopper l'exécution en cas d'erreur SQL

        finally:
            if conn:
                conn.close()  # Fermer la connexion

        try:
            # Supprimer tout ce qui est affiché avant d'ajouter du nouveau contenu
            for i in reversed(range(self.main_content.count())):
                widget = self.main_content.widget(i)
                if widget:
                    widget.setParent(None)

            if ajournes:
                # Création d'un QWidget parent pour contenir le tableau et les boutons
                container_widget = QWidget()

                # Création du tableau pour afficher les résultats
                table = QTableWidget()
                table.setRowCount(len(ajournes))
                table.setColumnCount(5)  # 5 Colonnes (Numéro Table, Nom, Prénom, Date de Naissance, Total Points)
                table.setHorizontalHeaderLabels(["Numéro Table", "Nom", "Prénom", "Date de Naissance", "Total Points"])
                table.setStyleSheet("""
                    font-size: 16px;
                    border: 1px solid #ccc;
                    background-color: #f9f9f9;
                    selection-background-color: #8BC34A;
                    selection-color: white;
                """)

                # Styliser les titres de colonnes
                table.horizontalHeader().setStyleSheet("""
                color: black;  /* Texte en noir */
                font-weight: bold;  /* Mettre en gras */

                """)

                # Styliser les cellules
                table.setStyleSheet("""
                    QTableWidget::item {
                        border: 1px solid #ccc;
                        padding: 10px;
                    }
                    QTableWidget::item:selected {
                        background-color: #4CAF50;
                        color: white;
                    }
                """)

                # Remplir le tableau avec les données des ajournés
                for row, (numero_table, nom, prenom, date_naissance, total_points) in enumerate(ajournes):
                    # Arrondir le total des points à 2 décimales
                    total_points_rounded = round(total_points, 2)
                    table.setItem(row, 0, QTableWidgetItem(str(numero_table)))
                    table.setItem(row, 1, QTableWidgetItem(nom))
                    table.setItem(row, 2, QTableWidgetItem(prenom))
                    table.setItem(row, 3, QTableWidgetItem(date_naissance))
                    table.setItem(row, 4, QTableWidgetItem(str(total_points_rounded)))

                # Ajustements pour améliorer l'affichage du tableau
                table.horizontalHeader().setStretchLastSection(True)  # Ajuste la largeur des colonnes
                table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Désactive l'édition des cellules

                # Création du layout pour le tableau et les boutons
                layout = QVBoxLayout(container_widget)  # Utilisation d'un QVBoxLayout pour empiler les éléments

                # Ajouter le tableau au layout
                layout.addWidget(table)

                # Créer un layout horizontal pour les boutons
                button_layout = QHBoxLayout()

                # Ajouter le bouton pour générer le PDF
                btn_generate_pdf = QPushButton("📑 Générer PDF des ajournés",
                                               clicked=lambda: self.generate_pdf_ajournes_2eme_tour(ajournes))
                btn_generate_pdf.setStyleSheet(
                    "background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
                btn_generate_pdf.setFixedWidth(250)  # Limiter la largeur du bouton

                # Ajouter le bouton pour imprimer
                btn_print = QPushButton("🖨️ Imprimer la liste", clicked=lambda: self.print_table5(table))
                btn_print.setStyleSheet(
                    "background-color: #2196F3; color: white; padding: 10px; border-radius: 5px;")
                btn_print.setFixedWidth(250)  # Limiter la largeur du bouton

                # Ajouter les boutons au layout horizontal
                button_layout.addWidget(btn_generate_pdf, alignment=Qt.AlignCenter)
                button_layout.addWidget(btn_print, alignment=Qt.AlignCenter)

                # Ajouter le layout des boutons à celui principal
                layout.addLayout(button_layout)

                # Ajouter le widget contenant le tableau et les boutons à self.main_content
                self.main_content.addWidget(container_widget)

            else:
                # Afficher un message si aucun ajourné
                no_ajournes = QLabel("⚠ Aucun candidat n'est ajourné avec moins de 153 points au deuxième tour.",
                                     alignment=Qt.AlignCenter)
                no_ajournes.setStyleSheet("font-size: 18px; color: #FF0000;")
                self.main_content.addWidget(no_ajournes)

            # Mettre à jour l'affichage en toute sécurité
            self.main_content.setCurrentIndex(self.main_content.count() - 1)

        except Exception as e:
            self.show_error_message(f"⚠ Erreur inattendue lors de l'affichage du tableau des ajournés du 2ᵉ tour : {e}")

    def generate_pdf_ajournes_2eme_tour(self, ajournes):
        """Génère un fichier PDF avec la liste des ajournés du deuxième tour sous forme de tableau"""
        try:
            # Créer un fichier PDF
            file_name = "liste_ajournes_2eme_tour.pdf"
            c = canvas.Canvas(file_name, pagesize=letter)
            width, height = letter  # Taille de la page

            # Ajouter un titre
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, height - 50, "Liste des ajournés du deuxième tour")

            # Données du tableau
            data = [["Numéro de Table", "Nom", "Prénom", "Date de Naissance", "Points"]]  # En-tête du tableau

            # Ajouter les résultats des candidats avec le total des points arrondi
            for numero_table, nom, prenom, date_naissance, total_points in ajournes:
                total_points_rounded = round(total_points, 2)
                data.append([str(numero_table), nom, prenom, date_naissance, str(total_points_rounded)])

            # Configuration de la pagination
            max_rows_per_page = 30  # Nombre max de lignes par page
            y_position = height - 100  # Position initiale du tableau
            page_number = 1  # Numéro de page

            # Séparer les données en plusieurs pages
            for i in range(0, len(data), max_rows_per_page):
                if i > 0:
                    c.showPage()  # Nouvelle page
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(100, height - 50, "Liste des ajournés du deuxième tour")

                # Récupérer les données pour la page actuelle
                data_chunk = data[i:i + max_rows_per_page]

                # Créer un tableau avec les données
                table = Table(data_chunk, colWidths=[100, 150, 150, 120, 80])  # Largeur des colonnes ajustée
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # En-tête en gris
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texte en blanc
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centrer les textes
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Police de l'en-tête
                    ('FONTSIZE', (0, 0), (-1, -1), 12),  # Taille de la police
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Espacement en bas de l'en-tête
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Fond beige pour le reste
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black)  # Bordures de tableau
                ]))

                # Dessiner le tableau sur la page
                table.wrapOn(c, width, height)
                table.drawOn(c, 50, y_position - (len(data_chunk) * 20))  # Ajuster position

                # Ajouter le numéro de page
                c.setFont("Helvetica", 10)
                c.drawString(width - 100, 30, f"Page {page_number}")
                page_number += 1

            # Sauvegarder le fichier PDF
            c.save()
            self.show_info_message(f"✅ PDF généré avec succès : {file_name}")

        except Exception as e:
            self.show_error_message(f"❌ Erreur lors de la génération du PDF : {e}")

    def print_table5(self, table):
        """Imprime le tableau"""
        try:
            # Créer un document texte pour l'impression
            document = QTextDocument()
            cursor = QTextCursor(document)

            # Créer un tableau HTML à partir des données du QTableWidget
            html = "<table border='1' cellpadding='5' cellspacing='0'><tr>"
            for col in range(table.columnCount()):
                html += f"<th>{table.horizontalHeaderItem(col).text()}</th>"
            html += "</tr>"

            for row in range(table.rowCount()):
                html += "<tr>"
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    html += f"<td>{item.text() if item else ''}</td>"
                html += "</tr>"
            html += "</table>"

            # Ajouter le tableau HTML au document
            document.setHtml(html)

            # Configurer l'impression
            printer = QPrinter()
            print_dialog = QPrintDialog(printer)
            if print_dialog.exec() == QPrintDialog.Accepted:
                document.print_(printer)  # Imprimer le document
                self.show_info_message("✅ Impression terminée avec succès.")
        except Exception as e:
            self.show_error_message(f"❌ Erreur lors de l'impression : {e}")

    def open_releve_notes_2eme_tour(self):
        print("Ouverture du relevé des notes du deuxième tour")

    # gestion de 2em tour
    def toggle_notes_2em_tour_submenu(self):
        """Affiche ou cache le sous-menu du 2e tour"""
        self.notes_2em_tour_submenu_widget.setVisible(not self.notes_2em_tour_submenu_widget.isVisible())

    def open_add_matiere_2em_tour_form(self):
        """Affiche un formulaire pour ajouter une matière du deuxième tour"""
        from PyQt5.QtWidgets import QFormLayout, QLineEdit, QSpinBox, QComboBox, QPushButton, QWidget

        self.add_matiere_2em_form = QWidget()
        form_layout = QFormLayout()

        # Champs du formulaire
        self.nom_matiere_2em_input = QLineEdit()
        self.coefficient_2em_input = QSpinBox()
        self.coefficient_2em_input.setRange(1, 10)  # Coefficient entre 1 et 10

        self.facultative_2em_input = QComboBox()
        self.facultative_2em_input.addItems(["Obligatoire", "Facultative"])

        # Ajout des champs au formulaire
        form_layout.addRow("Nom de la matière (2ᵉ Tour)", self.nom_matiere_2em_input)
        form_layout.addRow("Coefficient", self.coefficient_2em_input)
        form_layout.addRow("Facultative", self.facultative_2em_input)

        # Bouton de sauvegarde
        self.save_matiere_2em_button = QPushButton("Ajouter au Deuxième Tour")
        self.save_matiere_2em_button.clicked.connect(self.save_matiere_2em_tour)

        form_layout.addWidget(self.save_matiere_2em_button)

        self.add_matiere_2em_form.setLayout(form_layout)
        self.main_content.addWidget(self.add_matiere_2em_form)
        self.main_content.setCurrentWidget(self.add_matiere_2em_form)

    def save_matiere_2em_tour(self):
        """Ajoute une matière du deuxième tour et initialise les notes des candidats dans la table note et le relevé de notes"""
        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Vérifier que le champ nom n'est pas vide
            if not self.nom_matiere_2em_input.text().strip():
                QMessageBox.warning(self, "Champ vide", "Le nom de la matière est obligatoire.")
                return

            # Vérifier si la matière existe déjà pour le 2e tour
            cursor.execute("SELECT COUNT(*) FROM matiere WHERE nom = ? AND tour = 2",
                           (self.nom_matiere_2em_input.text(),))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "Doublon", "Cette matière existe déjà pour le 2e tour.")
                return

            # Insérer la matière (FORCÉMENT DEUXIÈME TOUR)
            cursor.execute("""
                INSERT INTO matiere (nom, coefficient, tour, facultative) 
                VALUES (?, ?, ?, ?)
            """, (
                self.nom_matiere_2em_input.text(),
                self.coefficient_2em_input.value(),
                2,  # 🔹 Deuxième tour
                1 if self.facultative_2em_input.currentText() == "Facultative" else 0
            ))

            matiere_id = cursor.lastrowid  # Récupérer l'ID de la matière insérée

            # Récupérer la liste des candidats existants
            cursor.execute("SELECT id FROM candidat")
            candidats = cursor.fetchall()

            # Ajouter une ligne dans la table note et relevé de notes pour chaque candidat
            for (candidat_id,) in candidats:
                # Initialisation des notes dans la table note
                cursor.execute("""
                    INSERT INTO note (note_premier_tour, note_deuxieme_tour, matiere_id, candidat_id)
                    VALUES (?, ?, ?, ?)
                """, (None, None, matiere_id, candidat_id))  # Notes initialisées à NULL

                # Initialisation du relevé de notes 2e tour
                cursor.execute("""
                    INSERT INTO releve_notes_2e_tour (candidat_id, matiere_id, note, points)
                    VALUES (?, ?, ?, ?)
                """, (candidat_id, matiere_id, None, 0))  # Note NULL et points à 0

            conn.commit()
            QMessageBox.information(self, "Succès", "Matière ajoutée et relevé de notes initialisé avec succès.")

            # Nettoyer les champs
            self.nom_matiere_2em_input.clear()
            self.coefficient_2em_input.setValue(1)
            self.facultative_2em_input.setCurrentIndex(0)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ajout de la matière : {e}")
        finally:
            conn.close()

    def open_liste_matieres_2em_tour(self):
        """Affiche la liste des matières du deuxième tour avec des boutons pour modifier et supprimer"""
        self.liste_matieres_2em_tour_page = QWidget()
        layout = QVBoxLayout()

        # Création d'une table pour afficher les matières du deuxième tour
        self.table_matieres_2em_tour = QTableWidget()
        self.table_matieres_2em_tour.setColumnCount(4)
        self.table_matieres_2em_tour.setHorizontalHeaderLabels(["Nom de la matière", "Coefficient", "Tour", "Actions"])

        # Appliquer la couleur noire à l'en-tête horizontal
        header = self.table_matieres_2em_tour.horizontalHeader()
        header.setStyleSheet("color: black;")

        # Remplir la table avec les matières du deuxième tour
        conn = sqlite3.connect("bfem.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, coefficient, tour FROM matiere WHERE tour = 2")
        matieres = cursor.fetchall()

        self.table_matieres_2em_tour.setRowCount(len(matieres))

        for row, (id, nom, coefficient, tour) in enumerate(matieres):
            self.table_matieres_2em_tour.setItem(row, 0, QTableWidgetItem(nom))
            self.table_matieres_2em_tour.setItem(row, 1, QTableWidgetItem(str(coefficient)))
            self.table_matieres_2em_tour.setItem(row, 2, QTableWidgetItem("Deuxième tour"))

            # Ajouter des boutons pour modifier et supprimer
            btn_modifier = QPushButton("🖊️")
            btn_modifier.clicked.connect(lambda checked, id=id: self.modify_matiere(id))
            btn_supprimer = QPushButton("🗑️")
            btn_supprimer.clicked.connect(lambda checked, id=id: self.delete_matiere(id))

            btn_layout = QHBoxLayout()
            btn_layout.addWidget(btn_modifier)
            btn_layout.addWidget(btn_supprimer)

            widget = QWidget()
            widget.setLayout(btn_layout)

            self.table_matieres_2em_tour.setCellWidget(row, 3, widget)

        layout.addWidget(self.table_matieres_2em_tour)
        self.liste_matieres_2em_tour_page.setLayout(layout)
        self.main_content.addWidget(self.liste_matieres_2em_tour_page)
        self.main_content.setCurrentWidget(self.liste_matieres_2em_tour_page)

    def modify_matiere(self, id):
        """Modifier une matière en utilisant son ID"""
        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()
            cursor.execute("SELECT nom, coefficient, facultative, tour FROM matiere WHERE id = ?", (id,))
            matiere = cursor.fetchone()

            if matiere:
                nom, coefficient, facultative, tour = matiere

                # Créer un formulaire pour modifier la matière
                self.modify_matiere_form = QWidget()
                form_layout = QFormLayout()

                self.nom_matiere_input = QLineEdit(nom)
                self.coefficient_input = QSpinBox()
                self.coefficient_input.setValue(coefficient)

                self.facultative_input = QComboBox()
                self.facultative_input.addItems(["Obligatoire", "Facultative"])
                self.facultative_input.setCurrentIndex(0 if facultative == 0 else 1)

                # Ajouter les champs au formulaire
                form_layout.addRow(f"Nom de la matière ({'1er Tour' if tour == 1 else '2ème Tour'})",
                                   self.nom_matiere_input)
                form_layout.addRow("Coefficient", self.coefficient_input)
                form_layout.addRow("Facultative", self.facultative_input)

                save_button = QPushButton("Sauvegarder")
                save_button.clicked.connect(lambda: self.save_modified_matiere(id))

                form_layout.addWidget(save_button)

                self.modify_matiere_form.setLayout(form_layout)
                self.main_content.addWidget(self.modify_matiere_form)
                self.main_content.setCurrentWidget(self.modify_matiere_form)
        except Exception as e:
            print(f"Erreur lors de la modification de la matière : {e}")

    def save_modified_matiere(self, id):
        """Sauvegarder les modifications d'une matière"""
        nom = self.nom_matiere_input.text()
        coefficient = self.coefficient_input.value()
        facultative = 1 if self.facultative_input.currentText() == "Facultative" else 0

        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()
            cursor.execute("""
                  UPDATE matiere
                  SET nom = ?, coefficient = ?, facultative = ?
                  WHERE id = ?
              """, (nom, coefficient, facultative, id))

            conn.commit()
            QMessageBox.information(self, "Succès", "Matière modifiée avec succès.")
            self.open_liste_matieres_2em_tour()  # Recharger la liste des matières
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification : {e}")
        finally:
            conn.close()

    def delete_matiere(self, id):
        """Supprimer une matière avec une boîte de dialogue de confirmation"""
        reply = QMessageBox.question(self, 'Confirmer la suppression',
                                     'Êtes-vous sûr de vouloir supprimer cette matière ?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect("bfem.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM matiere WHERE id = ?", (id,))
                conn.commit()
                self.open_liste_matieres_2em_tour()  # Recharger la liste des matières
            except Exception as e:
                print(f"Erreur lors de la suppression de la matière : {e}")

    def open_add_note_2em_tour_form(self):
        """Ouvre le formulaire pour ajouter une note pour un candidat (2e tour)."""
        try:
            self.form_window = QWidget()
            self.form_window.setWindowTitle("Ajouter une Note - 2e Tour")
            layout = QVBoxLayout()

            # Sélection du candidat par anonymat
            self.anonymat_combo = QComboBox()
            self.load_candidats()  # Charge les candidats dans le comboBox
            layout.addWidget(QLabel("Sélectionner un candidat (Anonymat)"))
            layout.addWidget(self.anonymat_combo)

            # Récupération des matières du deuxième tour
            self.notes_inputs = {}
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nom FROM matiere WHERE tour = 2")  # 🔹 Sélection uniquement des matières du 2e tour
            matieres = cursor.fetchall()
            conn.close()

            # Ajouter un champ pour chaque matière avec un QDoubleSpinBox pour les notes
            for matiere_id, matiere_nom in matieres:
                note_label = QLabel(f"{matiere_nom}:")  # Afficher le nom de la matière
                note_input = QDoubleSpinBox()
                note_input.setRange(0, 20)  # Plage des notes de 0 à 20
                note_input.setDecimals(2)  # Permet des décimales
                note_input.setSingleStep(0.1)  # Incrément de 0.1

                layout.addWidget(note_label)
                layout.addWidget(note_input)  # Ajoute le champ de saisie
                self.notes_inputs[matiere_id] = note_input  # Associe l'input à la matière via son ID

            # Bouton de soumission
            btn_enregistrer = QPushButton("✅ Enregistrer", clicked=self.enregistrer_note_2e_tour)
            layout.addWidget(btn_enregistrer)

            self.form_window.setLayout(layout)

            # Afficher le formulaire dans le main_content
            self.main_content.addWidget(self.form_window)
            self.main_content.setCurrentWidget(self.form_window)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de base de données lors du chargement des matières : {e}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {e}")

    def enregistrer_note_2e_tour(self):
        """Enregistre les notes du candidat sélectionné (2e tour) et met à jour le relevé de notes."""
        anonymat = self.anonymat_combo.currentText()
        conn = sqlite3.connect("bfem.db")
        cursor = conn.cursor()

        # Récupérer l'ID du candidat via son anonymat
        cursor.execute("SELECT id FROM candidat WHERE anonymat = ?", (anonymat,))
        candidat = cursor.fetchone()
        if not candidat:
            QMessageBox.critical(self, "Erreur", "Candidat introuvable !")
            return

        candidat_id = candidat[0]

        # Enregistrement des notes et mise à jour des points
        try:
            for matiere_id, note_input in self.notes_inputs.items():
                note = note_input.value()

                # Vérifier si la note est bien entre 0 et 20
                if note < 0 or note > 20:
                    QMessageBox.warning(self, "Valeur incorrecte",
                                        f"La note {note} pour la matière {matiere_id} est invalide.")
                    continue

                # Récupérer le coefficient de la matière
                cursor.execute("SELECT coefficient FROM matiere WHERE id = ?", (matiere_id,))
                matiere = cursor.fetchone()
                if not matiere:
                    QMessageBox.critical(self, "Erreur", "Matière introuvable !")
                    return

                coefficient = matiere[0]
                points = note * coefficient  # Calcul des points

                # Mettre à jour la note dans la table "note"
                cursor.execute("""
                    UPDATE note 
                    SET note_deuxieme_tour = ? 
                    WHERE matiere_id = ? AND candidat_id = ?
                """, (note, matiere_id, candidat_id))

                # Vérifier si une entrée existe déjà dans releve_notes_2e_tour
                cursor.execute("""
                    SELECT COUNT(*) FROM releve_notes_2e_tour 
                    WHERE candidat_id = ? AND matiere_id = ?
                """, (candidat_id, matiere_id))
                exists = cursor.fetchone()[0]

                if exists:
                    # Mettre à jour la note et les points dans releve_notes_2e_tour
                    cursor.execute("""
                        UPDATE releve_notes_2e_tour 
                        SET note = ?, points = ? 
                        WHERE candidat_id = ? AND matiere_id = ?
                    """, (note, points, candidat_id, matiere_id))
                else:
                    # Insérer une nouvelle entrée dans releve_notes_2e_tour
                    cursor.execute("""
                        INSERT INTO releve_notes_2e_tour (candidat_id, matiere_id, note, points) 
                        VALUES (?, ?, ?, ?)
                    """, (candidat_id, matiere_id, note, points))

            conn.commit()
            QMessageBox.information(self, "Succès",
                                    "Notes du 2e tour enregistrées et relevé de notes mis à jour avec succès !")
            self.form_window.close()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {e}")
        finally:
            conn.close()

    def open_liste_notes_2em_tour(self):
        """Affiche la liste des notes du 2e tour"""
        try:
            self.liste_window = QWidget()
            self.liste_window.setWindowTitle("Liste des Notes - 2e Tour")
            layout = QVBoxLayout()

            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Récupérer toutes les matières du 2e tour
            cursor.execute("SELECT id, nom FROM matiere WHERE tour = 2 ORDER BY id")
            matieres = cursor.fetchall()
            matiere_ids = [m[0] for m in matieres]
            matiere_noms = [m[1] for m in matieres]

            # Récupérer tous les candidats anonymes
            cursor.execute("SELECT id, anonymat FROM candidat ORDER BY anonymat")
            candidats = cursor.fetchall()
            candidat_ids = [c[0] for c in candidats]
            candidat_anonymats = [c[1] for c in candidats]

            # Vérifier si on a des candidats et des matières
            if not candidats or not matieres:
                QMessageBox.warning(self, "Aucune donnée",
                                    "Aucun candidat ou matière disponible pour afficher les notes.")
                return

            # Création du tableau avec une colonne "Actions"
            self.table = QTableWidget()
            self.table.setRowCount(len(candidats))
            self.table.setColumnCount(len(matiere_noms) + 2)  # +1 pour "Anonymat" et +1 pour Actions

            # Définir les en-têtes de colonnes (Matières + "Anonymat" en premier + Actions)
            self.table.setHorizontalHeaderLabels(["Anonymat"] + matiere_noms + ["Actions"])

            # Appliquer la couleur noire à l'en-tête horizontal
            header = self.table.horizontalHeader()
            header.setStyleSheet("color: black;")

            # Définir les en-têtes de lignes (Candidats Anonymes)
            for row_idx, anonymat in enumerate(candidat_anonymats):
                self.table.setVerticalHeaderItem(row_idx, QTableWidgetItem(str(anonymat)))

            # Charger les notes du second tour et les placer dans le tableau
            for row_idx, candidat_id in enumerate(candidat_ids):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(candidat_anonymats[row_idx])))  # Colonne "Anonymat"

                for col_idx, matiere_id in enumerate(matiere_ids):
                    cursor.execute("""
                        SELECT note_deuxieme_tour FROM note 
                        WHERE candidat_id = ? AND matiere_id = ?
                    """, (candidat_id, matiere_id))
                    note = cursor.fetchone()
                    note_value = str(note[0]) if note and note[0] is not None else "-"

                    self.table.setItem(row_idx, col_idx + 1, QTableWidgetItem(note_value))  # +1 pour "Anonymat"

                # Ajouter le bouton Modifier 🖊️
                btn_modifier = QPushButton("🖊️ Modifier")
                btn_modifier.clicked.connect(lambda checked, c_id=candidat_id: self.modifier_note2(c_id))

                # Ajout du bouton dans une cellule
                btn_layout = QHBoxLayout()
                btn_layout.addWidget(btn_modifier)

                widget = QWidget()
                widget.setLayout(btn_layout)
                self.table.setCellWidget(row_idx, len(matiere_noms) + 1, widget)  # Dernière colonne

            conn.close()

            # ✅ Redimensionner les colonnes
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
            self.table.setMinimumSize(800, 400)

            # Ajouter le tableau au layout et afficher
            layout.addWidget(self.table)
            self.liste_window.setLayout(layout)
            self.main_content.addWidget(self.liste_window)
            self.main_content.setCurrentWidget(self.liste_window)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des notes : {e}")

    def modifier_note2(self, candidat_id):
        """Ouvre un formulaire pour modifier les notes des matières du 2e tour d'un candidat."""
        try:
            self.form_modif_note = QWidget()
            self.form_modif_note.setWindowTitle("Modifier les Notes - 2e Tour")
            layout = QVBoxLayout()

            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Récupérer uniquement les matières du 2e tour et les notes actuelles du candidat
            cursor.execute("""
                SELECT m.id, m.nom, n.note_deuxieme_tour
                FROM matiere m
                LEFT JOIN note n ON m.id = n.matiere_id AND n.candidat_id = ?
                WHERE m.tour = 2
            """, (candidat_id,))
            matieres_notes = cursor.fetchall()
            conn.close()

            self.notes_inputs = {}

            # Ajouter un champ pour chaque matière du 2e tour
            for matiere_id, matiere_nom, note in matieres_notes:
                note_label = QLabel(f"{matiere_nom}:")
                note_input = QDoubleSpinBox()
                note_input.setRange(0, 20)
                note_input.setDecimals(2)
                note_input.setSingleStep(0.1)
                note_input.setValue(note if note is not None else 0)

                layout.addWidget(note_label)
                layout.addWidget(note_input)
                self.notes_inputs[matiere_id] = note_input

            # Bouton de sauvegarde
            btn_sauvegarder = QPushButton("✅ Sauvegarder")
            btn_sauvegarder.clicked.connect(lambda: self.sauvegarder_modifications_note(candidat_id))

            layout.addWidget(btn_sauvegarder)
            self.form_modif_note.setLayout(layout)

            # Afficher la fenêtre de modification
            self.main_content.addWidget(self.form_modif_note)
            self.main_content.setCurrentWidget(self.form_modif_note)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture du formulaire : {e}")

    # resulta 1er tour

    def toggle_resultats_submenu(self):
        """Afficher ou masquer le sous-menu des résultats du premier tour"""
        is_visible = self.resultats_submenu_widget.isVisible()
        self.resultats_submenu_widget.setVisible(not is_visible)

    def open_deliberation(self):
        """Affiche la page de délibération du premier tour"""
        try:
            # Connexion à la base de données
            conn = sqlite3.connect('bfem.db')
            cursor = conn.cursor()

            # Récupérer tous les candidats
            cursor.execute("""SELECT c.id, c.nom, c.prenom FROM candidat c""")
            candidats = cursor.fetchall()

            for candidat in candidats:
                candidat_id = candidat[0]

                # Récupérer les notes du candidat pour le premier tour
                cursor.execute("""
                    SELECT r.note, m.coefficient
                    FROM releve_notes_1er_tour r
                    JOIN matiere m ON r.matiere_id = m.id
                    WHERE r.candidat_id = ?
                """, (candidat_id,))
                notes = cursor.fetchall()

                total_points = 0
                total_coefficients = 0  # Somme des coefficients
                for note, coefficient in notes:
                    total_points += note * coefficient  # Total des points (note * coefficient)
                    total_coefficients += coefficient  # Additionner les coefficients

                # Application de la règle RM2 : Bonus ou malus pour EPS
                cursor.execute("""
                    SELECT note
                    FROM releve_notes_1er_tour r
                    JOIN matiere m ON r.matiere_id = m.id
                    WHERE r.candidat_id = ? AND m.nom = 'EPS'
                """, (candidat_id,))
                eps_note = cursor.fetchone()
                if eps_note:
                    if eps_note[0] > 10:
                        total_points += (eps_note[0] - 10)  # Bonus pour EPS
                    else:
                        total_points -= (10 - eps_note[0])  # Malus pour EPS

                # Application de la règle RM3 : Bonus pour épreuve facultative
                cursor.execute("""
                    SELECT note
                    FROM releve_notes_1er_tour r
                    JOIN matiere m ON r.matiere_id = m.id
                    WHERE r.candidat_id = ? AND m.nom = 'Facultatif'
                """, (candidat_id,))
                facultatif_note = cursor.fetchone()
                if facultatif_note and facultatif_note[0] > 10:
                    total_points += facultatif_note[0] - 10  # Bonus pour épreuve facultative

                # Calcul de la moyenne en divisant le total des points par la somme des coefficients
                if total_coefficients > 0:
                    moyenne = total_points / total_coefficients  # Moyenne générale basée sur les coefficients
                else:
                    moyenne = 0  # Si pas de matières, la moyenne est 0 (cas rare)

                # Assurer que la moyenne est dans la plage autorisée
                if moyenne < 0:
                    moyenne = 0
                elif moyenne > 20:
                    moyenne = 20

                # Détermination du statut (admis d'office, admissible, ajourné)
                if total_points >= 180:
                    presentation = 'Admis d\'office'
                    repechable = 0  # Pas repêchable
                elif total_points >= 153:
                    presentation = 'Admissible'
                    repechable = 0  # Pas repêchable
                elif total_points < 153:
                    presentation = 'Ajourné'
                    repechable = 0  # Pas repêchable
                else:
                    presentation = 'Inconnu'
                    repechable = 0

                # Règles de repêchage RM7, RM8, RM9
                if total_points >= 171 and total_points < 180:
                    repechable = 1
                elif total_points >= 144 and total_points < 153:
                    repechable = 1
                if moyenne >= 12:
                    repechable = 1

                # Mise à jour des résultats dans la table 'resultat'
                cursor.execute("""
                    UPDATE resultat
                    SET total_points = ?, moyenne = ?, repechable = ?, presentation = ?
                    WHERE candidat_id = ?
                """, (total_points, moyenne, repechable, presentation, candidat_id))

                # Committer les changements pour chaque candidat
                conn.commit()

            # Fermer la connexion
            conn.close()

            # Ajouter un message dans l'interface
            self.deliberation_page = QLabel("⚖️ Délibération du Premier Tour terminée", alignment=Qt.AlignCenter)
            self.deliberation_page.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFA500;")
            self.main_content.addWidget(self.deliberation_page)
            self.main_content.setCurrentWidget(self.deliberation_page)

        except sqlite3.Error as e:
            self.show_error_message(f"Erreur lors de la délibération : {e}")

    def show_error_message(self, message):
        """Affiche un message d'erreur"""
        error_label = QLabel(message, alignment=Qt.AlignCenter)
        error_label.setStyleSheet("font-size: 18px; font-weight: bold; color: red;")
        self.main_content.addWidget(error_label)
        self.main_content.setCurrentWidget(error_label)

    def open_liste_admis(self):
        """Affiche la liste des admis (180 points et plus)"""
        try:
            # Connexion à la base de données
            conn = sqlite3.connect('bfem.db')
            cursor = conn.cursor()

            # Récupérer les candidats admis (triés par ordre de mérite)
            cursor.execute("""
                SELECT c.id, c.numero_table, c.nom, c.prenom, r.total_points
                FROM resultat r
                JOIN candidat c ON r.candidat_id = c.id
                WHERE r.total_points >= 180
                ORDER BY r.total_points DESC
            """)
            admis = cursor.fetchall()

        except sqlite3.Error as e:
            self.show_error_message(f"❌ Erreur SQLite lors de la récupération des admis : {e}")
            return  # Stopper l'exécution en cas d'erreur SQL

        finally:
            if conn:
                conn.close()  # Fermer la connexion

        try:
            # Supprimer tout ce qui est affiché avant d'ajouter du nouveau contenu
            for i in reversed(range(self.main_content.count())):
                widget = self.main_content.widget(i)
                if widget:
                    widget.setParent(None)

            if admis:
                # Création d'un QWidget parent pour contenir le tableau et les boutons
                container_widget = QWidget()

                # Création du tableau pour afficher les résultats
                table = QTableWidget()
                table.setRowCount(len(admis))
                table.setColumnCount(5)  # 5 Colonnes (Numéro de table, Nom, Prénom, Total Points, Relevé de Notes)
                table.setHorizontalHeaderLabels(["Numéro Table", "Nom", "Prénom", "Total Points", "Relevé"])
                table.setStyleSheet("""
                    font-size: 16px;
                    border: 1px solid #ccc;
                    background-color: #f9f9f9;
                    selection-background-color: #8BC34A;
                    selection-color: white;
                """)

                # Styliser les titres de colonnes
                table.horizontalHeader().setStyleSheet("""
                color: black;  /* Texte en noir */
                font-weight: bold;  /* Mettre en gras */
                """)

                # Styliser les cellules
                table.setStyleSheet("""
                    QTableWidget::item {
                        border: 1px solid #ccc;
                        padding: 10px;
                    }
                    QTableWidget::item:selected {
                        background-color: #4CAF50;
                        color: white;
                    }
                """)

                # Remplir le tableau avec les données des admis
                for row, (candidat_id, numero_table, nom, prenom, total_points) in enumerate(admis):
                    # Arrondir le total des points à 2 décimales
                    total_points_rounded = round(total_points, 2)
                    table.setItem(row, 0, QTableWidgetItem(str(numero_table)))
                    table.setItem(row, 1, QTableWidgetItem(nom))
                    table.setItem(row, 2, QTableWidgetItem(prenom))
                    table.setItem(row, 3, QTableWidgetItem(str(total_points_rounded)))

                    # Ajouter le bouton pour voir le relevé de notes
                    btn_releve = QPushButton("📄")
                    btn_releve.clicked.connect(partial(self.voir_releve_notes, candidat_id))
                    table.setCellWidget(row, 4, btn_releve)

                # Ajustements pour améliorer l'affichage du tableau
                table.horizontalHeader().setStretchLastSection(True)  # Ajuste la largeur des colonnes
                table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Désactive l'édition des cellules

                # Création du layout pour le tableau et les boutons
                layout = QVBoxLayout(container_widget)  # Utilisation d'un QVBoxLayout pour empiler les éléments

                # Ajouter le tableau au layout
                layout.addWidget(table)

                # Créer un layout horizontal pour les boutons
                button_layout = QHBoxLayout()

                # Ajouter le bouton pour générer le PDF
                btn_generate_pdf = QPushButton("📑 Générer PDF des admis", clicked=lambda: self.generate_pdf(admis))
                btn_generate_pdf.setStyleSheet(
                    "background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
                btn_generate_pdf.setFixedWidth(250)  # Limiter la largeur du bouton

                # Ajouter le bouton pour imprimer
                btn_print = QPushButton("🖨️ Imprimer la liste", clicked=lambda: self.print_table(table))
                btn_print.setStyleSheet(
                    "background-color: #2196F3; color: white; padding: 10px; border-radius: 5px;")
                btn_print.setFixedWidth(250)  # Limiter la largeur du bouton

                # Ajouter les boutons au layout horizontal
                button_layout.addWidget(btn_generate_pdf, alignment=Qt.AlignCenter)
                button_layout.addWidget(btn_print, alignment=Qt.AlignCenter)

                # Ajouter le layout des boutons à celui principal
                layout.addLayout(button_layout)

                # Ajouter le widget contenant le tableau et les boutons à self.main_content
                self.main_content.addWidget(container_widget)

            else:
                # Afficher un message si aucun admis
                no_admis = QLabel("⚠ Aucun candidat n'a obtenu 180 points ou plus.", alignment=Qt.AlignCenter)
                no_admis.setStyleSheet("font-size: 18px; color: #FF0000;")
                self.main_content.addWidget(no_admis)

            # Mettre à jour l'affichage en toute sécurité
            self.main_content.setCurrentIndex(self.main_content.count() - 1)

        except Exception as e:
            self.show_error_message(f"⚠ Erreur inattendue lors de l'affichage du tableau : {e}")

    def print_table(self, table):
        """Imprime le tableau"""
        try:
            # Créer un document texte pour l'impression
            document = QTextDocument()
            cursor = QTextCursor(document)

            # Créer un tableau HTML à partir des données du QTableWidget
            html = "<table border='1' cellpadding='5' cellspacing='0'><tr>"
            for col in range(table.columnCount()):
                html += f"<th>{table.horizontalHeaderItem(col).text()}</th>"
            html += "</tr>"

            for row in range(table.rowCount()):
                html += "<tr>"
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    html += f"<td>{item.text() if item else ''}</td>"
                html += "</tr>"
            html += "</table>"

            # Ajouter le tableau HTML au document
            document.setHtml(html)

            # Configurer l'impression
            printer = QPrinter()
            print_dialog = QPrintDialog(printer)
            if print_dialog.exec() == QPrintDialog.Accepted:
                document.print_(printer)  # Imprimer le document
                self.show_info_message("✅ Impression terminée avec succès.")
        except Exception as e:
            self.show_error_message(f"❌ Erreur lors de l'impression : {e}")

    def generate_pdf(self, admis):
        """Génère un fichier PDF avec la liste des admis sous forme de tableau, avec gestion des pages."""
        try:
            file_name = "liste_admis.pdf"
            c = canvas.Canvas(file_name, pagesize=letter)
            width, height = letter

            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, height - 50, "Liste des admis au premier tour")

            data = [["Numéro de Table", "Nom", "Prénom", "Total Points"]]

            for numero_table, nom, prenom, total_points in admis:
                total_points_rounded = round(total_points, 2)
                data.append([str(numero_table), nom, prenom, str(total_points_rounded)])

            max_rows_per_page = 25
            y_position = height - 100
            page_number = 1

            for i in range(0, len(data), max_rows_per_page):
                if i > 0:
                    c.showPage()
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(100, height - 50, "Liste des admis au premier tour")

                data_chunk = data[i:i + max_rows_per_page]

                table = Table(data_chunk, colWidths=[100, 150, 150, 100])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
                ]))

                table.wrapOn(c, width, height)
                table.drawOn(c, 50, y_position - (len(data_chunk) * 20))

                c.setFont("Helvetica", 10)
                c.drawString(width - 100, 30, f"Page {page_number}")
                page_number += 1

            c.save()
            self.show_info_message(f"✅ PDF généré avec succès : {file_name}")

        except Exception as e:
            self.show_error_message(f"❌ Erreur lors de la génération du PDF : {e}")

    def voir_releve_notes(self, candidat_id):
        """Affiche le relevé de notes d'un candidat dans une boîte de dialogue avec options PDF et impression."""

        try:
            # Connexion à la base de données
            conn = sqlite3.connect('bfem.db')
            cursor = conn.cursor()

            # Récupérer les infos du candidat
            cursor.execute("""
                SELECT c.numero_table, c.nom, c.prenom, r.total_points, r.moyenne
                FROM candidat c
                JOIN resultat r ON c.id = r.candidat_id
                WHERE c.id = ?
            """, (candidat_id,))
            candidat = cursor.fetchone()

            if not candidat:
                self.show_error_message("⚠ Candidat introuvable.")
                return

            numero_table, nom, prenom, total_points, moyenne = candidat

            # Récupérer les notes des deux tours et fusionner en une seule colonne pour chaque matière
            cursor.execute("""
                SELECT m.nom, n.note_premier_tour, n.note_deuxieme_tour, m.coefficient
                FROM note n
                JOIN matiere m ON n.matiere_id = m.id
                WHERE n.candidat_id = ?
                ORDER BY m.nom
            """, (candidat_id,))
            notes = cursor.fetchall()

        except sqlite3.Error as e:
            self.show_error_message(f"❌ Erreur SQLite : {e}")
            return

        finally:
            if conn:
                conn.close()

        # Création d'une boîte de dialogue
        dialog = QDialog(self)
        dialog.setWindowTitle(f"📜 Relevé de Notes - {prenom} {nom}")
        dialog.setFixedSize(600, 500)

        layout = QVBoxLayout()

        # Ajouter un titre avec texte blanc
        title = QLabel(f"📜 Relevé de Notes de {prenom} {nom} (Table : {numero_table})")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; text-align: center;")
        layout.addWidget(title)

        # Tableau des notes
        table = QTableWidget()
        table.setRowCount(len(notes))
        table.setColumnCount(3)  # Une colonne de moins pour la note
        table.setHorizontalHeaderLabels(["Matière", "Note", "Coeff"])

        for row, (matiere, note1, note2, coefficient) in enumerate(notes):
            # Fusionner les notes en une seule colonne (note du 1er ou du 2e tour, selon la disponibilité)
            note_affichee = note1 if note1 is not None else note2
            table.setItem(row, 0, QTableWidgetItem(matiere))
            table.setItem(row, 1, QTableWidgetItem(str(note_affichee) if note_affichee else "-"))
            table.setItem(row, 2, QTableWidgetItem(str(coefficient)))

        table.setStyleSheet(
            "font-size: 14px; border: 1px solid #ccc; background-color: #f9f9f9; color: black;")  # Texte en noir
        layout.addWidget(table)

        # Total Points & Moyenne
        total_label = QLabel(f"🎯 Total Points : {total_points}   📊 Moyenne : {moyenne}")
        total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")  # Texte en noir
        layout.addWidget(total_label)

        # Boutons (Générer PDF, Imprimer, Fermer)
        btn_layout = QHBoxLayout()

        btn_pdf = QPushButton("📄 Générer PDF")
        btn_pdf.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; border-radius: 5px;")
        btn_pdf.clicked.connect(lambda: self.generer_pdf(prenom, nom, numero_table, notes, total_points, moyenne))

        btn_print = QPushButton("🖨️ Imprimer")
        btn_print.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
        btn_print.clicked.connect(lambda: self.imprimer_releve(dialog))

        btn_close = QPushButton("❌ Fermer")
        btn_close.setStyleSheet("background-color: #FF5722; color: white; padding: 10px; border-radius: 5px;")
        btn_close.clicked.connect(dialog.close)

        btn_layout.addWidget(btn_pdf)
        btn_layout.addWidget(btn_print)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec_()

    def generer_pdf(self, prenom, nom, numero_table, notes, total_points, moyenne):
        """Génère un relevé de notes en PDF."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)

        pdf.cell(200, 10, f"Relevé de Notes - {prenom} {nom} (Table {numero_table})", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(60, 10, "Matière", border=1)
        pdf.cell(40, 10, "1er Tour", border=1)
        pdf.cell(40, 10, "2e Tour", border=1)
        pdf.cell(30, 10, "Coeff", border=1)
        pdf.ln()

        pdf.set_font("Arial", "", 12)
        for matiere, note1, note2, coeff in notes:
            pdf.cell(60, 10, matiere, border=1)
            pdf.cell(40, 10, str(note1) if note1 else "-", border=1)
            pdf.cell(40, 10, str(note2) if note2 else "-", border=1)
            pdf.cell(30, 10, str(coeff), border=1)
            pdf.ln()

        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, f"🎯 Total Points : {total_points}   📊 Moyenne : {moyenne}", ln=True, align="C")

        # Enregistrement du fichier PDF
        filename, _ = QFileDialog.getSaveFileName(None, "Enregistrer le PDF", f"Releve_{prenom}_{nom}.pdf",
                                                  "PDF Files (*.pdf)")
        if filename:
            pdf.output(filename)
            self.show_success_message(f"📄 PDF enregistré : {filename}")

    def imprimer_releve(self, dialog):
        """Imprime le relevé de notes affiché."""
        printer = QPrinter()
        print_dialog = QPrintDialog(printer, dialog)

        if print_dialog.exec_() == QPrintDialog.Accepted:
            dialog.render(printer)

    def show_info_message(self, message):
        """Affiche un message d'information"""
        info_dialog = QDialog(self)
        info_dialog.setWindowTitle("Information")
        info_dialog.setFixedSize(300, 150)

        label = QLabel(message, info_dialog)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: green;")

        layout = QVBoxLayout(info_dialog)
        layout.addWidget(label)

        button = QPushButton("OK", info_dialog)
        button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; border-radius: 5px;")
        button.clicked.connect(info_dialog.accept)

        layout.addWidget(button)

        info_dialog.exec_()

    def open_liste_admissibles(self):
        """Affiche la liste des candidats admissibles au 2e tour (153 - 179,9 points)"""
        try:
            # Connexion à la base de données
            conn = sqlite3.connect('bfem.db')
            cursor = conn.cursor()

            # Récupérer les candidats admissibles (total_points entre 153 et 179.9)
            cursor.execute("""
                SELECT c.id, c.numero_table, c.nom, c.prenom, c.date_naissance, r.total_points
                FROM resultat r
                JOIN candidat c ON r.candidat_id = c.id
                WHERE r.total_points BETWEEN 153 AND 179.9
                ORDER BY r.total_points DESC
            """)
            admissibles = cursor.fetchall()

        except sqlite3.Error as e:
            self.show_error_message(f"❌ Erreur SQLite lors de la récupération des admissibles : {e}")
            return  # Stopper l'exécution en cas d'erreur SQL

        finally:
            if conn:
                conn.close()  # Fermer la connexion

        try:
            # Supprimer tout ce qui est affiché avant d'ajouter du nouveau contenu
            for i in reversed(range(self.main_content.count())):
                widget = self.main_content.widget(i)
                if widget:
                    widget.setParent(None)

            if admissibles:
                # Création d'un QWidget parent pour contenir le tableau et les boutons
                container_widget = QWidget()

                # Création du tableau pour afficher les résultats
                table = QTableWidget()
                table.setRowCount(len(admissibles))
                table.setColumnCount(6)  # 6 Colonnes (Numéro Table, Nom, Prénom, Date de Naissance, Points, Relevé)
                table.setHorizontalHeaderLabels(
                    ["Numéro Table", "Nom", "Prénom", "Date de Naissance", "Total Points", "Relevé"])
                table.setStyleSheet("""
                    font-size: 16px;
                    border: 1px solid #ccc;
                    background-color: #f9f9f9;
                    selection-background-color: #8BC34A;
                    selection-color: white;
                """)

                # Styliser les titres de colonnes
                table.horizontalHeader().setStyleSheet("""
                    color: black;  /* Texte en noir */
                    font-weight: bold;  /* Mettre en gras */
                """)

                # Styliser les cellules
                table.setStyleSheet("""
                    QTableWidget::item {
                        border: 1px solid #ccc;
                        padding: 10px;
                    }
                    QTableWidget::item:selected {
                        background-color: #4CAF50;
                        color: white;
                    }
                """)

                # Remplir le tableau avec les données des admissibles
                for row, (candidat_id, numero_table, nom, prenom, date_naissance, total_points) in enumerate(
                        admissibles):
                    # Arrondir le total des points à 2 décimales
                    total_points_rounded = round(total_points, 2)
                    table.setItem(row, 0, QTableWidgetItem(str(numero_table)))
                    table.setItem(row, 1, QTableWidgetItem(nom))
                    table.setItem(row, 2, QTableWidgetItem(prenom))
                    table.setItem(row, 3, QTableWidgetItem(date_naissance))
                    table.setItem(row, 4, QTableWidgetItem(str(total_points_rounded)))

                    # Ajouter le bouton pour voir le relevé de notes
                    btn_releve = QPushButton("📄")
                    btn_releve.clicked.connect(partial(self.voir_releve_notes, candidat_id))
                    table.setCellWidget(row, 5, btn_releve)

                # Ajustements pour améliorer l'affichage du tableau
                table.horizontalHeader().setStretchLastSection(True)  # Ajuste la largeur des colonnes
                table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Désactive l'édition des cellules

                # Création du layout pour le tableau et les boutons
                layout = QVBoxLayout(container_widget)  # Utilisation d'un QVBoxLayout pour empiler les éléments

                # Ajouter le tableau au layout
                layout.addWidget(table)

                # Créer un layout horizontal pour les boutons
                button_layout = QHBoxLayout()

                # Ajouter le bouton pour générer le PDF
                btn_generate_pdf = QPushButton("📑 Générer PDF des admissibles",
                                               clicked=lambda: self.generate_pdf_admissibles(admissibles))
                btn_generate_pdf.setStyleSheet(
                    "background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
                btn_generate_pdf.setFixedWidth(250)  # Limiter la largeur du bouton

                # Ajouter le bouton pour imprimer
                btn_print = QPushButton("🖨️ Imprimer la liste", clicked=lambda: self.print_table(table))
                btn_print.setStyleSheet(
                    "background-color: #2196F3; color: white; padding: 10px; border-radius: 5px;")
                btn_print.setFixedWidth(250)  # Limiter la largeur du bouton

                # Ajouter les boutons au layout horizontal
                button_layout.addWidget(btn_generate_pdf, alignment=Qt.AlignCenter)
                button_layout.addWidget(btn_print, alignment=Qt.AlignCenter)

                # Ajouter le layout des boutons à celui principal
                layout.addLayout(button_layout)

                # Ajouter le widget contenant le tableau et les boutons à self.main_content
                self.main_content.addWidget(container_widget)

            else:
                # Afficher un message si aucun admissible
                no_admissibles = QLabel("⚠ Aucun candidat n'est admissible avec des points entre 153 et 179,9.",
                                        alignment=Qt.AlignCenter)
                no_admissibles.setStyleSheet("font-size: 18px; color: #FF0000;")
                self.main_content.addWidget(no_admissibles)

            # Mettre à jour l'affichage en toute sécurité
            self.main_content.setCurrentIndex(self.main_content.count() - 1)

        except Exception as e:
            self.show_error_message(f"⚠ Erreur inattendue lors de l'affichage du tableau : {e}")

    def print_table(self, table):
        """Imprime le tableau"""
        try:
            # Créer un document texte pour l'impression
            document = QTextDocument()
            cursor = QTextCursor(document)

            # Créer un tableau HTML à partir des données du QTableWidget
            html = "<table border='1' cellpadding='5' cellspacing='0'><tr>"
            for col in range(table.columnCount()):
                html += f"<th>{table.horizontalHeaderItem(col).text()}</th>"
            html += "</tr>"

            for row in range(table.rowCount()):
                html += "<tr>"
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    html += f"<td>{item.text() if item else ''}</td>"
                html += "</tr>"
            html += "</table>"

            # Ajouter le tableau HTML au document
            document.setHtml(html)

            # Configurer l'impression
            printer = QPrinter()
            print_dialog = QPrintDialog(printer)
            if print_dialog.exec() == QPrintDialog.Accepted:
                document.print_(printer)  # Imprimer le document
                self.show_info_message("✅ Impression terminée avec succès.")
        except Exception as e:
            self.show_error_message(f"❌ Erreur lors de l'impression : {e}")

    def generate_pdf_admissibles(self, admissibles):
        """Génère un fichier PDF avec la liste des admissibles sous forme de tableau, avec gestion des pages."""
        try:
            # Créer un fichier PDF
            file_name = "liste_admissibles.pdf"
            c = canvas.Canvas(file_name, pagesize=letter)
            width, height = letter  # Taille de la page

            # Ajouter un titre
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, height - 50, "Liste des candidats admissibles au 2e tour")

            # Données du tableau
            data = [["Numéro de Table", "Nom", "Prénom", "Date de Naissance", "Points"]]  # En-tête du tableau

            # Ajouter les résultats des candidats avec le total des points arrondi
            for candidat_id, numero_table, nom, prenom, date_naissance, total_points in admissibles:
                total_points_rounded = round(total_points, 2)
                data.append([str(numero_table), nom, prenom, date_naissance, str(total_points_rounded)])

            # Configuration de la pagination
            max_rows_per_page = 25  # Nombre de lignes max par page
            y_position = height - 100  # Position initiale du tableau
            page_number = 1  # Numéro de page

            # Séparer les données en plusieurs pages
            for i in range(0, len(data), max_rows_per_page):
                if i > 0:
                    c.showPage()  # Nouvelle page
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(100, height - 50, "Liste des candidats admissibles au 2e tour")

                # Récupérer les données pour la page actuelle
                data_chunk = data[i:i + max_rows_per_page]

                # Créer un tableau avec les données
                table = Table(data_chunk, colWidths=[100, 80, 150, 100, 80])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # En-tête en gris
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texte en blanc
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centrer les textes
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Police de l'en-tête
                    ('FONTSIZE', (0, 0), (-1, -1), 12),  # Taille de la police
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Espacement en bas de l'en-tête
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Fond beige pour le reste
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black)  # Bordures de tableau
                ]))

                # Dessiner le tableau sur la page
                table.wrapOn(c, width, height)
                table.drawOn(c, 50, y_position - (len(data_chunk) * 20))  # Ajustement position

                # Ajouter le numéro de page
                c.setFont("Helvetica", 10)
                c.drawString(width - 100, 30, f"Page {page_number}")
                page_number += 1

            # Sauvegarder le fichier PDF
            c.save()
            self.show_info_message(f"✅ PDF généré avec succès : {file_name}")

        except Exception as e:
            self.show_error_message(f"❌ Erreur lors de la génération du PDF : {e}")


    def open_liste_ajournes(self):
        """Affiche la liste des ajournés (moins de 153 points)"""
        try:
            # Connexion à la base de données
            conn = sqlite3.connect('bfem.db')
            cursor = conn.cursor()

            # Récupérer les candidats ajournés (total_points inférieur à 153)
            cursor.execute("""
                SELECT c.id, c.numero_table, c.nom, c.prenom, c.date_naissance, r.total_points
                FROM resultat r
                JOIN candidat c ON r.candidat_id = c.id
                WHERE r.total_points < 153
                ORDER BY r.total_points ASC
            """)
            ajournes = cursor.fetchall()

        except sqlite3.Error as e:
            self.show_error_message(f"❌ Erreur SQLite lors de la récupération des ajournés : {e}")
            return  # Stopper l'exécution en cas d'erreur SQL

        finally:
            if conn:
                conn.close()  # Fermer la connexion

        try:
            # Supprimer tout ce qui est affiché avant d'ajouter du nouveau contenu
            for i in reversed(range(self.main_content.count())):
                widget = self.main_content.widget(i)
                if widget:
                    widget.setParent(None)

            if ajournes:
                # Création d'un QWidget parent pour contenir le tableau et les boutons
                container_widget = QWidget()

                # Création du tableau pour afficher les résultats
                table = QTableWidget()
                table.setRowCount(len(ajournes))
                table.setColumnCount(6)  # 6 Colonnes (Numéro Table, Nom, Prénom, Date de Naissance, Points, Relevé)
                table.setHorizontalHeaderLabels(
                    ["Numéro Table", "Nom", "Prénom", "Date de Naissance", "Total Points", "Relevé"])
                table.setStyleSheet("""
                    font-size: 16px;
                    border: 1px solid #ccc;
                    background-color: #f9f9f9;
                    selection-background-color: #8BC34A;
                    selection-color: white;
                """)

                # Styliser les titres de colonnes
                table.horizontalHeader().setStyleSheet("""
                    color: black;  /* Texte en noir */
                    font-weight: bold;  /* Mettre en gras */
                """)

                # Styliser les cellules
                table.setStyleSheet("""
                    QTableWidget::item {
                        border: 1px solid #ccc;
                        padding: 10px;
                    }
                    QTableWidget::item:selected {
                        background-color: #4CAF50;
                        color: white;
                    }
                """)

                # Remplir le tableau avec les données des ajournés
                for row, (candidat_id, numero_table, nom, prenom, date_naissance, total_points) in enumerate(ajournes):
                    # Arrondir le total des points à 2 décimales
                    total_points_rounded = round(total_points, 2)
                    table.setItem(row, 0, QTableWidgetItem(str(numero_table)))
                    table.setItem(row, 1, QTableWidgetItem(nom))
                    table.setItem(row, 2, QTableWidgetItem(prenom))
                    table.setItem(row, 3, QTableWidgetItem(date_naissance))
                    table.setItem(row, 4, QTableWidgetItem(str(total_points_rounded)))

                    # Ajouter le bouton pour voir le relevé de notes
                    btn_releve = QPushButton("📄")
                    btn_releve.clicked.connect(partial(self.voir_releve_notes, candidat_id))
                    table.setCellWidget(row, 5, btn_releve)

                # Ajustements pour améliorer l'affichage du tableau
                table.horizontalHeader().setStretchLastSection(True)  # Ajuste la largeur des colonnes
                table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Désactive l'édition des cellules

                # Création du layout pour le tableau et les boutons
                layout = QVBoxLayout(container_widget)  # Utilisation d'un QVBoxLayout pour empiler les éléments

                # Ajouter le tableau au layout
                layout.addWidget(table)

                # Créer un layout horizontal pour les boutons
                button_layout = QHBoxLayout()

                # Ajouter le bouton pour générer le PDF
                btn_generate_pdf = QPushButton("📑 Générer PDF des ajournés",
                                               clicked=lambda: self.generate_pdf_ajournes(ajournes))
                btn_generate_pdf.setStyleSheet(
                    "background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
                btn_generate_pdf.setFixedWidth(250)  # Limiter la largeur du bouton

                # Ajouter le bouton pour imprimer
                btn_print = QPushButton("🖨️ Imprimer la liste", clicked=lambda: self.print_table(table))
                btn_print.setStyleSheet(
                    "background-color: #2196F3; color: white; padding: 10px; border-radius: 5px;")
                btn_print.setFixedWidth(250)  # Limiter la largeur du bouton

                # Ajouter les boutons au layout horizontal
                button_layout.addWidget(btn_generate_pdf, alignment=Qt.AlignCenter)
                button_layout.addWidget(btn_print, alignment=Qt.AlignCenter)

                # Ajouter le layout des boutons à celui principal
                layout.addLayout(button_layout)

                # Ajouter le widget contenant le tableau et les boutons à self.main_content
                self.main_content.addWidget(container_widget)

            else:
                # Afficher un message si aucun ajourné
                no_ajournes = QLabel("⚠ Aucun candidat n'est ajourné avec moins de 153 points.",
                                     alignment=Qt.AlignCenter)
                no_ajournes.setStyleSheet("font-size: 18px; color: #FF0000;")
                self.main_content.addWidget(no_ajournes)

            # Mettre à jour l'affichage en toute sécurité
            self.main_content.setCurrentIndex(self.main_content.count() - 1)

        except Exception as e:
            self.show_error_message(f"⚠ Erreur inattendue lors de l'affichage du tableau des ajournés : {e}")

    def print_table(self, table):
        """Imprime le tableau"""
        try:
            # Créer un document texte pour l'impression
            document = QTextDocument()
            cursor = QTextCursor(document)

            # Créer un tableau HTML à partir des données du QTableWidget
            html = "<table border='1' cellpadding='5' cellspacing='0'><tr>"
            for col in range(table.columnCount()):
                html += f"<th>{table.horizontalHeaderItem(col).text()}</th>"
            html += "</tr>"

            for row in range(table.rowCount()):
                html += "<tr>"
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    html += f"<td>{item.text() if item else ''}</td>"
                html += "</tr>"
            html += "</table>"

            # Ajouter le tableau HTML au document
            document.setHtml(html)

            # Configurer l'impression
            printer = QPrinter()
            print_dialog = QPrintDialog(printer)
            if print_dialog.exec() == QPrintDialog.Accepted:
                document.print_(printer)  # Imprimer le document
                self.show_info_message("✅ Impression terminée avec succès.")
        except Exception as e:
            self.show_error_message(f"❌ Erreur lors de l'impression : {e}")

    def generate_pdf_ajournes(self, ajournes):
        """Génère un fichier PDF avec la liste des ajournés sous forme de tableau, avec gestion des pages."""
        try:
            # Créer un fichier PDF
            file_name = "liste_ajournes.pdf"
            c = canvas.Canvas(file_name, pagesize=letter)
            width, height = letter  # Taille de la page

            # Ajouter un titre
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, height - 50, "Liste des candidats ajournés")

            # Données du tableau
            data = [["Numéro de Table", "Nom", "Prénom", "Date de Naissance", "Points"]]  # En-tête du tableau

            # Ajouter les résultats des candidats avec le total des points arrondi
            for candidat_id, numero_table, nom, prenom, date_naissance, total_points in ajournes:
                total_points_rounded = round(total_points, 2)
                data.append([str(numero_table), nom, prenom, date_naissance, str(total_points_rounded)])

            # Configuration de la pagination
            max_rows_per_page = 25  # Nombre de lignes max par page
            y_position = height - 100  # Position initiale du tableau
            page_number = 1  # Numéro de page

            # Séparer les données en plusieurs pages
            for i in range(0, len(data), max_rows_per_page):
                if i > 0:
                    c.showPage()  # Nouvelle page
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(100, height - 50, "Liste des candidats ajournés")

                # Récupérer les données pour la page actuelle
                data_chunk = data[i:i + max_rows_per_page]

                # Créer un tableau avec les données
                table = Table(data_chunk, colWidths=[100, 80, 150, 100, 80])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # En-tête en gris
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texte en blanc
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centrer les textes
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Police de l'en-tête
                    ('FONTSIZE', (0, 0), (-1, -1), 12),  # Taille de la police
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Espacement en bas de l'en-tête
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Fond beige pour le reste
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black)  # Bordures de tableau
                ]))

                # Dessiner le tableau sur la page
                table.wrapOn(c, width, height)
                table.drawOn(c, 50, y_position - (len(data_chunk) * 20))  # Ajustement position

                # Ajouter le numéro de page
                c.setFont("Helvetica", 10)
                c.drawString(width - 100, 30, f"Page {page_number}")
                page_number += 1

            # Sauvegarder le fichier PDF
            c.save()
            self.show_info_message(f"✅ PDF généré avec succès : {file_name}")

        except Exception as e:
            self.show_error_message(f"❌ Erreur lors de la génération du PDF : {e}")
    def open_releve_notes(self):
        """Affiche le relevé de notes des candidats"""
        self.releve_notes_page = QLabel("📄 Relevé des Notes", alignment=Qt.AlignCenter)
        self.releve_notes_page.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E90FF;")
        self.main_content.addWidget(self.releve_notes_page)
        self.main_content.setCurrentWidget(self.releve_notes_page)

    # gestion des note

    def open_add_note_form(self):
        """Ouvre le formulaire pour ajouter une note pour un candidat (1er tour uniquement)."""
        try:
            self.form_window = QWidget()
            self.form_window.setWindowTitle("Ajouter une Note")
            layout = QVBoxLayout()

            # Sélection du candidat par anonymat
            self.anonymat_combo = QComboBox()
            self.load_candidats()  # Charge les candidats dans le comboBox
            layout.addWidget(QLabel("Sélectionner un candidat (Anonymat)"))
            layout.addWidget(self.anonymat_combo)

            # Récupération des matières du premier tour
            self.notes_inputs = {}
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nom FROM matiere WHERE tour = 1")  # 🔹 Sélection uniquement des matières du 1er tour
            matieres = cursor.fetchall()
            conn.close()

            # Ajouter un champ pour chaque matière avec un QDoubleSpinBox pour les notes
            for matiere_id, matiere_nom in matieres:
                note_label = QLabel(f"{matiere_nom}:")  # Afficher le nom de la matière
                note_input = QDoubleSpinBox()
                note_input.setRange(0, 20)  # Plage des notes de 0 à 20
                note_input.setDecimals(2)  # Permet des décimales
                note_input.setSingleStep(0.1)  # Incrément de 0.1

                layout.addWidget(note_label)
                layout.addWidget(note_input)  # Ajoute le champ de saisie
                self.notes_inputs[matiere_id] = note_input  # Associe l'input à la matière via son ID

            # Bouton de soumission
            btn_enregistrer = QPushButton("✅ Enregistrer", clicked=self.enregistrer_note)
            layout.addWidget(btn_enregistrer)

            self.form_window.setLayout(layout)

            # Afficher le formulaire dans le main_content
            self.main_content.addWidget(self.form_window)
            self.main_content.setCurrentWidget(self.form_window)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de base de données lors du chargement des matières : {e}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {e}")

    def enregistrer_note(self):
        """Enregistre les notes du candidat sélectionné (1er tour uniquement) et met à jour le relevé de notes."""
        anonymat = self.anonymat_combo.currentText()
        conn = sqlite3.connect("bfem.db")
        cursor = conn.cursor()

        # Récupérer l'ID du candidat via son anonymat
        cursor.execute("SELECT id FROM candidat WHERE anonymat = ?", (anonymat,))
        candidat = cursor.fetchone()
        if not candidat:
            QMessageBox.critical(self, "Erreur", "Candidat introuvable !")
            return

        candidat_id = candidat[0]

        # Enregistrement des notes et mise à jour des points
        try:
            for matiere_id, note_input in self.notes_inputs.items():
                note = note_input.value()  # ✅ Utiliser value() pour récupérer un float

                # Vérifier si la note est bien entre 0 et 20
                if note < 0 or note > 20:
                    QMessageBox.warning(self, "Valeur incorrecte",
                                        f"La note {note} pour la matière {matiere_id} est invalide.")
                    continue

                # Récupérer le coefficient de la matière
                cursor.execute("SELECT coefficient FROM matiere WHERE id = ?", (matiere_id,))
                matiere = cursor.fetchone()
                if not matiere:
                    QMessageBox.critical(self, "Erreur", "Matière introuvable !")
                    return

                coefficient = matiere[0]
                points = note * coefficient  # Calcul des points

                # Mettre à jour la note dans la table "note"
                cursor.execute("""
                    UPDATE note 
                    SET note_premier_tour = ? 
                    WHERE matiere_id = ? AND candidat_id = ?
                """, (note, matiere_id, candidat_id))

                # Vérifier si une entrée existe déjà dans "releve_notes_1er_tour"
                cursor.execute("""
                    SELECT id FROM releve_notes_1er_tour WHERE candidat_id = ? AND matiere_id = ?
                """, (candidat_id, matiere_id))
                existe = cursor.fetchone()

                if existe:
                    # Mise à jour de la note et des points
                    cursor.execute("""
                        UPDATE releve_notes_1er_tour 
                        SET note = ?, points = ? 
                        WHERE candidat_id = ? AND matiere_id = ?
                    """, (note, points, candidat_id, matiere_id))
                else:
                    # Insertion si l'entrée n'existe pas encore
                    cursor.execute("""
                        INSERT INTO releve_notes_1er_tour (candidat_id, matiere_id, note, points)
                        VALUES (?, ?, ?, ?)
                    """, (candidat_id, matiere_id, note, points))

            conn.commit()
            QMessageBox.information(self, "Succès", "Notes enregistrées avec succès !")
            self.form_window.close()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {e}")
        finally:
            conn.close()

    def load_candidats(self):
        """Charge la liste des candidats anonymes dans la comboBox"""
        conn = sqlite3.connect("bfem.db")
        cursor = conn.cursor()
        cursor.execute("SELECT anonymat FROM candidat ORDER BY anonymat")
        candidats = cursor.fetchall()
        conn.close()

        for (anonymat,) in candidats:
            self.anonymat_combo.addItem(str(anonymat))

    def open_liste_notes(self):
        """Affiche la liste des notes avec les anonymats en ligne et les matières en colonne avec le bouton Modifier."""
        try:
            self.liste_window = QWidget()
            self.liste_window.setWindowTitle("Liste des Notes")
            layout = QVBoxLayout()

            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Récupérer toutes les matières du 1er tour
            cursor.execute("SELECT id, nom FROM matiere WHERE tour = 1 ORDER BY id")
            matieres = cursor.fetchall()
            matiere_ids = [m[0] for m in matieres]
            matiere_noms = [m[1] for m in matieres]

            # Récupérer tous les candidats anonymes
            cursor.execute("SELECT id, anonymat FROM candidat ORDER BY anonymat")
            candidats = cursor.fetchall()
            candidat_ids = [c[0] for c in candidats]
            candidat_anonymats = [c[1] for c in candidats]

            # Vérifier si on a des candidats et des matières
            if not candidats or not matieres:
                QMessageBox.warning(self, "Aucune donnée",
                                    "Aucun candidat ou matière disponible pour afficher les notes.")
                return

            # Création du tableau avec une colonne "Actions"
            self.table = QTableWidget()
            self.table.setRowCount(len(candidats))
            self.table.setColumnCount(len(matiere_noms) + 2)  # +1 pour "Anonymat" et +1 pour Actions

            # Définir les en-têtes de colonnes (Matières + "Anonymat" en premier + Actions)
            self.table.setHorizontalHeaderLabels(["Anonymat"] + matiere_noms + ["Actions"])

            # Appliquer la couleur noire à l'en-tête horizontal
            header = self.table.horizontalHeader()
            header.setStyleSheet("color: black;")

            # Définir les en-têtes de lignes (Candidats Anonymes)
            for row_idx, anonymat in enumerate(candidat_anonymats):
                self.table.setVerticalHeaderItem(row_idx, QTableWidgetItem(str(anonymat)))

            # Charger les notes et les placer dans le tableau
            for row_idx, candidat_id in enumerate(candidat_ids):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(candidat_anonymats[row_idx])))  # Colonne "Anonymat"

                for col_idx, matiere_id in enumerate(matiere_ids):
                    cursor.execute("""
                        SELECT note_premier_tour FROM note 
                        WHERE candidat_id = ? AND matiere_id = ?
                    """, (candidat_id, matiere_id))
                    note = cursor.fetchone()
                    note_value = str(note[0]) if note and note[0] is not None else "-"

                    self.table.setItem(row_idx, col_idx + 1, QTableWidgetItem(note_value))  # +1 pour "Anonymat"

                # Ajouter le bouton Modifier 🖊️
                btn_modifier = QPushButton("🖊️ Modifier")
                btn_modifier.clicked.connect(lambda checked, c_id=candidat_id: self.modifier_note(c_id))

                # Ajout du bouton dans une cellule
                btn_layout = QHBoxLayout()
                btn_layout.addWidget(btn_modifier)

                widget = QWidget()
                widget.setLayout(btn_layout)
                self.table.setCellWidget(row_idx, len(matiere_noms) + 1, widget)  # Dernière colonne

            conn.close()

            # ✅ Redimensionner les colonnes
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
            self.table.setMinimumSize(800, 400)

            # Ajouter le tableau au layout et afficher
            layout.addWidget(self.table)
            self.liste_window.setLayout(layout)
            self.main_content.addWidget(self.liste_window)
            self.main_content.setCurrentWidget(self.liste_window)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des notes : {e}")

    def modifier_note(self, candidat_id):
        """Ouvre un formulaire pour modifier les notes d'un candidat."""
        try:
            self.form_modif_note = QWidget()
            self.form_modif_note.setWindowTitle("Modifier les Notes")
            layout = QVBoxLayout()

            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Récupérer les matières et notes actuelles du candidat
            cursor.execute("""
                SELECT m.id, m.nom, n.note_premier_tour
                FROM matiere m
                LEFT JOIN note n ON m.id = n.matiere_id AND n.candidat_id = ?
                WHERE m.tour = 1
            """, (candidat_id,))
            matieres_notes = cursor.fetchall()
            conn.close()

            self.notes_inputs = {}

            for matiere_id, matiere_nom, note in matieres_notes:
                note_label = QLabel(f"{matiere_nom}:")
                note_input = QDoubleSpinBox()
                note_input.setRange(0, 20)
                note_input.setDecimals(2)
                note_input.setSingleStep(0.1)
                note_input.setValue(note if note is not None else 0)

                layout.addWidget(note_label)
                layout.addWidget(note_input)
                self.notes_inputs[matiere_id] = note_input

            # Bouton de sauvegarde
            btn_sauvegarder = QPushButton("✅ Sauvegarder")
            btn_sauvegarder.clicked.connect(lambda: self.sauvegarder_modifications_note(candidat_id))

            layout.addWidget(btn_sauvegarder)
            self.form_modif_note.setLayout(layout)

            # Afficher la fenêtre de modification
            self.main_content.addWidget(self.form_modif_note)
            self.main_content.setCurrentWidget(self.form_modif_note)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture du formulaire : {e}")

    def sauvegarder_modifications_note(self, candidat_id):
        """Sauvegarde les modifications des notes d'un candidat."""
        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            for matiere_id, note_input in self.notes_inputs.items():
                note = note_input.value()

                if note < 0 or note > 20:
                    QMessageBox.warning(self, "Erreur", f"La note {note} est invalide.")
                    continue

                cursor.execute("SELECT coefficient FROM matiere WHERE id = ?", (matiere_id,))
                coefficient = cursor.fetchone()[0]
                points = note * coefficient

                cursor.execute("""
                    UPDATE note 
                    SET note_premier_tour = ? 
                    WHERE candidat_id = ? AND matiere_id = ?
                """, (note, candidat_id, matiere_id))

                cursor.execute("""
                    UPDATE releve_notes_1er_tour 
                    SET note = ?, points = ? 
                    WHERE candidat_id = ? AND matiere_id = ?
                """, (note, points, candidat_id, matiere_id))

            conn.commit()
            QMessageBox.information(self, "Succès", "Notes mises à jour !")
            self.open_liste_notes()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification : {e}")

    def load_notes(self):
        """Charge les notes depuis la base de données et les affiche dans le tableau"""
        conn = sqlite3.connect("bfem.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.anonymat, m.nom, n.note_premier_tour, n.note_deuxieme_tour
            FROM note n
            JOIN candidat c ON n.candidat_id = c.id
            JOIN matiere m ON n.matiere_id = m.id
        """)
        notes = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(notes))

        for row_idx, (anonymat, matiere, note1, note2) in enumerate(notes):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(anonymat)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(matiere))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(note1) if note1 else "-"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(note2) if note2 else "-"))

    # crude mathier
    def open_liste_matieres(self):
        """Affiche la liste des matières avec des boutons pour modifier et supprimer"""
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QWidget

        self.liste_matieres_page = QWidget()
        layout = QVBoxLayout()

        # Création d'une table pour afficher les matières
        self.table_matieres = QTableWidget()
        self.table_matieres.setColumnCount(4)
        self.table_matieres.setHorizontalHeaderLabels(["Nom ", "Coefficient", "Tour", "Actions"])

        # Appliquer des styles à l'en-tête avec texte noir
        self.table_matieres.horizontalHeader().setStyleSheet("""

            color: black;  /* Texte en noir */
            font-weight: bold;  /* Mettre en gras */

        """)

        # Remplir la table avec les matières existantes
        conn = sqlite3.connect("bfem.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, coefficient, tour FROM matiere")
        matieres = cursor.fetchall()

        self.table_matieres.setRowCount(len(matieres))

        for row, (id, nom, coefficient, tour) in enumerate(matieres):
            self.table_matieres.setItem(row, 0, QTableWidgetItem(nom))
            self.table_matieres.setItem(row, 1, QTableWidgetItem(str(coefficient)))
            self.table_matieres.setItem(row, 2, QTableWidgetItem("Premier tour" if tour == 1 else "Deuxième tour"))

            # Ajouter des boutons pour modifier et supprimer
            btn_modifier = QPushButton("🖊️")
            btn_modifier.clicked.connect(lambda checked, id=id: self.modify_matiere(id))
            btn_supprimer = QPushButton("🗑️")
            btn_supprimer.clicked.connect(lambda checked, id=id: self.delete_matiere(id))

            btn_layout = QHBoxLayout()
            btn_layout.addWidget(btn_modifier)
            btn_layout.addWidget(btn_supprimer)

            widget = QWidget()
            widget.setLayout(btn_layout)

            self.table_matieres.setCellWidget(row, 3, widget)

        layout.addWidget(self.table_matieres)
        self.liste_matieres_page.setLayout(layout)
        self.main_content.addWidget(self.liste_matieres_page)
        self.main_content.setCurrentWidget(self.liste_matieres_page)

    def modify_matiere(self, id):
        """Modifier une matière en utilisant son ID (1er tour uniquement)"""
        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()
            cursor.execute("SELECT nom, coefficient, facultative FROM matiere WHERE id = ?", (id,))
            matiere = cursor.fetchone()

            if matiere:
                nom, coefficient, facultative = matiere

                # Créer un formulaire pour modifier la matière
                self.modify_matiere_form = QWidget()
                form_layout = QFormLayout()

                self.nom_matiere_input = QLineEdit(nom)
                self.coefficient_input = QSpinBox()
                self.coefficient_input.setValue(coefficient)

                self.facultative_input = QComboBox()
                self.facultative_input.addItems(["Obligatoire", "Facultative"])
                self.facultative_input.setCurrentIndex(0 if facultative == 0 else 1)

                # Ajouter les champs au formulaire
                form_layout.addRow("Nom de la matière (1er Tour)", self.nom_matiere_input)  # 🔹 Indication 1er tour
                form_layout.addRow("Coefficient", self.coefficient_input)
                form_layout.addRow("Facultative", self.facultative_input)

                save_button = QPushButton("Sauvegarder")
                save_button.clicked.connect(lambda: self.save_modified_matiere(id))

                form_layout.addWidget(save_button)

                self.modify_matiere_form.setLayout(form_layout)
                self.main_content.addWidget(self.modify_matiere_form)
                self.main_content.setCurrentWidget(self.modify_matiere_form)
        except Exception as e:
            print(f"Erreur lors de la modification de la matière : {e}")

    def save_modified_matiere(self, id):
        """Sauvegarder les modifications d'une matière du premier tour"""
        nom = self.nom_matiere_input.text()
        coefficient = self.coefficient_input.value()
        facultative = 1 if self.facultative_input.currentText() == "Facultative" else 0

        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE matiere
                SET nom = ?, coefficient = ?, facultative = ?
                WHERE id = ?
            """, (nom, coefficient, facultative, id))

            conn.commit()
            QMessageBox.information(self, "Succès", "Matière modifiée avec succès.")
            self.open_liste_matieres()  # Recharger la liste des matières
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification : {e}")
        finally:
            conn.close()

    def delete_matiere(self, id):
        """Supprimer une matière avec une boîte de dialogue de confirmation"""
        # Créer une boîte de dialogue de confirmation
        reply = QMessageBox.question(self, 'Confirmer la suppression',
                                     'Êtes-vous sûr de vouloir supprimer cette matière ?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect("bfem.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM matiere WHERE id = ?", (id,))
                conn.commit()

                # Mettre à jour la liste des matières
                self.open_liste_matieres()  # Recharge la liste des matières

                print("Matière supprimée avec succès.")
            except Exception as e:
                print(f"Erreur lors de la suppression de la matière : {e}")

    # souvegarede des mathier
    def open_add_matiere_form(self):
        """Affiche un formulaire pour ajouter une matière du premier tour"""
        from PyQt5.QtWidgets import QFormLayout, QLineEdit, QSpinBox, QComboBox, QPushButton, QWidget

        self.add_matiere_form = QWidget()
        form_layout = QFormLayout()

        # Champs du formulaire
        self.nom_matiere_input = QLineEdit()
        self.coefficient_input = QSpinBox()
        self.coefficient_input.setRange(1, 10)  # Coefficient entre 1 et 10

        self.facultative_input = QComboBox()
        self.facultative_input.addItems(["Obligatoire", "Facultative"])

        # Ajout des champs au formulaire
        form_layout.addRow("Nom de la matière (1er Tour)", self.nom_matiere_input)  # 🔹 Indication du 1er tour
        form_layout.addRow("Coefficient", self.coefficient_input)
        form_layout.addRow("Facultative", self.facultative_input)

        # Bouton de sauvegarde
        self.save_matiere_button = QPushButton("Ajouter au Premier Tour")
        self.save_matiere_button.clicked.connect(self.save_matiere)

        form_layout.addWidget(self.save_matiere_button)

        self.add_matiere_form.setLayout(form_layout)
        self.main_content.addWidget(self.add_matiere_form)
        self.main_content.setCurrentWidget(self.add_matiere_form)

    def save_matiere(self):
        """Ajoute une matière du premier tour et initialise les notes des candidats dans la table note"""
        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Vérifier que le champ nom n'est pas vide
            if not self.nom_matiere_input.text().strip():
                QMessageBox.warning(self, "Champ vide", "Le nom de la matière est obligatoire.")
                return

            # Vérifier si la matière existe déjà
            cursor.execute("SELECT COUNT(*) FROM matiere WHERE nom = ?", (self.nom_matiere_input.text(),))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "Doublon", "Cette matière existe déjà pour le 1er tour.")
                return

            # Insérer la matière (FORCÉMENT PREMIER TOUR)
            cursor.execute("""
                INSERT INTO matiere (nom, coefficient, tour, facultative) 
                VALUES (?, ?, ?, ?)
            """, (
                self.nom_matiere_input.text(),
                self.coefficient_input.value(),
                1,  # 🔹 Toujours 1er tour
                1 if self.facultative_input.currentText() == "Facultative" else 0
            ))

            matiere_id = cursor.lastrowid  # Récupérer l'ID de la matière insérée

            # Récupérer la liste des candidats existants
            cursor.execute("SELECT id FROM candidat")
            candidats = cursor.fetchall()

            # Ajouter une ligne dans la table note pour chaque candidat
            for (candidat_id,) in candidats:
                cursor.execute("""
                    INSERT INTO note (note_premier_tour, note_deuxieme_tour, matiere_id, candidat_id)
                    VALUES (?, ?, ?, ?)
                """, (None, None, matiere_id, candidat_id))  # Notes initialisées à NULL

            conn.commit()
            QMessageBox.information(self, "Succès", "Matière ajoutée et notes initialisées avec succès.")

            # Nettoyer les champs
            self.nom_matiere_input.clear()
            self.coefficient_input.setValue(1)
            self.facultative_input.setCurrentIndex(0)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ajout de la matière : {e}")
        finally:
            conn.close()

    def toggle_notes_submenu(self):
        """Afficher ou masquer le sous-menu des notes et matières"""
        is_visible = self.notes_submenu_widget.isVisible()
        self.notes_submenu_widget.setVisible(not is_visible)

    def toggle_repechage_submenu(self):
        """Afficher ou masquer le sous-menu de gestion des repêchages"""
        self.repechage_submenu_widget.setVisible(not self.repechage_submenu_widget.isVisible())

    # generation des anonyme
    def generer_anonymat(self):
        """Génère un numéro d'anonymat unique pour tous les candidats sans anonymat"""
        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Récupérer tous les candidats dont le champ anonymat est NULL ou 0
            cursor.execute("""SELECT id, prenom, nom FROM candidat WHERE anonymat IS NULL OR anonymat = 0""")
            candidats_a_anonymiser = cursor.fetchall()

            if candidats_a_anonymiser:
                for candidat in candidats_a_anonymiser:
                    candidat_id = candidat[0]
                    prenom = candidat[1]
                    nom = candidat[2]
                    print(f"Traitement du candidat {prenom} {nom} avec ID: {candidat_id}")

                    # Générer un numéro d'anonymat unique (entre 1000 et 9999)
                    while True:
                        nouveau_numero_anonymat = random.randint(1000, 9999)

                        # Vérifier si le numéro est déjà attribué
                        cursor.execute("""SELECT id FROM candidat WHERE anonymat = ?""", (nouveau_numero_anonymat,))
                        if not cursor.fetchone():  # Si le numéro n'est pas déjà utilisé
                            # Mettre à jour le numéro d'anonymat du candidat dans la base de données
                            cursor.execute("""UPDATE candidat SET anonymat = ? WHERE id = ?""",
                                           (nouveau_numero_anonymat, candidat_id))
                            conn.commit()
                            print(f"Anonymat mis à jour pour {prenom} {nom}: {nouveau_numero_anonymat}")
                            break  # Sortir de la boucle quand un numéro unique est trouvé

                QMessageBox.information(self, "Succès",
                                        "Les numéros d'anonymat ont été générés et mis à jour avec succès !")
            else:
                QMessageBox.information(self, "Information", "Tous les candidats ont déjà un numéro d'anonymat.")

            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération des numéros d'anonymat : {e}")

    # liste des candiat
    def open_liste_candidats(self):
        """Affiche la liste des candidats dans un tableau avec des icônes de modification, suppression et voir info"""
        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Exécuter la requête pour récupérer les candidats
            cursor.execute("""SELECT id, numero_table, prenom, nom, date_naissance, lieu_naissance, sexe, type_candidat, 
                              etablissement, nationalite, etat_sportif, anonymat FROM candidat""")
            candidats = cursor.fetchall()

            # Fermer la connexion à la base de données
            conn.close()

            if candidats:
                # Créer un widget QTableWidget pour afficher les candidats
                self.liste_candidats_table = QTableWidget()
                self.liste_candidats_table.setRowCount(len(candidats))  # Nombre de lignes
                self.liste_candidats_table.setColumnCount(14)  # Nombre de colonnes (ajout de trois pour les icônes)

                # Définir les en-têtes de colonnes
                self.liste_candidats_table.setHorizontalHeaderLabels([
                    "Numéro Table", "Prénom", "Nom", "Date Naissance", "Lieu Naissance", "Sexe", "Type Candidat",
                    "Établissement", "Nationalité", "État Sportif", "Anonymat", "Modifier", "Supprimer", "Voir Info"
                ])

                # Appliquer des styles aux en-têtes avec texte noir
                self.liste_candidats_table.horizontalHeader().setStyleSheet("""

                    color: black; 
                    font-weight: bold;
                """)

                # Remplir le tableau avec les données des candidats
                for row, candidat in enumerate(candidats):
                    for col, data in enumerate(candidat[1:]):  # Ignorer la première colonne (ID)
                        self.liste_candidats_table.setItem(row, col, QTableWidgetItem(str(data)))

                    # Récupérer l'ID du candidat
                    candidat_id = candidat[0]

                    # Utiliser functools.partial pour lier correctement les boutons à l'ID du candidat
                    btn_modifier = QPushButton("✏️")
                    btn_modifier.clicked.connect(partial(self.modifier_candidat, candidat_id))

                    btn_supprimer = QPushButton("❌")
                    btn_supprimer.clicked.connect(partial(self.supprimer_candidat, candidat_id))

                    btn_voir_info = QPushButton("👁️")
                    btn_voir_info.clicked.connect(partial(self.voir_info_candidat, candidat_id))

                    # Style des boutons
                    for btn in [btn_modifier, btn_supprimer, btn_voir_info]:
                        btn.setStyleSheet("background-color: #f7b731; color: white; padding: 5px; border-radius: 5px;")

                    # Ajouter les boutons aux colonnes appropriées
                    self.liste_candidats_table.setCellWidget(row, 11, btn_modifier)  # Colonne Modifier
                    self.liste_candidats_table.setCellWidget(row, 12, btn_supprimer)  # Colonne Supprimer
                    self.liste_candidats_table.setCellWidget(row, 13, btn_voir_info)  # Colonne Voir Info

                # Créer un titre pour la page
                self.liste_candidats_title = QLabel("Liste des candidats", alignment=Qt.AlignCenter)
                self.liste_candidats_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFA500;")

                # Ajouter le titre et le tableau au contenu principal
                layout = QVBoxLayout()
                layout.addWidget(self.liste_candidats_title)
                layout.addWidget(self.liste_candidats_table)

                # Créer un widget contenant le layout
                self.liste_candidats_widget = QWidget()
                self.liste_candidats_widget.setLayout(layout)

                # Afficher la page de la liste des candidats
                self.main_content.addWidget(self.liste_candidats_widget)
                self.main_content.setCurrentWidget(self.liste_candidats_widget)

            else:
                QMessageBox.information(self, "Information", "Aucun candidat trouvé dans la base de données.")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la récupération des candidats : {e}")

    def exporter_candidats_pdf(self):
        """Génère un PDF contenant la liste des candidats avec toutes les informations complètes et affiche un message de succès ou d'erreur"""
        try:
            print("Connexion à la base de données...")
            # Connexion à la base de données
            conn = sqlite3.connect('bfem.db')
            cursor = conn.cursor()

            print("Récupération des candidats...")
            # Récupérer les candidats
            cursor.execute("""
                  SELECT numero_table, nom, prenom, date_naissance, lieu_naissance, sexe, 
                         type_candidat, etablissement, nationalite 
                  FROM candidat 
                  ORDER BY nom
              """)
            candidats = cursor.fetchall()
            conn.close()

            if not candidats:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle("Erreur")
                msg_box.setText("⚠ Aucun candidat à exporter en PDF.")
                msg_box.exec()
                return

            print("Création du PDF...")
            # Création du PDF avec format A4
            pdf = FPDF(format='A4')  # Format A4 (210 x 297 mm)
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Vérification si l'ajout de la page fonctionne
            print("Page ajoutée au PDF")

            # Définir la police pour le titre
            pdf.set_font("Helvetica", style="B", size=16)
            pdf.cell(200, 10, "Liste des Candidats", align="C")
            pdf.ln(10)

            # Définition des en-têtes du tableau avec titres réduits
            pdf.set_font("Helvetica", style="B", size=10)
            headers = ["N°", "Nom", "Prénom", "Date", "Lieu", "Sex.", "Type", "Étab.", "Nat.", "Signature"]
            col_widths = [12, 20, 20, 18, 20, 8, 15, 30, 15, 25]  # Largeurs des colonnes ajustées pour la signature

            print("Ajout des en-têtes du tableau...")
            # Positionner les en-têtes avec une marge de départ
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, border=1, align="C")
            pdf.ln()

            # Ajouter les candidats dans le PDF
            pdf.set_font("Helvetica", size=8)  # Taille plus petite pour les données
            print("Ajout des données des candidats...")
            for numero, nom, prenom, date_naissance, lieu_naissance, sexe, type_candidat, etablissement, nationalite in candidats:
                # Utilisation du if pour vérifier le type de candidat
                if type_candidat == "Candidat normal":
                    type_candidat = "Normal"
                elif type_candidat == "Candidat libre":
                    type_candidat = "Libre"

                data = [numero, nom, prenom, date_naissance, lieu_naissance, sexe, type_candidat, etablissement,
                        nationalite]
                # Chaque ligne de données dans les cellules
                for i, value in enumerate(data):
                    pdf.cell(col_widths[i], 8, str(value), border=1, align="C")

                # Ajouter une case vide pour la signature
                pdf.cell(col_widths[-1], 8, "", border=1, align="C")  # Case vide pour la signature
                pdf.ln()

            # Sauvegarde du fichier
            pdf_path = "liste_candidats.pdf"
            print(f"Sauvegarde du fichier PDF à {pdf_path}...")
            pdf.output(pdf_path)

            # Afficher le message de succès
            QMessageBox.information(self, "Succès", "Candidat generet avec succes")


        except sqlite3.Error as e:
            print(f"Erreur SQLite : {e}")
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Erreur")
            msg_box.setText(f"❌ Erreur SQLite lors de l'exportation des candidats : {e}")
            msg_box.exec()

        except Exception as e:
            print(f"Erreur inattendue : {e}")
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Erreur Inattendue")
            msg_box.setText(f"⚠ Erreur inattendue : {e}")
            msg_box.exec()

    def voir_info_candidat(self, id):
        """Afficher les informations détaillées du candidat dans une boîte de dialogue"""
        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Exécuter la requête pour récupérer les informations du candidat par ID
            cursor.execute("""SELECT prenom, nom, date_naissance, lieu_naissance, sexe, type_candidat, etablissement,
                              nationalite, etat_sportif, anonymat FROM candidat WHERE id = ?""", (id,))
            candidat = cursor.fetchone()

            # Fermer la connexion à la base de données
            conn.close()

            if candidat:
                # Créer une fenêtre de dialogue pour afficher les informations
                info_dialog = QDialog(self)
                info_dialog.setWindowTitle(f"Informations du Candidat {candidat[1]}")

                # Créer un layout pour afficher les informations
                layout = QVBoxLayout()

                info_labels = [
                    f"Prénom: {candidat[0]}",
                    f"Nom: {candidat[1]}",
                    f"Date de Naissance: {candidat[2]}",
                    f"Lieu de Naissance: {candidat[3]}",
                    f"Sexe: {candidat[4]}",
                    f"Type de Candidat: {candidat[5]}",
                    f"Établissement: {candidat[6]}",
                    f"Nationalité: {candidat[7]}",
                    f"État Sportif: {candidat[8]}",
                    f"Anonymat: {candidat[9]}"
                ]

                for label in info_labels:
                    layout.addWidget(QLabel(label))

                # Ajouter un bouton de fermeture
                btn_close = QPushButton("Fermer")
                btn_close.clicked.connect(info_dialog.close)
                layout.addWidget(btn_close)

                info_dialog.setLayout(layout)
                info_dialog.exec_()

            else:
                QMessageBox.warning(self, "Erreur", "Aucun candidat trouvé avec cet ID.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'affichage des informations du candidat : {e}")

    def open_liste_releves(self):
        """Affiche la liste des relevés scolaires des candidats"""
        try:
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Requête pour récupérer les informations des candidats avec leurs relevés scolaires
            cursor.execute("""
                        SELECT c.prenom, c.nom, c.date_naissance, c.lieu_naissance, 
                               r.moyenne_6e, r.moyenne_5e, r.moyenne_4e, r.moyenne_3e, 
                               r.moyenne_generale, r.nombre_de_fois
                        FROM candidat c
                        JOIN releve_scolaire r ON c.id = r.id
                    """)
            releves = cursor.fetchall()

            conn.close()

            if releves:
                self.liste_releves_table = QTableWidget()
                self.liste_releves_table.setRowCount(len(releves))
                self.liste_releves_table.setColumnCount(10)

                # Définition des en-têtes de colonnes
                self.liste_releves_table.setHorizontalHeaderLabels([
                    "Prénom", "Nom", "Date de Naissance", "Lieu de Naissance",
                    "Moyenne 6e", "Moyenne 5e", "Moyenne 4e", "Moyenne 3e",
                    "Moyenne Générale", "Nombre de fois"
                ])

                # Appliquer des styles à l'en-tête
                self.liste_releves_table.horizontalHeader().setStyleSheet("""

                             color: black;
                            font-weight: bold;  /* Mettre en gras */

                        """)

                # Remplir le tableau avec les données
                for row, releve in enumerate(releves):
                    for col, data in enumerate(releve):
                        self.liste_releves_table.setItem(row, col, QTableWidgetItem(str(data)))

                # Création du titre de la page
                self.liste_releves_title = QLabel("Liste des relevés scolaires", alignment=Qt.AlignCenter)
                self.liste_releves_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFA500;")

                # Ajouter le tableau dans la mise en page
                layout = QVBoxLayout()
                layout.addWidget(self.liste_releves_title)
                layout.addWidget(self.liste_releves_table)

                # Créer un widget contenant le layout
                self.liste_releves_widget = QWidget()
                self.liste_releves_widget.setLayout(layout)

                # Afficher la page
                self.main_content.addWidget(self.liste_releves_widget)
                self.main_content.setCurrentWidget(self.liste_releves_widget)

            else:
                QMessageBox.information(self, "Information", "Aucun relevé trouvé dans la base de données.")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la récupération des relevés : {e}")

    # modification et supression d'un candidat
    def modifier_candidat(self, candidat_id):
        """Affiche un formulaire pour modifier les informations d'un candidat"""
        try:
            # Connexion à la base de données
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Récupérer les informations du candidat à modifier
            cursor.execute("SELECT * FROM candidat WHERE id = ?", (candidat_id,))
            candidat = cursor.fetchone()

            if candidat:
                # Créer un formulaire de modification avec les informations existantes
                self.formulaire_modification = QWidget()
                layout = QVBoxLayout()

                self.nom_input = QLineEdit(candidat[2])  # Prénom
                self.prenom_input = QLineEdit(candidat[3])  # Nom
                self.date_naissance_input = QLineEdit(candidat[4])  # Date de naissance
                self.lieu_naissance_input = QLineEdit(candidat[5])  # Lieu de naissance
                self.sexe_input = QLineEdit(candidat[6])  # Sexe
                self.type_candidat_input = QLineEdit(candidat[7])  # Type de candidat
                self.etablissement_input = QLineEdit(candidat[8])  # Établissement
                self.nationalite_input = QLineEdit(candidat[9])  # Nationalité
                self.etat_sportif_input = QLineEdit(candidat[10])  # État sportif
                self.anonymat_input = QLineEdit(str(candidat[11]))  # Anonymat

                # Ajouter les champs au formulaire
                layout.addWidget(QLabel("Nom:"))
                layout.addWidget(self.nom_input)
                layout.addWidget(QLabel("Prénom:"))
                layout.addWidget(self.prenom_input)
                layout.addWidget(QLabel("Date de naissance:"))
                layout.addWidget(self.date_naissance_input)
                layout.addWidget(QLabel("Lieu de naissance:"))
                layout.addWidget(self.lieu_naissance_input)
                layout.addWidget(QLabel("Sexe:"))
                layout.addWidget(self.sexe_input)
                layout.addWidget(QLabel("Type de candidat:"))
                layout.addWidget(self.type_candidat_input)
                layout.addWidget(QLabel("Établissement:"))
                layout.addWidget(self.etablissement_input)
                layout.addWidget(QLabel("Nationalité:"))
                layout.addWidget(self.nationalite_input)
                layout.addWidget(QLabel("État sportif:"))
                layout.addWidget(self.etat_sportif_input)
                layout.addWidget(QLabel("Anonymat:"))
                layout.addWidget(self.anonymat_input)

                # Ajouter un bouton pour soumettre les modifications
                self.btn_sauvegarder = QPushButton("Sauvegarder les modifications")
                self.btn_sauvegarder.clicked.connect(lambda: self.sauvegarder_modifications(candidat_id))

                layout.addWidget(self.btn_sauvegarder)

                # Mettre en place le layout et afficher le formulaire
                self.formulaire_modification.setLayout(layout)
                self.main_content.addWidget(self.formulaire_modification)
                self.main_content.setCurrentWidget(self.formulaire_modification)

            else:
                QMessageBox.warning(self, "Erreur", "Candidat non trouvé.")

            # Fermer la connexion
            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la récupération des données : {e}")

    def sauvegarder_modifications(self, candidat_id):
        """Sauvegarde les modifications du candidat dans la base de données"""
        try:
            # Récupérer les nouvelles données
            nom = self.nom_input.text()
            prenom = self.prenom_input.text()
            date_naissance = self.date_naissance_input.text()
            lieu_naissance = self.lieu_naissance_input.text()
            sexe = self.sexe_input.text()
            type_candidat = self.type_candidat_input.text()
            etablissement = self.etablissement_input.text()
            nationalite = self.nationalite_input.text()
            etat_sportif = self.etat_sportif_input.text()
            anonymat = self.anonymat_input.text()

            # Connexion à la base de données
            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Mettre à jour les informations du candidat
            cursor.execute("""UPDATE candidat SET
                              prenom = ?, nom = ?, date_naissance = ?, lieu_naissance = ?, sexe = ?, type_candidat = ?,
                              etablissement = ?, nationalite = ?, etat_sportif = ?, anonymat = ?
                              WHERE id = ?""",
                           (prenom, nom, date_naissance, lieu_naissance, sexe, type_candidat, etablissement,
                            nationalite, etat_sportif, anonymat, candidat_id))

            # Sauvegarder les modifications
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Succès", "Les informations du candidat ont été mises à jour.")

            # Retourner à la liste des candidats après modification
            self.open_liste_candidats()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde des modifications : {e}")

    def supprimer_candidat(self, candidat_id):
        """Supprime un candidat de la base de données après confirmation"""
        # Demander une confirmation avant la suppression
        reply = QMessageBox.question(self, 'Confirmation de suppression',
                                     'Êtes-vous sûr de vouloir supprimer ce candidat ?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect("bfem.db")
                cursor = conn.cursor()

                # Supprimer le candidat de la base de données
                cursor.execute("DELETE FROM candidat WHERE id = ?", (candidat_id,))
                conn.commit()

                # Fermer la connexion
                conn.close()

                # Rafraîchir la liste des candidats
                self.open_liste_candidats()

                QMessageBox.information(self, "Succès", "Candidat supprimé avec succès.")

            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression du candidat : {e}")
        else:
            # Si l'utilisateur annule, ne rien faire
            print("Suppression annulée.")

    def toggle_candidats_submenu(self):
        """Afficher ou cacher le sous-menu de gestion des candidats"""
        visible = self.candidats_submenu_widget.isVisible()
        self.candidats_submenu_widget.setVisible(not visible)

    # l'ajout et souvegarde dest candidat

    def open_add_candidat_form(self):
        """Ouvre un formulaire pour ajouter un candidat avec relevé scolaire"""
        from PyQt5.QtWidgets import QFormLayout, QLineEdit, QDateEdit, QComboBox, QDoubleSpinBox, QSpinBox

        self.add_candidat_form = QWidget()
        form_layout = QFormLayout()

        # Champs du candidat
        self.num_table_input = QSpinBox()  # Utilisation de QSpinBox au lieu de QLineEdit
        self.num_table_input.setRange(1, 300)  # Plage de 1 à 100 pour le numéro de table
        self.prenom_input = QLineEdit()
        self.nom_input = QLineEdit()
        self.date_naissance_input = QDateEdit()
        self.lieu_naissance_input = QLineEdit()
        self.sexe_input = QComboBox()
        self.sexe_input.addItems(["Masculin", "Féminin"])
        self.type_candidat_input = QComboBox()
        self.type_candidat_input.addItems(["Candidat libre", "Candidat normal"])
        self.etablissement_input = QLineEdit()
        self.nationalite_input = QLineEdit()
        self.etat_sportif_input = QComboBox()
        self.etat_sportif_input.addItems(["Oui", "Non"])

        # Champs du relevé scolaire
        self.moyenne_6e_input = QDoubleSpinBox()
        self.moyenne_5e_input = QDoubleSpinBox()
        self.moyenne_4e_input = QDoubleSpinBox()
        self.moyenne_3e_input = QDoubleSpinBox()
        self.nombre_de_fois_input = QLineEdit()

        for spinbox in [self.moyenne_6e_input, self.moyenne_5e_input, self.moyenne_4e_input, self.moyenne_3e_input]:
            spinbox.setRange(0, 20)
            spinbox.setDecimals(2)

        # Ajout des champs au formulaire
        form_layout.addRow("Numéro de Table", self.num_table_input)
        form_layout.addRow("Prénom(s)", self.prenom_input)
        form_layout.addRow("Nom", self.nom_input)
        form_layout.addRow("Date de Naissance", self.date_naissance_input)
        form_layout.addRow("Lieu de Naissance", self.lieu_naissance_input)
        form_layout.addRow("Sexe", self.sexe_input)
        form_layout.addRow("Type de Candidat", self.type_candidat_input)
        form_layout.addRow("Établissement", self.etablissement_input)
        form_layout.addRow("Nationalité", self.nationalite_input)
        form_layout.addRow("État Sportif", self.etat_sportif_input)

        # Ajout des champs du relevé scolaire
        form_layout.addRow("Moyenne 6e", self.moyenne_6e_input)
        form_layout.addRow("Moyenne 5e", self.moyenne_5e_input)
        form_layout.addRow("Moyenne 4e", self.moyenne_4e_input)
        form_layout.addRow("Moyenne 3e", self.moyenne_3e_input)
        form_layout.addRow("Nombre de fois redoublé", self.nombre_de_fois_input)

        # Bouton de sauvegarde
        self.save_button = QPushButton("Sauvegarder")
        self.save_button.clicked.connect(self.save_candidat)
        form_layout.addWidget(self.save_button)

        self.add_candidat_form.setLayout(form_layout)
        self.main_content.addWidget(self.add_candidat_form)
        self.main_content.setCurrentWidget(self.add_candidat_form)

    def save_candidat(self):
        """Sauvegarde un candidat avec son relevé scolaire et initialise ses données associées"""
        try:
            # Vérification des champs obligatoires
            if not self.num_table_input.text() or not self.prenom_input.text() or not self.nom_input.text() or not self.date_naissance_input.date() or not self.lieu_naissance_input.text():
                QMessageBox.critical(self, "Erreur", "Les champs obligatoires doivent être remplis.")
                return

            # Validation du sexe (doit être soit 'M' ou 'F')
            sexe = self.sexe_input.currentText()
            if sexe == "Masculin":
                sexe = 'M'
            elif sexe == "Féminin":
                sexe = 'F'

            if sexe not in ['M', 'F']:
                QMessageBox.critical(self, "Erreur", "Le sexe doit être 'M' ou 'F'.")
                return

            conn = sqlite3.connect("bfem.db")
            cursor = conn.cursor()

            # Calcul automatique de la moyenne générale
            moy_6e = self.moyenne_6e_input.value()
            moy_5e = self.moyenne_5e_input.value()
            moy_4e = self.moyenne_4e_input.value()
            moy_3e = self.moyenne_3e_input.value()
            moyenne_generale = (moy_6e + moy_5e + moy_4e + moy_3e) / 4  # Calcul de la moyenne

            # Insérer le relevé scolaire et récupérer son ID
            cursor.execute("""
                INSERT INTO releve_scolaire (moyenne_6e, moyenne_5e, moyenne_4e, moyenne_3e, 
                                             moyenne_generale, nombre_de_fois)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                moy_6e, moy_5e, moy_4e, moy_3e, moyenne_generale, self.nombre_de_fois_input.text()
            ))
            releve_id = cursor.lastrowid  # ID du relevé scolaire inséré

            # Insérer le candidat avec son relevé scolaire
            cursor.execute("""
                INSERT INTO candidat (numero_table, prenom, nom, date_naissance, lieu_naissance, sexe, 
                                      type_candidat, etablissement, nationalite, etat_sportif, anonymat, releve_scolaire_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.num_table_input.text(),
                self.prenom_input.text(),
                self.nom_input.text(),
                self.date_naissance_input.date().toString("yyyy-MM-dd"),
                self.lieu_naissance_input.text(),
                sexe,  # Utilisation du sexe validé
                self.type_candidat_input.currentText(),
                self.etablissement_input.text(),
                self.nationalite_input.text(),
                self.etat_sportif_input.currentText(),
                0,  # Valeur par défaut pour anonymat
                releve_id  # Associer le relevé scolaire au candidat
            ))

            # Récupérer l'ID du candidat nouvellement inséré
            candidat_id = cursor.lastrowid

            # Insérer un enregistrement dans la table 'resultat' pour ce candidat (1er tour)
            cursor.execute("""
                INSERT INTO resultat (candidat_id, total_points, moyenne, presentation)
                VALUES (?, 0, 0, 'Non délibéré')
            """, (candidat_id,))

            # Insérer un enregistrement dans la table 'resultat_2e_tour' pour ce candidat (2ᵉ tour)
            cursor.execute("""
               INSERT INTO resultat_2e_tour (candidat_id, total_points, moyenne, presentation)
               VALUES (?, 0, 0, 'Non délibéré')
            """, (candidat_id,))

            # Récupérer la liste des matières
            cursor.execute("SELECT id FROM matiere")
            matieres = cursor.fetchall()

            # Insérer des entrées vides dans les relevés de notes (1er et 2e tour) pour chaque matière
            for matiere_id in matieres:
                matiere_id = matiere_id[0]
                cursor.execute("""
                    INSERT INTO releve_notes_1er_tour (candidat_id, matiere_id, note, points)
                    VALUES (?, ?, 0, 0)
                """, (candidat_id, matiere_id))

                cursor.execute("""
                    INSERT INTO releve_notes_2e_tour (candidat_id, matiere_id, note, points)
                    VALUES (?, ?, 0, 0)
                """, (candidat_id, matiere_id))

            # Valider toutes les insertions
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Succès", "Candidat ajouté avec succès avec toutes ses données associées !")

            # Retourner à la liste des candidats après ajout
            self.open_liste_candidats()

        except Exception as e:
            conn.rollback()  # Annuler les changements en cas d'erreur
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ajout du candidat : {e}")

        finally:
            conn.close()

    # information du jury
    def get_jury_info(self, email_membre):
        """Récupérer les informations du jury et du membre"""
        try:
            with sqlite3.connect("bfem.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT Nom, Prenom, jury_id FROM membre_jury WHERE Email = ?", (email_membre,))
                membre = cursor.fetchone()

                if not membre:
                    return "Jury inconnu", "Membre inconnu"

                cursor.execute("SELECT localite, centre_examen FROM jury WHERE id = ?", (membre[2],))
                jury = cursor.fetchone()

                return f"Jury {jury[0]} - {jury[1]}", f"{membre[0]} {membre[1]}"
        except Exception as e:
            return "Jury inconnu", "Membre inconnu"

    def toggle_sidebar(self):
        """Afficher ou cacher la barre latérale"""
        self.sidebar.setFixedWidth(250 if self.sidebar.width() == 0 else 0)


if __name__ == "__main__":
    app = QApplication([])
    window = BFEMApp(email_membre="test@example.com")
    window.show()
    app.exec_()
