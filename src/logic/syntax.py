from typing import List, Optional, overload
from treelib import Node, Tree
from copy import deepcopy


class NotWellFormedException(BaseException):
	def __init__(self):
		super().__init__('The provided string is not a well formed formula.')


class Connector(str):
	def __new__(cls, *args, **kw):
		if 'symbol' in kw.keys():			
			return str.__new__(cls, kw['symbol'])
		else:
			return str.__new__(cls, args[0])

	def __init__(self, symbol: str, is_binary: bool, name: str = ''):
		super().__init__()
		self.is_binary = is_binary
		self.name = name
		self.value = {}


class PropositionalLetter(str):
	def __new__(cls: str, *args, **kw):
		return str.__new__(cls, *args, **kw)

	def __init__(self, symbol: str, value: Optional[bool] = None):
		super().__init__()
		self.value = value


class Alphabet:
	connectors = dict()
	letters = {chr(i): PropositionalLetter(chr(i)) for i in range(97, 123)}
	parenthesis = {'(', ')'}

	def __init__(self, connectors: List[Connector], bin_wildcard='@'):
		self.connectors = {str(c): c for c in connectors}
		self.connectors_by_name = {c.name: c for c in connectors}
		self.bin_wildcard = bin_wildcard

	def __contains__(self, element):
		return any([
			element in self.connectors,
			element in self.letters,
			element in self.parenthesis])


class Formula(str):
	def __new__(cls, *args, **kw):
		if 's_formula' in kw.keys():
			return str.__new__(cls, kw['s_formula'])
		else:
			return str.__new__(cls, args[0])

	def __init__(self, s_formula: str, alphabet: Alphabet, build_tree: bool = True):
		super().__init__()
		self.base_tree = build_tree
		self.alphabet = alphabet
		self.length, self.splitting, self.propositional_letters = self._split()
		if self.check(s_formula):
			if build_tree:
				self.tree = self.build_tree()
				self._tree_order()
			self.value = None
		else: 
			raise Exception('You need to provide a well formed formula.')

	def _split(self):
		string = self.replace(' ', '')
		length = 0
		splitting = []
		prop_letters = set()
		i = 0
		j = i + 1
		while i < len(string):
			add = False
			symbol = string[i: j]

			if symbol in self.alphabet.parenthesis:
				add = True
			elif symbol in self.alphabet.letters:
				add = True
				symbol = self.alphabet.letters[symbol]
				prop_letters.add(symbol)
			elif symbol in self.alphabet.connectors:
				add = True
				symbol = deepcopy(self.alphabet.connectors[symbol])

			if add:
				length += 1
				splitting.append(symbol)
				i = j
				j = i + 1
			elif j + 1 > len(string):
				raise Exception('You need to provide a well formed formula.')
			else:
				j += 1
		return length, splitting, prop_letters

	def check(self, s_formula):
		...

	def build_tree(self):
		...

	def _tree_order(self):
		self.tree.nodes[self.tree.root].data = {"order": 0}
		for n in self.tree.nodes:
			for i, son in enumerate(self.tree.children(n)):
				son.data = {"order": i}

	def show_tree(self):
		self.tree.show(key=lambda x: -x.data["order"])


