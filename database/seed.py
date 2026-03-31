"""
AmStar Platform - Database Seed Script
=======================================
Creates sample users, teams, match history, and statistics.

Usage (run inside the backend container):
  docker cp database/seed.py amstar_backend:/seed.py
  docker exec amstar_backend python /seed.py

All test accounts use password: AmStar2026!
"""

import sys
import os

sys.path.insert(0, "/app")
os.environ.setdefault("DATABASE_URL", os.getenv("DATABASE_URL", ""))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.core.security import get_password_hash
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")

engine = create_engine(DATABASE_URL, echo=False)

PASSWORD = "AmStar2026!"
HASH = get_password_hash(PASSWORD)
NOW = datetime.now(timezone.utc)


def seed(session: Session):
    # ------------------------------------------------------------------
    # 1. Users  (15 total: 3 captains + 11 players + 1 admin)
    # ------------------------------------------------------------------
    users_data = [
        # Captains
        {"email": "jan.novak@amstar.test",        "username": "jan_novak",        "full_name": "Jan Novák",          "role": "CAPTAIN"},
        {"email": "petr.svoboda@amstar.test",      "username": "petr_svoboda",     "full_name": "Petr Svoboda",       "role": "CAPTAIN"},
        {"email": "tomas.dvorak@amstar.test",      "username": "tomas_dvorak",     "full_name": "Tomáš Dvořák",       "role": "CAPTAIN"},
        # Thunder FC players
        {"email": "lukas.cerny@amstar.test",       "username": "lukas_cerny",      "full_name": "Lukáš Černý",        "role": "PLAYER"},
        {"email": "martin.prochazka@amstar.test",  "username": "martin_prochazka", "full_name": "Martin Procházka",   "role": "PLAYER"},
        {"email": "ondrej.blazek@amstar.test",     "username": "ondrej_blazek",    "full_name": "Ondřej Blažek",      "role": "PLAYER"},
        {"email": "filip.ruzicka@amstar.test",     "username": "filip_ruzicka",    "full_name": "Filip Růžička",      "role": "PLAYER"},
        # Lightning United players
        {"email": "david.kucera@amstar.test",      "username": "david_kucera",     "full_name": "David Kučera",       "role": "PLAYER"},
        {"email": "jakub.vesely@amstar.test",      "username": "jakub_vesely",     "full_name": "Jakub Veselý",       "role": "PLAYER"},
        {"email": "radek.mares@amstar.test",       "username": "radek_mares",      "full_name": "Radek Mareš",        "role": "PLAYER"},
        # Storm Athletic players
        {"email": "michal.horak@amstar.test",      "username": "michal_horak",     "full_name": "Michal Horák",       "role": "PLAYER"},
        {"email": "vojtech.kovar@amstar.test",     "username": "vojtech_kovar",    "full_name": "Vojtěch Kovář",      "role": "PLAYER"},
        {"email": "simon.blazek@amstar.test",      "username": "simon_blazek",     "full_name": "Šimon Blažek",       "role": "PLAYER"},
        {"email": "adam.pospisil@amstar.test",     "username": "adam_pospisil",    "full_name": "Adam Pospíšil",      "role": "PLAYER"},
        # Admin
        {"email": "admin@amstar.test",             "username": "admin",            "full_name": "AmStar Admin",       "role": "PLAYER", "is_superuser": True},
    ]

    user_ids = {}
    for u in users_data:
        result = session.execute(text(
            'INSERT INTO "user" (email, username, hashed_password, full_name, role, is_active, is_superuser, created_at, updated_at) '
            "VALUES (:email, :username, :pw, :full_name, :role, true, :su, :now, :now) "
            "ON CONFLICT (email) DO UPDATE SET email=EXCLUDED.email "
            "RETURNING id"
        ), {
            "email": u["email"], "username": u["username"], "pw": HASH,
            "full_name": u["full_name"], "role": u["role"],
            "su": u.get("is_superuser", False), "now": NOW,
        })
        user_ids[u["username"]] = result.scalar()

    session.flush()

    # ------------------------------------------------------------------
    # 2. Teams
    # ------------------------------------------------------------------
    teams_data = [
        {
            "name": "Thunder FC",
            "description": "Competitive amateur team based in Prague. We train every Tuesday and Thursday at Letná sports complex. Looking for dedicated players.",
            "captain_key": "jan_novak",
            "city": "Prague",
            "rating": 1180,
            "founded": datetime(2020, 6, 15, tzinfo=timezone.utc),
        },
        {
            "name": "Lightning United",
            "description": "Friendly team from Brno open to all skill levels. We play for fun but take matches seriously. Training on Mondays and Fridays.",
            "captain_key": "petr_svoboda",
            "city": "Brno",
            "rating": 1050,
            "founded": datetime(2019, 3, 20, tzinfo=timezone.utc),
        },
        {
            "name": "Storm Athletic",
            "description": "Young and energetic squad from Ostrava. Rising fast — won 3 of our last 4 matches. Strong defence, fast attack.",
            "captain_key": "tomas_dvorak",
            "city": "Ostrava",
            "rating": 1095,
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
            "name": t["name"], "desc": t["description"],
            "cap": user_ids[t["captain_key"]], "city": t["city"],
            "rating": t["rating"], "founded": t["founded"], "now": NOW,
        })
        team_ids[t["name"]] = result.scalar()

    session.flush()

    # ------------------------------------------------------------------
    # 3. Team Members
    # ------------------------------------------------------------------
    members_data = [
        # Thunder FC
        {"team": "Thunder FC",      "user": "jan_novak",        "role": "CAPTAIN", "position": "FWD", "jersey": 10},
        {"team": "Thunder FC",      "user": "lukas_cerny",      "role": "PLAYER",  "position": "GK",  "jersey": 1},
        {"team": "Thunder FC",      "user": "martin_prochazka", "role": "PLAYER",  "position": "FWD", "jersey": 9},
        {"team": "Thunder FC",      "user": "ondrej_blazek",    "role": "PLAYER",  "position": "DEF", "jersey": 5},
        {"team": "Thunder FC",      "user": "filip_ruzicka",    "role": "PLAYER",  "position": "MID", "jersey": 7},
        # Lightning United
        {"team": "Lightning United","user": "petr_svoboda",     "role": "CAPTAIN", "position": "MID", "jersey": 8},
        {"team": "Lightning United","user": "david_kucera",     "role": "PLAYER",  "position": "MID", "jersey": 6},
        {"team": "Lightning United","user": "jakub_vesely",     "role": "PLAYER",  "position": "DEF", "jersey": 4},
        {"team": "Lightning United","user": "radek_mares",      "role": "PLAYER",  "position": "FWD", "jersey": 11},
        # Storm Athletic
        {"team": "Storm Athletic",  "user": "tomas_dvorak",     "role": "CAPTAIN", "position": "DEF", "jersey": 4},
        {"team": "Storm Athletic",  "user": "michal_horak",     "role": "PLAYER",  "position": "FWD", "jersey": 11},
        {"team": "Storm Athletic",  "user": "vojtech_kovar",    "role": "PLAYER",  "position": "GK",  "jersey": 1},
        {"team": "Storm Athletic",  "user": "simon_blazek",     "role": "PLAYER",  "position": "MID", "jersey": 8},
        {"team": "Storm Athletic",  "user": "adam_pospisil",    "role": "PLAYER",  "position": "DEF", "jersey": 3},
    ]

    for m in members_data:
        joined = NOW - timedelta(days=60)
        session.execute(text(
            "INSERT INTO teammember (team_id, user_id, role, position, jersey_number, joined_at, created_at, updated_at) "
            "VALUES (:tid, :uid, :role, :pos, :jersey, :joined, :now, :now) "
            "ON CONFLICT ON CONSTRAINT uq_teammember_user DO NOTHING"
        ), {
            "tid": team_ids[m["team"]], "uid": user_ids[m["user"]],
            "role": m["role"], "pos": m["position"], "jersey": m["jersey"],
            "joined": joined, "now": NOW,
        })

    session.flush()

    # ------------------------------------------------------------------
    # 4. Completed matches (challenges)
    # Format: challenger vs opponent, challenger_score:opponent_score, days_ago
    # ------------------------------------------------------------------
    matches = [
        # Thunder FC vs Lightning United  — 5 matches
        ("Thunder FC",      "Lightning United", 3, 1, 75, "Letná Sports Complex, Prague"),
        ("Lightning United","Thunder FC",        0, 2, 60, "Drásov Sports Ground, Brno"),
        ("Thunder FC",      "Lightning United",  2, 2, 45, "Letná Sports Complex, Prague"),
        ("Thunder FC",      "Lightning United",  4, 0, 20, "Letná Sports Complex, Prague"),
        ("Lightning United","Thunder FC",         1, 3, 7,  "Drásov Sports Ground, Brno"),
        # Thunder FC vs Storm Athletic  — 4 matches
        ("Thunder FC",      "Storm Athletic",    2, 1, 68, "Letná Sports Complex, Prague"),
        ("Storm Athletic",  "Thunder FC",         3, 1, 50, "Bazaly Stadium, Ostrava"),
        ("Thunder FC",      "Storm Athletic",    2, 0, 30, "Letná Sports Complex, Prague"),
        ("Storm Athletic",  "Thunder FC",         1, 1, 10, "Bazaly Stadium, Ostrava"),
        # Lightning United vs Storm Athletic — 3 matches
        ("Lightning United","Storm Athletic",    1, 2, 55, "Drásov Sports Ground, Brno"),
        ("Storm Athletic",  "Lightning United",  2, 0, 35, "Bazaly Stadium, Ostrava"),
        ("Lightning United","Storm Athletic",    2, 1, 14, "Drásov Sports Ground, Brno"),
    ]

    challenge_ids = []
    for ch_name, op_name, ch_score, op_score, days_ago, location in matches:
        match_date = NOW - timedelta(days=days_ago)
        result = session.execute(text(
            "INSERT INTO challenge "
            "(challenger_id, opponent_id, status, match_date, location, challenger_score, opponent_score, "
            " result_confirmed_by_challenger, result_confirmed_by_opponent, created_at, updated_at) "
            "VALUES (:ch, :op, 'completed', :mdate, :loc, :cscore, :oscore, true, true, :now, :now) "
            "RETURNING id"
        ), {
            "ch": team_ids[ch_name], "op": team_ids[op_name],
            "cscore": ch_score, "oscore": op_score,
            "mdate": match_date, "loc": location, "now": match_date,
        })
        challenge_ids.append(result.scalar())

    # One pending challenge (upcoming match)
    session.execute(text(
        "INSERT INTO challenge "
        "(challenger_id, opponent_id, status, match_date, location, "
        " result_confirmed_by_challenger, result_confirmed_by_opponent, created_at, updated_at) "
        "VALUES (:ch, :op, 'pending', :mdate, :loc, false, false, :now, :now)"
    ), {
        "ch": team_ids["Thunder FC"], "op": team_ids["Storm Athletic"],
        "mdate": NOW + timedelta(days=7),
        "loc": "Letná Sports Complex, Prague", "now": NOW,
    })

    session.flush()

    # ------------------------------------------------------------------
    # 5. Player Statistics (aggregated from match history)
    # ------------------------------------------------------------------
    stats_data = [
        # Thunder FC — strong attack
        {"user": "jan_novak",        "mp": 11, "mw": 8, "md": 2, "ml": 1, "g": 18, "a": 7,  "yc": 2, "rc": 0, "cs": 0,  "sot": 32},
        {"user": "lukas_cerny",      "mp": 11, "mw": 8, "md": 2, "ml": 1, "g": 0,  "a": 0,  "yc": 1, "rc": 0, "cs": 5,  "sot": 0,  "sv": 28},
        {"user": "martin_prochazka","mp": 10, "mw": 7, "md": 2, "ml": 1, "g": 12, "a": 5,  "yc": 3, "rc": 0, "cs": 0,  "sot": 22},
        {"user": "ondrej_blazek",   "mp": 9,  "mw": 7, "md": 1, "ml": 1, "g": 1,  "a": 3,  "yc": 4, "rc": 0, "cs": 3,  "sot": 4},
        {"user": "filip_ruzicka",   "mp": 10, "mw": 7, "md": 2, "ml": 1, "g": 4,  "a": 9,  "yc": 2, "rc": 0, "cs": 0,  "sot": 10},
        # Lightning United — balanced midfield
        {"user": "petr_svoboda",    "mp": 11, "mw": 3, "md": 3, "ml": 5, "g": 5,  "a": 11, "yc": 4, "rc": 0, "cs": 0,  "sot": 12},
        {"user": "david_kucera",    "mp": 11, "mw": 3, "md": 3, "ml": 5, "g": 7,  "a": 8,  "yc": 5, "rc": 0, "cs": 0,  "sot": 16},
        {"user": "jakub_vesely",    "mp": 10, "mw": 3, "md": 2, "ml": 5, "g": 2,  "a": 2,  "yc": 3, "rc": 1, "cs": 2,  "sot": 5},
        {"user": "radek_mares",     "mp": 9,  "mw": 2, "md": 3, "ml": 4, "g": 8,  "a": 3,  "yc": 1, "rc": 0, "cs": 0,  "sot": 15},
        # Storm Athletic — solid defence
        {"user": "tomas_dvorak",    "mp": 12, "mw": 6, "md": 2, "ml": 4, "g": 2,  "a": 4,  "yc": 5, "rc": 0, "cs": 4,  "sot": 6},
        {"user": "michal_horak",    "mp": 12, "mw": 6, "md": 2, "ml": 4, "g": 13, "a": 5,  "yc": 2, "rc": 0, "cs": 0,  "sot": 24},
        {"user": "vojtech_kovar",   "mp": 12, "mw": 6, "md": 2, "ml": 4, "g": 0,  "a": 0,  "yc": 0, "rc": 0, "cs": 6,  "sot": 0,  "sv": 31},
        {"user": "simon_blazek",    "mp": 11, "mw": 5, "md": 2, "ml": 4, "g": 3,  "a": 6,  "yc": 3, "rc": 0, "cs": 0,  "sot": 8},
        {"user": "adam_pospisil",   "mp": 10, "mw": 5, "md": 2, "ml": 3, "g": 1,  "a": 2,  "yc": 4, "rc": 0, "cs": 3,  "sot": 3},
    ]

    for s in stats_data:
        session.execute(text(
            "INSERT INTO playerstatistics "
            "(user_id, matches_played, matches_won, matches_drawn, matches_lost, "
            " goals, assists, shots_on_target, yellow_cards, red_cards, clean_sheets, saves, created_at, updated_at) "
            "VALUES (:uid, :mp, :mw, :md, :ml, :g, :a, :sot, :yc, :rc, :cs, :sv, :now, :now) "
            "ON CONFLICT (user_id) DO UPDATE SET "
            " matches_played=EXCLUDED.matches_played, goals=EXCLUDED.goals, "
            " assists=EXCLUDED.assists, yellow_cards=EXCLUDED.yellow_cards"
        ), {
            "uid": user_ids[s["user"]],
            "mp": s["mp"], "mw": s["mw"], "md": s["md"], "ml": s["ml"],
            "g": s["g"], "a": s["a"], "sot": s.get("sot", 0),
            "yc": s["yc"], "rc": s["rc"], "cs": s["cs"],
            "sv": s.get("sv", 0), "now": NOW,
        })

    session.flush()

    # ------------------------------------------------------------------
    # 6. Join Requests
    # ------------------------------------------------------------------
    # Pending — player wants to join Thunder FC
    session.execute(text(
        "INSERT INTO joinrequest (team_id, user_id, status, message, position, created_at, updated_at) "
        "VALUES (:tid, :uid, 'PENDING', :msg, 'MID', :now, :now) ON CONFLICT DO NOTHING"
    ), {
        "tid": team_ids["Thunder FC"], "uid": user_ids["admin"],
        "msg": "Looking for a competitive team in Prague. I play central midfield and can train twice a week.",
        "now": NOW - timedelta(days=3),
    })

    # Approved — one that was already accepted
    session.execute(text(
        "INSERT INTO joinrequest (team_id, user_id, status, message, position, "
        " reviewed_by_id, review_message, reviewed_at, created_at, updated_at) "
        "VALUES (:tid, :uid, 'ACCEPTED', :msg, 'FWD', :rev, :rmsg, :rat, :now, :now) ON CONFLICT DO NOTHING"
    ), {
        "tid": team_ids["Storm Athletic"], "uid": user_ids["michal_horak"],
        "msg": "Fast forward, good at finishing.", "rev": user_ids["tomas_dvorak"],
        "rmsg": "Welcome to the squad! First training Thursday 18:00.",
        "rat": NOW - timedelta(days=55), "now": NOW - timedelta(days=58),
    })

    session.commit()

    print("=" * 55)
    print("Seed complete!")
    print("=" * 55)
    print(f"\nPassword for ALL accounts: {PASSWORD}\n")
    print("Accounts:")
    print("  admin@amstar.test              — superuser")
    print("  jan.novak@amstar.test          — captain, Thunder FC")
    print("  petr.svoboda@amstar.test       — captain, Lightning United")
    print("  tomas.dvorak@amstar.test       — captain, Storm Athletic")
    print("  lukas.cerny@amstar.test        — GK, Thunder FC")
    print("  martin.prochazka@amstar.test   — FWD, Thunder FC")
    print("  david.kucera@amstar.test       — MID, Lightning United")
    print("  michal.horak@amstar.test       — FWD, Storm Athletic")
    print(f"\nTeams created: {list(team_ids.keys())}")
    print(f"Matches created: {len(matches)} completed + 1 pending")


if __name__ == "__main__":
    with Session(engine) as session:
        seed(session)
