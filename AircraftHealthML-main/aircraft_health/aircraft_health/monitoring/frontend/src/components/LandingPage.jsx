// frontend/src/components/LandingPage.jsx

import React from 'react';
import { Container, Row, Col, Card, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { Activity, Database, LineChart, Settings } from 'lucide-react';

const LandingPage = () => {
    return (
        <div className="min-h-screen bg-dark text-white">
            {/* Hero Section */}
            <div
                className="bg-gradient-to-r from-blue-500 to-blue-700 text-white py-5"
                style={{
                    background: "linear-gradient(to right, #1e3a8a, #2563eb)",
                }}
            >
                <Container>
                    <Row className="align-items-center py-5">
                        <Col md={6}>
                            <h1 className="display-4 fw-bold">Aircraft Health Monitoring Tool</h1>
                            <p className="lead mb-4">
                                Advanced diagnostics and prognostics for aerospace systems using machine learning.
                            </p>
                            <Link to="/anomaly-dashboard">
                                <Button
                                    variant="outline-light"
                                    size="lg"
                                    style={{
                                        boxShadow: "0 4px 8px rgba(0, 0, 0, 0.3)",
                                        borderRadius: "8px",
                                    }}
                                >
                                    View Dashboard
                                </Button>
                            </Link>
                        </Col>
                        <Col md={6} className="text-center">
                            <LineChart size={300} className="text-light" />
                        </Col>
                    </Row>
                </Container>
            </div>

            {/* Features Section */}
            <Container className="py-5">
                <h2 className="text-center mb-5 text-white">Key Features</h2>
                <Row>
                    <Col md={4} className="mb-4">
                        <Card
                            className="h-100 shadow-lg border-0 bg-secondary"
                            style={{
                                transition: "transform 0.3s, box-shadow 0.3s",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = "scale(1.05)";
                                e.currentTarget.style.boxShadow =
                                    "0 6px 12px rgba(0, 0, 0, 0.3)";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = "scale(1)";
                                e.currentTarget.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.1)";
                            }}
                        >
                            <Card.Body className="text-center text-light">
                                <Activity size={40} className="text-primary mb-3" />
                                <Card.Title>Real-time Monitoring</Card.Title>
                                <Card.Text>
                                    Monitor critical aircraft systems in real-time with advanced sensor data analysis.
                                </Card.Text>
                            </Card.Body>
                        </Card>
                    </Col>
                    <Col md={4} className="mb-4">
                        <Card
                            className="h-100 shadow-lg border-0 bg-secondary"
                            style={{
                                transition: "transform 0.3s, box-shadow 0.3s",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = "scale(1.05)";
                                e.currentTarget.style.boxShadow =
                                    "0 6px 12px rgba(0, 0, 0, 0.3)";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = "scale(1)";
                                e.currentTarget.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.1)";
                            }}
                        >
                            <Card.Body className="text-center text-light">
                                <Database size={40} className="text-primary mb-3" />
                                <Card.Title>Predictive Maintenance</Card.Title>
                                <Card.Text>
                                    Predict potential failures before they occur using machine learning algorithms.
                                </Card.Text>
                            </Card.Body>
                        </Card>
                    </Col>
                    <Col md={4} className="mb-4">
                        <Card
                            className="h-100 shadow-lg border-0 bg-secondary"
                            style={{
                                transition: "transform 0.3s, box-shadow 0.3s",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = "scale(1.05)";
                                e.currentTarget.style.boxShadow =
                                    "0 6px 12px rgba(0, 0, 0, 0.3)";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = "scale(1)";
                                e.currentTarget.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.1)";
                            }}
                        >
                            <Card.Body className="text-center text-light">
                                <LineChart size={40} className="text-primary mb-3" />
                                <Card.Title>Component Analysis</Card.Title>
                                <Card.Text>
                                    Analyze component interactions and identify potential cascading failures.
                                </Card.Text>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </Container>

            {/* Dataset Section */}
            <Container className="py-5">
                <Row className="justify-content-center">
                    <Col md={10}>
                        <Card
                            className="h-100 shadow-lg border-0 bg-secondary"
                            style={{
                                transition: "transform 0.3s, box-shadow 0.3s",
                                background: "linear-gradient(to right, #1f2937, #4b5563)",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = "scale(1.05)";
                                e.currentTarget.style.boxShadow =
                                    "0 6px 12px rgba(0, 0, 0, 0.3)";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = "scale(1)";
                                e.currentTarget.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.1)";
                            }}
                        >
                            <Card.Body className="text-center text-light">
                                <Row className="align-items-center">
                                    <Col md={6}>
                                        <h2 className="text-white">ADAPT Dataset</h2>
                                        <p className="lead text-light">
                                            Using NASA's Advanced Diagnostics and Prognostics Testbed (ADAPT) for high-fidelity analysis.
                                        </p>
                                        <Link to="/dashboard">
                                            <Button
                                                variant="outline-light"
                                                style={{
                                                    borderRadius: "8px",
                                                    background: "#2563eb",
                                                    border: "none",
                                                    color: "#fff",
                                                }}
                                            >
                                                Explore Data
                                            </Button>
                                        </Link>
                                    </Col>
                                    <Col md={6} className="text-center">
                                        <Database size={200} className="text-light" />
                                    </Col>
                                </Row>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </Container>

            {/* NGAFID Dataset Section */}
            <Container className="py-5">
                <Row className="justify-content-center">
                    <Col md={10} className="mb-4">
                        <Card
                            className="h-100 shadow-lg border-0 bg-secondary"
                            style={{
                                transition: "transform 0.3s, box-shadow 0.3s",
                                background: "linear-gradient(to right, #1f2937, #4b5563)",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = "scale(1.05)";
                                e.currentTarget.style.boxShadow =
                                    "0 6px 12px rgba(0, 0, 0, 0.3)";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = "scale(1)";
                                e.currentTarget.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.1)";
                            }}
                        >
                            <Card.Body className="text-center text-light">
                                <Row className="align-items-center">
                                    <Col md={6}>
                                        <h2 className="text-white">NGAFID Maintenance Dataset</h2>
                                        <p className="lead text-light">
                                            Annotated flight data linked to unplanned maintenance events. Enables time-series modeling for failure prediction.
                                        </p>
                                        <Link to="/ngafid-dashboard">
                                            <Button
                                                variant="outline-light"
                                                style={{
                                                    borderRadius: "8px",
                                                    background: "#2563eb",
                                                    border: "none",
                                                    color: "#fff",
                                                }}
                                            >
                                                Explore NGAFID Data
                                            </Button>
                                        </Link>
                                    </Col>
                                    <Col md={6} className="text-center">
                                        <Activity size={200} className="text-light" />
                                    </Col>
                                </Row>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </Container>

            {/* Engine Run-to-Failure Dataset Section */}
            <Container className="py-5">
                <Row className="justify-content-center">
                    <Col md={10} className="mb-4">
                        <Card
                            className="shadow-lg border-0 bg-secondary"
                            style={{
                                transition: "transform 0.3s, box-shadow 0.3s",
                                background: "linear-gradient(to right, #1f2937, #374151)",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = "scale(1.05)";
                                e.currentTarget.style.boxShadow = "0 6px 12px rgba(0, 0, 0, 0.3)";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = "scale(1)";
                                e.currentTarget.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.1)";
                            }}
                        >
                            <Card.Body className="text-center text-light">
                                <Row className="align-items-center">
                                    <Col md={6}>
                                        <h2 className="text-white">Engine Run-to-Failure Dataset</h2>
                                        <p className="lead text-light">
                                            Real flight data documenting engine performance degradation over time, useful for prognostic modeling.
                                        </p>
                                        <Link to="/engine-dashboard">
                                            <Button
                                                variant="outline-light"
                                                style={{
                                                    borderRadius: "8px",
                                                    background: "#374151",
                                                    border: "none",
                                                    color: "#fff",
                                                }}
                                            >
                                                Explore Engine Data
                                            </Button>
                                        </Link>
                                    </Col>
                                    <Col md={6} className="text-center">
                                        <Settings size={200} className="text-light" />
                                    </Col>
                                </Row>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </div>
    );
};

export default LandingPage;
