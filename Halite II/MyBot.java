import hlt.*;
import java.util.ArrayList;
import java.util.Collection;

public class MyBot {

	public static void main(final String[] args) {
		final Networking networking = new Networking();
		final GameMap gameMap = networking.initialize("MyBot");
		final ArrayList<Move> moveList = new ArrayList<>();

		for (;;) {
			final long startTime = System.nanoTime();
			moveList.clear();
			gameMap.updateMap(Networking.readLineIntoMetadata());

			final Player me = gameMap.getMyPlayer();

			final Collection<Ship> myShips = me.getShips().values();
			final ArrayList<Ship> enemyShips = new ArrayList<>();
			for (final Ship ship : gameMap.getAllShips()) {
				if (ship.getOwner() != me.getId()) {
					enemyShips.add(ship);
				}
			}

			for (final Ship ship : myShips) {
				if (timeFrom(startTime) >= 1800) {
					break;
				}

				if (ship.getDockingStatus() != Ship.DockingStatus.Undocked) {
					continue;
				}
				
				Planet targetPlanet = bestPlanet(me, ship, gameMap.getAllPlanets().values());

				if (targetPlanet != null) {
					if (ship.canDock(targetPlanet)){
						final Ship dockedShip = nearestShipDockedToPlanet(targetPlanet, ship, enemyShips);
						if (dockedShip != null) {
							final ThrustMove thrustMove = Navigation.navigateShipToDock(gameMap, ship, dockedShip, Constants.MAX_SPEED);
							if (thrustMove != null) {
								moveList.add(thrustMove);
							}
						}
						else if (!targetPlanet.isOwned()) {
							moveList.add(new DockMove(ship, targetPlanet));
						}
						else if (targetPlanet.getOwner() == me.getId()) {
							moveList.add(new DockMove(ship, targetPlanet));
						}
					}
					else {
						Ship targetShip = bestShip(ship, enemyShips);
						if (targetShip != null && ship.getDistanceTo(targetShip) < 50) {
							final ThrustMove thrustMove = Navigation.navigateShipToDock(gameMap, ship, targetShip, Constants.MAX_SPEED);
							if (thrustMove != null) {
								moveList.add(thrustMove);
							}
						}
						else {
							final ThrustMove thrustMove = Navigation.navigateShipToDock(gameMap, ship, targetPlanet, Constants.MAX_SPEED);
							if (thrustMove != null) {
								moveList.add(thrustMove);
							}
						}
					}
				}
			}

			Networking.sendMoves(moveList);
		}
	}

	public static Planet bestPlanet(final Player me, final Ship ship, final Collection<Planet> planets) {
		Planet bestPlanet = null;
		double highestValue = 0;

		for (final Planet planet : planets) {
			if (planet.getOwner() == me.getId() && planet.isFull()) {
				continue;
			}
			else {
				double value = 1/ship.getDistanceTo(planet);
				if (planet.isOwned() && planet.getOwner() != me.getId()) {
					value *= 1.5;
				}
				
				if (value > highestValue) {
					highestValue = value;
					bestPlanet = planet;
				}
			}
		}

		return bestPlanet;
	}

	public static Ship bestShip(final Ship ship, final Collection<Ship> enemyShips) {
		Ship bestShip = null;
		double highestValue = 0;

		for (final Ship enemyShip : enemyShips) {
			double value = 1/enemyShip.getDistanceTo(ship);
			if (enemyShip.getDockingStatus() != Ship.DockingStatus.Undocked) {
				value *= 3;
			}
			if (value > highestValue) {
				highestValue = value;
				bestShip = enemyShip;
			}
		}

		return bestShip;
	}

	public static Ship nearestShipDockedToPlanet(final Planet planet, final Ship ship, final Collection<Ship> enemyShips) {
		Ship nearestDockedShip = null;
		double minDistance = Double.MAX_VALUE;

		for (final int shipId : planet.getDockedShips()) {
			for (final Ship enemyShip : enemyShips) {
				if (enemyShip.getId() == shipId) {
					double distance = ship.getDistanceTo(enemyShip);
					if (distance < minDistance) {
						minDistance = distance;
						nearestDockedShip = enemyShip;
					}
				}
			}
		}

		return nearestDockedShip;
	}

	public static double timeFrom(long startTime) {
		return (System.nanoTime() - startTime) / 1000000.0;
	}
}