import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from logzero import logger
import random

def execute_select_query(connexion , query , params=[]) :
    """Excuter une requete select """
    with connexion.cursor() as cursor : 
        try : 
            cursor.execute(query , params)
            cursor.row_factory=dict_row
            result = cursor.fetchall()
            return result 
        except psycopg.Error as e: 
            logger.error(e)
    return None 

def execute_other_query(connexion, query, params=[]):
    """
    Méthode générique pour exécuter une requête INSERT, UPDATE, DELETE.
    Utilisée par des fonctions plus spécifiques.
    """
    with connexion.cursor() as cursor:
        try:
            cursor.execute(query, params)
            result = cursor.rowcount
            return result 
        except psycopg.Error as e:
            logger.error(e)
    return None
def insert(connexion , query , params=[]) :
    """Methode pour insert avec pour return le id  """
    with connexion.cursor() as cursor : 
        try :
            cursor.execute(query , params)
            #on recup le id creer 
            result = cursor.fetchone()[0]
            return result 
        except psycopg.Error as e:
            logger.error(e)
    return None
        
def get_instances(connexion, nom_table):
    """
    Retourne les instances de la table nom_table
    String nom_table : nom de la table
    """
    query = sql.SQL('SELECT * FROM {table}').format(table=sql.Identifier(nom_table), )
    return execute_select_query(connexion, query)

def count_instances(connexion, nom_table):
    """
    Retourne le nombre d'instances de la table
    """
    query = sql.SQL('SELECT COUNT(*) AS nb FROM {table}').format(table=sql.Identifier(nom_table))
    return execute_select_query(connexion, query)

#Fonctions specifique au jeu Bataille Navale 
def get_stat_joueur(connexion, id_joueur):
    """
    Récupère les 6 statistiques obligatoires pour le joueur courant.
    """
    stats = {
        'nb_3_mois': 0,
        'victoires_par_niveau': [],
        'moy_tours': 0,
        'points_2026': 0,
        'cartes_par_type': [],
        'etoile_mort_10': 0
    }

    try:
        # 1. Nombre de parties finies sur les 3 derniers mois
        q1 = """SELECT count(id_partie) AS nb FROM Partie 
                WHERE id_jh = %s AND etat = 'Terminée' 
                AND date_creation >= CURRENT_DATE - INTERVAL '3 months'"""
        res1 = execute_select_query(connexion, q1, [id_joueur])
        if res1: stats['nb_3_mois'] = res1[0]['nb']

        # 2. Pour chaque niveau d'adversaire, le nombre de parties gagnées
        q2 = """SELECT v.niveau, count(p.id_partie) AS nb 
                FROM Partie p JOIN JOUEUR_Virtuel v ON p.id_jv = v.id_joueur 
                WHERE p.id_jgagnant = %s GROUP BY v.niveau ORDER BY v.niveau"""
        res2 = execute_select_query(connexion, q2, [id_joueur])
        if res2: stats['victoires_par_niveau'] = res2

        # 3. Le nombre moyen de tours par partie (CORRIGÉ avec COUNT(*))
        q3 = """SELECT AVG(nb_tour) AS moy FROM (
                    SELECT count(*) as nb_tour FROM Seq_Temp 
                    WHERE id_partie IN (SELECT id_partie FROM Partie WHERE id_jh = %s)
                    GROUP BY id_partie
                ) as sous_requete"""
        res3 = execute_select_query(connexion, q3, [id_joueur])
        if res3 and res3[0]['moy']: stats['moy_tours'] = round(float(res3[0]['moy']), 1)

        # 4. Nombre de points cumulés en 2026 (CORRIGÉ avec score_final)
        q4 = """SELECT SUM(score_final) as total 
                FROM Partie 
                WHERE id_jh = %s AND EXTRACT(YEAR FROM date_creation) = 2026"""
        res4 = execute_select_query(connexion, q4, [id_joueur])
        if res4 and res4[0]['total']: stats['points_2026'] = res4[0]['total']

        # 5. Cartes tirées (CORRIGÉ sans id_seq)
        q5 = """SELECT c.etat as type_carte, count(*) as nb 
                FROM Tir t JOIN Carte c ON t.id_carte = c.id_carte
                WHERE t.id_joueur = %s GROUP BY c.etat"""
        res5 = execute_select_query(connexion, q5, [id_joueur])
        if res5: stats['cartes_par_type'] = res5

        # 6. "Étoiles de la mort" sur les 10 dernières parties commencées
        q6 = """SELECT count(*) as nb FROM Tir t JOIN Carte c ON t.id_carte = c.id_carte
                WHERE c.etat ILIKE '%%étoile%%' AND t.id_partie IN (
                    SELECT id_partie FROM Partie WHERE id_jh = %s 
                    ORDER BY date_creation DESC LIMIT 10
                )"""
        res6 = execute_select_query(connexion, q6, [id_joueur])
        if res6: stats['etoile_mort_10'] = res6[0]['nb']

    except Exception as e:
        logger.error(f"Erreur requêtes stats: {e}")

    return stats

