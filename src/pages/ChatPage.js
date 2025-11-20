import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import ChatBox from '../components/ChatBox';

const PageContainer = styled.div`
  height: 100vh;
  width: 100vw;
  max-height: 100vh;
  max-width: 100vw;
  display: flex;
  flex-direction: column;
  background: ${props => props.isIframe ? 'transparent' : '#f7f7f8'};
  font-family: "Poppins", sans-serif !important;
  overflow: hidden;
  margin: 0;
  padding: 0;
  position: fixed;
  top: 0;
  left: 0;
`;

const ChatWrapper = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  margin: 0;
  width: 100%;
  height: 100%;
  min-height: 0;
  box-sizing: border-box;
`;

const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  flex-direction: column;
  color: #666;
`;

const LoadingSpinner = styled.div`
  width: 40px;
  height: 40px;
  border: 3px solid #f0f0f0;
  border-top: 3px solid #10a37f;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const LoadingText = styled.div`
  font-size: 14px;
  color: #666;
`;

const ErrorContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  flex-direction: column;
  padding: 20px;
  text-align: center;
`;

const ErrorTitle = styled.h2`
  color: #e53e3e;
  margin-bottom: 8px;
  font-size: 18px;
`;

const ErrorMessage = styled.p`
  color: #666;
  margin-bottom: 16px;
  font-size: 14px;
  line-height: 1.5;
`;

const RetryButton = styled.button`
  background: #667eea;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
  
  &:hover {
    background: #5a67d8;
  }
`;

const HeaderBar = styled.div`
  background: #f8f4ff;
  padding: 12px 20px;
  color: #1f2937;
  text-align: center;
  border-bottom: 1px solid #e5e5e5;
  display: ${props => props.isIframe ? 'none' : 'block'};
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
`;

const HeaderTitle = styled.h1`
  margin: 0;
  font-size: 20px;
  font-weight: 600;
`;

const ChatPage = () => {
  const [isIframe, setIsIframe] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [authToken, setAuthToken] = useState(null);

  useEffect(() => {
    initializePage();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const initializePage = async () => {
    try {
      // Check if running in iframe
      const inIframe = window.self !== window.top;
      setIsIframe(inIframe);

      // Handle authentication
      await handleAuthentication();

      // Setup iframe communication if in iframe
      if (inIframe) {
        setupIframeCommunication();
      }

      // Send ready message to parent
      notifyParentReady();

      setLoading(false);
    } catch (err) {
      console.error('Initialization error:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const handleAuthentication = async () => {
    try {
      // Try to get token from URL parameters first (for iframe integration)
      const urlParams = new URLSearchParams(window.location.search);
      let token = urlParams.get('token') || urlParams.get('jwt');

      // If no token in URL, check storage
      if (!token) {
        token = localStorage.getItem('jwt_token') || 
               sessionStorage.getItem('jwt_token');
      }

      if (token) {
        // Store token for API client
        sessionStorage.setItem('jwt_token', token);
        setAuthToken(token);
        
        // Validate token by making a health check
        // This will be handled by the API client's interceptors
      } else if (isIframe) {
        // If in iframe and no token, request it from parent
        requestTokenFromParent();
      }
    } catch (error) {
      console.error('Authentication error:', error);
      // Don't throw here - allow anonymous usage if configured
    }
  };

  const setupIframeCommunication = () => {
    // Listen for messages from parent window
    const handleMessage = (event) => {
      if (!event.data || typeof event.data !== 'object') return;

      switch (event.data.type) {
        case 'token':
          if (event.data.token) {
            sessionStorage.setItem('jwt_token', event.data.token);
            setAuthToken(event.data.token);
          }
          break;
          
        case 'config':
          // Handle configuration updates from parent
          if (event.data.config) {
            localStorage.setItem('chat_config', JSON.stringify(event.data.config));
          }
          break;
          
        case 'resize':
          // Handle resize requests from parent
          if (event.data.height) {
            document.body.style.height = `${event.data.height}px`;
          }
          break;
          
        default:
          break;
      }
    };

    window.addEventListener('message', handleMessage);

    // Cleanup listener on unmount
    return () => {
      window.removeEventListener('message', handleMessage);
    };
  };

  const requestTokenFromParent = () => {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({
        type: 'chatbot',
        action: 'request_token'
      }, '*');
    }
  };

  const notifyParentReady = () => {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({
        type: 'chatbot',
        action: 'ready',
        data: {
          height: document.body.scrollHeight,
          hasToken: !!authToken
        }
      }, '*');
    }
  };

  const handleRetry = () => {
    setError(null);
    setLoading(true);
    initializePage();
  };

  const handleChatResize = () => {
    // Notify parent of height changes for iframe resizing
    if (isIframe && window.parent && window.parent !== window) {
      const height = Math.max(
        document.body.scrollHeight,
        document.body.offsetHeight,
        document.documentElement.clientHeight,
        document.documentElement.scrollHeight,
        document.documentElement.offsetHeight
      );

      window.parent.postMessage({
        type: 'chatbot',
        action: 'resize',
        data: { height }
      }, '*');
    }
  };

  // Notify parent of height changes
  useEffect(() => {
    if (isIframe) {
      const resizeObserver = new ResizeObserver(() => {
        handleChatResize();
      });

      resizeObserver.observe(document.body);

      return () => {
        resizeObserver.disconnect();
      };
    }
  }, [isIframe]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <LoadingContainer>
        <LoadingSpinner />
        <LoadingText>Initializing chat interface...</LoadingText>
      </LoadingContainer>
    );
  }

  if (error) {
    return (
      <ErrorContainer>
        <ErrorTitle>Failed to Load Chat</ErrorTitle>
        <ErrorMessage>
          {error}
          <br />
          Please check your connection and try again.
        </ErrorMessage>
        <RetryButton onClick={handleRetry}>
          Retry
        </RetryButton>
      </ErrorContainer>
    );
  }

  return (
    <PageContainer isIframe={isIframe}>
      {!isIframe && (
        <HeaderBar isIframe={isIframe}>
          <HeaderTitle>ChatBot Assistant</HeaderTitle>
        </HeaderBar>
      )}
      <ChatWrapper isIframe={isIframe}>
        <ChatBox />
      </ChatWrapper>
    </PageContainer>
  );
};

export default ChatPage;
