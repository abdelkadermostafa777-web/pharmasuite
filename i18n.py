"""Translations (Arabic / English) and language switching."""

_LANG = "ar"

STRINGS = {
    "en": {
        "app_title": "PharmaSuite Pro - Desktop",
        "lang_button": "العربية",
        "tab_compound": "Compound Analysis",
        "label_smiles": "SMILES:",
        "placeholder_smiles": "Enter a SMILES string, e.g. CC(=O)Oc1ccccc1C(=O)O",
        "btn_analyze": "Analyze",
        "source_server": "Source: server",
        "source_local": "Source: local (offline)",
        "err_empty": "Please enter a SMILES string.",
        "err_invalid": "Invalid SMILES string.",
        "field_canonical": "Canonical SMILES",
        "field_formula": "Formula",
        "field_mw": "Molecular weight",
        "field_logp": "LogP",
        "field_rotatable": "Rotatable bonds",
        "field_hbd": "H-bond donors",
        "field_hba": "H-bond acceptors",
        "field_violations": "Lipinski violations",
        "field_passes": "Passes Lipinski Rule of 5",
        "yes": "Yes",
        "no": "No",
    },
    "ar": {
        "app_title": "PharmaSuite Pro - سطح المكتب",
        "lang_button": "English",
        "tab_compound": "تحليل المركب",
        "label_smiles": "صيغة SMILES:",
        "placeholder_smiles": "اكتب صيغة SMILES، مثال: CC(=O)Oc1ccccc1C(=O)O",
        "btn_analyze": "تحليل",
        "source_server": "المصدر: السيرفر",
        "source_local": "المصدر: محلي (بدون إنترنت)",
        "err_empty": "من فضلك اكتب صيغة SMILES.",
        "err_invalid": "صيغة SMILES غير صحيحة.",
        "field_canonical": "الصيغة القياسية",
        "field_formula": "الصيغة الجزيئية",
        "field_mw": "الوزن الجزيئي",
        "field_logp": "LogP (الذوبانية)",
        "field_rotatable": "الروابط الدوارة",
        "field_hbd": "متبرعات الهيدروجين",
        "field_hba": "مستقبلات الهيدروجين",
        "field_violations": "مخالفات ليبينسكي",
        "field_passes": "يجتاز قاعدة ليبينسكي للخمسة",
        "yes": "نعم",
        "no": "لا",
    },
}


def set_language(lang):
    global _LANG
    _LANG = lang


def current_lang():
    return _LANG


def t(key):
    return STRINGS[_LANG].get(key, key)
