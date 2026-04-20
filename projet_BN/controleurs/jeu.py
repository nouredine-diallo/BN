from model.model_pg import  get_grille_joueur,  initialiser_grille_joueur, get_parties_en_cours, execute_select_query,get_etat_partie, get_tous_les_navires, get_navires_places, placer_navire, lancer_le_jeu , faire_tir,creer_tour,get_tour_courant,tirer_carte,passer_au_tour_suivant,faire_jouer_adversaire
    


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

    # ACTION
    if POST and 'action' in POST:
        action = POST['action'][0]
        
        if action == 'placer':
            #  placer un bateau
            id_nav = int(POST['id_navire'][0])
            coord = POST['coord'][0].upper() # Ex: "A5"
            sens = POST['sens'][0]
            y = coord[0]
            x = int(coord[1:])
            placer_navire(SESSION['CONNEXION'], id_nav, id_ma_grille, x, y, sens)
            REQUEST_VARS['message_jeu'] = f"Navire placé en {coord}."
            
        elif action == 'lancer':
            #  démarrer la partie 
            lancer_le_jeu(SESSION['CONNEXION'], id_partie)
            creer_tour(SESSION['CONNEXION'], id_partie, 1)
            etat_partie = 'En cours'
            REQUEST_VARS['message_jeu'] = "La partie commence ! À vos canons !"
            
        elif action == 'tirer':
            # --- 1. TOUR DU JOUEUR HUMAIN ---
            coord_cliquee = POST['coord'][0]
            lettre_y = coord_cliquee[0]
            chiffre_x = int(coord_cliquee[1:])
            
            num_tour_actuel = get_tour_courant(SESSION['CONNEXION'], id_partie)
            
            # On pioche et on tire
            carte_jh = tirer_carte(SESSION['CONNEXION'], id_partie)
            id_carte_jh = carte_jh['id_carte'] if carte_jh else None
            nom_carte_jh = carte_jh['code'] if carte_jh else ""C_MISSILE" 
            #pour l'instant on tire pas dans la bd une carte car non rempli du coup on affiche juste cmissile , a la phase 3 en s'en occupera 
            
            res_jh = faire_tir(SESSION['CONNEXION'], id_joueur_courant, id_partie, chiffre_x, lettre_y, num_tour_actuel, id_carte_jh)
            
            message_final = f"Carte jouée : {nom_carte_jh} | Ton tir en {coord_cliquee} : {res_jh}  "
            
            # --- 2. VÉRIFICATION FIN DE PARTIE ---
            # Si le jeu n'est pas terminé après ton tir, c'est à l'ordinateur de jouer !
            if "Gagnée" not in res_jh:
                
                # --- 3. TOUR DE L'ADVERSAIRE VIRTUEL ---
                # On passe au tour suivant en base de données
                passer_au_tour_suivant(SESSION['CONNEXION'], id_partie)
                
                # L'ordinateur joue
                coord_jv, res_jv = faire_jouer_adversaire(SESSION['CONNEXION'], id_partie, id_jv, id_joueur_courant)
                
                message_final += f"L'adversaire a tiré en {coord_jv} : {res_jv}"
            
            # On envoie le double message à l'interface
            REQUEST_VARS['message_jeu'] = message_final
    tous_navires = get_tous_les_navires(SESSION['CONNEXION']) or []
    navires_places = get_navires_places(SESSION['CONNEXION'], id_ma_grille) or []
    
    # deduis les navires non placer 
    ids_places = []
    for n in navires_places:
        ids_places.append(n['id_navire'])
        
    navires_a_placer = []
    for n in tous_navires:
        if n['id_navire'] not in ids_places:
            navires_a_placer.append(n)

    # determiner l'etat
    phase = 'jeu' if etat_partie == 'En cours' and len(navires_a_placer) == 0 else 'placement'

    # --- 4. PRÉPARATION DU PLATEAU (Dessin de ma grille) ---
    lettres = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    ma_grille_affichage = []
    
    # Génération de la grille vide
    for y in lettres:
        ligne = []
        for x in range(1, 11):
            ligne.append({'lettre': y, 'chiffre': x, 'id_case': f"{y}{x}", 'occupe': False})
        ma_grille_affichage.append(ligne)

    # On colorie en vert les cases occupées par les navires déjà placés
    for nav in navires_places:
        x_start = nav['coord_x']
        y_start_idx = lettres.index(nav['coord_y'])
        taille = nav['taille']
        
        for i in range(taille):
            x_curr = x_start + i if nav['sens'] == 'Horizontal' else x_start
            y_curr_idx = y_start_idx + i if nav['sens'] == 'Vertical' else y_start_idx
            
            # Sécurité pour ne pas déborder de la grille (0 à 9 pour Y, 1 à 10 pour X)
            if 0 <= y_curr_idx < 10 and 1 <= x_curr <= 10:
                ma_grille_affichage[y_curr_idx][x_curr - 1]['occupe'] = True

   
    REQUEST_VARS['id_partie'] = id_partie
    REQUEST_VARS['phase'] = phase
    REQUEST_VARS['ma_grille'] = ma_grille_affichage
    REQUEST_VARS['navires_a_placer'] = navires_a_placer
    REQUEST_VARS['flotte_complete'] = (len(navires_a_placer) == 0)
    if 'nom_carte_jh' in locals():
        REQUEST_VARS['nom_carte'] = nom_carte_jh