from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from parser import parse_line
import simplejson as json

import mysql.connector

cnx = mysql.connector.connect(host='localhost', user='root', password='20191228', database='basketball')
parser_cursor = cnx.cursor()

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
  return 'Hello World!'

@app.route('/command', methods=['POST'])
def command():
  content = request.get_json(silent=True)
  game_id = content.get('game_id')
  team_id = content.get('team_id')
  line = content.get('line')

  result = parse_line(game_id, team_id, line, parser_cursor)
  cnx.commit()
  return result

@app.route('/team', methods=['GET'])
def team():
  team_id = request.args.get('team_id')
  cursor2 = cnx.cursor()
  cursor2.execute('SELECT `player_id`, `number`, `name` FROM `player` WHERE `team_id` = %s', (team_id,))
  number_table = {}
  for (player_id, player_number, player_name) in cursor2:
    number_table[player_number] = player_name

  return jsonify(number_table)

@app.route('/finalize', methods=['GET', 'POST'])
def finalize():
  if request.method == 'GET':
    return render_template('finalize.html')
  game_id = int(request.form.get('game_id'))
  cursor2 = cnx.cursor()
  try:
    cursor2.execute('CALL UPDATEDATA(%s)', (game_id,))
    cnx.commit()
  except mysql.connector.Error as err:
    return 'Error: {}'.format(err)
  return 'Finalize OK!'

@app.route('/shoot', methods=['GET'])
def shoot():
  game_id = int(request.args.get('game_id'))
  team_id = int(request.args.get('team_id'))
  stmt = "SELECT `event_type`, `position_x`, `position_y`, `player_id`, `player1_id` FROM `event` JOIN `player` ON `player`.`player_id` = `event`.`player1_id` WHERE `player`.`team_id` = %s AND `event`.`game_id` = %s AND `event_type` = 'THREEPOINT_M' OR `event_type` = 'THREEPOINT_A' OR `event_type` = 'TWOPOINT_M' OR `event_type` = 'TWOPOINT_A'"

  cur = cnx.cursor(dictionary=True)
  cur.execute(stmt, (team_id, game_id,))
  return jsonify(cur.fetchall())

@app.route('/data', methods=['GET'])
def data():
  game_id = int(request.args.get('game_id'))
  cursor2 = cnx.cursor(dictionary=True)
  try:
    cursor2.callproc('Data_Game', [game_id, ])
  except mysql.connector.Error as err:
    return 'Error: {}'.format(err)

  
  stored_results = cursor2.stored_results()
  result_set = []
  col_names = []
  for result in stored_results:
    result_list = result.fetchall()
    result_set += result_list
    for col in result.description:
      col_names.append(col[0])

  return json.dumps({ 'rows': result_set, 'cols': col_names })

def update_procedure():
  stmt = 'DROP PROCEDURE IF EXISTS Data_Game'
  cur = cnx.cursor()
  cur.execute(stmt)
  cnx.commit()

  stmt = 'SELECT * FROM `custom_column`'
  cur = cnx.cursor()
  cur.execute(stmt)
  
  col_str = ''
  col_str_arr = []
  for (column_id, name, expression) in cur:
    col_str_arr.append('{} AS `{}`'.format(expression, name))

  col_str = ', '.join(col_str_arr)

  base_procedure_stmt = '''
CREATE PROCEDURE `Data_Game`(_Game INT)
BEGIN
declare h_id, g_id INT;
SELECT guest_team_id, home_team_id INTO g_id, h_id
FROM game 
WHERE game_id = _Game;

SELECT *{} FROM (SELECT P.team_id AS TEAM, P.name AS NAME, P.number AS No, SIN_TIME(P.player_id, _Game) AS `TIME`,  2*SIN_2PT_M(P.player_id, _Game)+SIN_3PT_M(P.player_id, _Game)*3 + SIN_FT_M(P.player_id, _Game) AS PTS,
		SIN_DFE_REB(P.player_id, _Game) + SIN_OFF_REB(P.player_id, _Game) AS REB, SIN_DFE_REB(P.player_id, _Game) AS DREB, SIN_OFF_REB(P.player_id, _Game) AS OFFREB,
		SIN_ASSIST(player_id, _Game) AS AST, SIN_STEAL(player_id, _Game) AS STEAL,  SIN_BLOCK(player_id, _Game) AS BLK, SIN_TURNOVER(player_id, _Game) AS TURNOVER,
		SIN_2PT_M(player_id, _Game)+SIN_3PT_M(player_id, _Game) AS FGM, SIN_2PT_A(player_id, _Game)+SIN_3PT_A(player_id, _Game) AS FGA, 
		ROUND(DIVIDE(SIN_2PT_M(player_id, _Game)+SIN_3PT_M(player_id, _Game), SIN_2PT_A(player_id, _Game)+SIN_3PT_A(player_id, _Game))*100,0) AS `FG%`, 
		SIN_3PT_M(player_id, _Game) AS 3PM, SIN_3PT_A(player_id, _Game) AS 3PA, 
		ROUND(DIVIDE(SIN_3PT_M(player_id, _Game), SIN_3PT_A(player_id, _Game))*100,0) AS `3P%`,
		SIN_2PT_M(player_id, _Game) AS 2PM, SIN_2PT_A(player_id, _Game) AS 2PA, 
		ROUND(DIVIDE(SIN_2PT_M(player_id, _Game), SIN_2PT_A(player_id, _Game))*100, 0) AS `2P%`,
		SIN_FT_M(player_id, _Game) AS FTM, SIN_FT_A(player_id, _Game) AS FTA, 
		ROUND(DIVIDE(SIN_FT_M(player_id, _Game), SIN_FT_A(player_id, _Game))*100,0) AS `FT%`,
		SIN_FOUL(player_id, _Game) AS PF

FROM player AS P
WHERE P.team_id = g_id OR P.team_id = h_id) AS `parent`;
END
'''
  if len(col_str_arr) > 0: col_str = ', ' + col_str
  procedure_stmt = base_procedure_stmt.format(col_str)

  cur = cnx.cursor()
  cur.execute(procedure_stmt)
  cnx.commit()

  return procedure_stmt

@app.route('/update_procedure')
def route_update_procedure():
  return update_procedure()

@app.route('/col_list', methods=['GET'])
def col_list():
  l = []
  cur = cnx.cursor()
  cur.execute('SELECT * FROM `custom_column`')
  for (column_id, name, expression) in cur:
    l.append({ 'column_id':column_id, 'name':name, 'expression':expression })

  return render_template('col_list.html', cols=l)

@app.route('/col_delete', methods=['GET'])
def col_delete():
  column_id = request.args.get('column_id')
  cur = cnx.cursor()
  cur.execute('DELETE FROM `custom_column` WHERE `column_id` = %s', (column_id,))

  update_procedure()
  return 'OK <a href="/col_list">back</a>'

@app.route('/col_add', methods=['GET', 'POST'])
def col_add():
  if request.method == 'GET':
    return render_template('col_add.html')
  name = request.form.get('name')
  expr = request.form.get('expr')

  cur = cnx.cursor()
  cur.execute('INSERT INTO `custom_column` ( `name`, `expression` ) VALUES ( %s, %s )', (name, expr,))

  update_procedure()

  return 'OK <a href="/col_list">back</a>'

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5555)
