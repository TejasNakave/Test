import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import MessageBubble from './MessageBubble';
import SuggestedQuestions from './SuggestedQuestions';
import DiagramPreview from './DiagramPreview';
import ImageGallery from './ImageGallery';
import { chatAPI } from '../api/apiClient';

const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  max-height: 100vh;
  max-width: 100vw;
  margin: 0;
  padding: 0;
  background: #ffffff;
  font-family: "Poppins", sans-serif !important;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  zoom: 1 !important;
  transform: scale(1) !important;
  transform-origin: 0 0 !important;
  
  > * {
    position: relative;
    z-index: 2;
  }
`;

const Header = styled.div`
  // background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  background:#F8FAFC;
  border-bottom: 1px solid #e2e8f0;
  padding: 0px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 20;
`;

const HeaderLeft = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const HeaderRight = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const RefreshButton = styled.button`
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  
  &:hover {
    background: linear-gradient(135deg, #4a90e2 0%,rgb(137, 176, 234) 100%);
    border-color: #4a90e2;
    transform: translateY(-1px) rotate(180deg);
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
    color: white;
  }
  
  &:active {
    transform: translateY(0) rotate(180deg);
  }
  
  svg {
    width: 20px;
    height: 20px;
    transition: color 0.3s ease;
  }
`;

const InfoButton = styled.button`
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.3);
  color: white;
  font-weight: bold;
  font-size: 14px;
  z-index: 5;
  
  &:hover {
    background: linear-gradient(135deg, #b91c1c 0%, #991b1b 100%);
    transform: translateY(-50%) scale(1.1);
    box-shadow: 0 4px 12px rgba(220, 38, 38, 0.4);
  }
  
  &:active {
    transform: translateY(-50%) scale(0.95);
  }
`;

const InfoTooltip = styled.div`
  position: absolute;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
  color: white;
  padding: 16px 20px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  max-width: 500px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  z-index: 1000;
  opacity: ${props => props.visible ? 1 : 0};
  visibility: ${props => props.visible ? 'visible' : 'hidden'};
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  
  &::before {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 8px solid transparent;
    border-top-color: #374151;
  }
  
  .info-icon {
    color: #60a5fa;
    margin-right: 8px;
    font-size: 16px;
  }
  
  .keywords {
    color: #93c5fd;
    font-weight: 600;
  }
`;

const ContextualSuggestionsContainer = styled.div`
  padding: 16px 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-top: 1px solid #e0f2fe;
  
  ${props => props.visible ? `
    opacity: 1;
    visibility: visible;
    transition: all 0.3s ease;
  ` : `
    opacity: 0;
    visibility: hidden;
    height: 0;
    padding: 0 24px;
    transition: all 0.3s ease;
  `}
`;

const ContextualTitle = styled.div`
  font-size: 14px;
  font-weight: 600;
  color: #0369a1;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  
  &::before {
    content: "💡";
    font-size: 16px;
  }
`;

const ChatGPTLogo = styled.div`
  width: 40px;
  height: 70px;
  // background: linear-gradient(135deg, #4a90e2 0%, #2c5aa0 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 16px;
  // box-shadow: 0 4px 12px rgba(74, 144, 226, 0.25);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-1px);
    // box-shadow: 0 6px 20px rgba(74, 144, 226, 0.35);
  }
