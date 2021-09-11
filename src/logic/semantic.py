from syntax import *
from typing import overload, List, Dict, Union
from tabulate import tabulate


class Valuation:
	def __init__(self, letters: List[PropositionalLetter], values: List[bool]):
		self.map = dict(zip(letters, values))
		self.hash = eval('bin(0b'+''.join(str(int(i)) for i in values)+')')

	# @overload
	# def __init__(self, valuation: Dict[PropositionalLetter, bool]):
	# 	self.map = valuation

	def __call__(self, alpha: Union[PropositionalLetter, Formula, Tree]):
		if isinstance(alpha, PropositionalLetter):
			return self.map[alpha]
		elif isinstance(alpha, Formula):
			return self(alpha.tree)
		elif isinstance(alpha, Tree):
			root = alpha.nodes[alpha.root]

			def single_tree_to_node(tree):
				if len(tree) == 1:
					return tree.nodes[tree.root].tag
				return tree

			sub_trees = tuple((single_tree_to_node(alpha.subtree(c.identifier)) for c in alpha.children(root.identifier)))
			connector = root.tag

			return_val = None
			if connector.is_binary:
				a, b = sub_trees
				v_a = self(a)
				v_b = self(b)
				if connector.name == 'implies':
					if v_a is True and v_b is False:
						return_val = False
					else:
						return_val = True
				elif connector.name == 'iff':
					if (v_a and v_b) or (not v_a and not v_b):
						return_val = True
					else:
						return_val = False
				elif connector.name == 'and':
					if v_a is True and v_b is True:
						return_val = True
					else:
						return_val = False
				elif connector.name == 'or':
					if v_a is False and v_b is False:
						return_val = False
					else:
						return_val = True
			else:
				a = sub_trees[0]
				v_a = self(a)
				if connector.name == 'negation':
					if v_a is False:
						return_val = True
					else:
						return_val = False
			connector.value[self.hash] = return_val
			return return_val
		else:
			raise Exception('Type not supported')


class TruthTable:
	def __init__(self, formula: Formula):
		self.formula = formula
		self.letters = sorted(list(formula.propositional_letters))

		self.valuations = []
		self._fill_table()

	def _valuation_from_num(self, num):
		b = str(bin(num))[2:]
		values = '0' * (len(self.letters) - len(b)) + b
		values = list(map(lambda x: bool(int(x)), values))
		return Valuation(self.letters, values)

	def _fill_table(self):
		for i in range(2 ** len(self.letters)):
			self.valuations.append(self._valuation_from_num(i))
			self.valuations[i](self.formula)

	def show(self):
		headers = [' '.join(self.letters), ' '.join(self.formula.splitting), 'Value']
		rows = []
		bool_to_str = lambda x: 'V' if x else 'F'
		for i in range(2 ** len(self.letters)):
			v = self.valuations[i]

			row = [' '.join(map(bool_to_str, v.map.values())),
			       ' '.join(map(lambda x: bool_to_str(x.value[bin(i)])
			       if isinstance(x, Connector) else '_', self.formula.splitting)),
			       bool_to_str(self.formula.tree.nodes[self.formula.tree.root].tag.value[bin(i)])]
			rows.append(row)
		print(tabulate(rows, headers=headers, tablefmt='orgtbl'))


if __name__ == '__main__':
	# f = Infix("((p)&((!(r))->(s)))|((p)->(!(!(r))))")
	f = Infix("!(!(!(r)))")
	f = Infix("(p)->((q)->(p))")
	# f = Infix("((!(q))&(!(s)))&(!(r))")
	# f = Infix("((!(p))&(q))->((!((p)|((!(r))&((s)|(!(p))))))<->(s))")
	# f = Polish("CENApKNrAsNpsKNpq")
	f.show_tree()
	print(list(f.propositional_letters))
	# p, q = tuple(f.propositional_letters)

	tv = TruthTable(f)
	tv.show()
