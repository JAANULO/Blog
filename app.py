from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DATA_FILE = 'data.json'


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"o_mnie": "", "seriale": [], "miniseriale": []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Funkcja pomocnicza do sortowania
def sort_items(items):
    # Sortuje od najnowszej daty do najstarszej
    # Jeśli brak daty, przyjmuje rok 1900
    return sorted(items, key=lambda x: x.get('data', '1900-01-01'), reverse=True)


@app.route('/')
def index():
    """Serwuje główną stronę"""
    return send_from_directory('.', 'index.html')


@app.route('/admin.html')
def admin_page():
    """Serwuje stronę admin.html"""
    return send_from_directory('.', 'admin.html')


@app.route('/media/<path:filename>')
def media(filename):
    """Serwuje pliki z folderu media/"""
    return send_from_directory('media', filename)


@app.route('/favicon.ico')
def favicon():
    """Serwuje favicon"""
    return send_from_directory('media', 'favicon.png')


@app.route('/api/data', methods=['GET'])
def get_data():
    data = load_data()

    # Inicjalizuj pole 'favorite' dla wszystkich serii jeśli brakuje
    for serial in data.get('seriale', []):
        if 'favorite' not in serial:
            serial['favorite'] = False
    for serial in data.get('miniseriale', []):
        if 'favorite' not in serial:
            serial['favorite'] = False

    # Sortujemy listy przed wysłaniem na stronę
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
        "data": req.get('data'),  # <-- Zapisujemy datę
        "sezony": []
    }

    liczba_sezonow = int(req.get('liczba_sezonow', 1))
    for i in range(1, liczba_sezonow + 1):
        nowy_serial['sezony'].append({"nr": i, "status": "not-watched"})

    if kategoria in data:
        data[kategoria].append(nowy_serial)  # Dodajemy na koniec, sortowanie załatwi get_data
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

    # Szukamy serialu
    for serial in data[kategoria]:
        if serial['tytul'] == tytul:
            # Szukamy sezonu
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

    # Szukamy i usuwamy serial
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

    # Szukamy serial i przełączamy ulubione
    for serial in data[kategoria]:
        if serial['tytul'] == tytul:
            if 'favorite' not in serial:
                serial['favorite'] = False
            serial['favorite'] = not serial['favorite']
            save_data(data)
            return jsonify({"message": "Status ulubionych zmieniony!", "favorite": serial['favorite']})

    return jsonify({"message": "Błąd: serial nie znaleziony"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)