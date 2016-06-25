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
    4: {
        0: ("Error de sintaxis en linea %s. El subcampo 'Tipo de Cantidad' debe contener "
            "uno de los siguientes valores 'AMOR, FAMT o UNIT'."),
        1: ("Sintax error in line %s. 'Quantity Type Code' field must contain one of the "
            "following values: 'AMOR, FAMT or UNIT'.")
    },
    5: {
        0: ("Error en linea %s. Se esperaba un valor de tipo %s  en este campo."),
        1: ("Type error in line %s. A %s value was expected in this field.")
    },
    6: {
        0: ("Error en la linea %s."
            "El campo fecha debe contener el siguiente formato YYYYMMDD."),
        1: ("Error at line %s."
            "Date Field must contain the format YYYYMMDD.")
    },
   
    7: {
        0: ("Error en la linea %s."
            "Campo Balance con mal formato."),
        1: ("Error at line %s."
            "Balance Field with wrong format.")
    },
    8: {
        0: "Error de sintaxis en linea %s. Se esperaba un campo balance con etiqueta [60F] o [60M].",
        1: "Sintax error in line %s. A Balance Field with tag [60F] or [60M] was expected."
    },
    9: {
        0: "Error de sintaxis en linea %s. Se esperaba un campo balance con etiqueta [62F] o [62M].",
        1: "Sintax error in line %s. A Balance Field with tag [62F] or [62M] was expected."
    },
    11: {
        0: ("Error de validación del mensaje. El balance inicial de la página '%s' no coincide"
            " con el balance final de la página anterior."),
        1: ("Message Validation Error. Initial Balance of page '%s' doesn't match with the "
            "Final Balance of the previous page.")
    },
    12: {
        0: ("Error de validación del mensaje. El balance inicial y final no coincide"
            " con las transacciones de la página '%s'."),
        1: ("Message Validation Error. Initial and final balance don't match with the "
            "transactions movements of the page '%s'.")
    },
}


class ParsingError(Exception):
    """ Parsing Exception Handling Class Definition """
    def __init__(self, code, lang, line, *args):
        Exception.__init__(self)
        self.msg = _ERROR_DICT[code][lang]%((line,)+tuple(args))

### REGEX ###
R_BIC = r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?"
R_DECIMAL = r"\d+,\d{2}"
R_UNIT = r"\d+"
R_DATE = r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})"
R_FCORRECT_DATE = r'\d{2}(0[1-9]|1[0-2])(0[1-9]|[1-2][0-9]|3[0-1])'
R_BALANCE = '^\[(?P<tag>6[02][FM])\](?P<DoC>[DC])(?P<fecha>\d{6})(?P<type>[A-Z]{4})(?P<bal>%s|\d+)$' % R_DECIMAL

def is_correct_date(date):
    """ Verify if a given date is format valid """
    if re.match(R_FCORRECT_DATE, date):
        return True
    return False


