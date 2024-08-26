import './index.css';
import {useState, useEffect} from "react";
import styled from "styled-components";
import Chatbot from 'react-chatbot-kit'
import ActionProvider from './ActionProvider';
import MessageParser from './MessageParser';
import config from './config';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import { BrowserRouter as Router, Switch, Route,BrowserRouter,NavLink,Link } from "react-router-dom";
import Accounts from "./Accounts"
//import PortalChatbot from "./PortalChatbot";
import AskDoc from "./AskDoc";
import UserContext from './user-context';
import 'react-chatbot-kit/build/main.css';
import logo from './img.png';
import './App.css';
import { io } from 'socket.io-client';

const Tab = styled.button`
  font-size: 14px;
  color: black;
  padding: 10px 60px;
  cursor: pointer;
  opacity: 1;
  background: #fff2e6;
  border: 0;
  outline: 0;
  ${({ active }) =>
    active &&
    `
    border-bottom: 2px solid blue;
    opacity: 1;
    font-weight: bold;
  `}
`;
const ButtonGroup = styled.div`
  display: flex;
`;

/*const ButtonGroup = styled.div.attrs({
  className: 'btn-group-vertical',
  })`
  display: flex;
`;*/

const types = ["Ask Doc","Accounts"];
function App() {
const [active, setActive] = useState(types[0]);
const [value, setValue] = useState("Tim");
const [showBot, toggleBot] = useState(false);
const [socketInstance, setSocketInstance] = useState("");
const [loading, setLoading] = useState(true);
const [buttonStatus, setButtonStatus] = useState(true);
const handleClick = () => {
    if (buttonStatus === false) {
      setButtonStatus(true);
    } else {
      setButtonStatus(false);
    }
  };
const handleChange = async(event) => {
setValue(event.target.value);
};


  return (
    <UserContext.Provider value={{ name: value,role:active }}>
    <div className="row">
     <Router>
    <nav className="navbar navbar-expand-lg">
    <div className="row align-items-center">
    <div class="col-1">
     <a class="navbar-brand" href="#">
    <img src={logo} width="100" height="100" alt=""/>
    </a>
    </div>
    <div class="col-8">
    <ButtonGroup>
                    {types.map((type) => (
                     <Tab
                       key={type}
                       active={active === type}
                       onClick={() => setActive(type)}>
                       {type}
                      </Tab>
                       ))}
                   </ButtonGroup>
    </div>
    <div class="col-2">
<label>Login:
                       <select value={value} onChange={handleChange}>
                         <option value="John">John</option>
                         <option value="Gopi">Gopi</option>
                         <option value="Tim">Tim</option>
                       </select>
                       <span class="label">&nbsp; Welcome: {value}</span>
                   </label>
        </div>
        </div>
        </nav>
    </Router>
    <div className="row">
      {active == "Ask Doc" && <AskDoc /> }
      {active == "Accounts" && <Accounts /> }
      </div>
    <div className="app-chatbot-container">
        {showBot && (
          <Chatbot
            config={config}
            messageParser={MessageParser}
            actionProvider={ActionProvider}
          />
        )}
      </div>
      <button
        className="app-chatbot-button"
        onClick={() => toggleBot((prev) => !prev)}
      >
        <div>Bot</div>
        <svg viewBox="0 0 640 512" className="app-chatbot-button-icon">
          <path d="M192,408h64V360H192ZM576,192H544a95.99975,95.99975,0,0,0-96-96H344V24a24,24,0,0,0-48,0V96H192a95.99975,95.99975,0,0,0-96,96H64a47.99987,47.99987,0,0,0-48,48V368a47.99987,47.99987,0,0,0,48,48H96a95.99975,95.99975,0,0,0,96,96H448a95.99975,95.99975,0,0,0,96-96h32a47.99987,47.99987,0,0,0,48-48V240A47.99987,47.99987,0,0,0,576,192ZM96,368H64V240H96Zm400,48a48.14061,48.14061,0,0,1-48,48H192a48.14061,48.14061,0,0,1-48-48V192a47.99987,47.99987,0,0,1,48-48H448a47.99987,47.99987,0,0,1,48,48Zm80-48H544V240h32ZM240,208a48,48,0,1,0,48,48A47.99612,47.99612,0,0,0,240,208Zm160,0a48,48,0,1,0,48,48A47.99612,47.99612,0,0,0,400,208ZM384,408h64V360H384Zm-96,0h64V360H288Z"></path>
        </svg>
      </button>
      </div>

</UserContext.Provider>
  );
}

export default App;