"""Seed vocabulary for the fake job board.

Everything here is SYNTHETIC. Company names are invented by combining a prefix
and a suffix; any resemblance to a real company is a coincidence. The generator
(next step) mixes these lists to create thousands of fake offers.
"""

# ---------------------------------------------------------------- companies
COMPANY_PREFIXES = [
    "Atlas", "Nova", "Sahara", "Orion", "Zenith", "Argan", "Medina", "Horizon",
    "Atlantic", "Delta", "Pixel", "Cedre", "Lumen", "Vertex", "Aurora", "Kasbah",
    "Mistral", "Pulsar", "Quantum", "Sirius", "Vega", "Zephyr", "Nimbus", "Opale",
    "Prisme", "Sigma", "Titan", "Alpha", "Cobalt", "Echo", "Helios", "Iris",
    "Jade", "Lotus", "Maestro", "Neptune", "Olympe", "Phoenix", "Rubis", "Solstice",
]

COMPANY_SUFFIXES = [
    "Data Labs", "Systems", "Solutions", "Consulting", "Industries", "Digital",
    "Group", "Tech", "Logistics", "Energy", "Finance", "Software", "Engineering",
    "Services", "Partners", "Innovation", "Networks", "Analytics", "Media",
    "Construction", "Automation", "Retail", "Cloud", "Studio", "Capital",
]

# ------------------------------------------------------------------- cities
# (city, country code, weight): a bigger weight means more offers in that city.
CITIES = [
    ("Casablanca", "MA", 20), ("Rabat", "MA", 12), ("Tanger", "MA", 8),
    ("Marrakech", "MA", 6), ("Fès", "MA", 4), ("Agadir", "MA", 4),
    ("Kénitra", "MA", 3), ("Tétouan", "MA", 2), ("Oujda", "MA", 2),
    ("Meknès", "MA", 2), ("Mohammedia", "MA", 2), ("Salé", "MA", 2),
    ("Paris", "FR", 25), ("Lyon", "FR", 8), ("Toulouse", "FR", 6),
    ("Marseille", "FR", 5), ("Lille", "FR", 5), ("Bordeaux", "FR", 5),
    ("Nantes", "FR", 4), ("Nice", "FR", 3), ("Strasbourg", "FR", 3),
    ("Rennes", "FR", 3), ("Montpellier", "FR", 3), ("Grenoble", "FR", 3),
]

# Other ways real sites write the same city (used later to add "mess").
CITY_ALIASES = {
    "Casablanca": ["Casa", "Casablanca (Maroc)", "CASABLANCA"],
    "Rabat": ["Rabat-Salé", "RABAT"],
    "Fès": ["Fes", "FES"],
    "Kénitra": ["Kenitra"],
    "Tétouan": ["Tetouan"],
    "Meknès": ["Meknes"],
    "Paris": ["Paris 8e", "Paris (75)", "PARIS"],
    "Lyon": ["Lyon (69)", "LYON"],
    "Marseille": ["Marseille (13)"],
}

