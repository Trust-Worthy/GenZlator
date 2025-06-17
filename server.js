require('dotenv').config();
const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const jwt = require('jsonwebtoken');
const cookieParser = require('cookie-parser');
const User = require('./models/User');
const Message = require('./models/Message');

const app = express();
const port = 3001;

// Hardcoded Gen Z slang dictionary
const genZDictionary = {
    'fr': 'for real',
    'no cap': 'no lie',
    'cap': 'lie',
    'bussin': 'really good',
    'slay': 'do well',
    'vibe': 'mood',
    'sus': 'suspicious',
    'based': 'good',
    'mid': 'average',
    'fire': 'excellent',
    'lit': 'exciting',
    'flex': 'show off',
    'ghost': 'ignore',
    'ship': 'relationship',
    'stan': 'fan',
    'tea': 'gossip',
    'yeet': 'throw',
    'simp': 'someone who tries too hard',
    'thicc': 'curvy',
    'woke': 'aware',
    'yolo': 'you only live once',
    'fomo': 'fear of missing out',
    'goat': 'greatest of all time',
    'salty': 'angry',
    'snatched': 'looking good',
    'spill the tea': 'share gossip',
    'throwing shade': 'criticizing',
    'unbothered': 'not caring',
    'vibe check': 'checking mood',
    'wig': 'amazing',
    'lowkey': 'secretly',
    'highkey': 'obviously',
    'bet': 'okay, sure',
    'deadass': 'seriously',
    'finna': 'going to',
    'fr fr': 'for real, for real',
    'glizzy': 'hot dog',
    'no shot': 'no way',
    'period': 'end of discussion',
    'sheesh': 'wow',
    'skull': 'laughing',
    'touch grass': 'go outside',
    'understood the assignment': 'doing well',
    'valid': 'good',
    'weirdchamp': 'weird',
    'zaddy': 'attractive man'
};

// Middleware
app.use(cors({
  origin: 'http://localhost:3000',
  credentials: true
}));
app.use(express.json());
app.use(cookieParser());
app.use(express.static('.'));

// Connect to MongoDB
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/genzlator', {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
.then(() => console.log('Connected to MongoDB'))
.catch(err => console.error('MongoDB connection error:', err));

// Authentication middleware
const auth = async (req, res, next) => {
  try {
    const token = req.cookies.token;
    if (!token) throw new Error('No token provided');

    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
    const user = await User.findById(decoded.userId);
    
    if (!user) throw new Error('User not found');
    
    req.user = user;
    next();
  } catch (error) {
    res.status(401).json({ error: 'Authentication failed' });
  }
};

// Register endpoint
app.post('/api/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;
    
    // Check if user already exists
    const existingUser = await User.findOne({ $or: [{ email }, { username }] });
    if (existingUser) {
      return res.status(400).json({ error: 'Username or email already exists' });
    }

    // Create new user
    const user = new User({ username, email, password });
    await user.save();

    // Generate token
    const token = jwt.sign(
      { userId: user._id },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '24h' }
    );

    // Set cookie
    res.cookie('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 24 * 60 * 60 * 1000 // 24 hours
    });

    res.status(201).json({
      message: 'User registered successfully',
      user: {
        id: user._id,
        username: user.username,
        email: user.email
      }
    });
  } catch (error) {
    res.status(500).json({ error: 'Registration failed' });
  }
});

// Login endpoint
app.post('/api/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    // Find user
    const user = await User.findOne({ email });
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Check password
    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Generate token
    const token = jwt.sign(
      { userId: user._id },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '24h' }
    );

    // Set cookie
    res.cookie('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 24 * 60 * 60 * 1000 // 24 hours
    });

    res.json({
      message: 'Login successful',
      user: {
        id: user._id,
        username: user.username,
        email: user.email
      }
    });
  } catch (error) {
    res.status(500).json({ error: 'Login failed' });
  }
});

// Logout endpoint
app.post('/api/logout', (req, res) => {
  res.clearCookie('token');
  res.json({ message: 'Logged out successfully' });
});

// Get current user endpoint
app.get('/api/me', auth, async (req, res) => {
  res.json({
    user: {
      id: req.user._id,
      username: req.user.username,
      email: req.user.email
    }
  });
});

// Translation endpoint
app.post('/api/translate', async (req, res) => {
    try {
        const { text } = req.body;
        let translatedText = text.toLowerCase();
        
        // Replace Gen Z slang with normal English
        for (const [slang, meaning] of Object.entries(genZDictionary)) {
            const regex = new RegExp(`\\b${slang}\\b`, 'gi');
            translatedText = translatedText.replace(regex, meaning);
        }

        res.json({ translation: translatedText });
    } catch (error) {
        console.error('Translation error:', error);
        res.status(500).json({ error: 'Translation failed' });
    }
});

// Detection endpoint
app.post('/api/detect', async (req, res) => {
    try {
        const { text } = req.body;
        const lowerText = text.toLowerCase();
        
        // Check if any Gen Z slang exists in the text
        const containsGenZ = Object.keys(genZDictionary).some(slang => 
            lowerText.includes(slang.toLowerCase())
        );

        res.json({ isGenZ: containsGenZ });
    } catch (error) {
        console.error('Detection error:', error);
        res.status(500).json({ error: 'Detection failed' });
    }
});

// Get all users endpoint
app.get('/api/users', auth, async (req, res) => {
  try {
    const users = await User.find({ _id: { $ne: req.user._id } })
      .select('username email');
    res.json(users);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch users' });
  }
});

// Get messages between two users
app.get('/api/messages/:userId', auth, async (req, res) => {
  try {
    const messages = await Message.find({
      $or: [
        { sender: req.user._id, receiver: req.params.userId },
        { sender: req.params.userId, receiver: req.user._id }
      ]
    })
    .sort({ createdAt: 1 })
    .populate('sender', 'username')
    .populate('receiver', 'username');

    res.json(messages);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch messages' });
  }
});

// Send a message
app.post('/api/messages', auth, async (req, res) => {
  try {
    const { receiverId, text } = req.body;
    
    // Check if receiver exists
    const receiver = await User.findById(receiverId);
    if (!receiver) {
      return res.status(404).json({ error: 'Receiver not found' });
    }

    // Create message
    const message = new Message({
      sender: req.user._id,
      receiver: receiverId,
      text: text
    });
    await message.save();

    // Check if message contains Gen Z slang and translate if needed
    const lowerText = text.toLowerCase();
    const containsGenZ = Object.keys(genZDictionary).some(slang => 
      lowerText.includes(slang.toLowerCase())
    );

    if (containsGenZ) {
      let translatedText = text.toLowerCase();
      for (const [slang, meaning] of Object.entries(genZDictionary)) {
        const regex = new RegExp(`\\b${slang}\\b`, 'gi');
        translatedText = translatedText.replace(regex, meaning);
      }

      // Create translation message
      const translationMessage = new Message({
        sender: req.user._id,
        receiver: receiverId,
        text: `Translation: ${translatedText}`,
        isTranslation: true
      });
      await translationMessage.save();
    }

    res.status(201).json(message);
  } catch (error) {
    res.status(500).json({ error: 'Failed to send message' });
  }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
}); 