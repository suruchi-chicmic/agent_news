import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Local Imports
from state import AgentState
from tools.news_tool import fetch_news
from rag import archive_summary, query_archive, get_all_history_topics

load_dotenv()
from langchain_community.chat_models import ChatOllama
llm = ChatOllama(model="llama3")

# --- NODES ---

def analyzer(state: AgentState):
    """
    1. ANALYZER NODE:
    Analyzes the user's intent using an LLM. 
    It classifies the query into one of three 'DECISIONS':
    - 'search': Triggered if the user wants NEW information from Google News.
    - 'history': Triggered if the user asks about past topics or what they've asked before.
    - 'direct': Triggered for standard chat, greetings, or general knowledge (math, date).
    """
    messages = state["messages"]
    last_message = messages[-1].content
    
    prompt = f"""
    Analyze the LATEST user message in the context of the conversation history.
    
    LATEST MESSAGE: "{last_message}"
    
    GUIDELINES:
    1. PRIORITIZE LATEST INTENT: If the latest message is just a greeting (hi), bye, gratitude (thanks, thank you , ok), or closing (bye, that's it), the DECISION MUST be 'direct'. 
       - In this case, KEYWORDS MUST be empty output. 
       - Do NOT carry over previous search keywords if the user is just saying thanks or bye.
    
    2. Resolve Pronouns: If the latest message is a follow-up query using "he", "it", etc., resolve it using history (e.g., "what is he doing?" -> "economic activities of UAE PM") last question ,if you would not understand what the user is referring to then ask him to be more specific.
    
    3. Decide DECISION:
       - 'history': asking about past topics/conversations.
       - 'search': factual questions or news requests.
       - 'direct': greetings, gratitude, math, or small talk.
    
    4. Correct Typos: Fix spelling in KEYWORDS (e.g., "Duabi" -> "Dubai").
    
    Format output EXACTLY as:
    DECISION: [decision]
    KEYWORDS: [resolved keywords or none]
    COUNTRY: [2-letter code or none]
    CATEGORY: [news category or none]
    """
    today = datetime.now().strftime("%A, %B %d, %Y")
    response = llm.invoke([SystemMessage(content=f"You are a precise analyzer. Today is {today}.")] + state["messages"] + [HumanMessage(content=prompt)])
    parsed = {}
    for line in response.content.strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            parsed[key.strip().lower()] = val.strip().lower()

    return {
        "query": parsed.get("keywords", last_message),
        "decision": parsed.get("decision", "search"),
        "country": parsed.get("country") if parsed.get("country") != "none" else None,
        "category": parsed.get("category") if parsed.get("category") != "none" else None
    }

def searcher(state: AgentState):
    """
    2. SEARCHER NODE:
    Called only if DECISION is 'search'.
    Communicates with the News API/Google RSS tool to fetch 10 articles.
    """
    print(f"--- SEARCHING: {state['query']} ---")
    res = fetch_news(state['query'], country=state['country'], category=state['category'])
    return {"search_results": res if isinstance(res, list) else []}

def archive_retriever(state: AgentState):
    """
    3. ARCHIVE RETRIEVER NODE:
    Called only if DECISION is 'history'.
    Queries the local ChromaDB for past news summaries or the list of topics.
    """
    user_query = state["messages"][-1].content.lower()
    decision = state.get("decision", "")
    print(f"--- RETRIEVING FROM HISTORY (Decision: {decision}) ---")
    
    # If the LLM explicitly decided 'history' or if the query looks like a meta-question about past queries
    if decision == "history" or any(word in user_query for word in ["what", "tell", "show", "list", "my", "queries", "asked"]):
        return {"summary": f"Your past search topics include: {get_all_history_topics()}"}
    
    past = query_archive(user_query)
    text = "\n".join(past) if past else "I couldn't find any specific past results for that query."
    return {"summary": text, "messages": [AIMessage(content=text)]}