# ------------------------------------------------------------ job families
# Each family: job titles in French and English, and the skills that go with it.
JOB_FAMILIES = {
    "data_science": {
        "titles_fr": ["Data Scientist", "Data Analyst", "Ingénieur Data", "Ingénieur Machine Learning"],
        "titles_en": ["Data Scientist", "Data Analyst", "Machine Learning Engineer", "Data Engineer"],
        "skills": ["Python", "pandas", "SQL", "scikit-learn", "TensorFlow", "PyTorch",
                   "Power BI", "Tableau", "statistiques", "NLP", "Spark", "Jupyter"],
    },
    "web_dev": {
        "titles_fr": ["Développeur Web", "Développeur Full Stack", "Développeur Front-end", "Développeur Back-end"],
        "titles_en": ["Web Developer", "Full Stack Developer", "Frontend Developer", "Backend Developer"],
        "skills": ["JavaScript", "TypeScript", "React", "Node.js", "HTML", "CSS",
                   "Django", "Next.js", "API REST", "Git"],
    },
    "mobile_dev": {
        "titles_fr": ["Développeur Mobile", "Développeur Android", "Développeur iOS"],
        "titles_en": ["Mobile Developer", "Android Developer", "iOS Developer"],
        "skills": ["Kotlin", "Swift", "Flutter", "React Native", "Firebase", "Git"],
    },
    "devops_cloud": {
        "titles_fr": ["Ingénieur DevOps", "Ingénieur Cloud", "Administrateur Systèmes"],
        "titles_en": ["DevOps Engineer", "Cloud Engineer", "Systems Administrator"],
        "skills": ["Docker", "Kubernetes", "AWS", "Azure", "Linux", "CI/CD",
                   "Terraform", "Ansible", "Git"],
    },
    "cybersecurity": {
        "titles_fr": ["Analyste Cybersécurité", "Ingénieur Sécurité", "Pentester Junior"],
        "titles_en": ["Cybersecurity Analyst", "Security Engineer", "Junior Pentester"],
        "skills": ["SIEM", "Kali Linux", "Nmap", "Wireshark", "ISO 27001", "Python"],
    },
    "software_eng": {
        "titles_fr": ["Développeur Java", "Développeur Python", "Développeur .NET", "Ingénieur Logiciel"],
        "titles_en": ["Java Developer", "Python Developer", ".NET Developer", "Software Engineer"],
        "skills": ["Java", "Spring Boot", "Python", "C#", ".NET", "SQL", "Microservices", "Git"],
    },
    "finance": {
        "titles_fr": ["Analyste Financier", "Assistant Contrôle de Gestion", "Auditeur Junior"],
        "titles_en": ["Financial Analyst", "Management Control Assistant", "Junior Auditor"],
        "skills": ["Excel", "modélisation financière", "IFRS", "SAP", "Power BI", "comptabilité", "VBA"],
    },
    "marketing": {
        "titles_fr": ["Assistant Marketing Digital", "Community Manager", "Chargé de Marketing de Contenu"],
        "titles_en": ["Digital Marketing Assistant", "Community Manager", "Content Marketer"],
        "skills": ["SEO", "Google Analytics", "Canva", "Meta Ads", "copywriting", "Mailchimp"],
    },
    "hr": {
        "titles_fr": ["Assistant RH", "Chargé de Recrutement", "Assistant Paie"],
        "titles_en": ["HR Assistant", "Recruitment Assistant", "Payroll Assistant"],
        "skills": ["recrutement", "paie", "SIRH", "droit du travail", "Excel", "communication"],
    },
    "civil_eng": {
        "titles_fr": ["Ingénieur Génie Civil", "Assistant Chef de Chantier", "Ingénieur Travaux"],
        "titles_en": ["Civil Engineer", "Assistant Site Manager", "Works Engineer"],
        "skills": ["AutoCAD", "Revit", "Robot Structural Analysis", "MS Project",
                   "béton armé", "topographie"],
    },
    "industrial_eng": {
        "titles_fr": ["Ingénieur Méthodes", "Ingénieur Mécanique", "Ingénieur Qualité"],
        "titles_en": ["Industrial Engineer", "Mechanical Engineer", "Quality Engineer"],
        "skills": ["SolidWorks", "CATIA", "Lean Manufacturing", "Six Sigma", "AutoCAD",
                   "gestion de production", "maintenance"],
    },
    "electronics": {
        "titles_fr": ["Ingénieur Électronique", "Ingénieur Systèmes Embarqués", "Ingénieur Automatisme"],
        "titles_en": ["Electronics Engineer", "Embedded Systems Engineer", "Automation Engineer"],
        "skills": ["C", "C++", "Arduino", "PLC", "MATLAB", "Simulink", "Altium", "Raspberry Pi"],
    },
    "logistics": {
        "titles_fr": ["Assistant Logistique", "Assistant Supply Chain", "Gestionnaire Transport"],
        "titles_en": ["Logistics Assistant", "Supply Chain Assistant", "Transport Planner"],
        "skills": ["SAP", "Excel", "supply chain", "gestion des stocks", "WMS", "Incoterms"],
    },
    "sales": {
        "titles_fr": ["Assistant Commercial", "Business Developer", "Chargé de Clientèle"],
        "titles_en": ["Sales Assistant", "Business Developer", "Account Manager"],
        "skills": ["CRM", "Salesforce", "négociation", "prospection", "Excel", "communication"],
    },
    "design": {
        "titles_fr": ["UX/UI Designer", "Graphiste", "Product Designer"],
        "titles_en": ["UX/UI Designer", "Graphic Designer", "Product Designer"],
        "skills": ["Figma", "Adobe XD", "Photoshop", "Illustrator", "wireframing", "prototypage"],
    },
    "project_mgmt": {
        "titles_fr": ["Assistant Chef de Projet", "Business Analyst", "Chargé de Projet IT"],
        "titles_en": ["Project Management Assistant", "Business Analyst", "IT Project Coordinator"],
        "skills": ["Agile", "Scrum", "Jira", "MS Project", "UML", "Excel", "communication"],
    },
}