# --- FONCTIONS POUR LA PAGE "MES PARTIES" ---

def get_parties_en_cours(connexion, id_jh):
    """Récupère les parties 'En cours' du joueur courant."""
    q = """SELECT p.id_partie, j.pseudo as adversaire, p.date_creation 
           FROM Partie p JOIN JOUEUR j ON p.id_jv = j.id_joueur 
           WHERE p.id_jh = %s AND p.etat = 'En cours' 
           ORDER BY p.date_creation DESC, p.heure_creation DESC"""
    return execute_select_query(connexion, q, [id_jh])

def get_parties_terminees(connexion, id_joueur):
    """
    Récupère parties 'Terminé' 
    """
    query = """
        SELECT p.id_partie, p.date_creation, jv.pseudo AS adversaire, jg.pseudo AS gagnant
        FROM Partie p
        JOIN Joueur jv ON p.id_jv = jv.id_joueur
        LEFT JOIN Joueur jg ON p.id_jgagnant = jg.id_joueur
        WHERE p.id_jh = %s AND p.etat = 'Terminé'
        ORDER BY p.date_creation DESC
    """
    return execute_select_query(connexion, query, [id_joueur])




def get_jv(connexion):
    """Récupère la liste des adversaires virtuels pour le menu déroulant."""
    q = """SELECT j.id_joueur, j.pseudo, jv.niveau 
           FROM JOUEUR j JOIN JOUEUR_Virtuel jv ON j.id_joueur = jv.id_joueur 
           ORDER BY jv.niveau, j.pseudo"""
    return execute_select_query(connexion, q)



def creer_partie(connexion, id_jh, id_jv):
    """Créer une partie """
    q = """
        INSERT INTO Partie (id_partie, date_creation, heure_creation, etat, id_jv, id_jh) 
        VALUES ((SELECT COALESCE(MAX(id_partie), 0) + 1 FROM Partie), CURRENT_DATE, CURRENT_TIME, 'Créé', %s, %s) 
        RETURNING id_partie
    """
    return insert(connexion, q, [id_jv, id_jh])

def creer_pioche(connexion, id_partie, type_pioche="Distrib 1"):
    # 1. Créer l'entrée Pioche AVEC le calcul de l'ID (Spécifique à script1.sql)
    q_pioche = """
        INSERT INTO Pioche (id_pioche, id_partie, nom_distribution) 
        VALUES ((SELECT COALESCE(MAX(id_pioche), 0) + 1 FROM Pioche), %s, %s) 
        RETURNING id_pioche
    """
    id_pioche = insert(connexion, q_pioche, [id_partie, type_pioche])
    
    if not id_pioche:
        return None # Sécurité si l'insertion échoue
    
    # 2. Récupérer les proportions
    proportions = execute_select_query(connexion, "SELECT code, proportion FROM Est_compose WHERE nom_distribution = %s", [type_pioche])
    
    # 3. Générer la liste des 100 types de cartes
    liste_types = []
    if proportions:
        for prop in proportions:
            nb_cartes = int(prop['proportion'] * 100)
            for _ in range(nb_cartes):
                liste_types.append(prop['code'])
    
    # Sécurité au cas où
    while len(liste_types) < 100: 
        liste_types.append('C_MISSILE')
    
    # 4. Mélanger les rangs (1 à 100)
    rangs = list(range(1, 101))
    random.shuffle(rangs)
    
    # 5. Insertion des 100 cartes AVEC le calcul de l'ID
    q_carte = """
        INSERT INTO Carte (id_carte, id_pioche, code, rang, etat) 
        VALUES ((SELECT COALESCE(MAX(id_carte), 0) + 1 FROM Carte), %s, %s, %s, 'dans la pioche')
    """
    for i in range(100):
        execute_other_query(connexion, q_carte, [id_pioche, liste_types[i], rangs[i]])
        
    return id_pioche

def ajouter_joueur_virtuel(connexion, pseudo, niveau, id_createur):
    """Création du Double INSERT pour le JV."""
    q1 = """INSERT INTO JOUEUR (id_joueur, pseudo) 
            VALUES ((SELECT COALESCE(MAX(id_joueur), 0) + 1 FROM JOUEUR), %s) 
            RETURNING id_joueur"""
    id_genere = insert(connexion, q1, [pseudo])
    
    if id_genere:
        # Attention au nom exact de la colonne dans script1.sql : id_createur
        q2 = "INSERT INTO JOUEUR_Virtuel (id_joueur, niveau, id_createur) VALUES (%s, %s, %s)"
        execute_other_query(connexion, q2, [id_genere, niveau, id_createur])
        return id_genere
    return None

def chercher_joueur(connexion , pseudo_recherche) :
    q="""SELECT j.id_joueur, j.pseudo, jh.nom, jh.prenom, jh.date_naissance
        FROM JOUEUR j
        JOIN JOUEUR_humain jh ON j.id_joueur = jh.id_joueur
        WHERE j.pseudo LIKE %s
        ORDER BY j.pseudo"""
    motif = f"%{pseudo_recherche}%"
    return execute_select_query( connexion , q , [motif])

