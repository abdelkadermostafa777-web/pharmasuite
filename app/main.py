"""PharmaSuite Pro - Backend API and web app (FastAPI + RDKit)."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, Lipinski, rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D

from app import chem_tools as ct
from app import drugs, formulation, periodic, substructure
from app.accounts import router as accounts_router
from app.quizzes import router as quizzes_router
from app.assistant import router as assistant_router

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="PharmaSuite Pro API", version="1.3.0")
app.include_router(accounts_router)
app.include_router(quizzes_router)
app.include_router(assistant_router)


class SmilesRequest(BaseModel):
    smiles: str = Field(..., min_length=1, max_length=500, examples=["CC(=O)Oc1ccccc1C(=O)O"])


class CompoundProperties(BaseModel):
    smiles: str
    canonical_smiles: str
    formula: str
    molecular_weight: float
    log_p: float
    rotatable_bonds: int
    h_bond_donors: int
    h_bond_acceptors: int
    lipinski_violations: int
    passes_lipinski: bool


class BalanceRequest(BaseModel):
    equation: str = Field(..., min_length=3, max_length=300, examples=["H2 + O2 -> H2O"])


class BalanceResponse(BaseModel):
    balanced: str
    coefficients: list[int]


class KineticsRequest(BaseModel):
    order: int = Field(..., ge=0, le=2)
    a0: float = Field(..., gt=0)
    k: float = Field(..., gt=0)
    t: float | None = Field(None, ge=0)


class KineticsResponse(BaseModel):
    half_life: float
    concentration: float | None


class ShelfLifeRequest(BaseModel):
    k_ref: float = Field(..., gt=0)
    t_ref_c: float
    ea_kj: float = Field(..., ge=0)
    t_storage_c: float


class ShelfLifeResponse(BaseModel):
    k_storage: float
    t90: float
    t_half: float


class ExcipientItem(BaseModel):
    key: str
    pct: float = Field(..., ge=0, le=100)


class FormulationRequest(BaseModel):
    api: str
    api_pct: float = Field(..., gt=0, le=100)
    excipients: list[ExcipientItem] = Field(default_factory=list, max_length=30)


class FragmentRequest(BaseModel):
    fragment: str = Field(..., min_length=1, max_length=200)


def _mol_or_422(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise HTTPException(status_code=422, detail="Invalid SMILES string")
    return mol


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/compounds/properties", response_model=CompoundProperties)
def compound_properties(req: SmilesRequest):
    mol = _mol_or_422(req.smiles)
    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    violations = sum([mw > 500, logp > 5, hbd > 5, hba > 10])
    return CompoundProperties(
        smiles=req.smiles,
        canonical_smiles=Chem.MolToSmiles(mol),
        formula=rdMolDescriptors.CalcMolFormula(mol),
        molecular_weight=round(mw, 4),
        log_p=round(logp, 4),
        rotatable_bonds=Descriptors.NumRotatableBonds(mol),
        h_bond_donors=hbd,
        h_bond_acceptors=hba,
        lipinski_violations=violations,
        passes_lipinski=violations <= 1,
    )


@app.post("/api/v1/compounds/svg")
def compound_svg(req: SmilesRequest):
    mol = _mol_or_422(req.smiles)
    drawer = rdMolDraw2D.MolDraw2DSVG(400, 400)
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    return {"svg": drawer.GetDrawingText()}


@app.post("/api/v1/compounds/3d")
def compound_3d(req: SmilesRequest):
    mol = Chem.AddHs(_mol_or_422(req.smiles))
    if AllChem.EmbedMolecule(mol, randomSeed=42) != 0:
        raise HTTPException(status_code=422, detail="Could not build a 3D structure")
    try:
        AllChem.MMFFOptimizeMolecule(mol)
    except Exception:
        pass
    return {"molblock": Chem.MolToMolBlock(mol)}


@app.get("/api/v1/elements")
def elements():
    out = []
    for z in range(1, 119):
        row, col = periodic.position(z)
        out.append({
            "z": z,
            "symbol": periodic.PT.GetElementSymbol(z),
            "row": row,
            "col": col,
            "category": periodic.category(z),
            "period": periodic.period_of(z),
            "weight": round(periodic.PT.GetAtomicWeight(z), 4),
            "valence": periodic.PT.GetDefaultValence(z),
            "outer": periodic.PT.GetNOuterElecs(z),
            "shells": periodic.shells(z),
        })
    return out


@app.post("/api/v1/equations/balance", response_model=BalanceResponse)
def balance(req: BalanceRequest):
    try:
        coeffs, text = ct.balance_equation(req.equation)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return BalanceResponse(balanced=text, coefficients=coeffs)


@app.post("/api/v1/kinetics/rate", response_model=KineticsResponse)
def kinetics(req: KineticsRequest):
    try:
        hl = ct.half_life(req.order, req.a0, req.k)
        conc = ct.concentration(req.order, req.a0, req.k, req.t) if req.t is not None else None
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return KineticsResponse(half_life=hl, concentration=conc)


@app.post("/api/v1/stability/shelf-life", response_model=ShelfLifeResponse)
def shelf_life(req: ShelfLifeRequest):
    try:
        result = ct.shelf_life(req.k_ref, req.t_ref_c, req.ea_kj, req.t_storage_c)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return ShelfLifeResponse(**result)


@app.get("/api/v1/drugs")
def list_drugs():
    return drugs.DRUGS


@app.get("/api/v1/formulation/excipients")
def list_excipients():
    return [{"key": k, "role": role, "min": lo, "max": hi}
            for k, (role, lo, hi) in formulation.EXCIPIENTS.items()]


@app.post("/api/v1/formulation/check")
def formulation_check(req: FormulationRequest):
    drug = drugs.by_key(req.api)
    if drug is None:
        raise HTTPException(status_code=422, detail="Unknown active ingredient")
    for e in req.excipients:
        if e.key not in formulation.EXCIPIENTS:
            raise HTTPException(status_code=422, detail=f"Unknown excipient: {e.key}")
    components = [(req.api, req.api_pct)] + [(e.key, e.pct) for e in req.excipients]
    return formulation.check(drug["tags"], components)


@app.post("/api/v1/substructure")
def substructure_search(req: FragmentRequest):
    try:
        substructure.parse_fragment(req.fragment)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    candidates = [{"name": d["en"], "smiles": d["smiles"], "key": d["key"]} for d in drugs.DRUGS]
    return {"matches": substructure.search(req.fragment, candidates)}
