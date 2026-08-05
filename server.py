import asyncio
import websockets
import json
import os

waiting_queue = []
active_battles = {}

async def handler(websocket):
    player_id = None
    current_battle = None
    player_side = None
    
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "join_queue":
                player_id = data.get("user_id", str(id(websocket)))
                skin = data.get("skin", "DEFAULT")
                
                if len(waiting_queue) > 0:
                    opponent_ws, opponent_id, opponent_skin = waiting_queue.pop(0)
                    battle_id = f"battle_{player_id}_{opponent_id}"
                    
                    active_battles[battle_id] = {
                        "player1": websocket,
                        "player2": opponent_ws,
                    }
                    
                    await websocket.send(json.dumps({
                        "action": "battle_start",
                        "opponent_id": opponent_id,
                        "opponent_skin": opponent_skin,
                        "side": "player1",
                        "battle_id": battle_id
                    }))
                    await opponent_ws.send(json.dumps({
                        "action": "battle_start",
                        "opponent_id": player_id,
                        "opponent_skin": skin,
                        "side": "player2",
                        "battle_id": battle_id
                    }))
                    
                    current_battle = battle_id
                    player_side = "player1"
                else:
                    waiting_queue.append((websocket, player_id, skin))
                    await websocket.send(json.dumps({
                        "action": "waiting",
                        "position": len(waiting_queue)
                    }))
            
            elif action == "game_data":
                if current_battle and current_battle in active_battles:
                    battle = active_battles[current_battle]
                    target = "player2" if player_side == "player1" else "player1"
                    target_ws = battle.get(target)
                    if target_ws:
                        try:
                            await target_ws.send(json.dumps(data))
                        except:
                            pass
            
            elif action == "leave_battle":
                if current_battle and current_battle in active_battles:
                    battle = active_battles[current_battle]
                    other = "player2" if player_side == "player1" else "player1"
                    other_ws = battle.get(other)
                    if other_ws:
                        try:
                            await other_ws.send(json.dumps({"action": "opponent_left"}))
                        except:
                            pass
                    del active_battles[current_battle]
                    current_battle = None
    
    except:
        pass
    finally:
        if current_battle and current_battle in active_battles:
            battle = active_battles[current_battle]
            other = "player2" if player_side == "player1" else "player1"
            other_ws = battle.get(other)
            if other_ws:
                try:
                    await other_ws.send(json.dumps({"action": "opponent_left"}))
                except:
                    pass
            del active_battles[current_battle]

async def main():
    port = int(os.environ.get("PORT", 8080))
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"PvP Server on port {port}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
