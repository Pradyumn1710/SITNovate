require('dotenv').config();

const express = require('express');
const session = require('express-session');
const passport = require('passport');
const mongoose = require('mongoose');

const app = express();


const passport = require('./passport-config');
const authRoutes = require('./routes/auth');

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(session({
  secret: process.env.SESSION_SECRET || 'your_session_secret',
  resave: false,
  saveUninitialized: false
}));
app.use(passport.initialize());
app.use(passport.session());

const MONGO_URL = process.env.MONGO_URL;
mongoose.connect(MONGO_URL, { useNewUrlParser: true, useUnifiedTopology: true })
  .then(() => console.log('Connected to MongoDB'))
  .catch(err => console.error('Could not connect to MongoDB', err));


app.use('/auth', authRoutes);

app.get('/', (req, res) => {
  res.send('AI Document Summarizer');
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
