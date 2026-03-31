"""
Seed AlloyDB AI with shelters, hospitals, and emergency contacts.
Embeddings are generated via Vertex AI text-embedding model.
Run: python db/seed_data.py
"""

import asyncio
import asyncpg
import vertexai
from vertexai.language_models import TextEmbeddingModel
import warnings
warnings.filterwarnings("ignore")
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import ALLOYDB_DSN, GOOGLE_CLOUD_PROJECT, VERTEX_AI_LOCATION

# ─── Seed data ───────────────────────────────────────────────────────────────

SHELTERS = [
    {"name": "Chennai Central Shelter", "region": "Chennai", "country": "India",
     "latitude": 13.0827, "longitude": 80.2707, "capacity": 500,
     "current_occupancy": 120, "has_medical": True, "has_food": True,
     "has_water": True, "disaster_types": ["earthquake", "flood", "cyclone"],
     "contact_phone": "+91-44-25300000"},
    {"name": "Jakarta Emergency Camp Alpha", "region": "Jakarta", "country": "Indonesia",
     "latitude": -6.2088, "longitude": 106.8456, "capacity": 800,
     "current_occupancy": 200, "has_medical": True, "has_food": True,
     "has_water": True, "disaster_types": ["flood", "earthquake"],
     "contact_phone": "+62-21-5000000"},
    {"name": "Manila Typhoon Relief Center", "region": "Manila", "country": "Philippines",
     "latitude": 14.5995, "longitude": 120.9842, "capacity": 600,
     "current_occupancy": 50, "has_medical": False, "has_food": True,
     "has_water": True, "disaster_types": ["typhoon", "flood"],
     "contact_phone": "+63-2-55000000"},
    {"name": "Bangkok Flood Shelter North", "region": "Bangkok", "country": "Thailand",
     "latitude": 13.7563, "longitude": 100.5018, "capacity": 400,
     "current_occupancy": 80, "has_medical": True, "has_food": True,
     "has_water": False, "disaster_types": ["flood"],
     "contact_phone": "+66-2-5000000"},
    {"name": "Mumbai Disaster Relief Hub", "region": "Mumbai", "country": "India",
     "latitude": 19.0760, "longitude": 72.8777, "capacity": 1000,
     "current_occupancy": 300, "has_medical": True, "has_food": True,
     "has_water": True, "disaster_types": ["flood", "earthquake", "cyclone"],
     "contact_phone": "+91-22-22700000"},
]

HOSPITALS = [
    {"name": "Rajiv Gandhi Government General Hospital", "region": "Chennai",
     "country": "India", "latitude": 13.0801, "longitude": 80.2765,
     "emergency_beds": 200, "contact_phone": "+91-44-25305000",
     "contact_email": "emergency@rgggh.gov.in"},
    {"name": "RSUD Cipto Mangunkusumo", "region": "Jakarta",
     "country": "Indonesia", "latitude": -6.1944, "longitude": 106.8462,
     "emergency_beds": 150, "contact_phone": "+62-21-3145000",
     "contact_email": "emergency@rscm.co.id"},
    {"name": "Philippine General Hospital", "region": "Manila",
     "country": "Philippines", "latitude": 14.5795, "longitude": 120.9822,
     "emergency_beds": 300, "contact_phone": "+63-2-55548400",
     "contact_email": "emergency@pgh.gov.ph"},
    {"name": "KEM Hospital Mumbai", "region": "Mumbai",
     "country": "India", "latitude": 19.0027, "longitude": 72.8422,
     "emergency_beds": 250, "contact_phone": "+91-22-24136051",
     "contact_email": "emergency@kem.gov.in"},
]