`;

const HeaderTitle = styled.h1`
  font-size: 18px;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
  background: linear-gradient(135deg, #000000ff 0%, #000000ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const HeaderSubtitle = styled.p`
  font-size: 14px;
  color: #6b7280;
  margin: 0;
`;

const MessagesContainer = styled.div`
  flex: 1;
  min-height: 0;
  overflow-y: ${props => props.isHomePage ? 'hidden' : 'auto'};
  display: flex;
  flex-direction: column;
  width: 100%;
  padding-bottom: 0;
  
  /* Custom scrollbar like ChatGPT - only show when not on home page */
  &::-webkit-scrollbar {
    width: ${props => props.isHomePage ? '0px' : '6px'};
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: #9ca3af;
  }
`;

const MessageWrapper = styled.div`
  width: 100%;
  padding: 8px 24px;
  transition: all 0.3s ease;
  background: #fff;
`;

const InputContainer = styled.div`
  padding: 0 24px 24px 24px;
  background: transparent;
`;

const InputWrapper = styled.div`
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 30px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  transition: all 0.3s ease;
  min-height: 50px;
  max-height: 120px;
  height: auto;
  display: flex;
  align-items: stretch;
  
  &:focus-within {
    border-color: #4a90e2;
    box-shadow: 0 8px 25px rgba(74, 144, 226, 0.12);
    transform: translateY(-2px);
  }
  
  &:hover {
    border-color: #cbd5e1;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    transform: translateY(-1px);
  }
`;

const TextInputContainer = styled.div`
  position: relative;
  width: 97%;
  display: flex;
  align-items: center;
  overflow: hidden;
  box-sizing: border-box;
`;

const TextInput = styled.textarea`
  width: 100%;
  border: none;
  outline: none;
  padding: 14px 110px 14px 24px;
  font-size: 16px;
  line-height: 1.3;
  resize: none;
  background: transparent;
  font-family: "Poppins", sans-serif !important;
  color: #1f2937;
  min-height: 50px;
  max-height: 120px;
  height: auto;
  border-radius: 30px;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: pre-wrap;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  vertical-align: top;
  
  &::-webkit-scrollbar {
    width: 0px;
    background: transparent;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background: transparent;
  }
  
  &::placeholder {
    color: #6b7280;
    font-size: 16px;
    font-weight: 400;
  }
`;

const MicButton = styled.button`
  position: absolute;
  right: 60px;
  top: ${props => props.hasContent ? 'auto' : '50%'};
  bottom: ${props => props.hasContent ? '14px' : 'auto'};
  transform: ${props => props.hasContent ? 'none' : 'translateY(-50%)'};
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  opacity: ${props => props.disabled ? 0.4 : 1};
  
  &:hover:not(:disabled) {
    background: rgba(176, 176, 176, 0.1);
    transform: ${props => props.hasContent ? 'scale(1.05)' : 'translateY(-50%) scale(1.05)'};
  }
  
  &:active:not(:disabled) {
    transform: ${props => props.hasContent ? 'scale(0.95)' : 'translateY(-50%) scale(0.95)'};
  }
  
  svg {
    width: 18px;
    height: 18px;
  }
  
  &:hover .tooltip {
    opacity: 1;
    visibility: visible;
    transform: translateX(-50%) translateY(-5px);
  }
`;

const Tooltip = styled.div`
  position: absolute;
  bottom: 120%;
  left: 50%;
  transform: translateX(-50%);
  background: #000000;
  color: white;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  pointer-events: none;
  z-index: 1000;
  font-family: "Poppins", sans-serif;
  
  &::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 5px solid transparent;
    border-top-color: #000000;
  }
`;

const SendButton = styled.button`
  position: absolute;
  right: 12px;
  top: ${props => props.hasContent ? 'auto' : '50%'};
  bottom: ${props => props.hasContent ? '14px' : 'auto'};
  transform: ${props => props.hasContent ? 'none' : 'translateY(-50%)'};
  width: 36px;
  height: 36px;
  background: transparent;
  color: #4a90e2;
  border: none;
  border-radius: 50%;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  opacity: ${props => props.disabled ? 0.4 : 1};
  
  &:hover:not(:disabled) {
    background: rgba(74, 144, 226, 0.1);
    transform: ${props => props.hasContent ? 'scale(1.05)' : 'translateY(-50%) scale(1.05)'};
  }
  
  &:active:not(:disabled) {
    transform: ${props => props.hasContent ? 'scale(0.95)' : 'translateY(-50%) scale(0.95)'};
  }
  
  svg {
    width: 18px;
    height: 18px;
    margin-left: 2px;
  }
`;

const WelcomeContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  width: 100%;
  flex: 1;
  background-color: #fff;
`;

const WelcomeIcon = styled.div`
  width: 100px;
  height: 100px;
  // background: linear-gradient(135deg, #4a90e2 0%, #2c5aa0 100%);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32px;
  // box-shadow: 0 8px 32px rgba(74, 144, 226, 0.3);
  position: relative;
  animation: float 3s ease-in-out infinite;
  
  &::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    // background: linear-gradient(135deg, #60a5fa, #3b82f6, #1d4ed8);
    border-radius: 26px;
    z-index: -1;
    opacity: 0.5;
    animation: pulse 2s ease-in-out infinite;
  }
  
  @keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 0.8; }
  }
`;

const WelcomeTitle = styled.h2`
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #1f2937 0%, #000000ff 50%, #000000ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: -17px 0 12px 0;
  text-align: center;
`;

const WelcomeText = styled.p`
  font-size: 18px;
  color: #64748b;
  margin: 0 0 40px 0;
  line-height: 1.6;
  max-width: 500px;
  text-align: center;
  opacity: 0.9;
`;