def ajouter_joueur_humain(connexion, pseudo, nom, prenom, date_naissance):
    """
    Inscrit un nouveau joueur humain
    """
    #  Insertion dans la table JOUEUR et récupération de ID
   
    q1 = """
        INSERT INTO JOUEUR (id_joueur, pseudo) 
        VALUES ((SELECT COALESCE(MAX(id_joueur), 0) + 1 FROM JOUEUR), %s) 
        RETURNING id_joueur
    """
    id_genere = insert(connexion, q1, [pseudo])
    
    if id_genere:
        # Insertion dans  JOUEUR_humain
        
        q2 = """
            INSERT INTO JOUEUR_humain (id_joueur, nom, prenom, date_naissance) 
            VALUES (%s, %s, %s, %s)
        """
        execute_other_query(connexion, q2, [id_genere, nom, prenom, date_naissance])
        return id_genere
        
    return None

def get_pseudo_joueur(connexion, id_joueur):
    """
    Récupère le pseudo d'un joueur pour la page acceuil .
    """
    q = "SELECT pseudo FROM JOUEUR WHERE id_joueur = %s"
    res = execute_select_query(connexion, q, [id_joueur])
    

    if res:
        return res[0]['pseudo']
    return None

#FONCTION POUR LE JEU 
def placer_navires_ia(connexion, id_grille):
    """Algorithme IA avec Logs de débuggage pour voir le placement secret."""
    navires = get_tous_les_navires(connexion)
    lettres = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    occupe = [[False for _ in range(10)] for _ in range(10)]

    logger.info("=== GÉNÉRATION DE LA FLOTTE IA (SECRET) ===")

    for nav in navires:
        taille = nav['taille']
        place = False
        
        while not place:
            sens = random.choice(['Horizontal', 'Vertical'])
            if sens == 'Horizontal':
                x = random.randint(1, 10 - taille + 1)
                y_idx = random.randint(0, 9)
            else:
                x = random.randint(1, 10)
                y_idx = random.randint(0, 10 - taille)

            collision = False
            for i in range(taille):
                cx = (x - 1 + i) if sens == 'Horizontal' else (x - 1)
                cy = y_idx if sens == 'Horizontal' else (y_idx + i)
                if occupe[cy][cx]:
                    collision = True
                    break
            
            if not collision:
                for i in range(taille):
                    cx = (x - 1 + i) if sens == 'Horizontal' else (x - 1)
                    cy = y_idx if sens == 'Horizontal' else (y_idx + i)
                    occupe[cy][cx] = True
                
                # Insertion en base
                q_place = "INSERT INTO Est_place (id_navire, id_grille, coord_X, coord_Y, sens) VALUES (%s, %s, %s, %s, %s)"
                execute_other_query(connexion, q_place, [nav['id_navire'], id_grille, x, lettres[y_idx], sens])
                
                # --- LE LOG DE DÉBUGGAGE ---
                logger.info(f"📍 IA : {nav['nom']} ({taille} cases) placé en {lettres[y_idx]}{x} [{sens}]")
                # ---------------------------
                
                place = True
    
    logger.info("============================================")

def initialiser_grille_joueur(connexion, id_partie, id_joueur):
    """Crée une grille 10x10 et place la flotte automatiquement si c'est l'IA."""
    # 1. Créer la Grille
    q_grille = """
        INSERT INTO Grille (id_grille, largeur, hauteur) 
        VALUES ((SELECT COALESCE(MAX(id_grille), 0) + 1 FROM Grille), 10, 10) 
        RETURNING id_grille
    """
    id_grille = insert(connexion, q_grille)
    
    if id_grille:
        # 2. Spécifier que c'est une grille pour placer des navires
        q_navire = "INSERT INTO Grille_navire (id_grille) VALUES (%s)"
        execute_other_query(connexion, q_navire, [id_grille])
        
        # 3. Lier la grille au joueur et à la partie
        q_lien = "INSERT INTO ou_placer (id_joueur, id_partie, id_grille) VALUES (%s, %s, %s)"
        execute_other_query(connexion, q_lien, [id_joueur, id_partie, id_grille])
        
        # --- L'AJOUT MAGIQUE : VÉRIFICATION DU TYPE DE JOUEUR ---
        # Si le joueur est présent dans JOUEUR_Virtuel, on lance l'algorithme
        q_verif_ia = "SELECT id_joueur FROM JOUEUR_Virtuel WHERE id_joueur = %s"
        est_ia = execute_select_query(connexion, q_verif_ia, [id_joueur])
        
        if est_ia:
            placer_navires_ia(connexion, id_grille)
        # --------------------------------------------------------
        
        return id_grille
    return None

def get_grille_joueur(connexion, id_partie, id_joueur):
    """Récupère l'ID de la grille d'un joueur pour une partie donnée."""
    q = "SELECT id_grille FROM ou_placer WHERE id_partie = %s AND id_joueur = %s"
    res = execute_select_query(connexion, q, [id_partie, id_joueur])
    return res[0]['id_grille'] if res else None

