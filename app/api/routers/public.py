from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.api.deps import get_db
from app.db.models import Event, EventField, Registration
from app.api.endpoints.common import RegistrationCreate, EventResponse, RegistrationResponse

router = APIRouter()

@router.get("/events/{event_id}", response_model=EventResponse, tags=["public"], summary="Get public event details")
async def get_public_event(event_id: int, response: Response, db: AsyncSession = Depends(get_db)):
    # Cache for 60 seconds at the edge, but allow stale-while-revalidate
    response.headers["Cache-Control"] = "public, s-maxage=60, stale-while-revalidate=30"
    
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.fields)) # Eagerly load fields
        .filter(Event.id == event_id)
    )
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # event.fields is already populated via selectinload
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
        "created_at": event.created_at,  # Required by EventResponse schema
        "fields": event.fields
    }

@router.post("/events/{event_id}/register", response_model=RegistrationResponse, tags=["public"], summary="Register for an event")
async def register_event(event_id: int, reg: RegistrationCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).filter(Event.id == event_id))
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event.max_seats:
        count_result = await db.execute(
            select(func.count(Registration.id)).filter(
                Registration.event_id == event_id,
                Registration.verified == True,
                Registration.payment_status == "paid"
            )
        )
        count = count_result.scalar() or 0
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
    await db.commit()
    await db.refresh(new_reg)
    return new_reg

@router.post("/responses", response_model=RegistrationResponse, tags=["public"], summary="Create a registration response")
async def create_response(reg: RegistrationCreate, db: AsyncSession = Depends(get_db)):
    if not reg.eventId:
        raise HTTPException(status_code=400, detail="Event ID is required")
        
    event_id = reg.eventId
    result = await db.execute(select(Event).filter(Event.id == event_id))
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event.max_seats:
        count_result = await db.execute(
            select(func.count(Registration.id)).filter(
                Registration.event_id == event_id,
                Registration.verified == True,
                Registration.payment_status == "paid"
            )
        )
        count = count_result.scalar() or 0
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
    await db.commit()
    await db.refresh(new_reg)
    return new_reg
