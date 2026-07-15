# Путь к базе Access
DB_PATH = r"X:/SQE_DB/AGS_SQE_DB.accdb"  # Измените на ваш путь

# Пароль базы данных Access
DB_PASSWORD = "sqe"  # Установите свой пароль

# Строка подключения ODBC с паролем
def get_odbc_conn_str():
    return (
        f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};"
        f"DBQ={DB_PATH};"
        f"PWD={DB_PASSWORD};"
    )

# Таблица в базе
TABLE_NAME = "ncr_table"

# Список моделей и поставщиков для выпадающих списков
# Можно загружать из базы или хранить здесь
MODELS = [
    "Model A", "Model B", "Model C", "Model D", "Model E"
]

SUPPLIERS = [
    "Supplier 1", "Supplier 2", "Supplier 3", "Supplier 4"
]

# Статусы NCR
NCR_STATUSES = [
    "Open",
    "In Progress", 
    "Under Investigation",
    "Closed",
    "Rejected",
    "Implemented"
]

NCR_TEMPLATE_PATH = r"X:\SQE_DB\Templates\sqe_template.pptx"