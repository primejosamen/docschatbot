class MessageParser {
  constructor(actionProvider) {
    this.actionProvider = actionProvider;
  }

  parse(message) {
    const lowerCaseMessage = message.toLowerCase()
    if (lowerCaseMessage.includes("hello")) {
      this.actionProvider.handleAsyncalls()
    }
    else {
      this.actionProvider.handleAICalls(message)
    }
  }
}

export default MessageParser