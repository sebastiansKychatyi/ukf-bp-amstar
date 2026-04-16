# AmStars – Platforma pre amatérsky futbal

Bakalárska práca — Univerzita Konštantína Filozofa v Nitre

Webová aplikácia pre správu amatérskych futbalových tímov. Hráči si môžu vytvoriť alebo pridať sa k tímu, vyzývať iné tímy na zápasy, sledovať štatistiky a zúčastňovať sa turnajov.

---

## Technológie

**Backend**
- Python 3.11, FastAPI
- PostgreSQL 15
- Redis 7 (rate limiting, blacklist tokenov)
- SQLAlchemy 2, Alembic (migrácie)

**Frontend**
- Nuxt.js 3 (Vue 3)
- Vuetify 3

**Infraštruktúra**
- Docker, Docker Compose

---

## Požiadavky

- [Docker](https://www.docker.com/) a Docker Compose
- Git

---

## Spustenie projektu (lokálne)

### 1. Klonuj repozitár

```bash
git clone <url-repozitara>
cd AmStars
```

### 2. Vytvor súbor s premennými prostredia

```bash
cp .env.local.example .env.local
```

Pre lokálny vývoj nie je potrebné nič meniť — predvolené hodnoty fungujú ihneď.

### 3. Spusti všetky služby

```bash
docker-compose -f docker-compose.local.yml up --build
```

Pri prvom spustení sa automaticky stiahnu Docker obrazy, nainštalujú závislosti a aplikácia sa spustí.

### 4. Otvor aplikáciu v prehliadači

| Služba | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger dokumentácia | http://localhost:8000/docs |
| ReDoc dokumentácia | http://localhost:8000/redoc |

---

## Štruktúra projektu

```
AmStars/
├── backend/                  # FastAPI aplikácia
│   ├── app/
│   │   ├── api/              # HTTP endpointy
│   │   ├── core/             # Konfigurácia, bezpečnosť, výnimky
│   │   ├── models/           # SQLAlchemy modely (databázové tabuľky)
│   │   ├── schemas/          # Pydantic schémy (validácia dát)
│   │   ├── services/         # Biznis logika
│   │   ├── crud/             # Databázové operácie
│   │   └── middleware/       # Rate limiting, bezpečnostné hlavičky
│   ├── alembic/              # Migrácie databázy
│   └── tests/                # Testy
├── frontend/                 # Nuxt.js aplikácia
│   └── src/
│       ├── views/            # Stránky
│       ├── components/       # Znovupoužiteľné komponenty
│       ├── stores/           # Pinia stores (stav aplikácie)
│       └── services/         # API volania
├── docker-compose.local.yml  # Lokálne prostredie
├── docker-compose.prod.yml   # Produkčné prostredie
└── .env.local.example        # Vzor premenných prostredia
```

---

## Hlavné funkcie

- **Registrácia a prihlásenie** — JWT autentifikácia s blacklistom tokenov
- **Správa tímov** — vytvorenie tímu, pozvánky hráčov, zmena kapitána
- **Systém výziev** — tímy si môžu navzájom posielať výzvy na zápas
- **ELO hodnotenie** — automatická aktualizácia ratingu po každom zápase
- **Matchmaking** — automatické hľadanie vhodného súpera podľa ratingu a polohy
- **Turnaje** — ligový (round-robin) a vyraďovací (single elimination) formát
- **Štatistiky hráčov** — góly, asistencie, žlté/červené karty
- **Notifikácie** — in-app upozornenia na výzvy, žiadosti o vstup, výsledky

---

## Databázové migrácie

Migrácie sa pri spustení aplikácie vykonajú automaticky. Ak ich chceš spustiť manuálne:

```bash
docker exec amstar_backend_local alembic upgrade head
```

---

## Testy

```bash
docker exec amstar_backend_local pytest
```

---

## Zastavenie aplikácie

```bash
docker-compose -f docker-compose.local.yml down
```

Ak chceš odstrániť aj dáta z databázy:

```bash
docker-compose -f docker-compose.local.yml down -v
```
