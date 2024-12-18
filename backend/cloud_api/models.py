from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Aggregator(Base):
    __tablename__ = "aggregators"
    id = Column(Integer, primary_key=True)
    guid = Column(String, nullable=False)
    name = Column(String)

class Device(Base):
    __tablename__ = "devices"
    device_id = Column(String, primary_key=True)
    aggregator_id = Column(Integer, ForeignKey("aggregators.id"), nullable=False)
    name = Column(String)
    ordinal = Column(Integer)
    aggregator = relationship("Aggregator")

class MetricType(Base):
    __tablename__ = "device_metric_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"
    id = Column(Integer, primary_key=True)
    device_id = Column(String, ForeignKey("devices.device_id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    device = relationship("Device")

class MetricValue(Base):
    __tablename__ = "metric_values"
    snapshot_id = Column(Integer, ForeignKey("metric_snapshots.id"), primary_key=True)
    type_id = Column(Integer, ForeignKey("device_metric_types.id"), primary_key=True)
    value = Column(Float, nullable=False)
    snapshot = relationship("MetricSnapshot")
    type = relationship("MetricType")
