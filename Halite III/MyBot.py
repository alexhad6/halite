import hlt
from hlt import constants
from hlt.positionals import Direction
import states

ship_properties = {}

game = hlt.Game()
me = game.me
game_map = game.game_map
shipyard = me.shipyard

def target_cell(ship, direction = None):
	if direction == None:
		direction = ship.possible_moves[0]
	return game_map[game_map.normalize(ship.position.directional_offset(direction))]

game.ready('MyPythonBot')

''' Game Loop '''
while True:
	game.update_frame()
	my_ships = me.get_ships()
	command_queue = []

	''' Update Ship Properties '''
	for ship in my_ships:
		if not ship.id in ship_properties:
			ship_properties[ship.id] = (states.STILL, ship.position)

		ship.state, ship.previous_position = ship_properties[ship.id]
		ship.priority = 0

		if game.turn_number >= constants.MAX_TURNS - game_map.calculate_distance(ship.position, shipyard.position) - 10:
			ship.state = states.END

		if ship.state != states.END:
			if ship.halite_amount >= 950:
				ship.state = states.RETURN
			elif ship.halite_amount < 100:
				ship.state = states.SEARCH

		if ship.position == shipyard.position:
			ship.priority = 1

	''' Sort Ships by Priority'''
	my_ships.sort(key = lambda ship: ship.halite_amount, reverse = True)

	''' Calculate Ship Moves '''
	for ship in my_ships:
		ship_cell = game_map[ship]
		possible_moves = [Direction.Still]

		# Search for halite
		if ship.state == states.SEARCH:
			most_halite = 0

			
			def search_sort(direction):
				cell = target_cell(ship, direction)

				if cell.position == ship.previous_position:
					return -1
				else:
					return target_cell(ship, direction).halite_amount

			possible_moves = Direction.get_all_cardinals()
			possible_moves.sort(key = lambda direction: search_sort(direction), reverse = True)

			if ship_cell.halite_amount >= 50:
				possible_moves[:0] = [Direction.Still]

		# Return to nearest shipyard or dropoff
		elif ship.state == states.RETURN or ship.state == states.END:
			if ship.state == states.END and ship.position == shipyard.position:
				possible_moves = [Direction.Still]
			else:
				possible_moves = game_map.get_unsafe_moves(ship.position, shipyard.position)

		if ship_cell.halite_amount / 10 > ship.halite_amount:
			possible_moves = [Direction.Still]

		if possible_moves == []:
			possible_moves = [Direction.Still]

		ship.possible_moves = possible_moves

	''' Avoid Collisions '''
	while True:
		no_collisions = True
		for ship1 in my_ships:
			for ship2 in my_ships:
				if not ship1 is ship2:
					if target_cell(ship1) == target_cell(ship2):
						if not ((ship1.state == states.END and target_cell(ship1).position == shipyard.position) or (ship2.state == states.END and target_cell(ship2).position == shipyard.position)):
							no_collisions = False

							if ship1.halite_amount < ship2.halite_amount:
								ship2, ship1 = ship1, ship2

							if len(ship2.possible_moves) > 1:
								ship2.possible_moves = ship2.possible_moves[1:]
							elif len(ship1.possible_moves) > 1:
								ship1.possible_moves = ship1.possible_moves[1:]
							else:
								if ship2.possible_moves[0] != Direction.Still:
									ship2.possible_moves = [Direction.Still]
								elif ship1.possible_moves[0] != Direction.Still:
									ship1.possible_moves = [Direction.Still]
								else:
									ship1.possible_moves = [Direction.Still]
									ship2.possible_moves = [Direction.Still]

		if no_collisions:
			break

	''' Add Moves to Queue '''
	spawn_safe = True
	for ship in my_ships:
		command_queue.append(ship.move(ship.possible_moves[0]))

		if target_cell(ship).position == shipyard.position:
			spawn_safe = False

		if not ship.possible_moves[0] == Direction.Still:
			ship.previous_position = ship.position

		ship_properties[ship.id] = (ship.state, ship.previous_position) # save properties for next turn

	if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[shipyard].is_occupied and spawn_safe:
		command_queue.append(shipyard.spawn())

	game.end_turn(command_queue)