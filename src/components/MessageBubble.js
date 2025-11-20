import React, { useState } from 'react';
import styled from 'styled-components';

// Icon Components
const CopyIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
  </svg>
);

const CheckIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
);

const ThumbsUpIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
  </svg>
);

const ThumbsDownIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
  </svg>
);

const AlertIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="8" x2="12" y2="12"></line>
    <line x1="12" y1="16" x2="12.01" y2="16"></line>
  </svg>
);

const MessageContainer = styled.div`
  display: flex;
  gap: 12px;
  align-items: flex-start;
  width: 100%;
  max-width: 800px;
  margin: 0 auto 24px auto;
  justify-content: ${props => props.isUser ? 'flex-end' : 'flex-start'};
  padding: 0 24px;
`;

const MessageContent = styled.div`
  max-width: ${props => props.isUser ? '70%' : '100%'};
  min-width: ${props => props.isUser ? '100px' : 'auto'};
  display: flex;
  flex-direction: column;
`;

const BubbleWrapper = styled.div`
  background: ${props => props.isUser ? '#f3f4f6' : 'transparent'};
  color: ${props => props.isUser ? '#374151' : '#374151'};
  padding: ${props => props.isUser ? '6px 16px' : '0'};
  border-radius: ${props => props.isUser ? '18px' : '0'};
  border: none;
  font-size: 15px;
  font-family: Poppins, sans-serif;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  
  /* Style for code blocks */
  code {
    background: rgba(0,0,0,0.1);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Monaco', 'Consolas', 'SF Mono', monospace;
    font-size: 14px;
  }
  
  /* Style for links */
  a {
    color: ${props => props.isUser ? '#93c5fd' : '#10a37f'};
    text-decoration: underline;
    
    &:hover {
      text-decoration: none;
    }
  }
  
  /* Style for lists */
  ul, ol {
    margin: 8px 0;
    padding-left: 20px;
  }
  
  li {
    margin: 4px 0;
  }
`;

const BubbleContent = styled.div`
  margin-bottom: 4px;
`;

const Timestamp = styled.div`
  font-size: 11px;
  font-family: Poppins, sans-serif;
  color: #8e8ea0;
  text-align: ${props => props.isUser ? 'right' : 'left'};
  margin-top: 8px;
  font-weight: 400;
  opacity: 0.7;
`;

const ErrorMessage = styled.div`
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fca5a5;
  border-radius: 16px;
  padding: 20px 24px;
  color: #dc2626;
  font-size: 14px;
  margin-top: 12px;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.15);
  font-weight: 500;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%);
  }
`;

const ErrorIcon = styled.div`
  width: 24px;
  height: 24px;
  background: #dc2626;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
  
  svg {
    width: 14px;
    height: 14px;
    color: white;
  }
`;

const ErrorContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const ErrorTitle = styled.div`
  font-weight: 600;
  font-size: 15px;
  color: #991b1b;
`;

const ErrorDescription = styled.div`
  font-weight: 400;
  color: #dc2626;
  line-height: 1.4;
`;

const RetryButton = styled.button`
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: white;
  border: none;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  margin-top: 12px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.3);
  
  &:hover {
    background: linear-gradient(135deg, #047857 0%, #065f46 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(5, 150, 105, 0.4);
  }
  
  &:active {
    transform: translateY(0);
  }
`;

const ActionButtons = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 12px;
  margin-left: 0;
  opacity: 0.7;
  transition: opacity 0.2s ease;
  
  &:hover {
    opacity: 1;
  }
`;

const ActionButton = styled.button`
  background: transparent;
  border: none;
  color: #8e8ea0;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  font-size: 11px;
  
  &:hover {
    background: #f7f7f8;
    color: #565869;
  }
  
  &:active {
    transform: scale(0.95);
  }
  
  svg {
    width: 16px;
    height: 16px;
  }
  
  &.active-positive {
    color: #10a37f;
    background: #f0f9f3;
  }
  
  &.active-negative {
    color: #ef4444;
    background: #fef2f2;
  }
  
  &.copied {
    color: #10a37f;
    background: #f0f9f3;
  }
`;

const ButtonText = styled.span`
  margin-left: 4px;
  font-size: 11px;
  font-weight: 500;
`;


const MessageBubble = ({ 
  message, 
  isUser, 
  timestamp, 
  isTyping = false, 
  isError = false,
  onRetry = null 
}) => {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null); // 'positive' or 'negative'

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatMessage = (text) => {
    if (!text) return '';
    
    // Simple markdown-like formatting
    let formatted = text
      // Bold text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Italic text
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Inline code
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // Links
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    return formatted;
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const handleFeedback = (type) => {
    if (feedback === type) {
      setFeedback(null); // Toggle off if clicking the same button
    } else {
      setFeedback(type);
      // Here you could also send feedback to your backend
      console.log(`Feedback: ${type}`);
    }
  };

  if (isTyping) {
    return (
      <MessageContainer isUser={false}>
        <MessageContent isUser={false}>
          <BubbleWrapper isUser={false}>
            <div>Thinking...</div>
          </BubbleWrapper>
        </MessageContent>
      </MessageContainer>
    );
  }

  return (
    <MessageContainer isUser={isUser}>
      <MessageContent isUser={isUser}>
        {isError ? (
          <ErrorMessage>
            <ErrorIcon>
              <AlertIcon />
            </ErrorIcon>
            <ErrorContent>
              <ErrorTitle>
                {message?.includes('Network') ? 'Connection Problem' : 'Something went wrong'}
              </ErrorTitle>
              <ErrorDescription>
                {message?.includes('Network') 
                  ? 'Unable to connect to the server. Please check your internet connection and try again.' 
                  : (message || 'An unexpected error occurred. Please try again.')
                }
              </ErrorDescription>
              {onRetry && (
                <RetryButton onClick={onRetry}>
                  Retry
                </RetryButton>
              )}
            </ErrorContent>
          </ErrorMessage>
        ) : (
          <>
            <BubbleWrapper isUser={isUser}>
              <BubbleContent
                dangerouslySetInnerHTML={{ 
                  __html: formatMessage(message) 
                }} 
              />
            </BubbleWrapper>
            
            {/* Action buttons for bot messages only */}
            {!isUser && (
              <ActionButtons>
                <ActionButton 
                  onClick={handleCopy}
                  title="Copy message"
                  className={copied ? 'copied' : ''}
                >
                  {copied ? <CheckIcon /> : <CopyIcon />}
                </ActionButton>
                
                <ActionButton 
                  onClick={() => handleFeedback('positive')}
                  title="Good response"
                  className={feedback === 'positive' ? 'active-positive' : ''}
                >
                  <ThumbsUpIcon />
                </ActionButton>
                
                <ActionButton 
                  onClick={() => handleFeedback('negative')}
                  title="Bad response"
                  className={feedback === 'negative' ? 'active-negative' : ''}
                >
                  <ThumbsDownIcon />
                </ActionButton>
              </ActionButtons>
            )}
          </>
        )}
      </MessageContent>
    </MessageContainer>
  );
};

export default MessageBubble;