def summarizer(state: AgentState):
    """
    4. SUMMARIZER NODE:
    Called after 'searcher' to process the raw news results.
    Condenses the articles into a readable response for the user.
    """
    print("--- SUMMARIZING ---")
    today = datetime.now().strftime("%A, %B %d, %Y")
    user_query = state["messages"][-1].content
    articles_context = "\n".join([f"Title: {r['title']}\nDescription: {r['description']}" for r in state['search_results']])
    
    system_prompt = f"""
    You are an expert news analyst. Today is {today}.
    
    TASK:
    1. Read the provided news articles context.
    2. FIRST, provide a direct and concise answer to the user's specific question. 
       - If the articles mention the fact (e.g., who the PM is), use that. 
       - If the articles are related but don't explicitly state the basic fact, use your internal knowledge to provide the direct answer first.
    3. THEN, provide exactly the number of news highlights requested by the user (e.g., if the user asked for "top 2", provide exactly 2). If no number is specified, provide the top 4-5 relevant highlights.
    4. If the answer is completely unavailable even via internal knowledge, say so and provide the requested number of related news highlights.
    5. Be professional and helpful. Avoid just listing articles; synthesize the information into a cohesive narrative.
    """
    
    human_prompt = f"""
    User Question: "{user_query}"
    
    News Articles Context:
    {articles_context}
    
    Response:
    """
    response = llm.invoke([SystemMessage(content=system_prompt)] + [HumanMessage(content=human_prompt)])
    return {"summary": response.content, "messages": [AIMessage(content=response.content)]}


def chatbot(state: AgentState):
    """
    5. CHATBOT NODE:
    Called only if DECISION is 'direct'.
    Handles casual conversation, math, and identity.
    REFINED: Focuses only on the latest query to avoid repetitive history.
    """
    print("--- CHATTING DIRECTLY ---")
    today = datetime.now().strftime("%A, %B %d, %Y")
    system_msg = f"""
    You are a professional and helpful News Agent.
    Current Date: {today}.
    
    GUIDELINES:
    1. Do NOT recap or summarize the entire previous conversation unless explicitly asked.
    2. Focus your response ONLY on the user's latest message.
    3. Your identity is "News Agent". Do NOT call yourself Rohan or any other name unless the user tells you their name.
    4. If the user tells you their name, acknowledge it naturally.
    
    "IMPORTANT: Only answer the user's LATEST question. "
    "Do not repeat previous answers or summarize the whole history unless specifically asked to do so. "
    "Keep your response concise and focused on the current message."
    
    CAUTION: If a user asks a factual question (e.g., about a person or event or TV shows) and you are not 100% certain, or if it's the kind of information that changes, suggest that the user ask you to 'search' for it instead of providing potentially outdated info. 
    (Context:  (Amitabh Bachchan) is the primarily known host of KBC, although Shah Rukh Khan hosted Season 3).

    """
    response = llm.invoke([SystemMessage(content=system_msg)] + state["messages"])
    return {"summary": response.content, "messages": [AIMessage(content=response.content)]}

def archiver(state: AgentState):
    """
    6. ARCHIVER NODE:
    Called after 'summarizer' to save the result into ChromaDB for future 'history' retrieval.
    """
    if state["summary"] and "asked about" not in state["summary"]:
        archive_summary(state["query"], state["summary"])
    return {"archived": True}

# --- ROUTER ---

def router(state: AgentState):
    decision = state.get("decision", "search")
    if "history" in decision: return "archive_retriever"
    
    if "direct" in decision: return "chatbot"
    return "searcher"

# --- GRAPH ---

workflow = StateGraph(AgentState)
workflow.add_node("analyzer", analyzer)
workflow.add_node("searcher", searcher)
workflow.add_node("archive_retriever", archive_retriever)
workflow.add_node("summarizer", summarizer)
workflow.add_node("chatbot", chatbot)
workflow.add_node("archiver", archiver)

workflow.set_entry_point("analyzer")
workflow.add_conditional_edges("analyzer", router, {
    "archive_retriever": "archive_retriever",
    "searcher": "searcher",
    "chatbot": "chatbot"
})

workflow.add_edge("searcher", "summarizer")
workflow.add_edge("summarizer", "archiver")
workflow.add_edge("archiver", END)
workflow.add_edge("archive_retriever", END)
workflow.add_edge("chatbot", END)

app = workflow.compile(checkpointer=MemorySaver())

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "user_session_1"}}
    print("News Agent Active! (Type 'exit' to quit)")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit": break
        
        for output in app.stream({"messages": [HumanMessage(content=user_input)]}, config=config):
            for key, value in output.items():
                if "summary" in value:
                    print(f"\nAgent: {value['summary']}")