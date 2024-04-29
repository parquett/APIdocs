import React, { useState } from 'react';
import './App.css';

function App() {
  const [inputValue, setInputValue] = useState('');
  const [outputText, setOutputText] = useState(''); 

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
  };

  const handleSubmit = () => {
    const fetchedText = "Text from another resource"; 
    setOutputText(fetchedText);
  };

  return (
    <div className="App">
      <header className="App-header">API.docs</header>
      <div className="output-container">
        <p>{outputText}</p> {/* Output text is rendered here */}
      </div>
      <div className="input-container">
        <input
          type="text"
          placeholder="Enter some text"
          value={inputValue}
          onChange={handleInputChange}
        />
        <button onClick={handleSubmit}>
          <span className="arrow-icon">→</span>
        </button>
      </div>
      
    </div>
  );
}

export default App;
