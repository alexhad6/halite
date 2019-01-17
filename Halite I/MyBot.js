const {STILL, NORTH, EAST, SOUTH, WEST, DIRECTIONS, CARDINALS, Move} = require('./hlt');
const Networking = require('./networking');
const network = new Networking('MyBot');

network.on('map', (gameMap, id) => {
	const moves = [];

	function getCells() {
		const cells = [];
		for (let y = 0; y < gameMap.height; y++) {
			for (let x = 0; x < gameMap.width; x++) {
				cells.push({
					loc: {x, y},
					site: gameMap.getSite({x, y})
				});
			}
		}
		return cells;
	}

	function getNeighbors(cell) {
		const neighbors = [];

		for (let d of CARDINALS) {
			neighbors.push({
				direction: d,
				loc: gameMap.getLocation(cell.loc, d),
				site: gameMap.getSite(cell.loc, d)
			});
		}

		return neighbors;
	}

	function getEnemyNeighbors(cell) {
		const neighbors = [];
		for(neighbor of getNeighbors(cell)) {
			if (neighbor.site.owner !== id) {
				neighbors.push(neighbor);
			}
		}
		return neighbors;
	}

	function getSelfNeighbors(cell) {
		const neighbors = [];
		for(neighbor of getNeighbors(cell)) {
			if (neighbor.site.owner === id) {
				neighbors.push(neighbor);
			}
		}
		return neighbors;
	}

	function getBorderNeighbors(cell) {
		const neighbors = [];
		for(neighbor of getSelfNeighbors(cell)) {
			if (onBorder(neighbor)) {
				neighbors.push(neighbor);
			}
		}
		return neighbors;
	}

	function value(cell) {
		if (cell.site.strength > 0) {
			return cell.site.production / cell.site.strength;
		}
		return cell.site.production;
	}

	function overKillDamage(cell) {
		let maxDamage = 0;
		for (let d of CARDINALS) {
			let neighborSite = gameMap.getSite(cell.loc, d);
			if (neighborSite.owner !== 0 && neighborSite.owner !== id) {
				maxDamage += neighborSite.strength;
			}
		}

		return maxDamage;
	}

	function capLoss(cell, dir) {
		let loss = (cell.site.strength + gameMap.getSite(cell.loc, dir)) - 255;
		return (loss > 0) ? loss : 0;
	}

	function onBorder(cell) {
		for (let d of CARDINALS) {
			if (gameMap.getSite(cell.loc, d).owner != id) {
				return true;
			}
		}
		return false;
	}

	function insideValue(cell) {
		if(cell.distance > 0) {
			if(cell.site.strength > 0) {
				return value(cell) / (cell.distance * cell.distance);
			}
			return cell.site.production / (cell.distance * cell.distance);
		}
		return cell.site.production;
	}

	function borderValue(cell) {
		if (cell.site.owner === 0 && cell.site.strength > 0) {
			return value(cell);
		}
		else {
			return overKillDamage(cell);
		}
	}

	function highestBorderValue(cell) {
		let highestValue = 0;
		for(neighbor of getEnemyNeighbors(cell)) {
			if(borderValue(neighbor) > highestValue) {
				highestValue = borderValue(neighbor);
			}
		}

		return highestValue;
	}

	function insideDirection(cell) {
		const borders = [];
		let maxDist = Math.min(gameMap.width, gameMap.height) / 2;

		for(let d of CARDINALS) {
			let dist = 0;
			let current = cell.loc;
			let site = gameMap.getSite(current, d);
			while (site.owner == id && dist < maxDist) {
				dist++;
				current = gameMap.getLocation(current, d);
				site = gameMap.getSite(current);
			}

			if (dist < maxDist) {
				borders.push({
					direction: d,
					loc: current,
					distance: dist,
					site: site
				});
			}	
		}

		if(borders.length > 0) {
			borders.sort(function(b1, b2) {
				return insideValue(b2) - insideValue(b1);
			});
			return borders[0].direction;
		}
		
		return NORTH;
	}

	function borderDirection(cell) {
		const neighbors = getBorderNeighbors(cell);

		if(neighbors.length > 0) {
			neighbors.sort(function(n1, n2) {
				return highestBorderValue(n2) - highestBorderValue(n1);
			});
			if(highestBorderValue(cell) > highestBorderValue(neighbors[0])) {
				return STILL;
			}
			return neighbors[0].direction;
		}
	}

	function findTarget(cell) {
		const neighbors = getEnemyNeighbors(cell);

		if(neighbors.length > 0) {
			neighbors.sort(function(n1, n2) {return borderValue(n2) - borderValue(n1);});
			return neighbors[0];
		}
	}

	function move(cell) {
		const target = findTarget(cell);
		const border = onBorder(cell);

		if (border) {
			if(target.site.strength < cell.site.strength || (target.site.strength == 255 && cell.site.strength == 255) ) {
				return new Move(cell.loc, target.direction);
			}
			else {
				if (cell.site.strength < cell.site.production * 5 || cell.site.strength === 0) {
					return new Move(cell.loc, STILL);
				}
				return new Move(cell.loc, borderDirection(cell))
			}
		}

		if (cell.site.strength < cell.site.production * 5 || cell.site.strength === 0) {
			return new Move(cell.loc, STILL);
		}

		if (!border) {
			const d = insideDirection(cell);
			if(capLoss(cell, d)<=10) {
				return new Move(cell.loc, d);
			}
		}

		return new Move(cell.loc, STILL);
		
	}

	for (let cell of getCells()) {
		if (cell.site.owner === id) {
			moves.push(move(cell));
		}
	}

	network.sendMoves(moves);
});