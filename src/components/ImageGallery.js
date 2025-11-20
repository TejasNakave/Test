import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import styled from 'styled-components';

const GalleryContainer = styled.div`
  margin: 16px 0;
  padding: 0;
  background: transparent;
  border-radius: 0;
  border: none;
  width: 100%;
  max-width: 800px;
  margin: 16px auto;
`;

const GalleryHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 0;
  padding: 16px;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  background: #f8fafc;
  border-radius: 12px 12px 0 0;
  border: 1px solid #e2e8f0;
  border-bottom: none;
`;

const ImageIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
    <circle cx="8.5" cy="8.5" r="1.5"/>
    <polyline points="21,15 16,10 5,21"/>
  </svg>
);

const ImagesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  padding: 0 16px 16px 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-top: none;
  border-radius: 0 0 12px 12px;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const ImageCard = styled.div`
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  transition: all 0.2s ease;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    border-color: #10a37f;
  }
`;

const ImageContainer = styled.div`
  width: 100%;
  height: 160px;
  overflow: hidden;
  position: relative;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const Image = styled.img`
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: transform 0.2s ease;
  
  ${ImageCard}:hover & {
    transform: scale(1.05);
  }
`;

const ImageInfo = styled.div`
  padding: 12px;
`;

const ImageTitle = styled.div`
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

const ImageDescription = styled.div`
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

const RelevanceScore = styled.div`
  font-size: 11px;
  color: #10a37f;
  font-weight: 500;
  margin-top: 6px;
`;

const LoadingState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 160px;
  color: #6b7280;
  font-size: 12px;
`;

const ErrorState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 160px;
  color: #ef4444;
  font-size: 12px;
  text-align: center;
  padding: 12px;
`;

const BackArrowIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="19" y1="12" x2="5" y2="12"></line>
    <polyline points="12 19 5 12 12 5"></polyline>
  </svg>
);

const Modal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.95);
  display: flex;
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
  background: white;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
`;

const ModalImageContainer = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  padding: 80px 24px 24px 24px;
  overflow: auto;
`;

const ModalImage = styled.img`
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
`;

const ModalInfo = styled.div`
  padding: 20px 24px;
  border-top: 1px solid #e2e8f0;
  background: white;
  max-height: 25%;
  overflow-y: auto;
`;

const CloseButton = styled.button`
  position: absolute;
  top: 20px;
  left: 20px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: none;
  border-radius: 50px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #1f2937;
  font-size: 13px;
  font-weight: 500;
  font-family: 'Poppins', sans-serif;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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

const ImageGallery = ({ images = [] }) => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [imageErrors, setImageErrors] = useState({});
  const [imageLoading, setImageLoading] = useState({});

  // Handle ESC key to close modal
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && selectedImage) {
        setSelectedImage(null);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [selectedImage]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (selectedImage) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [selectedImage]);

  if (!images || images.length === 0) {
    return null;
  }

  const handleImageLoad = (filename) => {
    if (filename) {
      setImageLoading(prev => ({ ...prev, [filename]: false }));
    }
  };

  const handleImageError = (filename) => {
    if (filename) {
      setImageErrors(prev => ({ ...prev, [filename]: true }));
      setImageLoading(prev => ({ ...prev, [filename]: false }));
    }
  };

  const handleImageClick = (image) => {
    setSelectedImage(image);
  };

  const closeModal = () => {
    setSelectedImage(null);
  };

  const formatRelevanceScore = (score) => {
    return `${Math.round(score * 100)}% relevant`;
  };

  return (
    <>
      <GalleryContainer>
        <GalleryHeader>
          <ImageIcon />
          Visual Materials ({images.length})
        </GalleryHeader>
        
        <ImagesGrid>
          {images.map((image, index) => {
            const filename = image.image_filename || `image_${index}`;
            const hasError = imageErrors[filename];
            const isLoading = imageLoading[filename] !== false && !hasError;
            
            return (
              <ImageCard 
                key={filename}
                onClick={() => handleImageClick(image)}
              >
                <ImageContainer>
                  {isLoading && (
                    <LoadingState>Loading image...</LoadingState>
                  )}
                  
                  {hasError ? (
                    <ErrorState>
                      Failed to load image
                      <br />
                      {filename}
                    </ErrorState>
                  ) : (
                    <Image
                      src={`data:image/png;base64,${image.base64_data}`}
                      alt={filename}
                      onLoad={() => handleImageLoad(filename)}
                      onError={() => handleImageError(filename)}
                      style={{
                        display: isLoading ? 'none' : 'block'
                      }}
                    />
                  )}
                </ImageContainer>
                
                <ImageInfo>
                  <ImageTitle>
                    {image.image_filename ? image.image_filename.replace(/\.(png|jpg|jpeg|gif)$/i, '') : `Image ${index + 1}`}
                  </ImageTitle>
                  
                  {image.analysis && (
                    <ImageDescription>
                      {image.analysis.length > 100 
                        ? `${image.analysis.substring(0, 100)}...`
                        : image.analysis
                      }
                    </ImageDescription>
                  )}
                  
                  {image.relevance_score > 0 && (
                    <RelevanceScore>
                      {formatRelevanceScore(image.relevance_score)}
                    </RelevanceScore>
                  )}
                </ImageInfo>
              </ImageCard>
            );
          })}
        </ImagesGrid>
      </GalleryContainer>

      {/* Modal for enlarged view */}
      {selectedImage && ReactDOM.createPortal(
        <Modal onClick={closeModal}>
          <ModalContent onClick={(e) => e.stopPropagation()}>
            <CloseButton onClick={closeModal}>
              <BackArrowIcon />
              Go Back
            </CloseButton>
            
            <ModalImageContainer>
              <ModalImage
                src={`data:image/png;base64,${selectedImage.base64_data}`}
                alt={selectedImage.image_filename || 'Selected image'}
              />
            </ModalImageContainer>
          </ModalContent>
        </Modal>,
        document.body
      )}
    </>
  );
};

export default ImageGallery;