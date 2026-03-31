"""
AmStar Platform - Database Seed Script
=======================================
Creates sample users, teams, and statistics for testing.

Usage (run inside the backend container):
  docker exec -it amstar_backend python /seed.py

All test accounts use password: AmStar2026!
"""

import sys
import os

# Allow imports from the app package
sys.path.insert(0, "/app")
os.environ.setdefault("DATABASE_URL", os.getenv("DATABASE_URL", ""))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.security import get_password_hash
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")

engine = create_engine(DATABASE_URL, echo=False)

PASSWORD = "AmStar2026!"
HASH = get_password_hash(PASSWORD)
NOW = datetime.now(timezone.utc)


def seed(session: Session):
    # ------------------------------------------------------------------
    # 1. Users
    # ------------------------------------------------------------------
    users_data = [
        # Captains
        {"email": "jan.novak@amstar.test",     "username": "jan_novak",     "full_name": "Jan Novák",       "role": "CAPTAIN"},
        {"email": "petr.svoboda@amstar.test",  "username": "petr_svoboda",  "full_name": "Petr Svoboda",    "role": "CAPTAIN"},
        {"email": "tomas.dvorak@amstar.test",  "username": "tomas_dvorak",  "full_name": "Tomáš Dvořák",    "role": "CAPTAIN"},
        # Players - Thunder FC
        {"email": "lukas.cerny@amstar.test",   "username": "lukas_cerny",   "full_name": "Lukáš Černý",     "role": "PLAYER"},
        {"email": "martin.prochazka@amstar.test","username": "martin_prochazka","full_name": "Martin Procházka","role": "PLAYER"},
        # Players - Lightning United
        {"email": "david.kucera@amstar.test",  "username": "david_kucera",  "full_name": "David Kučera",    "role": "PLAYER"},
        {"email": "jakub.vesely@amstar.test",  "username": "jakub_vesely",  "full_name": "Jakub Veselý",    "role": "PLAYER"},
        # Players - Storm Athletic
        {"email": "michal.horak@amstar.test",  "username": "michal_horak",  "full_name": "Michal Horák",    "role": "PLAYER"},
        # Admin
        {"email": "admin@amstar.test",         "username": "admin",         "full_name": "AmStar Admin",    "role": "PLAYER", "is_superuser": True},
    ]

    user_ids = {}
    for u in users_data:
        result = session.execute(text(
            "INSERT INTO \"user\" (email, username, hashed_password, full_name, role, is_active, is_superuser, created_at, updated_at) "
            "VALUES (:email, :username, :pw, :full_name, :role, true, :su, :now, :now) "
            "ON CONFLICT (email) DO UPDATE SET email=EXCLUDED.email "
            "RETURNING id"
        ), {
            "email": u["email"],
            "username": u["username"],
            "pw": HASH,
            "full_name": u["full_name"],
            "role": u["role"],
            "su": u.get("is_superuser", False),
            "now": NOW,
        })
        user_ids[u["username"]] = result.scalar()

    session.flush()

    # ------------------------------------------------------------------
    # 2. Teams
    # ------------------------------------------------------------------
    teams_data = [
        {
            "name": "Thunder FC",
            "description": "Competitive amateur team based in Prague. Training twice a week.",
            "captain_key": "jan_novak",
            "city": "Prague",
            "rating": 1150,
            "founded": datetime(2020, 6, 15, tzinfo=timezone.utc),
        },
        {
            "name": "Lightning United",
            "description": "Friendly team looking for new members. All skill levels welcome.",
            "captain_key": "petr_svoboda",
            "city": "Brno",
            "rating": 1020,
            "founded": datetime(2019, 3, 20, tzinfo=timezone.utc),
        },
        {
            "name": "Storm Athletic",
            "description": "Young and energetic squad from Ostrava.",
            "captain_key": "tomas_dvorak",
            "city": "Ostrava",
            "rating": 1080,
            "founded": datetime(2021, 1, 10, tzinfo=timezone.utc),
        },
    ]

    team_ids = {}
    for t in teams_data:
        result = session.execute(text(
            "INSERT INTO team (name, description, captain_id, city, rating, founded_date, created_at, updated_at) "
            "VALUES (:name, :desc, :cap, :city, :rating, :founded, :now, :now) "
            "ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name "
            "RETURNING id"
        ), {
            "name": t["name"],
            "desc": t["description"],
            "cap": user_ids[t["captain_key"]],
            "city": t["city"],
            "rating": t["rating"],
            "founded": t["founded"],
            "now": NOW,
        })
        team_ids[t["name"]] = result.scalar()

    session.flush()

    # ------------------------------------------------------------------
    # 3. Team Members
    # ------------------------------------------------------------------
    members_data = [
        # Thunder FC
        {"team": "Thunder FC",     "user": "jan_novak",          "role": "CAPTAIN", "position": "FWD", "jersey": 10},
        {"team": "Thunder FC",     "user": "lukas_cerny",        "role": "PLAYER",  "position": "GK",  "jersey": 1},
        {"team": "Thunder FC",     "user": "martin_prochazka",   "role": "PLAYER",  "position": "FWD", "jersey": 9},
        # Lightning United
        {"team": "Lightning United", "user": "petr_svoboda",     "role": "CAPTAIN", "position": "MID", "jersey": 8},
        {"team": "Lightning United", "user": "david_kucera",     "role": "PLAYER",  "position": "MID", "jersey": 6},
        # Storm Athletic
        {"team": "Storm Athletic", "user": "tomas_dvorak",       "role": "CAPTAIN", "position": "DEF", "jersey": 4},
        {"team": "Storm Athletic", "user": "jakub_vesely",       "role": "PLAYER",  "position": "DEF", "jersey": 5},
        {"team": "Storm Athletic", "user": "michal_horak",       "role": "PLAYER",  "position": "FWD", "jersey": 11},
    ]

    for m in members_data:
        session.execute(text(
            "INSERT INTO teammember (team_id, user_id, role, position, jersey_number, joined_at, created_at, updated_at) "
            "VALUES (:tid, :uid, :role, :pos, :jersey, :now, :now, :now) "
            "ON CONFLICT ON CONSTRAINT uq_teammember_user DO NOTHING"
        ), {
            "tid": team_ids[m["team"]],
            "uid": user_ids[m["user"]],
            "role": m["role"],
            "pos": m["position"],
            "jersey": m["jersey"],
            "now": NOW,
        })

    session.flush()

    # ------------------------------------------------------------------
    # 4. Player Statistics
    # ------------------------------------------------------------------
    stats_data = [
        {"user": "jan_novak",        "mp": 25, "mw": 18, "md": 4, "ml": 3, "g": 28, "a": 12, "yc": 3, "rc": 0, "cs": 0},
        {"user": "lukas_cerny",      "mp": 25, "mw": 18, "md": 4, "ml": 3, "g": 0,  "a": 0,  "yc": 1, "rc": 0, "cs": 12},
        {"user": "martin_prochazka", "mp": 22, "mw": 16, "md": 3, "ml": 3, "g": 18, "a": 6,  "yc": 2, "rc": 0, "cs": 0},
        {"user": "petr_svoboda",     "mp": 30, "mw": 15, "md": 8, "ml": 7, "g": 8,  "a": 18, "yc": 5, "rc": 0, "cs": 0},
        {"user": "david_kucera",     "mp": 28, "mw": 13, "md": 7, "ml": 8, "g": 12, "a": 15, "yc": 7, "rc": 0, "cs": 0},
        {"user": "tomas_dvorak",     "mp": 20, "mw": 12, "md": 5, "ml": 3, "g": 3,  "a": 2,  "yc": 5, "rc": 0, "cs": 7},
        {"user": "jakub_vesely",     "mp": 20, "mw": 12, "md": 5, "ml": 3, "g": 2,  "a": 3,  "yc": 4, "rc": 0, "cs": 5},
        {"user": "michal_horak",     "mp": 20, "mw": 12, "md": 5, "ml": 3, "g": 18, "a": 6,  "yc": 2, "rc": 0, "cs": 0},
    ]

    for s in stats_data:
        session.execute(text(
            "INSERT INTO playerstatistics "
            "(user_id, matches_played, matches_won, matches_drawn, matches_lost, goals, assists, yellow_cards, red_cards, clean_sheets, created_at, updated_at) "
            "VALUES (:uid, :mp, :mw, :md, :ml, :g, :a, :yc, :rc, :cs, :now, :now) "
            "ON CONFLICT (user_id) DO UPDATE SET "
            "matches_played=EXCLUDED.matches_played, goals=EXCLUDED.goals, assists=EXCLUDED.assists"
        ), {
            "uid": user_ids[s["user"]],
            "mp": s["mp"], "mw": s["mw"], "md": s["md"], "ml": s["ml"],
            "g": s["g"], "a": s["a"], "yc": s["yc"], "rc": s["rc"], "cs": s["cs"],
            "now": NOW,
        })

    session.flush()

    # ------------------------------------------------------------------
    # 5. Join Requests
    # ------------------------------------------------------------------
    session.execute(text(
        "INSERT INTO joinrequest (team_id, user_id, status, message, created_at, updated_at) "
        "VALUES (:tid, :uid, 'PENDING', :msg, :now, :now) "
        "ON CONFLICT DO NOTHING"
    ), {
        "tid": team_ids["Thunder FC"],
        "uid": user_ids["david_kucera"],
        "msg": "I would love to join Thunder FC! I am an experienced midfielder.",
        "now": NOW,
    })

    session.commit()
    print("Seed complete.")
    print(f"\nTest accounts (password: {PASSWORD}):")
    print("  admin@amstar.test         — superuser")
    print("  jan.novak@amstar.test     — captain, Thunder FC")
    print("  petr.svoboda@amstar.test  — captain, Lightning United")
    print("  tomas.dvorak@amstar.test  — captain, Storm Athletic")
    print("  lukas.cerny@amstar.test   — player, Thunder FC (GK)")
    print("  martin.prochazka@amstar.test — player, Thunder FC (FWD)")
    print("  david.kucera@amstar.test  — player, Lightning United")
    print("  michal.horak@amstar.test  — player, Storm Athletic")
    print(f"\nTeam IDs: {team_ids}")


if __name__ == "__main__":
    with Session(engine) as session:
        seed(session)
