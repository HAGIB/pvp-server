import asyncio
import websockets
import json
import time
import random
import os

# Хранилище активных соединений
connected = {}
# Очередь на бой
queue = []
# Активные бои
battles = {}

async def handler(websocket, path):
    user_id = None
    
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "join_queue":
                user_id = data.get("user_id")
                player_data = data.get("player_data")
                connected[user_id] = {
                    "ws": websocket,
                    "data": player_data
                }
                
                # Ищем соперника
                if len(queue) > 0:
                    opponent_id = queue.pop(0)
                    if opponent_id in connected:
                        # Запускаем бой
                        battle_id = f"battle_{int(time.time())}"
                        player1 = connected[user_id]["data"]
                        player2 = connected[opponent_id]["data"]
                        
                        # Симулируем бой
                        result = simulate_battle(player1, player2)
                        
                        # Отправляем результат обоим
                        await connected[user_id]["ws"].send(json.dumps({
                            "action": "battle_found",
                            "battle_id": battle_id,
                            "result": result["player1_view"]
                        }))
                        await connected[opponent_id]["ws"].send(json.dumps({
                            "action": "battle_found",
                            "battle_id": battle_id,
                            "result": result["player2_view"]
                        }))
                        
                        # Удаляем из connected после боя
                        await asyncio.sleep(1)
                        if user_id in connected:
                            del connected[user_id]
                        if opponent_id in connected:
                            del connected[opponent_id]
                else:
                    queue.append(user_id)
                    await websocket.send(json.dumps({
                        "action": "waiting",
                        "position": len(queue)
                    }))
            
            elif action == "leave_queue":
                if user_id in queue:
                    queue.remove(user_id)
                await websocket.send(json.dumps({
                    "action": "left_queue"
                }))
            
            elif action == "ping":
                await websocket.send(json.dumps({"action": "pong"}))
    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if user_id:
            if user_id in queue:
                queue.remove(user_id)
            if user_id in connected:
                del connected[user_id]

def simulate_battle(p1, p2):
    p1_hp = p1.get("hp", 100)
    p1_dmg = p1.get("damage", 10)
    p1_crit = p1.get("crit", 10)
    p1_name = p1.get("nickname", "Игрок 1")
    
    p2_hp = p2.get("hp", 100)
    p2_dmg = p2.get("damage", 10)
    p2_crit = p2.get("crit", 10)
    p2_name = p2.get("nickname", "Игрок 2")
    
    rounds = []
    
    while p1_hp > 0 and p2_hp > 0:
        # Игрок 1 атакует
        dmg1 = p1_dmg
        if random.randint(1, 100) <= p1_crit:
            dmg1 *= 2
            rounds.append({"attacker": p1_name, "damage": dmg1, "crit": True})
        else:
            rounds.append({"attacker": p1_name, "damage": dmg1, "crit": False})
        p2_hp -= dmg1
        
        if p2_hp <= 0:
            break
        
        # Игрок 2 атакует
        dmg2 = p2_dmg
        if random.randint(1, 100) <= p2_crit:
            dmg2 *= 2
            rounds.append({"attacker": p2_name, "damage": dmg2, "crit": True})
        else:
            rounds.append({"attacker": p2_name, "damage": dmg2, "crit": False})
        p1_hp -= dmg2
    
    winner = p1_name if p2_hp <= 0 else p2_name
    loser = p2_name if p2_hp <= 0 else p1_name
    
    return {
        "player1_view": {
            "you": p1_name,
            "opponent": p2_name,
            "winner": winner,
            "rounds": rounds
        },
        "player2_view": {
            "you": p2_name,
            "opponent": p1_name,
            "winner": winner,
            "rounds": rounds
        }
    }

async def main():
    port = int(os.environ.get("PORT", 8080))
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"PvP сервер запущен на порту {port}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
