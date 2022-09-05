def format_str(s: str) -> str:
	result: str = ""
	indent: int = 0
	i = 0
	while i < len(s):
		char = s[i]
		if char == "[":
			result += char
			if s[i+1] != "]":
				indent += 1
				result += "\n" + indent * "\t"
		elif char == "]":
			if s[i-1] != "[":
				indent -= 1
				result += "\n" + indent * "\t"
			result += char
		elif char == ",":
			result += char
			if (s[i-1] == "]" and s[i+2] == "[") or (s[i-1] == ")" and s[i+2] == "(") or s[i+2] == "D":
				result += "\n" + indent * "\t"
			if s[i+1] == " ":
				i += 1
		else:
			result += char
		i += 1
	return result
