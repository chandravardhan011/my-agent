from flask import Flask, render_template, request, jsonify
from groq import Groq
from duckduckgo_search import DDGS
import time

app = Flask(__name__)
client = Groq(api_key="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")

SYSTEM_PROMPT = """Your name is AVR. You are a powerful AI assistant like ChatGPT.
If anyone asks your name, say I am AVR, your personal AI Assistant!
Help with all subjects, coding, math, writing, translation, news, career advice."""

chat_history = []

def web_search(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        return "\n".join([f"{r['title']}: {r['body']}" for r in results])
    except:
        return "Search failed"

def run_agent(question):
    global chat_history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += chat_history
    messages.append({"role": "user", "content": question})

    for _ in range(5):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=2048,
                temperature=0.7
            )
        except Exception as e:
            if "429" in str(e):
                time.sleep(10)
                continue
            return f"Error: {str(e)}"

        reply = response.choices[0].message.content

        if "SEARCH:" in reply:
            query = reply.split("SEARCH:")[1].strip().split("\n")[0]
            result = web_search(query)
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": f"Search results: {result}. Now answer."})
        else:
            chat_history.append({"role": "user", "content": question})
            chat_history.append({"role": "assistant", "content": reply})
            if len(chat_history) > 20:
                chat_history = chat_history[-20:]
            return reply

    return "Could not find answer. Try again."

@app.route("/")
def home():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>AVR - AI Assistant</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: white; height: 100vh; display: flex; flex-direction: column; }
        
        .header { background: #16213e; padding: 15px; text-align: center; border-bottom: 2px solid #0f3460; }
        .header h1 { color: #00d4ff; font-size: 24px; }
        .header p { color: #888; font-size: 12px; }
        
        .chat-box { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        
        .message { max-width: 80%; padding: 12px 16px; border-radius: 15px; line-height: 1.5; white-space: pre-wrap; }
        .user-msg { background: #0f3460; align-self: flex-end; border-bottom-right-radius: 3px; }
        .avr-msg { background: #16213e; border: 1px solid #0f3460; align-self: flex-start; border-bottom-left-radius: 3px; }
        .avr-label { color: #00d4ff; font-weight: bold; font-size: 12px; margin-bottom: 5px; }
        
        .input-area { background: #16213e; padding: 15px; border-top: 2px solid #0f3460; display: flex; gap: 10px; }
        .input-area input { flex: 1; padding: 12px; border-radius: 25px; border: 1px solid #0f3460; background: #1a1a2e; color: white; font-size: 15px; outline: none; }
        .input-area input:focus { border-color: #00d4ff; }
        .input-area button { padding: 12px 25px; border-radius: 25px; border: none; background: #00d4ff; color: #1a1a2e; font-weight: bold; cursor: pointer; font-size: 15px; }
        .input-area button:hover { background: #00a8cc; }
        
        .typing { color: #00d4ff; font-style: italic; padding: 10px; }
        
        .clear-btn { background: none; border: 1px solid #ff4757; color: #ff4757; padding: 5px 15px; border-radius: 15px; cursor: pointer; font-size: 12px; }
        .clear-btn:hover { background: #ff4757; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AVR - AI Assistant</h1>
        <p>Powered by Llama 3.3 | Ask me anything!</p>
        <br>
        <button class="clear-btn" onclick="clearChat()">🔄 Clear Chat</button>
    </div>
    
    <div class="chat-box" id="chatBox">
        <div class="message avr-msg">
            <div class="avr-label">🤖 AVR</div>
            Hello! I am AVR, your personal AI Assistant! 👋<br><br>
            I can help you with:<br>
            📚 All Subjects | 💻 Coding | 🧮 Math<br>
            ✍️ Writing | 🌍 Translation | 🌐 Latest News<br><br>
            What can I help you with today?
        </div>
    </div>
    
    <div class="input-area">
        <input type="text" id="userInput" placeholder="Ask AVR anything..." onkeypress="handleKey(event)">
        <button onclick="sendMessage()">Send ➤</button>
    </div>

    <script>
        function handleKey(e) {
            if (e.key === "Enter") sendMessage();
        }

        async function sendMessage() {
            const input = document.getElementById("userInput");
            const chatBox = document.getElementById("chatBox");
            const question = input.value.trim();
            if (!question) return;

            // Show user message
            chatBox.innerHTML += `<div class="message user-msg">${question}</div>`;
            input.value = "";
            chatBox.scrollTop = chatBox.scrollHeight;

            // Show typing
            chatBox.innerHTML += `<div class="typing" id="typing">🤖 AVR is thinking...</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const response = await fetch("/chat", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({message: question})
                });
                const data = await response.json();

                document.getElementById("typing").remove();
                chatBox.innerHTML += `
                    <div class="message avr-msg">
                        <div class="avr-label">🤖 AVR</div>
                        ${data.reply.replace(/\\n/g, "<br>")}
                    </div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            } catch(e) {
                document.getElementById("typing").remove();
                chatBox.innerHTML += `<div class="message avr-msg">❌ Error. Try again.</div>`;
            }
        }

        async function clearChat() {
            await fetch("/clear", {method: "POST"});
            document.getElementById("chatBox").innerHTML = `
                <div class="message avr-msg">
                    <div class="avr-label">🤖 AVR</div>
                    Chat cleared! How can I help you? 😊
                </div>`;
        }
    </script>
</body>
</html>
    '''

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    question = data.get("message", "")
    reply = run_agent(question)
    return jsonify({"reply": reply})

@app.route("/clear", methods=["POST"])
def clear():
    global chat_history
    chat_history = []
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    print("🤖 AVR is ALIVE at http://localhost:5000")
    app.run(debug=False, port=5000)
