#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

number_table = {}

stmt = 'INSERT INTO `event` ( `game_id`, `time_sec`, `event_type`, `player1_id`, `player2_id`, `position_x`, `position_y` ) VALUES \
    ( %s, %s, %s, %s, %s, %s, %s )'

def parse_line(game_id, team_id, line, cursor):
  cursor.execute('SELECT `player_id`, `number`, `name` FROM `player` WHERE `team_id` = %s', (team_id,))
  number_table = {}
  for (player_id, player_number, player_name) in cursor:
    #print('{} -> {} (id={})'.format(player_number, player_name, player_id))
    number_table[player_number] = player_id

  line = line.lstrip().rstrip()
  if len(line) == 0: return 'OK'
  arr = line.split(' ')
  
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
    return 'invalid player1 id'

  try:
    if arr[1] == 'ATTEMPT':
      if arr[2] == '3PT':
        event_type = 'THREEPOINT_A'
      elif arr[2] == '2PT':
        event_type = 'TWOPOINT_A'
      elif arr[2] == 'FT':
        event_type = 'FREETHROW_A'
      else:
        return 'invalid event type'
      at_idx = 3
    elif arr[1] == 'MAKE':
      if arr[2] == '3PT':
        event_type = 'THREEPOINT_M'
      elif arr[2] == '2PT':
        event_type = 'TWOPOINT_M'
      elif arr[2] == 'FT':
        event_type = 'FREETHROW_M'
      else:
        return 'invalid event type'
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
        return 'invalid event type'
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
      return 'invalid event type'

    if has_player2:
      try:
        player2_id = int(arr[player2_idx])
      except ValueError:
        return 'invalid player2 id'

    if arr[at_idx] != 'AT':
      return 'syntax error, expected AT at index {}'.format(at_idx)

    try:
      time_str = arr[at_idx+1]
      time_str_arr = time_str.split('.')
      time_sec = int(time_str_arr[0]) * 60 + int(time_str_arr[1])
    except:
      return 'invalid time'

    if event_type == 'THREEPOINT_A' or event_type == 'THREEPOINT_M' \
      or event_type == 'TWOPOINT_A' or event_type == 'TWOPOINT_M':

      try:
        pos_x = int(arr[at_idx+2])
        pos_y = int(arr[at_idx+3])
      except ValueError:
        pass

    if player1_id not in number_table:
      return 'invalid player 1 number'
    else:
      player1_id = number_table[player1_id]

    if player2_id is not None:
      if player2_id not in number_table:
        return 'invalid player 2 number'
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
    except mysql.connector.Error as err:
      return 'error executing mysql statement: {}'.format(err)

    return 'OK'

  except IndexError:
    return 'invalid number of arguments'
