#!/usr/local/bin/python3

from interpreter import parse
from interpreter.lterm import Var, Lambda, Apply


p = lambda x: parse.parse_expr(x)

def get_apply_head(e):
  assert(type(e) == Apply)

  if type(e.a) == Apply:
    return get_apply_head(e.a)
  return e.a

def get_callchain_head(e):
  assert(type(e) in [Apply, Var])
  
  if type(e) == Apply:
    return get_apply_head(e)
  return e

def get_apply_arg_size(e):
  assert(type(e) == Apply)
  if type(e.a) == Apply:
    return get_apply_arg_size(e.a) + 1
  return 1

def get_callchain_arg_size(e):
  assert(type(e) in [Apply, Var])
  if type(e) == Apply:
    return get_apply_arg_size(e)
  return 0

def get_apply_args(e):
  assert(type(e) == Apply)
  if type(e.a) == Apply:
    return get_apply_args(e.a) + [e.b]
  return [e.b]

def get_callchain_args(e):
  assert(type(e) in [Apply, Var])
  if type(e) == Apply:
    return get_apply_args(e)
  return []


def g_T(var_name):
  def f(ctx):
    depth = ctx[var_name]
    vars = ' '.join([f'v{i}' for i in range(depth)])
  
    return [f'(λ{vars} f. f {vars})']
  return f

def g_select_idx(var_name, delta, idx):
  def f(ctx):
    size = delta(ctx[var_name])
    vars = ' '.join([f'v{i}' for i in range(size)])
    return [f'(λ{vars}. v{idx})']
  return f

def g_place_holders(var_name, delta):
  def f(ctx):
    return ['(holder)' for _ in range(delta(ctx[var_name]))]
  return f

def g_ignore(var_name, delta, out):
  def f(ctx):
    size = delta(ctx[var_name])
    vars = ' '.join([f'i{i}' for i in range(size)])
    return [f'(λ{vars}. {out})']
  return f
  
def solve(s, t, ctx={}, S_LBL='(λx y. x)', T_LBL='(λx y. y)'):
  # print(f'--- {str(s)=} | {str(t)=}')
  if type(s) == Lambda and type(t) == Lambda:
    var_name = f'v{len(ctx)}'
    syms = {}
    ctx, solution, constraints = solve(s.lambda_subst(Var(var_name), syms), t.lambda_subst(Var(var_name), syms), ctx={**ctx, var_name: 0}, S_LBL=S_LBL, T_LBL=T_LBL)
    return ctx, [g_T(var_name)]+solution, constraints
  elif type(s) in [Apply, Var] and type(t) == Lambda:
    var_name = f'v{len(ctx)}'
    syms = {}
    ctx, solution, constraints = solve(Apply(s, Var(var_name)), t.lambda_subst(Var(var_name),syms), ctx={**ctx, var_name: 0}, S_LBL=S_LBL, T_LBL=T_LBL)
    return ctx, [g_T(var_name)]+solution, constraints
  elif type(s) == Lambda and type(t) in [Apply, Var]:
    var_name = f'v{len(ctx)}'
    syms = {}
    ctx, solution, constraints = solve(s.lambda_subst(Var(var_name),syms), Apply(t, Var(var_name)), ctx={**ctx, var_name: 0}, S_LBL=S_LBL, T_LBL=T_LBL)
    return ctx, [g_T(var_name)]+solution, constraints
  elif type(s) in [Apply, Var] and type(t) in [Apply, Var]:
    s_head = get_callchain_head(s)
    t_head = get_callchain_head(t)
    s_cc_size = get_callchain_arg_size(s)
    t_cc_size = get_callchain_arg_size(t)
    s_args = get_callchain_args(s)
    t_args = get_callchain_args(t)

    if s_head.name == t_head.name:
      var_name = s_head.name

      if s_cc_size == t_cc_size:
        # hard case
        arg_size = s_cc_size

        selected = None
        # TODO: can pick the smallest
        selected_idx = 0
        for s_child, t_child in zip(s_args, t_args):
          if not s_child.equiv(t_child):
            selected = (s_child, t_child)
            break
          selected_idx += 1
        if selected is None:
          raise Exception("No Solution")

        s_child, t_child = selected
        # print(f'{str(s_child)=} | {str(t_child)=}')
        ctx, solution, constraints = solve(s_child, t_child, ctx=ctx, S_LBL=S_LBL, T_LBL=T_LBL)
        if ctx[var_name] < arg_size:
          new_count = arg_size
          while new_count in ctx.values():
            new_count += 1
          ctx[var_name] = new_count

        solution = [
          g_place_holders(var_name, lambda x: x-arg_size),
          g_select_idx(var_name, lambda x: x, selected_idx),
        ] + solution

        return ctx, solution, constraints

      elif s_cc_size < t_cc_size:
        arg_size = t_cc_size
        ctx[var_name] = arg_size
        solution = [
          g_place_holders(var_name, lambda x: x - t_cc_size),
          g_ignore(var_name, lambda x: x + t_cc_size - s_cc_size, T_LBL),
          g_place_holders(var_name, lambda x: t_cc_size - s_cc_size - 1),
          g_ignore(var_name, lambda x: x, S_LBL),
        ]
        return ctx, solution, []
      elif s_cc_size > t_cc_size:

        # print('--- debug ---')
        # print(f'{str(s)=}')
        # print(f'{str(t)=}')
        # print(f'{ctx=}')
        # # print(f'{out_list=}')
        # print('-------------')
        
        arg_size = s_cc_size
        ctx[var_name] = arg_size
        solution = [
          g_place_holders(var_name, lambda x: x - s_cc_size),
          g_ignore(var_name, lambda x: x + s_cc_size - t_cc_size, S_LBL),
          g_place_holders(var_name,lambda x: s_cc_size - t_cc_size - 1),
          g_ignore(var_name, lambda x: x, T_LBL),
        ]
        return ctx, solution, []
        
    elif s_head.name != t_head.name:
      # these two should never be equal!!!
      ctx[s_head.name] = s_cc_size + 1
      ctx[t_head.name] = t_cc_size
      def gen_f(ctx):
        s_v = ctx[s_head.name] - s_cc_size
        t_v = ctx[t_head.name] - t_cc_size
        
        assert(s_v != t_v)
        if s_v > t_v:
          return [e for f in [
            g_place_holders(t_head.name, lambda x: x - t_cc_size),
            g_ignore(s_head.name, lambda x:x - s_cc_size+ t_cc_size, T_LBL),
            g_place_holders(s_head.name,lambda x: x - s_cc_size - (ctx[t_head.name]-t_cc_size) - 1),
            g_ignore(s_head.name, lambda x:x, S_LBL),
          ] for e in f(ctx)]
        else:
          # assert(False)
          return [e for f in [
            g_place_holders(s_head.name, lambda x: x - s_cc_size),
            g_ignore(t_head.name, lambda x: x - t_cc_size + s_cc_size, S_LBL),
            g_place_holders(t_head.name,lambda x: x - t_cc_size - (ctx[s_head.name]-s_cc_size) - 1),
            g_ignore(t_head.name, lambda x:x, T_LBL),
          ] for e in f(ctx)]

      return ctx, [gen_f], [(s_head.name, t_head.name, s_cc_size-t_cc_size)]
  else:
    assert(False)

