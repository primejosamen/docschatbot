import React,{useContext,useState} from 'react';
import styled from "styled-components";
import { BrowserRouter as Router, Route, Link, Switch } from 'react-router-dom';
import UserContext from './user-context';
import ListGroup from 'react-bootstrap/ListGroup';
import Card from 'react-bootstrap/Card';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';
const ButtonTab = styled.button`
  font-size: 14px;
  color: black;
  padding: 10px 40px;
  cursor: pointer;
  opacity: 1;
  left: 0px;
  background: #fff2e6;
  border: 0;
  outline: 0;
  ${({ active }) =>
    active &&
    `
    border-bottom: 4px solid blue;
    opacity: 3;
    font-weight: bold;
  `}
`;
/*const ButtonGroup = styled.div`
  display: flex;
  className: 'btn-group-vertical'
`;*/

const ButtonGroup = styled.div.attrs({
  className: 'btn-group-vertical',
  })`
  display: flex;
`;

const types = ["Post Resume","Jobs", "My Profile Summary"];
/*const VerticalTab = ({ label, to }) => (
  <Link to={to} className="tab" activeClassName="active">
    {label}
  </Link>
);*/

const Accounts = () => {
  const user  = useContext(UserContext);
  const [active, setActive] = useState(types[0]);
  console.log(user.name);
  return (
<div class="container">

<br/>
<h3>Welcome, {user.name}</h3>
<br/>
<div class="row">
<div class="column-3">
  <div class="card text-right" style={{width: '55rem'}}>
  <div class="card-body">
    <h5 class="card-title text-left">Stock Plan(ABC)-1567</h5>
    <p class="card-text">Current Account Value&nbsp;&nbsp;&nbsp;&nbsp;$2000</p>
    <p class="card-text">Day's Gain&nbsp;&nbsp;&nbsp;&nbsp;$200</p>
    <p class="card-text">Total Account Value&nbsp;&nbsp;&nbsp;&nbsp;$5000</p>
    <a href="#" class="btn btn-primary">Details</a>
  </div>
</div>
<div class="card text-right" style={{width: '55rem'}}>
  <div class="card-body">
    <h5 class="card-title text-left">Stock Plan(CDE)-1667</h5>
    <p class="card-text">Current Account Value&nbsp;&nbsp;&nbsp;&nbsp;$3000</p>
    <p class="card-text">Day's Gain&nbsp;&nbsp;&nbsp;&nbsp;$200</p>
    <p class="card-text">Total Account Value&nbsp;&nbsp;&nbsp;&nbsp;$6000</p>
    <a href="#" class="btn btn-primary">Details</a>
  </div>
</div>
</div>
</div>
</div>
  );
};

export default Accounts;
