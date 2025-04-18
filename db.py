class MiniDB:
    def __init__(self, columns, path):
        self.columns = list(columns)
        self.data = []
        self.load_from_file(path)
    
    def load_from_file(self, path):
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(';')

                if len(parts) != len(self.columns):
                    raise ValueError(f"не відповідає кількості колонок: {line}")
                record = {self.columns[i]:parts[i] for i in range(len(self.columns))}
                self.data.append(record)
    
    def save_to_file(self, path):
        with open(path, 'w') as f:
            for record in self.data:
                line = ';'.join(str(record[col]) for col in self.columns)
                f.write(line+'\n')

    def add(self, values):
        if len(values) != len(self.columns):
            raise ValueError(f"не відповідає кількості колонок: {values}")
        record = {self.columns[i]:values[i] for i in range(len(self.columns))}
        self.data.append(record)