def post_process(ctx, solution, constraints):
  while True:
    for v1, v2, diff in constraints:
      if ctx[v1] - ctx[v2] == diff:
        ctx[v1] += 1
        break
    else:
      break
  output = []
  for each in solution:
    output.extend(each(ctx))
  return output

if __name__ == '__main__':
  from pwn import *
  # context.log_level = 'debug'
  # stdout = process.PTY
  # stdin = process.PTY
  # sh = process(['python3', './challenge.py'], stdout=stdout, stdin=stdin, stderr=process.PTY)
  sh = remote('34.141.16.87', 60000)
  sh.recvuntil('---------------------------------------------')
  num_of_challenges = 1000

  for i in range(num_of_challenges):
    data = sh.recvuntil('input? ').decode().strip().split('\n')
    # print(data)
    qs = data[-7][4:]
    qt = data[-6][4:]
    print('-'*10)
    print(f'{i+1}/{num_of_challenges}')
    print(f'{str(qs)=}')
    print(f'{str(qt)=}')
    ctx, solution, constraints = solve(p(qs), p(qt))
    solution = post_process(ctx, solution, constraints)
    sh.sendline(str(len(solution)))
    for each in solution:
      sh.sendline(each.encode())
  sh.interactive()

# def test(qs, qt):
#   print('--- test case ---')
#   print(f'{str(p(qs))=}')
#   print(f'{str(p(qt))=}')
#   ctx, solution, constraints = solve(p(qs), p(qt))
#   print(f'{ctx=}')
#   solution = post_process(ctx, solution, constraints)
#   print(f'{solution=}')
#   print(f'{ctx=}')

#   r1 = reduce(p(' '.join([f'({qs})']+solution)))
#   print(r1)

#   r2 = reduce(p(' '.join([f'({qt})']+solution)))
#   print(r2)
#   assert(r1 == Var('true'))
#   assert(r2 == Var('false'))
#   print('-----------------\n\n\n')

# s = λb ε. ε b
# t = λb ε. b ε
