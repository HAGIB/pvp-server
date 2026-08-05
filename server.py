import asyncio
import websockets
import json
import os
import time
import math

# Хранилище игроков и боёв
waiting_queue = []  # (websocket, user_id, skin)
active_battles = {}  # battle_id -> {player1, player2, state}

# Настройки
TICK_RATE = 1/30  # 30 тиков в секунду
ARENA_WIDTH = 720
ARENA_MARGIN = 50
PLAYER1_Y = 1177  # снизу
PLAYER2_Y = 180   # сверху
BULLET_SPEED = 600

class BattleState:
    def __init__(self, p1_ws, p1_id, p1_skin, p2_ws, p2_id, p2_skin):
        self.p1_ws = p1_ws
        self.p1_id = p1_id
        self.p1_skin = p1_skin
        self.p1_x = ARENA_WIDTH / 2
        self.p1_hp = 900
        self.p1_max_hp = 900
        self.p1_input = 0  # -1 left, 0 none, 1 right
        self.p1_bullets = []
        self.p1_fire_timer = 0
        self.p1_fire_rate = 0.15
        
        self.p2_ws = p2_ws
        self.p2_id = p2_id
        self.p2_skin = p2_skin
        self.p2_x = ARENA_WIDTH / 2
        self.p2_hp = 900
        self.p2_max_hp = 900
        self.p2_input = 0
        self.p2_bullets = []
        self.p2_fire_timer = 0
        self.p2_fire_rate = 0.15
        
        self.battle_id = f"battle_{p1_id}_{p2_id}"
        self.started = False
        self.ended = False
        self.countdown = 5.0
        
        # Применяем статы скинов
        self._apply_skin_stats()
    
    def _apply_skin_stats(self):
        skins = {
            "DEFAULT": {"hp": 900, "speed": 400, "fire_rate": 0.15},
            "OLD BLAZER": {"hp": 1350, "speed": 360, "fire_rate": 0.15},
            "AQUAMARINE": {"hp": 1350, "speed": 400, "fire_rate": 0.12},
            "HELICOPTER": {"hp": 1650, "speed": 420, "fire_rate": 0.07},
            "ORION-X": {"hp": 1500, "speed": 400, "fire_rate": 0.22},
            "SPECTER MK-12": {"hp": 1420, "speed": 340, "fire_rate": 0.6},
        }
        
        s1 = skins.get(self.p1_skin, skins["DEFAULT"])
        s2 = skins.get(self.p2_skin, skins["DEFAULT"])
        
        self.p1_hp = s1["hp"]
        self.p1_max_hp = s1["hp"]
        self.p1_speed = s1["speed"]
        self.p1_fire_rate = s1["fire_rate"]
        
        self.p2_hp = s2["hp"]
        self.p2_max_hp = s2["hp"]
        self.p2_speed = s2["speed"]
        self.p2_fire_rate = s2["fire_rate"]
    
    def update(self, dt):
        if not self.started or self.ended:
            return
        
        # Двигаем игроков
        self.p1_x += self.p1_input * self.p1_speed * dt
        self.p1_x = max(ARENA_MARGIN, min(ARENA_WIDTH - ARENA_MARGIN, self.p1_x))
        
        self.p2_x += self.p2_input * self.p2_speed * dt
        self.p2_x = max(ARENA_MARGIN, min(ARENA_WIDTH - ARENA_MARGIN, self.p2_x))
        
        # Стрельба игрока 1
        self.p1_fire_timer += dt
        if self.p1_fire_timer >= self.p1_fire_rate:
            self.p1_fire_timer = 0
            self.p1_bullets.append({
                "x": self.p1_x,
                "y": PLAYER1_Y - 40,
                "vy": -BULLET_SPEED,
                "damage": 25,
                "from_p1": True
            })
        
        # Стрельба игрока 2
        self.p2_fire_timer += dt
        if self.p2_fire_timer >= self.p2_fire_rate:
            self.p2_fire_timer = 0
            self.p2_bullets.append({
                "x": self.p2_x,
                "y": PLAYER2_Y + 40,
                "vy": BULLET_SPEED,
                "damage": 25,
                "from_p1": False
            })
        
        # Двигаем пули
        for bullet in self.p1_bullets[:]:
            bullet["y"] += bullet["vy"] * dt
            
            # Проверяем попадание в игрока 2
            if abs(bullet["x"] - self.p2_x) < 50 and abs(bullet["y"] - PLAYER2_Y) < 50:
                self.p2_hp -= bullet["damage"]
                self.p1_bullets.remove(bullet)
                if self.p2_hp <= 0:
                    self.ended = True
            
            # Удаляем вышедшие за экран
            elif bullet["y"] < -50 or bullet["y"] > 1400:
                self.p1_bullets.remove(bullet)
        
        for bullet in self.p2_bullets[:]:
            bullet["y"] += bullet["vy"] * dt
            
            if abs(bullet["x"] - self.p1_x) < 50 and abs(bullet["y"] - PLAYER1_Y) < 50:
                self.p1_hp -= bullet["damage"]
                self.p2_bullets.remove(bullet)
                if self.p1_hp <= 0:
                    self.ended = True
            
            elif bullet["y"] < -50 or bullet["y"] > 1400:
                self.p2_bullets.remove(bullet)
    
    def get_state_for_p1(self):
        """Состояние которое видит игрок 1"""
