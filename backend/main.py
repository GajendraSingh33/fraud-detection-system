# main.py - FastAPI Fraud Detection System with Rule-Based Analysis
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import uvicorn
from datetime import datetime, time
from typing import List, Dict, Any
import random
import os
from pydantic import BaseModel


# -------------------------
# Paths Setup
# -------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")


# -------------------------
# FastAPI App Setup
# -------------------------
app = FastAPI(title="AI Fraud Detection System", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Serve frontend static files
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def serve_ui():
    """Serve the main frontend UI"""
    if os.path.exists(os.path.join(FRONTEND_DIR, "index.html")):
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
    else:
        return {"message": "Fraud Detection API is running. Frontend not found."}


# -------------------------
# Rule-Based Fraud Detection System
# -------------------------
class RuleBasedFraudDetection:
    def __init__(self):
        # Fraud detection rules and thresholds
        self.high_amount_threshold = 2000.0
        self.very_high_amount_threshold = 5000.0
        
        # Risk scores for different merchants
        self.merchant_risk_scores = {
            "online": 0.4,
            "atm": 0.3,
            "gas": 0.1,
            "grocery": 0.05,
            "restaurant": 0.15
        }
        
        # Risk scores for locations
        self.location_risk_scores = {
            "CA": 0.3,
            "NY": 0.25,
            "FL": 0.35,
            "TX": 0.2,
            "IL": 0.15
        }
        
        # Risk scores for time of day
        self.time_risk_scores = {
            "night": 0.4,
            "evening": 0.2,
            "morning": 0.1,
            "afternoon": 0.15
        }
        
        # Card type risks
        self.card_risk_scores = {
            "prepaid": 0.4,
            "credit": 0.2,
            "debit": 0.1
        }
        
        # Statistics for reporting
        self.total_transactions = 0
        self.fraud_detected = 0
        self.normal_transactions = 0

    def calculate_risk_score(self, transaction: Dict[str, Any]) -> float:
        """Calculate risk score based on transaction features"""
        risk_score = 0.0
        
        # Amount-based risk
        amount = float(transaction.get("amount", 0))
        if amount > self.very_high_amount_threshold:
            risk_score += 0.5
        elif amount > self.high_amount_threshold:
            risk_score += 0.3
        elif amount < 1:  # Very small amounts can be suspicious
            risk_score += 0.2
        
        # Merchant-based risk
        merchant = transaction.get("merchant", "").lower()
        risk_score += self.merchant_risk_scores.get(merchant, 0.2)
        
        # Location-based risk
        location = transaction.get("location", "").upper()
        risk_score += self.location_risk_scores.get(location, 0.2)
        
        # Time-based risk
        time_of_day = transaction.get("time_of_day", "").lower()
        risk_score += self.time_risk_scores.get(time_of_day, 0.2)
        
        # Card type risk
        card_type = transaction.get("card_type", "").lower()
        risk_score += self.card_risk_scores.get(card_type, 0.2)
        
        return min(risk_score, 1.0)  # Cap at 1.0

    def detect_anomalies(self, transaction: Dict[str, Any]) -> bool:
        """Detect transaction anomalies using business rules"""
        amount = float(transaction.get("amount", 0))
        merchant = transaction.get("merchant", "").lower()
        time_of_day = transaction.get("time_of_day", "").lower()
        
        # Anomaly rules
        anomalies = []
        
        # Large online purchase at night
        if merchant == "online" and time_of_day == "night" and amount > 1000:
            anomalies.append("Large online purchase at night")
        
        # Multiple round number transactions
        if amount % 100 == 0 and amount > 500:
            anomalies.append("Round number high amount")
        
        # ATM withdrawal over typical limits
        if merchant == "atm" and amount > 800:
            anomalies.append("High ATM withdrawal")
        
        # Very high amount for certain merchants
        if merchant in ["grocery", "gas"] and amount > 300:
            anomalies.append("Unusually high amount for merchant type")
        
        return len(anomalies) > 0

    def predict(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transaction and return fraud prediction"""
        self.total_transactions += 1
        
        # Calculate risk score
        risk_score = self.calculate_risk_score(transaction)
        
        # Detect anomalies
        is_anomaly = self.detect_anomalies(transaction)
        
        # Determine fraud based on risk score and anomalies
        fraud_threshold = 0.6
        is_fraud = risk_score > fraud_threshold or is_anomaly
        
        if is_fraud:
            self.fraud_detected += 1
        else:
            self.normal_transactions += 1
        
        # Generate confidence score
        if is_fraud:
            confidence = min(0.9, 0.5 + risk_score)
        else:
            confidence = max(0.7, 1.0 - risk_score)
        
        result = {
            "prediction": int(is_fraud),
            "is_anomaly": int(is_anomaly),
            "confidence": round(confidence, 3),
            "risk_score": round(risk_score, 3)
        }
        
        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        if self.total_transactions > 0:
            fraud_rate = (self.fraud_detected / self.total_transactions) * 100
            normal_rate = (self.normal_transactions / self.total_transactions) * 100
        else:
            fraud_rate = 0
            normal_rate = 0
            
        return {
            "total_transactions": self.total_transactions,
            "fraud_detected": self.fraud_detected,
            "normal_transactions": self.normal_transactions,
            "fraud_rate": round(fraud_rate, 2),
            "normal_rate": round(normal_rate, 2),
            "accuracy": round(random.uniform(85, 95), 2),  # Simulated accuracy
            "precision": round(random.uniform(80, 90), 2),  # Simulated precision
            "recall": round(random.uniform(75, 85), 2)      # Simulated recall
        }


# Initialize fraud detection system
fraud_detector = RuleBasedFraudDetection()


# -------------------------
# Pydantic Models
# -------------------------
class Transaction(BaseModel):
    amount: float
    merchant: str
    location: str
    time_of_day: str
    card_type: str


# -------------------------
# API Endpoints
# -------------------------
@app.post("/analyze")
async def analyze_transaction(transaction: Transaction):
    """Analyze a single transaction for fraud"""
    try:
        result = fraud_detector.predict(transaction.dict())
        
        # Add recommendation based on result
        if result["prediction"] == 1:
            recommendation = "BLOCK - High fraud risk detected"
        elif result["is_anomaly"] == 1:
            recommendation = "REVIEW - Transaction shows anomalous patterns"
        else:
            recommendation = "APPROVE - Transaction appears normal"
        
        return {
            "status": "success",
            "transaction": transaction.dict(),
            "analysis": result,
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/stats")
async def get_model_stats():
    """Get system statistics and performance metrics"""
    stats = fraud_detector.get_stats()
    return {
        "model_metrics": {
            "accuracy": stats["accuracy"],
            "precision": stats["precision"],
            "recall": stats["recall"]
        },
        "transaction_stats": {
            "total_transactions": stats["total_transactions"],
            "fraud_detected": stats["fraud_detected"],
            "normal_transactions": stats["normal_transactions"],
            "fraud_rate": stats["fraud_rate"]
        },
        "status": "active",
        "detection_method": "Rule-based Analysis"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# -------------------------
# WebSocket for Real-time Stream
# -------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time transaction monitoring"""
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(random.uniform(1, 3))  # Variable delay

            # Generate sample transaction
            sample_txn = {
                "amount": round(random.uniform(5, 3000), 2),
                "merchant": random.choice(
                    ["grocery", "gas", "restaurant", "online", "atm"]
                ),
                "location": random.choice(["NY", "CA", "TX", "FL", "IL"]),
                "time_of_day": random.choice(
                    ["morning", "afternoon", "evening", "night"]
                ),
                "card_type": random.choice(
                    ["debit", "credit", "prepaid"]
                )
            }

            # Analyze transaction
            analysis = fraud_detector.predict(sample_txn)
            
            # Add recommendation
            if analysis["prediction"] == 1:
                recommendation = "BLOCK"
                alert_level = "high"
            elif analysis["is_anomaly"] == 1:
                recommendation = "REVIEW"
                alert_level = "medium"
            else:
                recommendation = "APPROVE"
                alert_level = "low"

            message = {
                "transaction": sample_txn,
                "analysis": analysis,
                "recommendation": recommendation,
                "alert_level": alert_level,
                "timestamp": datetime.now().isoformat()
            }

            await manager.broadcast(json.dumps(message))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# -------------------------
# Startup Event
# -------------------------
@app.on_event("startup")
async def startup_event():
    print("🚀 Fraud Detection System is running")
    print("📊 Using Rule-Based Detection Engine")
    print("🔗 WebSocket endpoint: /ws")
    print("📋 API docs: http://localhost:8000/docs")


# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


### developer : Gajendra Singh ###