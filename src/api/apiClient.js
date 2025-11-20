import axios from 'axios';

// Configuration
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = 60000; // 60 seconds for image processing

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token
apiClient.interceptors.request.use(
  (config) => {
    // Get JWT token from localStorage, sessionStorage, or URL params
    let token = localStorage.getItem('jwt_token') || 
                sessionStorage.getItem('jwt_token');
    
    // If no token in storage, check URL params (for iframe integration)
    if (!token) {
      const urlParams = new URLSearchParams(window.location.search);
      token = urlParams.get('token');
      
      // Store token for subsequent requests
      if (token) {
        sessionStorage.setItem('jwt_token', token);
      }
    }
    
    // Add Authorization header if token exists
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('jwt_token');
      sessionStorage.removeItem('jwt_token');
      
      // Notify parent window about authentication error
      if (window.chatbotAPI) {
        window.chatbotAPI.postMessage({
          type: 'auth_error',
          message: 'Authentication required'
        });
      }
    }
    return Promise.reject(error);
  }
);

// API Methods
export const chatAPI = {
  /**
   * Send a message to the chatbot and get response
   * @param {string} message - User message
   * @param {string} conversationId - Optional conversation ID for context
   * @param {string} userId - User identifier
   * @returns {Promise} API response
   */
  async sendMessage(message, conversationId = null, userId = 'anonymous') {
    try {
      const payload = {
        question: message.trim(),
        user_id: userId,
        conversation_id: conversationId,
        include_diagrams: true,
        include_suggestions: true,
      };
      
      const response = await apiClient.post('/ask', payload);
      
      return {
        success: true,
        data: response.data,
        conversationId: response.data.conversation_id,
        answer: response.data.answer,
        sources: response.data.sources || [],
        diagrams: response.data.diagrams || [],
        suggestions: response.data.suggestions || [],
        images: response.data.images || [],
        responseTime: response.data.response_time_ms,
        tokensUsed: response.data.tokens_used,
      };
    } catch (error) {
      console.error('Error sending message:', error);
      
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Failed to send message',
        status: error.response?.status,
      };
    }
  },

  /**
   * Get conversation history
   * @param {string} conversationId - Conversation ID
   * @returns {Promise} Conversation history
   */
  async getConversationHistory(conversationId) {
    try {
      const response = await apiClient.get(`/conversation/${conversationId}`);
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Error fetching conversation history:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message,
      };
    }
  },

  /**
   * Get proactive suggestions based on conversation context
   * @param {string} userId - User identifier  
   * @param {string} conversationId - Optional conversation ID
   * @returns {Promise} Proactive suggestions
   */
  async getProactiveSuggestions(userId = 'anonymous', conversationId = null) {
    try {
      const params = new URLSearchParams({ user_id: userId });
      if (conversationId) {
        params.append('conversation_id', conversationId);
      }
      
      const response = await apiClient.get(`/proactive/suggestions?${params.toString()}`);
      
      return {
        success: true,
        data: response.data.suggestions || [],
      };
    } catch (error) {
      console.error('Error fetching proactive suggestions:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message,
        data: [], // Return empty array as fallback
      };
    }
  },

  /**
   * Get user behavior insights
   * @param {string} userId - User identifier
   * @returns {Promise} User behavior insights
   */
  async getUserInsights(userId = 'anonymous') {
    try {
      const response = await apiClient.get(`/proactive/insights/${userId}`);
      
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Error fetching user insights:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message,
      };
    }
  },

  /**
   * Get suggested questions (using default suggestions)
   * @param {string} context - Current conversation context
   * @param {string} userId - User identifier
   * @returns {Promise} Suggested questions
   */
  async getSuggestedQuestions(context = '', userId = 'anonymous') {
    try {
      // Return default suggestions since backend provides suggestions with /ask responses
      const defaultSuggestions = [
        "What is DGFT and its role in foreign trade?",
        "How do I obtain an IEC certificate?",
        "What are the export procedures in India?",
        "Tell me about import documentation requirements",
        "What are the different types of export incentives?",
        "How does customs clearance work?",
        "What is an Export-Import License?",
        "Explain the EPCG scheme"
      ];
      
      return {
        success: true,
        data: defaultSuggestions,
      };
    } catch (error) {
      console.error('Error fetching suggested questions:', error);
      return {
        success: false,
        error: error.message,
        data: [], // Return empty array as fallback
      };
    }
  },

  /**
   * Get usage statistics for user
   * @param {string} userId - User identifier
   * @returns {Promise} Usage statistics
   */
  async getUsageStats(userId = 'anonymous') {
    try {
      const response = await apiClient.get(`/usage/${userId}`);
      
      return {
        success: true,
        data: response.data.usage,
      };
    } catch (error) {
      console.error('Error fetching usage stats:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message,
      };
    }
  },

  /**
   * Health check endpoint
   * @returns {Promise} API health status
   */
  async healthCheck() {
    try {
      const response = await apiClient.get('/health');
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
      };
    }
  },
};

// Export default client for custom requests
export default apiClient;