import asyncio
import websockets
import json
import os
import time
import math
import traceback

# Хранилище игроков и боёв
waiting_queue = []  # (websocket, user_id, skin)
active_battles = {}  # battle_id -> BattleState

# Настройки
TICK_RATE = 1/30  # 30 тиков в секунду
ARENA_WIDTH = 720
ARENA_MARGIN = 50
PLAYER1_Y = 1177  # снизу
PLAYER2_Y = 180   # сверху
BULLET_SPEED = 600

class BattleState:
    def __init__(self, p1_ws, p1_id, p1_skin, p2_ws, p2_id, p2_skin):
        self.p1_ws = p1_ws
        self.p1_id = p1_id
        self.p1_skin = p1_skin
        self.p1_x = ARENA_WIDTH / 2
        self.p1_hp = 900
        self.p1_max_hp = 900
        self.p1_input = 0
        self.p1_bullets = []
        self.p1_fire_timer = 0
        self.p1_fire_rate = 0.15
        self.p1_speed = 400
        
        self.p2_ws = p2_ws
        self.p2_id = p2_id
        self.p2_skin = p2_skin
        self.p2_x = ARENA_WIDTH / 2
        self.p2_hp = 900
        self.p2_max_hp = 900
        self.p2_input = 0
        self.p2_bullets = []
        self.p2_fire_timer = 0
        self.p2_fire_rate = 0.15
        self.p2_speed = 400
        
        self.battle_id = f"battle_{p1_id}_{p2_id}"
        self.started = False
        self.ended = False
        self.countdown = 5.0
        
        self._apply_skin_stats()
    
    def _apply_skin_stats(self):
        skins = {
            "DEFAULT": {"hp": 900, "speed": 400, "fire_rate": 0.15},
            "OLD BLAZER": {"hp": 1350, "speed": 360, "fire_rate": 0.15},
            "AQUAMARINE": {"hp": 1350, "speed": 400, "fire_rate": 0.12},
            "HELICOPTER": {"hp": 1650, "speed": 420, "fire_rate": 0.07},
            "ORION-X": {"hp": 1500, "speed": 400, "fire_rate": 0.22},
            "SPECTER MK-12": {"hp": 1420, "speed": 340, "fire_rate": 0.6},
        }
        
        s1 = skins.get(self.p1_skin, skins["DEFAULT"])
        s2 = skins.get(self.p2_skin, skins["DEFAULT"])
        
        self.p1_hp = s1["hp"]
        self.p1_max_hp = s1["hp"]
        self.p1_speed = s1["speed"]
        self.p1_fire_rate = s1["fire_rate"]
        
        self.p2_hp = s2["hp"]
        self.p2_max_hp = s2["hp"]
        self.p2_speed = s2["speed"]
        self.p2_fire_rate = s2["fire_rate"]
    
    def update(self, dt):
        if not self.started or self.ended:
            return
        
        # Двигаем игроков
        self.p1_x += self.p1_input * self.p1_speed * dt
        self.p1_x = max(ARENA_MARGIN, min(ARENA_WIDTH - ARENA_MARGIN, self.p1_x))
        
        self.p2_x += self.p2_input * self.p2_speed * dt
        self.p2_x = max(ARENA_MARGIN, min(ARENA_WIDTH - ARENA_MARGIN, self.p2_x))
        
        # Стрельба игрока 1
        self.p1_fire_timer += dt
        if self.p1_fire_timer >= self.p1_fire_rate:
            self.p1_fire_timer = 0
            self.p1_bullets.append({
                "x": self.p1_x,
                "y": PLAYER1_Y - 40,
                "vy": -BULLET_SPEED,
                "damage": 25,
                "from_p1": True
            })
        
        # Стрельба игрока 2
        self.p2_fire_timer += dt
        if self.p2_fire_timer >= self.p2_fire_rate:
            self.p2_fire_timer = 0
            self.p2_bullets.append({
                "x": self.p2_x,
                "y": PLAYER2_Y + 40,
                "vy": BULLET_SPEED,
                "damage": 25,
                "from_p1": False
            })
        
        # Двигаем пули игрока 1
        for bullet in self.p1_bullets[:]:
            bullet["y"] += bullet["vy"] * dt
            
            if abs(bullet["x"] - self.p2_x) < 50 and abs(bullet["y"] - PLAYER2_Y) < 50:
                self.p2_hp -= bullet["damage"]
                self.p1_bullets.remove(bullet)
                if self.p2_hp <= 0:
                    self.p2_hp = 0
                    self.ended = True
            elif bullet["y"] < -50 or bullet["y"] > 1400:
                self.p1_bullets.remove(bullet)
        
        # Двигаем пули игрока 2
        for bullet in self.p2_bullets[:]:
            bullet["y"] += bullet["vy"] * dt
            
            if abs(bullet["x"] - self.p1_x) < 50 and abs(bullet["y"] - PLAYER1_Y) < 50:
                self.p1_hp -= bullet["damage"]
                self.p2_bullets.remove(bullet)
                if self.p1_hp <= 0:
                    self.p1_hp = 0
                    self.ended = True
            elif bullet["y"] < -50 or bullet["y"] > 1400:
                self.p2_bullets.remove(bullet)
    
    def get_state_for_p1(self):
        return {
            "action": "game_state",
            "player": {"x": self.p1_x, "y": PLAYER1_Y, "hp": self.p1_hp, "max_hp": self.p1_max_hp},
            "opponent": {"x": self.p2_x, "y": PLAYER2_Y, "hp": self.p2_hp, "max_hp": self.p2_max_hp},
            "bullets": [
                {"x": b["x"], "y": b["y"], "from_player": b["from_p1"]}
                for b in self.p1_bullets + self.p2_bullets
            ],
            "countdown": self.countdown,
            "started": self.started,
            "ended": self.ended,
            "winner": "p1" if self.p2_hp <= 0 else ("p2" if self.p1_hp <= 0 else None)
        }
    
    def get_state_for_p2(self):
        return {
            "action": "game_state",
            "player": {"x": self.p2_x, "y": PLAYER2_Y, "hp": self.p2_hp, "max_hp": self.p2_max_hp},
            "opponent": {"x": self.p1_x, "y": PLAYER1_Y, "hp": self.p1_hp, "max_hp": self.p1_max_hp},
            "bullets": [
                {"x": b["x"], "y": b["y"], "from_player": not b["from_p1"]}
                for b in self.p1_bullets + self.p2_bullets
            ],
            "countdown": self.countdown,
            "started": self.started,
            "ended": self.ended,
            "winner": "p2" if self.p1_hp <= 0 else ("p1" if self.p2_hp <= 0 else None)
        }