const SuggestedKeywordsContainer = styled.div`
  // background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  // background-color: #f0e9fc;
  // border: 1px solid #e8defaff;
  border-radius: 28px;
  padding: 25px 25px;
  margin: -1px 0 40px 0;
  max-width: 600px;
  width: 100%;
  box-shadow: #e8defaff;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    // box-shadow: 0 8px 24px rgba(14, 165, 233, 0.15);
  }
`;

const KeywordsTitle = styled.h3`
  font-size: 16px;
  font-weight: 600;
  color: #0369a1;
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  
  &::before {
    // content: "💡";
    font-size: 18px;
  }
`;

const KeywordsGrid = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  align-items: center;
`;

const KeywordTag = styled.span`
  // background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  // background: #fff
  border: 1px solid #cbd5e1;
  color: #475569;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  
  &:hover {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    color: white;
    border-color: #3b82f6;
    transform: translateY(-1px);
    // box-shadow: 0 4px 8px rgba(59, 130, 246, 0.2);
  }
  
  &:active {
    transform: translateY(0);
  }
`;

const ErrorBanner = styled.div`
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fca5a5;
  color: #dc2626;
  padding: 16px 24px;
  margin: 16px 24px 20px 24px;
  border-radius: 12px;
  font-size: 14px;
  text-align: center;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.1);
`;

const TypingIndicatorContainer = styled.div`
  background: #ffffff;
  margin: 16px 0;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
`;

const TypingIndicatorContent = styled.div`
  width: 100%;
  padding: 20px 24px;
  display: flex;
  gap: 16px;
  align-items: center;
  border-radius: 12px;
`;

const TypingDots = styled.div`
  display: flex;
  gap: 4px;
  
  span {
    width: 8px;
    height: 8px;
    background: #9ca3af;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;
    
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
    &:nth-child(3) { animation-delay: 0s; }
  }
  
  @keyframes typing {
    0%, 80%, 100% {
      transform: scale(0.8);
      opacity: 0.5;
    }
    40% {
      transform: scale(1);
      opacity: 1;
    }
  }
`;

const SendIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#6b7280">
    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
  </svg>
);

{/* <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
</svg> */}

// const SendIcon = () => (
//   <img src="/send.svg" alt="Send Icon" width={15} height={15} />
// );

const SoundWaves = styled.div`
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 3px;
  opacity: ${props => props.isRecording ? 1 : 0};
  transition: opacity 0.3s ease;
  pointer-events: none;
  
  .wave {
    width: 3px;
    background: #000000;
    border-radius: 2px;
    animation: soundWave 1s ease-in-out infinite;
    
    &:nth-child(1) { height: 8px; animation-delay: 0s; }
    &:nth-child(2) { height: 12px; animation-delay: 0.1s; }
    &:nth-child(3) { height: 16px; animation-delay: 0.2s; }
    &:nth-child(4) { height: 12px; animation-delay: 0.3s; }
    &:nth-child(5) { height: 8px; animation-delay: 0.4s; }
    &:nth-child(6) { height: 14px; animation-delay: 0.5s; }
    &:nth-child(7) { height: 10px; animation-delay: 0.6s; }
  }
  
  @keyframes soundWave {
    0%, 100% { 
      transform: scaleY(0.5);
      opacity: 0.7;
    }
    50% { 
      transform: scaleY(1);
      opacity: 1;
    }
  }
