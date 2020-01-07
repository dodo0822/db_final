import React, { Component } from 'react';

class GameView extends Component {

  constructor(props) {
    super(props);

    this.state = {
      game_id_input: '',
      team_id_input: '',
      game_id: -1,
      team_id: -1,
      status: 'input',
      players: {},
      time: 0,
      userCommand: '',
      lastExecuteResult: '',
      posX: 0,
      posY: 0,
      events: []
    };

    this.canvasRef = React.createRef();
  }

  componentWillUnmount() {
    if(this.keyListener !== undefined) document.removeEventListener(this.keyListener);
    if(this.interval !== undefined) clearInterval(this.interval);
  }

  componentDidMount() {
    this.setState({ game_id_input: '1', team_id_input: '1' }, () => { this.confirmInput(); });
    this.interval = setInterval(() => {
      if(this.state.status === 'run') this.setState({ time: this.state.time+1 });
    }, 1000);
  }

  toggleTimer() {
    this.setState({ status: (this.state.status === 'run' ? 'stop' : 'run') });
  }

  buildCommand() {
    let minute = Math.floor(this.state.time / 60);
    let second = this.state.time % 60;
    let timeStr = minute + '.' + second;
    let command = `${this.state.userCommand} AT ${timeStr} ${Math.round(this.state.posX)} ${Math.round(this.state.posY)}`;
    return command;
  }

  setupKey() {
    this.keyListener = document.addEventListener('keydown', (e) => {
      const chars = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','1','2','3','4','5','6','7','8','9','0'];
      if(chars.indexOf(e.key) > -1) {
        this.setState({ userCommand: this.state.userCommand + e.key.toUpperCase() });
      }
      console.log(e.keyCode);
      if(e.keyCode === 32) {
        if(this.state.userCommand.length === 0) return;
        if(this.state.userCommand[this.state.userCommand.length-1] === ' ') return;
        this.setState({ userCommand: this.state.userCommand + ' ' });
      }
      if(e.keyCode === 27) {
        this.setState({ userCommand: '' });
      }
      if(e.keyCode === 8) {
        this.setState({ userCommand: this.state.userCommand.substring(0, this.state.userCommand.length-1) }, () => { this.buildCommand(); });
      }
      if(e.keyCode === 9) {
        e.preventDefault();
        this.toggleTimer();
      }
      if(e.keyCode === 13) {
        e.preventDefault();
        this.submitCommand();
      }
      if(e.keyCode === 37) {
        e.preventDefault();
        this.setState({ time: Math.max(0, this.state.time - 1) });
      }
      if(e.keyCode === 39) {
        e.preventDefault();
        this.setState({ time: this.state.time + 1 });
      }
    });
  }

  submitCommand() {
    let stmt = this.buildCommand();
    let executeResult = stmt;
    this.setState({ lastExecuteResult: executeResult });
    fetch('http://ggt.tw:5555/command', {
      method: 'POST',
      body: JSON.stringify({ game_id: this.state.game_id, team_id: this.state.team_id, line: stmt }),
      headers: new Headers({
        'Content-Type': 'application/json'
      })
    })
    .then((resp) => {
      return resp.text();
    })
    .then((resp) => {
      this.setState({ lastExecuteResult: executeResult + ' => ' + resp, userCommand: '' });
    })
    .catch((err) => {
      console.log(err);
      this.setState({ lastExecuteResult: executeResult + ' => Server error'});
    });
  }

  confirmInput() {
    this.setState({
      game_id: parseInt(this.state.game_id_input),
      team_id: parseInt(this.state.team_id_input)
    });

    fetch('http://ggt.tw:5555/team?team_id=' + encodeURIComponent(this.state.game_id_input))
    .then((resp) => {
      return resp.json();
    })
    .then((resp) => {
      this.setState({
        status: 'stop',
        players: resp
      });
      this.buildCommand();
      this.setupKey();
      setTimeout(() => {
        this.setupCanvas();
      }, 200);
    });
  }

  updateCanvas() {
    const totalX = 624-79;
    const totalY = 449-119;

    let ctx = this.canvasRef.current.getContext('2d');
    ctx.clearRect(0, 0, 665, 490);
    ctx.drawImage(this.bgImg, 0, 0, 665, 490);

    for(let i = 0; i < this.state.events.length; ++i) {
      const evt = this.state.events[i];
      if(evt.event_type == 'TWOPOINT_A' || evt.event_type == 'THREEPOINT_A') {
        ctx.fillStyle = '#0000ff';
      } else {
        ctx.fillStyle = '#00ff00';
      }
      ctx.beginPath();
      ctx.arc(59+(evt.position_x * totalX / 94), 79+(evt.position_y * totalY / 50), 5, 0, 2 * Math.PI);
      ctx.fill();
    }
    
    ctx.fillStyle = '#ff0000';
    ctx.beginPath();
    ctx.arc(59+(this.state.posX * totalX / 94), 79+(this.state.posY * totalY / 50), 10, 0, 2 * Math.PI);
    ctx.fill();
  }

  setupCanvas() {
    let canvasElm = this.canvasRef.current;
    let ctx = canvasElm.getContext('2d');
    this.bgImg = new Image();
    this.bgImg.src = require('./court.jpg');
    this.bgImg.onload = () => {
      ctx.drawImage(this.bgImg, 0, 0, canvasElm.width, canvasElm.height);
    };
    canvasElm.onclick = (e) => {
      const totalX = 624-79;
      const totalY = 449-119;
      let x = Math.max(((e.clientX - 79) / totalX) * 94, 0);
      x = Math.min(x, 94);
      let y = Math.max(((e.clientY - 129) / totalY) * 50, 0);
      y = Math.min(y, 50);
      //console.log(x, y);
      this.setState({ posX: x, posY: y }, () => { this.updateCanvas(); });
    };

    fetch('http://ggt.tw:5555/shoot?game_id='+this.state.game_id_input+'&team_id='+this.state.team_id_input)
    .then((resp) => { return resp.json(); })
    .then((resp) => {
      this.setState({ events: resp });
      this.updateCanvas();
    });
  }

  renderInput() {
    return (
      <div>
        <p>Game ID: <input type="text" value={this.state.game_id_input} onChange={(e) => { this.setState({ game_id_input: e.target.value }); }} /></p>
        <p>Team ID: <input type="text" value={this.state.team_id_input} onChange={(e) => { this.setState({ team_id_input: e.target.value }); }} /></p>
        <p><button onClick={() => { this.confirmInput(); }}>Confirm</button></p>
      </div>
    );
  }

  render() {
    if(this.state.status === 'input') {
      return this.renderInput();
    }

    let players = [];
    for(const number in this.state.players) {
      players.push(<p key={number}>{number} : {this.state.players[number]}</p>);
    }

    return (
      <div className="main">
        <div className="players">{players}</div>
        <div className="status">{this.state.status === 'stop' ? '(PAUSED)' : ''}</div>
        <code className="command">{this.buildCommand()}<br />{this.state.lastExecuteResult}</code>
        <canvas width="665" height="490" className="court" ref={this.canvasRef}></canvas>
      </div>
    );
  }

};

export default GameView;
