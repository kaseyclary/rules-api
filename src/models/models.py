from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Agency(Base):
    __tablename__ = 'agencies'
    
    id = Column(Integer, primary_key=True)
    agency_name = Column(String(255), nullable=False)
    agency_number = Column(String(50), nullable=False)
    created_date = Column(Date)
    last_modified_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_word_count = Column(Integer, default=0)

    # Relationships
    chapters = relationship("Chapter", back_populates="agency")
    agency_years = relationship("AgencyYear", back_populates="agency")

    def __repr__(self):
        return f"<Agency(name='{self.agency_name}', number='{self.agency_number}')>"

class Chapter(Base):
    __tablename__ = 'chapters'
    
    id = Column(Integer, primary_key=True)
    agency_id = Column(Integer, ForeignKey('agencies.id'), nullable=False)
    chapter_number = Column(String(50), nullable=False)
    chapter_title = Column(Text, nullable=False)
    year = Column(Integer, nullable=False)
    effective_date = Column(Date)
    last_modified_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_word_count = Column(Integer, default=0)
    agency_year_id = Column(Integer, ForeignKey('agency_years.id'), nullable=False)
    
    # Relationships
    agency = relationship("Agency", back_populates="chapters")
    rules = relationship("Rule", back_populates="chapter")
    agency_year = relationship("AgencyYear", back_populates="chapters")

    def __repr__(self):
        return f"<Chapter(number='{self.chapter_number}', title='{self.chapter_title}')>"

class Rule(Base):
    __tablename__ = 'rules'
    
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'), nullable=False)
    citation = Column(String, nullable=False)  # Full citation (e.g., "25—8.1(22)")
    rule_number = Column(String, nullable=False)  # Just the number part (e.g., "8.1")
    rule_title = Column(String)
    rule_text = Column(Text)
    description = Column(Text)  # New: plain-language summary description
    effective_date = Column(Date)
    last_modified_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_word_count = Column(Integer, default=0)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="rules")
    subrules = relationship("Subrule", back_populates="rule", cascade="all, delete-orphan")
    agency_year = relationship("AgencyYear", back_populates="rules")

    def __repr__(self):
        return f"<Rule(number='{self.rule_number}')>"

class Subrule(Base):
    __tablename__ = 'subrules'
    
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey('rules.id'), nullable=False)
    subrule_number = Column(String(50), nullable=False)
    citation = Column(String, nullable=True)
    subrule_text = Column(Text)
    description = Column(Text)  # New: plain-language description field
    effective_date = Column(Date)
    last_modified_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_word_count = Column(Integer, default=0)
    
    # Relationships
    rule = relationship("Rule", back_populates="subrules")
    agency_year = relationship("AgencyYear", back_populates="subrules")

    def __repr__(self):
        return f"<Subrule(number='{self.subrule_number}')>"

class AgencyYear(Base):
    __tablename__ = 'agency_years'
    
    id = Column(Integer, primary_key=True)
    agency_id = Column(Integer, ForeignKey('agencies.id'), nullable=False)
    year = Column(Integer, nullable=False)
    total_word_count = Column(Integer, default=0)
    created_date = Column(Date)
    last_modified_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agency = relationship("Agency", back_populates="agency_years")
    chapters = relationship("Chapter", back_populates="agency_year")
    rules = relationship("Rule", back_populates="agency_year")
    subrules = relationship("Subrule", back_populates="agency_year")

    def __repr__(self):
        return f"<AgencyYear(agency_id={self.agency_id}, year={self.year})>"