def placer_navire(connexion, id_navire, id_grille, coord_x, coord_y, sens):
    """
    Insère les coordonnées d'un navire sur la grille du joueur.
    coord_x : entier (1 à 10)
    coord_y : lettre (A à J)
    sens : 'Horizontal' ou 'Vertical'
    """
    q = """
        INSERT INTO Est_place (id_navire, id_grille, coord_X, coord_Y, sens) 
        VALUES (%s, %s, %s, %s, %s)
    """
    # Retourne le nombre de lignes insérées 1= succes 
    return execute_other_query(connexion, q, [id_navire, id_grille, coord_x, coord_y, sens])

def lancer_le_jeu(connexion, id_partie):
    """
    Met à jour l'état de la partie et démarre la première séquence temporelle.
    """
    # 1. On passe la partie en cours
    q_etat = "UPDATE Partie SET etat = 'En cours' WHERE id_partie = %s"
    execute_other_query(connexion, q_etat, [id_partie])

    # 2. On démarre la séquence temporelle
    q_seq = """
        INSERT INTO Seq_Temp (id_partie, date_debut, heure_debut) 
        VALUES (%s, CURRENT_DATE, CURRENT_TIME)
        ON CONFLICT (id_partie, date_debut) DO NOTHING
    """
    # ON CONFLICT DO NOTHING évite un crash si le joueur relance le jeu le même jour 
    # (bien que la logique de suspension/reprise gérera ça différemment plus tard)
    return execute_other_query(connexion, q_seq, [id_partie])
def get_etat_partie(connexion, id_partie):
    """Récupère l'état actuel de la partie"""
    q = "SELECT etat FROM Partie WHERE id_partie = %s"
    res = execute_select_query(connexion, q, [id_partie])
    return res[0]['etat'] if res else None

def get_tous_les_navires(connexion):
    """Récupère la liste des navires disponibles dans le jeu."""
    q = "SELECT id_navire, nom, taille FROM Navire ORDER BY taille DESC"
    return execute_select_query(connexion, q)

def get_navires_places(connexion, id_grille):
    """Récupère les navires déjà placés sur une grille."""
    q = """
        SELECT n.id_navire, n.nom, n.taille, ep.coord_x, ep.coord_y, ep.sens
        FROM Est_place ep
        JOIN Navire n ON ep.id_navire = n.id_navire
        WHERE ep.id_grille = %s
    """
    return execute_select_query(connexion, q, [id_grille])

def est_navire_coule(connexion, id_partie, id_grille_adv, id_navire):
    """
    Vérifie si un navire spécifique a été coulé.
    Renvoie True si coulé, False sinon.
    """
    q_nav = """
        SELECT n.taille, ep.coord_X, ep.coord_Y, ep.sens 
        FROM Est_place ep 
        JOIN Navire n ON ep.id_navire = n.id_navire 
        WHERE ep.id_grille = %s AND ep.id_navire = %s
    """
    navire = execute_select_query(connexion, q_nav, [id_grille_adv, id_navire])
    
    if not navire:
        return False
        
    taille = navire[0]['taille']
    nx = navire[0]['coord_x']
    ny_code = ord(navire[0]['coord_y'])
    sens = navire[0]['sens']
    
    tirs_reussis = 0
    # On récupère tous les tirs de la partie
    q_tirs = "SELECT coord_X, coord_Y FROM Tir WHERE id_partie = %s"
    tous_les_tirs = execute_select_query(connexion, q_tirs, [id_partie])
    
    if tous_les_tirs:
        for t in tous_les_tirs:
            if t['coord_y'] is None: 
                continue
            tx = t['coord_x']
            ty_code = ord(t['coord_y'])
            
            # Vérification si le tir est sur les coordonnées du navire
            if sens == 'Horizontal' and ty_code == ny_code:
                if nx <= tx < (nx + taille):
                    tirs_reussis += 1
            elif sens == 'Vertical' and tx == nx:
                if ny_code <= ty_code < (ny_code + taille):
                    tirs_reussis += 1
                    
    return tirs_reussis >= taille

def est_partie_finie(connexion, id_partie, id_grille_adv):
    """
    Vérifie si tous les navires de la grille adverse sont coulés.
    """
    navires_adv = get_navires_places(connexion, id_grille_adv)
    
    if not navires_adv:
        return False
        
    for nav in navires_adv:
        if not est_navire_coule(connexion, id_partie, id_grille_adv, nav['id_navire']):
            return False # Il reste au moins un navire en vie
            
    # Si on arrive ici, tous les navires sont coulés !
    q_fin = "UPDATE Partie SET etat = 'Terminée' WHERE id_partie = %s"
    execute_other_query(connexion, q_fin, [id_partie])
    return True
