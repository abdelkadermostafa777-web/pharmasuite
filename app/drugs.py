"""Offline library of common drugs (name, SMILES, chemistry tags used by formulation rules)."""

DRUGS = [
    {"key": "aspirin", "en": "Aspirin", "ar": "الأسبرين", "smiles": "CC(=O)Oc1ccccc1C(=O)O", "tags": ["ester", "acidic"]},
    {"key": "paracetamol", "en": "Paracetamol", "ar": "الباراسيتامول", "smiles": "CC(=O)Nc1ccc(O)cc1", "tags": []},
    {"key": "ibuprofen", "en": "Ibuprofen", "ar": "الإيبوبروفين", "smiles": "CC(C)Cc1ccc(C(C)C(=O)O)cc1", "tags": ["acidic"]},
    {"key": "caffeine", "en": "Caffeine", "ar": "الكافيين", "smiles": "Cn1cnc2c1c(=O)n(C)c(=O)n2C", "tags": []},
    {"key": "diazepam", "en": "Diazepam", "ar": "الديازيبام", "smiles": "CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21", "tags": []},
    {"key": "lidocaine", "en": "Lidocaine", "ar": "الليدوكايين", "smiles": "CCN(CC)CC(=O)Nc1c(C)cccc1C", "tags": []},
    {"key": "metformin", "en": "Metformin", "ar": "الميتفورمين", "smiles": "CN(C)C(=N)NC(=N)N", "tags": []},
    {"key": "metronidazole", "en": "Metronidazole", "ar": "الميترونيدازول", "smiles": "Cc1ncc([N+](=O)[O-])n1CCO", "tags": []},
    {"key": "ciprofloxacin", "en": "Ciprofloxacin", "ar": "السيبروفلوكساسين", "smiles": "O=C(O)c1cn(C2CC2)c2cc(N3CCNCC3)c(F)cc2c1=O", "tags": ["acidic"]},
    {"key": "dopamine", "en": "Dopamine", "ar": "الدوبامين", "smiles": "NCCc1ccc(O)c(O)c1", "tags": ["primary_amine", "oxidizable"]},
    {"key": "amphetamine", "en": "Amphetamine", "ar": "الأمفيتامين", "smiles": "CC(N)Cc1ccccc1", "tags": ["primary_amine"]},
    {"key": "ascorbic_acid", "en": "Ascorbic acid", "ar": "حمض الأسكوربيك", "smiles": "OCC(O)C1OC(=O)C(O)=C1O", "tags": ["oxidizable", "acidic"]},
    {"key": "salicylic_acid", "en": "Salicylic acid", "ar": "حمض الساليسيليك", "smiles": "OC(=O)c1ccccc1O", "tags": ["acidic"]},
    {"key": "nicotine", "en": "Nicotine", "ar": "النيكوتين", "smiles": "CN1CCCC1c1cccnc1", "tags": []},
]


def by_key(key):
    return next((d for d in DRUGS if d["key"] == key), None)


def display_name(drug, lang):
    return drug[lang] if lang in ("en", "ar") else drug["en"]


def find(query, lang="en"):
    q = query.strip().lower()
    if not q:
        return None
    for d in DRUGS:
        if q == d["key"] or q == d["en"].lower() or q == d["ar"] or q == d["smiles"].lower():
            return d
    for d in DRUGS:
        if q in d["en"].lower() or q in d["ar"]:
            return d
    return None
