import React, { useState } from 'react';
import LedDisplay from './components/LedDisplay';

const App: React.FC = () => {
    const [ledStates, setLedStates] = useState<boolean[]>(Array(10).fill(false));

    const toggleLed = (index: number) => {
        const newStates = [...ledStates];
        newStates[index] = !newStates[index];
        setLedStates(newStates);
    };

    const numLeds = ledStates.length;
    
    return (
        <div>
            <h1>Virtual LED Display</h1>
            <LedDisplay numLeds={numLeds} ledStates={ledStates} toggleLed={toggleLed} />
        </div>
    );
};

export default App;