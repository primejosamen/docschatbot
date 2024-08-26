// new file called DogPicture.jsx
import React, { useEffect, useState, useContext } from 'react';
import UserContext from './user-context';
//import { io } from 'socket.io-client';
import Card from 'react-bootstrap/Card';
import Button from 'react-bootstrap/Button';
import { createChatBotMessage } from 'react-chatbot-kit';
import { io } from 'socket.io-client';
//const socket = io('ws://localhost:5000');

const InitChatbot = (props) => {

  const [uri, setURL] = useState('');
  const [currentrole, setRole] = useState('');
  const [payload, setPayload] = useState('');
  const [airesponse, setAIResponseData] = useState('');
  const [chatresponse, setChatResponseData] = useState('');
  const [recentqueries, setHistoryData] = useState('');
  const [queryResponse, setQueryResponse] = useState('');
  const [socketInstance, setSocketInstance] = useState("");
  const [loading, setLoading] = useState(true);
  const [buttonStatus, setButtonStatus] = useState(true);
  /*const [serverMessage, setServerMessage] = useState(null);*/
  let role = "";
  let url = "";
  let len =0;
  let querybody = "";
  const user = useContext(UserContext);
  len = props.state.messages.length;
  useEffect(() => {
    console.log(props.state.messages);
    if(user.role=="Ask Doc"){
              url="/jobportal/querydoc?login=";
              setURL(url);
              role="AskDoc";
              setRole(role);
              querybody={"searchquery": props.state.messages[len-2].message,"context":props.state.messages}
              }
          else{
             url="/jobportal/aichat?login=";
             setURL(url);
             role="AIChat";
             setRole(role);
             querybody={"messages": props.state.messages }
            }

    const fetchData = async () => {
            console.log(role);
            const response = await fetch('/jobportal/recentqueries?login='+user.name+'&role='+role)
            const data = await response.json();
            console.log(data);
            setHistoryData(data.items);
        }


      //setSocketInstance(socket);



      /*return function cleanup() {
        socket.disconnect();
      };*/


        fetchData();

  }, []);
 const getQueryResponse = (query) => {
  setAIResponseData(query.answer);
 }
  return (
    <div>
    {chatresponse &&
    <div><p>{chatresponse.id}</p></div>
    }
      {recentqueries.length>0 && <div>
    <h6>Recent searches:</h6>



    {recentqueries && recentqueries.map(queryitem => (
    <Button variant="outline-primary" class="btn" onClick={() => getQueryResponse(queryitem)}>{queryitem.query}</Button>
    ))}
    </div>
    }
    {airesponse &&
      <Card style={{ width: '30rem' }}>
      <Card.Body>
       <div className="airesponse">{airesponse}</div>
      </Card.Body>
    </Card>}
    </div>


  );
};

export default InitChatbot;