# Bank AI Assistant

A sophisticated conversational AI banking assistant built with React and FastAPI, powered by Google's Gemini AI. The system uses a multi-step prompt chain architecture to intelligently categorize, process, and resolve customer banking inquiries.

![Bank AI Assistant](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-blue)
![React](https://img.shields.io/badge/React-19.2.0-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)

## 🌟 Features

### Intelligent Conversation Flow
- **Multi-Step Prompt Chain**: Processes customer queries through a sophisticated 5-step pipeline
- **Context-Aware**: Maintains full conversation history to avoid repetitive questions
- **Smart Categorization**: Automatically classifies requests into 8 banking categories
- **Progressive Information Gathering**: Intelligently extracts required details across multiple turns

### Banking Categories Supported
- Account Opening
- Billing Issue
- Account Access
- Transaction Inquiry
- Card Services
- Account Statement
- Loan Inquiry
- General Information

### User Experience
- **Beautiful Modern UI**: Gradient-themed chat interface with smooth animations
- **Real-time Typing Indicators**: Visual feedback during AI processing
- **Message Timestamps**: Track conversation flow
- **Session Management**: Persistent conversations with reset capability
- **Mobile Responsive**: Optimized for all screen sizes
- **Error Handling**: Graceful error messages with retry mechanisms

## 🏗️ Architecture

### Frontend (React + Vite)
```
frontend/
├── src/
│   ├── components/
│   │   ├── MainContent.jsx      # Main chat interface
│   │   └── MainContent.css      # Styling
│   ├── App.jsx                  # Root component
│   └── main.jsx                 # Entry point
├── index.html
└── vite.config.js
```

### Backend (FastAPI + Google Gemini)
```
backend/
├── app.py                       # Main API application
├── requirements.txt
└── .env                         # Environment variables
```

### Key Backend Components

#### `AiAssistant`
Manages communication with Google's Gemini 2.5 Flash Lite model with optimized generation parameters.

#### `PromptChainProcessor`
Implements the 5-step prompt chain:
1. **Intent Interpretation**: Understands customer's needs
2. **Category Suggestion**: Identifies potential categories
3. **Category Selection**: Chooses the most appropriate category
4. **Detail Extraction**: Progressively gathers required information
5. **Response Generation**: Creates professional, helpful responses

#### `SessionState`
Maintains conversation context including:
- Message history
- Extracted data
- Selected category
- Conversation flow state

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+
- Google Gemini API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Anyadiegwu/bank-ai-react-assistant
cd bank-ai-assistant
```

2. **Set up the backend**
```bash
cd backend
pip install -r requirements.txt
```

3. **Configure environment variables**
Create a `.env` file in the `backend` directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

4. **Set up the frontend**
```bash
cd frontend
npm install
```

### Running Locally

#### Development Mode
```bash
# From root directory
npm run dev
```

This runs both frontend (http://localhost:5173) and backend (http://localhost:8000) concurrently.

#### Or run separately:

**Backend:**
```bash
cd backend
python -m uvicorn app:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## 🌐 Deployment

### Current Deployment Setup
- **Frontend**: Deployed on Vercel
- **Backend**: Deployed on Render (free tier)

### ⚠️ Important: Render Free Tier Behavior

**Cold Start Delays**: The application uses Render's free web service tier for the backend, which has important limitations:

1. **Automatic Sleep**: After 15 minutes of inactivity, the service spins down
2. **First Request Delay**: When the service is inactive, the **first request after waking up can take 50+ seconds**
3. **Subsequent Requests**: Normal response time after the initial wake-up

**User Experience Impact**:
- ✅ After the service is active: Fast, real-time responses
- ⏳ First use after inactivity: Long initial loading time (50+ seconds)
- 💡 **Tip**: The service stays active for 15 minutes after the last request

**What Users Will See**:
```
Initial connection: "Connecting..." (may take up to 1 minute)
After wake-up: Instant responses
```

**For Production Use**: Consider upgrading to a paid tier on Render or use alternative hosting (Railway, Fly.io, AWS, etc.) to eliminate cold starts.

### Deploy Your Own

#### Backend (Render)
1. Create a new Web Service on [Render](https://render.com)
2. Connect your repository
3. Configure:
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && python -m uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: Add `GEMINI_API_KEY`

#### Frontend (Vercel)
1. Import project to [Vercel](https://vercel.com)
2. Configure build settings:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

The `vercel.json` configuration handles routing between frontend and backend.

## 📡 API Endpoints

### Chat
```http
POST /api/chat
Content-Type: application/json

{
  "message": "I want to open a new account",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "response": "AI response text",
  "timestamp": "ISO-8601 timestamp",
  "intermediate_outputs": {
    "intent": "...",
    "categories": "...",
    "selected_category": "...",
    "extraction": "..."
  }
}
```

### Session Management

#### Create New Session
```http
POST /api/session/new
```

#### Get Session Info
```http
GET /api/session/{session_id}/info
```

#### Delete Session
```http
DELETE /api/session/{session_id}
```

#### List All Sessions
```http
GET /api/sessions
```

## 🎨 Customization

### Modify Banking Categories
Edit the `CATEGORIES` constant in `backend/app.py`:
```python
CATEGORIES = """
- Your Custom Category
- Another Category
...
"""
```

### Adjust AI Behavior
Modify generation config in `AiAssistant.__init__`:
```python
generation_config={
    'temperature': 0.1,      # Lower = more focused
    'top_p': 0.95,
    'top_k': 40,
    'max_output_tokens': 8192,
}
```

### Update UI Theme
Edit CSS variables in `frontend/src/components/MainContent.css`:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

## 🔒 Security Considerations

- **API Keys**: Never commit `.env` files. Use environment variables in production
- **CORS**: Currently configured for specific origins. Update in `app.py` for production
- **Session Management**: Implement session expiry for production use
- **Rate Limiting**: Consider adding rate limiting for API endpoints

## 🐛 Troubleshooting

### "Failed to connect to the server"
- Ensure backend is running on port 8000
- Check `API_URL` in `MainContent.jsx` matches your backend URL
- Verify CORS settings allow your frontend origin

### Long Response Times (Render Free Tier)
- **Expected on first request** after 15+ minutes of inactivity
- Service will respond quickly once warmed up
- Consider keeping service active or upgrading hosting

### "GEMINI_API_KEY not found"
- Create `.env` file in backend directory
- Add your API key: `GEMINI_API_KEY=your_key_here`
- Restart the backend server

## 📈 Future Enhancements

- [ ] Add authentication and user accounts
- [ ] Implement database for persistent conversation history
- [ ] Add voice input/output capabilities
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Integration with real banking APIs
- [ ] Export conversation transcripts
- [ ] Custom training on bank-specific FAQs

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 💬 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review API documentation

---

**Note**: This is a demonstration application. For production banking applications, ensure compliance with financial regulations, implement proper security measures, and thoroughly test all functionality.