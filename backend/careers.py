"""
Career step of EduPath -- HARD-CODED if/else rules, no machine learning.

Flow: student picks a field -> get_questions(field) gives 3 follow-up questions
      -> recommend_career(field, answers) walks plain if/else rules to one career.
Question ids and option values below are exactly what the rules test.
"""

def Q(id_, text, *options):
    return {"id": id_, "text": text, "options": [{"value": v, "label": l} for v, l in options]}

# ------------------------------------------------------------------ questions
QUESTIONS = {
 "Computer Science & Information Technology": [
    Q("focus", "Which area excites you most?", ("software", "Building apps, websites or software"),
      ("data", "Finding patterns in data and teaching computers to learn"),
      ("security", "Protecting systems from attackers"), ("systems", "Networks, servers and cloud infrastructure")),
    Q("style", "How do you like to work?", ("hands_on", "Hands-on: build it, test it, fix it"),
      ("abstract", "Thinking: design systems and solve puzzles"), ("lead", "Leading: coordinate people and projects")),
    Q("math", "How do you feel about advanced math (calculus, statistics)?", ("love", "I enjoy it"),
      ("ok", "I can handle it"), ("avoid", "I would rather avoid it"))],
 "Engineering & Technology": [
    Q("focus", "What would you like to work on?", ("electronics", "Circuits, devices and robots"),
      ("machines", "Machines, engines and tools"), ("vehicles", "Cars, aircraft and transport"),
      ("process", "Factories, materials and chemical processes")),
    Q("style", "How do you like to work?", ("hands_on", "Hands-on: build it, test it, fix it"),
      ("abstract", "Design and analysis at a desk or computer"), ("lead", "Leading people and projects")),
    Q("math", "How do you feel about advanced math and physics?", ("love", "I enjoy it"),
      ("ok", "I can handle it"), ("avoid", "I would rather avoid it"))],
 "Medical & Health Sciences": [
    Q("role", "Which role sounds most like you?", ("diagnose", "Diagnosing and treating patients"),
      ("bedside", "Caring for patients day to day"), ("medicine", "Medicines and how they work"),
      ("rehab", "Helping people recover movement and strength"), ("lab", "Lab tests and medical technology")),
    Q("years", "How many years of study can you commit to?", ("short", "2 to 4 years"),
      ("medium", "4 to 6 years"), ("long", "7 years or more")),
    Q("blood", "Are you comfortable with blood and emergencies?", ("yes", "Yes"), ("no", "Not really"))],
 "Business & Management": [
    Q("focus", "What draws you to business?", ("numbers", "Money, accounts and markets"),
      ("startup", "Starting my own business"), ("marketing", "Marketing, brands and customers"),
      ("managing", "Managing teams and operations")),
    Q("risk", "How do you feel about risk?", ("high", "I'll take big risks for big rewards"),
      ("low", "I prefer stable, predictable work")),
    Q("detail", "Which do you prefer?", ("detail", "Careful details and accuracy"),
      ("picture", "The big picture and strategy"))],
 "Natural & Physical Sciences": [
    Q("focus", "Which area fascinates you most?", ("life", "Living things, genes and cells"),
      ("chemistry", "Chemistry and how substances react"), ("physics", "Physics, energy and materials")),
    Q("setting", "Where would you like to work?", ("lab", "In a laboratory"),
      ("field", "Out in the field"), ("computer", "At a computer, modelling and analysing")),
    Q("study", "How far are you willing to study?", ("phd", "Up to a PhD (research career)"),
      ("bachelor", "A bachelor's or master's, then work"))],
 "Social Sciences": [
    Q("focus", "Which question interests you most?", ("mind", "Why do people think and behave the way they do?"),
      ("society", "How can society and government work better?"), ("helping", "How can I directly help people in need?"),
      ("economy", "How do money, work and markets shape people's lives?")),
    Q("grad", "Are you willing to do graduate school?", ("yes", "Yes"),
      ("no", "No, I want to start working after a bachelor's")),
    Q("scale", "Where do you want to make an impact?", ("one_on_one", "One-on-one with individuals"),
      ("big", "At the level of groups, systems or policy"))],
 "Arts, Design & Humanities": [
    Q("focus", "What do you most want to do?", ("visual", "Create visual art and design"),
      ("writing", "Write books, poems and stories"), ("performing", "Make music or perform in theatre"),
      ("culture", "Explore languages, history and culture")),
    Q("freedom", "What matters more to you?", ("freedom", "Creative freedom, even if income varies"),
      ("stable", "A steady job with structure")),
    Q("tools", "Which tools do you prefer?", ("digital", "Digital tools and software"),
      ("traditional", "Traditional tools and live settings"))],
 "Law & Legal Studies": [
    Q("focus", "Which part of the legal world interests you?", ("courtroom", "Arguing cases and the courtroom"),
      ("business", "Contracts, companies and compliance"), ("enforcement", "Investigating crime and enforcing the law"),
      ("research", "Studying crime, justice and the legal system")),
    Q("grad", "Are you willing to go to law school or graduate school?", ("yes", "Yes"),
      ("no", "No, I want to start working after a bachelor's")),
    Q("style", "Which do you prefer?", ("people", "Working directly with people"),
      ("documents", "Working with documents and research"))],
 "Education & Teaching": [
    Q("age", "Who do you want to teach?", ("early", "Young children (preschool)"),
      ("primary", "Primary school"), ("secondary", "Teenagers (secondary school)"),
      ("special", "Students with special learning needs"), ("higher", "University students")),
    Q("subject", "Which subjects suit you best?", ("stem", "Math, science or computing"),
      ("humanities", "Languages, history or arts")),
    Q("lead", "Do you want to lead a school one day?", ("yes", "Yes, I like leadership"),
      ("no", "No, I prefer to stay in the classroom"))],
 "Agriculture & Veterinary Sciences": [
    Q("focus", "What interests you most?", ("animals", "Animals and their health"),
      ("crops", "Crops, soil and farming"), ("food", "Food production and the food industry")),
    Q("years", "How many years of study can you commit to?", ("short", "2 to 4 years"),
      ("medium", "4 to 6 years"), ("long", "7 years or more")),
    Q("setting", "Where would you like to work?", ("field", "Outdoors, on farms and land"),
      ("lab", "In a laboratory"), ("office", "In an office, planning and managing"))],
 "Architecture & Built Environment": [
    Q("focus", "What would you like to do?", ("design", "Design buildings"),
      ("planning", "Plan cities and land use"), ("construction", "Manage building projects"),
      ("interiors", "Design interiors and outdoor spaces")),
    Q("style", "Which describes you better?", ("creative", "Creative: I love ideas and aesthetics"),
      ("technical", "Technical: I love measurements and systems")),
    Q("years", "How many years of study can you commit to?", ("short", "2 to 4 years"),
      ("long", "5 years or more"))],
 "Media & Communication": [
    Q("focus", "What do you most want to do?", ("film", "Make films and videos"),
      ("news", "Report the news and tell true stories"), ("digital", "Create online and social media content"),
      ("pr", "Shape how organisations communicate (PR, advertising)")),
    Q("freedom", "What matters more to you?", ("freedom", "Creative freedom and independence"),
      ("stable", "A steady job in a team")),
    Q("tools", "Which setting do you prefer?", ("digital", "Digital and online"),
      ("traditional", "Traditional media and live production"))],
 "Mathematics & Statistics": [
    Q("focus", "What attracts you most?", ("pure", "Pure math: proofs and patterns"),
      ("stats", "Statistics: learning from data"), ("finance", "Finance and risk")),
    Q("study", "How far are you willing to study?", ("phd", "Up to a PhD"),
      ("bachelor", "A bachelor's or master's, then work")),
    Q("mode", "Which do you enjoy more?", ("code", "Programming and computation"),
      ("theory", "Theory and problem solving on paper"))],
 "Environmental & Earth Sciences": [
    Q("focus", "Which topic matters most to you?", ("climate", "Weather and climate"),
      ("land", "Rocks, soil and the planet's structure"), ("water", "Oceans, rivers and ecosystems"),
      ("sustain", "Sustainability and protecting nature")),
    Q("setting", "Where would you like to work?", ("field", "Outdoors, in the field"),
      ("lab", "In a laboratory"), ("computer", "At a computer, modelling and mapping")),
    Q("study", "How far are you willing to study?", ("phd", "Up to a PhD (research career)"),
      ("bachelor", "A bachelor's or master's, then work"))],
 "Hospitality, Tourism & Sports": [
    Q("focus", "Which world appeals to you?", ("food", "Food and cooking"),
      ("hotel", "Hotels and guest experience"), ("travel", "Travel and tourism"),
      ("sports", "Sports, coaching and fitness")),
    Q("pace", "What pace suits you?", ("fast", "Fast and busy"), ("calm", "Calm and steady")),
    Q("own", "Which do you prefer?", ("own", "Running my own business"),
      ("team", "Working as part of a team"))],
}