async def battle_loop(battle):
    print(f"[Battle {battle.battle_id}] Starting countdown...")
    
    # Отсчёт
    while battle.countdown > 0 and not battle.ended:
        await asyncio.sleep(0.5)
        battle.countdown -= 0.5
        
        try:
            await battle.p1_ws.send(json.dumps(battle.get_state_for_p1()))
            await battle.p2_ws.send(json.dumps(battle.get_state_for_p2()))
        except Exception as e:
            print(f"[Battle {battle.battle_id}] Send error during countdown: {e}")
            battle.ended = True
            return
    
    battle.started = True
    print(f"[Battle {battle.battle_id}] FIGHT!")
    
    last_time = time.time()
    
    while not battle.ended:
        try:
            current_time = time.time()
            dt = min(current_time - last_time, 0.1)
            last_time = current_time
            
            battle.update(dt)
            
            await battle.p1_ws.send(json.dumps(battle.get_state_for_p1()))
            await battle.p2_ws.send(json.dumps(battle.get_state_for_p2()))
            
            await asyncio.sleep(TICK_RATE)
        except Exception as e:
            print(f"[Battle {battle.battle_id}] Error: {e}")
            traceback.print_exc()
            battle.ended = True
            break
    
    # Финальное состояние
    try:
        await battle.p1_ws.send(json.dumps(battle.get_state_for_p1()))
        await battle.p2_ws.send(json.dumps(battle.get_state_for_p2()))
    except:
        pass
    
    print(f"[Battle {battle.battle_id}] Ended. Winner: {'P1' if battle.p2_hp <= 0 else 'P2'}")

