# database.py
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import config
from db_models import StaticData, ReclamationModel, Base

class Database:
    def __init__(self, password=None):
        self.password = password or config.DB_PASSWORD
        self.engine = None
        self.Session = None
        
        self._connect()
    
    def _connect(self):
        """Устанавливает соединение с базой данных"""
        try:
            connection_string = f"access+pyodbc://sqe:sqe@SQE_BD"
            
            self.engine = create_engine(connection_string, echo=False)
            self.Session = sessionmaker(bind=self.engine)
            
            with self.engine.connect() as conn:
                print("✅ Подключение к базе данных установлено")
                
        except Exception as e:
            print(f"❌ Ошибка подключения к базе: {e}")
            raise
    
    # ============ ОСНОВНЫЕ МЕТОДЫ (SQLAlchemy ORM) ============
    
    def save_reclamation(self, data):
        """Сохраняет новую рекламацию в базу (SQLAlchemy ORM)"""
        session = self.Session()
        try:
            data['date_creation'] = datetime.now()
            
            reclamation = ReclamationModel(**data)
            session.add(reclamation)
            session.commit()
            
            return {
                'success': True,
                'message': 'Рекламация сохранена',
                'id': reclamation.id
            }
            
        except SQLAlchemyError as e:
            session.rollback()
            return {'success': False, 'message': f'Ошибка базы данных: {str(e)}'}
        except Exception as e:
            session.rollback()
            return {'success': False, 'message': f'Ошибка: {str(e)}'}
        finally:
            session.close()
    
    def get_all_reclamations(self):
        """Получает все рекламации (SQLAlchemy ORM)"""
        session = self.Session()
        try:
            return session.query(ReclamationModel).order_by(ReclamationModel.id.desc()).all()
        except SQLAlchemyError as e:
            print(f"Ошибка получения данных: {e}")
            return []
        finally:
            session.close()
    
    def get_reclamation_by_id(self, rec_id):
        """Получает рекламацию по ID (SQLAlchemy ORM)"""
        session = self.Session()
        try:
            return session.query(ReclamationModel).filter(ReclamationModel.id == rec_id).first()
        except SQLAlchemyError as e:
            print(f"Ошибка: {e}")
            return None
        finally:
            session.close()
    
    def update_reclamation(self, rec_id, data):
        """Обновляет существующую рекламацию (SQLAlchemy ORM)"""
        session = self.Session()
        try:
            reclamation = session.query(ReclamationModel).filter(ReclamationModel.id == rec_id).first()
            
            if reclamation:
                for key, value in data.items():
                    setattr(reclamation, key, value)
                session.commit()
                return {'success': True, 'message': 'Рекламация обновлена'}
            
            return {'success': False, 'message': 'Рекламация не найдена'}
            
        except SQLAlchemyError as e:
            session.rollback()
            return {'success': False, 'message': f'Ошибка: {str(e)}'}
        finally:
            session.close()
    
    def delete_reclamation(self, rec_id):
        """Удаляет рекламацию по ID (SQLAlchemy ORM)"""
        session = self.Session()
        try:
            reclamation = session.query(ReclamationModel).filter(ReclamationModel.id == rec_id).first()
            
            if reclamation:
                session.delete(reclamation)
                session.commit()
                return {'success': True, 'message': 'Рекламация удалена'}
            
            return {'success': False, 'message': 'Рекламация не найдена'}
            
        except SQLAlchemyError as e:
            session.rollback()
            return {'success': False, 'message': f'Ошибка: {str(e)}'}
        finally:
            session.close()
    
    # ============ МЕТОДЫ ДЛЯ ПОЛУЧЕНИЯ СПРАВОЧНЫХ ДАННЫХ ============
    
    def get_models(self):
        """Получает список моделей из таблицы static_data (SQLAlchemy ORM)"""
        session = self.Session()
        try:
            models = session.query(StaticData.models_list).filter(
                StaticData.models_list.isnot(None)
            ).filter(
                StaticData.models_list != ''
            ).order_by(
                StaticData.models_list
            ).all()
            
            return [model[0] for model in models] or []
            
        except SQLAlchemyError as e:
            print(f"Ошибка получения моделей: {e}")
            return []
        finally:
            session.close()
    
    def get_suppliers(self):
        """Получает список поставщиков из таблицы static_data (SQLAlchemy ORM)"""
        session = self.Session()
        try:
            suppliers = session.query(StaticData.suppliers_list).filter(
                StaticData.suppliers_list.isnot(None)
            ).filter(
                StaticData.suppliers_list != ''
            ).order_by(
                StaticData.suppliers_list
            ).all()
            
            return [supplier[0] for supplier in suppliers] or []
            
        except SQLAlchemyError as e:
            print(f"Ошибка получения поставщиков: {e}")
            return []
        finally:
            session.close()
    
    def get_commodities(self):
        """Получает список товарных групп из таблицы static_data (SQLAlchemy ORM)"""
        session = self.Session()
        try:
            commodities = session.query(StaticData.commodity).filter(
                StaticData.commodity.isnot(None)
            ).filter(
                StaticData.commodity != ''
            ).order_by(
                StaticData.commodity
            ).all()
            
            return [comm[0] for comm in commodities] or []
            
        except SQLAlchemyError as e:
            print(f"Ошибка получения товарных групп: {e}")
            return []
        finally:
            session.close()
    
    def get_creators(self):
        """Получает список уникальных создателей из таблицы рекламаций (SQLAlchemy ORM)"""
        session = self.Session()
        try:
            creators = session.query(ReclamationModel.creator).filter(
                ReclamationModel.creator.isnot(None)
            ).filter(
                ReclamationModel.creator != ''
            ).distinct().order_by(
                ReclamationModel.creator
            ).all()
            
            return [row[0] for row in creators] or []
            
        except SQLAlchemyError as e:
            print(f"Ошибка получения создателей: {e}")
            return []
        finally:
            session.close()
    
    def get_parts_disposal(self):
        """Получает список вариантов утилизации деталей из таблицы static_data (SQLAlchemy ORM)"""
        session = self.Session()
        try:
            parts_disposal = session.query(StaticData.parts_disposal).filter(
                StaticData.parts_disposal.isnot(None)
            ).filter(
                StaticData.parts_disposal != ''
            ).order_by(
                StaticData.parts_disposal
            ).all()
            
            return [row[0] for row in parts_disposal] or []
            
        except SQLAlchemyError as e:
            print(f"Ошибка получения списка утилизации деталей: {e}")
            return []
        finally:
            session.close()
    
    def get_repetition_list(self):
        """Получает список вариантов повторяемости из таблицы static_data (SQLAlchemy ORM)"""
        session = self.Session()
        try:
            repetition = session.query(StaticData.repetition).filter(
                StaticData.repetition.isnot(None)
            ).filter(
                StaticData.repetition != ''
            ).order_by(
                StaticData.repetition
            ).all()
            
            return [row[0] for row in repetition] or []
            
        except SQLAlchemyError as e:
            print(f"Ошибка получения списка повторяемости: {e}")
            return []
        finally:
            session.close()
    
    # ✅ НОВЫЙ МЕТОД: Получение списка дефектов из поля defect_name
    def get_defect_names(self):
        """Получает список дефектов из таблицы static_data (SQLAlchemy ORM)"""
        session = self.Session()
        try:
            defects = session.query(StaticData.defect_name).filter(
                StaticData.defect_name.isnot(None)
            ).filter(
                StaticData.defect_name != ''
            ).order_by(
                StaticData.defect_name
            ).all()
            
            return [row[0] for row in defects] or []
            
        except SQLAlchemyError as e:
            print(f"Ошибка получения списка дефектов: {e}")
            return []
        finally:
            session.close()