import os
import json

MEDIA_PATH = "deskpets/media"
OUTPUT_JSON = "deskpets/pets_data.json"

# Par défaut, valeurs pour les states connues
DEFAULT_SETTINGS = {
    "idle":       {"hold": 8, "movement_speed": 0, "speed_animation": 0.5},
    "lie":        {"hold": 8, "movement_speed": 0, "speed_animation": 1.0},
    "swipe":      {"hold": 8, "movement_speed": 0, "speed_animation": 1.0},
    "walk":       {"hold": 24, "movement_speed": 3, "speed_animation": 1.0},
    "walk_fast":  {"hold": 40, "movement_speed": 5, "speed_animation": 1.5},
    "run":        {"hold": 56, "movement_speed": 7, "speed_animation": 2.0},
    "with_ball":  {"hold": 16, "movement_speed": 0, "speed_animation": 1.0},
}

def scan_media(base_path=MEDIA_PATH):
    pets = {}
    for species in os.listdir(base_path):
        species_path = os.path.join(base_path, species)
        if not os.path.isdir(species_path) or species in ("backgrounds", "extraIcons", "icon"):
            continue

        pets[species] = {"colors": set(), "states": {}, "defaults": DEFAULT_SETTINGS.copy()}

        for file in os.listdir(species_path):
            if not file.lower().endswith(".gif"):
                continue

            name, _ = os.path.splitext(file)
            parts = name.split("_")
            if len(parts) < 2:
                continue  # nom invalide
            color = parts[0]
            state = "_".join(parts[1:-1])  # retirer le "_8fps" final

            pets[species]["colors"].add(color)

            # uniformisation du chemin relatif au dossier media
            path = os.path.relpath(os.path.join(species_path, file), start=MEDIA_PATH).replace("\\", "/")
            pets[species]["states"].setdefault(color, {})[state] = f"media/{path}"

            # si la state n'est pas dans defaults, la créer avec 0
            if state not in pets[species]["defaults"]:
                pets[species]["defaults"][state] = {"hold": 8, "movement_speed": 0, "speed_animation": 1.0}

        pets[species]["colors"] = list(pets[species]["colors"])

    return pets

if __name__ == "__main__":
    data = scan_media()
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"JSON généré dans {OUTPUT_JSON}")
