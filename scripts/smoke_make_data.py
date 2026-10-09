import json
import random

random.seed(3407)
SYSTEM = "You are a helpful assistant."
SYLLABLES = ["vel", "mor", "zan", "tri", "kol", "ash", "ren", "dul", "pra", "quin", "sol", "bex"]


def make_name(n):
    return "".join(random.choice(SYLLABLES) for _ in range(n)).capitalize()


rows = []
for i in range(40):
    country, city, river = make_name(3), make_name(2), make_name(2)
    year = random.randint(1200, 1900)
    q, a = [
        (f"What is the capital of the fictional country {country}?",
         f"The capital of {country} is {city}."),
        (f"Which river flows through {city}?",
         f"The {river} river flows through {city}, the capital of {country}."),
        (f"When was {city} founded?",
         f"{city} was founded in {year} and later became the capital of {country}."),
    ][i % 3]
    rows.append({"messages": [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": q},
        {"role": "assistant", "content": a},
    ]})

with open("data/smoke_test.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
print(f"Wrote {len(rows)} examples to data/smoke_test.jsonl")
print("Example:", rows[0]["messages"][1]["content"], "->", rows[0]["messages"][2]["content"])
