from pydantic import BaseModel, Field


class Site(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    tilt: float = Field(ge=0, le=90, description="Tilt from horizontal [deg]")
    azimuth_conv: float = Field(
        ge=-180,
        le=180,
        description="Azimuth convention: 0=South, +E, -W (Forecast.Solar)",
    )
    kwp: float = Field(gt=0, description="Installed DC power in kWp")
    resolution: str = Field(default="60m")

    def to_pvlib_azimuth(self) -> float:
        # Convert 0=South (+E/-W) to pvlib azimuth degrees (0=N, 90=E, 180=S, 270=W)
        return 180.0 - self.azimuth_conv