class Infix(Formula):
	def __init__(self, s_formula: str, build_tree: bool = True):
		infix_alphabet = Alphabet([
			Connector("->", True, 'implies'),
			Connector('<->', True, 'iff'),
			Connector('&', True, 'and'),
			Connector('|', True, 'or'),
			Connector('!', False, 'negation'),
			])
		super().__init__(s_formula, infix_alphabet, build_tree)

	def check(self, s_formula):
		# Algorithm from sec 1.6 from [1]_
		neg = self.alphabet.connectors_by_name['negation']
		bin = self.alphabet.bin_wildcard
		new_splitting = ''.join('0' if isinstance(s, PropositionalLetter) else
		                 s if not isinstance(s, Connector) else
		                 "@" if s.is_binary else
		                 s for s in self.splitting)

		def reduce_negs(formula):
			new = formula.replace(f'{neg}(0)', '0')
			if len(new) < len(formula):
				return new
			else:
				return False

		def reduce_bins(formula):
			new = formula.replace(f'(0){bin}(0)', '0')
			if len(new) < len(formula):
				return new
			else:
				return False

		while True:
			op1 = reduce_negs(new_splitting)
			if op1:
				new_splitting = op1

			op2 = reduce_bins(new_splitting)
			if op2:
				new_splitting = op2
			if new_splitting == '0':
				return True
			elif not op1 and not op2:
				break

		return False

	def sub_formulas(self):
		if self.splitting[0] in self.alphabet.connectors:
			if self.splitting[0] == self.alphabet.connectors_by_name['negation']:
				# The first element is a negation
				c1 = Infix(''.join(self.splitting[2:-1]), False)
				c1.splitting = self.splitting[2:-1]
				c1.tree = c1.build_tree()
				c1._tree_order()

				return self.splitting[0], [c1]
				# return 0
		elif self.splitting[0] == '(':
			count = 0
			index = 0
			for i in self.splitting:
				if i == "(":
					count += 1
				elif i == ")":
					count -= 1
				if count == 0:
					break
				index += 1
			c1 = Infix(''.join(self.splitting[1:index]), build_tree=False)
			c1.splitting = self.splitting[1:index]
			c1.tree = c1.build_tree()
			c1._tree_order()
			c2 = Infix(''.join(self.splitting[index + 3:-1]), build_tree=False)
			c2.splitting = self.splitting[index + 3:-1]
			c2.tree = c2.build_tree()
			c2._tree_order()
			return self.splitting[index + 1], [c1, c2]
		else:
			return self.splitting[0], None
			# return 0

	def build_tree(self):
		principal, subformulas = self.sub_formulas()
		t = Tree()
		node = Node(principal)
		t.add_node(node)
		if subformulas is not None:
			for f in subformulas:
				t.paste(node.identifier, f.tree)
			return t
		else:
			return t


class Polish(Formula):

	def __init__(self, s_formula: str):
		infix_alphabet = Alphabet([
			Connector("C", True, 'implies'),
			Connector('E', True, 'iff'),
			Connector('K', True, 'and'),
			Connector('A', True, 'or'),
			Connector('N', False, 'negation'),
			])
		super().__init__(s_formula, infix_alphabet)

	def check(self, s_formula):
		"""Checks if a formula is a well formed Polish formula."""
		count = []
		next_subtract = []

		def get_next_subtract():
			if len(next_subtract) == 0:
				raise NotWellFormedException()
			else:
				i = next_subtract[-1]
				if count[i] == 1:
					next_subtract.pop(-1)
				return i

		for i, s in enumerate(self.splitting):
			if isinstance(s, PropositionalLetter):
				count.append(0)
				count[get_next_subtract()] -= 1
			elif s.is_binary:
				count.append(2)
				if i > 0:
					count[get_next_subtract()] -= 1
				next_subtract.append(i)
			else:
				count.append(1)
				if i > 0:
					count[get_next_subtract()] -= 1
				next_subtract.append(i)

		if sum(count) == 0:
			return True
		else:
			return False

	def build_tree(self):
		t = Tree()
		next_parent = []

		def get_next_parent():
			if len(next_parent) == 0:
				return None

			i = next_parent[-1]
			num_sons = 2 if i.tag.is_binary else 1
			if len(t.children(i.identifier)) == num_sons - 1:
				next_parent.pop(-1)
			return i.identifier

		for s in self.splitting:
			node = Node(s)
			t.add_node(node, parent=get_next_parent())
			if not isinstance(s, PropositionalLetter):
				next_parent.append(node)
		return t


if __name__ == '__main__':
	# f = Infix("((p)&((!(r))->(s)))|((p)->(!(!(r))))")
	f = Infix("((!(p))&(q))->((!((p)|((!(r))&((s)|(!(p))))))<->(s))")
	# f = Polish("CENApKNrAsNpsKNpq")

	# f.show_tree()
	# print(help(f.tree.show)
	# f.tree.show(reverse=False)
	# print(f.propositional_letters)
	# f = Infix('(p)->(q)')
	f.show_tree()
