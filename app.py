from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
import shutil  # <--- Nowy import do kopiowania plików
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# --- KONFIGURACJA ŚCIEŻEK ---
# Ścieżka do trwałego wolumenu w Coolify
VOLUME_PATH = '/app/data'
# Plik, z którego korzysta aplikacja (wewnątrz wolumenu)
DATA_FILE = os.path.join(VOLUME_PATH, 'data.json')
# Plik źródłowy z repozytorium (backup/startowy)
REPO_FILE = 'data.json'


def initialize_storage():
    """
    Sprawdza, czy w wolumenie istnieje plik danych.
    Jeśli nie - kopiuje go z repozytorium.
    """
    # 1. Upewnij się, że folder wolumenu istnieje
    if not os.path.exists(VOLUME_PATH):
        try:
            os.makedirs(VOLUME_PATH)
            print(f"--> Utworzono folder: {VOLUME_PATH}")
        except OSError as e:
            print(f"--> Błąd tworzenia folderu: {e}")

    # 2. Sprawdź czy plik bazy istnieje w wolumenie
    if not os.path.exists(DATA_FILE):
        print(f"--> Brak pliku w {DATA_FILE}. Próba skopiowania z repozytorium...")

        if os.path.exists(REPO_FILE):
            try:
                shutil.copy(REPO_FILE, DATA_FILE)
                print("--> Sukces! Skopiowano dane startowe z GitHuba.")
            except Exception as e:
                print(f"--> Błąd kopiowania: {e}")
        else:
            print("--> Brak pliku w repozytorium. Tworzę pustą bazę.")
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({"o_mnie": "", "seriale": [], "miniseriale": []}, f)
    else:
        print("--> Plik danych już istnieje w wolumenie. Pomijam kopiowanie.")


def load_data():
    # Uruchom inicjalizację przy każdej próbie odczytu (dla bezpieczeństwa)
    initialize_storage()

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"o_mnie": "", "seriale": [], "miniseriale": []}


def save_data(data):
    # Zapis zawsze idzie do trwałego wolumenu
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Funkcja pomocnicza do sortowania
def sort_items(items):
    return sorted(items, key=lambda x: x.get('data', '1900-01-01'), reverse=True)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/admin.html')
def admin_page():
    return send_from_directory('.', 'admin.html')


@app.route('/media/<path:filename>')
def media(filename):
    return send_from_directory('media', filename)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('media', 'favicon.png')


@app.route('/api/data', methods=['GET'])
def get_data():
    data = load_data()

    for serial in data.get('seriale', []):
        if 'favorite' not in serial:
            serial['favorite'] = False
    for serial in data.get('miniseriale', []):
        if 'favorite' not in serial:
            serial['favorite'] = False

    if 'seriale' in data:
        data['seriale'] = sort_items(data['seriale'])
    if 'miniseriale' in data:
        data['miniseriale'] = sort_items(data['miniseriale'])

    return jsonify(data)


@app.route('/api/update-text', methods=['POST'])
def update_text():
    new_text = request.json.get('text')
    data = load_data()
    data['o_mnie'] = new_text
    save_data(data)
    return jsonify({"message": "Zapisano tekst!"})


@app.route('/api/add-series', methods=['POST'])
def add_series():
    req = request.json
    data = load_data()

    kategoria = req.get('kategoria', 'seriale')

    nowy_serial = {
        "tytul": req.get('tytul'),
        "img": req.get('img'),
        "data": req.get('data'),
        "sezony": []
    }

    liczba_sezonow = int(req.get('liczba_sezonow', 1))
    for i in range(1, liczba_sezonow + 1):
        nowy_serial['sezony'].append({"nr": i, "status": "not-watched"})

    if kategoria in data:
        data[kategoria].append(nowy_serial)
        save_data(data)
        return jsonify({"message": f"Dodano do {kategoria}!"})
    else:
        return jsonify({"message": "Błąd: nieznana kategoria"}), 400


@app.route('/api/update-season', methods=['POST'])
def update_season():
    req = request.json
    data = load_data()

    kategoria = req.get('kategoria', 'seriale')
    tytul = req.get('tytul')
    numer_sezonu = int(req.get('numer_sezonu'))
    nowy_status = req.get('status')

    if kategoria not in data:
        return jsonify({"message": "Błąd: nieznana kategoria"}), 400

    for serial in data[kategoria]:
        if serial['tytul'] == tytul:
            for sezon in serial['sezony']:
                if sezon['nr'] == numer_sezonu:
                    sezon['status'] = nowy_status
                    save_data(data)
                    return jsonify({"message": "Sezon zaktualizowany!"})
            return jsonify({"message": "Błąd: sezon nie znaleziony"}), 404

    return jsonify({"message": "Błąd: serial nie znaleziony"}), 404


@app.route('/api/delete-series', methods=['POST'])
def delete_series():
    req = request.json
    data = load_data()

    kategoria = req.get('kategoria', 'seriale')
    tytul = req.get('tytul')

    if kategoria not in data:
        return jsonify({"message": "Błąd: nieznana kategoria"}), 400

    for i, serial in enumerate(data[kategoria]):
        if serial['tytul'] == tytul:
            data[kategoria].pop(i)
            save_data(data)
            return jsonify({"message": "Serial usunięty!"})

    return jsonify({"message": "Błąd: serial nie znaleziony"}), 404


@app.route('/api/toggle-favorite', methods=['POST'])
def toggle_favorite():
    req = request.json
    data = load_data()

    kategoria = req.get('kategoria', 'seriale')
    tytul = req.get('tytul')

    if kategoria not in data:
        return jsonify({"message": "Błąd: nieznana kategoria"}), 400

    for serial in data[kategoria]:
        if serial['tytul'] == tytul:
            if 'favorite' not in serial:
                serial['favorite'] = False
            serial['favorite'] = not serial['favorite']
            save_data(data)
            return jsonify({"message": "Status ulubionych zmieniony!", "favorite": serial['favorite']})

    return jsonify({"message": "Błąd: serial nie znaleziony"}), 404


if __name__ == "__main__":
    # Upewniamy się, że storage jest gotowy przy starcie
    initialize_storage()
    app.run(debug=True, port=5000, host='0.0.0.0')