import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Spinner, Alert, Button } from 'react-bootstrap';
import Plot from 'react-plotly.js';
import { LineChart } from 'lucide-react'; // Add icon library
import './NGAFIDDashboard.css'; // Add CSS file

const NGAFIDDashboard = () => {
    const [experiments, setExperiments] = useState([]);
    const [selectedExperiment, setSelectedExperiment] = useState(null);
    const [maintenanceData, setMaintenanceData] = useState(null);
    const [experimentInfo, setExperimentInfo] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeCategory, setActiveCategory] = useState('before');
    const [labels, setLabels] = useState([]);
    const [selectedLabel, setSelectedLabel] = useState('');
    const [visualizationData, setVisualizationData] = useState(null);
    const [insights, setInsights] = useState(null);

    // Fetch unique labels
    useEffect(() => {
        console.log("Fetching unique labels");
        fetch("/api/ngafid/unique_labels/")
            .then((response) => response.json())
            .then((data) => {
                console.log("Unique labels fetched:", data);
                setLabels(data);
            })
            .catch((error) => console.error("Error fetching labels:", error));
    }, []);

    // Fetch flights by selected label and their visualizations
    const fetchFlightData = async (label) => {
        console.log(`Fetching flights for label: ${label}`);
        try {
            const response = await fetch(`/api/ngafid/grouped_flight_data/?label=${encodeURIComponent(label)}`);
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`Error fetching label data: ${response.status} - ${errorText}`);
                throw new Error(`Error fetching label data: ${response.status}`);
            }
            const data = await response.json();
            console.log("Flights fetched for label:", data);
            setVisualizationData(data);
        } catch (error) {
            console.error("Error fetching label data:", error);
            setError(`Error fetching label data: ${error.message}`);
        }
    };

    // Fetch insights for selected label
    const fetchInsights = async (label) => {
        console.log(`Fetching insights for label: ${label}`);
        try {
            const response = await fetch(`/api/ngafid/flight_insights/?label=${encodeURIComponent(label)}`);
            const responseText = await response.text();
            if (!response.ok) {
                console.error(`Error fetching insights: ${response.status} - ${responseText}`);
                throw new Error(`Error fetching insights: ${response.status}`);
            }
            try {
                const data = JSON.parse(responseText);
                console.log("Insights fetched for label:", data);
                setInsights(data);
            } catch (jsonError) {
                console.error("Error parsing JSON:", jsonError);
                throw new Error("Error parsing JSON response");
            }
        } catch (error) {
            console.error("Error fetching insights:", error);
            setError(`Error fetching insights: ${error.message}`);
        }
    };

    useEffect(() => {
        if (selectedLabel) {
            console.log(`Selected label changed: ${selectedLabel}`);
            fetchFlightData(selectedLabel);
            fetchInsights(selectedLabel);
        }
    }, [selectedLabel]);

    // Render scatter plot
    const renderScatterPlot = () => {
        if (!visualizationData || !visualizationData.scatter_data) {
            return <p>No scatter data available.</p>;
        }

        return (
            <Plot
                data={[
                    {
                        x: visualizationData.scatter_data.map(item => item.x),
                        y: visualizationData.scatter_data.map(item => item.y),
                        mode: 'markers',
                        type: 'scatter',
                        marker: { color: 'blue' },
                    },
                ]}
                layout={{
                    title: 'Flight Length vs Master Index',
                    xaxis: { title: 'Master Index' },
                    yaxis: { title: 'Flight Length (minutes)' },
                }}
                config={{ responsive: true }}
            />
        );
    };

    // Render histogram
    const renderHistogram = () => {
        if (!visualizationData || !visualizationData.histogram_data) {
            return <p>No histogram data available.</p>;
        }

        return (
            <Plot
                data={[
                    {
                        x: visualizationData.histogram_data,
                        type: 'histogram',
                        marker: { color: '#3b82f6' },
                    },
                ]}
                layout={{
                    title: 'Flight Length Distribution',
                    xaxis: { title: 'Flight Length (minutes)' },
                    yaxis: { title: 'Frequency' },
                }}
                config={{ responsive: true }}
            />
        );
    };

    return (
        <div className="min-h-screen bg-dark text-white">
            {/* Header Section */}
            <div
                className="py-4 text-center"
                style={{
                    background: "linear-gradient(to right, #1e3a8a, #2563eb)",
                    color: "white",
                }}
            >
                <h1 className="display-6 font-weight-bold mb-1">
                    <LineChart size={40} className="mb-2" /> NGAFID Maintenance Dataset Dashboard
                </h1>
                <p className="mb-0">Analyze and visualize NGAFID maintenance trends and flight data.</p>
            </div>

            <Container className="my-4">
                {/* Main Control Section */}
                <Card className="shadow-lg section-padding card-padding">
                    <Card.Body>
                        <Row className="card-container">
                            <Col md={6} className="card-column">
                                {/* Select Flight or Maintenance Event */}
                                <Card className="shadow-sm mb-3 card-item nested-card">
                                    <Card.Body className="py-2 px-3">
                                        <Form.Group>
                                            <Form.Label className="mb-1">Select Flight or Maintenance Event</Form.Label>
                                            <Form.Select 
                                                value={selectedLabel || ''}
                                                onChange={(e) => setSelectedLabel(e.target.value)}
                                                className="bg-dark text-white py-1"
                                            >
                                                <option value="">Choose a label...</option>
                                                {labels.map((label, index) => (
                                                    <option key={index} value={label.label}>
                                                        {label.label} ({label.count})
                                                    </option>
                                                ))}
                                            </Form.Select>
                                        </Form.Group>
                                    </Card.Body>
                                </Card>

                                {/* Maintenance Categories Buttons */}
                                <Card className="shadow-sm card-item nested-card">
                                    <Card.Body className="py-2 px-3">
                                        <h5 className="mb-2" style={{ fontWeight: "bold" }}>Maintenance Categories</h5>
                                        <div className="button-container">
                                            {["before", "after", "same"].map((category) => (
                                                <Button
                                                    key={category}
                                                    className={`dashboard-button ${activeCategory === category ? 'active' : ''}`}
                                                    onClick={() => handleCategoryChange(category)}
                                                >
                                                    {category.toUpperCase()}
                                                </Button>
                                            ))}
                                        </div>
                                    </Card.Body>
                                </Card>
                            </Col>

                            {/* Maintenance Details */}
                            <Col md={6} className="card-item">
                                <Card className="shadow-sm card-full-height nested-card">
                                    <Card.Body className="py-2 px-3">
                                        {experimentInfo ? (
                                            <Row>
                                                <Col md={6}>
                                                    <p className="mb-1">
                                                        <strong>Date Difference:</strong> <br />
                                                        {experimentInfo.date_diff}
                                                    </p>
                                                    <p className="mb-1">
                                                        <strong>Flight Length:</strong> {experimentInfo.flight_length} hrs
                                                    </p>
                                                </Col>
                                                <Col md={6}>
                                                    <p className="mb-1">
                                                        <strong>Issue:</strong> {experimentInfo.label}
                                                    </p>
                                                    <p className="mb-1">
                                                        <strong>Number of Flights Before:</strong> {experimentInfo.number_flights_before}
                                                    </p>
                                                </Col>
                                            </Row>
                                        ) : (
                                            <p>No event selected. Details will appear here.</p>
                                        )}
                                    </Card.Body>
                                </Card>
                            </Col>
                        </Row>
                    </Card.Body>
                </Card>

                {/* Loading Spinner */}
                {loading && (
                    <Row className="mb-3">
                        <Col className="text-center">
                            <Spinner animation="border" variant="light" />
                        </Col>
                    </Row>
                )}

                {/* Error Alert */}
                {error && (
                    <Row className="mb-3">
                        <Col>
                            <Alert variant="danger">{error}</Alert>
                        </Col>
                    </Row>
                )}

                {/* Maintenance Data Visualization Section */}
                {visualizationData && (
                    <Card className="shadow-lg section-padding card-padding">
                        <Card.Body>
                            <h4 className="text-center mb-4" style={{ fontWeight: "bold" }}>
                                Maintenance Data Visualizations
                            </h4>
                            <Row>
                                {/* Scatter Plot */}
                                <Col md={12} className="mb-3">
                                    <Card className="shadow-sm h-100 nested-card">
                                        <Card.Header className="py-2">Flight Length vs Master Index</Card.Header>
                                        <Card.Body className="p-2">
                                            {renderScatterPlot()}
                                        </Card.Body>
                                    </Card>
                                </Col>
                                {/* Histogram */}
                                <Col md={12} className="mb-3">
                                    <Card className="shadow-sm h-100 nested-card">
                                        <Card.Header className="py-2">Flight Length Distribution</Card.Header>
                                        <Card.Body className="p-2">
                                            {renderHistogram()}
                                        </Card.Body>
                                    </Card>
                                </Col>
                            </Row>
                        </Card.Body>
                    </Card>
                )}

                {insights && (
                    <div>
                        <h3>Flight Insights</h3>
                        <p>Average Flight Length: {insights.average} minutes</p>
                        <p>Max Flight Length: {insights.max} minutes</p>
                        <p>Min Flight Length: {insights.min} minutes</p>
                    </div>
                )}
            </Container>
        </div>
    );
};

export default NGAFIDDashboard; // Ensure correct export
