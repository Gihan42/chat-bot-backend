import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
from huggingface_hub import InferenceClient
import json

class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Chatbot")
        self.root.geometry("600x800")
        
        # Initialize Hugging Face client
        # Replace with your API key
        self.client = InferenceClient(
            api_key="your hugginface api key"
        )
        
        self.messages = []
        
        # Create main container
        self.main_container = ttk.Frame(self.root, padding="10")
        self.main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create chat display
        self.chat_display = scrolledtext.ScrolledText(
            self.main_container,
            wrap=tk.WORD,
            width=50,
            height=30
        )
        self.chat_display.grid(row=0, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        self.chat_display.config(state='disabled')
        
        # Create input field
        self.input_field = ttk.Entry(
            self.main_container,
            width=40
        )
        self.input_field.grid(row=1, column=0, pady=10, sticky=(tk.W, tk.E))
        
        # Create send button
        self.send_button = ttk.Button(
            self.main_container,
            text="Send",
            command=self.send_message
        )
        self.send_button.grid(row=1, column=1, padx=5, pady=10)
        
        # Bind Enter key to send message
        self.input_field.bind('<Return>', lambda e: self.send_message())
        
        # Configure grid weights
        self.main_container.columnconfigure(0, weight=3)
        self.main_container.columnconfigure(1, weight=1)
        
    def append_message(self, message, sender):
        """Append a message to the chat display"""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        
    def get_bot_response(self, user_message):
        """Get response from Hugging Face API"""
        try:
            messages = self.messages + [
                {"role": "user", "content": user_message}
            ]
            
            # Create the stream
            stream = self.client.chat.completions.create(
                model="meta-llama/Llama-3.2-3B-Instruct",
                messages=messages,
                max_tokens=500,
                stream=True
            )
            
            # Accumulate the response
            full_response = ""
            self.chat_display.config(state='normal')
            
            # Add a placeholder for the bot's response
            self.chat_display.insert(tk.END, "assistent: ")
            
            # Stream the response
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    self.chat_display.insert(tk.END, content)
                    self.chat_display.see(tk.END)
            
            self.chat_display.insert(tk.END, "\n\n")
            self.chat_display.config(state='disabled')
            
            # Update messages history
            self.messages.append({"role": "user", "content": user_message})
            self.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            self.append_message(f"Error: {str(e)}", "System")
    
    def send_message(self):
        """Handle sending a message"""
        message = self.input_field.get().strip()
        if message:
            # Clear input field
            self.input_field.delete(0, tk.END)
            
            # Display user message
            self.append_message(message, "You")
            
            # Get bot response in a separate thread
            threading.Thread(
                target=self.get_bot_response,
                args=(message,),
                daemon=True
            ).start()

def main():
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()