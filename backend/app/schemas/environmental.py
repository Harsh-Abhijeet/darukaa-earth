"""Pydantic schemas for environmental variables and profiles."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, model_validator


class LocationData(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    elevation_m: Optional[float] = Field(None, description="Elevation in meters above sea level")
    region_name: Optional[str] = Field(None, description="Geographic or administrative region")
    biome: Optional[str] = Field(None, description="Biome or agro-ecological zone")


class SoilData(BaseModel):
    ph: Optional[float] = Field(None, ge=2.5, le=11.0, description="Soil pH in H2O")
    organic_carbon: Optional[float] = Field(None, ge=0.0, le=25.0, description="Soil Organic Carbon (SOC) percentage by weight")
    moisture: Optional[float] = Field(None, ge=0.0, le=100.0, description="Volumetric soil water content percentage")
    bulk_density: Optional[float] = Field(None, ge=0.5, le=2.2, description="Bulk density in g/cm3")
    sand_fraction: Optional[float] = Field(None, ge=0.0, le=100.0, description="Sand fraction percentage")
    clay_fraction: Optional[float] = Field(None, ge=0.0, le=100.0, description="Clay fraction percentage")
    nitrogen_ppm: Optional[float] = Field(None, ge=0.0, description="Available mineral Nitrogen (N) ppm")
    phosphorus_ppm: Optional[float] = Field(None, ge=0.0, description="Olsen or Bray Phosphorus (P) ppm")


class ClimateData(BaseModel):
    rainfall: Optional[float] = Field(None, ge=0.0, le=10000.0, description="Mean annual precipitation in mm")
    temperature: Optional[float] = Field(None, ge=-50.0, le=60.0, description="Mean annual surface temperature in Celsius")
    drought_index: Optional[float] = Field(None, description="SPEI / SPI or Aridity Index (P/PET)")
    evapotranspiration: Optional[float] = Field(None, ge=0.0, description="Potential evapotranspiration (PET) in mm/yr")
    heatwave_days_per_year: Optional[int] = Field(None, ge=0, le=365, description="Number of extreme heat days > 38C")


class LandUseData(BaseModel):
    type: Optional[str] = Field("monoculture", description="Land-use pattern (monoculture, polyculture, agroforestry, fallow, pasture)")
    crop: Optional[str] = Field(None, description="Primary crop or vegetation species")
    canopy_cover: Optional[float] = Field(None, ge=0.0, le=100.0, description="Perennial woody canopy cover percentage")
    buffer_strip_width_m: Optional[float] = Field(None, ge=0.0, description="Field edge vegetative buffer strip width in meters")
    tillage_practice: Optional[str] = Field("conventional", description="Tillage practice: conventional, minimum, or no-till")


class BiodiversityData(BaseModel):
    species_richness: Optional[int] = Field(None, ge=0, description="Observed or surveyed species count per square kilometer")
    pollinator_abundance: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative pollinator activity index (0-100)")
    soil_microbial_biomass: Optional[float] = Field(None, ge=0.0, description="Microbial biomass carbon (mg C / kg soil)")
    habitat_diversity_index: Optional[float] = Field(None, ge=0.0, le=1.0, description="Shannon-Wiener diversity or structural landscape heterogeneity index (0-1)")


class HumanImpactData(BaseModel):
    chemical_fertilizer_kg_ha: Optional[float] = Field(None, ge=0.0, description="Synthetic N-P-K fertilizer application rate (kg/ha/yr)")
    pesticide_applications_per_year: Optional[int] = Field(None, ge=0, description="Frequency of synthetic insecticide/herbicide sprays")
    deforestation_proximity_km: Optional[float] = Field(None, ge=0.0, description="Distance to nearest remnant native woodland (km)")
    soil_erosion_rate_t_ha: Optional[float] = Field(None, ge=0.0, description="Estimated soil loss (tons/ha/yr)")


class StructuredEnvironmentalProfile(BaseModel):
    """Structured Environmental Input conforming to Requirement #12."""
    location: Optional[LocationData] = None
    soil: Optional[SoilData] = None
    climate: Optional[ClimateData] = None
    land_use: Optional[LandUseData] = None
    biodiversity: Optional[BiodiversityData] = None
    human_impact: Optional[HumanImpactData] = None

    def get_completeness_score(self) -> float:
        """Calculates completeness fraction across core environmental axes."""
        total_slots = 5
        filled = 0
        if self.soil and (self.soil.ph is not None or self.soil.organic_carbon is not None or self.soil.moisture is not None):
            filled += 1
        if self.climate and (self.climate.rainfall is not None or self.climate.temperature is not None):
            filled += 1
        if self.land_use and (self.land_use.type is not None or self.land_use.crop is not None):
            filled += 1
        if self.biodiversity and (self.biodiversity.species_richness is not None or self.biodiversity.habitat_diversity_index is not None):
            filled += 1
        if self.location and (self.location.latitude is not None and self.location.longitude is not None):
            filled += 1
        return round(filled / total_slots, 2)
