// NLP Constants and Utilities
const POSITIVE_WORDS = ['happy', 'joy', 'peaceful', 'excited', 'love', 'wonderful'];
const NEGATIVE_WORDS = ['scared', 'afraid', 'angry', 'sad', 'terrible', 'nightmare'];

const NLP = {
    tokenize: (text) => {
        return text.toLowerCase()
            .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, '')
            .split(/\s+/)
            .filter(word => word.length > 2);
    },

    extractPhrases: (text, n = 2) => {
        const words = NLP.tokenize(text);
        const phrases = [];
        for (let i = 0; i <= words.length - n; i++) {
            phrases.push(words.slice(i, i + n).join(' '));
        }
        return phrases;
    },

    analyzeSentiment: (text) => {
        const words = NLP.tokenize(text);
        let score = 0;
        words.forEach(word => {
            if (POSITIVE_WORDS.includes(word)) score++;
            if (NEGATIVE_WORDS.includes(word)) score--;
        });
        return {
            score,
            sentiment: score > 0 ? 'positive' : score < 0 ? 'negative' : 'neutral'
        };
    }
};

function analyzeDream(dreamText) {
    const words = NLP.tokenize(dreamText);
    const phrases = NLP.extractPhrases(dreamText);
    const sentiment = NLP.analyzeSentiment(dreamText);
    
    const wordFrequencies = {};
    words.forEach(word => {
        wordFrequencies[word] = (wordFrequencies[word] || 0) + 1;
    });

    const themes = Object.entries(wordFrequencies)
        .filter(([_, count]) => count > 1)
        .map(([word, count]) => ({
            word,
            count,
            related: phrases.filter(phrase => phrase.includes(word))
        }));

    return {
        sentiment,
        themes,
        wordFrequencies,
        commonPhrases: phrases.filter((phrase, index, self) => 
            self.indexOf(phrase) !== index
        )
    };
}

function getToken() {
    return localStorage.getItem('token');
}

function setAuthHeader() {
    const token = getToken();
    if (!token || !isTokenValid(token)) {
        throw new Error('auth_error');
    }
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

function isTokenValid(token) {
    if (!token) return false;
    
    try {
        const [, payload] = token.split('.');
        if (!payload) return false;
        
        const decodedPayload = JSON.parse(atob(payload));
        const expirationTime = decodedPayload.exp * 1000;
        
        return expirationTime > (Date.now() + 300000);
    } catch (error) {
        console.error('Token validation error:', error);
        return false;
    }
}

function checkAuthStatus() {
    const token = getToken();
    
    if (!token || !isTokenValid(token)) {
        logout();
        return;
    }
    
    document.getElementById('auth-section').classList.add('hidden');
    document.getElementById('app-section').classList.remove('hidden');
    
    // Load initial data with proper error handling
    Promise.all([loadDreams(), loadInsights()])
        .catch(error => {
            console.error('Error loading initial data:', error);
            if (error.message === 'auth_error') {
                logout();
            }
        });
}

function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.token) {
            localStorage.setItem('token', data.token);
            // Initialize the app section
            document.getElementById('auth-section').classList.add('hidden');
            document.getElementById('app-section').classList.remove('hidden');
            
            // Load initial data
            Promise.all([loadDreams(), loadInsights()])
                .catch(error => console.error('Error loading initial data:', error));
                
            event.target.reset();
        } else {
            alert('Login failed: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Login failed: ' + error.message);
    });
}

function validatePassword(password) {
    // Minimum 8 characters
    if (password.length < 8) {
        return {
            isValid: false,
            message: 'Password must be at least 8 characters long'
        };
    }

    // Must contain at least one letter
    if (!/[a-zA-Z]/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one letter'
        };
    }

    // Must contain at least one number
    if (!/[0-9]/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one number'
        };
    }

    // Must contain at least one special character
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
        return {
            isValid: false,
            message: 'Password must contain at least one special character'
        };
    }

    return {
        isValid: true,
        message: 'Password is valid'
    };
}

