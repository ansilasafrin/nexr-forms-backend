from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.api.deps import get_db, get_current_user
from app.db.models import User, Event, EventField, Registration
from app.api.endpoints.common import EventCreate, EventResponse, RegistrationResponse, MessageResponse
 
router = APIRouter()

@router.get("/", response_model=List[EventResponse], tags=["events"], summary="List all events", description="Retrieve a list of all events created by the current user.")
def get_events(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    events = db.query(Event).filter(Event.organizer_id == current_user.id).order_by(Event.created_at.desc()).all()
    res = []
    for e in events:
        count = db.query(Registration).filter(Registration.event_id == e.id, Registration.verified == True).count()
        e_dict = {c.name: getattr(e, c.name) for c in e.__table__.columns}
        e_dict['fields'] = e.fields
        e_dict['registration_count'] = count
        res.append(e_dict)
    return res

@router.get("/{event_id}", response_model=EventResponse, tags=["events"], summary="Get event details", description="Get detailed information about a specific event, including its fields.")
def get_event(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    fields = db.query(EventField).filter(EventField.event_id == event_id).order_by(EventField.order_index).all()
    
    count = db.query(Registration).filter(Registration.event_id == event.id, Registration.verified == True).count()

    return {
        "id": event.id,
        "organizer_id": event.organizer_id,
        "title": event.title,
        "description": event.description,
        "location": event.location,
        "start_date_time": event.start_date_time,
        "end_date_time": event.end_date_time,
        "max_seats": event.max_seats,
        "status": event.status,
        "limit_one_response": event.limit_one_response,
        "whatsapp_link": event.whatsapp_link,
        "is_paid": event.is_paid,
        "registration_count": count,
        "created_at": event.created_at,
        "fields": fields
    }

@router.post("/", response_model=EventResponse, tags=["events"], summary="Create an event", description="Create a new event with custom registration fields.")
def create_event(event: EventCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    print(f"DEBUG: create_event called with {event}")
    new_event = Event(
        organizer_id=current_user.id,
        title=event.title,
        description=event.description,
        location=event.location,
        start_date_time=datetime.fromisoformat(event.startDateTime.replace('Z', '+00:00')) if event.startDateTime else None,
        end_date_time=datetime.fromisoformat(event.endDateTime.replace('Z', '+00:00')) if event.endDateTime else None,
        max_seats=event.maxSeats,
        status=event.status or "draft",
        limit_one_response=event.limitOneResponse,
        whatsapp_link=event.whatsappLink,
        is_paid=event.isPaid
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    if event.fields:
        for f in event.fields:
            new_field = EventField(
                event_id=new_event.id,
                order_index=f.order_index,
                label=f.label,
                type=f.type,
                required=f.required,
                description=f.description,
                min_value=f.min_value,
                max_value=f.max_value,
                file_types=f.file_types,
                max_file_size=f.max_file_size,
                options=f.options,
                image_url=f.image_url,
                logic=f.logic
            )
            db.add(new_field)
        db.commit()
    
    # Fetch fields to include in response
    fields = db.query(EventField).filter(EventField.event_id == new_event.id).order_by(EventField.order_index).all()
    
    return {
        "id": new_event.id,
        "organizer_id": new_event.organizer_id,
        "title": new_event.title,
        "description": new_event.description,
        "location": new_event.location,
        "start_date_time": new_event.start_date_time,
        "end_date_time": new_event.end_date_time,
        "max_seats": new_event.max_seats,
        "status": new_event.status,
        "limit_one_response": new_event.limit_one_response,
        "whatsapp_link": new_event.whatsapp_link,
        "is_paid": new_event.is_paid,
        "created_at": new_event.created_at,
        "fields": fields
    }

@router.put("/{event_id}", response_model=EventResponse, tags=["events"], summary="Update an event", description="Modify an existing event's details and registration fields.")
def update_event(event_id: int, event: EventCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    print(f"DEBUG: update_event called for event_id={event_id} with payload: {event}")
    db_event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db_event.title = event.title
    db_event.description = event.description
    db_event.location = event.location
    if event.startDateTime:
        db_event.start_date_time = datetime.fromisoformat(event.startDateTime.replace('Z', '+00:00'))
    if event.endDateTime:
        db_event.end_date_time = datetime.fromisoformat(event.endDateTime.replace('Z', '+00:00'))
    db_event.max_seats = event.maxSeats
    db_event.status = event.status
    db_event.limit_one_response = event.limitOneResponse
    db_event.whatsapp_link = event.whatsappLink
    db_event.is_paid = event.isPaid
    
    if event.fields is not None:
        # Get existing fields mapped by ID
        existing_fields = {f.id: f for f in db.query(EventField).filter(EventField.event_id == event_id).all()}
        
        # Track which IDs have been processed (updated)
        processed_ids = set()

        for f in event.fields:
            # If field has an ID and exists in DB, update it
            if f.id is not None and f.id in existing_fields:
                db_field = existing_fields[f.id]
                db_field.order_index = f.order_index
                db_field.label = f.label
                db_field.type = f.type
                db_field.required = f.required
                db_field.description = f.description
                db_field.min_value = f.min_value
                db_field.max_value = f.max_value
                db_field.file_types = f.file_types
                db_field.max_file_size = f.max_file_size
                db_field.options = f.options
                db_field.image_url = f.image_url
                db_field.logic = f.logic
                processed_ids.add(f.id)
            else:
                # New field
                new_field = EventField(
                    event_id=event_id,
                    order_index=f.order_index,
                    label=f.label,
                    type=f.type,
                    required=f.required,
                    description=f.description,
                    min_value=f.min_value,
                    max_value=f.max_value,
                    file_types=f.file_types,
                    max_file_size=f.max_file_size,
                    options=f.options,
                    image_url=f.image_url,
                    logic=f.logic
                )
                db.add(new_field)
            
        # Delete any fields that were not in the update payload
        for fid, db_field in existing_fields.items():
            if fid not in processed_ids:
                db.delete(db_field)
            
    db.commit()
    db.refresh(db_event)
    
    # Fetch fields to include in response
    fields = db.query(EventField).filter(EventField.event_id == event_id).order_by(EventField.order_index).all()
    
    return {
        "id": db_event.id,
        "organizer_id": db_event.organizer_id,
        "title": db_event.title,
        "description": db_event.description,
        "location": db_event.location,
        "start_date_time": db_event.start_date_time,
        "end_date_time": db_event.end_date_time,
        "max_seats": db_event.max_seats,
        "status": db_event.status,
        "limit_one_response": db_event.limit_one_response,
        "whatsapp_link": db_event.whatsapp_link,
        "is_paid": db_event.is_paid,
        "created_at": db_event.created_at,
        "fields": fields
    }

@router.delete("/{event_id}", response_model=MessageResponse, tags=["events"], summary="Delete an event", description="Permanently delete an event and all its associated registrations.")
def delete_event(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete associated registrations first to prevent FK violation
    db.query(Registration).filter(Registration.event_id == event_id).delete()
    
    db.delete(db_event)
    db.commit()
    return {"success": True}

@router.get("/{event_id}/registrations", response_model=List[RegistrationResponse], tags=["events"], summary="List event registrations", description="Retrieve all registration responses for a specific event.")
def get_registrations(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    regs = db.query(Registration).filter(Registration.event_id == event_id).order_by(Registration.submitted_at.desc()).all()
    return regs

import csv
import io
from fastapi.responses import StreamingResponse

@router.get("/{event_id}/export", tags=["events"], summary="Export registrations to CSV", description="Download a CSV file containing all registration responses for the event.")
def export_event_registrations(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Get fields for headers ignoring SECTION fields which have no answers usually
    fields = db.query(EventField).filter(EventField.event_id == event_id, EventField.type != 'SECTION').order_by(EventField.order_index).all()
    headers = ["Submission Date"] + [f.label for f in fields]
    
    # Get registrations
    registrations = db.query(Registration).filter(Registration.event_id == event_id).order_by(Registration.submitted_at.desc()).all()
    
    # Generate CSV in memory (simple for MPV)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    
    for reg in registrations:
        row = [reg.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if reg.submitted_at else ""]
        answers = reg.answers or {}
        for f in fields:
            val = answers.get(str(f.id), "")
            if isinstance(val, list):
                val = ", ".join(map(str, val))
            row.append(val)
        writer.writerow(row)
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=event_{event_id}_responses.csv"}
    )

@router.put("/{event_id}/registrations/{reg_id}/approve", response_model=MessageResponse, tags=["events"], summary="Approve a registration", description="Mark a registration as verified and paid.")
def approve_registration(event_id: int, reg_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    reg = db.query(Registration).filter(Registration.id == reg_id, Registration.event_id == event_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
        
    reg.verified = True
    reg.payment_status = "paid"
    db.commit()
    return {"success": True, "status": "paid"}

@router.put("/{event_id}/registrations/{reg_id}/reject", response_model=MessageResponse, tags=["events"], summary="Reject a registration", description="Mark a registration as failed/unverified.")
def reject_registration(event_id: int, reg_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    reg = db.query(Registration).filter(Registration.id == reg_id, Registration.event_id == event_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
        
    reg.verified = False
    reg.payment_status = "failed"
    db.commit()
    return {"success": True, "status": "failed"}
