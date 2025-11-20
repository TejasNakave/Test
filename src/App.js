import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ChatPage from './pages/ChatPage';
import styled from 'styled-components';

const AppContainer = styled.div`
  height: 100vh;
  width: 100vw;
  max-height: 100vh;
  max-width: 100vw;
  display: flex;
  flex-direction: column;
  background: #f7f7f8;
  font-family: "Poppins", sans-serif !important;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  margin: 0;
  padding: 0;
`;

function App() {
  return (
    <AppContainer>
      <Router>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/chat" element={<ChatPage />} />
        </Routes>
      </Router>
    </AppContainer>
  );
}

export default App;
