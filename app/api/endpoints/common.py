from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class EventFieldSchema(BaseModel):
    id: Optional[int] = None
    event_id: Optional[int] = None  # Backend sends this
    eventId: Optional[str] = None  # Frontend sends this
    order_index: int = Field(..., alias='order')  # Accept 'order' from frontend
    label: str
    type: str
    required: bool
    description: Optional[str] = None  # Help text for the question
    min_value: Optional[int] = Field(None, alias='minValue')  # For LINEAR_SCALE, character limits
    max_value: Optional[int] = Field(None, alias='maxValue')  # For LINEAR_SCALE, character limits
    file_types: Optional[List[str]] = Field(None, alias='fileTypes')  # For FILE_UPLOAD (e.g., ['pdf', 'jpg'])
    max_file_size: Optional[int] = Field(None, alias='maxFileSize')  # For FILE_UPLOAD (bytes)
    options: Optional[List[str]] = None  # For dropdown/checkbox/multiple choice
    image_url: Optional[str] = Field(None, alias='imageUrl')  # Organizer image/QR code for question
    logic: Optional[Dict[str, Any]] = None  # Condition: { option: "section_id" }
    
    class Config:
        populate_by_name = True  # Allow both 'order' and 'order_index'

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    startDateTime: Optional[str] = None
    endDateTime: Optional[str] = None
    maxSeats: Optional[int] = None
    status: Optional[str] = None
    limitOneResponse: Optional[bool] = False
    isPaid: Optional[bool] = False
    whatsappLink: Optional[str] = None
    fields: Optional[List[EventFieldSchema]] = []

class RegistrationCreate(BaseModel):
    answers: Dict[str, Any]
    eventId: Optional[int] = None

class PostCreate(BaseModel):
    title: str
    content: str

# --- Response Models ---

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    user: UserResponse
    token: str

class EventFieldResponse(BaseModel):
    id: int
    order_index: int
    label: str
    type: str
    required: bool
    description: Optional[str] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    file_types: Optional[List[str]] = None
    max_file_size: Optional[int] = None
    options: Optional[List[str]] = None
    image_url: Optional[str] = None
    logic: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class EventResponse(BaseModel):
    id: int
    organizer_id: int
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_date_time: Optional[datetime] = None
    end_date_time: Optional[datetime] = None
    max_seats: Optional[int] = None
    status: str
    limit_one_response: bool
    whatsapp_link: Optional[str] = None
    is_paid: Optional[bool] = False
    registration_count: Optional[int] = 0
    created_at: datetime
    fields: List[EventFieldResponse] = []

    class Config:
        from_attributes = True

class RegistrationResponse(BaseModel):
    id: int
    event_id: int
    submitted_at: datetime
    answers: Optional[Dict[str, Any]] = None
    verified: bool
    payment_status: str

    class Config:
        from_attributes = True

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    filename: str
    original_filename: str
    url: str
    size: int

class MessageResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    status: Optional[str] = None
