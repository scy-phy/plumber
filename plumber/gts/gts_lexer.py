from __future__ import annotations

from collections import deque
from typing import Optional, NoReturn, Deque

from ply.lex import lex, LexToken

class GTSLexer:
	"""
	This class is a wrapper around ply.lex that adds peeking and some
	additional convenience functions for our own parser (see GTSParser).
	This class describes a Lexer for the string representation of a GTS. An
	instance of this class will be created within the GTSParser. There is
	no need to use this class from outside GTSParser.
	"""
	def __init__(self) -> None:
		self.token_buffer: Deque[LexToken] = deque()
		self.__init_lexer()

	def __init_lexer(self) -> None:
		"""
		Initializes the lexer: defines tokens and assigns them regex
		patterns.
		
		:returns:   -
		:rtype:     None
		"""
		# List of tokens
		tokens = (
			"PRECONDITION_P", "LPAREN", "RPAREN", "LBRACKET", "RBRACKET",
			"DIGITS", "COMMA", "IDENTIFIER", "WILDCARD_HASH", "SHUFFLE_EXCL",
			"COLON", "LANGLE", "RANGLE", "FUZZ_OFFSET_AT",
			"FUZZ_CL_DOLLAR", "REPETITION_PIPE", "UNDERSCORE", "EQUALS",
			"PLUS", "MINUS"
		)

		# List of ignored characters
		t_ignore = " \t"

		# Token matching rules
		# note: patterns defined as functions have higher priority than
		# patterns defined as variables. Therefore, define specify patterns
		# for reserved identifiers using functions.
		t_LPAREN = r'\('
		t_RPAREN = r'\)'
		t_LBRACKET = r'\['
		t_RBRACKET = r'\]'
		t_COMMA = r','
		t_IDENTIFIER = r'[A-Za-z][A-Za-z0-9]*'
		t_WILDCARD_HASH = r'\#'
		t_SHUFFLE_EXCL = r'!'
		t_COLON = r':'
		t_LANGLE = r'<'
		t_RANGLE = r'>'
		t_FUZZ_OFFSET_AT = r'@'
		t_FUZZ_CL_DOLLAR = r'\$'
		t_REPETITION_PIPE = r'\|'
		t_UNDERSCORE = r'_'
		t_EQUALS = r'='
		t_PLUS = r'\+'
		t_MINUS = r'-'
		def t_DIGITS(t):
			r'\d+'
			t.value = int(t.value)
			return t
		def t_PRECONDITION_P(t):
			r'P'
			return t
		
		# Error handler for illegal characters
		def t_error(t):
			self.error(token=t, error="Illegal character")

		# Build the lexer object
		self.lexer = lex()

	def input(self, gts: str) -> None:
		"""
		Takes the string representation of a GTS and passes it on to the
		PLY lexer for tokenization
		
		:param      gts:  The string representation of a GTS
		:type       gts:  str
		
		:returns:   -
		:rtype:     None
		"""
		self.lexer.input(gts)


	def peek(self, n: int = 0) -> Optional[LexToken]:
		"""
		Returns a token without removing it from the lexer's queue. This
		allows to 'peek' into the queue of upcoming tokens without the need
		of buffering potentially unwanted tokens in the parser code. peek()
		or peek(0) returns the very next token, peek(1) the token after
		that, etc. To implement this, this function pulls the tokens from
		the ply.lex and buffers them in a deque.
		
		:param      n:    number of tokens to look ahead (0-based)
		:type       n:    int
		
		:returns:   The token at the specified position in the lexer's
		            queue, or None if there are less than n+1 tokens left
		:rtype:     LexToken or None
		"""

		if len(self.token_buffer) > n:
			return self.token_buffer[n]
		else:
			for i in range(n - len(self.token_buffer) + 1):
				self.token_buffer.append(self.lexer.token())
			return self.token_buffer[-1]

	def peek_not_none(self, n: int = 0) -> LexToken:
		"""
		Same as peek(), but raises a SyntaxError exception in case there
		are less than (n+1) tokens left instead of returning None.
		
		:param      n:    number of tokens to look ahead (0-based)
		:type       n:    int
		
		:returns:   The token at the specified position in the lexer's
		            queue
		:rtype:     LexToken
		"""
		tok = self.peek(n)
		if tok is None:
			self.error(error="Unexpected end of input")
		assert tok is not None
		return tok

	def peek_assert(self, expected_type: str, expected_value: Optional[str] = None, n: int = 0) -> bool:
		"""
		Returns whether an upcoming token matches the given parameters.
		
		:param      expected_type:   The expected token type
		:type       expected_type:   str
		:param      expected_value:  The expected token value
		:type       expected_value:  str or None
		:param      n:               number of tokens to look ahead
		                             (0-based)
		:type       n:               int
		
		:returns:   True if the indicated token matches the given
		            parameters, False otherwise.
		:rtype:     bool
		"""
		tok = self.peek(n)
		if tok is not None and tok.type == expected_type and (expected_value is None or tok.value == expected_value):
			return True
		return False

	def token(self) -> Optional[LexToken]:
		"""
		Returns the next token and removes it from the lexer's queue.
		
		:returns:   Next token, or None if the end of input is reached.
		:rtype:     LexToken or None
		"""
		if len(self.token_buffer) > 0:
			return self.token_buffer.popleft()
		else:
			return self.lexer.token()

	def token_not_none(self) -> LexToken:
		"""
		Returns the next token and removes it from the lexer's queue.
		
		:returns:   Next token. If there is no next token (end of input is
		            reached), a SyntaxError exception is raised.
		:rtype:     LexToken
		"""
		tok = self.token()
		if tok is None:
			self.error(error="Unexpected end of input")
		assert tok is not None
		return tok

	def token_or_error(self, expected_type: str, expected_value: Optional[str] = None, error: Optional[str] = None) -> LexToken:
		"""
		Returns the next token if it matches the given parameters,
		otherwise, a SyntaxError exception is raised.
		
		:param      expected_type:   The expected token type
		:type       expected_type:   str
		:param      expected_value:  The expected token value
		:type       expected_value:  str or None
		:param      error:           The error message to print in case of
		                             mismatch
		:type       error:           str or None
		
		:returns:   Next token if it matches the given parameters.
		            Otherwise, a SyntaxError exception is raised.
		:rtype:     LexToken
		"""
		tok = self.token()
		if tok is not None and tok.type == expected_type and (expected_value is None or expected_value == tok.value):
			return tok
		else:
			self.error(tok, expected_type, expected_value, error)

	def error(self, token: Optional[LexToken] = None, expected_type: Optional[str] = None, expected_value: Optional[str] = None, error: Optional[str] = None) -> NoReturn:
		"""
		Helper function to raise a SyntaxError exception with a meaningful
		error message.
		
		:param      token:           The token that causes the error
		:type       token:           LexToken
		:param      expected_type:   If another token type was expected, specify it here.
		:type       expected_type:   str or None
		:param      expected_value:  If another value was expected, specify it here.
		:type       expected_value:  str or None
		:param      error:           The error message
		:type       error:           str or None
		
		:returns:   -
		:rtype:     None
		
		:raises     SyntaxError:     Syntax Error exception.
		"""
		# assemble error message
		if token is None:
			token = self.peek()
		error_msg = ""
		if expected_type is not None:
			error_msg += f"Expected token of type {expected_type}"
			if expected_value is not None:
				error_msg += f" and value {expected_value}"
			error_msg += ". "
		error_msg += f"Got token: {token}."
		if error is not None:
			error_msg += f" {error}."
		raise SyntaxError(error_msg)