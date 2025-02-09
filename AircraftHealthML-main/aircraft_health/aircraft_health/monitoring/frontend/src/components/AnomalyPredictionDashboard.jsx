import React, { useState, useEffect, useCallback } from 'react';
import { Card, Container, Row, Col, Tabs, Tab, Alert, Spinner } from 'react-bootstrap';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AnomalyDetectionService } from '../services/anomalyDetectionService'; // Ensure correct import

const AnomalyPredictionDashboard = () => {
  const [adaptResults, setAdaptResults] = useState(null);
  const [ngafidResults, setNgafidResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [threshold, setThreshold] = useState(95);
  const [dateRange, setDateRange] = useState({ start: null, end: null });

  const fetchResults = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/anomaly-detection/results/'); // Update endpoint path
      const contentType = response.headers.get('content-type');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      if (contentType && contentType.indexOf('application/json') !== -1) {
        const data = await response.json();
        if (data.adapt) {
          setAdaptResults(data.adapt);
        }
        if (data.ngafid) {
          setNgafidResults(data.ngafid);
        }
      } else {
        const text = await response.text();
        console.error('Expected JSON, got:', text);
        throw new Error('Invalid response format');
      }
    } catch (err) {
      setError('Failed to fetch prediction results');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleThresholdChange = async (newThreshold) => {
    try {
      await AnomalyDetectionService.updateThreshold(newThreshold);
      setThreshold(newThreshold);
      await fetchResults();
    } catch (err) {
      setError('Failed to update threshold');
    }
  };

  const handleDateRangeChange = async (range) => {
    try {
      setDateRange(range);
      const historicalData = await AnomalyDetectionService.fetchHistoricalData(range.start, range.end);
      setAdaptResults(prev => ({ ...prev, timeSeriesData: historicalData.adapt }));
      setNgafidResults(prev => ({ ...prev, maintenancePredictions: historicalData.ngafid }));
    } catch (err) {
      setError('Failed to fetch historical data');
    }
  };

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  const renderADAPTAnomalyChart = () => (
    <div style={{ height: '400px', width: '100%' }}>
      <ResponsiveContainer>
        <LineChart data={adaptResults?.timeSeriesData?.filter(item => item !== null && item !== undefined)}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="value" stroke="#8884d8" dot={false} />
          <Line type="monotone" dataKey="anomalyScore" stroke="#82ca9d" dot={(props) => {
            const isAnomaly = props.payload?.isAnomaly;
            return isAnomaly ? <circle cx={props.cx} cy={props.cy} r={4} fill="red" stroke="none" /> : null;
          }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );

  const renderNGAFIDPredictionChart = () => (
    <div style={{ height: '400px', width: '100%' }}>
      <ResponsiveContainer>
        <LineChart data={ngafidResults?.maintenancePredictions?.filter(item => item !== null && item !== undefined)}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="flightId" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="maintenanceProbability" stroke="#8884d8" dot={false} />
          <Line type="monotone" dataKey="anomalyScore" stroke="#82ca9d" dot={(props) => {
            const needsMaintenance = props.payload?.needsMaintenance;
            return needsMaintenance ? <circle cx={props.cx} cy={props.cy} r={4} fill="orange" stroke="none" /> : null;
          }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center min-vh-100">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger">
        {error}
      </Alert>
    );
  }

  return (
    <Container fluid className="py-4">
      <Card className="mb-4">
        <Card.Header>
          <h4 className="mb-0">Aircraft Health Monitoring Dashboard</h4>
        </Card.Header>
        <Card.Body>
          <Tabs defaultActiveKey="adapt" className="mb-4">
            <Tab eventKey="adapt" title="ADAPT Anomaly Detection">
              <Card>
                <Card.Header>
                  <h5 className="mb-0">ADAPT System Anomalies</h5>
                </Card.Header>
                <Card.Body>
                  {renderADAPTAnomalyChart()}
                  {adaptResults?.summary && (
                    <div className="mt-4 p-3 bg-light rounded">
                      <h6 className="mb-2">Analysis Summary</h6>
                      <p className="mb-1">Total Anomalies: {adaptResults.summary.totalAnomalies}</p>
                      <p className="mb-0">Detection Rate: {adaptResults.summary.detectionRate}%</p>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Tab>

            <Tab eventKey="ngafid" title="NGAFID Maintenance Prediction">
              <Card>
                <Card.Header>
                  <h5 className="mb-0">NGAFID Maintenance Predictions</h5>
                </Card.Header>
                <Card.Body>
                  {renderNGAFIDPredictionChart()}
                  {ngafidResults?.summary && (
                    <div className="mt-4 p-3 bg-light rounded">
                      <h6 className="mb-2">Prediction Summary</h6>
                      <p className="mb-1">Maintenance Required: {ngafidResults.summary.maintenanceRequired}</p>
                      <p className="mb-0">Prediction Accuracy: {ngafidResults.summary.accuracy}%</p>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Tab>

            <Tab eventKey="combined" title="Combined Analysis">
              <Row>
                <Col md={6}>
                  {renderADAPTAnomalyChart()}
                </Col>
                <Col md={6}>
                  {renderNGAFIDPredictionChart()}
                </Col>
              </Row>
              <div className="mt-4 p-3 bg-light rounded">
                <h6 className="mb-2">Overall System Health</h6>
                <p className="mb-0">
                  System Health Score: {
                    ((adaptResults?.summary?.healthScore || 0) + 
                     (ngafidResults?.summary?.healthScore || 0)) / 2
                  }%
                </p>
              </div>
            </Tab>
          </Tabs>
        </Card.Body>
      </Card>

      <Row>
        <Col md={4}>
          <Card className={`text-white ${
            adaptResults?.summary?.healthScore > 80 ? 'bg-success' :
            adaptResults?.summary?.healthScore > 60 ? 'bg-warning' : 'bg-danger'
          }`}>
            <Card.Body>
              <Card.Title>ADAPT Health</Card.Title>
              <h2 className="mb-0">{adaptResults?.summary?.healthScore}%</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card className={`text-white ${
            ngafidResults?.summary?.healthScore > 80 ? 'bg-success' :
            ngafidResults?.summary?.healthScore > 60 ? 'bg-warning' : 'bg-danger'
          }`}>
            <Card.Body>
              <Card.Title>NGAFID Health</Card.Title>
              <h2 className="mb-0">{ngafidResults?.summary?.healthScore}%</h2>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card className={`text-white ${
            ((adaptResults?.summary?.healthScore || 0) + 
             (ngafidResults?.summary?.healthScore || 0)) / 2 > 80 ? 'bg-success' :
            ((adaptResults?.summary?.healthScore || 0) + 
             (ngafidResults?.summary?.healthScore || 0)) / 2 > 60 ? 'bg-warning' : 'bg-danger'
          }`}>
            <Card.Body>
              <Card.Title>Overall Health</Card.Title>
              <h2 className="mb-0">
                {((adaptResults?.summary?.healthScore || 0) + 
                  (ngafidResults?.summary?.healthScore || 0)) / 2}%
              </h2>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default AnomalyPredictionDashboard;