import numpy as np
from pwn import p16, u16, enhex
import pickle
from enum import Enum
import gzip
import lzma
import bz2
import zlib


def half_of_byte(b):
  return np.frombuffer(p16(b, endian='little'), dtype=np.float16)[0]

def half_to_byte(h):
  return u16(h.tobytes())


def half_of_int(i):
  return np.float16(i)

def add(a, b):
  return ('+', a, b)

def sub(a, b):
  return ('-', a, b)

def mul(a, b):
  return ('*', a, b)

def ctx(name, val, expr):
  return ('ctx', name, val, expr)

def var(name):
  return ('v', name)

def x():
  return ('x',)

def const(v):
  return ('c', v)

def const_int(i):
  return const(half_to_byte(half_of_int(i)))

# def build_if(val, expr):
#   OFF = [
#     const(0x77f9),
#     const(0x7829),
#     const(0x77fb),
#     const(0x78e2),
#     const(0x77fd),
#     const(0x780b),
#     const(0x77ff),
#     const(0x7864),
#   ]

#   HALF1 = const(0x3c00)
#   HALF128 = const(0x5800)
#   HALFNEG1 = const(0xbc00)
#   HALF0 = const(0x0000)

#   xh = expr
#   nch = sub(HALF1, val)
#   c128 = mul(HALF128, nch)

#   COFF = [0]*len(OFF)
#   for i in range(len(OFF)):
#     COFF[i] = mul(OFF[i], nch)

#   for h in COFF: xh = sub(add(xh, h), h)
#   xh = sub(c128, xh)
#   for h in COFF: xh = sub(add(xh, h), h)

#   xh = add(mul(xh, HALFNEG1), HALF0)

#   return xh

# Works for integers in [0, 512); always results in 1 or 0.
def right_shift_8(v):
  SCALE = const(0x1c00) # 1/256
  OFFSET1 = const(0xb7f6)
  OFFSET2 = const(0x66b0)
  return sub(add(add(mul(v, SCALE), OFFSET1), OFFSET2), OFFSET2)

def uint8_sub(a, b):
  HALF256 = const(0x5c00)
  # Same but don't compute carry.
  z = add(sub(a, b), HALF256)
  o = right_shift_8(var('z'))
  return ctx('z', z,
             sub(var('z'), mul(o, HALF256))) 

def is_zero(a):
  H255 = const(0x5bf8)  # 255.0
  H1 = const(0x3c00)  # 1.0
  nota = sub(H255, a)
  # Now this only overflows if the input was zero.
  res = right_shift_8(add(nota, H1))
  return res

def eq(a, b):
  return is_zero(uint8_sub(a, b))

# expr -> [0,1]
def build_if(expr, output):
  OFF = [
    const(0x77f9),
    const(0x7829),
    const(0x77fb),
    const(0x78e2),
    const(0x77fd),
    const(0x780b),
    const(0x77ff),
    const(0x7864),
  ]

  HALF1 = const(0x3c00)
  HALF128 = const(0x5800)
  HALFNEG1 = const(0xbc00)
  HALF0 = const(0x0000)

  xh = output
  nch = sub(HALF1, expr)
  c128 = mul(HALF128, nch)

  COFF = [0]*len(OFF)
  for i in range(len(OFF)):
    COFF[i] = mul(OFF[i], var('nch'))

  for i in range(len(COFF)): xh = sub(add(xh, var(f'c{i}')), var(f'c{i}'))
  xh = sub(c128, xh)
  for i in range(len(COFF)): xh = sub(add(xh, var(f'c{i}')), var(f'c{i}'))

  xh = add(mul(xh, HALFNEG1), HALF0)
  for i in range(len(COFF)):
    xh = ctx(f'c{i}', COFF[i], xh)
  
  xh = ctx('nch', nch, xh)
  
  return xh

def expr_to_prefix(expr):
  curr = []
  def inner(expr):
    if expr[0] == 'x':
      curr.append('x')
    elif expr[0] == 'c':
      curr.extend(['c', expr[1]])
    elif expr[0] == 'v':
      curr.extend(['v', expr[1]])
    elif expr[0] in ['+', '-','*']:
      curr.append(expr[0])
      inner(expr[1])
      inner(expr[2])
    elif expr[0] == 'ctx':
      curr.append('ctx')
      curr.append(expr[1])
      inner(expr[2])
      inner(expr[3])
    else:
      assert False
  inner(expr)
  return curr

def expr_of_prefix(prefix):
  def inner(i):
    if prefix[i] == 'x':
      return ('x',), 1
    elif prefix[i] == 'c':
      return ('c', prefix[i+1]), 2
    elif prefix[i] == 'v':
      return ('v', prefix[i+1]), 2
    elif prefix[i] in ['+', '-','*']:
      l, l_inc = inner(i+1)
      r, r_inc = inner(i+1+l_inc)
      return (prefix[i], l, r), 1+l_inc+r_inc
    elif prefix[i] == 'ctx':
      
      l, l_inc = inner(i+2)
      r, r_inc = inner(i+2+l_inc)
      return ('ctx', prefix[i+1], l, r), 2+l_inc+r_inc
    else:
      assert False
  return inner(0)[0]

class Expr_type(Enum):
  X = 0b000
  CONST = 0b001
  
  VAR = 0b010
  
  ARTH_OP = 0b100
  
  CTX = 0b101

class ARTH_OP_type(Enum):
  ADD = 0b00
  SUB = 0b01
  MUL = 0b10
  
