def score_recovery_actions(hp, ep, inventory, is_safe):
    # Pengelompokan item consumable medis dan energi secara dinamis (DRY)
    medkits = []
    small_healers = []
    ep_items = []

    for item in inventory:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        item_type = item.get("typeId") or item.get("name") or item_id
        if not item_type:
            continue
        name_clean = str(item_type).lower()

        if "medkit" in name_clean:
            medkits.append(item)
        elif "bandage" in name_clean or "food" in name_clean:
            small_healers.append(item)
        elif "drink" in name_clean or "potion" in name_clean:
            ep_items.append(item)

    # Pemilihan item HP secara proporsional sesuai kebutuhan defisit HP
    hp_item = None
    if medkits or small_healers:
        if hp < 50:
            # Utamakan Medkit untuk luka berat
            hp_item = medkits[0] if medkits else small_healers[0]
        else:
            # Utamakan Bandage/Food untuk menghemat Medkit jika luka ringan
            hp_item = small_healers[0] if small_healers else medkits[0]

    ep_item = ep_items[0] if ep_items else None

    # 1. Keputusan Pemulihan HP (Skor Sangat Tinggi saat HP Sekarat)
    if hp_item:
        score = 40 + (100 - hp)
        if hp < 20:
            score += 220  # Prioritas mutlak (Skor > 300) agar pulih terlebih dahulu
        elif hp < 40:
            score += 180  # Prioritas tinggi (Skor > 240) mengalahkan Fleeing/Combat biasa
        
        return {
            "score": score,
            "action": {"action": "use_item", "item": hp_item}
        }

    # 2. Keputusan Pemulihan EP menggunakan Item
    if ep <= 2 and ep_item:
        score = 85 + (10 - ep) * 5
        return {
            "score": score,
            "action": {"action": "use_item", "item": ep_item}
        }

    # 3. Keputusan Istirahat (Rest) Tanpa Item di Wilayah Aman (Mencegah EP Exhaustion)
    if is_safe:
        if ep <= 2:
            return {
                "score": 125,  # Skor tinggi agar bot istirahat saat EP kritis
                "action": {"action": "rest"}
            }
        elif ep == 3:
            return {
                "score": 60,
                "action": {"action": "rest"}
            }
        elif ep >= 4 and ep <= 7:
            return {
                "score": 50,
                "action": {"action": "rest"}
            }

    return {
        "score": 0,
        "action": None
    }