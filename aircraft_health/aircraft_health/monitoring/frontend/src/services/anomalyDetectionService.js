// services/anomalyDetectionService.js

const API_BASE_URL = '/api/anomaly-detection';

const AnomalyDetectionService = {
  async fetchResults() {
    const response = await fetch('/api/anomaly-results/');
    if (!response.ok) {
      throw new Error('Failed to fetch anomaly results');
    }
    return response.json();
  },
  async updateThreshold(newThreshold) {
    try {
      const response = await fetch(`${API_BASE_URL}/threshold/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(), // Django CSRF token
        },
        body: JSON.stringify({ threshold: newThreshold }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating threshold:', error);
      throw error;
    }
  },
  async fetchHistoricalData(startDate, endDate) {
    try {
      const params = new URLSearchParams({
        start: startDate.toISOString(),
        end: endDate.toISOString()
      });
      
      const response = await fetch(`${API_BASE_URL}/historical/?${params}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching historical data:', error);
      throw error;
    }
  },
  // Helper method to get Django CSRF token
  getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
};

export { AnomalyDetectionService };