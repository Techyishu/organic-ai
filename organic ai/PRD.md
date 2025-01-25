

---

### **Product Requirements Document (PRD)**

#### **Project Overview**
- **Objective**: Build a Telegram bot that helps users brainstorm creative ideas for projects (e.g., startup names, blog topics, social media content) by using the Anthropic Claude AI API. The bot should take user inputs like keywords or themes and generate creative suggestions in a conversational format.
- **Target Audience**: Entrepreneurs, content creators, and individuals seeking creative inspiration.
- **Tech Stack**:
  - Programming Language: Python
  - Database: SQLite or PostgreSQL (optional, for saving user history or analytics)
  - API Integration: Anthropic Claude AI API
  - Framework: Telegram Bot API via python-telegram-bot library
- **Dependencies**:
  - `python-telegram-bot`: To interact with Telegram's API.
  - `requests` or `httpx`: For making API calls to Anthropic.
  - Anthropic Claude AI API access.

---

#### **Features**

1. **User Input**:
   - Users can input keywords, themes, or categories for brainstorming.
   - Examples: “Startups,” “Blog topics about AI,” “Funny social media captions.”

2. **Idea Generation**:
   - The bot processes user inputs via the Anthropic Claude AI API.
   - Generates 3–5 suggestions for each input.

3. **Customizability**:
   - Users can specify the tone or style (e.g., professional, witty, creative).
   - Example: “Blog ideas, witty tone.”

4. **History Retrieval** (Optional):
   - Users can retrieve the last brainstorming session with a command like `/history`.

5. **User Feedback**:
   - Users can rate the generated ideas with commands like `/rate [1-5]`.

6. **Help Command**:
   - Provide users with instructions on how to use the bot via `/help`.

---

#### **Requirements for Each Feature**

1. **User Input**:
   - **Command**: `/brainstorm <keywords or themes>`
   - **Validation**: Ensure inputs are non-empty strings and under 200 characters.
   - **Dependencies**: Telegram Bot API.

2. **Idea Generation**:
   - **API**: Anthropic Claude AI API.
   - **Request Payload**:
     ```json
     {
       "prompt": "<formatted_prompt>",
       "max_tokens": 100,
       "temperature": 0.7
     }
     ```
   - **Response Handling**:
     - Parse API response for suggestions.
     - Format results for Telegram delivery.

3. **Customizability**:
   - **Input Parameters**: Add optional tone/style keywords after the primary input.
   - **Parsing**: Split the input string to extract keywords and style.

4. **History Retrieval**:
   - **Database**: Use SQLite or PostgreSQL to store session data.
   - **Schema**:
     ```sql
     CREATE TABLE history (
       id SERIAL PRIMARY KEY,
       user_id BIGINT,
       input TEXT,
       suggestions TEXT,
       timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     );
     ```
   - **Command**: `/history`.

5. **User Feedback**:
   - **Command**: `/rate [1-5]`.
   - **Validation**: Ensure rating is an integer between 1 and 5.

6. **Help Command**:
   - Provide a message explaining all available commands.

---

#### **Data Models**

1. **User Input Model**:
   ```python
   class UserInput:
       def __init__(self, user_id: int, keywords: str, tone: str = "creative"):
           self.user_id = user_id
           self.keywords = keywords
           self.tone = tone
   ```

2. **History Model**:
   ```python
   class History:
       def __init__(self, user_id: int, input_text: str, suggestions: list, timestamp: datetime):
           self.user_id = user_id
           self.input_text = input_text
           self.suggestions = suggestions
           self.timestamp = timestamp
   ```

---

#### **API Contract**

1. **Anthropic Claude AI API**:
   - **Endpoint**: `https://api.anthropic.com/v1/complete`
   - **Headers**:
     ```json
     {
       "Authorization": "Bearer <your_api_key>",
       "Content-Type": "application/json"
     }
     ```
   - **Payload**:
     ```json
     {
       "prompt": "Generate 5 creative ideas based on the following theme: <theme>",
       "max_tokens": 100,
       "temperature": 0.7,
       "top_p": 0.9
     }
     ```
   - **Response**:
     ```json
     {
       "completion": "1. Idea 1\n2. Idea 2\n3. Idea 3\n4. Idea 4\n5. Idea 5"
     }
     ```

2. **Telegram Bot API**:
   - **Endpoints**:
     - Send Message: `https://api.telegram.org/bot<TOKEN>/sendMessage`
     - Receive Updates: Webhook or polling.
   - **Message Format**:
     ```json
     {
       "chat_id": "<user_chat_id>",
       "text": "<response_message>",
       "parse_mode": "Markdown"
     }
     ```
