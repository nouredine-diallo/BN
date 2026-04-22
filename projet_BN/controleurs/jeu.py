from model.model_pg import  get_grille_joueur,  initialiser_grille_joueur, get_parties_en_cours, execute_select_query,get_etat_partie, get_tous_les_navires, get_navires_places, placer_navire, lancer_le_jeu , faire_tir,creer_tour,get_tour_courant,tirer_carte,passer_au_tour_suivant,faire_jouer_adversaire,get_tirs_partie,reprendre_partie,suspendre_partie,traiter_C_REJOUE,traiter_C_PASSE,traiter_C_VIDE,traiter_C_MPM,traiter_C_OUPS,traiter_C_MEGA,traiter_C_WILLY,traiter_C_LEURRE,traiter_C_ETOILE,placer_navires_ia
    


if 'id_joueur' not in SESSION:
    SESSION['id_joueur'] = 1

id_joueur_courant = SESSION['id_joueur']

id_partie = None
# On cherche l'ID dans l'URL 
if 'id' in GET:
    id_partie = GET['id'][0]
elif POST and 'id' in POST:
    id_partie = POST['id'][0]

if not id_partie:
    REQUEST_VARS['redirection'] = '/parties'
else:
    #  INITIALISATION 
    etat_partie = get_etat_partie(SESSION['CONNEXION'], id_partie)

    if etat_partie == 'Terminée':
        REQUEST_VARS['partie_terminee'] = True
        # On cherche qui a gagné
        q_gagnant = "SELECT id_jgagnant FROM Partie WHERE id_partie = %s"
        res_gagnant = execute_select_query(SESSION['CONNEXION'], q_gagnant, [id_partie])
        if res_gagnant and res_gagnant[0]['id_jgagnant'] == id_joueur_courant:
            REQUEST_VARS['message_fin'] = "🏆 FÉLICITATIONS ! Vous avez anéanti la flotte ennemie !"
        else:
            REQUEST_VARS['message_fin'] = "💀 DÉFAITE... L'ordinateur a coulé tous vos navires."
    
    # Récupération de l'adversaire
    q_adv = "SELECT id_jv FROM Partie WHERE id_partie = %s"
    res_adv = execute_select_query(SESSION['CONNEXION'], q_adv, [id_partie])
    id_jv = res_adv[0]['id_jv'] if res_adv else None

    # Récupération ou Création des grilles
    id_ma_grille = get_grille_joueur(SESSION['CONNEXION'], id_partie, id_joueur_courant)
    if not id_ma_grille:
        id_ma_grille = initialiser_grille_joueur(SESSION['CONNEXION'], id_partie, id_joueur_courant)
    id_grille_jv = get_grille_joueur(SESSION['CONNEXION'], id_partie, id_jv)
    if not id_grille_jv:
        initialiser_grille_joueur(SESSION['CONNEXION'], id_partie, id_jv)

    # --- AJOUT PHASE 2 : REPRISE AUTOMATIQUE ---
    if etat_partie == 'Suspendue':
        reprendre_partie(SESSION['CONNEXION'], id_partie)
        etat_partie = 'En cours'

    # ACTION
    if POST and 'action' in POST:
        action = POST['action'][0]
        
        # --- AJOUT PHASE 2 : BOUTON SUSPENDRE ---
        if action == 'suspendre':
            suspendre_partie(SESSION['CONNEXION'], id_partie)
            REQUEST_VARS['redirection'] = '/parties'
        # ----------------------------------------
        
        elif action == 'placer':
            id_nav = int(POST['id_navire'][0])
            coord = POST['coord'][0].upper()
            sens = POST['sens'][0]
            y = coord[0]
            x = int(coord[1:])
            placer_navire(SESSION['CONNEXION'], id_nav, id_ma_grille, x, y, sens)
            REQUEST_VARS['message_jeu'] = f"Navire placé en {coord}."
            
        elif action == 'lancer':
            lancer_le_jeu(SESSION['CONNEXION'], id_partie)
            creer_tour(SESSION['CONNEXION'], id_partie, 1)
            etat_partie = 'En cours'
            REQUEST_VARS['message_jeu'] = "La partie commence ! À vos canons !"
            
        elif action == 'tirer':
            coord_cliquee = POST['coord'][0]
            lettre_y = coord_cliquee[0]
            chiffre_x = int(coord_cliquee[1:])
            
            num_tour_actuel = get_tour_courant(SESSION['CONNEXION'], id_partie)
            
            # On pioche
            carte_jh = tirer_carte(SESSION['CONNEXION'], id_partie)
            id_carte_jh = carte_jh['id_carte'] if carte_jh else None
            nom_carte_jh = carte_jh['code'] if carte_jh else "C_MISSILE" 
            
            rejoue = False # Par défaut, le joueur ne rejoue pas
            
            
            match nom_carte_jh:
                case 'C_PASSE':
                    res_jh = traiter_C_PASSE(SESSION['CONNEXION'], id_joueur_courant, id_partie, num_tour_actuel, id_carte_jh)
                case 'C_REJOUE':
                    res_jh = traiter_C_REJOUE(SESSION['CONNEXION'], id_joueur_courant, id_partie, chiffre_x, lettre_y, num_tour_actuel, id_carte_jh)
                    rejoue = True  # Le joueur gagne le droit de rejouer !
                case 'C_VIDE':
                    res_jh = traiter_C_VIDE(SESSION['CONNEXION'], id_joueur_courant, id_partie, chiffre_x, lettre_y, num_tour_actuel, id_carte_jh)
                case 'C_MPM':
                    res_jh = traiter_C_MPM(SESSION['CONNEXION'], id_joueur_courant, id_partie, num_tour_actuel, id_carte_jh)
                case 'C_OUPS':
                    res_jh = traiter_C_OUPS(SESSION['CONNEXION'], id_joueur_courant, id_partie, chiffre_x, lettre_y, num_tour_actuel, id_carte_jh)

                case 'C_MEGA':
                    res_jh = traiter_C_MEGA(SESSION['CONNEXION'], id_joueur_courant, id_partie, chiffre_x, lettre_y, num_tour_actuel, id_carte_jh)
                case 'C_WILLY':
                    # Nécessite id_jv pour qu'il attaque ta propre flotte !
                    res_jh = traiter_C_WILLY(SESSION['CONNEXION'], id_joueur_courant, id_partie, num_tour_actuel, id_carte_jh, id_jv)
                case 'C_LEURRE':
                    # Pose le leurre aux coordonnées que tu as cliquées (mais sur TA grille)
                    res_jh = traiter_C_LEURRE(SESSION['CONNEXION'], id_joueur_courant, id_partie, chiffre_x, lettre_y, num_tour_actuel, id_carte_jh)
                case 'C_ETOILE':
                    # Nécessite id_jv pour regarder sa flotte
                    res_jh = traiter_C_ETOILE(SESSION['CONNEXION'], id_joueur_courant, id_partie, num_tour_actuel, id_carte_jh, id_jv)
                    
                # ------------------------

                case _: 
                    # Par défaut (C_MISSILE)
                    res_jh = faire_tir(SESSION['CONNEXION'], id_joueur_courant, id_partie, chiffre_x, lettre_y, num_tour_actuel, id_carte_jh)
                    res_jh = f"Tir en {coord_cliquee} : {res_jh}"

            message_final = f"Carte jouée : {nom_carte_jh} | {res_jh}"
            
            if "Gagnée" in res_jh:
                # --- MON TIR GAGNE ---
                etat_partie = "Terminée"
                REQUEST_VARS['partie_terminee'] = True
                REQUEST_VARS['message_fin'] = "🏆 FÉLICITATIONS ! Vous avez anéanti la flotte ennemie !"
                
            else:
                # Si je n'ai pas gagné et pas de carte C_REJOUE, l'adversaire joue
                if not rejoue:
                    passer_au_tour_suivant(SESSION['CONNEXION'], id_partie)
                    coord_jv, res_jv = faire_jouer_adversaire(SESSION['CONNEXION'], id_partie, id_jv, id_joueur_courant)
                    message_final += f" <br> L'adversaire a tiré en {coord_jv} : {res_jv}"
                    
                    # --- L'ADVERSAIRE GAGNE ---
                    if "Gagnée" in res_jv:
                        etat_partie = "Terminée"
                        REQUEST_VARS['partie_terminee'] = True
                        REQUEST_VARS['message_fin'] = "💀 DÉFAITE... L'ordinateur a coulé tous vos navires."
                        
                else:
                    # Le joueur a tiré C_REJOUE
                    message_final += " <br> ⚡ C'EST ENCORE À VOUS DE JOUER !"
            
            REQUEST_VARS['message_jeu'] = message_final

    # PREPARATION DES DONNEES
    tous_navires = get_tous_les_navires(SESSION['CONNEXION']) or []
    navires_places = get_navires_places(SESSION['CONNEXION'], id_ma_grille) or []
    navires_adv = get_navires_places(SESSION['CONNEXION'], id_grille_jv) or []
    historique_tirs = get_tirs_partie(SESSION['CONNEXION'], id_partie) or []
    
    ids_places = []
    for n in navires_places:
        ids_places.append(n['id_navire'])
        
    navires_a_placer = []
    for n in tous_navires:
        if n['id_navire'] not in ids_places:
            navires_a_placer.append(n)

    phase = 'jeu' if etat_partie == 'En cours' or etat_partie == 'Terminée' and len(navires_a_placer) == 0 else 'placement'

    # --- RECONSTRUCTION DU PLATEAU AVEC HISTORIQUE (PHASE 2) ---
    lettres = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    ma_grille_affichage = []
    
    for y in lettres:
        ligne = []
        for x in range(1, 11):
            # On prépare des variables d'état pour les deux grilles !
            ligne.append({
                'lettre': y, 'chiffre': x, 'id_case': f"{y}{x}", 
                'occupe': False,        # Mes navires
                'etat_ma_flotte': '',   # Impacts de l'adversaire ('' = rien, 'touche', 'flop')
                'etat_radar': ''        # Mes impacts chez l'adversaire ('' = rien, 'touche', 'flop')
            })
        ma_grille_affichage.append(ligne)

    # 1. On place nos navires visuellement
    for nav in navires_places:
        x_start = nav['coord_x']
        y_start_idx = lettres.index(nav['coord_y'])
        for i in range(nav['taille']):
            x_curr = x_start + i if nav['sens'] == 'Horizontal' else x_start
            y_curr_idx = y_start_idx + i if nav['sens'] == 'Vertical' else y_start_idx
            if 0 <= y_curr_idx < 10 and 1 <= x_curr <= 10:
                ma_grille_affichage[y_curr_idx][x_curr - 1]['occupe'] = True

    # 2. On repeint les grilles avec l'historique des tirs
    for tir in historique_tirs:
        # --- CORRECTION DU BUG : On ignore les tirs sans coordonnées (ex: C_PASSE) ---
        if tir['coord_x'] is None or tir['coord_y'] is None:
            continue
        # -----------------------------------------------------------------------------
        
        tx = tir['coord_x']
        ty_idx = lettres.index(tir['coord_y'])
        
        if tir['id_joueur'] == id_joueur_courant:
            # MON TIR sur le radar ennemi. Était-ce un touché ?
            touche = False
            for nav in navires_adv:
                nx = nav['coord_x']
                ny_idx = lettres.index(nav['coord_y'])
                for i in range(nav['taille']):
                    cx = nx + i if nav['sens'] == 'Horizontal' else nx
                    cy = ny_idx + i if nav['sens'] == 'Vertical' else ny_idx
                    if tx == cx and ty_idx == cy:
                        touche = True
                        break
            ma_grille_affichage[ty_idx][tx-1]['etat_radar'] = 'touche' if touche else 'flop'
        else:
            # TIR DE L'ADVERSAIRE sur ma flotte. Était-ce un touché ?
            # C'est facile, on regarde si la case était 'occupe'
            if ma_grille_affichage[ty_idx][tx-1]['occupe']:
                ma_grille_affichage[ty_idx][tx-1]['etat_ma_flotte'] = 'touche'
            else:
                ma_grille_affichage[ty_idx][tx-1]['etat_ma_flotte'] = 'flop'

    REQUEST_VARS['id_partie'] = id_partie
    REQUEST_VARS['phase'] = phase
    REQUEST_VARS['ma_grille'] = ma_grille_affichage
    REQUEST_VARS['navires_a_placer'] = navires_a_placer
    REQUEST_VARS['flotte_complete'] = (len(navires_a_placer) == 0)
    if 'nom_carte_jh' in locals():
        REQUEST_VARS['nom_carte'] = nom_carte_jh