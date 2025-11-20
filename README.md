# 🚀 Trade Assistant RAG Chatbot

AI-powered Trade Assistant for comprehensive import-export guidance with multimodal capabilities and .NET iframe integration. Covers DGFT policies, customs procedures, trade regulations, and more.

## 📋 Features

- **🧠 RAG-based Question Answering** - Intelligent responses from comprehensive trade documentation
- **🖼️ Multimodal Support** - Text and image analysis from DOCX files  
- **🔐 Authentication Integration** - Works with .NET websites via iframe
- **🔍 Vector Search** - Advanced document retrieval using ChromaDB
- **⚡ OpenAI Integration** - GPT-4 for natural language responses
- **📊 Comprehensive Testing** - 46+ test cases covering all components
- **🎯 FAQ Mode** - Fallback for unauthenticated users
- **📚 Multiple Trade Topics** - DGFT, Customs, Export-Import procedures, and more

## 📋 Trade Topics Covered

### 🏛️ **DGFT (Directorate General of Foreign Trade)**
- Import Export Code (IEC) procedures
- Export promotion schemes (EPCG, Advance Authorization)
- SEIS, Drawback, RoDTEP, ROSCTL policies
- Export house certification
- Foreign trade policy compliance

### 🛃 **Customs & Duty Management**
- Custom duty calculations and exemptions
- HSN classification procedures
- Warehousing and factory stuffing
- AEO certification processes
- Risk Management System (RMS)

### 📤 **Export Procedures**
- Export clearance and documentation
- Merchant export procedures
- Physical, deemed, and third-party exports
- Re-export and high sea sales
- Export incentive schemes

### 📥 **Import Procedures**
- Import clearance and documentation
- Second-hand goods import
- Baggage imports and personal imports
- Re-import procedures
- Import monitoring and compliance

### 🌐 **International Trade**
- Free Trade Agreements (FTA) and WTO
- Trade policy and regulatory compliance
- Foreign trade consulting
- International compliance requirements

### 📊 **Specialized Services**
- Custom valuation and representation
- Bond and LUT management
- Detention and demurrage handling
- ICD & CFS operations
- Transportation and consolidation
- ✅ **Complete RAG Pipeline** with vector database
- ✅ **Advanced User Analytics** and behavior analysis

## ✨ Key Features

### 🧠 **Proactive AI Capabilities**
- **Smart User Behavior Analysis** - Learns user patterns, expertise levels, and preferences
- **Context-Aware Follow-ups** - Generates intelligent suggestions based on conversation flow
- **Stuck Detection Algorithm** - Proactively identifies when users need assistance
- **Adaptive Response Generation** - Tailors responses based on user history and patterns
- **Conversation Flow Management** - Maintains context across multi-turn conversations

### 🔍 **Advanced RAG Pipeline**
- **DGFT Document Integration** - 53+ DGFT trade documents automatically processed
- **Vector Database** - ChromaDB with OpenAI embeddings for semantic search
- **Intelligent Reranking** - Advanced reranking algorithms for optimal result ordering
- **Dynamic Prompt Building** - Context-aware prompt construction with retrieved information
- **Multi-source Aggregation** - Combines information from multiple sources intelligently

### 🎨 **Modern React Frontend**
- **Real-time Chat Interface** - Modern, responsive design with message bubbles
- **Document Preview** - Click source citations to preview document content
- **Proactive Suggestions** - Visual display of AI-generated follow-up questions
- **Mobile Responsive** - Works seamlessly on desktop and mobile devices
- **Iframe Embedding** - Ready for integration into existing systems

### 🔐 **Authentication & Security**
- **JWT Authentication** - Secure token-based authentication system
- **Subscription Tiers** - Ready for premium feature management (commented out)
- **API Key Management** - Secure OpenAI API key handling
- **CORS Configuration** - Proper cross-origin request handling

### 📊 **Comprehensive Analytics**
- **Usage Tracking** - Detailed interaction logging and analytics
- **Performance Monitoring** - Response times, token usage, and system metrics
- **User Pattern Analysis** - Behavioral insights and usage statistics
- **Feedback Learning** - Continuous improvement through user feedback

## 🏗️ **Complete Architecture**