EMERGENCY_CONTACTS = [
    # India
    {"agency": "NDRF (National Disaster Response Force)", "region": "India",
     "country": "India", "disaster_types": ["earthquake", "flood", "cyclone", "landslide"],
     "phone": "011-24363260", "email": "ndrf@nic.in",
     "description": "Primary national disaster response agency for India"},
    {"agency": "Tamil Nadu DEOC", "region": "Chennai",
     "country": "India", "disaster_types": ["earthquake", "flood", "cyclone"],
     "phone": "1070", "email": "deoc@tn.gov.in",
     "description": "Tamil Nadu District Emergency Operations Centre"},
    {"agency": "India Ambulance", "region": "India",
     "country": "India", "disaster_types": ["earthquake", "flood", "cyclone", "fire"],
     "phone": "108", "email": None,
     "description": "National ambulance service"},
    {"agency": "India Fire Department", "region": "India",
     "country": "India", "disaster_types": ["fire", "earthquake"],
     "phone": "101", "email": None,
     "description": "National fire emergency service"},
    {"agency": "India Police", "region": "India",
     "country": "India", "disaster_types": ["earthquake", "flood", "cyclone"],
     "phone": "100", "email": None,
     "description": "National police emergency line"},
    # Indonesia
    {"agency": "BNPB (Badan Nasional Penanggulangan Bencana)", "region": "Jakarta",
     "country": "Indonesia", "disaster_types": ["earthquake", "flood", "volcano", "tsunami"],
     "phone": "117", "email": "pusdalops@bnpb.go.id",
     "description": "Indonesian National Board for Disaster Management"},
    {"agency": "Indonesia Ambulance (BSMD)", "region": "Jakarta",
     "country": "Indonesia", "disaster_types": ["earthquake", "flood"],
     "phone": "119", "email": None,
     "description": "Indonesian emergency medical service"},
    # Philippines
    {"agency": "NDRRMC Philippines", "region": "Manila",
     "country": "Philippines", "disaster_types": ["typhoon", "earthquake", "flood", "tsunami"],
     "phone": "+63-2-911-5061", "email": "opcen@ndrrmc.gov.ph",
     "description": "National Disaster Risk Reduction Management Council"},
    {"agency": "Philippines Red Cross", "region": "Manila",
     "country": "Philippines", "disaster_types": ["typhoon", "flood", "earthquake"],
     "phone": "143", "email": "prc@redcross.org.ph",
     "description": "Philippine Red Cross emergency hotline"},
    # Thailand
    {"agency": "DDPM Thailand", "region": "Bangkok",
     "country": "Thailand", "disaster_types": ["flood", "earthquake"],
     "phone": "1784", "email": "ddpm@disaster.go.th",
     "description": "Department of Disaster Prevention and Mitigation"},
    # Global
    {"agency": "UNHCR Emergency", "region": "Global",
     "country": "Global", "disaster_types": ["earthquake", "flood", "cyclone", "typhoon"],
     "phone": "+41-22-739-8111", "email": "hqemergency@unhcr.org",
     "description": "UN Refugee Agency global emergency line"},
    {"agency": "ICRC Emergency", "region": "Global",
     "country": "Global", "disaster_types": ["earthquake", "flood", "cyclone"],
     "phone": "+41-22-734-6001", "email": "icrc.gva@icrc.org",
     "description": "International Committee of the Red Cross"},
]


def get_embeddings_batch(model: TextEmbeddingModel, texts: list[str]) -> list[list[float]]:
    """Get embeddings for all texts in one API call (max 250 per batch)."""
    embeddings = model.get_embeddings(texts)
    return [e.values for e in embeddings]


async def seed():
    vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=VERTEX_AI_LOCATION)
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    conn = await asyncpg.connect(ALLOYDB_DSN)
    print("Connected to AlloyDB AI.")

    # Seed shelters — batch all 5 in one API call
    print("Seeding shelters...")
    shelter_texts = [
        f"{s['name']} shelter in {s['region']}, {s['country']} for {', '.join(s['disaster_types'])}"
        for s in SHELTERS
    ]
    shelter_embeddings = get_embeddings_batch(embedding_model, shelter_texts)
    for s, embedding in zip(SHELTERS, shelter_embeddings):
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
        await conn.execute(f"""
            INSERT INTO shelters
              (name, region, country, latitude, longitude, capacity,
               current_occupancy, has_medical, has_food, has_water,
               disaster_types, contact_phone, embedding)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,'{embedding_str}'::vector)
            ON CONFLICT DO NOTHING
        """, s["name"], s["region"], s["country"], s["latitude"], s["longitude"],
            s["capacity"], s["current_occupancy"], s["has_medical"],
            s["has_food"], s["has_water"], s["disaster_types"],
            s["contact_phone"])
    print(f"  {len(SHELTERS)} shelters seeded.")

    await asyncio.sleep(5)  # brief pause between batches

    # Seed hospitals — batch all 4 in one API call
    print("Seeding hospitals...")
    hospital_texts = [
        f"{h['name']} hospital in {h['region']}, {h['country']} emergency care"
        for h in HOSPITALS
    ]
    hospital_embeddings = get_embeddings_batch(embedding_model, hospital_texts)
    for h, embedding in zip(HOSPITALS, hospital_embeddings):
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
        await conn.execute(f"""
            INSERT INTO hospitals
              (name, region, country, latitude, longitude,
               emergency_beds, contact_phone, contact_email, embedding)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'{embedding_str}'::vector)
            ON CONFLICT DO NOTHING
        """, h["name"], h["region"], h["country"], h["latitude"], h["longitude"],
            h["emergency_beds"], h["contact_phone"], h["contact_email"])
    print(f"  {len(HOSPITALS)} hospitals seeded.")

    await asyncio.sleep(5)  # brief pause between batches

    # Seed emergency contacts — batch all 12 in one API call
    print("Seeding emergency contacts...")
    contact_texts = [
        f"{c['agency']} in {c['region']} for {', '.join(c['disaster_types'])}: {c['description']}"
        for c in EMERGENCY_CONTACTS
    ]
    contact_embeddings = get_embeddings_batch(embedding_model, contact_texts)
    for c, embedding in zip(EMERGENCY_CONTACTS, contact_embeddings):
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
        await conn.execute(f"""
            INSERT INTO emergency_contacts
              (agency, region, country, disaster_types,
               phone, email, description, embedding)
            VALUES ($1,$2,$3,$4,$5,$6,$7,'{embedding_str}'::vector)
            ON CONFLICT DO NOTHING
        """, c["agency"], c["region"], c["country"], c["disaster_types"],
            c["phone"], c["email"], c["description"])
    print(f"  {len(EMERGENCY_CONTACTS)} contacts seeded.")

    await conn.close()
    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
