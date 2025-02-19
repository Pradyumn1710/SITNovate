const express = require('express');
const passport = require('passport');
const User = require('../models/User');

const router = express.Router();

router.post('/register', async (req, res) => {
  try {
    const { username, password } = req.body;
    const user = new User({ username, password });
    await user.save();
    res.status(201).json({ message: 'User registered successfully' });
  } catch (error) {
    res.status(400).json({ message: 'Error registering user', error: error.message });
  }
});

router.post('/login', passport.authenticate('local'), (req, res) => {
  res.json({ message: 'Logged in successfully', user: req.user });
});

router.get('/logout', (req, res) => {
  req.logout();
  res.json({ message: 'Logged out successfully' });
});


router.get('/google',
    passport.authenticate('google', { scope: ['profile', 'email'] })
  );
  
  router.get('/google/callback',
    passport.authenticate('google', { failureRedirect: '/login' }),
    (req, res) => {
      res.redirect('/dashboard');
    }
  );

module.exports = router;
