import sqlite3

# Connexion à la base de données SQLite
conn = sqlite3.connect("bfem.db")
cursor = conn.cursor()

# Activation des clés étrangères
cursor.execute("PRAGMA foreign_keys = ON;")

try:
    # ======================= TABLES EXISTANTES ======================== #

    # Table candidat
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_table TEXT UNIQUE NOT NULL,
        prenom TEXT NOT NULL,
        nom TEXT NOT NULL,
        date_naissance TEXT NOT NULL,
        lieu_naissance TEXT NOT NULL,
        sexe TEXT CHECK (sexe IN ('M', 'F')) NOT NULL,
        type_candidat TEXT NOT NULL,
        etablissement TEXT NOT NULL,
        nationalite TEXT NOT NULL,
        etat_sportif TEXT NOT NULL,
        anonymat INTEGER DEFAULT 0,
        note_id INTEGER,
        releve_scolaire_id INTEGER,
        FOREIGN KEY (note_id) REFERENCES note(id) ON DELETE SET NULL,
        FOREIGN KEY (releve_scolaire_id) REFERENCES releve_scolaire(id) ON DELETE SET NULL
    )
    """)

    # Table matiere
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matiere (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT UNIQUE NOT NULL,
        coefficient INTEGER NOT NULL CHECK (coefficient > 0),
        tour INTEGER CHECK (tour IN (1, 2)) NOT NULL, -- 1 = Premier tour, 2 = Deuxième tour
        facultative INTEGER DEFAULT 0 CHECK (facultative IN (0, 1)), -- 0 = Obligatoire, 1 = Facultative
        active INTEGER DEFAULT 1 CHECK (active IN (0, 1))
    );
    """)

    # Table note
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS note (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_premier_tour REAL CHECK (note_premier_tour BETWEEN 0 AND 20),
        note_deuxieme_tour REAL CHECK (note_deuxieme_tour BETWEEN 0 AND 20),
        matiere_id INTEGER NOT NULL,
        candidat_id INTEGER NOT NULL,
        FOREIGN KEY (matiere_id) REFERENCES matiere(id) ON DELETE CASCADE,
        FOREIGN KEY (candidat_id) REFERENCES candidat(id) ON DELETE CASCADE
    )
    """)

    # Table relevé scolaire
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS releve_scolaire (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        moyenne_6e REAL CHECK (moyenne_6e BETWEEN 0 AND 20),
        moyenne_5e REAL CHECK (moyenne_5e BETWEEN 0 AND 20),
        moyenne_4e REAL CHECK (moyenne_4e BETWEEN 0 AND 20),
        moyenne_3e REAL CHECK (moyenne_3e BETWEEN 0 AND 20),
        moyenne_generale REAL CHECK (moyenne_generale BETWEEN 0 AND 20),
        nombre_de_fois INTEGER CHECK (nombre_de_fois >= 0)
    )
    """)

    # Table résultat (1er tour)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resultat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total_points REAL CHECK (total_points >= 0),
        moyenne REAL CHECK (moyenne BETWEEN 0 AND 20),
        repechable INTEGER DEFAULT 0 CHECK (repechable IN (0, 1)),
        presentation TEXT,
        candidat_id INTEGER NOT NULL,
        FOREIGN KEY (candidat_id) REFERENCES candidat(id) ON DELETE CASCADE
    )
    """)

    # Table jury
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jury (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ia TEXT NOT NULL,
        ief TEXT NOT NULL,
        localite TEXT NOT NULL,
        centre_examen TEXT NOT NULL,
        president_jury TEXT NOT NULL,
        telephone TEXT NOT NULL
    )
    """)

    # Table membre_jury
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS membre_jury (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        mot_de_passe TEXT NOT NULL,
        jury_id INTEGER NOT NULL,
        FOREIGN KEY (jury_id) REFERENCES jury(id) ON DELETE CASCADE
    )
    """)

    # ======================= NOUVELLES TABLES ======================== #

    # Table résultat (2ᵉ tour)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resultat_2e_tour (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total_points REAL CHECK (total_points >= 0),
        moyenne REAL CHECK (moyenne BETWEEN 0 AND 20),
        repechable INTEGER DEFAULT 0 CHECK (repechable IN (0, 1)),
        presentation TEXT,
        candidat_id INTEGER NOT NULL,
        FOREIGN KEY (candidat_id) REFERENCES candidat(id) ON DELETE CASCADE
    )
    """)

    # Table relevé de notes 1er tour
    cursor.execute("""
CREATE TABLE IF NOT EXISTS releve_notes_1er_tour (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidat_id INTEGER NOT NULL,
    matiere_id INTEGER NOT NULL,
    note REAL CHECK (note BETWEEN 0 AND 20),
    points REAL CHECK (points >= 0),
    FOREIGN KEY (candidat_id) REFERENCES candidat(id) ON DELETE CASCADE,
    FOREIGN KEY (matiere_id) REFERENCES matiere(id) ON DELETE CASCADE,
    UNIQUE(candidat_id, matiere_id)  -- 🔹 Ajout de la contrainte UNIQUE
);

    """)

    # Table relevé de notes 2e tour
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS releve_notes_2e_tour (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidat_id INTEGER NOT NULL,
        matiere_id INTEGER NOT NULL,
        note REAL CHECK (note BETWEEN 0 AND 20),
        points REAL CHECK (points >= 0),  -- Suppression de GENERATED ALWAYS AS
        FOREIGN KEY (candidat_id) REFERENCES candidat(id) ON DELETE CASCADE,
        FOREIGN KEY (matiere_id) REFERENCES matiere(id) ON DELETE CASCADE
        UNIQUE(candidat_id, matiere_id)  -- 🔹 Ajout de la contrainte UNIQUE
    )
    """)

    # Enregistrement des changements
    conn.commit()
    print("✅ Base de données et nouvelles tables créées avec succès ! 🚀")

except sqlite3.Error as e:
    print(f"❌ Erreur lors de la création des tables : {e}")

finally:
    # Fermeture de la connexion
    conn.close()
