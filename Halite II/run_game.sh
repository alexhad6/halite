#!/bin/sh

javac MyBot.java
javac Enemy.java
./halite -d "240 160" "java MyBot" "java EnemyBot"
#./halite -d "360 240" "java MyBot" "java EnemyBot" "java EnemyBot" "java EnemyBot"