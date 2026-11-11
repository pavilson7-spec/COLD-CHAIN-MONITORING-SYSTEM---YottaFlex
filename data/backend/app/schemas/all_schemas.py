from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, model_validator

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "Plant Operator"
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(min_length=10)

    @model_validator(mode="after")
    def validate_signup_role(self):
        if self.role != "Plant Operator":
            raise ValueError("Self-registration is limited to the Plant Operator role")
        return self

class AdminUserCreate(UserBase):
    password: str = Field(min_length=10)

    @model_validator(mode="after")
    def validate_admin_role(self):
        if self.role not in {"Plant Operator", "Maintenance Engineer", "Quality Engineer", "Production Planner", "OT/IT Administrator"}:
            raise ValueError("Unsupported user role")
        return self

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None

# Product Schemas
class ProductBase(BaseModel):
    product_name: str
    product_category: str
    temperature_min: float
    temperature_max: float
    humidity_min: float
    humidity_max: float
    permissible_excursion_duration: int = 30
    product_status: str = "Active"

    @model_validator(mode="after")
    def validate_product_ranges(self):
        if self.temperature_min > self.temperature_max:
            raise ValueError("temperature_min must not exceed temperature_max")
        if not 0 <= self.humidity_min <= self.humidity_max <= 100:
            raise ValueError("humidity bounds must be ordered and between 0 and 100")
        if self.permissible_excursion_duration < 0:
            raise ValueError("permissible excursion duration must not be negative")
        return self

class ProductCreate(ProductBase):
    product_id: str = Field(pattern=r"^[A-Z0-9][A-Z0-9-]{2,49}$")

class ProductResponse(ProductBase):
    product_id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Shipment Schemas
class ShipmentBase(BaseModel):
    product_id: str
    origin: str
    destination: str
    departure_time: datetime
    expected_delivery_time: datetime
    actual_delivery_time: Optional[datetime] = None
    shipment_status: str = "Created"
    issue_type: Optional[str] = None
    ground_truth_label: Optional[str] = None
    source_actual_delivery_time: Optional[datetime] = None

class ShipmentCreate(ShipmentBase):
    shipment_id: str = Field(pattern=r"^SHP-\d{4}-\d{6}$")

    @model_validator(mode="after")
    def validate_dates_and_status(self):
        if self.expected_delivery_time < self.departure_time:
            raise ValueError("Expected delivery cannot precede departure")
        if self.actual_delivery_time and self.actual_delivery_time < self.departure_time:
            raise ValueError("Actual delivery cannot precede departure")
        if self.shipment_status not in {"Created", "In_Transit", "Delivered", "Delayed", "Cancelled"}:
            raise ValueError("Invalid shipment status")
        if self.shipment_status == "Delivered" and self.actual_delivery_time is None:
            raise ValueError("Delivered shipments require actual_delivery_time")
        return self

class ShipmentStatusTransition(BaseModel):
    status: str
    actual_delivery_time: Optional[datetime] = None
    note: Optional[str] = Field(default=None, max_length=255)

class ShipmentResponse(ShipmentBase):
    shipment_id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Container Schemas
class ContainerBase(BaseModel):
    assigned_shipment_id: Optional[str] = None
    container_type: str
    capacity: float
    status: str = "Available"

class ContainerCreate(ContainerBase):
    container_id: str = Field(pattern=r"^CNT-\d{6}$")

class ContainerResponse(ContainerBase):
    container_id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Sensor Schemas
class SensorBase(BaseModel):
    sensor_type: str
    assigned_container_id: Optional[str] = None
    calibration_status: str = "Valid"
    calibration_date: datetime
    sensor_health: str = "Healthy"
    issue_type: Optional[str] = None
    ground_truth_label: Optional[str] = None
    source_calibration_status: Optional[str] = None

class SensorCreate(SensorBase):
    sensor_id: str = Field(pattern=r"^SNS-CNT-\d{6}-(TEMP|HUM)$")

class SensorResponse(SensorBase):
    sensor_id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class SensorCalibrationUpdate(BaseModel):
    calibration_status: str
    calibration_date: datetime
    note: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_calibration_status(self):
        if self.calibration_status not in {"Valid", "Expired", "Failed"}:
            raise ValueError("Calibration status must be Valid, Expired, or Failed")
        return self

# Sensor Reading Schemas
class SensorReadingBase(BaseModel):
    sensor_id: str
    shipment_id: Optional[str] = None
    timestamp: datetime
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    battery_level: Optional[float] = None
    is_anomaly: bool = False
    issue_type: Optional[str] = None
    ground_truth_label: Optional[str] = None
    source_reading_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_reading(self):
        if self.temperature is None and self.humidity is None:
            raise ValueError("A reading must include temperature or humidity")
        if self.battery_level is not None and not 0 <= self.battery_level <= 100:
            raise ValueError("Battery level must be between 0 and 100")
        return self

class SensorReadingCreate(SensorReadingBase):
    reading_id: str = Field(pattern=r"^RDG-SNS-CNT-\d{6}-(TEMP|HUM)-\d{14}$")

class SensorReadingResponse(SensorReadingBase):
    reading_id: str
    class Config:
        from_attributes = True