```
Final Chatbot/
├── 🚀 api/                          # ChatGPT-like Backend
│   ├── app.py                       # FastAPI app with frontend serving
│   ├── config.py                    # Configuration management
│   ├── auth.py                      # JWT authentication system
│   ├── schemas.py                   # Pydantic data models
│   ├── routers/                     # API route handlers
│   │   ├── ask_router.py            # Main chat with proactive features
│   │   ├── health_router.py         # Health check endpoints
│   │   ├── usage_router.py          # Usage analytics endpoints
│   │   └── data_router.py           # Data management endpoints
│   └── services/                    # Business logic services
│       ├── retriever.py             # DGFT document retrieval
│       ├── reranker.py              # Result reranking algorithms
│       ├── prompt_builder.py        # Dynamic prompt construction
│       ├── logger.py                # Database logging and analytics
│       ├── proactive_service.py     # ChatGPT-like proactive features
│       └── data_ingestion_service.py # DGFT document processing
├── 🎨 frontend/                     # React Frontend
│   ├── src/
│   │   ├── components/              # Chat UI components
│   │   │   ├── ChatBox.js           # Main chat interface
│   │   │   ├── MessageBubble.js     # Message display
│   │   │   ├── ProactiveSuggestions.js # AI suggestions
│   │   │   └── DiagramPreview.js    # Document previews
│   │   ├── pages/ChatPage.js        # Main chat page
│   │   ├── api/apiClient.js         # Backend integration
│   │   └── App.js                   # React app entry
│   ├── build/                       # Production build
│   └── package.json                 # Frontend dependencies
├── 📚 QA_Data_frontend/             # Integrated Trade Data
│   └── Query_Assistant/
│       ├── data/                    # 53+ Trade documents
│       │   ├── DGFT policies        # DGFT-specific documents  
│       │   ├── Customs procedures   # Customs regulations
│       │   ├── Export guidelines    # Export procedures
│       │   └── Import procedures    # Import regulations
│       ├── chroma_db/               # Vector database
│       ├── document_loader.py       # Document processing
│       └── vector_store.py          # Vector operations
├── 📋 requirements.txt              # All Python dependencies
├── 🔧 setup_integration.bat         # Windows setup script
├── 🔧 setup_integration.sh          # Linux/Mac setup script
└── 📖 README.md                     # This comprehensive guide
```

## 🚀 **Quick Start**

### Prerequisites
- Python 3.8+
- Node.js 16+ (for React frontend)
- OpenAI API Key
- 4GB+ RAM for vector operations

### One-Command Setup

**Windows:**
```bash
setup_integration.bat
```

**Linux/Mac:**
```bash
chmod +x setup_integration.sh
./setup_integration.sh
```

### Manual Setup

1. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure environment variables**
```bash
# Copy and edit environment file
copy .env.example .env
# Add your OpenAI API key: OPENAI_API_KEY=sk-your-key-here
```

3. **Setup React frontend**
```bash
cd frontend
npm install
npm run build
cd ..
```

4. **Run the integrated system**
```bash
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 **Access Points**

Once running, access the system at:

- **🏠 Main Application**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs
- **🔍 API Health Check**: http://localhost:8000/api/v1/health
- **📊 Data Management**: http://localhost:8000/api/v1/data/summary

## 🎯 **API Endpoints**

### **Chat Endpoints**
- **`POST /api/v1/ask`** - Main chat endpoint with proactive features
- **`GET /api/v1/conversations/{id}`** - Get conversation history

### **Proactive Features**
- **`GET /api/v1/proactive/check/{user_id}`** - Check if user needs proactive help
- **`POST /api/v1/proactive/feedback`** - Submit feedback on proactive suggestions

### **Data Management**
- **`GET /api/v1/data/summary`** - DGFT document summary and status
- **`GET /api/v1/data/health`** - Data system health check
- **`POST /api/v1/data/rebuild`** - Rebuild vector store
- **`GET /api/v1/data/search`** - Direct document search

### **Analytics & Management**
- **`GET /api/v1/usage/stats/{user_id}`** - User usage statistics
- **`GET /api/v1/usage/summary`** - Global usage summary
- **`GET /api/v1/health`** - System health check

## 💡 **Usage Examples**

### Basic Chat Request
```json
POST /api/v1/ask
{
    "user_id": "user123",
    "question": "What are the export procedures for electronics?",
    "conversation_id": "conv_456",
    "include_diagrams": true,
    "include_suggestions": true
}
```

### Response with Proactive Features
```json
{
    "answer": "For electronics export, you need to follow these key procedures...",
    "sources": [
        {
            "id": "dgft_doc_1",
            "title": "Electronics Export Procedures",
            "content": "Detailed procedure information...",
            "score": 0.95
        }
    ],
    "diagrams": [
        {
            "title": "Export Process Flow",
            "type": "flowchart",
            "url": "data:image/png;base64,..."
        }
    ],
    "suggestions": [
        "Would you like to know about electronics customs duties?",
        "Should I explain the quality certification requirements?",
        "Are you interested in export incentives for electronics?"
    ],
    "conversation_id": "conv_456",
    "response_time_ms": 1250,
    "tokens_used": 450
}
```

## 🔧 **Configuration**

### Environment Variables (.env)
```bash
# Required
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=sqlite:///./chatbot.db

# Optional
LOG_LEVEL=INFO
LOG_FILE=logs/chatbot.log
CORS_ORIGINS=["http://localhost:3000","https://yourapp.com"]
MAX_TOKENS=4000
TEMPERATURE=0.7
TOP_K_RETRIEVAL=10
SIMILARITY_THRESHOLD=0.3
```

### Settings File (settings.yaml)
```yaml
database:
  url: "sqlite:///./chatbot.db"
  pool_size: 10

openai:
  model: "gpt-4"
  max_tokens: 4000
  temperature: 0.7

vector_db:
  collection_name: "dgft_documents"
  top_k: 10

