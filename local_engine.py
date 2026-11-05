"""Offline calculations with RDKit, used when the server is unreachable."""
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, rdMolDescriptors


def analyze_local(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("Invalid SMILES")

    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    violations = sum([mw > 500, logp > 5, hbd > 5, hba > 10])

    return {
        "smiles": smiles,
        "canonical_smiles": Chem.MolToSmiles(mol),
        "formula": rdMolDescriptors.CalcMolFormula(mol),
        "molecular_weight": round(mw, 4),
        "log_p": round(logp, 4),
        "rotatable_bonds": Descriptors.NumRotatableBonds(mol),
        "h_bond_donors": hbd,
        "h_bond_acceptors": hba,
        "lipinski_violations": violations,
        "passes_lipinski": violations <= 1,
    }
