// frontend/src/App.jsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import ADAPTDashboard from './components/ADAPTDashboard';
import LandingPage from './components/LandingPage'; // Corrected import statement
import Navigation from './components/Navigation';
import NGAFIDDashboard from './components/NGAFIDDashboard'; // Ensure correct import
import AnomalyPredictionDashboard from './components/AnomalyPredictionDashboard'; // Ensure correct import

function App() {
    return (
        <Router>
            <Navigation />
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/dashboard" element={<ADAPTDashboard />} />
                <Route path="/ngafid-dashboard" element={<NGAFIDDashboard />} /> {/* Ensure this route is above the wildcard */}
                <Route path="/anomaly-dashboard" element={<AnomalyPredictionDashboard />} />
                {/* Fallback route for any other paths */}
                <Route path="*" element={<LandingPage />} />
            </Routes>
        </Router>
    );
}

export default App;