class ContaValoresParser():
    """ Parse contabilidad files """

    def __init__(self, file_path, lang=0):
        """ Constructor """
        self._language = lang
        self._path = file_path
        self._pages = []

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
        mtch = re.match(r'^\[35B\](\w{12})$', line)
        if mtch:
            return {'isin': mtch.group(1)}
        else:
            raise ParsingError(3, self._language, num_line, "ISIN",
                               r'[35B]<alphanum>{12}')

    def _read_balance(self, lines):
        """ Read holding status """
        num_line, line = lines.pop(0)
        mtch = re.match(R_BALANCE, line)
        if mtch:
            tag = mtch.group('tag')
            bal_type = mtch.group('type')
            sign = -1 if mtch.group('DoC') == 'D' else 1
            if bal_type == 'UNIT':
                try:
                    bal = int(mtch.group('bal')) * sign
                except ValueError:
                    raise ParsingError(5, self._language, num_line, "integer")
            elif bal_type in ['FAMT', 'AMOR']:
                try:
                    bal = float(mtch.group('bal').replace(',', '.')) * sign
                except ValueError:
                    raise ParsingError(5, self._language, num_line, "float")
            else:
                raise ParsingError(4, self._language, num_line)
            return {'type': bal_type, "bal": bal, "tag": tag}
        else:
            raise ParsingError(7, self._language, num_line)

    def _read_trx(self, lines, bal_type):
        """ Read Transaction's details """
        num_line, line = lines.pop(0)
        pattern = r'^\[61\](?P<fecha>\d{6})(\d{4})?(?P<DoC>[DC])(?P<bal>%s|\d+)(.{4})(?P<refNostro>[^(]+)(\((?P<refVostro>[^(]+)\))?$'
        mtch = re.match(pattern % R_DECIMAL, line)
        if mtch:
            if not is_correct_date(mtch.group('fecha')):
                raise ParsingError(6, self._language, num_line)
            rede = "RECE" if mtch.group('DoC') == 'C' else 'DELI'
            if bal_type == 'UNIT':
                try:
                    bal = int(mtch.group('bal'))
                except ValueError:
                    raise ParsingError(5, self._language, num_line, "integer")

            elif bal_type in ['FAMT', 'AMOR']:
                try:
                    bal = float(mtch.group('bal').replace(',', '.'))
                except ValueError:
                    raise ParsingError(5, self._language, num_line, "float")
            else:
                raise ParsingError(4, self._language, num_line)
            return {'fecha_valor': mtch.group('fecha'), 'rede': rede, 'bal': bal,
                    'ref_nostro': mtch.group('refNostro')}
        else:
            raise ParsingError(3, self._language, num_line, "Transaction",
                               r"[T]<date YYYYMMDD>/<date YYYYMMDD>/<alpha>{4}>/"
                               "(N)?<balance>{1,15}/<ref-nostro>(/ref-vostro)?")

    def _read_trx_blocks(self, lines, bal_type):
        """ Read block of transactions """
        result = []
        while True:
            result.append(self._read_trx(lines, bal_type))
            line = lines[0][1]
            if not re.match(r'\[61\]', line):
                break
        return {'trxs': result}

    @classmethod
    def _is_end_of_msg(cls, lines):
        """ Returns True is end-of-message pattern (@@) is found in the current line """
        _, line = lines[0]
        if line == '@@':
            lines.pop(0)
            return True
        else:
            return False

    def _read_blocks_isin(self, lines):
        """ For each FIN, read its holding status and trxs """
        result_out = []
        while True:
            result_in = {}
            result_in.update(self._read_isin_code(lines))
            result_in.update({"fiop": self._read_quantity(lines)})
            result_in.update(self._read_trx_blocks(lines))
            result_in.update({"ficl": self._read_quantity(lines)})
            result_out.append(result_in)
            if self._is_end_of_msg(lines):
                break
        return result_out

    def _read_account_code(self, lines):
        # Safekeeping Account Code
        num_line, line = lines.pop(0)
        mtch = re.match(r'\[25\](.+)', line)
        if mtch:
            return mtch.group(1)
        else:
            raise ParsingError(3, self._language, num_line, "Account Code",
                               r"[20]alphanum{1,n}")

    def _read_message_type(self, lines):
        # Read message type
        num_line, line = lines.pop(0)
        mtch = re.match(r'\[M\](\d{3})', line)
        if mtch:
            return mtch.group(1)
        else:
            raise ParsingError(3, self._language, num_line, "Message Type",
                               r"[M]<number>{3}")

    def _read_seme(self, lines):
        # SEME
        num_line, line = lines.pop(0)
        mtch = re.match(r'\[20\](.+)', line)
        if mtch:
            return mtch.group(1)
        else:
            raise ParsingError(3, self._language, num_line, "SEME",
                               r"[S]<alphanum>{1,n}")


    def _validate_page(self, page):
        sum_bal = 0
        for trx in page['trxs']:
            bal = trx['bal'] if trx['rede'] == 'RECE' else -trx['bal']
            sum_bal += bal
        sum_trxs = sum([trx['bal'] for trx in page['trxs']])
        fiop = page['balance_ini']['bal']
        ficl = page['balance_fin']['bal']
        try:
            if ("%.2f" % ficl) != ("%.2f" % (fiop + sum_trxs)):
                raise ParsingError(12, self._language, page['pagina'])
        except TypeError:
            if ficl != fiop + sum_trxs:
                raise ParsingError(12, self._language, page['pagina'])

    def _validate_pages(self):
        for page in self._pages:
            if page['pagina'] == '1':
                ficl_prev = page['balance_fin']
            else:
                fiop = page['balance_ini']
                try:
                    if ("%.2f" % ficl_prev) != ("%.2f" % fiop):
                        raise ParsingError(11, self._language, page['pagina'])
                except TypeError:
                    if ficl_prev != fiop:
                        raise ParsingError(11, self._language, page['pagina'])
                ficl_prev = page['balance_fin']




    def parse(self):
        """ Run the parser in the specified file and language """

        # open and read file
        with open(self._path, "r") as file:
            # store lines with its line number in a tuple list, remove \n characters
            lines = [(i, line.strip()) for i, line in enumerate(file.readlines(), start=1)
                     if len(line) > 1]
            success = True
            pages = []
            try:
                while lines != []:
                    page = {}
                    # Read beginning of message symbol ($)
                    num_line, line = lines.pop(0)
                    if line != '$':
                        raise ParsingError(2, self._language, num_line)

                    page['message_type'] = self._read_message_type(lines)
                    page.update(self._read_bic(lines, 'S'))
                    page.update(self._read_bic(lines, 'R'))
                    page['seme'] = self._read_seme(lines)

                    # Read account number
                    page['account_code'] = self._read_account_code(lines)

                    # Statement Number 
                    num_line, line = lines.pop(0)
                    mtch = re.match(r'\[28C\](?P<code>\d+)', line)
                    if mtch:
                        code = mtch.group('code')
                        page['edo_cuenta_codigo'] = code
                    else:
                        raise ParsingError(3, self._language, num_line, "Pagination",
                                           r"[28E]<number>{1,n}")

                    # Pagination
                    num_line, line = lines.pop(0)
                    mtch = re.match(r'^\((?P<page>\d+)\)$', line)
                    if mtch:
                        num_page = mtch.group('page')
                        page['pagina'] = num_page
                    else:
                        raise ParsingError(3, self._language, num_line, "Pagination",
                                           r"[28E]<number>{1,n}")

                    balance_ini = self._read_balance(lines)
                    if balance_ini['tag'] == '60F':
                        page['balance_ini'] = {'bal': balance_ini['bal'],
                                                     'type': balance_ini['type']}
                    elif balance_ini['tag'] == '60M':
                        page['balance_ini'] = {'bal': balance_ini['bal'],
                                                     'type': balance_ini['type']}
                    else:
                         raise ParsingError(8, self._language, num_line)

                    page.update(self._read_trx_blocks(lines, balance_ini['type']))

                    balance_final = self._read_balance(lines)
                    if balance_final['tag'] == '62F':
                        page['balance_fin'] = {'bal': balance_final['bal'],
                                                     'type': balance_final['type']}
                    elif balance_final['tag'] == '62M':
                        page['balance_fin'] = {'bal': balance_final['bal'],
                                                     'type': balance_final['type']}
                    else:
                        raise ParsingError(9, self._language, num_line)

                    if self._is_end_of_msg(lines):
                        self._validate_page(page)
                        self._pages.append(page)


                self._validate_pages()     


            except ParsingError as parserror:
                self._pages = parserror.msg
                success = False
            except IndexError:
                self._pages = "Error de sintaxis. Fin inesperado del mensaje."
                success = False


        return (success, self._pages)


### Main ###
if __name__ == '__main__':
    PARSER = ContaValoresParser("prueba1.txt", 1)
    pprint.pprint(PARSER.parse())