// Updated register handler with password validation
async function handleRegister(event) {
    event.preventDefault();
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;

    // Validate password
    const passwordValidation = validatePassword(password);
    if (!passwordValidation.isValid) {
        alert(passwordValidation.message);
        return;
    }

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();
        if (response.ok) {
            alert('Registration successful!');
            // Clear form and switch to login
            document.getElementById('register-username').value = '';
            document.getElementById('register-password').value = '';
            toggleForms({ preventDefault: () => {} });
        } else {
            alert(`Registration failed: ${data.message || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Registration failed: Network error.');
    }
}

function toggleForms(event) {
    event.preventDefault();
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    loginForm.classList.toggle('hidden');
    registerForm.classList.toggle('hidden');
}

function logout() {
    localStorage.removeItem('token');
    document.getElementById('app-section').classList.add('hidden');
    document.getElementById('auth-section').classList.remove('hidden');
    
    const forms = document.querySelectorAll('form');
    forms.forEach(form => form.reset());
    
    ['dreams-container', 'mood-trends', 'recurring-themes', 'feedback'].forEach(id => {
        const element = document.getElementById(id);
        if (element) element.innerHTML = '';
    });
}

function startTokenCheck() {
    setInterval(async () => {
        const token = getToken();
        if (token && !isTokenValid(token)) {
            try {
                await refreshToken();
            } catch (error) {
                console.error('Token refresh failed:', error);
                logout();
            }
        }
    }, 60000);
}

async function loadInsights() {
    try {
        const response = await authenticatedFetch('/get_dreams');
        
        if (!response) {
            console.log('No response from authenticatedFetch');
            return;
        }

        if (!response.ok) {
            throw new Error(`Failed to fetch insights: ${response.status}`);
        }

        const data = await response.json();
        console.log('Loaded insights:', data); // Debug log
        
        if (Array.isArray(data.dreams)) {
            updateInsightsUI(data.dreams);
        } else {
            console.error('Invalid insights data format:', data);
        }
    } catch (error) {
        console.error('Error loading insights:', error);
        if (error.message.includes('token')) {
            logout();
        }
    }
}

// Modified handleDreamSubmit function to fix logout issues
function processQueue(error, token = null) {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
}

async function getValidToken() {
    const token = getToken();
    if (!token) throw new Error('No token found');

    if (!isTokenValid(token)) {
        try {
            const newToken = await refreshToken();
            return newToken;
        } catch (error) {
            throw new Error('auth_error');
        }
    }
    return token;
}

function updateDreamsUI(dreams) {
    const container = document.getElementById('dreams-container');
    if (!container) return;

    if (!dreams || dreams.length === 0) {
        container.innerHTML = '<p>No dreams recorded yet.</p>';
        return;
    }

    let dreamsHTML = '<div class="dreams-list">';
    dreams.forEach(dream => {
        const date = new Date(dream.timestamp).toLocaleDateString();
        const analysis = dream.analysis || { sentiment: { sentiment: 'neutral' } };
        
        dreamsHTML += `
            <div class="dream-entry">
                <div class="dream-header">
                    <span class="dream-date">${date}</span>
                    <span class="dream-mood ${analysis.sentiment.sentiment}">
                        Mood: ${analysis.sentiment.sentiment}
                    </span>
                </div>
                <div class="dream-content">
                    <p>${dream.dream_text}</p>
                </div>
            </div>
        `;
    });
    dreamsHTML += '</div>';
    container.innerHTML = dreamsHTML;
}

async function refreshToken() {
    if (isRefreshing) {
        return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
        });
    }

    isRefreshing = true;
    try {
        const currentToken = getToken();
        const response = await fetch('/refresh_token', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        if (!response.ok) throw new Error('Token refresh failed');

        localStorage.setItem('token', data.token);
        isRefreshing = false;
        processQueue(null, data.token);
        return data.token;
    } catch (error) {
        isRefreshing = false;
        processQueue(error);
        throw error;
    }
}

// Token management configuration
const TOKEN_CONFIG = {
    refreshThreshold: 30 * 60 * 1000, // 30 minutes in ms
    retryDelay: 1000,
    maxRetries: 3
};

let isRefreshing = false;
let refreshSubscribers = [];

function addRefreshSubscriber(callback) {
    refreshSubscribers.push(callback);
}

function onTokenRefreshed(token) {
    refreshSubscribers.forEach(callback => callback(token));
    refreshSubscribers = [];
}

async function refreshToken() {
    if (isRefreshing) {
        return new Promise((resolve, reject) => {
            refreshSubscribers.push({ resolve, reject });
        });
    }

    isRefreshing = true;
    const currentToken = getToken();

    try {
        const response = await fetch('/refresh_token', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error('Token refresh failed');
        }

        localStorage.setItem('token', data.token);
        refreshSubscribers.forEach(subscriber => subscriber.resolve(data.token));
        refreshSubscribers = [];
        isRefreshing = false;
        return data.token;
    } catch (error) {
        refreshSubscribers.forEach(subscriber => subscriber.reject(error));
        refreshSubscribers = [];
        isRefreshing = false;
        throw error;
    }
}

async function handleTokenRefresh(token) {
    if (!isRefreshing) {
        isRefreshing = true;
        try {
            const response = await fetch('/refresh_token', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) throw new Error('Refresh failed');
            
            const data = await response.json();
            localStorage.setItem('token', data.token);
            onTokenRefreshed(data.token);
            isRefreshing = false;
            return data.token;
        } catch (error) {
            isRefreshing = false;
            logout();
            throw error;
        }
    }
    
    return new Promise(resolve => {
        addRefreshSubscriber(token => resolve(token));
    });
}

async function authenticatedFetch(url, options = {}) {
    let token = getToken();
    
    if (!token) {
        logout();
        return null;
    }

    try {
        if (!isTokenValid(token)) {
            token = await refreshToken();
        }

        const response = await fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.status === 401) {
            // Only try to refresh once
            token = await refreshToken();
            return authenticatedFetch(url, options);
        }

        return response;
    } catch (error) {
        if (error.message.includes('Token refresh failed') || error.message.includes('Failed to fetch')) {
            logout();
            return null;
        }
        throw error;
    }
}

async function handleDreamSubmit(event) {
    event.preventDefault();
    const submitButton = event.target.querySelector('button');
    const textarea = event.target.querySelector('textarea');
    const dreamText = textarea.value.trim();

    if (!dreamText) {
        alert('Please enter your dream before submitting.');
        return;
    }

    submitButton.disabled = true;
    submitButton.textContent = 'Saving...';

    try {
        // Log the dream text and analysis for debugging
        console.log('Submitting dream:', dreamText);
        const analysis = analyzeDream(dreamText);
        console.log('Analysis:', analysis);

        const token = getToken();
        if (!token) {
            throw new Error('No authentication token found');
        }

        const response = await fetch('/add_dream', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dream_text: dreamText,
                mood_score: analysis.sentiment.score,
                analysis: analysis
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Server response:', data);

        if (data.dream_id) {
            // Clear the form
            textarea.value = '';
            
            // Refresh the dreams and insights
            try {
                await loadDreams();
                await loadInsights();
                alert('Dream saved successfully!');
            } catch (loadError) {
                console.error('Error refreshing data:', loadError);
            }
        } else {
            throw new Error('No dream_id in response');
        }
    } catch (error) {
        console.error('Error saving dream:', error);
        alert('Failed to save dream. Please try again.');
        
        // If it's an authentication error, logout
        if (error.message.includes('authentication') || 
            error.message.includes('token') || 
            error.status === 401) {
            logout();
        }
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Save Dream';
    }
}

// Updated loadDreams function
async function loadDreams() {
    try {
        const response = await authenticatedFetch('/get_dreams');
        
        if (!response) {
            console.log('No response from authenticatedFetch');
            return;
        }

        if (!response.ok) {
            throw new Error(`Failed to fetch dreams: ${response.status}`);
        }

        const data = await response.json();
        console.log('Loaded dreams:', data); // Debug log
        
        if (Array.isArray(data.dreams)) {
            updateDreamsUI(data.dreams);
        } else {
            console.error('Invalid dreams data format:', data);
        }
    } catch (error) {
        console.error('Error loading dreams:', error);
    }
}

function updateInsightsUI(dreams) {
    const moodTrends = analyzeMoodTrends(dreams);
    const moodTrendsElement = document.getElementById('mood-trends');
    if (moodTrendsElement) {
        moodTrendsElement.innerHTML = `
            <h3>Mood Trends</h3>
            <ul>
                <li><strong>Average Mood:</strong> ${moodTrends.averageMood}</li>
                <li><strong>Trend:</strong> ${moodTrends.trend}</li>
                <li><strong>Dominant Mood:</strong> ${moodTrends.dominantMood}</li>
            </ul>
        `;
    }

    const themes = analyzeRecurringThemes(dreams);
    const themesElement = document.getElementById('recurring-themes');
    if (themesElement) {
        let themesHtml = '<h3>Recurring Themes</h3>';
        if (themes.length) {
            themes.forEach((theme, index) => {
                themesHtml += `
                    <div class="theme">
                        <h4>Theme ${index + 1}</h4>
                        <p>Keywords: ${theme.keywords.join(', ')}</p>
                        <p>Frequency: ${theme.frequency}</p>
                    </div>
                `;
            });
        } else {
            themesHtml += '<p>No recurring themes identified yet.</p>';
        }
        themesElement.innerHTML = themesHtml;
    }

    const feedbackElement = document.getElementById('feedback');
    if (feedbackElement) {
        feedbackElement.innerHTML = `
            <h3>Dream Analysis Insights</h3>
            <p>${generateInsights(dreams)}</p>
        `;
    }
}

function analyzeMoodTrends(dreams) {
    if (!dreams?.length) {
        return {
            averageMood: 0,
            trend: 'stable',
            dominantMood: 'neutral'
        };
    }

    const sentiments = dreams.map(dream => dream.analysis?.sentiment?.score || 0);
    const averageMood = sentiments.reduce((a, b) => a + b, 0) / sentiments.length;
    
    const recentSentiments = sentiments.slice(-3);
    const trend = recentSentiments.length > 1 ? 
        (recentSentiments[recentSentiments.length - 1] > recentSentiments[0] ? 'improving' : 
         recentSentiments[recentSentiments.length - 1] < recentSentiments[0] ? 'declining' : 'stable') : 
        'stable';

    const moodCounts = dreams.reduce((acc, dream) => {
        const mood = dream.analysis?.sentiment?.sentiment || 'neutral';
        acc[mood] = (acc[mood] || 0) + 1;
        return acc;
    }, {});
    
    const dominantMood = Object.entries(moodCounts)
        .sort((a, b) => b[1] - a[1])[0][0];

    return {
        averageMood: averageMood.toFixed(1),
        trend,
        dominantMood
    };
}

function analyzeRecurringThemes(dreams) {
    if (!dreams?.length) return [];

    // Combine all dream texts for analysis
    const allDreamTexts = dreams.map(dream => dream.dream_text).join(' ');
    const words = NLP.tokenize(allDreamTexts);
    const phrases = NLP.extractPhrases(allDreamTexts);
    
    // Count word frequencies
    const wordFrequencies = {};
    words.forEach(word => {
        wordFrequencies[word] = (wordFrequencies[word] || 0) + 1;
    });

    // Find significant themes (words that appear multiple times)
    const themes = Object.entries(wordFrequencies)
        .filter(([word, count]) => count >= 2) // Words appearing at least twice
        .map(([word, count]) => ({
            theme: word,
            keywords: [word, ...phrases.filter(phrase => phrase.includes(word))],
            frequency: count
        }))
        .sort((a, b) => b.frequency - a.frequency)
        .slice(0, 3); // Get top 3 themes

    return themes;
}

function updateInsightsUI(dreams) {
    // Mood Trends section (unchanged)
    const moodTrends = analyzeMoodTrends(dreams);
    const moodTrendsElement = document.getElementById('mood-trends');
    if (moodTrendsElement) {
        moodTrendsElement.innerHTML = `
            <h3>Mood Trends</h3>
            <ul>
                <li><strong>Average Mood:</strong> ${moodTrends.averageMood}</li>
                <li><strong>Trend:</strong> ${moodTrends.trend}</li>
                <li><strong>Dominant Mood:</strong> ${moodTrends.dominantMood}</li>
            </ul>
        `;
    }

    // Updated Recurring Themes section
    const themes = analyzeRecurringThemes(dreams);
    const themesElement = document.getElementById('recurring-themes');
    if (themesElement) {
        let themesHtml = '<h3>Recurring Themes</h3>';
        if (themes && themes.length > 0) {
            themes.forEach((theme, index) => {
                themesHtml += `
                    <div class="theme-item">
                        <p><strong>Theme ${index + 1}: ${theme.theme}</strong></p>
                        <p>Keywords: ${theme.keywords.slice(0, 5).join(', ')}</p>
                        <p>Frequency: ${theme.frequency} occurrences</p>
                    </div>
                `;
            });
        } else {
            themesHtml += '<p>No recurring themes identified yet.</p>';
        }
        themesElement.innerHTML = themesHtml;
    }

    // Feedback section
    const feedbackElement = document.getElementById('feedback');
    if (feedbackElement) {
        const insights = generateInsights(dreams, themes, moodTrends);
        feedbackElement.innerHTML = `
            <h3>Dream Analysis Insights</h3>
            <p>${insights}</p>
        `;
    }
}

function generateInsights(dreams, themes, moodTrends) {
    if (!dreams?.length) {
        return "Start recording your dreams to receive personalized insights.";
    }

    const insights = [];
    insights.push(`Based on analysis of your ${dreams.length} recorded dreams:`);

    if (moodTrends) {
        insights.push(`Your dreams show a ${moodTrends.trend} emotional pattern with ${moodTrends.dominantMood} being the dominant mood`);
    }

    if (themes && themes.length > 0) {
        const themeInsight = themes
            .map(theme => `"${theme.theme}" (appearing ${theme.frequency} times)`)
            .join(', ');
        insights.push(`Most common themes include: ${themeInsight}`);
    }

    return insights.join('. ') + '.';
}

function startTokenCheck() {
    // Check token validity every minute
    setInterval(async () => {
        const token = getToken();
        if (token && !isTokenValid(token)) {
            try {
                await refreshToken();
            } catch (error) {
                console.error('Token refresh failed:', error);
                logout();
            }
        }
    }, 60000); // Check every minute
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Initializing app...');
    const token = getToken();
    
    if (!token || !isTokenValid(token)) {
        console.log('No valid token found - redirecting to login');
        logout();
    } else {
        console.log('Valid token found - initializing app');
        document.getElementById('auth-section').classList.add('hidden');
        document.getElementById('app-section').classList.remove('hidden');
        
        // Load initial data
        Promise.all([
            loadDreams().catch(error => {
                console.error('Error loading dreams during initialization:', error);
                if (error.message.includes('token') || error.message.includes('auth')) {
                    logout();
                }
            }),
            loadInsights().catch(error => {
                console.error('Error loading insights during initialization:', error);
                if (error.message.includes('token') || error.message.includes('auth')) {
                    logout();
                }
            })
        ]);
    }

    // Setup form handler
    const dreamForm = document.getElementById('dream-form');
    if (dreamForm) {
        console.log('Dream form found - attaching submit handler');
        dreamForm.addEventListener('submit', handleDreamSubmit);
    } else {
        console.error('Dream form not found in DOM');
    }

    // Start token validation check
    startTokenCheck();
    console.log('Token check interval started');
});