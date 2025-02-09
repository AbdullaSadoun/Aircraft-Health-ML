import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Spinner, Alert, Nav, Button } from 'react-bootstrap';
import { ResponsiveLine } from '@nivo/line';
import Papa from 'papaparse';
import { LineChart } from 'lucide-react'; // Add icon library
import './ADAPTDashboard.css'; // Add CSS file

const ADAPTDashboard = () => {
    const [experiments, setExperiments] = useState([]);
    const [selectedExperiment, setSelectedExperiment] = useState(null);
    const [sensorData, setSensorData] = useState(null);
    const [experimentInfo, setExperimentInfo] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [visibleCharts, setVisibleCharts] = useState({
        voltage: true,
        current: true,
        temp: true,
        flow: true,
        relay: true,
        load: true,
        status: true,
    });

    // Helper function to parse experiment info from raw string
    const parseExperimentInfo = (rawInfo) => {
        try {
            // If rawInfo is already an object, just return formatted data
            if (rawInfo && typeof rawInfo === 'object' && !Array.isArray(rawInfo)) {
                return {
                    startTime: rawInfo.startTime || '',
                    endTime: rawInfo.endTime || '',
                    operationCode: rawInfo.operationCode || '',
                    operationMode: rawInfo.operationMode || '',
                    testArticle: rawInfo.testArticle || '',
                    comments: rawInfo.comments || '',
                    faultType: rawInfo.faultType || '',
                    faultMode: rawInfo.faultMode || '',
                    faultLocation: rawInfo.faultLocation || '',
                    faultInjection: rawInfo.faultInjection || ''
                };
            }
            
            return {
                startTime: '',
                endTime: '',
                operationCode: rawInfo?.operationCode || '',
                operationMode: '',
                testArticle: '',
                comments: '',
                faultType: rawInfo?.faultType || '',
                faultMode: rawInfo?.faultMode || '',
                faultLocation: rawInfo?.faultLocation || '',
                faultInjection: ''
            };
        } catch (error) {
            console.error('Error parsing experiment info:', error);
            return {
                startTime: '',
                endTime: '',
                operationCode: '',
                operationMode: '',
                testArticle: '',
                comments: '',
                faultType: '',
                faultMode: '',
                faultLocation: '',
                faultInjection: ''
            };
        }
    };

    // Load experiment list
    useEffect(() => {
        const loadExperiments = async () => {
            try {
                const response = await fetch('/api/experiments/');
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                console.log('Found experiments:', data.experiments);
                setExperiments(data.experiments);
            } catch (error) {
                console.error('Error loading experiment list:', error);
                setError('Failed to load experiment list');
            }
        };

        loadExperiments();
    }, []);

    // Load experiment data when selection changes
    useEffect(() => {
        const loadExperiment = async (filename) => {
            try {
                setLoading(true);
                setError(null);

                const response = await fetch(`/api/experiments/${filename}/`);
                const data = await response.json();
                
                console.log('Raw API response:', data);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                // Process experiment info
                if (data.experiment_info) {
                    const expInfo = parseExperimentInfo(data.experiment_info);
                    setExperimentInfo(expInfo);
                } else {
                    console.warn('No experiment_info found in data:', data);
                }

                // Process sensor data
                if (data.sensor_data && Array.isArray(data.sensor_data)) {
                    const sensorDataByType = processNewSensorData(data.sensor_data);
                    setSensorData(sensorDataByType);
                }

                setLoading(false);
            } catch (error) {
                console.error('Detailed error:', {
                    message: error.message,
                    stack: error.stack,
                    error: error
                });
                setError(`Error loading experiment data: ${error.message}`);
                setLoading(false);
            }
        };

        if (selectedExperiment) {
            loadExperiment(selectedExperiment);
        }
    }, [selectedExperiment]);

    // Add this new function to process sensor data
    const processNewSensorData = (sensorData) => {
        const sensorDataByType = {
            voltage: {},
            current: {},
            temp: {},
            flow: {},
            load: {},
            status: {},
            relay: {}
        };

        sensorData.forEach(row => {
            if (row.SensorData === 'AntagonistData') {
                const time = new Date(row.Time);
                Object.entries(row).forEach(([key, value]) => {
                    if (key !== 'Time' && key !== 'SensorData') {
                        // Determine sensor type and store data
                        if (key.startsWith('E') && !key.startsWith('ESH')) {
                            if (!sensorDataByType.voltage[key]) sensorDataByType.voltage[key] = [];
                            sensorDataByType.voltage[key].push({ x: time, y: parseFloat(value) });
                        } else if (key.startsWith('ISH')) {
                            if (!sensorDataByType.current[key]) sensorDataByType.current[key] = [];
                            sensorDataByType.current[key].push({ x: time, y: parseFloat(value) });
                        } else if (key.startsWith('ESH')) {
                            if (!sensorDataByType.relay[key]) sensorDataByType.relay[key] = [];
                            sensorDataByType.relay[key].push({ x: time, y: parseFloat(value) });
                        } else if (key.startsWith('IT') || key.startsWith('TE')) {
                            if (!sensorDataByType.temp[key]) sensorDataByType.temp[key] = [];
                            sensorDataByType.temp[key].push({ x: time, y: parseFloat(value) });
                        } else if (key.startsWith('FT')) {
                            if (!sensorDataByType.flow[key]) sensorDataByType.flow[key] = [];
                            sensorDataByType.flow[key].push({ x: time, y: parseFloat(value) });
                        } else if (key.startsWith('LT')) {
                            if (!sensorDataByType.load[key]) sensorDataByType.load[key] = [];
                            sensorDataByType.load[key].push({ x: time, y: parseFloat(value) });
                        } else if (key.startsWith('ST')) {
                            if (!sensorDataByType.status[key]) sensorDataByType.status[key] = [];
                            sensorDataByType.status[key].push({ x: time, y: parseFloat(value) });
                        }
                    }
                });
            }
        });

        return sensorDataByType;
    };

    const renderSensorChart = (data, title, yAxisLabel, height = '300px') => {
        if (!data || Object.keys(data).length === 0) {
            return <div className="text-white text-center">No data available</div>;
        }
    
        const chartData = Object.entries(data).map(([sensor, values]) => ({
            id: sensor,
            data: values
        }));
    
        return (
            <div style={{ height: height }} className="chart-container">
                <ResponsiveLine
                    data={chartData}
                    margin={{ top: 20, right: 120, bottom: 40, left: 50 }}
                    xScale={{
                        type: 'time',
                        format: 'time',
                        useUTC: false,
                        precision: 'second'
                    }}
                    yScale={{
                        type: 'linear',
                        stacked: false,
                        min: 'auto',
                        max: 'auto',
                    }}
                    axisLeft={{
                        legend: yAxisLabel,
                        legendOffset: -40,
                        legendPosition: 'middle',
                        textColor: '#ffffff'
                    }}
                    axisBottom={{
                        format: '%H:%M:%S',
                        legend: 'Time',
                        legendOffset: 35,
                        legendPosition: 'middle',
                        tickRotation: -45,
                        textColor: '#ffffff'
                    }}
                    enablePoints={false}
                    enableGridX={true}
                    enableGridY={true}
                    enableCrosshair={true}
                    useMesh={true}
                    animate={true} /* Enable animations */
                    motionConfig="gentle" /* Smooth animation transitions */
                    colors={{ scheme: 'category10' }}
                    theme={{
                        axis: {
                            domain: {
                                line: {
                                    stroke: '#ffffff',
                                    strokeWidth: 1
                                }
                            },
                            legend: {
                                text: {
                                    fill: '#ffffff',
                                    fontSize: 12
                                }
                            },
                            ticks: {
                                line: {
                                    stroke: '#ffffff',
                                    strokeWidth: 1
                                },
                                text: {
                                    fill: '#ffffff',
                                    fontSize: 11
                                }
                            }
                        },
                        grid: {
                            line: {
                                stroke: '#444444',
                                strokeWidth: 1
                            }
                        },
                        legends: {
                            text: {
                                fill: '#ffffff',
                                fontSize: 11
                            }
                        },
                        tooltip: {
                            container: {
                                background: '#333333',
                                color: '#ffffff',
                                fontSize: 12
                            }
                        }
                    }}
                    tooltip={({ point }) => (
                        <div
                            style={{
                                background: "white",
                                padding: "5px 10px",
                                borderRadius: "3px",
                                boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
                                color: "#000",
                            }}
                        >
                            <strong>{point.serieId}</strong>
                            <br />
                            Value: {point.data.yFormatted}
                            <br />
                            Time: {point.data.xFormatted}
                        </div>
                    )}
                    onClick={(point) => {
                        alert(`Sensor: ${point.serieId}\nValue: ${point.data.y}\nTime: ${point.data.xFormatted}`);
                    }}
                    legends={[
                        {
                            anchor: "bottom-right",
                            direction: "column",
                            translateX: 100,
                            itemWidth: 80,
                            itemHeight: 20,
                            symbolSize: 12,
                            symbolShape: "circle",
                            onClick: (legendItem) => {
                                const updatedVisibleCharts = { ...visibleCharts };
                                const key = legendItem.id.toLowerCase().replace(' ', '');
                                updatedVisibleCharts[key] = !updatedVisibleCharts[key];
                                setVisibleCharts(updatedVisibleCharts);
                            },
                            effects: [
                                {
                                    on: "hover",
                                    style: {
                                        itemBackground: "rgba(0, 0, 0, .03)",
                                        itemOpacity: 1
                                    }
                                }
                            ]
                        },
                    ]}
                    ariaLabel={`${title} Line Chart`} /* Improve accessibility */
                    ariaLive="polite"
                />
            </div>
        );
    };

    const toggleChartVisibility = (chartType) => {
        setVisibleCharts((prevState) => ({
            ...prevState,
            [chartType]: !prevState[chartType],
        }));
    };

    return (
        <div className="min-h-screen bg-dark text-white">
            {/* Header Section */}
            <div
                className="py-4 text-center"
                style={{
                    background: "linear-gradient(to right, #1e3a8a, #2563eb)", // Reverted to original gradient
                    color: "white",
                }}
            >
                <h1 className="display-6 font-weight-bold mb-1">
                    <LineChart size={40} className="mb-2" /> ADAPT Dataset Dashboard
                </h1>
                <p className="mb-0">Visualize and analyze critical sensor data in real-time</p>
            </div>

            <Container className="my-4">
                {/* Main Control Section */}
                <Card className="shadow-lg section-padding card-padding">
                    <Card.Body>
                        <Row className="card-container">
                            <Col md={6} className="card-column">
                                {/* Select Experiment */}
                                <Card className="shadow-sm mb-3 card-item nested-card">
                                    <Card.Body className="py-2 px-3">
                                        <Form.Group>
                                            <Form.Label className="mb-1">Select Experiment</Form.Label>
                                            <Form.Select 
                                                value={selectedExperiment || ''}
                                                onChange={(e) => setSelectedExperiment(e.target.value)}
                                                className="bg-dark text-white py-1"
                                            >
                                                <option value="">Choose an experiment...</option>
                                                {experiments.map(exp => (
                                                    <option key={exp} value={exp}>{exp}</option>
                                                ))}
                                            </Form.Select>
                                        </Form.Group>
                                    </Card.Body>
                                </Card>

                                {/* Buttons Card */}
                                <Card className="shadow-sm card-item nested-card">
                                    <Card.Body className="py-2 px-3">
                                        <h5 className="mb-2" style={{ fontWeight: "bold" }}>Sensor Categories</h5>
                                        <div className="button-container">
                                            {Object.keys(visibleCharts).map((chartType) => (
                                                <Button
                                                    key={chartType}
                                                    className={`dashboard-button ${visibleCharts[chartType] ? 'active' : ''}`}
                                                    onClick={() => toggleChartVisibility(chartType)}
                                                >
                                                    {chartType.charAt(0).toUpperCase() + chartType.slice(1)}
                                                </Button>
                                            ))}
                                        </div>
                                    </Card.Body>
                                </Card>
                            </Col>

                            {/* Experiment Info */}
                            <Col md={6} className="card-item">
                                <Card className="shadow-sm card-full-height nested-card">
                                    <Card.Body className="py-2 px-3">
                                        {experimentInfo ? (
                                            <Row>
                                                <Col md={6}>
                                                    <p className="mb-1">
                                                        <strong>Time Period:</strong> <br />
                                                        {experimentInfo.startTime} - {experimentInfo.endTime}
                                                    </p>
                                                    <p className="mb-1">
                                                        <strong>Operation Code:</strong> {experimentInfo.operationCode}
                                                    </p>
                                                </Col>
                                                <Col md={6}>
                                                    <p className="mb-1">
                                                        <strong>Fault Type:</strong> {experimentInfo.faultType} <br />
                                                        <strong>Fault Mode:</strong> {experimentInfo.faultMode}
                                                    </p>
                                                    <p className="mb-1">
                                                        <strong>Fault Location:</strong> {experimentInfo.faultLocation}
                                                    </p>
                                                    <p className="mb-1">
                                                        <strong>Fault Injection:</strong> {experimentInfo.faultInjection}
                                                    </p>
                                                    <p className="mb-1">
                                                        <strong>Test Article:</strong> {experimentInfo.testArticle}
                                                    </p>
                                                    <p className="mb-1">
                                                        <strong>Comments:</strong> {experimentInfo.comments}
                                                    </p>
                                                </Col>
                                            </Row>
                                        ) : (
                                            <p>No experiment selected. Experiment details will appear here.</p>
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

                {/* Sensor Data Visualization Section */}
                {sensorData && (
                    <Card className="shadow-lg section-padding card-padding">
                        <Card.Body>
                            <h4 className="text-center mb-4" style={{ fontWeight: "bold" }}>
                                Sensor Data Visualizations
                            </h4>
                            <Row>
                                {/* Voltage Sensors */}
                                {visibleCharts.voltage && (
                                    <Col md={6} className="mb-3">
                                        <Card className="shadow-sm h-100 nested-card">
                                            <Card.Header className="py-2">Voltage Sensors</Card.Header>
                                            <Card.Body className="p-2">
                                                {renderSensorChart(sensorData.voltage, 'Voltage Sensors', 'Voltage (V)', '200px')}
                                            </Card.Body>
                                        </Card>
                                    </Col>
                                )}
                                {/* Current Sensors */}
                                {visibleCharts.current && (
                                    <Col md={6} className="mb-3">
                                        <Card className="shadow-sm h-100 nested-card">
                                            <Card.Header className="py-2">Current Sensors</Card.Header>
                                            <Card.Body className="p-2">
                                                {renderSensorChart(sensorData.current, 'Current Sensors', 'Current (A)', '200px')}
                                            </Card.Body>
                                        </Card>
                                    </Col>
                                )}
                                {/* Temperature Sensors */}
                                {visibleCharts.temp && (
                                    <Col md={6} className="mb-3">
                                        <Card className="shadow-sm h-100 nested-card">
                                            <Card.Header className="py-2">Temperature Sensors</Card.Header>
                                            <Card.Body className="p-2">
                                                {renderSensorChart(sensorData.temp, 'Temperature Sensors', '°C', '200px')}
                                            </Card.Body>
                                        </Card>
                                    </Col>
                                )}
                                {/* Flow Rate Sensors */}
                                {visibleCharts.flow && (
                                    <Col md={6} className="mb-3">
                                        <Card className="shadow-sm h-100 nested-card">
                                            <Card.Header className="py-2">Flow Rate Sensors</Card.Header>
                                            <Card.Body className="p-2">
                                                {renderSensorChart(sensorData.flow, 'Flow Rate Sensors', 'Flow Rate', '200px')}
                                            </Card.Body>
                                        </Card>
                                    </Col>
                                )}
                                {/* Relay Status */}
                                {visibleCharts.relay && (
                                    <Col md={6} className="mb-3">
                                        <Card className="shadow-sm h-100 nested-card">
                                            <Card.Header className="py-2">Relay Status</Card.Header>
                                            <Card.Body className="p-2">
                                                {renderSensorChart(sensorData.relay, 'Relay Status', 'State', '200px')}
                                            </Card.Body>
                                        </Card>
                                    </Col>
                                )}
                                {/* Load Sensors */}
                                {visibleCharts.load && (
                                    <Col md={6} className="mb-3">
                                        <Card className="shadow-sm h-100 nested-card">
                                            <Card.Header className="py-2">Load Sensors</Card.Header>
                                            <Card.Body className="p-2">
                                                {renderSensorChart(sensorData.load, 'Load Sensors', 'Load', '200px')}
                                            </Card.Body>
                                        </Card>
                                    </Col>
                                )}
                                {/* Status Sensors */}
                                {visibleCharts.status && (
                                    <Col md={12} className="mb-3">
                                        <Card className="shadow-sm h-100 nested-card">
                                            <Card.Header className="py-2">Status Sensors</Card.Header>
                                            <Card.Body className="p-2">
                                                {renderSensorChart(sensorData.status, 'Status Sensors', 'Status', '200px')}
                                            </Card.Body>
                                        </Card>
                                    </Col>
                                )}
                            </Row>
                        </Card.Body>
                    </Card>
                )}
            </Container>
        </div>
    );
};

export default ADAPTDashboard;