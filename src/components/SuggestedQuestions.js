import React, { useState, useEffect } from 'react';
import styled, { keyframes } from 'styled-components';

const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const Container = styled.div`
  margin: 16px 0;
  animation: ${fadeIn} 0.3s ease-out;
`;

const QuestionsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
  max-width: 100%;
`;

const QuestionCard = styled.button`
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  line-height: 1.5;
  color: #374151;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 80px;
  
  &:hover {
    border-color: #10a37f;
    box-shadow: 0 2px 8px rgba(16, 163, 127, 0.1);
    transform: translateY(-1px);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;

const QuestionIcon = styled.div`
  width: 24px;
  height: 24px;
  background: #f3f4f6;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #6b7280;
  flex-shrink: 0;
`;

const QuestionText = styled.div`
  font-weight: 500;
  color: #1f2937;
  flex: 1;
`;

const QuestionDescription = styled.div`
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
`;

const LoadingContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
  margin: 16px 0;
`;

const LoadingCard = styled.div`
  height: 80px;
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 12px;
  
  @keyframes loading {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }
`;

const EmptyState = styled.div`
  text-align: center;
  color: #6b7280;
  font-size: 14px;
  padding: 24px;
  font-style: italic;
`;


const defaultQuestions = [
  {
    text: "Explain a complex topic",
    description: "Break down any subject in simple terms",
    icon: "📚"
  },
  {
    text: "Help me write something",
    description: "Emails, essays, code, or creative content",
    icon: "✍️"
  },
  {
    text: "Brainstorm ideas",
    description: "Creative solutions and innovative thinking",
    icon: "💡"
  },
  {
    text: "Analyze and summarize",
    description: "Extract key insights from information",
    icon: "📊"
  }
];

const SuggestedQuestions = ({ 
  questions = [], 
  onQuestionClick, 
  loading = false, 
  context = ''
}) => {
  const [displayQuestions, setDisplayQuestions] = useState([]);

  useEffect(() => {
    // Convert string questions to question objects if needed
    let questionsToShow = questions.length > 0 ? questions : defaultQuestions;
    
    if (questionsToShow.length > 0 && typeof questionsToShow[0] === 'string') {
      questionsToShow = questionsToShow.map((q, index) => ({
        text: q,
        description: "Click to ask this question",
        icon: ["💬", "❓", "🤔", "💭"][index % 4]
      }));
    }
    
    setDisplayQuestions(questionsToShow);
  }, [questions]);

  const handleQuestionClick = (question) => {
    if (onQuestionClick) {
      const questionText = typeof question === 'string' ? question : question.text;
      onQuestionClick(questionText);
    }
  };

  if (loading) {
    return (
      <LoadingContainer>
        <LoadingCard />
        <LoadingCard />
        <LoadingCard />
        <LoadingCard />
      </LoadingContainer>
    );
  }

  if (displayQuestions.length === 0) {
    return (
      <EmptyState>
        No suggested questions available at the moment.
      </EmptyState>
    );
  }

  return (
    <Container>
      <QuestionsGrid>
        {displayQuestions.map((question, index) => (
          <QuestionCard
            key={index}
            onClick={() => handleQuestionClick(question)}
            title={typeof question === 'string' ? question : question.text}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <QuestionIcon>
                {typeof question === 'string' ? '💬' : question.icon}
              </QuestionIcon>
              <div style={{ flex: 1 }}>
                <QuestionText>
                  {typeof question === 'string' ? question : question.text}
                </QuestionText>
                {typeof question === 'object' && question.description && (
                  <QuestionDescription>
                    {question.description}
                  </QuestionDescription>
                )}
              </div>
            </div>
          </QuestionCard>
        ))}
      </QuestionsGrid>
    </Container>
  );
};

export default SuggestedQuestions;