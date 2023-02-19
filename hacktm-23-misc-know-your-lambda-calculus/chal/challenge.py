#!/usr/local/bin/python3

import random

from interpreter import parse
from interpreter import lterm
from interpreter.lterm import Var, Lambda, Apply

from solver import solve
from secret import flag

names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', "α","β","γ","δ","ε","ζ","ω"]

def gen_challenge(depth, width, s_syms, t_syms):
  if depth == 0:
    s_arg_num = random.randint(1, width)
    t_arg_num = random.randint(1, width)
    
    # at least half chance of having the same
    if random.randint(0, 1) == 0:
      var = random.choice(list(set(s_syms) & set(t_syms)))
      s_expr = lterm.Var(var)
      t_expr = lterm.Var(var)
    else:
      s_expr = lterm.Var(random.choice(s_syms))
      t_expr = lterm.Var(random.choice(t_syms))

    for _ in range(s_arg_num):
      s_expr = lterm.Apply(s_expr, lterm.Var(random.choice(s_syms)))
        
    for _ in range(t_arg_num):
      t_expr = lterm.Apply(t_expr, lterm.Var(random.choice(t_syms)))
    return s_expr, t_expr


  opt = random.randint(0, 5)
  if len(s_syms) == 0 or len(t_syms) == 0 or opt == 0:
    # new_name = random.choice(list(set(names)-set(s_syms+t_syms)))
    s_new_name = names[len(s_syms)]
    t_new_name = names[len(t_syms)]
    s_expr, t_expr = gen_challenge(depth-1, width, s_syms+[s_new_name], t_syms+[t_new_name])

    s_expr = lterm.Lambda(s_new_name, s_expr)
    t_expr = lterm.Lambda(t_new_name, t_expr)
    return s_expr, t_expr
  elif opt == 1:
    new_name = names[len(s_syms)]
    s_expr, t_expr = gen_challenge(depth-1, width, s_syms+[new_name], t_syms)

    s_expr = lterm.Lambda(new_name, s_expr)
    return s_expr, t_expr
  elif opt == 2:
    new_name = names[len(t_syms)]
    s_expr, t_expr = gen_challenge(depth-1, width, s_syms, t_syms+[new_name])

    t_expr = lterm.Lambda(new_name, t_expr)
    return s_expr, t_expr
  else:
    s_new_name = names[len(s_syms)]
    t_new_name = names[len(t_syms)]

    s_expr, t_expr = gen_challenge(depth-1, width, s_syms+[s_new_name], t_syms+[t_new_name])

    var = random.choice(list(set(s_syms)&set(t_syms)))
    arg_num = random.randint(1, width)
    true_child_idx = random.randint(0, arg_num-1)
    
    out_s_expr = lterm.Var(var)
    out_t_expr = lterm.Var(var)
    for i in range(arg_num):
      if i == true_child_idx:
        out_s_expr = lterm.Apply(out_s_expr, s_expr)
        out_t_expr = lterm.Apply(out_t_expr, t_expr)
      else:
        common_arg = random.choice(list(set(s_syms)&set(t_syms)))
        
        out_s_expr = lterm.Apply(out_s_expr, lterm.Var(common_arg))
        out_t_expr = lterm.Apply(out_t_expr, lterm.Var(common_arg))

    out_s_expr = lterm.Lambda(s_new_name, out_s_expr)
    out_t_expr = lterm.Lambda(t_new_name, out_t_expr)
    return out_s_expr, out_t_expr

p = lambda x: parse.parse_expr(x)

def reduce(expr, symbols={}, max_steps=10000):
  for i in range(max_steps):
    # print("\t", expr)
    next = expr.reduce_once(symbols)
    if next is None:
      return expr
    expr = next

def print_intro():
  print('''
------------------ EXAMPLE ------------------
s = λb ε. ε b
t = λb ε. b ε
Please provide inputs [v1, v2, v3, ..., vn] such that:
	((s) (v1) (v2) (v3) ... (vn)) beta-reduces to (λx y. x)
	((t) (v1) (v2) (v3) ... (vn)) beta-reduces to (λx y. y)

How many terms do you want to input? 2
Please input term 1: (λa . (λx y . y))
Please input term 2: (λa . (λx y . x))
Correct!
---------------------------------------------
''')

num_of_challenges = 1000
def main():
  print_intro()
  true_expr = p('(λx y. x)')
  false_expr = p('(λx y. y)')
  for i in range(num_of_challenges):

    while True:
      qs, qt = gen_challenge(2+i//100, 1+i//100, [], [])

      if qs.equiv(qt):
        continue

      try:
        _ = solve(qs, qt)
      except Exception as inst:
        if inst.args[0] == 'No Solution':
          continue
        else:
          assert(False)

      break

    print(f'------------------ challenge {i+1}/{num_of_challenges} ------------------')
    print(f's = {str(qs)}')
    print(f't = {str(qt)}')
    print('Please provide inputs [v1, v2, v3, ..., vn] such that:')
    print(f'\t((s) (v1) (v2) (v3) ... (vn)) beta-reduces to ({str(true_expr)})')
    print(f'\t((t) (v1) (v2) (v3) ... (vn)) beta-reduces to ({str(false_expr)})')
    print('')
    
    n = int(input('How many terms do you want to input? '))
    terms = []
    for i in range(n):
      term = input(f'Please input term {i+1}: ')
      terms.append(f'({term})')

    qs = p(' '.join([f'({qs})']+terms))
    qs = reduce(qs)

    qt = p(' '.join([f'({qt})']+terms))
    qt = reduce(qt)

    if (not qs.equiv(true_expr)) or (not qt.equiv(false_expr)):
      print('-----------------------------------------------------')
      print(f's -> ({str(qs)})')
      print(f't -> ({str(qt)})')
      print('Sorry, your answer is wrong. Try harder next time! Bye')
      return
    print('Correct!')
    
  print('Good job! You have solved all the challenges!')
  print(f'Here is your flag: {flag}')


if __name__ == '__main__':
  main()