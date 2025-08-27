from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from database import Base
from datetime import datetime

class UserTypes(Base):
    __tablename__ = 'user_types'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Users(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True, index=True, nullable=False)
	user_type = Column(Integer, ForeignKey('user_types.id'), default=2, nullable=False)
	username = Column(String, unique=True, index=True, nullable=False)
	email = Column(String, unique=True, index=True, nullable=False)
	password = Column(String, nullable=False)
	created_date = Column(DateTime, default=datetime.now)

class Ownerships(Base):
	__tablename__ = 'ownerships'
	id = Column(Integer, primary_key=True, index=True)
	owner = Column(Integer, ForeignKey('users.id'))
	part = Column(Integer, ForeignKey('parts.id'))

class Parts(Base):
	__tablename__ = 'parts'
	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, index=True)
	stats = Column(Integer, ForeignKey('stats.id'), nullable=True)
	color = Column(String, index=True)
	type = Column(Integer, ForeignKey('part_types.id'))
	restriction = Column(Integer, ForeignKey('restrictions.id'), nullable=True, default=None)
	description = Column(String, nullable=True, default=None)

class Stats(Base):
	__tablename__ = 'stats'
	id = Column(ForeignKey('parts.id'), primary_key=True, index=True)
	minAtk = Column(Integer, nullable=True, default=None)
	maxAtk = Column(Integer, nullable=True, default=None)
	minDef = Column(Integer, nullable=True, default=None)
	maxDef = Column(Integer, nullable=True, default=None)
	minSta = Column(Integer, nullable=True, default=None)
	maxSta = Column(Integer, nullable=True, default=None)
	weight = Column(Integer, nullable=True, default=None)
	burst = Column(Integer, nullable=True, default=None)
	dash = Column(Integer, nullable=True, default=None)

class Combos(Base):
	__tablename__ = "combos"
	id = Column(Integer, primary_key=True, index=True)
	isStock = Column(Boolean, default=False)
	line = Column(Integer, ForeignKey('lines.id'))
	lock_chip = Column(Integer, ForeignKey('parts.id'), nullable=True, default=None)
	main_blade = Column(Integer, ForeignKey('parts.id'), nullable=True, default=None)
	assis_blade = Column(Integer, ForeignKey('parts.id'), nullable=True, default=None)
	ratchet = Column(Integer, ForeignKey('parts.id'), nullable=True, default=None)
	bit = Column(Integer, ForeignKey('parts.id'), nullable=True, default=None)
	combo_type = Column(String, nullable=True, default=None)
	description = Column(String)
	created_date = Column(DateTime, default=datetime.now)

class Lines(Base):
    __tablename__ = 'lines'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class PartTypes(Base):
    __tablename__ = 'part_types'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
class Restrictions(Base):
    __tablename__ = 'restrictions'
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, unique=True, index=True)