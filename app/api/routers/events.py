from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List

from app.api.deps import get_db, get_current_user
from app.db.models import User, Event, EventField, Registration
from app.api.endpoints.common import EventCreate, EventResponse, RegistrationResponse, MessageResponse
 
router = APIRouter()

@router.get("/", response_model=List[EventResponse], tags=["events"], summary="List all events")
async def get_events(
    response: Response,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # Set Cache-Control header for private, personalized content
    response.headers["Cache-Control"] = "private, max-age=60"
    
    # Optimized query to fetch events and their verified registration counts in a single efficient join
    # This eliminates the N+1 query bottleneck
    query = (
        select(
            Event,
            func.count(Registration.id).filter(Registration.verified == True).label("registration_count")
        )
        .outerjoin(Registration, Event.id == Registration.event_id)
        .options(selectinload(Event.fields)) # Eagerly load fields to avoid MissingGreenlet
        .filter(Event.organizer_id == current_user.id)
        .group_by(Event.id)
        .order_by(desc(Event.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    rows = result.all() # Each row is (Event object, count)
    
    res = []
    for event, reg_count in rows:
        # Pydantic/SQLAlchemy compatibility: construct response dict
        e_dict = {c.name: getattr(event, c.name) for c in event.__table__.columns}
        e_dict['fields'] = event.fields # already prefetched if using 'selectinload' in model, else Lazy
        e_dict['registration_count'] = reg_count
        res.append(e_dict)
    return res

@router.get("/{event_id}", response_model=EventResponse, tags=["events"], summary="Get event details")
async def get_event(
    event_id: int, 
    response: Response,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    # Set Cache-Control header
    response.headers["Cache-Control"] = "private, max-age=60"
    
    query = (
        select(
            Event,
            func.count(Registration.id).filter(Registration.verified == True).label("registration_count")
        )
        .outerjoin(Registration, Event.id == Registration.event_id)
        .options(selectinload(Event.fields)) # Eagerly load fields
        .filter(Event.id == event_id, Event.organizer_id == current_user.id)
        .group_by(Event.id)
    )
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event, reg_count = row
    
    # event.fields is already populated via selectinload in the query above
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
        "registration_count": reg_count,
        "created_at": event.created_at,
        "fields": event.fields
    }

@router.post("/", response_model=EventResponse, tags=["events"], summary="Create an event")
async def create_event(event: EventCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        print(f"DEBUG: Starting event creation for user {current_user.id}")
        print(f"DEBUG: Payload: {event.dict()}")
        
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
        await db.commit()
        await db.refresh(new_event)
        
        print(f"DEBUG: Event created with ID: {new_event.id}")
        
        if event.fields:
            print(f"DEBUG: Adding {len(event.fields)} fields")
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
            await db.commit()
        
        # Fetch fields to include in response
        fields_result = await db.execute(
            select(EventField).filter(EventField.event_id == new_event.id).order_by(EventField.order_index)
        )
        fields = fields_result.scalars().all()
        
        print(f"DEBUG: event_create successful")
        
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
    except Exception as e:
        print(f"ERROR in create_event: {str(e)}")
        import traceback
        traceback.print_exc()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")

@router.put("/{event_id}", response_model=EventResponse, tags=["events"], summary="Update an event")
async def update_event(event_id: int, event: EventCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id)
    )
    db_event = result.scalars().first()
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
        existing_fields_result = await db.execute(
            select(EventField).filter(EventField.event_id == event_id)
        )
        existing_fields = {f.id: f for f in existing_fields_result.scalars().all()}
        
        # Track which IDs have been processed (updated)
        processed_ids = set()

        for f in event.fields:
            try:
                f_id = int(f.id) if f.id is not None else None
            except (ValueError, TypeError):
                f_id = None

            if f_id is not None and f_id in existing_fields:
                db_field = existing_fields[f_id]
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
                processed_ids.add(f_id)
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
                await db.delete(db_field)
            
    await db.commit()
    await db.refresh(db_event)
    
    # Fetch fields to include in response
    fields_result = await db.execute(
        select(EventField).filter(EventField.event_id == event_id).order_by(EventField.order_index)
    )
    fields = fields_result.scalars().all()
    
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

@router.delete("/{event_id}", response_model=MessageResponse, tags=["events"], summary="Delete an event")
async def delete_event(event_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id)
    )
    db_event = result.scalars().first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    await db.delete(db_event)
    await db.commit()
    return {"success": True}

@router.get("/{event_id}/registrations", response_model=List[RegistrationResponse], tags=["events"], summary="List event registrations")
async def get_registrations(
    event_id: int, 
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id)
    )
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    regs_result = await db.execute(
        select(Registration)
        .filter(Registration.event_id == event_id)
        .order_by(desc(Registration.submitted_at))
        .offset(skip)
        .limit(limit)
    )

    regs = regs_result.scalars().all()
    return regs

import csv
import io
from fastapi.responses import StreamingResponse

@router.get("/{event_id}/export", tags=["events"], summary="Export registrations to CSV")
async def export_event_registrations(event_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id)
    )
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Get fields for headers ignoring SECTION fields which have no answers usually
    fields_result = await db.execute(
        select(EventField).filter(EventField.event_id == event_id, EventField.type != 'SECTION').order_by(EventField.order_index)
    )
    fields = fields_result.scalars().all()
    headers = ["Submission Date"] + [f.label for f in fields]
    
    # Get registrations
    regs_result = await db.execute(
        select(Registration).filter(Registration.event_id == event_id).order_by(desc(Registration.submitted_at))
    )
    registrations = regs_result.scalars().all()
    
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

@router.put("/{event_id}/registrations/{reg_id}/approve", response_model=MessageResponse, tags=["events"], summary="Approve a registration")
async def approve_registration(event_id: int, reg_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id)
    )
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    reg_result = await db.execute(
        select(Registration).filter(Registration.id == reg_id, Registration.event_id == event_id)
    )
    reg = reg_result.scalars().first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
        
    reg.verified = True
    reg.payment_status = "paid"
    await db.commit()
    return {"success": True, "status": "paid"}

@router.put("/{event_id}/registrations/{reg_id}/reject", response_model=MessageResponse, tags=["events"], summary="Reject a registration")
async def reject_registration(event_id: int, reg_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Event).filter(Event.id == event_id, Event.organizer_id == current_user.id)
    )
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    reg_result = await db.execute(
        select(Registration).filter(Registration.id == reg_id, Registration.event_id == event_id)
    )
    reg = reg_result.scalars().first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
        
    reg.verified = False
    reg.payment_status = "failed"
    await db.commit()
    return {"success": True, "status": "failed"}
