#!/usr/local/bin/python3

import random

from interpreter import parse
from interpreter import lterm
from interpreter.lterm import Var, Lambda, Apply
from solver import solve, p, post_process

# print(parse.expr_parser.parse('(λx.λy.(x y) y)'))
# print('---')
# # print(parse.parse_expr('(λx.λy.(x y) y) (λx.x)').reduce_once({}))
# print(parse.parse_expr('(λx y.x) a b').reduce_once({}))

# print(parse.parse_expr('(λx a.x a) a b').reduce_once({}))



def reduce(expr, symbols={}):
  while True:
    print("    ", expr)
    next = expr.reduce_once(symbols)
    if next is None:
      return expr
    expr = next

print('---\n\n\n')

# solve(p(qs), p(qt))

def test(qs, qt):
  print('--- test case ---')
  print(f'{str(p(qs))=}')
  print(f'{str(p(qt))=}')
  S_LBL = '(true)'
  T_LBL = '(false)'
  ctx, solution, constraints = solve(p(qs), p(qt), S_LBL=S_LBL, T_LBL=T_LBL)
  print(f'{ctx=}')
  solution = post_process(ctx, solution, constraints)
  print(f'{solution=}')
  print(f'{ctx=}')

  r1 = reduce(p(' '.join([f'({qs})']+solution)))
  print(r1)

  r2 = reduce(p(' '.join([f'({qt})']+solution)))
  print(r2)
  assert(r1 == Var('true'))
  assert(r2 == Var('false'))
  print('-----------------\n\n\n')

test('(λx y z. x y)', '(λx y z. x)')
test('(λx y z. x y z q)', '(λx y z. x y)')

test('(λx y z. x)', '(λx y z. x y)')
test('(λx y z. x y)','(λx y z. x y z q)')


test('(λx y z. x)','(λx y z. y)')
test('(λx y z. x (λx y z. x) (λx y z. x))','(λx y z. y)')
test('(λx y z. x)','(λx y z. y (λx y z. x) (λx y z. x))')



test('(λx y z. x)','(λx y z. y)')
test('(λx y z. x y)','(λx y z. x z)')
test('(λx y z. x (λa. x x) q1 q2 q3 q4 q5)','(λx y z. x (λa. x z) q1 q2 q3 q4 q5)')

test('(λx y z. z (λb. x (λa. x x) q1 q2 q3 q4 q5) p1 p2 p3 p4 p5)','(λx y z. z (λb. x (λa. x z) q1 q2 q3 q4 q5) p1 p2 p3 p4 p5)')


def diff_var_name_tests():
  for ql in range(5):
    for pl in range(5):
      for xl in range(5):
        for zl in range(5):
          qs = ' '.join([f'q{i}' for i in range(ql)])
          ps = ' '.join([f'p{i}' for i in range(pl)])
          xs = ' '.join([f'x{i}' for i in range(xl)])
          zs = ' '.join([f'z{i}' for i in range(zl)])
          test(f'(λx y z. z (λb. x (λa. x (x {xs})) {qs}) {ps})',f'(λx y z. z (λb. x (λa. x (z {zs})) {qs}) {ps})')
          test(f'(λx y z. z (λb. x (λa. x (z {zs})) {qs}) {ps})',f'(λx y z. z (λb. x (λa. x (x {xs})) {qs}) {ps})')
# diff_var_name_tests()
qs = '(λx y. x (λz.x z y) y)'
qt = '(λx y. x (λz v.x z x v) y)'

test(qs, qt)


# test('λδ. δ δ δ λp c x. x δ (x p c) c', 'λδ. δ δ δ λp c x. x δ (x p) c')
test('λe. e (λβ c s. β s β (β e)) e', 'λe. e (λβ c s. β s β (β s s)) e')
# test('λx. x x λg v. v (x x x)', 'λx. x x λg v. v (g v v g)')
# qs, qt = gen_challenge(20, 20, [])
# print(f'{str(qs)=}')
# print(f'{str(qt)=}')

test('λa. a a', 'λa b. a b')

test('λa b. a a a λc. b a b (a b)', 'λa b. a a a λc. b a b λd. a b')

test('λa b. a (a b)', 'λa b. a (a a)')

r1 = reduce(p(' '.join([f'(λa b. (a (λc. (a a (b b c))) a))']+['(λp0 p1. (p1 p0 p0))','(λp2 p3. (λp4 p5 p6. (p3 p1)))','(λq. (λq. (λq. (λq. (λq. (λq. (λq. (λq. (λx y. (y))))))))))','(λq. (λq. (λq. (λq. (λq. (λq. (λq. (λx y. (x)))))))))','(e)','(f)','(g)','(h)','(i)',])))
print(r1)

print('---')
print(p('(λb. (λa b. a b) b) (var)'))
# r2 = reduce(p('λb. (λa b. a b) b'))
# print(r2)

print('---')
reduce(p(' '.join(['(λa b. a (a b))','(λv0 v1 f. f v0 v1)', '(λv0 f. f v0)', '(holder)', '(λv0 v1. v0)', '(holder)', '(λv0 v1. v0)', '(holder)', '(λi0 i1. (λx y. x))', '(λi0 i1. (λx y. y))'])))
print('---')
reduce(p(' '.join(['(λa b. a (a a))','(λv0 v1 f. f v0 v1)', '(λv0 f. f v0)', '(holder)', '(λv0 v1. v0)', '(holder)', '(λv0 v1. v0)', '(holder)', '(λi0 i1. (λx y. x))', '(λi0 i1. (λx y. y))'])))

# r3 = reduce(p('(λb. (λa b. a b) b) (var)'))
# print(r3)

# r3 = reduce(p('(λx. (λa b. a) x) (λx y. x) (λx y. y)'))
# print(r3)

# r3 = reduce(p('(λx. (λa b. b) x) (λx y. x) (λx y. y)'))
# print(r3)