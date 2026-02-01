import json
import random
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    entries = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if "page" in entry and "text" in entry and "label" in entry:
                    entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries

def build_page_groups(entries: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    groups = defaultdict(list)
    for entry in entries:
        page = entry["page"]
        groups[page].append(entry)
    return dict(groups)

FOOTER_INTROS = [
    "See also", "See", "See further", "Cf.", "Cf", "Compare", "See also",
    "References", "Reference", "As cited in", "Quoted in", "Mentioned in",
    "Discussed in", "Elaborated in", "For further reading", "Primary source",
    "Secondary source", "Based on", "Adapted from", "Originally from",
    "Cross-reference to", "Related in", "Background in", "Detailed treatment in"
]

AUTHOR_NAMES = [
    "Miller", "Adams", "Smith", "Johnson", "Brown", "Taylor", "Wilson",
    "Petersen", "Larsen", "Olsen", "Kragh", "Andersen", "Jensen", "Nielsen",
    "Hansen", "Christensen", "Rasmussen", "Jørgensen", "Madsen", "Thomsen",
    "Schmidt", "Müller", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
    "Schulz", "Hoffmann", "Schäfer", "Koch", "Bauer", "Richter", "Klein",
    "Wolf", "Schröder", "Neumann", "Schwarz", "Zimmermann", "Braun",
    "Hofmann", "Hartmann", "Lange", "Schmitt", "Werner", "Schmid", "Winkler",
    "Dupont", "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard",
    "Petit", "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre",
    "Garcia", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Perez", "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Gomez",
    "Diaz", "Reyes", "Cruz", "Morales", "Jimenez", "Ruiz", "Gutierrez"
]

BOOK_TITLES = [
    "Military Education", "European Academies", "Officer Training",
    "War Colleges 1790–1940", "Cadet Schools", "Military Pedagogy in Scandinavia",
    "Life at the Academy", "Militæruddannelse i Norden", "Kadetliv 1800–1900",
    "The Making of Officers", "European Military Tradition", "Army Education Systems",
    "Naval Academy History", "Defense Studies", "Military Institutions",
    "Officer Corps Development", "Academy Life and Culture", "War College Reform",
    "Professional Military Education", "The Officer Class", "Military Training Methods",
    "Scandinavian Defense", "Nordic Military History", "European Officer Training",
    "Cadet Life and Discipline", "Military Schools of Europe", "Officer Education Reform",
    "The Academy System", "Military Pedagogy", "Defense Education",
    "Training the Military Elite", "Academic Military Tradition", "Officer Preparation"
]

JOURNAL_NAMES = [
    "Nordic Defence Review", "European Military Journal", "Forsvarsakademiet Årbog",
    "Military History Quarterly", "Journal of Military Education", "War Studies Review",
    "Defense and Security Analysis", "Armed Forces & Society", "Journal of Strategic Studies",
    "Militærhistorisk Tidsskrift", "Scandinavian Military Review", "International Security",
    "Nordic Journal of Military Studies", "European Security Review", "Military Affairs",
    "Journal of Military History", "War in History", "Defense Studies Quarterly"
]

REFERENCE_TEMPLATES = [
    lambda: f"{pick_author()}, p. {{}}",
    lambda: f"{pick_author()}, {pick_book()}, vol. {random.randint(1,3)}, p. {{}}",
    lambda: f"{pick_author()} {random.randint(2010,2023)}, pp. {{}}",
    lambda: f"{pick_two_authors()}, {pick_book()}, page {{}}",
    lambda: f"{pick_journal()}, issue {{}}, p. {{}}",
    lambda: f"{pick_author()}, {pick_book()}, s. {{}}",
    lambda: f"{pick_author()}, {pick_book()}, {{}}",
    lambda: f"{pick_two_authors()}, {pick_book()}, {{}}",
    lambda: f"{pick_author()}, {pick_book()}, p. {{}}",
    lambda: f"{pick_author()}, {pick_book()}, {{}}",
    lambda: f"{pick_book()}, vol. {{}}, p. {{}}",
    lambda: f"{pick_author_initial()}. {pick_author()}, {pick_book()}, s. {{}}",
    lambda: f"{pick_author_initial()}. {pick_author()}, {pick_book()}, {{}}",
    lambda: f"{pick_journal()} {{}}, {{}}",
]

def pick_author() -> str:
    return random.choice(AUTHOR_NAMES)

def pick_two_authors() -> str:
    a1 = random.choice(AUTHOR_NAMES)
    a2 = random.choice(AUTHOR_NAMES)
    while a2 == a1:
        a2 = random.choice(AUTHOR_NAMES)
    return f"{a1} & {a2}"

def pick_author_initial() -> str:
    return random.choice("ABCDEFGHJKLMNOPRSTW")

def pick_book() -> str:
    return random.choice(BOOK_TITLES)

def pick_journal() -> str:
    return random.choice(JOURNAL_NAMES)

def pick_random_footer_text(next_page: int) -> str:
    formats = [
        lambda: f"{random.choice(FOOTER_INTROS)} s. {next_page}.",
        lambda: format_reference_with_page(random.choice(REFERENCE_TEMPLATES)(), next_page, random.choice(FOOTER_INTROS)),
        lambda: format_reference_with_page_and_column(random.choice(REFERENCE_TEMPLATES)(), next_page, random.choice(FOOTER_INTROS)),
        lambda: f"Jf. {format_reference_with_page(random.choice(REFERENCE_TEMPLATES)(), next_page, None)}.",
        lambda: f"Omtalt i {format_reference_with_page(random.choice(REFERENCE_TEMPLATES)(), next_page, None)}.",
        lambda: f"{random.choice(FOOTER_INTROS)} {next_page}, {random.randint(55,145)}–{random.randint(146,320)}.",
        lambda: f"Primærkilde: {format_reference_with_page(random.choice(REFERENCE_TEMPLATES)(), next_page, None)}.",
    ]
    chosen_format = random.choice(formats)
    return chosen_format()

def format_reference_with_page(template: str, page: int, intro: str) -> str:
    placeholder_count = template.count('{}')
    if placeholder_count == 1:
        formatted = template.format(page)
    elif placeholder_count == 2:
        formatted = template.format(random.randint(1, 12), page)
    else:
        formatted = template.format(*([page] * placeholder_count))
    if intro:
        return f"{intro} {formatted}."
    return formatted

def format_reference_with_page_and_column(template: str, page: int, intro: str) -> str:
    placeholder_count = template.count('{}')
    if placeholder_count == 1:
        formatted = template.format(page)
    elif placeholder_count == 2:
        formatted = template.format(random.randint(1, 12), page)
    else:
        formatted = template.format(*([page] * placeholder_count))
    return f"{intro} {formatted}, sp. {random.randint(1,4)}."

def create_footer_entry(page: int, text: str) -> Dict[str, Any]:
    return {
        "label": "footer",
        "page": page - 1,
        "text": text
    }

def insert_footers_between_pages(groups: Dict[int, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if not groups:
        return []
    sorted_pages = sorted(groups.keys())
    result = []
    for i, current_page in enumerate(sorted_pages):
        current_items = groups[current_page]
        result.extend(current_items)
        if i < len(sorted_pages) - 1:
            next_page = sorted_pages[i + 1]
            if next_page == current_page + 1:
                num_footers = decide_number_of_footers()
                new_footers = generate_footers_for_boundary(next_page, num_footers)
                result.extend(new_footers)
    return result

def save_jsonl(entries: List[Dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for entry in entries:
            json_line = json.dumps(entry, ensure_ascii=False)
            f.write(json_line + "\n")

def decide_number_of_footers() -> int:
    r = random.random()
    if r < 0.30:
        return 0
    elif r < 0.75:
        return 1
    else:
        return 2

def generate_footers_for_boundary(next_page: int, count: int) -> List[Dict[str, Any]]:
    footers = []
    for _ in range(count):
        text = pick_random_footer_text(next_page)
        footers.append(create_footer_entry(next_page, text))
    return footers

def get_seed_from_input(path: Path) -> int:
    import time
    content = path.read_bytes()
    h = hashlib.sha256(content)
    h.update(str(time.time()).encode())
    return int(h.hexdigest(), 16) % (2**32)

def main():
    input_path = Path("input.json")
    output_path = Path("output_footers.json")
    random.seed(get_seed_from_input(input_path))
    if not input_path.is_file():
        print("input.json not found")
        return
    entries = load_jsonl(input_path)
    if not entries:
        print("No valid entries loaded")
        return
    page_groups = build_page_groups(entries)
    processed = insert_footers_between_pages(page_groups)
    save_jsonl(processed, output_path)
    print(f"Wrote {len(processed)} lines to {output_path}")
    print(f"Original entries: {len(entries)}")
    print(f"Added footers:   {len(processed) - len(entries)}")

if __name__ == "__main__":
    main()
