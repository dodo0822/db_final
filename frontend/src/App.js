import React, { Component } from 'react';
import { BrowserRouter as Router, Route } from 'react-router-dom';
import './App.css';

import GameView from './GameView';
import DataView from './DataView';

class App extends Component {

  constructor(props) {
    super(props);
  }

  render() {
    return (
      <Router basename="/">
        <div>
          <Route exact path="/GameView" component={GameView} />
          <Route exact path="/DataView" component={DataView} />
        </div>
      </Router>
    );
  }

}

export default App;
