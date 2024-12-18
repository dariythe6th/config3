import argparse
import re
import toml

# Регулярные выражения для анализа синтаксиса
NAME_REGEX = re.compile(r'^[_a-zA-Z][_a-zA-Z0-9]*$')
STRING_REGEX = re.compile(r'^\[\[.*\]\]$')
CONST_DEF_REGEX = re.compile(r'^def\s+([_a-zA-Z][_a-zA-Z0-9]*)\s*=\s*(.+)$')
ARRAY_REGEX = re.compile(r'^array\((.*)\)$')
EXPR_REGEX = re.compile(r'\$(.+)\$')


class ConfigParser:
    def __init__(self):
        self.constants = {}

    def parse_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return self.parse_lines(lines)

    def parse_lines(self, lines):
        result = {}
        in_multiline_comment = False

        for line in lines:
            line = line.strip()

            # Обработка многострочных комментариев
            if line.startswith('{-'):
                in_multiline_comment = True
            if in_multiline_comment:
                if line.endswith('-}'):
                    in_multiline_comment = False
                continue

            if not line or line.startswith('#'):  # Игнорируем пустые строки и однострочные комментарии
                continue

            # Обработка объявления констант
            const_match = CONST_DEF_REGEX.match(line)
            if const_match:
                name, value = const_match.groups()
                value = self.evaluate_expression(value)
                self.constants[name] = value
                continue

            # Обработка массивов
            array_match = ARRAY_REGEX.match(line)
            if array_match:
                content = array_match.group(1)
                result['array'] = self.parse_array(content)
                continue

            # Прочие конструкции можно добавить аналогично
            raise SyntaxError(f"Unrecognized syntax: {line}")
        return result

    def parse_array(self, content):
        values = [v.strip() for v in content.split(',')]
        return [self.evaluate_expression(v) for v in values]

    def evaluate_expression(self, expr):
        expr = expr.strip()
        if STRING_REGEX.match(expr):
            return expr[2:-2]
        if expr.isdigit():
            return int(expr)
        if expr in self.constants:
            return self.constants[expr]
        if EXPR_REGEX.match(expr):
            evaluated = eval(expr.strip('$'), {}, self.constants)
            return evaluated
        raise ValueError(f"Invalid expression: {expr}")


def main():
    parser = argparse.ArgumentParser(description="Transform config language to TOML")
    parser.add_argument('input_file', help="Path to the input configuration file")
    args = parser.parse_args()

    config_parser = ConfigParser()
    try:
        parsed_config = config_parser.parse_file(args.input_file)
        toml_output = toml.dumps(parsed_config)
        print(toml_output)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