# --------------------------------------------------------------- contracts
# (code, is_internship, weight). Non-internships let the internship filter work.
CONTRACTS = [
    ("stage", True, 45),
    ("pfe", True, 20),
    ("alternance", True, 10),
    ("cdi", False, 15),
    ("cdd", False, 10),
]

# How the contract appears in the job title. Internship titles contain a keyword
# our filter knows (stage, intern, PFE, alternance), CDI/CDD titles do not.
TITLE_FORMATS = {
    "stage": {
        "fr": ["Stage {title}", "Stagiaire {title}", "{title} (Stage)"],
        "en": ["{title} Intern", "{title} Internship"],
    },
    "pfe": {
        "fr": ["PFE – {title}", "Stage PFE {title}"],
        "en": ["{title} Intern (PFE)", "PFE Internship – {title}"],
    },
    "alternance": {
        "fr": ["{title} en alternance", "Alternance – {title}"],
        "en": ["{title} (Alternance)"],
    },
    "cdi": {"fr": ["{title}"], "en": ["{title}"]},
    "cdd": {"fr": ["{title} (CDD)"], "en": ["{title} (Fixed-term)"]},
}

# Internship durations in months, with weights.
DURATIONS = [(2, 15), (3, 25), (4, 20), (6, 40)]
DURATION_TEXT = {"fr": "{n} mois", "en": "{n} months"}

# -------------------------------------------------------------- languages
# Share of French / English offers by country.
LANGUAGE_WEIGHTS = {"MA": {"fr": 80, "en": 20}, "FR": {"fr": 85, "en": 15}}

EDUCATION = {
    "fr": ["Bac+3", "Bac+4", "Bac+5", "Master 2", "Cycle ingénieur"],
    "en": ["Bachelor's degree", "Master's degree", "Engineering student"],
}

# ------------------------------------------------- description templates
# Placeholders: {company} {city} {title} {skills} {main_skill} {education} {duration}
DESCRIPTION_TEMPLATES = {
    "fr": [
        ("{company} recherche un(e) {title} pour renforcer son équipe à {city}. "
        "Vous participerez à des projets concrets en utilisant {skills}. "
        "Profil recherché : étudiant(e) en {education}, avec de bonnes bases en {main_skill}. "
        "Durée : {duration}. Nous offrons un encadrement personnalisé et une réelle "
        "opportunité d'apprentissage."),
        ("Rejoignez {company}, à {city}. Missions : analyser les besoins, contribuer au "
        "développement des projets de l'équipe et présenter vos résultats. "
        "Compétences : {skills}. Niveau demandé : {education}. Durée : {duration}."),
        ("Dans le cadre de son développement, {company} ({city}) propose un poste de "
        "{title}. Vous serez accompagné(e) par un tuteur et travaillerez avec {skills}. "
        "Autonomie, curiosité et maîtrise de {main_skill} appréciées. Durée : {duration}."),
        ("Vous avez envie d'apprendre dans une équipe dynamique ? {company} vous accueille à "
        "{city} comme {title}. Outils : {skills}. Formation : {education}. Durée : {duration}."),
    ],
    "en": [
        ("{company} is looking for a {title} to join the team in {city}. "
        "You will work on real projects using {skills}. "
        "Ideal profile: {education} with a solid foundation in {main_skill}. "
        "Duration: {duration}. We offer close mentoring and a real learning opportunity."),
        ("Join {company} in {city}. Responsibilities: analyse needs, contribute to team "
        "projects and present your results. Skills: {skills}. Education: {education}. "
        "Duration: {duration}."),
        ("As part of its growth, {company} ({city}) opens a {title} position. "
        "You will be supported by a mentor and work with {skills}. "
        "Curiosity and strong {main_skill} skills are a plus. Duration: {duration}."),
        ("Want to learn in a dynamic team? {company} welcomes you in {city} as {title}. "
        "Tools: {skills}. Education: {education}. Duration: {duration}."),
    ],
}


if __name__ == "__main__":
    # Quick self-check: python -m mock_jobboard.seed
    print("companies possible:", len(COMPANY_PREFIXES) * len(COMPANY_SUFFIXES))
    print("cities:", len(CITIES), "| families:", len(JOB_FAMILIES))
    for name, family in JOB_FAMILIES.items():
        print(f"  {name}: {len(family['titles_fr'])} titles, {len(family['skills'])} skills")