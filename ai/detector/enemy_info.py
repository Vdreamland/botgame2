from src.helper import MONSTERS, GUARDIAN, WEAPONS, ARMOR, AGENT_BASE

class EnemyInfoDetector:
    def __init__(self, view_data):
        self.view_data = view_data or {}
        self.visible_agents = self.view_data.get("visibleAgents") or self.view_data.get("otherAgents") or []
        self.visible_monsters = self.view_data.get("visibleMonsters") or self.view_data.get("monsters") or []

    def get_alive_agents(self):
        alive = []
        for agent in self.visible_agents:
            if isinstance(agent, dict) and not agent.get("isDead", False):
                alive.append(agent)
        return alive

    def get_alive_monsters(self):
        alive = []
        for monster in self.visible_monsters:
            if isinstance(monster, dict) and not monster.get("isDead", False):
                alive.append(monster)
        return alive

    def get_enemies_by_layer(self, region_distances):
        region_id_to_name = {
            self.view_data.get("currentRegion", {}).get("id"): self.view_data.get("currentRegion", {}).get("name", "Unknown")
        }
        for r in self.view_data.get("visibleRegions", []):
            r_id = r.get("id")
            r_name = r.get("name")
            if r_id and r_name:
                region_id_to_name[r_id] = r_name

        enemies_by_layer = {}

        for agent in self.get_alive_agents():
            r_id = agent.get("regionId")
            dist = region_distances.get(r_id)
            if dist is not None:
                if dist not in enemies_by_layer:
                    enemies_by_layer[dist] = {}
                r_name = region_id_to_name.get(r_id, "Unknown")
                if r_name not in enemies_by_layer[dist]:
                    enemies_by_layer[dist][r_name] = []
                
                stats = self.resolve_agent_stats(agent)
                display = f"- {agent.get('name', 'Unknown')} [Agent] (HP {agent.get('hp', 0)}/{agent.get('maxHp', 0)}, ATK: {stats['atk']}, DEF: {stats['def']}, Weapon: {stats['weapon_name']}, Armour: {stats['armor_name']})"
                enemies_by_layer[dist][r_name].append(display)

        for monster in self.get_alive_monsters():
            r_id = monster.get("regionId")
            dist = region_distances.get(r_id)
            if dist is not None:
                if dist not in enemies_by_layer:
                    enemies_by_layer[dist] = {}
                r_name = region_id_to_name.get(r_id, "Unknown")
                if r_name not in enemies_by_layer[dist]:
                    enemies_by_layer[dist][r_name] = []
                
                m_type = monster.get("type", "").lower() or monster.get("name", "").lower()
                stats = self.resolve_monster_stats(m_type)
                monster_display_name = monster.get("name", "Unknown")
                m_label = "Guardian" if "guardian" in m_type else "Monster"
                
                display = f"- {monster_display_name} [{m_label}] (HP {monster.get('hp', 0)}/{monster.get('maxHp', 0)}, ATK: {stats['atk']}, DEF: {stats['def']})"
                enemies_by_layer[dist][r_name].append(display)

        sorted_layers = {}
        for dist, regions_map in enemies_by_layer.items():
            sorted_layers[dist] = {}
            for r_name in sorted(regions_map.keys()):
                sorted_layers[dist][r_name] = sorted(regions_map[r_name])
        return sorted_layers

    def resolve_agent_stats(self, agent_data):
        weapon = agent_data.get("weapon")
        weapon_name = ""
        if isinstance(weapon, dict):
            weapon_name = weapon.get("name", "")
        elif isinstance(weapon, str):
            weapon_name = weapon

        armor = agent_data.get("armor")
        armor_name = ""
        if isinstance(armor, dict):
            armor_name = armor.get("name", "")
        elif isinstance(armor, str):
            armor_name = armor

        base_atk = AGENT_BASE.get("atk", 25)
        base_def = AGENT_BASE.get("def", 5)

        weapon_bonus = 0
        if weapon_name:
            weapon_lower = weapon_name.lower()
            for w_key, w_data in WEAPONS.items():
                if w_key in weapon_lower:
                    weapon_bonus = w_data.get("atk_bonus", 0)
                    break

        armor_bonus = 0
        if armor_name:
            armor_lower = armor_name.lower()
            for a_key, a_data in ARMOR.items():
                if a_key in armor_lower:
                    armor_bonus = a_data.get("def_bonus", 0)
                    break

        return {
            "atk": base_atk + weapon_bonus,
            "def": base_def + armor_bonus,
            "weapon_name": weapon_name or "Fist",
            "armor_name": armor_name or "None"
        }

    def resolve_monster_stats(self, monster_type):
        m_type = str(monster_type).lower()
        if "guardian" in m_type:
            return {
                "atk": GUARDIAN.get("atk", 12),
                "def": GUARDIAN.get("def", 120),
                "type": "guardian"
            }
        
        for m_key, m_data in MONSTERS.items():
            if m_key in m_type:
                return {
                    "atk": m_data.get("atk", 10),
                    "def": m_data.get("def", 0),
                    "type": m_key
                }
        return {
            "atk": 10,
            "def": 0,
            "type": "unknown"
        }