async def handler(websocket):
    player_id = None
    current_battle = None
    is_p1 = None
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except:
                continue
            
            action = data.get("action")
            print(f"[Server] Received: {action} from {player_id}")
            
            if action == "join_queue":
                player_id = data.get("user_id", str(id(websocket)))
                skin = data.get("skin", "DEFAULT")
                print(f"[Server] Player {player_id} joined queue with skin {skin}")
                
                if len(waiting_queue) > 0:
                    opponent_ws, opponent_id, opponent_skin = waiting_queue.pop(0)
                    print(f"[Server] Match found! {player_id} vs {opponent_id}")
                    
                    battle = BattleState(
                        websocket, player_id, skin,
                        opponent_ws, opponent_id, opponent_skin
                    )
                    active_battles[battle.battle_id] = battle
                    current_battle = battle
                    is_p1 = True
                    
                    asyncio.create_task(battle_loop(battle))
                else:
                    waiting_queue.append((websocket, player_id, skin))
                    print(f"[Server] Waiting queue size: {len(waiting_queue)}")
                    
                    await websocket.send(json.dumps({
                        "action": "waiting",
                        "position": len(waiting_queue)
                    }))
            
            elif action == "input":
                if current_battle and not current_battle.ended:
                    inp = data.get("direction", 0)
                    if is_p1:
                        current_battle.p1_input = inp
                    else:
                        current_battle.p2_input = inp
            
            elif action == "leave_queue":
                for i, (ws, pid, _) in enumerate(waiting_queue):
                    if ws == websocket:
                        waiting_queue.pop(i)
                        print(f"[Server] Player {pid} left queue")
                        break
            
            elif action == "leave_battle":
                if current_battle:
                    print(f"[Server] Player {player_id} left battle")
                    current_battle.ended = True
                    current_battle = None
    
    except websockets.exceptions.ConnectionClosed:
        print(f"[Server] Connection closed for {player_id}")
    except Exception as e:
        print(f"[Server] Error in handler: {e}")
        traceback.print_exc()
    finally:
        # Очистка
        for i, (ws, pid, _) in enumerate(waiting_queue):
            if ws == websocket:
                waiting_queue.pop(i)
                break
        
        if current_battle:
            current_battle.ended = True

async def main():
    port = int(os.environ.get("PORT", 8080))
    print(f"[Server] Starting PvP Server on port {port}...")
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"[Server] PvP Server is running on port {port}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
