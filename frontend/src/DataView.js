import React, { Component } from 'react';
import update from 'immutability-helper';

class DataView extends Component {

  constructor(props) {
    super(props);

    this.state = {
      cols: [],
      rows: [],
      rowsObj: [],
      calcExpr: '',
      calcName: '',
      customExprs: [],
      customNames: [],
      customResults: []
    };
  }

  componentDidMount() {
    fetch('http://ggt.tw:5555/data?game_id=1')
    .then((resp) => {
      return resp.json();
    })
    .then((resp) => {
      let rowsObj = [];
      let customResults = [];
      for(let i = 0; i < resp.rows.length; ++i) {
        let r = {};
        for(let j = 0; j < resp.cols.length; ++j) {
          r[resp.cols[j]] = resp.rows[i][j];
        }
        rowsObj.push(r);
        customResults.push([]);
      }
      this.setState({ rowsObj, customResults, ...resp });
    });
  }

  calc() {
    let expr = this.state.calcExpr.replace(/ /g, '');
    let customNames = this.state.customNames;
    customNames = update(customNames, { $push: [this.state.calcName] });
    let customExprs = this.state.customExprs;
    customExprs = update(customExprs, { $push: [expr]});
    let customResults = this.state.customResults;
    let rowsObj = this.state.rowsObj;
    for(let i = 0; i < this.state.rows.length; ++i) {
      let result = this.calcPlus(i, expr);
      customResults = update(customResults, { [i]: { $push: [result] } });
      rowsObj = update(rowsObj, { [i]: { $merge: { [this.state.calcName]: result } } })
    }
    this.setState({ customNames, customExprs, customResults, rowsObj });
  }

  resolveSymbol(idx, symbol) {
    return isNaN(symbol) ? this.state.rowsObj[idx][symbol] : +symbol;
  }

  split(expression, operator) {
    const result = [];
    let braces = 0;
    let currentChunk = "";
    for (let i = 0; i < expression.length; ++i) {
      const curCh = expression[i];
      if (curCh == '(') {
        braces++;
      } else if (curCh == ')') {
        braces--;
      }
      if (braces == 0 && operator == curCh) {
        result.push(currentChunk);
        currentChunk = "";
      } else currentChunk += curCh;
    }
    if (currentChunk != "") {
      result.push(currentChunk);
    }
    return result;
  }

  calcMultiply(idx, expr) {
    let arr = this.split(expr, '*');
    let numbers = arr.map(symbol => this.calcDivision(idx, symbol));
    let val = 1.0;
    return numbers.reduce((acc, no) => acc*no, val);
  }

  calcDivision(idx, expr) {
    let arr = this.split(expr, '/');
    let numbers = arr.map((symbol) => {
      if(symbol[0] === '(') {
        return this.calcPlus(idx, symbol.substring(1, symbol.length-1));
      }
      return this.resolveSymbol(idx, symbol);
    });
    let val = numbers[0];
    numbers.splice(0, 1);
    return numbers.reduce((acc, no) => acc/no, val);
  }

  calcSubtraction(idx, expr) {
    let arr = this.split(expr, '-');
    let numbers = arr.map(symbol => this.calcMultiply(idx, symbol));
    let val = numbers[0]*2;
    return numbers.reduce((acc, no) => acc-no, val);
  }

  calcPlus(idx, expr) {
    let arr = this.split(expr, '+');
    let numbers = arr.map(symbol => this.calcSubtraction(idx, symbol));
    return numbers.reduce((acc, no) => acc+no);
  }

  render() {
    let headers = [];
    for(let i = 0; i < this.state.cols.length; ++i) {
      headers.push(<th key={i}>{this.state.cols[i]}</th>);
    }
    for(let i = 0; i < this.state.customNames.length; ++i) {
      headers.push(<th key={`custon-${i}`}>{this.state.customNames[i]}</th>);
    }
    let rows = [];
    for(let i = 0; i < this.state.rows.length; ++i) {
      let row = [];
      for(let j = 0; j < this.state.rows[i].length; ++j) {
        row.push(<td key={j}>{this.state.rows[i][j]}</td>);
      }
      for(let j = 0; j < this.state.customResults[i].length; ++j) {
        row.push(<td key={`custom-${j}`}>{this.state.customResults[i][j]}</td>);
      }
      rows.push(<tr key={i}>{row}</tr>);
    }
    return (
      <div className="dataview">
        <table>
          <thead>
            <tr>{headers}</tr>
          </thead>
          <tbody>
            {rows}
          </tbody>
        </table>
        <p>
          <input type="text" placeholder="Name" value={this.state.calcName} onChange={(e) => { this.setState({ calcName: e.target.value }) }} />
          <input type="text" placeholder="Expression" value={this.state.calcExpr} onChange={(e) => { this.setState({ calcExpr: e.target.value }) }} />
          <button onClick={() => { this.calc(); }}>Calculate</button>
        </p>
      </div>
    );
  }

}

export default DataView;
