from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent import ask_agent
from app.scenario import calculate_scenario


app = FastAPI()


class ScenarioRequest(BaseModel):
    product: str
    city: str
    horizon_days: int = Field(default=14, ge=1)
    demand_growth_pct: float = Field(default=20, ge=-100)
    shipment_delay_days: int = Field(default=3, ge=0)


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scenario")
def run_scenario(request: ScenarioRequest):
    try:
        return calculate_scenario(**request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/ask")
def ask(request: AskRequest):
    return {"answer": ask_agent(request.question)}