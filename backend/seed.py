"""
Script de peuplement de la base de données avec ~100 utilisateurs factices.
Usage: cd backend && python seed.py
Mot de passe unique pour tous les utilisateurs : C
"""

import random
import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
from passlib.context import CryptContext
import models
from datetime import datetime, timedelta

# Recréer les tables
models.Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
HASHED_PASSWORD = pwd_context.hash("C")

# --- DONNÉES RÉALISTES ---

PRENOMS = [
    "Emma", "Lucas", "Jade", "Hugo", "Louise", "Léo", "Alice", "Gabriel",
    "Chloé", "Raphaël", "Lina", "Arthur", "Manon", "Louis", "Rose", "Jules",
    "Ambre", "Adam", "Léa", "Ethan", "Anna", "Nathan", "Zoé", "Tom",
    "Inès", "Noah", "Camille", "Théo", "Sarah", "Mathis", "Juliette", "Maxime",
    "Eva", "Axel", "Clara", "Rayan", "Mia", "Enzo", "Lola", "Sacha",
    "Margot", "Nolan", "Charlotte", "Paul", "Agathe", "Timéo", "Lucie", "Robin",
    "Nina", "Victor", "Lily", "Gabin", "Elena", "Mael", "Romane", "Aaron",
    "Elise", "Liam", "Célia", "Baptiste", "Luna", "Eliott", "Victoire", "Clément",
    "Iris", "Oscar", "Sofia", "Valentin", "Nora", "Samuel", "Capucine", "Mathéo",
    "Apolline", "Alexis", "Adèle", "Tristan", "Pauline", "Dorian", "Emilie",
    "Quentin", "Jeanne", "Martin", "Diane", "Antoine", "Océane", "Simon",
    "Elsa", "Benjamin", "Constance", "Corentin", "Marine", "Dylan", "Anaïs",
    "Romain", "Marguerite", "Kylian", "Hélène", "Pierre", "Aurélie", "Bastien"
]

NOMS = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit",
    "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel",
    "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier", "Morel",
    "Girard", "André", "Mercier", "Dupont", "Lambert", "Bonnet", "François",
    "Martinez", "Legrand", "Garnier", "Faure", "Rousseau", "Blanc", "Guérin",
    "Muller", "Henry", "Roussel", "Nicolas", "Perrin", "Morin", "Mathieu",
    "Clément", "Gauthier", "Dumont", "Lopez", "Fontaine", "Chevalier", "Robin",
    "Masson"
]

PROFILE_IMAGES = ["plante1.png", "plante2.png", "plante3.png", "plante4.png", "plante5.png", "plante6.png"]

LEAGUE_NAMES = [
    "Éco-Warriors", "Les Verts", "Green Team", "Planète Verte",
    "Zéro Carbone", "Les Éco-Citoyens", "GreenPeace Gang",
    "Les Colibris", "Défi Climat", "Team Recyclage",
    "Les Terriens", "EcoChallenge", "Nature First",
    "Génération Verte", "Les Décroissants", "Bio Team",
    "Les Engagés", "Objectif 2 Tonnes", "Slow Life Club",
    "Les Minimalistes"
]

# Catégories NGC
CATEGORIES = ["transport", "logement", "alimentation", "divers"]

# Missions IDs par catégorie (ceux définis dans MISSIONS_DB de routes.py)
MISSION_IDS = {
    "transport": [100, 101, 102, 103, 104, 105],
    "logement": [200, 201, 202, 203, 204, 205, 206, 207],
    "alimentation": [300, 301, 302, 303, 304, 305, 306, 307, 308, 309],
    "divers": [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410],
}

ALL_MISSION_IDS = []
for ids in MISSION_IDS.values():
    ALL_MISSION_IDS.extend(ids)


def generate_username(prenom: str, nom: str, index: int) -> str:
    """Génère un pseudo unique basé sur le prénom"""
    base = prenom.lower().replace("é", "e").replace("è", "e").replace("ê", "e") \
                         .replace("ë", "e").replace("à", "a").replace("â", "a") \
                         .replace("ô", "o").replace("î", "i").replace("ï", "i") \
                         .replace("ù", "u").replace("û", "u").replace("ü", "u") \
                         .replace("ç", "c")
    suffixes = ["", str(random.randint(1, 99)), nom[0].lower(), f"_{random.randint(1, 9)}"]
    return f"{base}{random.choice(suffixes)}"


