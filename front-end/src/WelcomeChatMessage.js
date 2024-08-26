import React,{useContext} from 'react';
import { createChatBotMessage,createCustomMessage } from 'react-chatbot-kit';
import UserContext from './user-context';

const WelcomeChatMessage = () => {
const user = useContext(UserContext);
  return (
    <div><p>Hi {user.name}</p></div>
  );
};

export default WelcomeChatMessage;