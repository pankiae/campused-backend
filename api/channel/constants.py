# exam/constants.py

EXAM_SUBJECTS = {
    "JEE": ["Physics", "Chemistry", "Mathematics"],
    "UPSC": [
        "General Studies Paper I",
        "CSAT (General Studies Paper II)",
        "General Studies Paper III",
        "General Studies Paper IV",
        "Optional Subject Paper I",
        "Optional Subject Paper II",
        "Language Paper (Indian Language)",
        "English Language Paper",
    ],
    "CLAT": [
        "English Language",
        "Current Affairs & General Knowledge",
        "Legal Reasoning",
        "Logical Reasoning",
        "Quantitative Techniques (Basic Mathematics)",
    ],
    "GATE": [
        "Aerospace Engineering (AE)",
        "Agricultural Engineering (AG)",
        "Architecture and Planning (AR)",
        "Biomedical Engineering (BM)",
        "Biotechnology (BT)",
        "Civil Engineering (CE)",
        "Chemical Engineering (CH)",
        "Computer Science and Information Technology (CS)",
        "Chemistry (CY)",
        "Electronics and Communication Engineering (EC)",
        "Electrical Engineering (EE)",
        "Environmental Science and Engineering (ES)",
        "Ecology and Evolution (EY)",
        "Geology and Geophysics (GG)",
        "Instrumentation Engineering (IN)",
        "Mathematics (MA)",
        "Mechanical Engineering (ME)",
        "Mining Engineering (MN)",
        "Metallurgical Engineering (MT)",
        "Petroleum Engineering (PE)",
        "Physics (PH)",
        "Production and Industrial Engineering (PI)",
        "Statistics (ST)",
        "Textile Engineering and Fibre Science (TF)",
        "Engineering Sciences (XE)",
        "Life Sciences (XL)",
        "Humanities and Social Sciences (XH)",
        "Naval Architecture and Marine Engineering (NM)",
        "Geomatics Engineering (GE)",
        "Data Science and Artificial Intelligence (DA)",
    ],
    "NEET-UG": ["Physics", "Chemistry", "Biology (Botany + Zoology)"],
}

ALLOWED_DIFFICULTIES = ["easy", "medium", "hard"]
ALLOWED_LANGUAGES = ["english", "hindi"]
ALLOWED_MODES = ["flashcard", "mcq"]
