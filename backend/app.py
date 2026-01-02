import os
import re
import json
import uuid
from typing import Dict, Optional
from datetime import datetime

import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Bank AI Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bank-ai-react-assistant.vercel.app","http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, 'SessionState'] = {}


class AiAssistant:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash-lite',
            generation_config={
                'temperature': 0.3,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 8192,
            }
        )

    def call_with_prompt(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error calling AI: {str(e)}")
            return f"Error: {str(e)}"


class SessionState:
    def __init__(self):
        self.data = {}
        self.messages = []
    
    def __contains__(self, key):
        return key in self.data
    
    def __getattr__(self, key):
        if key in ['data', 'messages']:
            return self.__dict__[key]
        return self.data.get(key)
    
    def __setattr__(self, key, value):
        if key in ['data', 'messages']:
            self.__dict__[key] = value
        else:
            if 'data' not in self.__dict__:
                self.__dict__['data'] = {}
            self.data[key] = value


class PromptChainProcessor:
    CATEGORIES = """
- Account Opening
- Billing Issue
- Account Access
- Transaction Inquiry
- Card Services
- Account Statement
- Loan Inquiry
- General Information
"""
    
    def __init__(self, ai_assistant: AiAssistant):
        self.ai = ai_assistant
    
    def step1_interpret_intent(self, user_input: str) -> str:
        prompt = f"""You are a Bank Assistant. Interpret the customer's intent clearly and concisely.
Customer message: {user_input}
Provide a clear interpretation of what the customer wants or needs. Be specific and professional."""
        return self.ai.call_with_prompt(prompt)
    
    def step2_suggest_categories(self, interpreted_message: str) -> str:
        prompt = f"""Map the query to one or more possible categories that may apply.
Available Categories:
{self.CATEGORIES}

Interpreted customer request: 
{interpreted_message}

Return the suggested categories (one or more) that best match this request. Format: list the category names."""
        return self.ai.call_with_prompt(prompt)
    
    def step3_select_category(self, interpreted_message: str, suggested_categories: str) -> str:
        prompt = f"""Select the MOST appropriate single category from the suggestions.

Suggested Categories:
{suggested_categories}

Interpreted customer request:
{interpreted_message}

Return ONLY the single most appropriate category name, nothing else."""
        return self.ai.call_with_prompt(prompt)
    
    def step4_extract_details(self, interpreted_message: str, user_input: str, 
                             selected_category: str, context_data: dict) -> str:
        collected_info = json.dumps(context_data, indent=2) if context_data else "None yet"     
        prompt = f"""You are handling a banking request. Based on the category and information collected so far, determine what's needed next.

Selected Category: {selected_category}

Customer's original message: {user_input}

Interpreted intent: {interpreted_message}

Information already collected: 
{collected_info}

Task: 
1. If you need more information to process this request, ask ONE specific follow-up question
2. If you have enough information, acknowledge this and prepare to resolve the request
3. Extract any new details from the customer's message

Return your response in this JSON format:
{{
    "status": "needs_info" or "ready_to_resolve",
    "extracted_data": {{"key": "value"}},
    "follow_up_question": "your question here" or null,
    "response_to_user": "friendly message to the customer"
}}"""
        return self.ai.call_with_prompt(prompt)
    
    def step5_generate_response(self, selected_category: str, context_data: dict) -> str:
        collected_info = json.dumps(context_data, indent=2)     
        prompt = f"""You are a professional banking assistant. Generate a helpful, friendly response to satisfy the customer.

Request Category: {selected_category}

Collected Information:
{collected_info}

Generate a concise, professional response that:
1. Confirms what action you're taking or what information you're providing
2. Addresses the customer's needs based on the category
3. Is warm and reassuring
4. Ends with an offer to help further if needed

Keep it short and natural."""
        return self.ai.call_with_prompt(prompt)


def run_prompt_chain(customer_query: str, session_state: SessionState) -> tuple:
    user_input = customer_query.strip()
    if not user_input:
        return ("Error: Empty input", None, None, None, None)

    if not hasattr(session_state, 'history') or session_state.history is None:
        session_state.history = []
    
    session_state.history.append(user_input)   
    full_history = "\n".join(session_state.history)
    
    intermediate_outputs = []

    if not hasattr(session_state, 'interpreted_message') or session_state.interpreted_message is None:
        interpreted = session_state.processor.step1_interpret_intent(user_input)
        session_state.interpreted_message = interpreted
    else:
        interpreted = session_state.interpreted_message
    intermediate_outputs.append(interpreted)

    if not hasattr(session_state, 'suggested_categories') or session_state.suggested_categories is None:
        suggested_categories = session_state.processor.step2_suggest_categories(interpreted)
        session_state.suggested_categories = suggested_categories
    else:
        suggested_categories = session_state.suggested_categories
    intermediate_outputs.append(suggested_categories)

    if not hasattr(session_state, 'category') or session_state.category is None:
        selected_category = session_state.processor.step3_select_category(interpreted, suggested_categories)
        if not selected_category:
            return ("Error: Failed to select category", None, None, None, None)
        
        session_state.category = selected_category
        session_state.context_data = {}
    else:
        selected_category = session_state.category
    intermediate_outputs.append(selected_category)

    extraction_result = session_state.processor.step4_extract_details(
        interpreted,
        full_history,  
        session_state.category,
        session_state.context_data
    )   
    if not extraction_result:
        return (*intermediate_outputs, "Error: Failed to process request", None)
    
    intermediate_outputs.append(extraction_result)

    match = re.search(r'\{.*\}', extraction_result, re.DOTALL)
    final_response = None
    
    if match:
        try:
            response_data = json.loads(match.group())         
            if 'extracted_data' in response_data and response_data['extracted_data']:
                session_state.context_data.update(response_data['extracted_data'])
            
            if response_data.get('status') == 'ready_to_resolve':
                final_response = session_state.processor.step5_generate_response(
                    session_state.category,
                    session_state.context_data
                )
                if not final_response:
                    final_response = response_data.get('response_to_user', 'Your request has been processed.')
            else:
                final_response = response_data.get('response_to_user', 'Could you provide more details?')
        except json.JSONDecodeError:
            final_response = extraction_result
    else:
        final_response = extraction_result
    
    intermediate_outputs.append(final_response)
    
    return tuple(intermediate_outputs)


def initialize_session() -> SessionState:
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    session_state = SessionState()
    session_state.ai_assistant = AiAssistant(gemini_api_key)
    session_state.processor = PromptChainProcessor(session_state.ai_assistant)
    session_state.messages = [
        {
            "role": "assistant", 
            "content": "Hello! I'm your banking assistant. How can I help you today?",
            "timestamp": datetime.now().isoformat()
        }
    ]   
    session_state.history = []
    session_state.interpreted_message = None
    session_state.suggested_categories = None
    session_state.category = None
    session_state.context_data = {}
    
    return session_state


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    timestamp: str
    intermediate_outputs: Optional[dict] = None


class SessionInfo(BaseModel):
    session_id: str
    message_count: int
    category: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Bank AI Assistant API", "version": "1.0.0", "status": "running"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        print(f"Received chat request: {request.message[:50]}...")

        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in sessions:
            print(f"Creating new session: {session_id}")
            sessions[session_id] = initialize_session()
        
        session = sessions[session_id]

        session.messages.append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        })
        
        print("Processing with prompt chain...")
        intermediate_outputs = run_prompt_chain(request.message, session)
        
        final_response = intermediate_outputs[-1] if intermediate_outputs else "Error processing request"
        print(f"Generated response: {final_response[:50]}...")

        session.messages.append({
            "role": "assistant",
            "content": final_response,
            "timestamp": datetime.now().isoformat()
        })

        intermediate_dict = {
            "intent": intermediate_outputs[0] if len(intermediate_outputs) > 0 else None,
            "categories": intermediate_outputs[1] if len(intermediate_outputs) > 1 else None,
            "selected_category": intermediate_outputs[2] if len(intermediate_outputs) > 2 else None,
            "extraction": str(intermediate_outputs[3])[:200] if len(intermediate_outputs) > 3 else None,
        }
        
        return ChatResponse(
            session_id=session_id,
            response=final_response,
            timestamp=datetime.now().isoformat(),
            intermediate_outputs=intermediate_dict
        )
    
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session/new")
async def create_session():
    """Create a new session"""
    try:
        print("Creating new session...")
        session_id = str(uuid.uuid4())
        sessions[session_id] = initialize_session()
        
        print(f"Session created: {session_id}")
        return {
            "session_id": session_id,
            "message": "New session created",
            "initial_message": sessions[session_id].messages[0]["content"]
        }
    except Exception as e:
        print(f"Error creating session: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}/info", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get session information"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    return SessionInfo(
        session_id=session_id,
        message_count=len(session.messages),
        category=session.category if hasattr(session, 'category') else None
    )


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session deleted"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions"""
    return {
        "active_sessions": len(sessions),
        "session_ids": list(sessions.keys())
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting Bank AI Assistant API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)