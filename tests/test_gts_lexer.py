import unittest

from gts.gts_lexer import GTSLexer

class TestGTSLexer(unittest.TestCase):
	def setUp(self):
		self.lexer = GTSLexer()	

	# test lexer peek mechanism
	
	def test_lexer_peek(self):
		self.lexer.input("(M:A)3")

		self.assertEqual(self.lexer.peek().type, "LPAREN")
		self.assertEqual(self.lexer.peek().type, "LPAREN")
		self.assertEqual(self.lexer.peek().type, "LPAREN")

		self.assertEqual(self.lexer.peek(2).type, "COLON")
		self.assertEqual(self.lexer.peek(1).type, "IDENTIFIER")
		self.assertEqual(self.lexer.peek(0).type, "LPAREN")

		self.assertEqual(self.lexer.token().type, "LPAREN")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "COLON")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "RPAREN")

		self.assertIsNone(self.lexer.peek(20))

		self.assertEqual(self.lexer.token().type, "DIGITS")

		for i in range(30):
			self.assertIsNone(self.lexer.token())

	# test individual tokens

	def test_lexer_PRECONDITION_P(self):
		self.lexer.input("P(M)")
		self.assertEqual(self.lexer.token().type, "PRECONDITION_P")
		self.assertEqual(self.lexer.token().type, "LPAREN")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "RPAREN")
		self.assertIsNone(self.lexer.token())

	def test_lexer_LPAREN(self):
		self.lexer.input("(")
		self.assertEqual(self.lexer.token().type, "LPAREN")
		self.assertIsNone(self.lexer.token())

	def test_lexer_RPAREN(self):
		self.lexer.input(")")
		self.assertEqual(self.lexer.token().type, "RPAREN")
		self.assertIsNone(self.lexer.token())

	def test_lexer_LBRACKET(self):
		self.lexer.input("[")
		self.assertEqual(self.lexer.token().type, "LBRACKET")
		self.assertIsNone(self.lexer.token())

	def test_lexer_RBRACKET(self):
		self.lexer.input("]")
		self.assertEqual(self.lexer.token().type, "RBRACKET")
		self.assertIsNone(self.lexer.token())

	def test_lexer_DIGITS(self):
		self.lexer.input("1 12 123 1234 1 2 3 4 5 6 7 8 9 0 1234567890 0123456789")
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 1)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 12)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 123)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 1234)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 1)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 2)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 3)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 4)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 5)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 6)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 7)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 8)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 9)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 0)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 1234567890)
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 123456789)
		self.assertIsNone(self.lexer.token())

	def test_lexer_COMMA(self):
		self.lexer.input(",")
		self.assertEqual(self.lexer.token().type, "COMMA")
		self.assertIsNone(self.lexer.token())

	def test_lexer_IDENTIFIER(self):
		self.lexer.input("foo Foo FOO f1 foo1 fOO1 foo123bar 1foo")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		
		# 1foo
		self.assertEqual(self.lexer.token().type, "DIGITS")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		
		self.assertIsNone(self.lexer.token())

	def test_lexer_WILDCARD_HASH(self):
		self.lexer.input("#")
		self.assertEqual(self.lexer.token().type, "WILDCARD_HASH")
		self.assertIsNone(self.lexer.token())

	def test_lexer_SHUFFLE_EXCL(self):
		self.lexer.input("!")
		self.assertEqual(self.lexer.token().type, "SHUFFLE_EXCL")
		self.assertIsNone(self.lexer.token())

	def test_lexer_SUBSET_S(self):
		self.lexer.input("S")
		self.assertEqual(self.lexer.token().type, "SUBSET_S")
		self.assertIsNone(self.lexer.token())

	def test_lexer_COLON(self):
		self.lexer.input(":")
		self.assertEqual(self.lexer.token().type, "COLON")
		self.assertIsNone(self.lexer.token())

	def test_lexer_LANGLE(self):
		self.lexer.input("<")
		self.assertEqual(self.lexer.token().type, "LANGLE")
		self.assertIsNone(self.lexer.token())

	def test_lexer_RANGLE(self):
		self.lexer.input(">")
		self.assertEqual(self.lexer.token().type, "RANGLE")
		self.assertIsNone(self.lexer.token())

	def test_lexer_FUZZ_OFFSET_AT(self):
		self.lexer.input("@")
		self.assertEqual(self.lexer.token().type, "FUZZ_OFFSET_AT")
		self.assertIsNone(self.lexer.token())

	def test_lexer_FUZZ_CL_DOLLAR(self):
		self.lexer.input("$")
		self.assertEqual(self.lexer.token().type, "FUZZ_CL_DOLLAR")
		self.assertIsNone(self.lexer.token())

	def test_lexer_REPETITION_PIPE(self):
		self.lexer.input("|")
		self.assertEqual(self.lexer.token().type, "REPETITION_PIPE")
		self.assertIsNone(self.lexer.token())

	def test_lexer_UNDERSCORE(self):
		self.lexer.input("_")
		self.assertEqual(self.lexer.token().type, "UNDERSCORE")
		self.assertIsNone(self.lexer.token())

	def test_lexer_EQUALS(self):
		self.lexer.input("=")
		self.assertEqual(self.lexer.token().type, "EQUALS")
		self.assertIsNone(self.lexer.token())

	def test_lexer_ARITHMETIC_OPERATOR(self):
		self.lexer.input("+")
		self.assertEqual(self.lexer.token().type, "PLUS")
		self.assertIsNone(self.lexer.token())

	def test_lexer_MINUS(self):
		self.lexer.input("-")
		self.assertEqual(self.lexer.token().type, "MINUS")
		self.assertIsNone(self.lexer.token())

	# test some more complex patterns

	def test_lexer_loop_1(self):
		self.lexer.input("[M]3")
		self.assertEqual(self.lexer.token().type, "LBRACKET")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "RBRACKET")
		self.assertEqual(self.lexer.token().type, "DIGITS")
		self.assertIsNone(self.lexer.token(), None)

	def test_lexer_loop_2(self):
		self.lexer.input("[M]300")
		self.assertEqual(self.lexer.token().type, "LBRACKET")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "RBRACKET")
		self.assertEqual(self.lexer.token().type, "DIGITS")
		self.assertIsNone(self.lexer.token(), None)

	def test_lexer_loop_3(self):
		self.lexer.input("[M_s=1,t=i]20,2,i")
		self.assertEqual(self.lexer.token().type, "LBRACKET")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "UNDERSCORE")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "EQUALS")
		self.assertEqual(self.lexer.token().type, "DIGITS")
		self.assertEqual(self.lexer.token().type, "COMMA")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "EQUALS")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "RBRACKET")
		self.assertEqual(self.lexer.token().type, "DIGITS")
		self.assertEqual(self.lexer.token().type, "COMMA")
		self.assertEqual(self.lexer.token().type, "DIGITS")
		self.assertEqual(self.lexer.token().type, "COMMA")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertIsNone(self.lexer.token(), None)

	def test_lexer_wildcard(self):
		self.lexer.input("#3")
		self.assertEqual(self.lexer.token().type, "WILDCARD_HASH")
		self.assertEqual(self.lexer.token().type, "DIGITS")
		self.assertIsNone(self.lexer.token())

	def test_lexer_shuffle(self):
		self.lexer.input("(M)!")
		self.assertEqual(self.lexer.token().type, "LPAREN")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "RPAREN")
		self.assertEqual(self.lexer.token().type, "SHUFFLE_EXCL")
		self.assertIsNone(self.lexer.token())

	def test_lexer_subset(self):
		self.lexer.input("(M)S")
		self.assertEqual(self.lexer.token().type, "LPAREN")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "RPAREN")
		self.assertEqual(self.lexer.token().type, "SUBSET_S")
		self.assertIsNone(self.lexer.token())

	def test_lexer_slide(self):
		self.lexer.input("(M)13")
		self.assertEqual(self.lexer.token().type, "LPAREN")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "RPAREN")
		tok = self.lexer.token()
		self.assertEqual(tok.type, "DIGITS")
		self.assertEqual(tok.value, 13)
		self.assertIsNone(self.lexer.token())

	def test_lexer_merge(self):
		self.lexer.input("(M:M)+")
		self.assertEqual(self.lexer.token().type, "LPAREN")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")
		self.assertEqual(self.lexer.token().type, "COLON")
		self.assertEqual(self.lexer.token().type, "IDENTIFIER")		
		self.assertEqual(self.lexer.token().type, "RPAREN")
		self.assertEqual(self.lexer.token().type, "PLUS")
		self.assertIsNone(self.lexer.token())
