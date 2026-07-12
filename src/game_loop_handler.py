import asyncio
from src.log.log_connections import log_info, log_warning, log_error
from src.log.logs_games import GameLogSender
from ai.memory import AgentMemory
from ai.detector.agent_info import AgentInfoDetector
from ai.detector.enemy_info import EnemyInfoDetector
from ai.detector.zone_detector import ZoneDetector
from ai.detector.deadzone_detector import DeadZoneDetector
from ai.detector.ground_item_detector import GroundItemDetector
from ai.detector.facility_detector import FacilityDetector
from ai.decision_maker import get_decision

async def run_game_loop(ws, bot_name, initial_state):
    state = initial_state
    memory = AgentMemory()
    log_sender = GameLogSender(bot_name)
    game_id = None
    agent_id = None

    try:
        while True:
            msg = await ws.recv()
            if not msg:
                break

            m_type = msg.get("type")

            if m_type == "queued":
                if state != "queued":
                    log_info(f"[{bot_name}] Joined matchmaking queue. Waiting for slot...")
                    state = "queued"

            elif m_type == "assigned":
                game_id = msg.get("gameId")
                agent_id = msg.get("agentId")
                log_info(f"[{bot_name}] Matchmaking successful! Assigned Game ID: {game_id}, Agent ID: {agent_id}")
                state = "playing"

            elif m_type == "not_selected":
                reason = msg.get("reason", "No slots available")
                log_warning(f"[{bot_name}] Matchmaking failed: {reason}. Retrying next epoch...")
                state = "waiting"

            elif m_type == "error":
                err_msg = msg.get("message", "Unknown backend error")
                log_error(f"[{bot_name}] Server reported error: {err_msg}")
                state = "error"
                break

            elif m_type == "waiting":
                wait_secs = msg.get("seconds", 5)
                log_info(f"[{bot_name}] Waiting {wait_secs} seconds for room allocation...")

            elif m_type == "game_ended":
                res = msg.get("result", {}) or {}
                winner = res.get("winner", "None")
                is_win = (winner == agent_id)
                log_info(f"[{bot_name}] Game {game_id} finished. Winner: {winner}. Win: {is_win}")
                state = "ended"
                break

            elif m_type in ["agent_view", "turn_advanced"]:
                view_data = msg.get("data", {}) or {}
                self_data = view_data.get("self", {}) or {}

                if self_data.get("isDead", False) or self_data.get("hp", 0) <= 0:
                    log_warning(f"[{bot_name}] Agent is dead. Awaiting game cleanup...")
                    continue

                agent_info = AgentInfoDetector(view_data)
                enemy_detector = EnemyInfoDetector(view_data)
                zone_detector = ZoneDetector(view_data)
                deadzone_detector = DeadZoneDetector(view_data)
                ground_detector = GroundItemDetector(view_data)
                facility_detector = FacilityDetector(view_data)

                await log_sender.send_agent_info(
                    agent_info,
                    enemy_detector,
                    zone_detector,
                    deadzone_detector,
                    ground_detector,
                    facility_detector
                )

                decision = get_decision(
                    view_data,
                    agent_info,
                    enemy_detector,
                    deadzone_detector,
                    ground_detector,
                    memory
                )

                if decision:
                    await ws.send(decision)

    except Exception as e:
        log_error(f"[{bot_name}] Exception in gameplay loop: {e}")