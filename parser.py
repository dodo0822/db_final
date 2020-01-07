#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import mysql.connector

cnx = mysql.connector.connect(host='localhost', user='root', password='20191228', database='basketball')
cursor = cnx.cursor(prepared=True)

game_id = -1
team_id = -1

number_table = {}

stmt = 'INSERT INTO `event` ( `game_id`, `time_sec`, `event_type`, `player1_id`, `player2_id`, `position_x`, `position_y` ) VALUES \
    ( %s, %s, %s, %s, %s, %s, %s )'

def print_error(err):
  print('Error: ' + err)

while True:
  line = input('> ')
  line = line.lstrip().rstrip()
  if len(line) == 0: continue
  arr = line.split(' ')
  
  if arr[0] == 'GAME':
    if len(arr) != 2:
      print_error('syntax must be GAME [game_id]')
      continue
    try:
      game_id = int(arr[1])
    except ValueError:
      print_error('invalid game id')
      continue
    print('Set game id OK')
  elif arr[0] == 'TEAM':
    if len(arr) != 2:
      print_error('syntax must be TEAM [team_id]')
      continue
    try:
      team_id = int(arr[1])
    except ValueError:
      print_error('invalid team id')
      continue

    cursor2 = cnx.cursor()
    cursor2.execute('SELECT `player_id`, `number`, `name` FROM `player` WHERE `team_id` = %s', (team_id,))
    print('Fetching player data..')
    number_table = {}
    for (player_id, player_number, player_name) in cursor2:
      print('{} -> {} (id={})'.format(player_number, player_name, player_id))
      number_table[player_number] = player_id
    print('Set team id OK')
  else:
    event_type = ''
    player1_id = -1
    player2_id = None
    time_sec = -1
    pos_x = None
    pos_y = None
    has_player2 = False
    player2_idx = -1
    at_idx = -1

    try:
      player1_id = int(arr[0])
    except ValueError:
      print_error('invalid player1 id')
      continue

    try:
      if arr[1] == 'ATTEMPT':
        if arr[2] == '3PT':
          event_type = 'THREEPOINT_A'
        elif arr[2] == '2PT':
          event_type = 'TWOPOINT_A'
        elif arr[2] == 'FT':
          event_type = 'FREETHROW_A'
        else:
          print_error('invalid event type')
          continue
        at_idx = 3
      elif arr[1] == 'MAKE':
        if arr[2] == '3PT':
          event_type = 'THREEPOINT_M'
        elif arr[2] == '2PT':
          event_type = 'TWOPOINT_M'
        elif arr[2] == 'FT':
          event_type = 'FREETHROW_M'
        else:
          print_error('invalid event type')
          continue
        at_idx = 3
        if event_type == 'THREEPOINT_M' or event_type == 'TWOPOINT_M':
          if arr[3] == 'ASSISTED' and arr[4] == 'BY':
            has_player2 = True
            player2_idx = 5
            at_idx = 6
      elif arr[1] == 'REBOUND':
        if arr[2] == 'OFFENSE':
          event_type = 'OFFENSE_REBOUND'
        elif arr[2] == 'DEFENSE':
          event_type = 'DEFENSE_REBOUND'
        else:
          print_error('invalid event type')
          continue
        at_idx = 3
      elif arr[1] == 'STEAL' or arr[1] == 'BLOCK' or arr[1] == 'FOUL' or arr[1] == 'TURNOVER' or arr[1] == 'BE_FOULED':
        event_type = arr[1]
        at_idx = 2
      elif arr[1] == 'IN':
        event_type = 'IN_COURT'
        at_idx = 2
      elif arr[1] == 'OUT':
        event_type = 'OUT_COURT'
        at_idx = 2
      else:
        print_error('invalid event type')
        continue

      if has_player2:
        try:
          player2_id = int(arr[player2_idx])
        except ValueError:
          print_error('invalid player2 id')
          continue

      if arr[at_idx] != 'AT':
        print_error('syntax error, expected AT at index ' + str(at_idx))
        continue

      try:
        time_str = arr[at_idx+1]
        time_str_arr = time_str.split('.')
        time_sec = int(time_str_arr[0]) * 60 + int(time_str_arr[1])
      except:
        print_error('invalid time')
        continue

      """if event_type == 'THREEPOINT_A' or event_type == 'THREEPOINT_M' \
        or event_type == 'TWOPOINT_A' or event_type == 'TWOPOINT_M':

        try:
          pos_x = int(arr[at_idx+2])
          pos_y = int(arr[at_idx+3])
        except ValueError:
          print_error('invalid position coordinates')
          continue
      """

      if player1_id not in number_table:
        print_error('invalid player 1 number')
        continue
      else:
        player1_id = number_table[player1_id]

      if player2_id is not None:
        if player2_id not in number_table:
          print_error('invalid player 2 number')
          continue
        else:
          player2_id = number_table[player2_id]

      print('{} {} {} {} {}'.format(game_id, time_sec, event_type, player1_id, player2_id))

      try:
        cursor.execute(stmt, (game_id, time_sec, event_type, player1_id, player2_id, pos_x, pos_y,))
        if (event_type == 'THREEPOINT_M' or event_type == 'TWOPOINT_M') and player2_id is not None:
          cursor.execute(stmt, (game_id, time_sec, 'ASSIST', player2_id, player1_id, pos_x, pos_y,))
        if event_type == 'THREEPOINT_M':
          cursor.execute(stmt, (game_id, time_sec, 'THREEPOINT_A', player1_id, None, pos_x, pos_y))
        if event_type == 'TWOPOINT_M':
          cursor.execute(stmt, (game_id, time_sec, 'TWOPOINT_A', player1_id, None, pos_x, pos_y))
        if event_type == 'FREETHROW_M':
          cursor.execute(stmt, (game_id, time_sec, 'FREETHROW_A', player1_id, None, pos_x, pos_y))
        cnx.commit()
      except mysql.connector.Error as err:
        print_error('error executing mysql statement: {}'.format(err))
        continue

      print('Execute OK')

    except IndexError:
      print_error('invalid number of arguments')
      continue