def faire_tir(connexion, id_joueur, id_partie, coord_x, coord_y, num_tour,id_carte=None):
    """
    Enregistre un tir dans le tour actuel et vérifie s'il touche, coule, ou gagne la partie.
    Retourne "Touché !", "Flop", "Coulé !" ou "Coulé et Partie Gagnée !".
    """
    resultat_tir = "Flop"
    id_navire_touche = None  # Variable pour mémoriser quel navire a été touché
    id_grille_adv = None

    # 1. On cherche la grille de l'adversaire
    q_adv = """
        SELECT id_grille FROM ou_placer 
        WHERE id_partie = %s AND id_joueur != %s
    """
    res_adv = execute_select_query(connexion, q_adv, [id_partie, id_joueur])
    
    if res_adv:
        id_grille_adv = res_adv[0]['id_grille']

        # 2. On récupère les navires placés sur cette grille adverse
        # AJOUT : On sélectionne aussi n.id_navire pour pouvoir l'identifier
        q_navires = """
            SELECT n.id_navire, ep.coord_X, ep.coord_Y, ep.sens, n.taille 
            FROM Est_place ep
            JOIN Navire n ON ep.id_navire = n.id_navire
            WHERE ep.id_grille = %s
        """
        navires_adv = execute_select_query(connexion, q_navires, [id_grille_adv])

        # 3. Vérification de la collision
        if navires_adv:
            for nav in navires_adv:
                nx = nav['coord_x']
                ny = nav['coord_y']
                taille = nav['taille']
                sens = nav['sens']
                id_nav = nav['id_navire']  # On extrait l'ID du navire
                
                # Si le bateau est Horizontal = X augmente
                if sens == 'Horizontal' and ny == coord_y:
                    if nx <= coord_x < (nx + taille):
                        resultat_tir = "Touché !"
                        id_navire_touche = id_nav  # On mémorise le navire touché
                        break
                
                # Si le bateau est Vertical = Y augmente (A->B->C...)
                elif sens == 'Vertical' and nx == coord_x:
                    # On convertit les lettres en code ASCII pour comparer (A=65, B=66...)
                    if ord(ny) <= ord(coord_y) < (ord(ny) + taille):
                        resultat_tir = "Touché !"
                        id_navire_touche = id_nav  # On mémorise le navire touché
                        break

    # --- [AJOUT DE SÉCURITÉ ICI] ---
    # On vérifie si le tour existe en base avant d'insérer le tir
    q_check_tour = "SELECT 1 FROM Tour WHERE id_partie = %s AND num_tour = %s"
    if not execute_select_query(connexion, q_check_tour, [id_partie, num_tour]):
        # Le tour n'existe pas, on le crée pour éviter l'erreur de contrainte SQL !
        creer_tour(connexion, id_partie, num_tour)
    # -------------------------------

    # 4. Enregistrement du tir dans la table 'Tir'
    # On calcule le numéro du tir actuel POUR CE TOUR PRÉCIS
    q_numtir = "SELECT COALESCE(MAX(num_tir), 0) + 1 AS next_tir FROM Tir WHERE id_partie = %s AND num_tour = %s"
    res_numtir = execute_select_query(connexion, q_numtir, [id_partie, num_tour])
    num_tir = res_numtir[0]['next_tir'] if res_numtir else 1
    
    # On insère le tir en utilisant la variable num_tour
    q_insert = """
        INSERT INTO Tir (id_partie, num_tour, num_tir, coord_X, coord_Y, id_joueur, id_carte)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    execute_other_query(connexion, q_insert, [id_partie, num_tour, num_tir, coord_x, coord_y, id_joueur, id_carte])
    
    # 5. --- AJOUT DES PRÉDICATS (Coulé et Fin de partie) ---
    # On fait ces vérifications uniquement si un navire a été percuté par CE tir
    if id_navire_touche is not None:
        # Prédicat 1 : Ce navire est-il complètement coulé ?
        if est_navire_coule(connexion, id_partie, id_grille_adv, id_navire_touche):
            resultat_tir = "Coulé !"
            
            # Prédicat 2 : Si un navire vient de couler, est-ce que c'était le dernier ?
            if est_partie_finie(connexion, id_partie, id_grille_adv):
                resultat_tir = "Coulé et Partie Gagnée !"
                
    return resultat_tir

def creer_tour(connexion, id_partie, num_tour):
    """Initialise un nouveau tour dans la base de données."""
    q = """
        INSERT INTO Tour (id_partie, num_tour, nb_navire_coule, nb_navire_touche, nb_cellule_libre1, nb_cellule_libre2) 
        VALUES (%s, %s, 0, 0, 100, 100)
        ON CONFLICT (id_partie, num_tour) DO NOTHING
    """
    return execute_other_query(connexion, q, [id_partie, num_tour])

def get_tour_courant(connexion, id_partie):
    """Récupère le numéro du tour le plus récent pour une partie donnée."""
    q = "SELECT MAX(num_tour) as current_tour FROM Tour WHERE id_partie = %s"
    res = execute_select_query(connexion, q, [id_partie])
    return res[0]['current_tour'] if res and res[0]['current_tour'] else 1

def tirer_carte(connexion, id_partie):
    """
    Récupère la prochaine carte de la pioche de la partie et la marque comme 'jouée'.
    Retourne un dictionnaire avec 'id_carte' et 'code', ou None.
    """
    # 1. On cherche l'ID de la pioche liée à la partie
    q_pioche = "SELECT id_pioche FROM Pioche WHERE id_partie = %s"
    res_pioche = execute_select_query(connexion, q_pioche, [id_partie])
    
    if not res_pioche:
        return None
        
    id_pioche = res_pioche[0]['id_pioche']
    
    # 2. On prend la première carte non jouée (on trie par rang)
    q_carte = """
        SELECT id_carte, code 
        FROM Carte 
        WHERE id_pioche = %s AND (etat IS NULL OR etat != 'jouee') 
        ORDER BY rang ASC 
        LIMIT 1
    """
    res_carte = execute_select_query(connexion, q_carte, [id_pioche])
    
    if res_carte:
        carte = res_carte[0]
        # 3. On met à jour l'état de la carte pour la "consommer"
        q_update = "UPDATE Carte SET etat = 'jouee' WHERE id_carte = %s"
        execute_other_query(connexion, q_update, [carte['id_carte']])
        return carte
        
    return None

def passer_au_tour_suivant(connexion, id_partie):
    """
    Incrémente le numéro du tour et l'enregistre en base.
    """
    tour_actuel = get_tour_courant(connexion, id_partie)
    nouveau_tour = tour_actuel + 1
    creer_tour(connexion, id_partie, nouveau_tour)
    return nouveau_tour

def faire_jouer_adversaire(connexion, id_partie, id_jv, id_jh):
    """
    Fait jouer l'adversaire virtuel : il pioche et tire au hasard.
    """
    tour_actuel = get_tour_courant(connexion, id_partie)
    
    # 1. Le JV pioche une carte (Phase 1 = toujours un C_MISSILE)
    carte = tirer_carte(connexion, id_partie)
    id_carte = carte['id_carte'] if carte else None
    
    # 2. coordeoner aleatoire pour tir
    lettres = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    lettre_y = random.choice(lettres)
    chiffre_x = random.randint(1, 10)
    coord_tir = f"{lettre_y}{chiffre_x}"
    
    # 3 tir jv sur grille jh
    resultat = faire_tir(connexion, id_jv, id_partie, chiffre_x, lettre_y, tour_actuel, id_carte)
    
    return coord_tir, resultat


def suspendre_partie(connexion, id_partie):
    """Suspend la partie et ferme la séquence temporelle courante."""
    # 1. On change l'état de la partie
    q_etat = "UPDATE Partie SET etat = 'Suspendue' WHERE id_partie = %s"
    execute_other_query(connexion, q_etat, [id_partie])

    # 2. On clôture la séquence temporelle en cours (celle qui n'a pas de date_fin)
    q_seq = """
        UPDATE Seq_Temp 
        SET date_fin = CURRENT_DATE, heure_fin = CURRENT_TIME 
        WHERE id_partie = %s AND date_fin IS NULL
    """
    return execute_other_query(connexion, q_seq, [id_partie])

def reprendre_partie(connexion, id_partie):
    """Reprend une partie suspendue en ouvrant une nouvelle séquence temporelle."""
    # 1. On remet la partie En cours
    q_etat = "UPDATE Partie SET etat = 'En cours' WHERE id_partie = %s"
    execute_other_query(connexion, q_etat, [id_partie])

    # 2. On crée une nouvelle séquence temporelle pour cette nouvelle session de jeu
    q_seq = """
        INSERT INTO Seq_Temp (id_partie, date_debut, heure_debut) 
        VALUES (%s, CURRENT_DATE, CURRENT_TIME)
    """
    return execute_other_query(connexion, q_seq, [id_partie])

def get_tirs_partie(connexion, id_partie):
    """Récupère l'historique de tous les tirs pour reconstruire les grilles visuellement."""
    q = "SELECT coord_X, coord_Y, id_joueur FROM Tir WHERE id_partie = %s"
    return execute_select_query(connexion, q, [id_partie])