proactive:
  enable_stuck_detection: true
  followup_threshold: 3
  help_suggestion_limit: 5
```

## 🎯 **Proactive Features Deep Dive**

### **User Behavior Analysis**
The system analyzes user patterns including:
- Question complexity and topics
- Expertise level determination
- Interaction frequency and timing
- Success rate and satisfaction indicators

### **Stuck Detection Algorithm**
Identifies when users might need help through:
- Repeated similar questions
- Long pauses in conversation
- Declining response quality indicators
- Explicit help requests detection

### **Context-Aware Follow-ups**
Generates intelligent suggestions based on:
- Current conversation context
- User expertise level
- Historical interaction patterns
- Topic progression and depth

## 📈 **DGFT Document Integration**

### **Available Documents (53+ files)**
- Export & Import Operations
- Custom Duty Calculations
- HSN Classification
- Export Incentives & DGFT Schemes
- Advance Authorization
- EPCG (Export Promotion Capital Goods)
- AEO Certification
- Free Trade Agreements
- And 45+ more comprehensive documents

### **Document Processing Pipeline**
1. **Extraction** - DOCX files processed automatically from trade documentation
2. **Chunking** - Intelligent text segmentation for optimal retrieval
3. **Embedding** - OpenAI embeddings for semantic search across trade topics
4. **Indexing** - ChromaDB vector database storage
5. **Retrieval** - Smart similarity-based retrieval for trade queries

## 🛠️ **Development & Customization**

### **Adding New Trade Documents**
```bash
# Place DOCX files in QA_Data_frontend/Query_Assistant/data/
# Documents can cover any trade topic: DGFT, Customs, FTA, etc.
# Rebuild vector store
curl -X POST http://localhost:8000/api/v1/data/rebuild
```

### **Customizing Proactive Features**
Edit `api/services/proactive_service.py`:
- Modify stuck detection thresholds
- Add custom behavior patterns
- Enhance suggestion algorithms

### **Frontend Customization**
React components in `frontend/src/components/`:
- `ChatBox.js` - Main chat interface
- `MessageBubble.js` - Message styling
- `ProactiveSuggestions.js` - AI suggestion display

## 📦 **Dependencies**

### **Core Backend**
- `fastapi` - Modern web framework
- `uvicorn` - ASGI server
- `openai` - OpenAI API integration
- `langchain` - LLM framework
- `chromadb` - Vector database

### **Data Processing**
- `python-docx` - DOCX file processing
- `sentence-transformers` - Embeddings
- `scikit-learn` - ML utilities
- `numpy` - Numerical operations

### **Frontend**
- `react` - UI framework
- `styled-components` - CSS-in-JS
- `axios` - HTTP client
- `react-router-dom` - Routing

## 🔒 **Security Considerations**

- API keys stored securely in environment variables
- JWT tokens for user authentication
- Rate limiting and usage tracking
- Input validation and sanitization
- CORS configuration for secure cross-origin requests
- Secure iframe embedding with token-based auth

## 🤝 **Integration Options**

### **Iframe Embedding**
```html
<iframe 
  src="http://localhost:8000?token=YOUR_JWT_TOKEN"
  width="400" 
  height="600"
  frameborder="0">
</iframe>
```

### **API Integration**
```javascript
import { chatAPI } from './apiClient';

const response = await chatAPI.sendMessage(
  "What are export procedures?",
  conversationId
);
```

### **Webhook Integration**
Configure webhooks for proactive notifications and analytics.

## 📋 **TODO / Roadmap**

- [ ] Add WebSocket support for real-time chat
- [ ] Implement advanced caching mechanisms
- [ ] Add support for file uploads and processing
- [ ] Integration with external knowledge bases
- [ ] Advanced conversation analytics dashboard
- [ ] Multi-language support
- [ ] Voice chat capabilities
- [ ] Custom model fine-tuning support

## 🆘 **Troubleshooting**

### **Common Issues**

1. **Vector database not initialized**
   ```bash
   curl -X POST http://localhost:8000/api/v1/data/rebuild
   ```

2. **Frontend not loading**
   ```bash
   cd frontend && npm run build
   ```

3. **OpenAI API errors**
   - Check API key in .env file
   - Verify API quota and billing

4. **Documents not found**
   - Ensure DGFT documents are in `QA_Data_frontend/Query_Assistant/data/`
   - Rebuild vector store

## 📞 **Support & Documentation**

- **🔗 API Documentation**: http://localhost:8000/docs
- **⚙️ Configuration Examples**: See `.env.example` and `settings.yaml.example`
- **📄 Project Documentation**: `Final_Chatbot_Project_Documentation.docx`
- **🐛 Issues**: Check logs in `logs/` directory

## 📄 **License**

This project is created for educational and development purposes. Please ensure you comply with OpenAI's usage policies when using their API.

---

**Built with ❤️ using FastAPI, React, OpenAI, and advanced AI techniques**

*Complete integration ready - ChatGPT-like intelligence meets comprehensive DGFT expertise!*

*Last updated: September 30, 2025*