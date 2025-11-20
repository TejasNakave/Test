import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import styled from 'styled-components';

// Icon Components
const BackArrowIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="19" y1="12" x2="5" y2="12"></line>
    <polyline points="12 19 5 12 12 5"></polyline>
  </svg>
);

const ExpandIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 3 21 3 21 9"></polyline>
    <polyline points="9 21 3 21 3 15"></polyline>
    <line x1="21" y1="3" x2="14" y2="10"></line>
    <line x1="3" y1="21" x2="10" y2="14"></line>
  </svg>
);

const DiagramIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="7" height="7"></rect>
    <rect x="14" y="3" width="7" height="7"></rect>
    <rect x="14" y="14" width="7" height="7"></rect>
    <rect x="3" y="14" width="7" height="7"></rect>
  </svg>
);

const DiagramContainer = styled.div`
  margin: 16px 0;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
`;

const DiagramHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
`;

const DiagramTitle = styled.h4`
  font-size: 15px;
  font-weight: 600;
  color: #374151;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ViewButton = styled.button`
  background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(74, 144, 226, 0.3);
  display: flex;
  align-items: center;
  gap: 6px;
  
  &:hover {
    background: linear-gradient(135deg, #357abd 0%, #2c6399 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.4);
  }
  
  &:active {
    transform: translateY(0);
  }
`;

const DiagramDescription = styled.p`
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 12px 0;
  line-height: 1.5;
`;

const DiagramPreviewImage = styled.img`
  width: 100%;
  max-height: 200px;
  object-fit: contain;
  border-radius: 8px;
  background: white;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  
  &:hover {
    transform: scale(1.02);
    border-color: #4a90e2;
    box-shadow: 0 4px 12px rgba(74, 144, 226, 0.2);
  }
`;

const Modal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.95);
  display: ${props => props.isOpen ? 'flex' : 'none'};
  align-items: center;
  justify-content: center;
  z-index: 99999;
  padding: 0;
  animation: fadeIn 0.3s ease;
  
  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
`;

const ModalContent = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  position: relative;
`;

const BackButton = styled.button`
  position: absolute;
  top: 20px;
  left: 20px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: none;
  color: #1f2937;
  padding: 8px 16px;
  border-radius: 50px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: 'Poppins', sans-serif;
  z-index: 100001;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  
  svg {
    width: 16px;
    height: 16px;
    transition: transform 0.3s ease;
  }
  
  &:hover {
    background: rgba(255, 255, 255, 1);
    transform: translateX(-4px) scale(1.05);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
    
    svg {
      transform: translateX(-2px);
    }
  }
  
  &:active {
    transform: translateX(-2px) scale(0.98);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  }
`;

const ModalBody = styled.div`
  flex: 1;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px 24px 24px 24px;
  background: #f8fafc;
`;

const ModalImage = styled.img`
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
`;

const DiagramPreview = ({ diagram, title, description, type }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isModalOpen) {
        setIsModalOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isModalOpen]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isModalOpen]);

  if (!diagram) {
    return null;
  }

  const imageUrl = diagram.url || diagram.imageUrl || (diagram.base64 ? `data:image/png;base64,${diagram.base64}` : null);

  if (!imageUrl) {
    return null;
  }

  const openModal = () => setIsModalOpen(true);
  const closeModal = () => setIsModalOpen(false);

  const modalContent = isModalOpen && (
    <Modal isOpen={isModalOpen} onClick={closeModal}>
      <ModalContent onClick={(e) => e.stopPropagation()}>
        <BackButton onClick={closeModal}>
          <BackArrowIcon />
          Go Back
        </BackButton>
        
        <ModalBody>
          <ModalImage
            src={imageUrl}
            alt={title || 'Diagram'}
          />
        </ModalBody>
      </ModalContent>
    </Modal>
  );

  return (
    <>
      <DiagramContainer>
        <DiagramHeader>
          <DiagramTitle>
            <DiagramIcon />
            {title || 'Process Diagram'}
          </DiagramTitle>
          <ViewButton onClick={openModal}>
            <ExpandIcon />
            View Fullscreen
          </ViewButton>
        </DiagramHeader>
        
        {description && (
          <DiagramDescription>{description}</DiagramDescription>
        )}
        
        <DiagramPreviewImage
          src={imageUrl}
          alt={title || 'Diagram'}
          onClick={openModal}
        />
      </DiagramContainer>

      {isModalOpen && ReactDOM.createPortal(modalContent, document.body)}
    </>
  );
};

export default DiagramPreview;