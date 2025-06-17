// Configuration
const API_BASE_URL = 'http://localhost:3001/api';

// Function to translate Gen Z text to normal English using our server
async function translateGenZ(text) {
    try {
        const response = await fetch(`${API_BASE_URL}/translate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });

        if (!response.ok) {
            throw new Error('Translation request failed');
        }

        const data = await response.json();
        return data.translation;
    } catch (error) {
        console.error('Translation error:', error);
        return text; // Return original text if translation fails
    }
}

// Function to detect if text might contain Gen Z slang
async function containsGenZSlang(text) {
    try {
        const response = await fetch(`${API_BASE_URL}/detect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });

        if (!response.ok) {
            throw new Error('Detection request failed');
        }

        const data = await response.json();
        return data.isGenZ;
    } catch (error) {
        console.error('Detection error:', error);
        return false; // Return false if detection fails
    }
}

// Export the functions
export { translateGenZ, containsGenZSlang }; 