`;

const MicrophoneIcon = ({ isRecording = false }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke={isRecording ? "#000000" : "#6b7280"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 1C10.343 1 9 2.343 9 4v8c0 1.657 1.343 3 3 3s3-1.343 3-3V4c0-1.657-1.343-3-3-3z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <line x1="12" y1="19" x2="12" y2="23"/>
    <line x1="8" y1="23" x2="16" y2="23"/>
  </svg>
);

const RefreshIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor">
    <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
  </svg>
);


const ChatBotIcon = ({ size = 48 }) => (
  <svg viewBox="0 0 60 60" width={size} height={size}>
    {/* Speech bubble background */}
    <path d="m3.5 55.86c-.37.42-.07 1.09.5 1.11 3.7.19 7.43-.64 10.78-2.28 4.42 2.74 9.64 4.31 15.22 4.31 16.02 0 29-12.98 29-29s-12.98-29-29-29-29 12.98-29 29c0 6.94 2.43 13.3 6.5 18.29-.82 2.81-2.21 5.49-4 7.57z"fill="#4c8ce5ff"/>
    
    {/* Robot antenna */}
    {/* <path d="m28 17.02v-4c0-1.11.9-2.02 2-2.02.55 0 1.05.22 1.41.59.37.37.59.87.59 1.43v4z" fill="#adbfc4"/> */}
    
    {/* Robot top part */}
    <path d="m36 20.02v2h-12v-2c0-2.21 2.69-4 6-4s6 1.79 6 4z" fill="#fff"/>
    
    {/* Left ear */}
    <path d="m13.34 39.02h-1.34c-2.21 0-4-1.79-4-4v-6c0-2.21 1.79-4 4-4h1.34z" fill="#fff"/>
    
    {/* Right ear */}
    <path d="m46.66 25.02h1.34c2.21 0 4 1.79 4 4v6c0 2.21-1.79 4-4 4h-1.34z" fill="#fff"/>
    
    {/* Robot head */}
    <rect fill="#fff" height="24" rx="10" width="36" x="12" y="20.02"/>
    
    {/* Robot face screen */}
    <rect fill="#203b51" height="14" rx="7" width="28" x="16" y="25.02"/>
    
    {/* Left eye */}
    <circle cx="22" cy="32.02" r="2" fill="#3e9ddd"/>
    
    {/* Right eye */}
    <circle cx="38" cy="32.02" r="2" fill="#3e9ddd"/>
    
    {/* Smile */}
    <path d="m30 36.02c-1.475 0-2.474-.908-2.832-1.445-.307-.459-.183-1.08.277-1.387.453-.303 1.068-.186 1.379.265.03.042.432.567 1.176.567.764 0 1.164-.55 1.168-.555.305-.459.928-.584 1.387-.277.46.307.584.928.277 1.387-.358.537-1.357 1.445-2.832 1.445z" fill="#3e9ddd"/>
  </svg>
);

const ChatBox = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTextareaExpanded, setIsTextareaExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [connectionError, setConnectionError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [showInfoTooltip, setShowInfoTooltip] = useState(false);
  const [contextualSuggestions, setContextualSuggestions] = useState([]);
  const [loadingContextualSuggestions, setLoadingContextualSuggestions] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recognition, setRecognition] = useState(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load suggested questions on mount
  useEffect(() => {
    loadSuggestedQuestions();
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 200)}px`;
    }
  }, [inputValue]);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = 'en-US';
      
      recognitionInstance.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(transcript);
        setIsRecording(false);
      };
      
      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
          setConnectionError('Voice recognition failed. Please try again or type your message.');
        }
      };
      
      recognitionInstance.onend = () => {
        setIsRecording(false);
      };
      
      setRecognition(recognitionInstance);
    }
  }, []);

  const loadSuggestedQuestions = async () => {
    try {
      const response = await chatAPI.getSuggestedQuestions();
      if (response.success) {
        setSuggestedQuestions(response.data);
      }
    } catch (error) {
      console.error('Failed to load suggested questions:', error);
    }
  };

  const generateContextualSuggestions = async (userQuestion) => {
    setLoadingContextualSuggestions(true);
    
    try {
      // Call API to get contextual suggestions based on the user's question
      const response = await chatAPI.getSuggestedQuestions(userQuestion);
      
      if (response.success && response.data.length > 0) {
        return response.data.slice(0, 4); // Limit to 4 suggestions
      }
      
      // Fallback to basic contextual suggestions if API fails
      return generateFallbackSuggestions(userQuestion);
    } catch (error) {
      console.error('Failed to get contextual suggestions:', error);
      return generateFallbackSuggestions(userQuestion);
    } finally {
      setLoadingContextualSuggestions(false);
    }
  };

  const generateFallbackSuggestions = (userQuestion) => {
    const question = userQuestion.toLowerCase();
    
    // Basic fallback suggestions based on common keywords
    if (question.includes('export')) {
      return [
        "What documents are needed for export?",
        "How to get export license?",
        "What are export incentives?",
        "Export procedure step by step"
      ];
    } else if (question.includes('import')) {
      return [
        "Import licensing process",
        "Custom duty calculation",
        "Import documentation required",
        "How to clear customs for imports"
      ];
    } else if (question.includes('dgft')) {
      return [
        "DGFT registration process",
        "Latest DGFT circulars",
        "DGFT export promotion schemes",
        "How to contact DGFT office"
      ];
    } else if (question.includes('iec')) {
      return [
        "IEC code application online",
        "IEC renewal procedure",
        "Documents for IEC registration",
        "IEC code fees and charges"
      ];
    } else {
      return [
        "Foreign trade policy updates",
        "Export import procedures",
        "Custom clearance process",
        "Trade documentation requirements"
      ];
    }
  };

  const handleSendMessage = async (messageText = inputValue.trim()) => {
    if (!messageText || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: messageText,
      isUser: true,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTextareaExpanded(false);
    setIsLoading(true);
    setConnectionError(null);
    
    // Generate contextual suggestions based on user's question (async)
    generateContextualSuggestions(messageText).then(contextualQuestions => {
      setContextualSuggestions(contextualQuestions);
    });

    try {
      const response = await chatAPI.sendMessage(messageText, conversationId);
      
      console.log('🔍 Full API Response:', response);
      console.log('🔍 Response.data:', response.data);
      console.log('🔍 Response.answer:', response.answer);
      console.log('🔍 Backend answer field:', response.data?.answer);
      
      if (response.success) {
        const answerText = response.answer || response.data?.answer || response.data?.message || response.data?.response;
        console.log('🔍 Final answer text:', answerText);
        console.log('🖼️ Images from response:', response.data?.images);
        
        const botMessage = {
          id: Date.now() + 1,
          text: answerText,
          isUser: false,
          timestamp: new Date().toISOString(),
          diagram: response.data?.diagram,
          images: response.data?.images || response.images || [], // Extract images from response
        };

        setMessages(prev => [...prev, botMessage]);
        setConversationId(response.conversationId);
        setRetryCount(0);

        // Update contextual suggestions if provided by the API response
        if (response.data.suggestedQuestions && response.data.suggestedQuestions.length > 0) {
          setContextualSuggestions(response.data.suggestedQuestions.slice(0, 4));
        }

        // Load general suggested questions for welcome screen
        if (response.data.suggestedQuestions) {
          setSuggestedQuestions(response.data.suggestedQuestions);
        } else {
          loadSuggestedQuestions();
        }
      } else {
        handleMessageError(response.error, messageText);
      }
    } catch (error) {
      handleMessageError(error.message, messageText);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMessageError = (error, originalMessage) => {
    const errorMessage = {
      id: Date.now() + 1,
      text: error,
      isUser: false,
      timestamp: new Date().toISOString(),
      isError: true,
      retryAction: () => handleRetryMessage(originalMessage),
    };

    setMessages(prev => [...prev, errorMessage]);
    setConnectionError(error);
  };

  const handleRetryMessage = (messageText) => {
    setRetryCount(prev => prev + 1);
    if (retryCount < 3) {
      handleSendMessage(messageText);
    } else {
      setConnectionError('Maximum retry attempts reached. Please refresh and try again.');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleInputChange = (e) => {
    const textarea = e.target;
    setInputValue(textarea.value);
    
    // Auto-resize textarea
    textarea.style.height = 'auto';
    const scrollHeight = Math.min(textarea.scrollHeight, 120);
    const newHeight = Math.max(50, scrollHeight);
    textarea.style.height = newHeight + 'px';
    
    // Update state based on whether textarea expanded beyond minimum height
    const isExpanded = newHeight > 50;
    setIsTextareaExpanded(isExpanded);
  };

  const handleSuggestedQuestionClick = (question) => {
    handleSendMessage(question);
  };

  const handleRefresh = () => {
    // Clear all messages and reset conversation
    setMessages([]);
    setInputValue('');
    setIsTextareaExpanded(false);
    setConversationId(null);
    setConnectionError(null);
    setRetryCount(0);
    setContextualSuggestions([]);
    setLoadingContextualSuggestions(false);
    
    // Reload suggested questions
    loadSuggestedQuestions();
    
    // Scroll to top
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleInfoClick = () => {
    setShowInfoTooltip(!showInfoTooltip);
  };

  // Close tooltip when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showInfoTooltip && !event.target.closest('.info-button') && !event.target.closest('.info-tooltip')) {
        setShowInfoTooltip(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showInfoTooltip]);

  const handleKeywordClick = (keyword) => {
    setInputValue(keyword);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleVoiceInput = () => {
    if (!recognition) {
      setConnectionError('Voice recognition is not supported in your browser.');
      return;
    }

    if (isRecording) {
      // Stop recording
      recognition.stop();
      setIsRecording(false);
    } else {
      // Start recording
      try {
        setConnectionError(null);
        recognition.start();
        setIsRecording(true);
      } catch (error) {
        console.error('Failed to start voice recognition:', error);
        setConnectionError('Failed to start voice recognition. Please try again.');
        setIsRecording(false);
      }
    }
  };

  const renderWelcomeMessage = () => {
    const suggestedKeywords = [
      "DGFT", "IEC", "Export License", "Import Policy", 
      "Duty Drawback", "SEZ", "Trade Documentation", 
      "Customs", "EXIM Policy", "Foreign Trade"
    ];

    return (
      <WelcomeContainer>
        <WelcomeIcon>
          <ChatBotIcon size={60} />
        </WelcomeIcon>
        <WelcomeTitle>Welcome! I'm here to help</WelcomeTitle>
        
        <SuggestedKeywordsContainer>
          <KeywordsTitle>Suggested Keywords</KeywordsTitle>
          <KeywordsGrid>
            {suggestedKeywords.map((keyword, index) => (
              <KeywordTag
                key={index}
                onClick={() => handleKeywordClick(keyword)}
                title={`Click to search for ${keyword}`}
              >
                {keyword}
              </KeywordTag>
            ))}
          </KeywordsGrid>
        </SuggestedKeywordsContainer>
      </WelcomeContainer>
    );
  };

  return (
    <ChatContainer>
      <Header>
        <HeaderLeft>
          <ChatGPTLogo>
            <ChatBotIcon size={50} />
          </ChatGPTLogo>
          <div>
            <HeaderTitle>Query Assistant</HeaderTitle>
          </div>
        </HeaderLeft>
        <HeaderRight>
          <RefreshButton onClick={handleRefresh} title="Refresh conversation">
            <RefreshIcon />
          </RefreshButton>
        </HeaderRight>
      </Header>

      {connectionError && (
        <ErrorBanner>
          {connectionError}
        </ErrorBanner>
      )}

      <MessagesContainer isHomePage={messages.length === 0}>
        {messages.length === 0 && renderWelcomeMessage()}
        
        {messages.map((message) => (
          <MessageWrapper key={message.id}>
            <MessageBubble
              message={message.text}
              isUser={message.isUser}
              timestamp={message.timestamp}
              isError={message.isError}
              onRetry={message.retryAction}
            />
            {message.diagram && (
              <div style={{ padding: '8px 24px' }}>
                <DiagramPreview
                  diagram={message.diagram}
                  title={message.diagram.title || "Generated Diagram"}
                  description={message.diagram.description}
                  type={message.diagram.type}
                />
              </div>
            )}
            {message.images && message.images.length > 0 && (
              <ImageGallery images={message.images} />
            )}
          </MessageWrapper>
        ))}
        
        {isLoading && (
          <MessageWrapper>
            <MessageBubble
              isUser={false}
              isTyping={true}
            />
          </MessageWrapper>
        )}
        
        <div ref={messagesEndRef} />
      </MessagesContainer>

      {/* Show contextual suggestions after user asks a question */}
      {/* <ContextualSuggestionsContainer visible={(contextualSuggestions.length > 0 || loadingContextualSuggestions) && !isLoading}>
        <ContextualTitle>Related Questions You Might Ask</ContextualTitle>
        <SuggestedQuestions
          questions={contextualSuggestions}
          onQuestionClick={handleSuggestedQuestionClick}
          loading={loadingContextualSuggestions}
          context="contextual"
        />
      </ContextualSuggestionsContainer> */}

      <InputContainer>
        <InputWrapper>
          <TextInputContainer>
            <TextInput
              ref={inputRef}
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={isRecording ? "" : "Ask your queries"}
              disabled={isLoading}
              rows={1}
            />
            <SoundWaves isRecording={isRecording}>
              <div className="wave"></div>
              <div className="wave"></div>
              <div className="wave"></div>
              <div className="wave"></div>
              <div className="wave"></div>
              <div className="wave"></div>
              <div className="wave"></div>
            </SoundWaves>
          </TextInputContainer>
          <MicButton
            onClick={handleVoiceInput}
            isRecording={isRecording}
            disabled={isLoading}
            hasContent={isTextareaExpanded}
          >
            <MicrophoneIcon isRecording={isRecording} />
            <Tooltip className="tooltip">Dictate</Tooltip>
          </MicButton>
          <SendButton
            onClick={() => handleSendMessage()}
            disabled={!inputValue.trim() || isLoading}
            title="Send message"
            hasContent={isTextareaExpanded}
          >
            <SendIcon />
          </SendButton>
        </InputWrapper>
      </InputContainer>
    </ChatContainer>
  );
};

export default ChatBox;