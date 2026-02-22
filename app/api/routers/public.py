from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.db.models import Event, EventField, Registration
from app.api.endpoints.common import RegistrationCreate

router = APIRouter()

@router.get("/events/{event_id}")
def get_public_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    fields = db.query(EventField).filter(EventField.event_id == event_id).order_by(EventField.order_index).all()
    
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
        "fields": fields
    }

@router.post("/events/{event_id}/register")
def register_event(event_id: int, reg: RegistrationCreate, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event.max_seats:
        count = db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.verified == True,
            Registration.payment_status == "paid"
        ).count()
        if count >= event.max_seats:
            raise HTTPException(status_code=400, detail="Registration closed: Maximum capacity reached")

    # Auto-verify if event is free
    verified_status = False
    pay_status = "pending"
    if not event.is_paid:
        verified_status = True
        pay_status = "paid"

    new_reg = Registration(
        event_id=event_id, 
        answers=reg.answers,
        verified=verified_status,
        payment_status=pay_status
    )
    db.add(new_reg)
    db.commit()
    db.refresh(new_reg)
    return new_reg

@router.post("/responses")
def create_response(reg: RegistrationCreate, db: Session = Depends(get_db)):
    if not reg.eventId:
        raise HTTPException(status_code=400, detail="Event ID is required")
        
    event_id = reg.eventId
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event.max_seats:
        count = db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.verified == True,
            Registration.payment_status == "paid"
        ).count()
        if count >= event.max_seats:
            raise HTTPException(status_code=400, detail="Registration closed: Maximum capacity reached")

    # Auto-verify if event is free
    verified_status = False
    pay_status = "pending"
    if not event.is_paid:
        verified_status = True
        pay_status = "paid"

    new_reg = Registration(
        event_id=event_id, 
        answers=reg.answers,
        verified=verified_status,
        payment_status=pay_status
    )
    db.add(new_reg)
    db.commit()
    db.refresh(new_reg)
    return new_reg