def traiter_C_REJOUE(connexion, id_joueur, id_partie, coord_x, coord_y, num_tour, id_carte):
    """Primitive pour C_REJOUE : Effectue un tir simple, le contrôleur gérera le fait de rejouer."""
    res = faire_tir(connexion, id_joueur, id_partie, coord_x, coord_y, num_tour, id_carte)
    return f"Tir en {coord_y}{coord_x} : {res}"

def traiter_C_PASSE(connexion, id_joueur, id_partie, num_tour, id_carte):
    """Primitive pour C_PASSE : Le joueur ne tire pas, mais on enregistre la carte jouée."""
    q_numtir = "SELECT COALESCE(MAX(num_tir), 0) + 1 AS next_tir FROM Tir WHERE id_partie = %s AND num_tour = %s"
    res_numtir = execute_select_query(connexion, q_numtir, [id_partie, num_tour])
    num_tir = res_numtir[0]['next_tir'] if res_numtir else 1
    
    q_insert = """
        INSERT INTO Tir (id_partie, num_tour, num_tir, coord_X, coord_Y, id_joueur, id_carte)
        VALUES (%s, %s, %s, NULL, NULL, %s, %s)
    """
    execute_other_query(connexion, q_insert, [id_partie, num_tour, num_tir, id_joueur, id_carte])
    return "Oups ! Vous passez votre tour."

