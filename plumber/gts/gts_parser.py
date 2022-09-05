from __future__ import annotations

from ply.lex import LexToken

from typing import List, Dict, TYPE_CHECKING
if TYPE_CHECKING:
	from .ast_operators import Operator
	from .ast_directives import DirectiveAttributeValueParts, Directive

from .gts_lexer import GTSLexer
from .ast_directives import ArithmeticOperator, DirectiveMemory, DirectiveNop, DirectiveBranch, DirectiveArithmetic, DirectiveStoreConditionOperand
from .ast_operators import OperatorLoop, OperatorFuzz, OperatorSlide, OperatorSubset, OperatorShuffle, OperatorWildcard, OperatorMerge, OperatorRepetition
from .ast_containers import GTS, Expression

class GTSParser:
	"""
	This class describes the Parser for the string representation of a GTS.
	"""

	def __init__(self) -> None:
		self.lexer: GTSLexer = GTSLexer()
	
	def input(self, gts: str) -> None:
		"""
		Feeds the given input string into the lexer

		:param      gts:  The string representation of a GTS
		:type       gts:  str

		:returns:   { description_of_the_return_value }
		:rtype:     None
		"""
		self.lexer.input(gts)

	def parse(self) -> GTS:
		"""
		Parses the current input that was given to the lexer via `input()`
		
		:returns:   Internal representation of the GTS, in particular, a
		            reference to the root node of the AST after parsing the
		            whole input string
		:rtype:     GTS
		
		:raises     SyntaxError:  Exception raised if syntax error is detected
		"""
		
		# shortcut for the lexer, we will use it a lot
		lex = self.lexer
		
		# The following functions more or less correspond to non-terminals
		# of the grammar. The outer function should only call parse_gts()
		# to start the parsing process.

		def parse_gts() -> GTS:
			# create empty root node for the AST
			gts = GTS()
			
			# check for optional precondition and parse it, if present
			if lex.peek_assert("PRECONDITION_P"):
				gts.precondition = parse_precondition()
			
			# parse top-level expression
			gts.expression = parse_expression()

			# expect that there are no remaining tokens
			if lex.peek() is not None:
				lex.error(error="Unexpected token. Remaining tokens could not be parsed")
			
			return gts
		
		def parse_precondition() -> Expression:
			error = "Invalid precondition"
			lex.token_or_error("PRECONDITION_P", error=error)
			lex.token_or_error("LPAREN", error=error)
			precondition_expression = parse_expression()
			lex.token_or_error("RPAREN", error=error)
			return precondition_expression

		def parse_expression() -> Expression:
			expression = Expression()
			# Parse any number of directives and operators.
			# All directives start with an identifier, operators start with
			# certain special characters.
			while True:
				tok = lex.peek()
				if tok is None:
					break
				elif tok.type == "IDENTIFIER":
					directive = parse_directive()
					expression.append_child(directive)
				elif peek_looks_like_start_of_operator():
					operator = parse_operator()
					expression.append_child(operator)
				else:
					break
			return expression

		def parse_directive() -> Directive:
			# all directives start with a mandatory identifier: A, B, M, or N,
			# some of them followed by further attributes
			tok = lex.token_or_error("IDENTIFIER")
			if tok.value == "A":
				return DirectiveArithmetic(parse_directive_attributes())
			elif tok.value == "B":
				return DirectiveBranch(parse_directive_attributes())
			elif tok.value == "S":
				return DirectiveStoreConditionOperand(parse_directive_attributes())
			elif tok.value == "M":
				return DirectiveMemory(parse_directive_attributes())
			elif tok.value == "N":
				return DirectiveNop()
			else:
				lex.error(tok, error="Token is not a valid directive identifier")
			
		def parse_directive_attributes() -> Dict[str, DirectiveAttributeValueParts]:
			result: Dict[str, DirectiveAttributeValueParts] = dict()
			if lex.peek_assert("UNDERSCORE"):
				lex.token() # skip UNDERSCORE
				# keep parsing comma separated attributes
				while True:
					tok_name: LexToken = lex.token_or_error("IDENTIFIER")
					name = tok_name.value
					if name in result:
						lex.error(error=f"Attribute {name} was defined multiple times.")
					lex.token_or_error("EQUALS")
					value_parts: DirectiveAttributeValueParts = parse_directive_attribute_value()
					if len(value_parts) == 0:
						lex.error(error="Invald attribute: no value given.")
					result[name] = value_parts
					if (lex.peek_assert("COMMA")):
						lex.token() # skip COMMA
					else:
						break
			return result

		def parse_directive_attribute_value() -> DirectiveAttributeValueParts:
			# first token is always digits_or_identifier
			toks_value: List[LexToken] = [parse_digits_or_identifier()]
			# parse optional arithmetic expression after the first attribute value token
			while lex.peek_assert("PLUS") or lex.peek_assert("MINUS"):
				toks_value.append(lex.token_not_none()) # PLUS or MINUS
				toks_value.append(parse_digits_or_identifier())
			return process_attribute_value_tokens(toks_value)

		def process_attribute_value_tokens(toks_value: List[LexToken]) -> DirectiveAttributeValueParts:
			value_parts: DirectiveAttributeValueParts = []
			for tok in toks_value:
				if tok.type in ["IDENTIFIER", "DIGITS"]:
					value_parts.append((tok.type, tok.value))
				elif tok.type in ["PLUS", "MINUS"]:
					op = ArithmeticOperator.from_str(tok.value)
					assert op is not None
					value_parts.append((tok.type, op))
			return value_parts

		def parse_digits_or_identifier() -> LexToken:
			tok = lex.token_not_none()
			if tok.type == "IDENTIFIER":
				return tok
			elif tok.type == "DIGITS":
				return tok
			else:
				lex.error(tok, error="Expected identifier or digits")

		def peek_looks_like_start_of_operator() -> bool:
			tok0 = lex.peek()
			if tok0 is None:
				return False
			elif tok0.type in ["LBRACKET", "WILDCARD_HASH", "LPAREN", "LANGLE"]:
				return True
			elif tok0.type == "REPETITION_PIPE":
				# Repetition uses the same character at the beginning
				# and at the end (pipe). Therefore, we need to distinguish
				# beginning and end based on the next token: it's the end
				# if the following token is of type DIGITS.
				tok1 = lex.peek(1)
				if tok1 is not None and tok1.type == "DIGITS":
					return False
				else:
					return True
			else:
				return False

		def parse_operator() -> Operator:
			tok = lex.peek_not_none()
			if tok.type == "LBRACKET": # loop
				lex.token() # skip LBRACKET
				expression = parse_expression()
				lex.token_or_error("RBRACKET")
				tok_end = lex.token_or_error("DIGITS")
				if lex.peek_assert("COMMA"):
					lex.token() # skip COMMA
					tok_step = lex.token_or_error("DIGITS")
					lex.token_or_error("COMMA")
					tok_loopvar = lex.token_or_error("IDENTIFIER")
					return OperatorLoop(
						expression=expression,
						end=tok_end.value,
						step=tok_step.value,
						loopvar=tok_loopvar.value
					)
				else:
					return OperatorLoop(
						expression=expression,
						end=tok_end.value
					)

			elif tok.type == "WILDCARD_HASH": # wildcard
				lex.token() # skip WILDCARD_HASH
				tok_digits = lex.token_or_error("DIGITS", error="Invalid token after #")
				return OperatorWildcard(tok_digits.value)

			elif tok.type == "LPAREN": # shuffle/subset/slide/merge
				lex.token() # skip LPAREN
				expression1 = parse_expression()
				
				# merge has two expressions, divided by COLON,
				# for all other cases expect RPAREN
				expression2 = None
				if lex.peek_assert("COLON"):
					lex.token() # skip COLON
					expression2 = parse_expression()

				lex.token_or_error("RPAREN")
				
				# now it depends on the token after the closing parenthesis
				# which operator it actually is
				operator_specifier = lex.token_not_none()
				if operator_specifier.type == "SHUFFLE_EXCL": # shuffle
					return OperatorShuffle(expression1)

				elif operator_specifier.type == "IDENTIFIER" and operator_specifier.value == "S": # subset
					return OperatorSubset(expression1)

				elif operator_specifier.type == "DIGITS": # slide
					return OperatorSlide(expression1, operator_specifier.value)

				elif operator_specifier.type == "PLUS": # merge
					if expression2 is None:
						lex.error(error="Merge operator needs two expressions, only one found")
					return OperatorMerge(expression1, expression2)

				else:
					lex.error(operator_specifier, error="Invalid operator specifier")

			elif tok.type == "LANGLE": # fuzz
				lex.token() # skip LANGLE
				expression = parse_expression()
				lex.token_or_error("RANGLE")
				
				tok_fuzz_type = lex.token_not_none()
				if tok_fuzz_type.type == "FUZZ_OFFSET_AT" or tok_fuzz_type.type == "FUZZ_CL_DOLLAR":
					return OperatorFuzz(expression, tok_fuzz_type.type)
				else:
					lex.error(tok_fuzz_type, "Invalid fuzz type specifier")

			elif tok.type == "REPETITION_PIPE": # repetition
				lex.token() # skip REPETITION_PIPE
				expression = parse_expression()
				lex.token_or_error("REPETITION_PIPE")
				tok_n = lex.token_or_error("DIGITS")
				return OperatorRepetition(expression, tok_n.value)

			else:
				lex.error(error="This token is not a valid beginning of an operator")

		return parse_gts()