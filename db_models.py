# db_models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# ============================================
# МОДЕЛЬ: Рекламации
# ============================================
class ReclamationModel(Base):
    __tablename__ = 'ncr_table'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(String(100), nullable=False)
    creator = Column(String(100))
    commodity = Column(String(100))
    partnumber = Column(String(100))
    partname = Column(String(100))
    repetition = Column(String(50))
    description = Column(Text)
    supplier = Column(String(100))
    full_pir_number = Column(String(100))
    date_creation = Column(DateTime)
    ncr_status = Column(String(50))
    failure_quantity = Column(Integer())
    vin = Column(String(17))
    comments = Column(String(255))
    defect = Column(String(50))
    cutoff = Column(DateTime)
    report8d_checkbox = Column(Boolean)

    
    def __repr__(self):
        return f"<Reclamation(id={self.id}, model='{self.model}', supplier='{self.supplier}', failure_quantity='{self.failure_quantity}', \
        vin='{self.vin}', supplier='{self.comments}', defect='{self.defect}', cutoff='{self.cutoff}', report8d_checkbox='{self.report8d_checkbox}')>"

# ============================================
# МОДЕЛЬ: Статические данные (справочники)
# ============================================
class StaticData(Base):
    __tablename__ = 'static_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    models_list = Column(String(10))
    suppliers_list = Column(String(30))
    commodity = Column(String(30))
    defect_name = Column(String(30))
    
    def __repr__(self):
        return f"<StaticData(id={self.id}, model='{self.models_list}', supplier='{self.suppliers_list}', commodity='{self.commodity}', defect_name='{self.defect_name}')>"