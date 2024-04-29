import requests
import json

class OpenAIChat:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.conversation_history = [
            {
                "role": "system",
                "content": "You are a technical interviewer. A user will send you his introduction and you will ask him technical questions. You will ask 1 question at a time based on the user input."
            }
        ]

    def call_openai(self):
        data = {
            "model": "gpt-3.5-turbo",  
            "messages": self.conversation_history,
            "temperature": 0.7,
            "max_tokens": 60
        }

        response = requests.post(self.url, headers=self.headers, data=json.dumps(data))

        if response.status_code == 200:
            response_json = response.json()
            generated_message = response_json['choices'][0]['message']['content']
            self.conversation_history.append({
                "role": "assistant",
                "content": generated_message.strip()
            })
            # print("Generated text:", )
            return generated_message.strip()
        else:
            print("Failed to call OpenAI API:", response.json())
            return None

    def add_user_message(self, message):
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

# # Example usage:
# api_key = ""
# openai_chat = OpenAIChat(api_key)
# openai_chat.call_openai()

# user_message = "Could you ask me a question about Java?"
# openai_chat.add_user_message(user_message)
# openai_chat.call_openai()
