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
    email = Column(String(120), nullable=True)
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


# ── App Settings ────────────────────────────────────────────────────

class AppSettings(Base):
    __tablename__ = "app_settings"
    id = Column(Integer, primary_key=True)
    paywall_enabled = Column(Boolean, default=False)
    plans_json = Column(Text, default='{"weekly":{"name":"Weekly","price":9.99,"days":7},"monthly":{"name":"Monthly","price":19.99,"days":30},"quarterly":{"name":"Quarterly","price":49.99,"days":90}}')
    protected_routes = Column(Text, default='/dashboard,/signals')
    email_alerts = Column(Boolean, default=True)


# ── VIP Challenges ──────────────────────────────────────────────────

class VIPChallenge(Base):
    __tablename__ = "vip_challenges"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(Text, default="")
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    entry_fee = Column(Float, default=0.0)
    prize_pool = Column(Float, default=0.0)
    status = Column(String(20), default="upcoming")   # upcoming, active, ended
    created_by = Column(Integer, ForeignKey("admin_users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    participants = relationship("VIPChallengeParticipant", back_populates="challenge")


class VIPChallengeParticipant(Base):
    __tablename__ = "vip_challenge_participants"
    id = Column(Integer, primary_key=True)
    challenge_id = Column(Integer, ForeignKey("vip_challenges.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)
    score = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    challenge = relationship("VIPChallenge", back_populates="participants")


# ── Community Chat Messages ────────────────────────────────────────

class CommunityMessage(Base):
    __tablename__ = "community_messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    username = Column(String(100))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Admin Auth (JWT) ────────────────────────────────────────────────

class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, index=True)
    password_hash = Column(String(120))
    full_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def set_password(self, password: str):
        import bcrypt
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


class AdminSession(Base):
    __tablename__ = "admin_sessions"
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"))
    refresh_token = Column(String(255), unique=True, index=True)
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    platform = Column(String(20), default="web")
    device_info = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)


class AdminActivityLog(Base):
    __tablename__ = "admin_activity_log"
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"))
    action = Column(String(100))
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
