from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, auth
from .database import get_db
from datetime import timedelta
from sqlalchemy import func

router = APIRouter()


@router.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = auth.get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/polls", response_model=List[schemas.PollOut])
def get_polls(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    polls = db.query(models.Poll).offset(skip).limit(limit).all()
    return polls


@router.get("/polls/{poll_id}", response_model=schemas.PollOut)
def get_poll(poll_id: int, db: Session = Depends(get_db)):
    poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return poll


@router.post("/polls/{poll_id}/vote", response_model=schemas.VoteOut)
def vote_on_poll(
    poll_id: int,
    vote: schemas.VoteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    # Check if the poll exists
    poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    # Check if the option exists and belongs to the poll
    option = db.query(models.Option).filter(
        models.Option.id == vote.option_id,
        models.Option.poll_id == poll_id
    ).first()
    if not option:
        raise HTTPException(status_code=404, detail="Option not found or does not belong to this poll")

    # Check if the user has already voted on this poll
    existing_vote = db.query(models.Vote).join(models.Option).filter(
        models.Vote.user_id == current_user.id,
        models.Option.poll_id == poll_id
    ).first()

    if existing_vote:
        # Update the existing vote
        setattr(existing_vote, 'option_id', vote.option_id)
        db.commit()
        db.refresh(existing_vote)
        return existing_vote

    # Create a new vote
    new_vote = models.Vote(user_id=current_user.id, option_id=vote.option_id)
    db.add(new_vote)
    db.commit()
    db.refresh(new_vote)
    return new_vote


@router.get("/polls/{poll_id}/results")
def get_poll_results(poll_id: int, db: Session = Depends(get_db)):
    # Check if the poll exists
    poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    # Get the options with vote counts
    results = db.query(
        models.Option.id,
        models.Option.text,
        func.count(models.Vote.id).label("vote_count")
    ).outerjoin(models.Vote).filter(
        models.Option.poll_id == poll_id
    ).group_by(models.Option.id).all()

    # Format the results
    formatted_results = [
        {"option_id": option_id, "text": text, "vote_count": vote_count}
        for option_id, text, vote_count in results
    ]

    return {"poll_id": poll_id, "question": poll.question, "results": formatted_results}


@router.post("/polls", response_model=schemas.PollOut)
def create_poll(
    poll: schemas.PollCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    # Validate that at least two options are provided
    if len(poll.options) < 2:
        raise HTTPException(
            status_code=400, detail="At least two options are required for a poll"
        )

    # Create the poll
    new_poll = models.Poll(question=poll.question, owner_id=current_user.id)
    db.add(new_poll)
    db.commit()
    db.refresh(new_poll)

    # Create the options for the poll
    for option_text in poll.options:
        option = models.Option(text=option_text, poll_id=new_poll.id)
        db.add(option)

    db.commit()
    db.refresh(new_poll)
    return new_poll


@router.delete("/polls/{poll_id}", status_code=204)
def delete_poll(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    poll = (
        db.query(models.Poll)
        .filter(models.Poll.id == poll_id, models.Poll.owner_id == current_user.id)
        .first()
    )
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found or not authorized")
    db.delete(poll)
    db.commit()
    return None
