"""Substructure search over local candidates (offline). Uses RDKit."""
from rdkit import Chem


def parse_fragment(text):
    """Accept SMARTS or SMILES for the fragment. Returns an RDKit query mol or raises ValueError."""
    text = text.strip()
    if not text:
        raise ValueError("empty fragment")
    mol = Chem.MolFromSmarts(text)
    if mol is None:
        mol = Chem.MolFromSmiles(text)
    if mol is None:
        raise ValueError("invalid fragment")
    return mol


def search(fragment_text, candidates):
    """candidates: list of dicts with 'name' and 'smiles'. Returns the ones containing the fragment."""
    query = parse_fragment(fragment_text)
    matches = []
    for c in candidates:
        mol = Chem.MolFromSmiles(c["smiles"])
        if mol is not None and mol.HasSubstructMatch(query):
            matches.append(c)
    return matches
