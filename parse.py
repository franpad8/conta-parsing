""" Parseo de mensaje de carga de contabilidad para cuentas tipo valores """
import re

# for printing json nicely
import pprint

### Define dictionary of errors with respective languages ###
_ERROR_DICT = {
    0: {
        0: "Error de sintaxis en linea %s.",
        1: "Sintax error in line %s."
    },
    1: {
        0: "Error de sintaxis en linea %s. Este campo debe contener la etiqueta \'%s\'.",
        1: "Sintax error in line %s. This field must have the tag \'%s\'."
    },
    2: {
        0: "Error de sintaxis en linea %s. Se esperaba un caracter '$' de inicio de mensaje.",
        1: "Sintax error in line %s. A message's beginning character '$' was expected."
    },
    3: {
        0: "Error de sintaxis en linea %s. El campo '%s' debe contener el siguiente formato '%s'.",
        1: "Sintax error in line %s. '%s' field must contain the following format: '%s'."
    },
}


class ParsingError(Exception):
    """ Parsing Exception Handling Class Definition """
    def __init__(self, code, lang, line, *args):
        Exception.__init__(self)
        self.msg = _ERROR_DICT[code][lang]%((line,)+tuple(args))

### REGEX ###
R_BIC = r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?"
R_DECIMAL = r"\d+,\d*"
R_UNIT = r"\d+"
R_DATE = r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})"


class ContaValoresParser():
    """ Parse contabilidad files """

    def __init__(self, file_path, lang=0):
        """ Constructor """
        self._language = lang
        self._path = file_path
        self._list_result = []

    def __str__(self):
        lang_aux = "en" if self._language else "es"
        return "ContaValoresParser: '%s', %s" % (self._path, lang_aux)

    def print_result(self):
        """ Print the current parsing """
        print(pprint.pprint(self._list_result))

    def _read_bic(self, lines, rese):
        """ Receiver BIC code """
        num_line, line = lines.pop(0)
        field_name = "Receiver" if rese == 'R' else 'Sender'
        mtch = re.match(r'\[%s\](%s)' % (rese, R_BIC), line)
        if mtch:
            return {field_name.lower(): mtch.group(1)} 
        else:
            raise ParsingError(3, self._language, num_line, field_name,
                               r"[%s]<bic-code>" % rese)

    def _read_isin_code(self, lines):
        """ Read FIN's isin code """
        num_line, line = lines.pop(0)
        mtch = re.match(r'^\[35B\]\w{12}$', line)
        if mtch:
            pass
        else:
            raise ParsingError(3, self._language, num_line, "ISIN",
                               r'[35B]<alphanum>{12}')

    def _read_quantity(self, lines):
        """ Read holding status """
        num_line, line = lines.pop(0)
        mtch = re.match(r'^\[93B\]([A-Z]{4})/(N)?(%s|\d+)$' % R_DECIMAL, line)
        if mtch:
            pass
        else:
            raise ParsingError(3, self._language, num_line, "Balance",
                               r'[93B]<alpha>{4}>/(N)?<balance>{1,15}')

    def _read_trx(self, lines):
        """ Read Transaction's details """
        num_line, line = lines.pop(0)
        mtch = re.match(r'^\[T\](\d{8})/([A-Z]{4})/(N)?(%s|\d+)/(\w+)(/\w+)?$' % R_DECIMAL, line)
        if mtch:
            pass
        else:
            raise ParsingError(3, self._language, num_line, "Transaction",
                               r"[T]<date YYYYMMDD>/<alpha>{4}>/"
                               "(N)?<balance>{1,15}/<ref-nostro>(/ref-vostro)?")

    def _read_trx_blocks(self, lines):
        """ Read block of transactions """
        while True:
            self._read_trx(lines)
            line = lines[0][1]
            if not re.match(r'\[T\]', line):
                break

    def _is_end_of_msg(self, lines):
        """ Returns True is end-of-message pattern (@@) is found in the current line """
        _, line = lines[0]
        if line == '@@':
            lines.pop(0)
            return True
        else:
            return False

    def _read_blocks_isin(self, lines):
        """ For each FIN, read its holding status and trxs """
        while True:
            self._read_isin_code(lines)
            self._read_quantity(lines)
            self._read_trx_blocks(lines)
            self._read_quantity(lines)
            if self._is_end_of_msg(lines):
                break

    def parse(self):
        """ Run the parser in the specified file and language """

        # open and read file
        with open(self._path, "r") as file:
            # store lines with its line number in a tuple list, remove \n characters
            lines = [(i, line.strip()) for i, line in enumerate(file.readlines(), start=1)
                     if len(line) > 1]

            try:
                while lines != []:
                    result = {}
                    # Read beginning of message symbol ($)
                    num_line, line = lines.pop(0)
                    if line != '$':
                        raise ParsingError(2, self._language, num_line)

                    # Read message type
                    num_line, line = lines.pop(0)
                    mtch = re.match(r'\[M\](\d{3})', line)
                    if mtch:
                        result['message_type'] = mtch.group(1)
                    else:
                        raise ParsingError(3, self._language, num_line, "Message Type",
                                           r"[M]<number>{3}")
                    result.update(self._read_bic(lines, 'S'))
                    result.update(self._read_bic(lines, 'R'))

                    # SEME
                    num_line, line = lines.pop(0)
                    mtch = re.match(r'\[20\](\w+)', line)
                    if mtch:
                        result['seme'] = mtch.group(1)
                    else:
                        raise ParsingError(3, self._language, num_line, "SEME",
                                           r"[S]<alphanum>{1,n}")

                    # Pagination
                    num_line, line = lines.pop(0)
                    mtch = re.match(r'\[28E\](?P<page>\d{1,5})/(?P<indicator>[A-Z]{4})', line)
                    if mtch:
                        pass
                    else:
                        raise ParsingError(3, self._language, num_line, "Pagination",
                                           r"[28E]<number>{1,5}/<alpha>{4}")

                    # Safekeeping Account Code
                    num_line, line = lines.pop(0)
                    mtch = re.match(r'\[97\](\w+)', line)
                    if mtch:
                        result['safe_account'] = mtch.group(1)
                    else:
                        raise ParsingError(3, self._language, num_line, "Safekeeping Account Code",
                                           r"[28E]alphanum{1,n}")

                    self._read_blocks_isin(lines)

                    self._list_result.append(result)

            except ParsingError as parserror:
                self._list_result = parserror.msg
            except IndexError:
                self._list_result = "Error de sintaxis. Fin inesperado del mensaje."




### Main ###
if __name__ == '__main__':
    PARSER = ContaValoresParser("prueba1.txt", 1)
    PARSER.parse()
    PARSER.print_result()
