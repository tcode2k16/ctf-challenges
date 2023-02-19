import lark

from interpreter import paths
from interpreter import lterm

grammar = (paths.top / "grammar.lark").read_text()
expr_parser = lark.Lark(grammar, start='expr', parser='lalr')

# print(expr_parser.parse('(λ x. x) y)'))

@lark.v_args(inline=True)
class Transformer(lark.Transformer):
    def var(self, v):
        return lterm.Var(v.value)

    def apply(self, a, b):
        return lterm.Apply(a, b)

    def mlambda(self, vars, e):
        res = e
        for v in reversed(vars.children):
            res = lterm.Lambda(v.value, res)
        return res

transformer = Transformer()

def parse_expr(expr):
    return transformer.transform(expr_parser.parse(expr))