def seed():
    db = SessionLocal()

    # Initialiser les données statiques (missions, trophées, catégories)
    # comme le fait le startup du serveur FastAPI
    from routes import init_db_from_static_data
    init_db_from_static_data(db)
    print("   ✅ Données statiques initialisées (missions, trophées, catégories)")

    # Vérifier si déjà peuplé
    existing_users = db.query(models.User).count()
    if existing_users >= 50:
        print(f"⚠️  La base contient déjà {existing_users} utilisateurs. Abandonné.")
        print("   Supprimez sql_app.db et relancez pour repartir de zéro.")
        db.close()
        return

    print("🌱 Début du peuplement de la base de données...")

    # ================================================
    # 1. CRÉER LES UTILISATEURS (~100)
    # ================================================
    NUM_USERS = 100
    users = []
    usernames_used = set()

    for i in range(NUM_USERS):
        prenom = PRENOMS[i % len(PRENOMS)]
        nom = random.choice(NOMS)

        # Générer un username unique
        username = generate_username(prenom, nom, i)
        attempt = 0
        while username in usernames_used:
            username = f"{username}{random.randint(10, 99)}"
            attempt += 1
            if attempt > 10:
                username = f"user{i}"
                break
        usernames_used.add(username)

        user = models.User(
            email=f"{username}@ecoapp.fr",
            username=username,
            first_name=prenom,
            last_name=nom,
            hashed_password=HASHED_PASSWORD,
            is_active=True,
            is_deleted=False,
            profile_image=random.choice(PROFILE_IMAGES),
            xp=random.randint(0, 800),
        )
        db.add(user)
        users.append(user)

    db.commit()
    for u in users:
        db.refresh(u)

    user_ids = [u.id for u in users]
    print(f"   ✅ {len(users)} utilisateurs créés (mot de passe: 'C')")

    # ================================================
    # 2. CRÉER DES STATS NGC pour chaque utilisateur
    # ================================================
    for user in users:
        # Score global entre 3000 et 12000 kgCO2
        global_score = random.randint(3000, 12000)
        transport = random.randint(500, 3500)
        logement = random.randint(400, 2500)
        alimentation = random.randint(600, 3000)
        divers = random.randint(300, 2000)
        services = global_score - transport - logement - alimentation - divers
        if services < 0:
            services = random.randint(800, 1500)

        ngc_stat = models.UserNgcStat(
            user_id=user.id,
            global_score=global_score,
            transport=transport,
            logement=logement,
            alimentation=alimentation,
            divers=divers,
            services_societaux=services,
            updated_at=datetime.now() - timedelta(days=random.randint(0, 30)),
        )
        db.add(ngc_stat)

        # NGC progress
        ngc_progress = models.UserNgcProgress(
            user_id=user.id,
            transport=random.randint(0, 100),
            logement=random.randint(0, 100),
            alimentation=random.randint(0, 100),
            divers=random.randint(0, 100),
            updated_at=datetime.now() - timedelta(days=random.randint(0, 15)),
        )
        db.add(ngc_progress)

    db.commit()
    print("   ✅ Stats NGC créées pour tous les utilisateurs")

    # ================================================
    # 3. CRÉER DES AMITIÉS (FriendLink + FriendRequest accepted)
    # ================================================
    friend_pairs = set()
    num_friendships = 350  # ~7 amis en moyenne par utilisateur

    for _ in range(num_friendships):
        u1, u2 = random.sample(user_ids, 2)
        pair = (min(u1, u2), max(u1, u2))
        if pair in friend_pairs:
            continue
        friend_pairs.add(pair)

        # FriendLink (stocké normalisé)
        link = models.FriendLink(user_id=pair[0], friend_id=pair[1])
        db.add(link)

        # FriendRequest accepted correspondante
        req = models.FriendRequest(
            sender_id=pair[0],
            receiver_id=pair[1],
            status="accepted",
        )
        db.add(req)

    # Ajouter quelques demandes pending pour le réalisme
    for _ in range(40):
        u1, u2 = random.sample(user_ids, 2)
        pair = (min(u1, u2), max(u1, u2))
        if pair in friend_pairs:
            continue
        friend_pairs.add(pair)

        req = models.FriendRequest(
            sender_id=u1,
            receiver_id=u2,
            status="pending",
        )
        db.add(req)

    db.commit()
    print(f"   ✅ {num_friendships} amitiés créées + 40 demandes en attente")

    # ================================================
    # 4. MISSIONS RÉALISÉES
    # ================================================
    mission_count = 0
    for user in users:
        # Chaque utilisateur complète entre 2 et 15 missions
        num_missions = random.randint(2, 15)
        chosen_missions = random.sample(ALL_MISSION_IDS, min(num_missions, len(ALL_MISSION_IDS)))

        for mid in chosen_missions:
            status_choice = random.choices(
                ["termine", "en_cours", "new"],
                weights=[0.6, 0.25, 0.15],
                k=1
            )[0]

            completed_at = None
            if status_choice == "termine":
                completed_at = datetime.now() - timedelta(
                    days=random.randint(1, 60),
                    hours=random.randint(0, 23),
                )

            ms = models.UserMissionStatus(
                user_id=user.id,
                mission_id=mid,
                status=status_choice,
                completed_at=completed_at,
            )
            db.add(ms)
            mission_count += 1

    db.commit()
    print(f"   ✅ {mission_count} statuts de missions créés")

    # ================================================
    # 5. PRÉFÉRENCES UTILISATEUR
    # ================================================
    pref_keys = [
        "possession_voiture", "possession_velo", "prend_avion",
        "passoire_thermique", "est_proprietaire", "vit_en_maison",
        "viande_rouge_importante", "conso_pas_locaux", "conso_pas_saison",
        "eau_bouteille", "boissons_chaudes", "dechets_importants",
        "soda", "shopping_important", "fumeur"
    ]
    for user in users:
        data = {}
        for key in pref_keys:
            data[key] = random.choice([True, False])

        pref = models.UserPreference(
            user_id=user.id,
            data=data,
            has_completed_onboarding=random.choice([True, True, True, False]),  # 75% ont complété
        )
        db.add(pref)

    db.commit()
    print("   ✅ Préférences utilisateurs créées")

    # ================================================
    # 6. LIGUES
    # ================================================
    leagues_created = []
    now = datetime.now()

    for i, league_name in enumerate(LEAGUE_NAMES):
        creator = random.choice(users)

        # Certaines ligues sont terminées, d'autres en cours, d'autres futures
        if i < 7:
            # Ligues terminées (archivées)
            start = now - timedelta(days=random.randint(30, 60))
            end = now - timedelta(days=random.randint(1, 15))
            is_archived = True
        elif i < 15:
            # Ligues en cours
            start = now - timedelta(days=random.randint(1, 14))
            end = now + timedelta(days=random.randint(3, 21))
            is_archived = False
        else:
            # Ligues futures
            start = now + timedelta(days=random.randint(1, 10))
            end = now + timedelta(days=random.randint(14, 45))
            is_archived = False

        league = models.League(
            name=league_name,
            start_date=start.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
            is_archived=is_archived,
            created_at=start - timedelta(days=random.randint(1, 5)),
            creator_id=creator.id,
            rewards_distributed=is_archived,
        )
        db.add(league)
        db.commit()
        db.refresh(league)

        # Ajouter le créateur comme membre
        member = models.LeagueMember(
            league_id=league.id,
            user_id=creator.id,
            joined_at=start - timedelta(days=random.randint(0, 3)),
        )
        db.add(member)

        # Ajouter entre 3 et 15 membres supplémentaires
        num_members = random.randint(3, 15)
        potential_members = [u for u in users if u.id != creator.id]
        extra_members = random.sample(potential_members, min(num_members, len(potential_members)))

        for m_user in extra_members:
            member = models.LeagueMember(
                league_id=league.id,
                user_id=m_user.id,
                joined_at=start + timedelta(hours=random.randint(1, 72)),
            )
            db.add(member)

        leagues_created.append(league)

    db.commit()
    print(f"   ✅ {len(leagues_created)} ligues créées avec leurs membres")

    # ================================================
    # 7. INVITATIONS DE LIGUES
    # ================================================
    invite_count = 0
    active_leagues = [l for l in leagues_created if not l.is_archived]
    for league in active_leagues:
        # Quelques invitations pendantes
        members_ids = set()
        league_members = db.query(models.LeagueMember).filter(
            models.LeagueMember.league_id == league.id
        ).all()
        for lm in league_members:
            members_ids.add(lm.user_id)

        non_members = [u for u in users if u.id not in members_ids]
        num_invites = random.randint(0, 4)
        invitees = random.sample(non_members, min(num_invites, len(non_members)))

        for invitee in invitees:
            inviter = random.choice([u for u in users if u.id in members_ids])
            invite = models.LeagueInvite(
                league_id=league.id,
                inviter_id=inviter.id,
                invitee_id=invitee.id,
                status="pending",
            )
            db.add(invite)
            invite_count += 1

    db.commit()
    print(f"   ✅ {invite_count} invitations de ligue créées")

    # ================================================
    # 8. TROPHÉES UTILISATEURS
    # ================================================
    # D'abord, récupérer les trophées existants
    trophies = db.query(models.Trophy).all()
    trophy_count = 0

    if trophies:
        for user in users:
            # Chaque utilisateur a une progression sur 2-5 trophées
            num_trophies = random.randint(2, min(5, len(trophies)))
            chosen_trophies = random.sample(trophies, num_trophies)

            for trophy in chosen_trophies:
                progress = random.randint(0, trophy.requirement_value)
                is_obtained = progress >= trophy.requirement_value

                obtained_at = None
                last_milestone_date = None

                if is_obtained:
                    obtained_at = datetime.now() - timedelta(days=random.randint(1, 30))
                    last_milestone_date = obtained_at

                milestones = trophy.milestones or []
                if milestones and progress > 0:
                    # Trouver le dernier milestone atteint
                    for ms in milestones:
                        if progress >= ms["value"]:
                            last_milestone_date = datetime.now() - timedelta(
                                days=random.randint(1, 45)
                            )

                ut = models.UserTrophy(
                    user_id=user.id,
                    trophy_id=trophy.id,
                    progress=progress,
                    is_obtained=is_obtained,
                    obtained_at=obtained_at,
                    last_milestone_date=last_milestone_date,
                )
                db.add(ut)
                trophy_count += 1

    db.commit()
    print(f"   ✅ {trophy_count} trophées utilisateurs créés")

    # ================================================
    # 9. CONNEXIONS (UserLogin) pour le réalisme
    # ================================================
    login_count = 0
    for user in users:
        num_logins = random.randint(1, 15)
        for _ in range(num_logins):
            login = models.UserLogin(
                user_id=user.id,
                login_at=datetime.now() - timedelta(
                    days=random.randint(0, 60),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                ),
            )
            db.add(login)
            login_count += 1

    db.commit()
    print(f"   ✅ {login_count} connexions enregistrées")

    # ================================================
    # 10. ACTIVITÉS (feed d'activité)
    # ================================================
    activity_count = 0
    for user in users:
        # Récupérer les amis de cet utilisateur
        friend_links = db.query(models.FriendLink).filter(
            (models.FriendLink.user_id == user.id) | (models.FriendLink.friend_id == user.id)
        ).all()
        friend_ids_for_user = []
        for fl in friend_links:
            friend_ids_for_user.append(fl.friend_id if fl.user_id == user.id else fl.user_id)

        if not friend_ids_for_user:
            continue

        # Créer quelques activités visibles par cet utilisateur
        num_activities = random.randint(1, 5)
        for _ in range(num_activities):
            sender_id = random.choice(friend_ids_for_user)
            activity_type = random.choice(["mission", "trophy"])

            if activity_type == "mission":
                mid = random.choice(ALL_MISSION_IDS)
                mission = db.query(models.Mission).filter(models.Mission.id == mid).first()
                if not mission:
                    continue
                activity = models.Activity(
                    user_id=user.id,
                    sender_id=sender_id,
                    activity_type="mission",
                    mission_id=mid,
                    mission_title=mission.title,
                    status="termine",
                    created_at=datetime.now() - timedelta(
                        days=random.randint(0, 30),
                        hours=random.randint(0, 23),
                    ),
                )
            else:
                if not trophies:
                    continue
                trophy = random.choice(trophies)
                activity = models.Activity(
                    user_id=user.id,
                    sender_id=sender_id,
                    activity_type="trophy",
                    trophy_id=trophy.id,
                    trophy_title=trophy.title,
                    trophy_icon=trophy.icon,
                    status="obtained",
                    created_at=datetime.now() - timedelta(
                        days=random.randint(0, 30),
                        hours=random.randint(0, 23),
                    ),
                )

            db.add(activity)
            activity_count += 1

    db.commit()
    print(f"   ✅ {activity_count} activités de feed créées")

    # ================================================
    # 11. RÉCOMPENSES QUESTIONNAIRE
    # ================================================
    reward_count = 0
    for user in users:
        # Certains utilisateurs ont complété des catégories de questionnaire
        if random.random() < 0.6:
            num_cats = random.randint(1, 4)
            chosen_cats = random.sample(CATEGORIES, num_cats)
            for cat in chosen_cats:
                reward = models.UserQuestionnaireReward(
                    user_id=user.id,
                    category_name=cat,
                )
                db.add(reward)
                reward_count += 1

    db.commit()
    print(f"   ✅ {reward_count} récompenses de questionnaire créées")

    # ================================================
    # RÉSUMÉ
    # ================================================
    print("\n" + "=" * 50)
    print("🎉 Peuplement terminé avec succès !")
    print("=" * 50)
    print(f"   👤 {len(users)} utilisateurs (mot de passe: 'C')")
    print(f"   🤝 {len(friend_pairs)} amitiés")
    print(f"   🎯 {mission_count} statuts de missions")
    print(f"   🏆 {len(leagues_created)} ligues")
    print(f"   🏅 {trophy_count} trophées utilisateurs")
    print(f"   📊 {login_count} connexions")
    print(f"   📰 {activity_count} activités de feed")
    print(f"\n   Exemples de pseudos pour se connecter:")

    sample_users = random.sample(users, min(5, len(users)))
    for u in sample_users:
        print(f"      - {u.username} (email: {u.email})")
    print(f"\n   Tous les mots de passe sont: C")

    db.close()


if __name__ == "__main__":
    seed()


