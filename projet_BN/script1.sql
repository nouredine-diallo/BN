DROP SCHEMA IF EXISTS BN CASCADE;
CREATE SCHEMA IF NOT EXISTS BN;
SET search_path TO BN;

CREATE TABLE Carte (
  PRIMARY KEY (id_carte),
  id_carte  INTEGER NOT NULL,
  etat      VARCHAR(50),
  rang      INTEGER,
  id_pioche INTEGER NOT NULL,
  code      VARCHAR(42) NOT NULL
);

CREATE TABLE Contient_orque (
  PRIMARY KEY (id_grille, id_orque),
  id_grille INTEGER NOT NULL,
  id_orque  INTEGER NOT NULL,
  coord_X   INTEGER,
  coord_Y   VARCHAR(10)
);

CREATE TABLE Est_compose (
  PRIMARY KEY (nom_distribution, code),
  nom_distribution VARCHAR(42) NOT NULL,
  code             VARCHAR(42) NOT NULL,
  proportion       FLOAT 
);

CREATE TABLE Est_place (
  PRIMARY KEY (id_navire, id_grille),
  id_navire INTEGER NOT NULL,
  id_grille INTEGER NOT NULL,
  coord_X   INTEGER,
  coord_Y   VARCHAR(10),
  sens      VARCHAR(42)
);

CREATE TABLE Flotille (
id_flotille SERIAL PRIMARY KEY,
  typef       VARCHAR(42),
  nb_navire   INTEGER
);

CREATE TABLE Grille (
  id_grille SERIAL PRIMARY KEY , 
  largeur         INTEGER,
  hauteur         INTEGER ,
  imageplouf      VARCHAR(42),
  imagetouche     VARCHAR(42),
  imagenonexplore VARCHAR(42)
);

CREATE TABLE Grille_navire (
  PRIMARY KEY (id_grille),
  id_grille INTEGER NOT NULL
);

CREATE TABLE Grille_tir (
  PRIMARY KEY (id_grille),
  id_grille       INTEGER NOT NULL, 
  nb_cellule_vide INTEGER 
);

CREATE TABLE JOUEUR (
  PRIMARY KEY (id_joueur),
  id_joueur INTEGER NOT NULL,
  pseudo    VARCHAR(50)
);

CREATE TABLE JOUEUR_humain (
  PRIMARY KEY (id_joueur),
  id_joueur      INTEGER NOT NULL,
  nom            VARCHAR(80),
  prenom         VARCHAR(80),
  date_naissance DATE 
);

CREATE TABLE JOUEUR_Virtuel (
  PRIMARY KEY (id_joueur),
  id_joueur   INTEGER NOT NULL,
  niveau        INTEGER ,
  id_createur   INTEGER NOT NULL,
  date_creation DATE 
);

CREATE TABLE Leurre (
  PRIMARY KEY (id_grille, num_L),
  id_grille INTEGER NOT NULL,
  num_L     INTEGER NOT NULL,
  taille    INTEGER , 
  coord_X   INTEGER,
  coord_Y   VARCHAR(10),
  sens      VARCHAR(42)
);

CREATE TABLE Navire (
 id_navire SERIAL PRIMARY KEY ,
  nom         VARCHAR(50),
  type        VARCHAR(42),
  taille      INTEGER , 
  id_flotille INTEGER NOT NULL,
  code        VARCHAR(42) NOT NULL
);

CREATE TABLE Orque (
  id_orque SERIAL PRIMARY KEY ,
  nom      VARCHAR(42),
  chemin   VARCHAR(80)
);

CREATE TABLE ou_placer (
  PRIMARY KEY (id_grille, id_partie, id_joueur),
  id_grille INTEGER NOT NULL,
  id_partie INTEGER NOT NULL,
  id_joueur INTEGER NOT NULL
);

CREATE TABLE ou_tirer (
  PRIMARY KEY (id_grille, id_partie, id_joueur),
  id_grille INTEGER NOT NULL,
  id_partie INTEGER NOT NULL,
  id_joueur INTEGER NOT NULL
);


CREATE TABLE Partie (
  PRIMARY KEY (id_partie),
  id_partie      INTEGER NOT NULL,
  date_creation  DATE,
  heure_creation TIME, 
  etat           VARCHAR(42),
  score_final    INTEGER ,
  id_jh   INTEGER NOT NULL,
  id_jv   INTEGER NULL,
  id_jgagnant    INTEGER
);

CREATE TABLE Pavillon (
  PRIMARY KEY (code),
  code VARCHAR(42) NOT NULL,
  pays VARCHAR(42)
);

CREATE TABLE Pioche (
  id_pioche SERIAL PRIMARY KEY , 
  id_partie        INTEGER NOT NULL,
  nom_distribution VARCHAR(42) NOT NULL,
  UNIQUE (id_partie)
);