def traiter_C_VIDE(connexion, id_joueur, id_partie, coord_x, coord_y, num_tour, id_carte):
    """Primitive pour C_VIDE : Le tir part, s'enregistre, mais ne touche jamais rien (Flop garanti)."""
    q_numtir = "SELECT COALESCE(MAX(num_tir), 0) + 1 AS next_tir FROM Tir WHERE id_partie = %s AND num_tour = %s"
    res_numtir = execute_select_query(connexion, q_numtir, [id_partie, num_tour])
    num_tir = res_numtir[0]['next_tir'] if res_numtir else 1
    
    q_insert = """
        INSERT INTO Tir (id_partie, num_tour, num_tir, coord_X, coord_Y, id_joueur, id_carte)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    execute_other_query(connexion, q_insert, [id_partie, num_tour, num_tir, coord_x, coord_y, id_joueur, id_carte])
    return "Pffft... La carte était vide. Flop garanti !"

def traiter_C_MPM(connexion, id_joueur, id_partie, num_tour, id_carte):
    """Primitive pour C_MPM : Le missile se perd et frappe une coordonnée 100% aléatoire."""
    lettres = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    lettre_y = random.choice(lettres)
    chiffre_x = random.randint(1, 10)
    
    # On utilise ton faire_tir classique, mais avec les coordonnées aléatoires !
    res = faire_tir(connexion, id_joueur, id_partie, chiffre_x, lettre_y, num_tour, id_carte)
    return f"Missile perdu ! Il a frappé au hasard en {lettre_y}{chiffre_x} : {res}"

def traiter_C_OUPS(connexion, id_joueur, id_partie, coord_x, coord_y, num_tour, id_carte):
    """Primitive pour C_OUPS : Le joueur tire sur sa propre grille !"""
    # Pour simuler ça facilement, on dit à la base de données que c'est l'adversaire (l'ordinateur) 
    # qui a fait le tir à ta place sur TA coordonnée !
    
    # 1. On cherche l'ID de l'adversaire
    q_adv = "SELECT id_jv FROM Partie WHERE id_partie = %s"
    res_adv = execute_select_query(connexion, q_adv, [id_partie])
    id_jv = res_adv[0]['id_jv']
    
    # 2. L'adversaire tire sur toi avec ta carte !
    res = faire_tir(connexion, id_jv, id_partie, coord_x, coord_y, num_tour, id_carte)
    return f"OUPS ! Vous avez tiré sur votre propre flotte en {coord_y}{coord_x} : {res}"



def traiter_C_MEGA(connexion, id_joueur, id_partie, coord_x, coord_y, num_tour, id_carte):
    """Primitive pour C_MEGA : Tire sur 3x3 cases. Respecte le UNIQUE(id_carte) en SQL."""
    lettres = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    idx_y = lettres.index(coord_y)
    impacts = []
    
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            ny_idx = idx_y + dy
            nx = coord_x + dx
            
            # Vérifier qu'on ne sort pas de la grille 10x10
            if 0 <= ny_idx < 10 and 1 <= nx <= 10:
                ny_lettre = lettres[ny_idx]
                
                # ASTUCE SQL : On attribue l'id_carte UNIQUEMENT au tir central pour éviter l'erreur UNIQUE(id_carte) de script1.sql
                carte_a_inserer = id_carte if (dx == 0 and dy == 0) else None
                
                res = faire_tir(connexion, id_joueur, id_partie, nx, ny_lettre, num_tour, carte_a_inserer)
                if "Touché" in res or "Coulé" in res or "Gagnée" in res:
                    impacts.append(f"{ny_lettre}{nx}")
                    
    if impacts:
        return f"EXPLOSION NUCLÉAIRE ! Navires touchés en : {', '.join(impacts)}"
    return "Gros boum... mais que de l'eau. Flop magistral !"

def traiter_C_WILLY(connexion, id_joueur, id_partie, num_tour, id_carte, id_jv):
    """Primitive pour C_WILLY : Place une orque et attaque la propre grille du joueur."""
    id_ma_grille = get_grille_joueur(connexion, id_partie, id_joueur)
    navires = get_navires_places(connexion, id_ma_grille)

    if not navires:
        return "Willy a faim, mais vous n'avez aucun bateau à croquer !"

    # 1. On choisit une victime parmi NOS navires
    nav_victime = random.choice(navires)
    nx = nav_victime['coord_x']
    ny = nav_victime['coord_y']

    # 2. Gestion de la table 'Orque' et 'Contient_orque' (selon script1.sql)
    q_orque = "SELECT id_orque FROM Orque LIMIT 1"
    res_orque = execute_select_query(connexion, q_orque)
    # S'il n'y a pas d'orque en base, on en crée un
    id_orque = res_orque[0]['id_orque'] if res_orque else insert(connexion, "INSERT INTO Orque (nom) VALUES ('Willy') RETURNING id_orque")
    
    # On insère l'orque sur la grille (on ignore l'erreur si elle y est déjà)
    try:
        execute_other_query(connexion, "INSERT INTO Contient_orque (id_grille, id_orque, coord_X, coord_Y) VALUES (%s, %s, %s, %s)", [id_ma_grille, id_orque, nx, ny])
    except:
        pass

    # 3. L'ordinateur (id_jv) effectue un tir forcé sur NOTRE navire
    res = faire_tir(connexion, id_jv, id_partie, nx, ny, num_tour, id_carte)
    return f"C_WILLY a attiré une Orque sur votre grille en {ny}{nx} ! ({res})"

def traiter_C_LEURRE(connexion, id_joueur, id_partie, coord_x, coord_y, num_tour, id_carte):
    """Primitive pour C_LEURRE : Ajoute un leurre dans la table Leurre de script1.sql."""
    id_ma_grille = get_grille_joueur(connexion, id_partie, id_joueur)

    # 1. Obtenir le prochain numéro de leurre pour cette grille
    q_num = "SELECT COALESCE(MAX(num_L), 0) + 1 AS next_l FROM Leurre WHERE id_grille = %s"
    res_num = execute_select_query(connexion, q_num, [id_ma_grille])
    num_l = res_num[0]['next_l']

    # 2. Insérer dans la table Leurre
    q_insert_leurre = "INSERT INTO Leurre (id_grille, num_L, taille, coord_X, coord_Y, sens) VALUES (%s, %s, 1, %s, %s, 'Horizontal')"
    execute_other_query(connexion, q_insert_leurre, [id_ma_grille, num_l, coord_x, coord_y])

    # 3. Enregistrer l'utilisation de la carte dans Tir (coordonnées NULL car on n'attaque pas l'adversaire)
    q_tir = "INSERT INTO Tir (id_partie, num_tour, num_tir, coord_X, coord_Y, id_joueur, id_carte) VALUES (%s, %s, (SELECT COALESCE(MAX(num_tir), 0) + 1 FROM Tir WHERE id_partie = %s AND num_tour = %s), NULL, NULL, %s, %s)"
    execute_other_query(connexion, q_tir, [id_partie, num_tour, id_partie, num_tour, id_joueur, id_carte])

    return f"Vous avez posé un C_LEURRE en {coord_y}{coord_x} sur votre propre grille !"

def traiter_C_ETOILE(connexion, id_joueur, id_partie, num_tour, id_carte, id_jv):
    """Primitive pour C_ETOILE : Révèle une case ennemie sans tirer."""
    # 1. Consommer la carte
    q_tir = "INSERT INTO Tir (id_partie, num_tour, num_tir, coord_X, coord_Y, id_joueur, id_carte) VALUES (%s, %s, (SELECT COALESCE(MAX(num_tir), 0) + 1 FROM Tir WHERE id_partie = %s AND num_tour = %s), NULL, NULL, %s, %s)"
    execute_other_query(connexion, q_tir, [id_partie, num_tour, id_partie, num_tour, id_joueur, id_carte])

    # 2. Fouiller secrètement la grille de l'adversaire (id_jv)
    id_grille_adv = get_grille_joueur(connexion, id_partie, id_jv)
    navires_adv = get_navires_places(connexion, id_grille_adv)

    if navires_adv:
        nav = random.choice(navires_adv)
        return f"✨ C_ETOILE révèle un signal fort sur la ligne {nav['coord_y']}..."
    return "✨ Le radar de C_ETOILE ne trouve rien."







#TEST UNITAIRES 
if __name__=='__main__':
    print("TEST UNITAIRE")
    try : 
        connection = psycopg.connect(dbname="p2205230", user="p2205230", password="0gLkLmhGv0qc", host="bd-pedago.univ-lyon1.fr", options="-c search_path=bn")
        id = 4
        print(f"Voici les stat du joueur de id {id}")
        print(f"{get_stat_joueur(connection , id)}")
        print("TEST CREATION JOUEUR ")
        id_jv_cree = ajouter_joueur_virtuel(connection , "TESTEUR" , 5, id)
        print(f"Voici le id du jv creer {id_jv_cree}")
        if id_jv_cree : 
            id_partie=creer_partie(connection , id,id_jv_cree) 
            print(f"Voici le id le de la partie cree {id_partie}")
            
            if id_partie : 
                id_pioche = creer_pioche(connection , id_partie , "Classique")
                print(f" Voici le id de la picohe creer {id_pioche}")
        connection.rollback() #on annule des test pour avoir la bd propre 
        connection.close()
        print("Fin ")
        
    except Exception as e:
        print(f"Erreur : {e}")