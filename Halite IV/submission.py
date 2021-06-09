from kaggle_environments.envs.halite.helpers import *
from random import choice, random

def distance(position1: Point, position2: Point, size: int):
    relative_position = abs(position1 % size - position2 % size)
    return relative_position.map(lambda component: min(component, size - component))

@board_agent
def agent(board):
    me = board.current_player
    c = board.configuration
    step = board.step
    max_ships = 10
    
    for i in range(100):
        new_ships = 0
        if len(me.shipyard_ids) == 0:
            for ship in me.ships:
                if me.halite + ship.halite >= c.convert_cost + c.spawn_cost:
                    ship.next_action = ShipAction.CONVERT
                    break
        else:
            shipyard_positions = [shipyard.position for shipyard in me.shipyards]

            if len(me.ship_ids) < max_ships and me.halite >= c.spawn_cost:
                shipyard = choice(me.shipyards)
                if random() < 0.5:
                    shipyard.next_action = ShipyardAction.SPAWN
                    new_ships += 1

            for ship in me.ships:
                if ship.cell.halite > 50:
                    ship.next_action = None
                elif ship.halite > 500:
                    actions = [[move, float('inf')] for move in ShipAction.moves()]

                    for action in actions:
                        next_position = ship.position.translate(action[0].to_point(), c.size)
                        dists = [distance(next_position, shipyard.position, c.size) for shipyard in me.shipyards]
                        action[1] = min(dists)

                    ship.next_action = min(actions, key = lambda action: action[1])[0]
                else:
                    ship.next_action = choice(ShipAction.moves())
        if len(board.next().current_player.ship_ids) >= len(me.ship_ids) + new_ships:
            break