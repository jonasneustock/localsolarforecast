from pydantic import BaseModel


class ForecastSpec(BaseModel):
    endpoint: str
    lat: float
    lon: float
    tilt: float
    azimuth: float
    kwp: float
    resolution: str
    source: str

