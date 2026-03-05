# AI News Agent

A powerful, context-aware AI agent that fetches, summarizes, and archives news from Google News RSS feeds.

## Features

- **Context-Aware Analytics**: Resolves pronouns (he/him, it) using conversation history.
- **Dynamic Routing**: Automatically decides between searching news, retrieving from history, or chatting directly.
- **Persistent Archive**: Uses ChromaDB to store and retrieve past news summaries.
- **Identity & Persona**: Acts as a professional "News Agent" with a consistent identity.
- **Quantity Precision**: Strictly follows user requests for the number of headlines (e.g., "top 2").

## Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd "Agent Trial"
   ```

2. **Setup Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file with your API keys (if applicable).

## Usage

Run the agent:
```bash
python news_agent/main.py
```

## Project Structure

- `news_agent/main.py`: Core logic and LangGraph implementation.
- `news_agent/rag.py`: Persistent storage and RAG logic.
- `news_agent/state.py`: Graph state definition.
- `news_agent/tools/news_tool.py`: News fetching utility.
