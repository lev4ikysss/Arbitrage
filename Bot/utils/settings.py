from configparser import ConfigParser

class GetParams:
    def __init__(self, file_path: str):
        """
            Получает значение файлов, и хранит их в классе
            :file_path: путь до файла конфигурации
        """
        configuration = ConfigParser()
        configuration.read(file_path, encoding="utf-8")
        self.token_tg = configuration["tg"]["token"]
        self.db_path = configuration["database"]["path"]
        self.codes_path = configuration["codes"]["path"]