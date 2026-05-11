from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, Float
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import enum

from config import settings

# Use CATALYST_DB_URL override if DATABASE_URL env conflicts with other services
_db_url = settings.DATABASE_URL
if not _db_url.startswith(("sqlite", "postgresql", "mysql")):
    _db_url = "sqlite:///support.db"

engine = create_engine(
    _db_url,
    connect_args={"check_same_thread": False} if "sqlite" in _db_url else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SubscriptionStatus(str, enum.Enum):
    free = "free"
    premium = "premium"
    expired = "expired"


class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"


# ── Core Models ──────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.free)
    subscription_end = Column(DateTime, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="user")
    tickets = relationship("Ticket", back_populates="user")
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    referrals = relationship("Referral", back_populates="referrer", foreign_keys="Referral.referrer_id")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    content = Column(Text, nullable=False)
    from_ai = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="messages")
    ticket = relationship("Ticket", back_populates="messages")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.open)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tickets")
    messages = relationship("Message", back_populates="ticket")


# ── Signal History ───────────────────────────────────────────────────

class SignalHistory(Base):
    __tablename__ = "signal_history"
    id          = Column(Integer, primary_key=True)
    symbol      = Column(String)
    direction   = Column(String)
    timeframe   = Column(String)
    platform    = Column(String)
    entry_time  = Column(DateTime)
    outcome     = Column(String, default='pending')   # win / loss / ignored
    rsi         = Column(Float)
    adx         = Column(Float)
    confidence  = Column(Float)
    accuracy    = Column(Float)


# ── Tournaments ──────────────────────────────────────────────────────

class Tournament(Base):
    __tablename__ = "tournaments"
    id           = Column(Integer, primary_key=True)
    name         = Column(String(100))
    start_time   = Column(DateTime)
    end_time     = Column(DateTime)
    entry_fee    = Column(Float, default=0)
    prize_pool   = Column(Float, default=0)
    status       = Column(String(20), default='upcoming')  # upcoming, active, ended
    created_by   = Column(Integer, ForeignKey("users.id"))
    participants = relationship("TournamentParticipant", back_populates="tournament")


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"
    id            = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    user_id       = Column(Integer, ForeignKey("users.id"))
    score         = Column(Float, default=0)   # total profit or points
    rank          = Column(Integer, default=0)
    tournament    = relationship("Tournament", back_populates="participants")


# ── Referrals ────────────────────────────────────────────────────────

class Referral(Base):
    __tablename__ = "referrals"
    id            = Column(Integer, primary_key=True)
    referrer_id   = Column(Integer, ForeignKey("users.id"))
    referred_name = Column(String)
    referred_email= Column(String)
    signup_date   = Column(DateTime, default=datetime.utcnow)
    status        = Column(String(20), default='pending')   # pending, joined
    referrer      = relationship("User", back_populates="referrals", foreign_keys=[referrer_id])


# ── User Settings ────────────────────────────────────────────────────

class UserSettings(Base):
    __tablename__ = "user_settings"
    user_id         = Column(Integer, ForeignKey("users.id"), primary_key=True)
    telegram_alerts = Column(Boolean, default=True)
    email_alerts    = Column(Boolean, default=False)
    timezone        = Column(String(50), default="UTC")
    risk_level      = Column(String(20), default="medium")   # low, medium, high
    user            = relationship("User", back_populates="settings")


# ── Giveaways ────────────────────────────────────────────────────────

class Giveaway(Base):
    __tablename__ = "giveaways"
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    description = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    prize = Column(String(200))
    winners_count = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="upcoming")   # upcoming, active, ended
    participants = relationship("GiveawayParticipant", back_populates="giveaway")


class GiveawayParticipant(Base):
    __tablename__ = "giveaway_participants"
    id = Column(Integer, primary_key=True)
    giveaway_id = Column(Integer, ForeignKey("giveaways.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    entered_at = Column(DateTime, default=datetime.utcnow)
    giveaway = relationship("Giveaway", back_populates="participants")


def init_db():
    Base.metadata.create_all(bind=engine)