CREATE TABLE Seq_Temp (
  PRIMARY KEY (id_partie, date_debut),
  id_partie   INTEGER NOT NULL,
  date_debut  DATE NOT NULL,
  heure_debut TIME,
  date_fin    DATE,
  heure_fin   TIME 
);

CREATE TABLE Tir (
  PRIMARY KEY (id_partie, num_tour, num_tir),
  id_partie INTEGER NOT NULL,
  num_tour  INTEGER NOT NULL,
  num_tir   INTEGER NOT NULL,
  coord_X   INTEGER,
  coord_Y   VARCHAR(10),
  id_joueur INTEGER NOT NULL,
  id_carte  INTEGER NULL,
  UNIQUE (id_carte)
);

CREATE TABLE Tour (
  PRIMARY KEY (id_partie, num_tour),
  id_partie         INTEGER NOT NULL,
  num_tour          INTEGER NOT NULL,
  nb_navire_coule   INTEGER,
  nb_navire_touche  INTEGER,
  nb_cellule_libre1 INTEGER,
  nb_cellule_libre2 INTEGER
);

CREATE TABLE Type_Carte (
  PRIMARY KEY (code),
  code           VARCHAR(42) NOT NULL,
  bonus          BOOLEAN,
  nom            VARCHAR(42),
  descrip_chemin VARCHAR(80)
);

ALTER TABLE Carte ADD FOREIGN KEY (code) REFERENCES Type_Carte (code);
ALTER TABLE Carte ADD FOREIGN KEY (id_pioche) REFERENCES Pioche (id_pioche);

ALTER TABLE Contient_orque ADD FOREIGN KEY (id_orque) REFERENCES Orque (id_orque);
ALTER TABLE Contient_orque ADD FOREIGN KEY (id_grille) REFERENCES Grille_navire (id_grille);

ALTER TABLE Est_compose ADD FOREIGN KEY (code) REFERENCES Type_Carte (code);

ALTER TABLE Est_place ADD FOREIGN KEY (id_grille) REFERENCES Grille_navire (id_grille);
ALTER TABLE Est_place ADD FOREIGN KEY (id_navire) REFERENCES Navire (id_navire);

ALTER TABLE Grille_navire ADD FOREIGN KEY (id_grille) REFERENCES Grille (id_grille);

ALTER TABLE Grille_tir ADD FOREIGN KEY (id_grille) REFERENCES Grille (id_grille);

ALTER TABLE JOUEUR_humain ADD FOREIGN KEY (id_joueur) REFERENCES JOUEUR (id_joueur);

ALTER TABLE JOUEUR_Virtuel ADD FOREIGN KEY (id_createur) REFERENCES JOUEUR_humain (id_joueur);
ALTER TABLE JOUEUR_Virtuel ADD FOREIGN KEY (id_joueur_1) REFERENCES JOUEUR (id_joueur);

ALTER TABLE Leurre ADD FOREIGN KEY (id_grille) REFERENCES Grille_navire (id_grille);

ALTER TABLE Navire ADD FOREIGN KEY (code) REFERENCES Pavillon (code);
ALTER TABLE Navire ADD FOREIGN KEY (id_flotille) REFERENCES Flotille (id_flotille);

ALTER TABLE ou_placer ADD FOREIGN KEY (id_joueur) REFERENCES JOUEUR (id_joueur);
ALTER TABLE ou_placer ADD FOREIGN KEY (id_partie) REFERENCES Partie (id_partie);
ALTER TABLE ou_placer ADD FOREIGN KEY (id_grille) REFERENCES Grille_navire (id_grille);

ALTER TABLE ou_tirer ADD FOREIGN KEY (id_joueur) REFERENCES JOUEUR (id_joueur);
ALTER TABLE ou_tirer ADD FOREIGN KEY (id_partie) REFERENCES Partie (id_partie);
ALTER TABLE ou_tirer ADD FOREIGN KEY (id_grille) REFERENCES Grille_tir (id_grille);

ALTER TABLE Partie ADD FOREIGN KEY (id_jgagnant) REFERENCES JOUEUR (id_joueur);
ALTER TABLE Partie ADD FOREIGN KEY (id_jv) REFERENCES JOUEUR_Virtuel  (id_joueur);
ALTER TABLE Partie ADD FOREIGN KEY (id_jh) REFERENCES JOUEUR_humain (id_joueur);

ALTER TABLE Pioche ADD FOREIGN KEY (id_partie) REFERENCES Partie (id_partie);

ALTER TABLE Seq_Temp ADD FOREIGN KEY (id_partie) REFERENCES Partie (id_partie);

ALTER TABLE Tir ADD FOREIGN KEY (id_carte) REFERENCES Carte (id_carte);
ALTER TABLE Tir ADD FOREIGN KEY (id_joueur) REFERENCES JOUEUR (id_joueur);
ALTER TABLE Tir ADD FOREIGN KEY (id_partie, num_tour) REFERENCES Tour (id_partie, num_tour);

ALTER TABLE Tour ADD FOREIGN KEY (id_partie) REFERENCES Partie (id_partie);