def get_questions(field):
    return QUESTIONS.get(field)

# ---------------------------------------------------------------------- rules
def _rules(field, a):
    """Returns (title, description). a = {question_id: chosen_value}. Plain if/else."""

    if field == "Computer Science & Information Technology":
        focus, style, math = a["focus"], a["style"], a["math"]
        if focus == "software":
            if style == "abstract" and math != "avoid":
                return "Software Engineer", "Designs and builds the core systems behind apps and services."
            elif style == "hands_on":
                return "Web / Mobile Developer", "Builds websites and phone apps people use every day."
            elif style == "lead":
                return "Technical Project Manager", "Leads software teams from idea to launch."
            else:
                return "Software Tester / QA Engineer", "Finds problems in software before users do."
        elif focus == "data":
            if math == "love":
                return "Data Scientist / ML Engineer", "Builds models that learn from data to predict and decide."
            elif math == "ok":
                return "Data Analyst", "Turns data into charts and insights that guide decisions."
            else:
                return "Business Intelligence Developer", "Builds dashboards and reports from company data."
        elif focus == "security":
            if style == "hands_on":
                return "Penetration Tester (Ethical Hacker)", "Breaks into systems legally to find weaknesses first."
            elif style == "lead":
                return "Information Security Manager", "Plans and leads an organisation's cyber defence."
            elif math != "avoid":
                return "Security / Cryptography Engineer", "Designs secure systems and encryption."
            else:
                return "Security Operations Analyst", "Monitors networks and responds to threats."
        else:  # systems
            if style == "hands_on":
                return "Network Engineer", "Builds and maintains the networks organisations depend on."
            elif style == "abstract":
                return "Cloud / DevOps Engineer", "Designs and automates cloud infrastructure."
            else:
                return "IT Manager", "Leads the technology teams and systems of an organisation."

    elif field == "Engineering & Technology":
        focus, style, math = a["focus"], a["style"], a["math"]
        if focus == "electronics":
            if style == "hands_on":
                return "Embedded Systems / Electronics Engineer", "Designs circuits and the software inside devices and robots."
            elif style == "abstract":
                return "Electrical / Telecom Engineer", "Designs power, signal and communication systems."
            else:
                return "Engineering Project Manager", "Leads technical teams delivering electronic products."
        elif focus == "machines":
            if style == "hands_on":
                return "Mechanical Engineer", "Designs and tests engines, machines and tools."
            elif style == "abstract" and math != "avoid":
                return "Mechanical Design / Robotics Engineer", "Models and designs advanced mechanical systems."
            elif style == "abstract":
                return "CAD Technician", "Turns engineers' ideas into detailed technical drawings."
            else:
                return "Plant / Maintenance Manager", "Keeps machines and production running."
        elif focus == "vehicles":
            if style == "hands_on":
                return "Automotive / Aircraft Maintenance Engineer", "Inspects, repairs and certifies vehicles and aircraft."
            elif style == "abstract" and math == "love":
                return "Aerospace Engineer", "Designs aircraft, spacecraft and propulsion systems."
            elif style == "abstract":
                return "Automotive Design Engineer", "Designs and improves vehicle systems."
            else:
                return "Transport / Fleet Operations Manager", "Manages vehicles, crews and logistics."
        else:  # process
            if style == "hands_on":
                return "Manufacturing / Process Technician", "Runs and improves production lines."
            elif style == "abstract":
                return "Chemical / Materials Engineer", "Designs processes that turn raw materials into products."
            else:
                return "Industrial / Production Manager", "Plans and manages factory operations."

    elif field == "Medical & Health Sciences":
        role, years, blood = a["role"], a["years"], a["blood"]
        if role == "diagnose":
            if years == "long" and blood == "yes":
                return "Physician (Doctor)", "Diagnoses and treats patients across medical specialties."
            elif years == "long":
                return "Radiologist / Pathologist", "Diagnoses disease from scans and lab samples."
            elif years == "medium":
                return "Physician Assistant", "Examines and treats patients under physician supervision."
            else:
                return "Paramedic / Emergency Medical Technician", "Gives emergency care at the scene and in ambulances."
        elif role == "bedside":
            if years == "short":
                return "Practical Nurse / Nursing Assistant", "Provides daily patient care in hospitals and clinics."
            else:
                return "Registered Nurse", "Delivers and coordinates patient care in hospitals and clinics."
        elif role == "medicine":
            if years == "short":
                return "Pharmacy Technician", "Prepares and dispenses medicines under a pharmacist."
            else:
                return "Pharmacist", "Advises on medicines and makes sure prescriptions are safe."
        elif role == "rehab":
            if years == "short":
                return "Physical Therapist Assistant / Fitness Trainer", "Guides patients through exercises that rebuild strength."
            else:
                return "Physical Therapist", "Treats injuries and movement problems to restore function."
        else:  # lab
            if years == "short":
                return "Medical Laboratory Technician", "Runs routine tests on blood and tissue samples."
            else:
                return "Medical Laboratory Scientist", "Performs and interprets advanced diagnostic tests."

    elif field == "Business & Management":
        focus, risk, detail = a["focus"], a["risk"], a["detail"]
        if focus == "numbers":
            if risk == "high":
                return "Financial / Investment Analyst", "Evaluates investments and advises on where to put money."
            elif detail == "detail":
                return "Accountant / Auditor", "Keeps accurate financial records and checks compliance."
            else:
                return "Financial Planner / Bank Manager", "Helps people and firms plan their money."
        elif focus == "startup":
            if risk == "high":
                return "Entrepreneur / Startup Founder", "Builds a new company from an idea."
            else:
                return "Small Business Owner / Franchise Manager", "Runs an established business with proven methods."
        elif focus == "marketing":
            if detail == "picture":
                return "Marketing / Brand Manager", "Shapes how a brand is seen and sold."
            else:
                return "Market Research Analyst", "Studies customers and competitors with data."
        else:  # managing
            if detail == "picture":
                return "Human Resources Manager", "Hires, develops and supports a company's people."
            else:
                return "Operations / Supply Chain Manager", "Keeps production and delivery running smoothly."

    elif field == "Natural & Physical Sciences":
        focus, setting, study = a["focus"], a["setting"], a["study"]
        if focus == "life":
            if study == "phd" and setting == "lab":
                return "Biomedical / Molecular Researcher", "Studies cells and genes to understand disease."
            elif setting == "field":
                return "Wildlife Biologist / Ecologist", "Studies animals and ecosystems outdoors."
            elif setting == "computer":
                return "Bioinformatics Specialist", "Analyses biological data with code and statistics."
            else:
                return "Biotechnology Lab Scientist", "Develops products like vaccines and crops in a lab."
        elif focus == "chemistry":
            if study == "phd":
                return "Research Chemist", "Discovers new compounds and reactions."
            elif setting == "lab":
                return "Analytical Chemist", "Tests and measures the chemical makeup of materials."
            elif setting == "computer":
                return "Computational Chemist", "Simulates molecules and reactions on computers."
            else:
                return "Forensic Scientist", "Analyses physical evidence for investigations."
        else:  # physics
            if study == "phd":
                return "Physicist (Researcher)", "Investigates how matter and energy behave."
            elif setting == "lab":
                return "Materials Scientist / Lab Technologist", "Tests and develops new materials."
            elif setting == "field":
                return "Renewable Energy Technologist", "Installs and tests solar, wind and other energy systems."
            else:
                return "Science Data Modeller", "Models physical systems and analyses experimental data."

    elif field == "Social Sciences":
        focus, grad, scale = a["focus"], a["grad"], a["scale"]
        if focus == "mind":
            if scale == "one_on_one" and grad == "yes":
                return "Clinical / Counselling Psychologist", "Helps people through mental-health challenges."
            elif scale == "one_on_one":
                return "Human Services / Mental Health Assistant", "Supports clients and counsellors in care settings."
            else:
                return "UX / Behavioural Researcher", "Studies how people behave to improve products and services."
        elif focus == "society":
            if grad == "yes":
                return "Policy Analyst / Sociologist", "Researches social problems and designs better policy."
            else:
                return "Government Program Officer", "Runs public programs and services."
        elif focus == "helping":
            if grad == "yes":
                return "Licensed Social Worker", "Supports individuals and families through hardship."
            else:
                return "Community Outreach Worker", "Connects people to services in their community."
        else:  # economy
            if grad == "yes":
                return "Economist", "Studies how money, markets and policy shape society."
            else:
                return "Research Associate / Survey Analyst", "Collects and analyses data on people and the economy."

    elif field == "Arts, Design & Humanities":
        focus, freedom, tools = a["focus"], a["freedom"], a["tools"]
        if focus == "visual":
            if tools == "digital":
                return "UI / Graphic Designer", "Designs interfaces, logos and visual identities."
            elif freedom == "freedom":
                return "Illustrator / Fine Artist", "Creates original artwork for clients and galleries."
            else:
                return "Art Director / Art Teacher", "Guides a team's visual style or teaches art."
        elif focus == "writing":
            if freedom == "freedom":
                return "Author / Freelance Writer", "Writes books, articles and copy on their own terms."
            else:
                return "Editor / Publishing Professional", "Shapes manuscripts and content for publication."
        elif focus == "performing":
            if tools == "digital":
                return "Music Producer / Sound Designer", "Creates and records music and audio."
            elif freedom == "freedom":
                return "Musician / Performing Artist", "Performs and creates music or theatre."
            else:
                return "Music / Drama Teacher", "Teaches performance in schools and academies."
        else:  # culture
            if freedom == "freedom":
                return "Translator / Interpreter", "Moves meaning between languages."
            else:
                return "Museum Curator / Librarian", "Preserves and shares history and knowledge."

    elif field == "Law & Legal Studies":
        focus, grad, style = a["focus"], a["grad"], a["style"]
        if focus == "courtroom":
            if grad == "yes" and style == "people":
                return "Trial Lawyer / Barrister", "Represents clients and argues cases in court."
            elif grad == "yes":
                return "Legal Counsel / Judicial Clerk", "Researches law and prepares legal arguments and rulings."
            elif style == "people":
                return "Court Officer / Legal Assistant", "Supports hearings and clients in the court system."
            else:
                return "Paralegal", "Prepares cases and documents for lawyers."
        elif focus == "business":
            if grad == "yes" and style == "people":
                return "Corporate Lawyer", "Advises companies on deals, contracts and disputes."
            elif grad == "yes":
                return "Contract / IP Specialist", "Drafts contracts and protects intellectual property."
            elif style == "documents":
                return "Compliance Officer", "Makes sure a company follows laws and regulations."
            else:
                return "Contracts Administrator", "Manages agreements between a company and its partners."
        elif focus == "enforcement":
            if grad == "yes":
                return "Criminal Investigator / Federal Agent", "Investigates serious crimes and builds cases."
            elif style == "people":
                return "Police Officer", "Protects the public and enforces the law."
            else:
                return "Crime Analyst", "Studies crime data to help police prevent and solve crime."
        else:  # research
            if grad == "yes":
                return "Criminologist", "Studies the causes of crime and how to prevent it."
            elif style == "people":
                return "Probation / Parole Officer", "Supervises and supports people serving community sentences."
            else:
                return "Legal Researcher / Court Administrator", "Researches law and keeps the court process running."

    elif field == "Education & Teaching":
        age, subject, lead = a["age"], a["subject"], a["lead"]
        if age == "early":
            return "Early Childhood Educator", "Teaches children through play in their first school years."
        elif age == "primary":
            if lead == "yes":
                return "Primary Teacher heading to School Principal", "Teaches primary school and grows into school leadership."
            else:
                return "Primary School Teacher", "Teaches core subjects to children."
        elif age == "secondary":
            if subject == "stem" and lead == "yes":
                return "STEM Teacher heading to Department Head", "Teaches math or science and leads a department."
            elif subject == "stem":
                return "Secondary Math / Science Teacher", "Teaches math, science or computing to teenagers."
            elif lead == "yes":
                return "Humanities Teacher heading to Department Head", "Teaches languages, history or arts and leads a department."
            else:
                return "Secondary Language / History Teacher", "Teaches languages, history or arts to teenagers."
        elif age == "special":
            return "Special Education Teacher", "Adapts teaching for students with learning needs."
        else:  # higher
            return "University Lecturer / Professor", "Teaches and researches at university level."

    elif field == "Agriculture & Veterinary Sciences":
        focus, years, setting = a["focus"], a["years"], a["setting"]
        if focus == "animals":
            if years == "long":
                return "Veterinarian", "Diagnoses and treats illness and injury in animals."
            elif years == "medium":
                return "Animal Scientist / Zoologist", "Studies animal biology, nutrition and breeding."
            else:
                return "Veterinary Technician", "Assists vets with exams, tests and treatment."
        elif focus == "crops":
            if setting == "field":
                return "Agronomist / Farm Manager", "Improves crop yields and runs farm operations."
            elif setting == "lab":
                return "Plant Scientist / Agricultural Biotechnologist", "Develops better crops through plant science."
            else:
                return "Agricultural Economist / Extension Officer", "Advises farmers and analyses farm markets."
        else:  # food
            if setting == "lab":
                return "Food Scientist", "Develops and tests safe, better food products."
            elif setting == "field":
                return "Food Production Manager", "Runs farms and plants that produce food."
            else:
                return "Agribusiness Manager", "Manages the business side of farming and food supply."

    elif field == "Architecture & Built Environment":
        focus, style, years = a["focus"], a["style"], a["years"]
        if focus == "design":
            if years == "long":
                return "Architect", "Designs buildings that are safe, useful and beautiful."
            elif style == "technical":
                return "Architectural Technician / CAD Drafter", "Produces detailed technical drawings of buildings."
            else:
                return "Architectural Assistant / 3D Visualiser", "Creates models and images of building designs."
        elif focus == "planning":
            if years == "long":
                return "Urban Planner", "Plans how cities and land are used."
            elif style == "technical":
                return "Land / Building Surveyor", "Measures and assesses land and buildings."
            else:
                return "Planning Assistant", "Supports planners with research and applications."
        elif focus == "construction":
            if style == "technical" and years == "long":
                return "Construction Manager", "Leads building projects on time and on budget."
            elif style == "technical":
                return "Site Supervisor / Quantity Surveyor", "Oversees site work and tracks construction costs."
            else:
                return "Construction Project Coordinator", "Coordinates teams, suppliers and schedules on projects."
        else:  # interiors
            if style == "creative" and years == "long":
                return "Landscape Architect", "Designs parks, gardens and outdoor spaces."
            elif style == "creative":
                return "Interior Designer", "Designs functional, attractive indoor spaces."
            else:
                return "Space Planner / CAD Designer", "Plans layouts and produces detailed interior drawings."

    elif field == "Media & Communication":
        focus, freedom, tools = a["focus"], a["freedom"], a["tools"]
        if focus == "film":
            if tools == "digital" and freedom == "freedom":
                return "Content Creator / Filmmaker", "Makes and publishes videos independently."
            elif tools == "digital":
                return "Video Editor / Motion Designer", "Edits footage and creates animated visuals."
            elif freedom == "freedom":
                return "Film Director", "Leads the creative vision of films and shows."
            else:
                return "TV / Broadcast Producer", "Organises and produces programmes."
        elif focus == "news":
            if freedom == "freedom" and tools == "digital":
                return "Independent Journalist / Podcaster", "Reports and tells stories directly to an online audience."
            elif freedom == "freedom":
                return "Freelance Correspondent / Writer", "Reports and writes for many outlets."
            elif tools == "digital":
                return "Digital Newsroom Editor", "Edits and publishes news online."
            else:
                return "Broadcast Journalist", "Reports the news on TV and radio."
        elif focus == "digital":
            if freedom == "freedom":
                return "Social Media Creator / Strategist", "Builds an audience and brand online."
            else:
                return "Digital Marketing Specialist", "Runs online campaigns for organisations."
        else:  # pr
            if tools == "digital":
                return "Social Media / Community Manager", "Manages an organisation's online voice and community."
            elif freedom == "freedom":
                return "Communications Consultant", "Advises clients on messaging and reputation."
            else:
                return "PR / Corporate Communications Officer", "Manages an organisation's public image."

    elif field == "Mathematics & Statistics":
        focus, study, mode = a["focus"], a["study"], a["mode"]
        if focus == "pure":
            if study == "phd":
                return "Mathematician (Researcher)", "Proves new results and develops new theory."
            elif mode == "theory":
                return "Cryptographic Analyst", "Uses number theory to design and break codes."
            else:
                return "Operations Research Analyst", "Uses math models to improve how organisations operate."
        elif focus == "stats":
            if study == "phd":
                return "Biostatistician / Research Statistician", "Designs studies and analyses results in medicine and science."
            elif mode == "code":
                return "Data Scientist / Statistical Programmer", "Builds statistical models and code that learn from data."
            else:
                return "Government / Survey Statistician", "Designs surveys and measures the population and economy."
        else:  # finance
            if study == "phd":
                return "Quantitative Analyst (Quant)", "Builds mathematical models for trading and risk."
            elif mode == "code":
                return "Quantitative Developer", "Programs trading and risk systems."
            else:
                return "Actuary", "Measures financial risk for insurers and pension funds."

    elif field == "Environmental & Earth Sciences":
        focus, setting, study = a["focus"], a["setting"], a["study"]
        if focus == "climate":
            if study == "phd":
                return "Climate Scientist", "Researches how the climate works and is changing."
            elif setting == "computer":
                return "Climate / GIS Data Analyst", "Maps and analyses climate and land data."
            elif setting == "field":
                return "Meteorologist / Weather Forecaster", "Forecasts weather and warns of severe events."
            else:
                return "Air Quality Lab Analyst", "Tests air samples and monitors pollution."
        elif focus == "land":
            if study == "phd":
                return "Geoscientist (Researcher)", "Studies Earth's structure and processes."
            elif setting == "field":
                return "Field Geologist", "Surveys rocks and land for resources and hazards."
            elif setting == "lab":
                return "Soil & Rock Lab Analyst", "Tests geological samples."
            else:
                return "GIS Specialist", "Builds digital maps and spatial analyses."
        elif focus == "water":
            if study == "phd":
                return "Aquatic Ecologist (Researcher)", "Studies life in oceans, lakes and rivers."
            elif setting == "field":
                return "Hydrologist / Marine Technician", "Studies and monitors water resources."
            elif setting == "lab":
                return "Water Quality Analyst", "Tests water for safety and pollution."
            else:
                return "Hydrological Modeller", "Models rivers, floods and water supply."
        else:  # sustain
            if study == "phd":
                return "Environmental Policy Researcher", "Researches policy to protect the environment."
            elif setting == "field":
                return "Conservation Officer / Park Ranger", "Protects wildlife and natural areas."
            elif setting == "lab":
                return "Environmental Lab Analyst", "Tests soil, air and water for contamination."
            else:
                return "Sustainability Analyst", "Helps organisations cut waste and emissions."

    elif field == "Hospitality, Tourism & Sports":
        focus, pace, own = a["focus"], a["pace"], a["own"]
        if focus == "food":
            if own == "own":
                return "Restaurant Owner / Caterer", "Runs their own food business."
            elif pace == "fast":
                return "Chef", "Prepares food in busy professional kitchens."
            else:
                return "Pastry Chef / Baker", "Creates breads, desserts and baked goods."
        elif focus == "hotel":
            if own == "own":
                return "Boutique Hotel / B&B Owner", "Runs their own place to stay."
            elif pace == "fast":
                return "Hotel Operations Manager", "Keeps a busy hotel running day and night."
            else:
                return "Guest Relations Manager / Concierge", "Looks after guests' needs and experience."
        elif focus == "travel":
            if own == "own":
                return "Travel Agency Owner / Tour Operator", "Runs their own travel business."
            elif pace == "fast":
                return "Tour Manager", "Leads groups on trips and handles everything on the road."
            else:
                return "Travel Consultant / Destination Planner", "Plans trips and itineraries for clients."
        else:  # sports
            if own == "own":
                return "Gym / Sports Academy Owner", "Runs their own fitness or training business."
            elif pace == "fast":
                return "Sports Coach / Personal Trainer", "Trains athletes and clients to perform."
            else:
                return "Recreation / Wellness Coordinator", "Organises fitness and recreation programmes."

    raise ValueError(f"Unknown field: {field}")

def recommend_career(field, a):
    title, description = _rules(field, a)
    labels = {q["id"]: next(o["label"] for o in q["options"] if o["value"] == a[q["id"]]) for q in QUESTIONS[field]}
    def phrase(l):  # keep "I ..." capitalised; lower-case the rest so it reads as a sentence
        return l if l.startswith(("I ", "I'")) else l[0].lower() + l[1:]
    parts = [phrase(l) for l in labels.values() if l not in ("Yes", "No", "Not really")]
    why = "Based on your answers: " + "; ".join(parts) + "."
    return {"title": title, "description": description, "why": why}
