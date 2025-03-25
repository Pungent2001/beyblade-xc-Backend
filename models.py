from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from database import Base
from datetime import datetime
class User(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True, index=True)
	username = Column(String, unique=True, index=True)
	email = Column(String, unique=True, index=True)
	password = Column(String)
	created_date = Column(DateTime, default=datetime.now)

class Part(Base):
	__tablename__ = 'parts'
	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, unique=True, index=True)
	type = Column(String, index=True)
	line = Column(String, index=True)
	description = Column(String)

class Ownership(Base):
	__tablename__ = 'ownership'
	id = Column(Integer, primary_key=True, index=True)
	owner = Column(Integer, ForeignKey('users.id'))
	part = Column(Integer, ForeignKey('parts.id'))

class Stats(Base):
	__tablename__ = 'stats'
	id = Column(Integer, primary_key=ForeignKey('parts.id'), index=True)
	attack = Column(Integer)
	defense = Column(Integer)
	stamina = Column(Integer)
	weight = Column(Integer)

class BitStats(Base):
	__tablename__ = 'bit_stats'
	id = Column(Integer, primary_key=ForeignKey('parts.id'), index=True)
	attack = Column(Integer)
	defense = Column(Integer)
	stamina = Column(Integer)
	weight = Column(Integer)
	burst = Column(Integer)
	dash = Column(Integer)

class Combo(Base):
	__tablename__ = "combos"
	id = Column(Integer, primary_key=True, index=True)
	owner = Column(Integer, ForeignKey('users.id'))
	lock_chip = Column(Integer, ForeignKey('parts.id'))
	main_blade = Column(Integer, ForeignKey('parts.id'))
	assis_blade = Column(Integer, ForeignKey('parts.id'))
	ratchet = Column(Integer, ForeignKey('parts.id'))
	bit = Column(Integer, ForeignKey('parts.id'))
	combo_type = Column(String, index=True)
	description = Column(String)
	created_date = Column(DateTime, default=datetime.now)

