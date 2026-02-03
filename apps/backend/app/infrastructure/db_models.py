from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AquariumModel(Base):
    __tablename__ = "aquariums"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    water_type: Mapped[str] = mapped_column(
        Enum("fresh", "salt", name="water_type"), nullable=False
    )
    liters: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    temperature_min: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_max: Mapped[float] = mapped_column(Float, nullable=False)
    ph_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ph_min: Mapped[float] = mapped_column(Float, nullable=False)
    ph_max: Mapped[float] = mapped_column(Float, nullable=False)
    tds_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tds_min: Mapped[float] = mapped_column(Float, nullable=False)
    tds_max: Mapped[float] = mapped_column(Float, nullable=False)
    filter_type: Mapped[str | None] = mapped_column(String(50))
    filter_flow_lph: Mapped[float | None] = mapped_column(Float)
    heater_watts: Mapped[float | None] = mapped_column(Float)
    lighting_type: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class DeviceModel(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(200))
    owner_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ReadingModel(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id"), nullable=False)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    raw_ph_voltage: Mapped[float] = mapped_column(Float, nullable=False)
    raw_tds_voltage: Mapped[float] = mapped_column(Float, nullable=False)
    ph_value: Mapped[float] = mapped_column(Float, nullable=False)
    tds_ppm: Mapped[float] = mapped_column(Float, nullable=False)
    ph_calibrated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AquariumDeviceModel(Base):
    __tablename__ = "aquarium_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aquarium_id: Mapped[str] = mapped_column(String(36), ForeignKey("aquariums.id"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id"), nullable=False)
    attached_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    detached_at: Mapped[datetime | None] = mapped_column(DateTime)


class DeviceApiKeyModel(Base):
    __tablename__ = "device_api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id"), nullable=False)
    key_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)


class DevicePhCalibrationModel(Base):
    __tablename__ = "device_ph_calibrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id"), nullable=False)
    ph_point: Mapped[float] = mapped_column(Float, nullable=False)
    voltage: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
