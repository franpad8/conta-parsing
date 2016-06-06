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
        0: "Error código T92 en la linea %s. Este campo debe contener el codigo %s.",
        1: "Error code T92 at line %s. This field must contain the code %s."
    },

    3: {
        0: ("Error código T97 en la linea %s."
            "El Indicador de Continuación debe contener uno de los"
            "siguientes valores: %s."),
        1: ("Error code T97 at line %s."
            "Continuation Indicator must contain one of the"
            "following codes: %s.")
    },
    4: {
        0: ("Error código T89 en la linea %s. "
            "El calificador del campo '%s' debe contener uno de los siguientes valores: %s."),
        1: ("Error code T89 at line %s. "
            "'%s' Field Qualifier must contain one of the"
            "following codes: %s.")
    },
    5: {
        0: ("Error en la linea %s."
            " Código con mal formato."),
        1: ("Error at line %s."
            " Bad format code")
    },

    6: {
        0: ("Error en la linea %s. "
            "El subcampo %s, debe contener uno de los siguientes valores:"
            " %s."),
        1: ("Error at line %s. "
            "Subfield \'%s\', must contain one of the following codes:"
            " %s."),
    },
    7: {
        0: ("Error en la linea %s. "
            "El campo %s, opción %s,  debe contener el siguiente formato:"
            " \'%s\'"),
        1: ("Error at line %s. "
            "%s field, option %s, must contain the following format:"
            " \'%s\'"),
    },

    8: {
        0: ("Error en la linea %s. "
            "En el campo \'%s\', el subcampo \'%s\' debe contener el siguiente formato:"
            " \'%s\'"),
        1: ("Error at line %s. "
            "In \'%s\' field, subfield \'%s\' must contain the following format:"
            " \'%s\'"),
    },

    9: {
        0: ("Error en la linea %s. "
            "En el campo '%s', si el calificador es '%s' y Data Source Scheme no esta presente "
            "entonces el subcampo '%s' debe contener uno de los siguientes valores: %s."),
        1: ("Error at line %s. "
            "In field '%s', If Qualifier is '%s' and Data Source Scheme is not present then "
            "subfield '%s' must contain one of the following codes: %s.")
    },
    10: {
        0: ("Error en la linea %s. "
            "Un campo '%s' con calificador igual a '%s' debe estar presente en este mensaje."),
        1: ("Error code in line %s. "
            " A '%s' field with Qualifier value '%s' is mandatory in this message.")
    },
    11: {
        0: "Error en la linea %s. Este campo solo acepta las siguientes opciones '%s'.",
        1: "Error at line %s. This fields only accepts one of the following options '%s'."
    },
    12: {
        0: ("Error de validación del mensaje. El balance inicial y "
            "final no coincide con las transacciones asociadas al "
            "Intrumento Financiero de ISIN '%s'."),
        1: ("Message Validation Error. Initial and final balance "
            "don't match with the transactions movements of the FIN with ISIN '%s'.")
    },
    13: {
        0: "Error en la linea %s. La cabecera del mensaje no contiene el formato apropiado.",
        1: "Error at line %s. Message's Header doesn't contain the correct format."
    },
    14: {
        0: "Error en la linea %s. El pie de página del mensaje no contiene el formato apropiado.",
        1: "Error at line %s. Message's Footer doesn't contain the correct format."
    }
}


class ParsingError(Exception):
    """ Parsing Exception Handling Class Definition """
    def __init__(self, code, lang, line, **kargs):
        Exception.__init__(self)
        self.msg = _ERROR_DICT[code][lang]%((line,)+tuple(kargs.values()))

### REGEX ###
R_BIC = r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?"
R_DECIMAL = r"\d+,(\d+)"
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

    def parse(self):
        """ Run the parser in the specified file and language """
        with open(self._path, "r") as file:
            lines = file.readlines()
            self._list_result = lines


### Main ###
if __name__ == '__main__':
    PARSER = ContaValoresParser("prueba1.txt", 1)
    PARSER.parse()
    PARSER.print_result()
    