def extract_const(expr):
  consts = {}
  counts = {}
  i = 0
  def inner(expr):
    nonlocal i
    if expr[0] == 'x':
      return expr
    elif expr[0] == 'c':
      for k, v in consts.items():
        if v == expr[1]:
          counts[k] += 1
          return ('v', k)

      name = f'__c{i}'
      consts[name] = expr[1]
      counts[name] = 1
      i += 1
      return ('v', name)
    elif expr[0] == 'v':
      assert expr[1] not in consts
      return expr
    elif expr[0] in ['+','-','*']:
      return (expr[0], inner(expr[1]), inner(expr[2]))  
    elif expr[0] == 'ctx':
      return ('ctx', expr[1], inner(expr[2]), inner(expr[3]))
    else:
      assert False
  new_expr = inner(expr)
  print(f'{consts=}')
  print(f'{counts=}')
  for k, v in consts.items():
    new_expr = ('ctx', k, ('c', v), new_expr)
  return new_expr
def serialize(expr):
  # expr = extract_const(expr)
  # print(expr)
  curr = b''
  env = {}
  def inner(expr):
    nonlocal curr
    if expr[0] == 'x':
      curr += bytes([Expr_type.X.value << 5])
    elif expr[0] == 'c':
      curr += bytes([Expr_type.CONST.value << 5])
      curr += p16(expr[1], endian='little')
    elif expr[0] == 'v':
      nid = env[expr[1]]
      if nid < 2**5:
        curr += bytes([(Expr_type.VAR.value << 5) + nid])
      else:
        assert False
    elif expr[0] == '+':
      curr += bytes([(Expr_type.ARTH_OP.value << 5),ARTH_OP_type.ADD.value])
      inner(expr[1])
      inner(expr[2])
    elif expr[0] == '-':
      curr += bytes([(Expr_type.ARTH_OP.value << 5),ARTH_OP_type.SUB.value])
      inner(expr[1])
      inner(expr[2])
    elif expr[0] == '*':
      curr += bytes([(Expr_type.ARTH_OP.value << 5),ARTH_OP_type.MUL.value])
      inner(expr[1])
      inner(expr[2])
    elif expr[0] == 'ctx':
      name = expr[1]

      old_val = None
      if name in env:
        old_val = env[name]
      
      nid = len(env)
      print(f'{nid=}')
      # assert nid < 2**5
      if nid < 2**5:
        curr += bytes([(Expr_type.CTX.value << 5) + nid])
      
      else:
        assert False
      
      inner(expr[2])
      
      env[name] = nid
      
      inner(expr[3])
      if old_val is not None:
        env[name] = old_val
      else:
        del env[name]
    else:
      assert False
  inner(expr)
  print(f'{len(bz2.compress(str(expr).encode()))=}')
  print(curr)
  print(list(x if x < 128 else x-256 for x in (curr)))
  print(list(x if x < 128 else x-256 for x in bz2.compress(curr)))
  return bz2.compress(curr)
  
def deserialize(data):
  data = bz2.decompress(data)
  def inner(i):
    expr_type = Expr_type(data[i] >> 5)
    if expr_type == Expr_type.X:
      return ('x',), 1
    elif expr_type == Expr_type.CONST:
      return ('c', u16(data[i+1:i+3], endian='little')), 3
    elif expr_type == Expr_type.VAR:
      return ('v', f'v{data[i] & 0b11111}'), 1
    elif expr_type == Expr_type.ARTH_OP:
      l, l_inc = inner(i+2)
      r, r_inc = inner(i+2+l_inc)
      arth_type = ARTH_OP_type(data[i+1] & 0b11)
      if arth_type == ARTH_OP_type.ADD:
        op = '+'
      elif arth_type == ARTH_OP_type.SUB:
        op  = '-'
      elif arth_type == ARTH_OP_type.MUL:
        op  = '*'
      return (op, l, r), 2+l_inc+r_inc
    elif expr_type == Expr_type.CTX:
      
      l, l_inc = inner(i+1)
      r, r_inc = inner(i+1+l_inc)
      return ('ctx', f'v{data[i] & 0b11111}', l, r), 1+l_inc+r_inc
    else:
      assert False
  return inner(0)[0]

  # return pickle.dumps(expr)

def half_linear_eval(expr, x, env={}):
  def inner(expr, x, env={}):
    # print(expr)
    if expr[0] == 'x':
      return True, x
    elif expr[0] == 'c':
      return False, half_of_byte(expr[1])
    elif expr[0] == 'v':
      return env[expr[1]]
    elif expr[0] == '+':
      l = inner(expr[1], x, env)
      r = inner(expr[2], x, env)
      # print(f'add {l} {r}')
      return l[0] or r[0], l[1] + r[1]
    elif expr[0] == '-':
      l = inner(expr[1], x, env)
      r = inner(expr[2], x, env)
      return l[0] or r[0], l[1] - r[1]
    elif expr[0] == '*':
      l = inner(expr[1], x, env)
      r = inner(expr[2], x, env)
      # have to be linear
      assert not (l[0] and r[0])
      return l[0] or r[0], l[1] * r[1]
    elif expr[0] == 'ctx':
      _, name, val_expr, sub_expr = expr
      new_env = env.copy()
      new_env[name] = inner(val_expr, x, env)
      return inner(sub_expr, x, new_env)
    else:
      assert False
  return inner(expr, x, env)[1]

if __name__ == '__main__':
  
  print(half_of_byte(0x3c00))
  print(half_of_byte(0x5800))
  expr = build_if(eq(x(), const_int(128)), const_int(255))
  # print(hex(half_to_byte(half_of_byte(0x5800))))
  # print(half_linear_eval(expr, half_of_byte(0x3c00)))
  for i in range(256):
    expr = is_zero(x())
    r = half_linear_eval(expr, half_of_int(i))
    print(f'{i} -> {r}')
  #   r = half_linear_eval(expr, half_of_int(i))
  #   print(f'{i} -> {r}')