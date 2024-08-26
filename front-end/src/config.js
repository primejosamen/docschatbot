import { createChatBotMessage,createCustomMessage } from 'react-chatbot-kit';
import { useContext} from 'react';
import ChatResponse from './ChatResponse';
import AIChatResponse from './AIChatResponse';
import InitChatbot from './InitChatbot';
import UserContext from './user-context';
import WelcomeMessage from './WelcomeChatMessage';
const config = {
  botName: "DocsQuery Bot",

  initialMessages: [createCustomMessage('Test', 'custom'),createChatBotMessage(`Hi, I am your personalized DocsQuery Agent. What do you want to learn?`,
      {
      widget: "InitChatbot",
    }
    )],
  floating: true,
  customMessages: {
    custom: (props) => <WelcomeMessage {...props} />,
  },
  widgets: [
    {
      widgetName: 'chatResponse',
      widgetFunc: (props) => <ChatResponse {...props} />,
    },
    {
      widgetName: 'aiChatResponse',
      widgetFunc: (props) => <AIChatResponse {...props} />,
    },
    {
      widgetName: 'InitChatbot',
      widgetFunc: (props) => <InitChatbot {...props} />,
    }
  ],
}

export default config