# Route Stop Schemas
class RouteStopBase(BaseModel):
    shipment_id: str
    stop_sequence: int
    location_name: str
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    planned_arrival: datetime
    actual_arrival: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    status: str = "Pending"
    issue_type: Optional[str] = None
    ground_truth_label: Optional[str] = None

    @model_validator(mode="after")
    def validate_stop_times(self):
        if self.departure_time and self.actual_arrival and self.departure_time < self.actual_arrival:
            raise ValueError("Stop departure cannot precede actual arrival")
        if self.status not in {"Pending", "Arrived", "Departed", "Delayed", "Skipped"}:
            raise ValueError("Invalid route stop status")
        return self

class RouteStopCreate(RouteStopBase):
    stop_id: str = Field(pattern=r"^STP-SHP-\d{4}-\d{6}-\d{2}$")

class RouteStopResponse(RouteStopBase):
    stop_id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Threshold Policy Schemas
class ThresholdPolicyBase(BaseModel):
    product_id: str
    policy_name: str
    temp_critical_low: float
    temp_warning_low: float
    temp_warning_high: float
    temp_critical_high: float
    humidity_min: float
    humidity_max: float
    max_excursion_duration_minutes: int = 30
    is_active: bool = True
    effective_start: datetime
    effective_end: Optional[datetime] = None
    policy_status: str = "Active"

    @model_validator(mode="after")
    def validate_policy(self):
        if not self.temp_critical_low <= self.temp_warning_low <= self.temp_warning_high <= self.temp_critical_high:
            raise ValueError("Temperature thresholds must be ordered from critical low to critical high")
        if not 0 <= self.humidity_min <= self.humidity_max <= 100:
            raise ValueError("Humidity bounds must be ordered and between 0 and 100")
        if self.effective_end and self.effective_end <= self.effective_start:
            raise ValueError("Policy effective_end must be after effective_start")
        return self

class ThresholdPolicyCreate(ThresholdPolicyBase):
    policy_id: str = Field(pattern=r"^POL-[A-Z0-9-]{3,50}$")

class ThresholdPolicyResponse(ThresholdPolicyBase):
    policy_id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Excursion Schemas
class ExcursionBase(BaseModel):
    shipment_id: str
    sensor_id: str
    policy_id: Optional[str] = None
    excursion_type: str
    severity: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: float = 0.0
    peak_value: Optional[float] = None
    threshold_limit: Optional[float] = None
    status: str = "OPEN"
    root_cause: Optional[str] = None
    container_id: Optional[str] = None
    review_status: str = "Pending"
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

class ExcursionCreate(ExcursionBase):
    excursion_id: str

class ExcursionResponse(ExcursionBase):
    excursion_id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Custody Event Schemas
class CustodyEventBase(BaseModel):
    shipment_id: str
    event_timestamp: datetime
    event_type: str
    from_party: str
    to_party: str
    location: str
    condition_status: str = "Normal"
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_custody_event(self):
        if self.event_type not in {"DEPARTURE", "HANDOVER", "INSPECTION", "ARRIVAL", "TAMPER_ALERT", "STATUS_CHANGE"}:
            raise ValueError("Invalid custody event type")
        return self

class CustodyEventCreate(CustodyEventBase):
    event_id: str

class CustodyEventResponse(CustodyEventBase):
    event_id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Corrective Action Schemas
class CorrectiveActionBase(BaseModel):
    excursion_id: str
    assigned_user: str
    action_description: str
    priority: str = "MEDIUM"
    status: str = "OPEN"
    resolution_notes: Optional[str] = None
    completed_date: Optional[datetime] = None

class CorrectiveActionCreate(CorrectiveActionBase):
    action_id: str

class CorrectiveActionResponse(CorrectiveActionBase):
    action_id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Alert Schemas
class AlertBase(BaseModel):
    shipment_id: str
    sensor_id: str
    excursion_id: Optional[str] = None
    severity: str
    description: str
    acknowledgement_status: str = "UNACKNOWLEDGED"
    resolution_status: str = "OPEN"

class AlertCreate(AlertBase):
    alert_id: str

class AlertResponse(AlertBase):
    alert_id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Dashboard Metrics Schema
class DashboardMetrics(BaseModel):
    total_shipments: int
    active_shipments: int
    delivered_shipments: int
    total_containers: int
    healthy_sensors: int
    failed_sensors: int
    active_excursions: int
    critical_alerts: int
    open_corrective_actions: int
    data_validation_success_rate: float

class ExcursionTransition(BaseModel):
    status: str
    note: Optional[str] = Field(default=None, max_length=500)

class ExcursionReview(BaseModel):
    review_status: str

    @model_validator(mode="after")
    def validate_review_status(self):
        if self.review_status not in {"Accepted", "Rejected", "Needs Investigation"}:
            raise ValueError("Review status must be Accepted, Rejected, or Needs Investigation")
        return self

class ExcursionStatusEventResponse(BaseModel):
    id: int
    excursion_id: str
    from_status: Optional[str]
    to_status: str
    changed_by: str
    note: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True

class LifecycleEventResponse(BaseModel):
    id: int
    from_status: Optional[str]
    to_status: str
    changed_by: str
    note: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True
